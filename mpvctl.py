"""Shared settings and control of the single mpv player.

tv.py keeps one mpv running in idle mode and loads each episode or clip into
it over mpv's JSON IPC socket.

Settings come from environment variables, which the systemd service loads
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
CACHE_DIR = os.environ.get('SIMPSONSTV_CACHE_DIR', os.path.join(BASE_DIR, 'cache'))
RUN_DIR = os.environ.get('SIMPSONSTV_RUN_DIR', '/run/simpsonstv')
SOCKET_PATH = os.path.join(RUN_DIR, 'mpv.sock')

# Hardware-specific mpv options; override with MPV_ARGS in simpsonstv.conf.
DEFAULT_MPV_ARGS = (
    '--vo=gpu --gpu-context=drm --hwdec=auto-safe --video-rotate=270 '
    '--ao=alsa --audio-device=alsa/plughw:CARD=Headphones,DEV=0'
)


def ensure_dirs():
    os.makedirs(RUN_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)


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


def is_interstitial(path):
    return bool(path) and os.path.dirname(path) == INTERSTITIAL_DIR


def start():
    """Start mpv in idle mode and wait until it accepts commands."""
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)
    args = [
        'mpv',
        '--idle=yes',
        '--fullscreen',
        '--osd-level=0',
        '--input-terminal=no',
        '--msg-level=all=warn',
        '--input-ipc-server=' + SOCKET_PATH,
    ]
    args += shlex.split(os.environ.get('MPV_ARGS', DEFAULT_MPV_ARGS))
    process = subprocess.Popen(args)
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline and process.poll() is None:
        if ok(send('get_property', 'idle-active')):
            break
        time.sleep(0.2)
    return process


def send(*command):
    """Send one command to mpv.

    Returns mpv's reply as a dict, or None if mpv isn't running or didn't answer.
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


def load(path, start_at=None):
    """Replace whatever is playing with `path`, optionally starting part-way in."""
    send('set', 'start', 'none' if start_at is None else '%.2f' % start_at)
    return ok(send('loadfile', path, 'replace'))
