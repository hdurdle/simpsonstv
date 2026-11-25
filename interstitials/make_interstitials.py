"""Generate the TV's interstitial videos.

- static_NN.mp4  channel-change static in several random variants: different
                 lengths and noise, some with another channel bleeding through
- crt_off.mp4    picture brightens, collapses to a line, then to a fading dot

Encoded like videos/encode.py: 480 lines, H.264 baseline level 3.0, CRF 23,
yuv420p, AAC audio. Needs ffmpeg, numpy and Pillow.

    python make_interstitials.py                       # 640x480 (4:3, like the episodes)
    python make_interstitials.py --width 800           # fill the 800x480 screen
    python make_interstitials.py --off-image still.png # collapse a picture instead of a white flash
"""
import argparse
import os
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageFilter

HEIGHT = 480
FPS = 30
SAMPLE_RATE = 44100
PHOSPHOR = np.array([235, 242, 255], dtype=np.float32)  # slightly blue CRT white

SCANLINES = np.ones((HEIGHT, 1, 1), dtype=np.float32)
SCANLINES[1::2] = 0.72


def vignette(width):
    y = np.linspace(-1, 1, HEIGHT, dtype=np.float32)[:, None]
    x = np.linspace(-1, 1, width, dtype=np.float32)[None, :]
    return np.clip(1 - 0.3 * (x ** 2 + y ** 2) ** 1.5, 0, 1)[..., None]


def clamp01(x):
    return min(max(x, 0.0), 1.0)


def encode(path, width, frames, audio):
    """Encode RGB uint8 frames and mono float audio (-1..1) to an mp4."""
    with tempfile.NamedTemporaryFile(suffix='.raw', delete=False) as file:
        file.write((np.clip(audio, -1, 1) * 32767).astype('<i2').tobytes())
        audio_path = file.name
    try:
        command = [
            'ffmpeg', '-y', '-loglevel', 'error',
            '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (width, HEIGHT),
            '-r', str(FPS), '-i', '-',
            '-f', 's16le', '-ar', str(SAMPLE_RATE), '-ac', '1', '-i', audio_path,
            '-c:v', 'libx264', '-profile:v', 'baseline', '-level', '3.0',
            '-preset', 'fast', '-crf', '23', '-pix_fmt', 'yuv420p',
            # Noise barely compresses; cap the bitrate so static stays within
            # level 3.0 and easy for the Pi's hardware decoder.
            '-maxrate', '4M', '-bufsize', '8M',
            '-c:a', 'aac', '-b:a', '128k', '-shortest', '-movflags', '+faststart',
            path,
        ]
        process = subprocess.Popen(command, stdin=subprocess.PIPE)
        for frame in frames:
            process.stdin.write(frame.tobytes())
        process.stdin.close()
        if process.wait() != 0:
            raise SystemExit('ffmpeg failed for ' + path)
    finally:
        os.remove(audio_path)
    print('wrote ' + path)


def band_limited_noise(samples, rng, low_hz, high_hz):
    spectrum = np.fft.rfft(rng.standard_normal(samples))
    freqs = np.maximum(np.fft.rfftfreq(samples, 1 / SAMPLE_RATE), 1)
    response = 1 / (1 + (low_hz / freqs) ** 4) / (1 + (freqs / high_hz) ** 4)
    noise = np.fft.irfft(spectrum * response, samples)
    return (noise / np.sqrt(np.mean(noise ** 2))).astype(np.float32)


def fade_edges(audio, attack_s, release_s):
    attack = int(attack_s * SAMPLE_RATE)
    release = int(release_s * SAMPLE_RATE)
    audio[:attack] *= np.linspace(0, 1, attack)
    audio[-release:] *= np.linspace(1, 0, release)
    return audio


# --- channel-change static -------------------------------------------------
#
# Each variant is a different "channel flick": its own length, snow texture,
# roll, interference and, usually, a brief moment where a weak signal from
# another channel bleeds through.

