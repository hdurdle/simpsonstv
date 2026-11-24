"""CRT look: a see-through overlay that mpv draws on top of the video.

The overlay darkens alternate screen rows (scanlines) and every third column
(a faint phosphor mask), darkens the edges (vignette), adds a faint glass
reflection and blacks out rounded corners. It's drawn to fit the area mpv
shows video in, so it lines up with 4:3 and widescreen episodes alike, and
costs almost nothing to display: mpv composites it like on-screen text.

Settings (simpsonstv.conf), each 0 to 1:
  CRT_EFFECT=on|off   CRT_SCANLINES   CRT_MASK   CRT_VIGNETTE
  CRT_REFLECTION      CRT_CORNERS (corner radius, as a fraction of picture height)

Preview on a PC (needs numpy and Pillow):
  python3 crt.py --preview picture.png out.png [--width 640 --height 480]
"""
import argparse
import os

OVERLAY_ID = 0

DEFAULTS = {
    'scanlines': 0.30,
    'mask': 0.08,
    'vignette': 0.45,
    'reflection': 0.05,
    'corners': 0.06,
}


def settings_from_env(environ=os.environ):
    settings = {}
    for name, default in DEFAULTS.items():
        try:
            value = float(environ.get('CRT_' + name.upper(), default))
        except ValueError:
            value = default
        settings[name] = min(max(value, 0.0), 1.0)
    return settings


def build_overlay(width, height, settings, screen_top=0):
    """BGRA pixels with premultiplied alpha (what mpv's overlay-add expects),
    as a (height, width, 4) uint8 array. `screen_top` is the picture's row on
    screen, so scanlines line up with the screen's own rows."""
    import numpy as np

    rows = np.arange(height, dtype=np.float32)[:, None]
    cols = np.arange(width, dtype=np.float32)[None, :]
    # Work in premultiplied form: colour (0-1, single grey level) and alpha.
    colour = np.zeros((height, width), dtype=np.float32)
    alpha = np.zeros((height, width), dtype=np.float32)

    def over(layer_colour, layer_alpha):
        """Composite a layer on top: out = src + dst * (1 - src_alpha)."""
        nonlocal colour, alpha
        layer_alpha = np.broadcast_to(layer_alpha, alpha.shape)
        colour = layer_colour * layer_alpha + colour * (1 - layer_alpha)
        alpha = layer_alpha + alpha * (1 - layer_alpha)

    # Scanlines: darken every other screen row.
    odd_rows = ((rows + screen_top) % 2 == 1).astype(np.float32)
    over(0.0, odd_rows * settings['scanlines'])
    # Phosphor mask: darken every third column a little.
    over(0.0, (cols % 3 == 2).astype(np.float32) * settings['mask'])
    # Vignette: darker towards the edges and corners.
    y = (rows / max(height - 1, 1)) * 2 - 1
    x = (cols / max(width - 1, 1)) * 2 - 1
    over(0.0, settings['vignette'] * np.clip((x ** 2 + y ** 2) / 2, 0, 1) ** 1.5)
    # Glass reflection: a soft white glow in the top-left.
    glow = np.exp(-(((x + 0.55) / 0.6) ** 2 + ((y + 0.6) / 0.35) ** 2))
    over(1.0, settings['reflection'] * glow)
    # Rounded corners: solid black outside a rounded rectangle, soft-edged.
    radius = settings['corners'] * height
    if radius >= 1:
        dx = np.clip(np.maximum(radius - cols - 0.5, cols + 0.5 - (width - radius)), 0, None)
        dy = np.clip(np.maximum(radius - rows - 0.5, rows + 0.5 - (height - radius)), 0, None)
        outside = np.sqrt(dx ** 2 + dy ** 2) - radius
        over(0.0, np.clip(outside + 0.5, 0, 1))

    pixels = np.empty((height, width, 4), dtype=np.uint8)
    grey = np.clip(colour * alpha * 255 + 0.5, 0, 255).astype(np.uint8)  # premultiplied
    pixels[..., 0] = grey  # B
    pixels[..., 1] = grey  # G
    pixels[..., 2] = grey  # R
    pixels[..., 3] = np.clip(alpha * 255 + 0.5, 0, 255).astype(np.uint8)
    return pixels


