#!/usr/bin/env python3
"""tvctl: control the Simpsons TV from the command line, e.g. over SSH.

Commands:
  on          turn the TV on, ignoring the power switch (until: tvctl auto)
  off         turn the TV off, ignoring the power switch (until: tvctl auto)
  auto        follow the physical power switch again
  up, right   channel up    (right VCR button)
  down, left  channel down  (left VCR button)
  switchoff   play the CRT switch-off, then carry on (no power-off; for testing)
  shutdown    switch-off, then power off the Pi (both VCR buttons held)
  status      power, switch, current channel, what's on air, channel list
  crt on|off  turn the CRT look (scanlines, rounded corners) on or off

The power and CRT overrides last until the service restarts (tvctl auto
hands power back to the switch sooner).
"""
import os
import socket
import sys

SOCKET_PATH = os.path.join(os.environ.get('SIMPSONSTV_RUN_DIR', '/run/simpsonstv'), 'control.sock')
COMMANDS = {'on', 'off', 'auto', 'up', 'right', 'down', 'left', 'switchoff', 'shutdown', 'both',
            'status', 'crt', 'crt on', 'crt off'}


def main(argv):
    if not argv or argv[0] in ('help', '-h', '--help'):
        print(__doc__.strip())
        return 0 if argv else 2
    command = ' '.join(argv).lower()
    if command not in COMMANDS:
        print('Unknown command: %s\n\n%s' % (' '.join(argv), __doc__.strip()), file=sys.stderr)
        return 2
    if command in ('shutdown', 'both') and sys.stdin.isatty():
        if input('Shut down the Pi? [y/N] ').strip().lower() not in ('y', 'yes'):
            print('Cancelled.')
            return 1

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(15)  # switchoff waits for the animation
            sock.connect(SOCKET_PATH)
            sock.sendall((command + '\n').encode('utf-8'))
            reply = b''
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                reply += chunk
    except FileNotFoundError:
        print('The TV service isn\'t running. Check: sudo systemctl status simpsonstv', file=sys.stderr)
        return 1
    except PermissionError:
        print('No permission to control the TV. Run tvctl as the user that owns the simpsonstv '
              'folder, or with sudo.', file=sys.stderr)
        return 1
    except OSError as error:
        print('Could not reach the TV service: %s' % error, file=sys.stderr)
        return 1
    print(reply.decode('utf-8', 'replace').rstrip())
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