def random_static_params(rng, max_seconds):
    seconds = min(rng.uniform(0.4, 2.5), max_seconds)
    bleeds = []
    for _ in range(int(rng.choice([0, 1, 1, 2]))):
        length = rng.uniform(0.15, min(0.7, seconds * 0.6))
        bleeds.append({
            'start': rng.uniform(0.05, max(0.06, seconds - length - 0.05)),
            'length': length,
            'strength': rng.uniform(0.25, 0.65),
            'sound': str(rng.choice(['murmur', 'hum', 'tone'])),
        })
    return {
        'frames': max(1, int(round(seconds * FPS))),
        'brightness': rng.uniform(0.75, 1.1),
        'contrast': rng.uniform(1.6, 2.6),
        'chroma': rng.uniform(8, 40),
        'roll_speed': rng.uniform(0.4, 1.6) * rng.choice([-1, 1]),
        'band_strength': rng.uniform(0.1, 0.45),
        'tears_per_frame': rng.uniform(0, 6),
        'jump_chance': rng.uniform(0, 0.12),     # chance per frame of a vertical-hold jump
        'hiss': rng.uniform(0.10, 0.22),
        'chirp': bool(rng.random() < 0.5),       # tuning chirp on the cut
        'bleeds': bleeds,
    }


def describe_static(params):
    parts = ['%.2fs' % (params['frames'] / FPS)]
    for bleed in params['bleeds']:
        parts.append('bleed %.2f-%.2fs (%s)' % (bleed['start'], bleed['start'] + bleed['length'], bleed['sound']))
    if params['chirp']:
        parts.append('chirp')
    return ', '.join(parts)


def bleed_strength(bleeds, t):
    """How strongly another channel shows through at time t (scalar or array)."""
    t = np.asarray(t, dtype=np.float32)
    total = np.zeros_like(t)
    ramp = 0.08
    for bleed in bleeds:
        rel = t - bleed['start']
        envelope = np.minimum(np.clip(rel / ramp, 0, 1), np.clip((bleed['length'] - rel) / ramp, 0, 1))
        total += bleed['strength'] * envelope
    return np.clip(total, 0, 0.9)


def make_ghost_picture(width, rng):
    """A made-up weak picture from another channel: blurry colour shapes, sometimes bars."""
    small = (rng.random((5, 7, 3)) * 255).astype(np.uint8)
    picture = np.asarray(Image.fromarray(small).resize((width, HEIGHT), Image.BICUBIC), dtype=np.float32)
    if rng.random() < 0.4:
        bars = (rng.random((1, int(rng.integers(5, 9)), 3)) * 255).astype(np.uint8)
        bars = np.asarray(Image.fromarray(bars).resize((width, HEIGHT), Image.NEAREST), dtype=np.float32)
        picture = picture * 0.3 + bars * 0.7
    grey = picture.mean(axis=2, keepdims=True)
    picture = grey + (picture - grey) * 0.55   # weak signals look washed out
    picture[:28] *= 0.1   # vertical blanking bar; rolls with the picture when hold is lost
    return picture


def static_frames(width, params, rng):
    fields = HEIGHT // 2          # draw 240 lines and line-double, like an interlaced field
    half_width = (width + 1) // 2
    vig = vignette(width)
    rows = np.arange(fields, dtype=np.float32) / fields
    ghost = make_ghost_picture(width, rng)
    ghost_roll = rng.uniform(150, 600) * rng.choice([-1, 1])     # pixels per second
    skew_amp = rng.uniform(5, 30)
    skew_freq = rng.uniform(0.01, 0.04)
    column_index = np.arange(width)[None, :]
    row_index = np.arange(HEIGHT)[:, None]

    for index in range(params['frames']):
        t = index / FPS
        snow = rng.random((fields, half_width), dtype=np.float32)
        snow = np.repeat(snow, 2, axis=1)[:, :width]
        # smear sideways, like a tuner's limited bandwidth
        snow = (snow + np.roll(snow, 1, axis=1) + 0.5 * np.roll(snow, 2, axis=1)) / 2.5
        snow = np.clip((snow - 0.5) * params['contrast'] + 0.5, 0, 1)
        luma = (30 + 225 * snow ** 1.2) * params['brightness']

        # torn, brighter lines
        for row in rng.choice(fields, size=int(rng.poisson(params['tears_per_frame']))):
            luma[row] = np.roll(luma[row], int(rng.integers(-60, 60))) * rng.uniform(1.1, 1.4)

        # darker band rolling through the picture (vertical hold drifting)
        band_pos = (t * params['roll_speed']) % 1.4 - 0.2
        luma *= (1 - params['band_strength'] * np.exp(-((rows - band_pos) / 0.08) ** 2))[:, None]
        luma *= rng.uniform(0.9, 1.05)  # frame-to-frame flicker
        if index < 2:
            luma = luma * 0.6 + 110     # flash on the cut

        chroma = (rng.random((fields, half_width, 3), dtype=np.float32) - 0.5) * params['chroma']
        chroma = np.repeat(chroma, 2, axis=1)[:, :width]
        rgb = np.repeat(luma[..., None] + chroma, 2, axis=0)

        strength = float(bleed_strength(params['bleeds'], t))
        if strength > 0:
            rolled = np.roll(ghost, int(t * ghost_roll) % HEIGHT, axis=0)
            shift = (skew_amp * np.sin(np.arange(HEIGHT) * skew_freq + t * 9)).astype(int)
            warped = rolled[row_index, (column_index - shift[:, None]) % width]
            rgb = rgb * (1 - 0.8 * strength) + warped * strength * 1.2

        if rng.random() < params['jump_chance']:
            rgb = np.roll(rgb, int(rng.integers(20, HEIGHT - 20)), axis=0)

        yield np.clip(rgb * SCANLINES * vig, 0, 255).astype(np.uint8)


