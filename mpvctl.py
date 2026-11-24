"""Shared settings and mpv control for the Simpsons TV scripts.

The player scripts start one mpv process per video with a JSON IPC socket.
buttons.py talks to whichever mpv is currently running through that socket.

Settings come from environment variables, which the systemd services load
from simpsonstv.conf (see simpsonstv.conf.example).
"""
import json
import os
import shlex
import socket
import subprocess
import time

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
VIDEO_DIR = os.environ.get('SIMPSONSTV_VIDEO_DIR', os.path.join(BASE_DIR, 'videos'))
INTERSTITIAL_DIR = os.environ.get('SIMPSONSTV_INTERSTITIAL_DIR', os.path.join(BASE_DIR, 'interstitials'))
RUN_DIR = os.environ.get('SIMPSONSTV_RUN_DIR', '/run/simpsonstv')
SOCKET_PATH = os.path.join(RUN_DIR, 'mpv.sock')
# Exists while the TV is switched off, so a newly started video starts paused.
PAUSE_FLAG = os.path.join(RUN_DIR, 'paused')

# Hardware-specific mpv options; override with MPV_ARGS in simpsonstv.conf.
DEFAULT_MPV_ARGS = (
    '--vo=gpu --gpu-context=drm --hwdec=auto-safe --video-rotate=270 '
    '--ao=alsa --audio-device=alsa/plughw:CARD=Headphones,DEV=0'
)


def ensure_run_dir():
    os.makedirs(RUN_DIR, exist_ok=True)


def list_videos():
    """Return the full paths of all .mp4 files in the video folder and its
    subfolders (one per show), sorted by path so each show's episodes are in order.

    Hidden files and folders are skipped, which also skips the "._" files
    macOS leaves on network shares.
    """
    videos = []
    for folder, subfolders, files in os.walk(VIDEO_DIR):
        subfolders[:] = [name for name in subfolders if not name.startswith('.')]
        videos.extend(
            os.path.join(folder, name)
            for name in files
            if name.lower().endswith('.mp4') and not name.startswith('.')
        )
    return sorted(videos)


def static_clips():
    """The channel-change static clips (interstitials/static_*.mp4)."""
    if not os.path.isdir(INTERSTITIAL_DIR):
        return []
    return sorted(
        os.path.join(INTERSTITIAL_DIR, name)
        for name in os.listdir(INTERSTITIAL_DIR)
        if name.startswith('static_') and name.lower().endswith('.mp4')
    )


def interstitial(name):
    """Full path of an interstitial clip, or None if it isn't there."""
    path = os.path.join(INTERSTITIAL_DIR, name)
    return path if os.path.isfile(path) else None


def mpv_command(video):
    args = [
        'mpv',
        '--fullscreen',
        '--osd-level=0',
        '--input-terminal=no',
        '--msg-level=all=warn',
        '--input-ipc-server=' + SOCKET_PATH,
    ]
    args += shlex.split(os.environ.get('MPV_ARGS', DEFAULT_MPV_ARGS))
    if os.path.exists(PAUSE_FLAG):
        args.append('--pause')
    args.append(video)
    return args


def play(video):
    """Play one video and block until mpv exits (video ended or 'quit' was sent)."""
    started = time.monotonic()
    result = subprocess.run(mpv_command(video))
    if result.returncode != 0 and time.monotonic() - started < 2:
        # mpv failed straight away (bad options, broken file); don't spin the CPU.
        time.sleep(2)
    return result.returncode


def send(*command):
    """Send one command to the running mpv.

    Returns mpv's reply as a dict, or None if no mpv is running or it didn't answer.
    """
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(1.0)
            sock.connect(SOCKET_PATH)
            sock.sendall((json.dumps({'command': list(command)}) + '\n').encode())
            buffer = b''
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    return None
                buffer += chunk
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    message = json.loads(line)
                    if 'event' not in message:  # skip async events, wait for the reply
                        return message
    except (OSError, ValueError):
        return None


def ok(reply):
    return bool(reply) and reply.get('error') == 'success'


def get(name):
    """Read an mpv property; None if mpv isn't running or the property isn't available."""
    reply = send('get_property', name)
    return reply.get('data') if ok(reply) else None