class CrtOverlay:
    """Keeps the overlay on screen and sized to the video, via mpv's overlay-add."""

    def __init__(self, mpvctl, enabled, settings, cache_dir):
        self.mpvctl = mpvctl
        self.enabled = enabled
        self.settings = settings
        self.cache_dir = cache_dir
        self.shown_rect = None   # (x, y, w, h) currently on screen
        self.files = {}

    def video_rect(self):
        """Where mpv draws the picture on screen, or None while nothing is shown."""
        dims = self.mpvctl.get('osd-dimensions')
        if not dims:
            return None
        try:
            x, y = int(dims['ml']), int(dims['mt'])
            width = int(dims['w']) - x - int(dims['mr'])
            height = int(dims['h']) - y - int(dims['mb'])
        except (KeyError, TypeError, ValueError):
            return None
        if width < 16 or height < 16:
            return None
        return x, y, width, height

    def file_for(self, rect):
        if rect not in self.files:
            x, y, width, height = rect
            pixels = build_overlay(width, height, self.settings, screen_top=y)
            os.makedirs(self.cache_dir, exist_ok=True)
            path = os.path.join(self.cache_dir, 'crt_%dx%d_%d.bgra' % (width, height, y % 2))
            with open(path, 'wb') as file:
                file.write(pixels.tobytes())
            self.files[rect] = path
        return self.files[rect]

    def update(self):
        """Show, resize or remove the overlay to match the setting and the video."""
        if not self.enabled:
            if self.shown_rect is not None:
                self.mpvctl.send('overlay-remove', OVERLAY_ID)
                self.shown_rect = None
            return
        rect = self.video_rect()
        if rect is None or rect == self.shown_rect:
            return
        try:
            path = self.file_for(rect)
        except ImportError:
            print('CRT effect needs numpy (sudo apt install python3-numpy); turning it off')
            self.enabled = False
            return
        x, y, width, height = rect
        reply = self.mpvctl.send('overlay-add', OVERLAY_ID, x, y, path, 0, 'bgra',
                                 width, height, width * 4)
        if self.mpvctl.ok(reply):
            self.shown_rect = rect

    def set_enabled(self, enabled):
        self.enabled = enabled
        self.shown_rect = None if enabled else self.shown_rect
        self.update()

    def forget(self):
        """mpv restarted, so nothing is on screen any more."""
        self.shown_rect = None


def preview(picture, out, width, height, settings):
    import numpy as np
    from PIL import Image

    base = np.asarray(Image.open(picture).convert('RGB').resize((width, height)), dtype=np.float32)
    overlay = build_overlay(width, height, settings).astype(np.float32) / 255
    alpha = overlay[..., 3:4]
    rgb = overlay[..., 2::-1] * 255 + base * (1 - alpha)   # BGR -> RGB, premultiplied "over"
    Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(out)
    print('wrote ' + out)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--preview', nargs=2, metavar=('PICTURE', 'OUT'), required=True,
                        help='draw the overlay on top of PICTURE and save it as OUT')
    parser.add_argument('--width', type=int, default=640)
    parser.add_argument('--height', type=int, default=480)
    for name, default in DEFAULTS.items():
        parser.add_argument('--' + name, type=float, default=None,
                            help='0-1 (default %s, or CRT_%s)' % (default, name.upper()))
    args = parser.parse_args()
    settings = settings_from_env()
    for name in DEFAULTS:
        if getattr(args, name) is not None:
            settings[name] = getattr(args, name)
    preview(args.preview[0], args.preview[1], args.width, args.height, settings)


if __name__ == '__main__':
    main()