def static_audio(params, rng):
    samples = int(round(params['frames'] / FPS * SAMPLE_RATE))
    t = np.arange(samples, dtype=np.float32) / SAMPLE_RATE

    audio = band_limited_noise(samples, rng, 250, 7000) * params['hiss']
    flicker = rng.uniform(-1, 1, params['frames'])
    audio *= 1 + 0.2 * np.repeat(flicker, SAMPLE_RATE // FPS)[:samples]
    audio *= 1 - 0.6 * bleed_strength(params['bleeds'], t) / 0.9   # hiss drops as a signal comes in
    for position in rng.integers(0, samples, size=max(1, int(samples / SAMPLE_RATE * 17))):
        audio[position] += rng.uniform(-0.5, 0.5)                   # crackle

    for bleed in params['bleeds']:
        if bleed['sound'] == 'murmur':     # muffled voices: low-passed noise, syllable-rate wobble
            syllables = 0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(3, 6) * t + rng.uniform(0, 6))
            sound = band_limited_noise(samples, rng, 150, 1200) * 0.12 * syllables
        elif bleed['sound'] == 'hum':      # mains hum and buzz
            mains = rng.choice([50, 60])
            sound = 0.1 * np.sign(np.sin(2 * np.pi * mains * t)) + 0.2 * np.sin(4 * np.pi * mains * t)
        else:                              # test-card tone
            sound = 0.3 * np.sin(2 * np.pi * rng.choice([440, 1000]) * t)
        audio += sound * bleed_strength([bleed], t) / 0.65

    if params['chirp']:                    # tuner sweeping past a carrier
        length = min(samples, int(0.09 * SAMPLE_RATE))
        freq = np.linspace(rng.uniform(1500, 3000), rng.uniform(200, 500), length)
        audio[:length] += 0.25 * np.sin(2 * np.pi * np.cumsum(freq) / SAMPLE_RATE) * np.linspace(1, 0, length)

    audio *= min(1.0, 0.6 / np.max(np.abs(audio)))   # peaks at -4.4 dB; AAC overshoots a little
    return fade_edges(audio, 0.005, 0.03)


# --- CRT switch-off ---------------------------------------------------------

BRIGHTEN_END = 0.10     # picture flares up
COLLAPSE_END = 0.30     # squashes to a horizontal line
LINE_END = 0.55         # line shrinks to a dot
DOT_END = 1.25          # dot fades out; black after this


def crt_off_frames(width, seconds, off_image):
    if off_image:
        base = np.asarray(Image.open(off_image).convert('RGB').resize((width, HEIGHT)), dtype=np.float32)
    else:
        base = np.broadcast_to(PHOSPHOR * 0.5, (HEIGHT, width, 3)).copy()
    base = base * SCANLINES * vignette(width)

    cx, cy = width / 2, HEIGHT / 2
    ys, xs = np.mgrid[0:HEIGHT, 0:width].astype(np.float32)
    dist2 = (xs - cx) ** 2 + (ys - cy) ** 2

    for index in range(int(round(seconds * FPS))):
        t = index / FPS
        canvas = np.zeros((HEIGHT, width, 3), dtype=np.float32)

        if t < BRIGHTEN_END:
            k = t / BRIGHTEN_END
            canvas = base * (1 + 0.5 * k) + PHOSPHOR * 0.5 * k
        elif t < COLLAPSE_END:
            k = clamp01((t - BRIGHTEN_END) / (COLLAPSE_END - BRIGHTEN_END)) ** 2
            height = max(2, int(round(HEIGHT * (1 - k))))
            bright = base * 1.5 + PHOSPHOR * 0.5
            squashed = np.asarray(
                Image.fromarray(np.clip(bright, 0, 255).astype(np.uint8)).resize((width, height)),
                dtype=np.float32)
            squashed = squashed * (1 - k) + PHOSPHOR * 1.3 * k   # washes out to white as it thins
            top = (HEIGHT - height) // 2
            canvas[top:top + height] = squashed
        elif t < LINE_END:
            k = clamp01((t - COLLAPSE_END) / (LINE_END - COLLAPSE_END)) ** 2
            half_width = max(2.0, width * (1 - k) / 2)
            outside = np.clip(np.abs(xs - cx) - half_width, 0, None)  # distance past the line's ends
            d2 = outside ** 2 + (ys - cy) ** 2
            core = (np.abs(ys - cy) <= 1.5) & (outside == 0)
            halo = 0.5 * np.exp(-d2 / (2 * 6 ** 2)) + 0.2 * np.exp(-d2 / (2 * 20 ** 2))
            canvas = PHOSPHOR * 1.3 * (core + halo)[..., None]
        elif t < DOT_END:
            k = clamp01((t - LINE_END) / (DOT_END - LINE_END))
            strength = np.exp(-3.5 * k) * (1 - k)               # phosphor decay to zero
            core_radius = 3.5 * (1 - 0.4 * k)
            core = np.clip(core_radius + 0.5 - np.sqrt(dist2), 0, 1)
            halo = 0.55 * np.exp(-dist2 / (2 * 14 ** 2)) + 0.25 * np.exp(-dist2 / (2 * 40 ** 2))
            canvas = PHOSPHOR * 1.3 * strength * (core + halo)[..., None]

        # bloom around anything bright
        emission = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8))
        glow = np.asarray(emission.filter(ImageFilter.GaussianBlur(10)), dtype=np.float32)
        yield np.clip(canvas + glow * 0.8, 0, 255).astype(np.uint8)


def crt_off_audio(seconds, rng):
    samples = int(round(seconds * SAMPLE_RATE))
    t = np.arange(samples, dtype=np.float32) / SAMPLE_RATE
    audio = np.zeros(samples, dtype=np.float32)

    # high flyback whine dying away
    audio += 0.03 * np.sin(2 * np.pi * 9000 * t) * np.exp(-t / 0.35)

    after = np.clip(t - BRIGHTEN_END, 0, None)
    started = t >= BRIGHTEN_END
    # click as the deflection collapses
    click_len = int(0.004 * SAMPLE_RATE)
    start = int(BRIGHTEN_END * SAMPLE_RATE)
    audio[start:start + click_len] += rng.standard_normal(click_len) * 0.25 * np.linspace(1, 0, click_len)
    # low thump, pitched down as it decays (110 Hz partial so small speakers carry it)
    freq = 60 - 25 * np.clip(after / 0.3, 0, 1)
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    thump = (0.4 * np.sin(phase) + 0.25 * np.sin(2 * phase)) * np.exp(-after / 0.09)
    audio += np.where(started, thump, 0)
    # short static fizz
    fizz = band_limited_noise(samples, rng, 1500, 8000) * 0.08 * np.exp(-after / 0.12)
    audio += np.where(started, fizz, 0)
    audio *= 0.7 / np.max(np.abs(audio))   # peak at -3 dB
    return fade_edges(audio, 0.002, 0.05)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--width', type=int, default=640, help='frame width (height is always 480)')
    parser.add_argument('--static-variants', type=int, default=6, help='how many static clips to make')
    parser.add_argument('--max-static-seconds', type=float, default=1.27, help='longest a static clip may be')
    parser.add_argument('--off-seconds', type=float, default=1.5)
    parser.add_argument('--off-image', help='picture to collapse instead of a white flash')
    parser.add_argument('--out-dir', default=os.path.dirname(os.path.realpath(__file__)))
    parser.add_argument('--seed', type=int, default=447)
    args = parser.parse_args()

    if args.width % 2:
        parser.error('--width must be even for yuv420p')
    for number in range(1, args.static_variants + 1):
        rng = np.random.default_rng([args.seed, number])   # each variant reproducible on its own
        params = random_static_params(rng, args.max_static_seconds)
        path = os.path.join(args.out_dir, 'static_%02d.mp4' % number)
        encode(path, args.width, static_frames(args.width, params, rng), static_audio(params, rng))
        print('   ' + describe_static(params))
    rng = np.random.default_rng(args.seed)
    encode(os.path.join(args.out_dir, 'crt_off.mp4'), args.width,
           crt_off_frames(args.width, args.off_seconds, args.off_image), crt_off_audio(args.off_seconds, rng))


if __name__ == '__main__':
    main()
