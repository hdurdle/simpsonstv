"""Simpsons TV: live channels, power switch and VCR buttons.

- Each show folder in videos/ is a channel airing its episodes on a real-time
  schedule (see channels.py). Changing channel shows static, then joins
  whatever is on now.
- Power switch (GPIO26): on = picture and sound; off = sound off and playback
  stopped. The channels keep going, so switching back on rejoins them live.
- Right VCR button (GPIO6): channel up.  Left VCR button (GPIO5): channel down.
- Hold both VCR buttons for 3 seconds: CRT switch-off animation, then shut down.

Everything can also be driven from the command line with tvctl (tvctl.py),
which talks to this process over a control socket; see `tvctl help`.
"""
import json
import os
import random
import socket
import subprocess
import threading
import time

import channels
import mpvctl

POWER_SWITCH_PIN = 26    # switch to GND; closed = TV on
CHANNEL_UP_PIN = 6       # right VCR button to GND
CHANNEL_DOWN_PIN = 5     # left VCR button to GND
AMP_SHUTDOWN_PIN = 13    # PAM8302 SD pin: high = amplifier on
AUDIO_PWM_PIN = 19       # PWM audio output (set by the audremap overlay)

SHUTDOWN_HOLD_SECONDS = 3
POLL_SECONDS = 0.05
SYNC_SECONDS = 0.5       # how often to check the screen shows what's on air
RESCAN_SECONDS = 60      # how often to look for new or removed episodes
# Re-tune if playback is this far from the schedule. Generous, because tuning
# in starts at the keyframe before the scheduled point (mpv --hr-seek=no),
# which can be several seconds early on files with sparse keyframes.
DRIFT_SECONDS = 60

# Set POWER_SWITCH_INVERT=1 in simpsonstv.conf if the switch works backwards.
POWER_SWITCH_INVERT = os.environ.get('POWER_SWITCH_INVERT', '0') == '1'

STATE_FILE = os.path.join(mpvctl.CACHE_DIR, 'state.json')
DURATIONS_FILE = os.path.join(mpvctl.CACHE_DIR, 'durations.json')
CONTROL_SOCKET = os.path.join(mpvctl.RUN_DIR, 'control.sock')


def pinctrl(*args):
    subprocess.run(['pinctrl'] + [str(arg) for arg in args], check=False)


class TV:
    def __init__(self, amplifier, clock=time.time):
        self.amplifier = amplifier
        self.clock = clock
        self.lineup = []
        self.lineup_lock = threading.Lock()
        self.channel_name = self.load_state()
        self.power_on = False
        self.switch_on = None     # physical power switch position
        self.override = None      # True/False from `tvctl on/off`; None = follow the switch
        self.last_static = None
        self.clip_lengths = {}

    # --- remembered channel ---------------------------------------------

    @staticmethod
    def load_state():
        try:
            with open(STATE_FILE) as file:
                return json.load(file).get('channel')
        except (OSError, ValueError, AttributeError):
            return None

    def save_state(self):
        try:
            with open(STATE_FILE, 'w') as file:
                json.dump({'channel': self.channel_name}, file)
        except OSError as error:
            print('Could not save channel: %s' % error)

    # --- channel line-up ------------------------------------------------

    def scan_forever(self):
        """Background thread: rebuild the line-up from the video folder every minute."""
        cache = channels.DurationCache(DURATIONS_FILE)
        while True:
            try:
                lineup = channels.scan(mpvctl.VIDEO_DIR, cache)
            except Exception as error:  # keep the TV running whatever happens
                print('Scanning videos failed: %s' % error)
            else:
                with self.lineup_lock:
                    changed = [c.name for c in lineup] != [c.name for c in self.lineup] or \
                        [len(c.paths) for c in lineup] != [len(c.paths) for c in self.lineup]
                    self.lineup = lineup
                if changed:
                    print('Channels: ' + ('; '.join(
                        '%d %s' % (number, channel) for number, channel in enumerate(lineup, 1)) or 'none'))
            time.sleep(RESCAN_SECONDS)

    def current_channel(self, lineup=None):
        if lineup is None:
            with self.lineup_lock:
                lineup = self.lineup
        if not lineup:
            return None
        for channel in lineup:
            if channel.name == self.channel_name:
                return channel
        return lineup[0]  # remembered channel is gone (or first start)

    def change_channel(self, step):
        """Channel up (+1) or down (-1). Returns a description for tvctl."""
        with self.lineup_lock:
            lineup = self.lineup
        message = 'No channels yet'
        channel = None
        if lineup:
            current = self.current_channel(lineup)
            number = (lineup.index(current) + step) % len(lineup)
            channel = lineup[number]
            self.channel_name = channel.name
            self.save_state()
            message = 'Channel %d: %s' % (number + 1, self.channel_name)
            print(message)
        if self.power_on:
            self.play_static(then=channel)
        else:
            message += ' (TV is off)'
        return message

    # --- what's on screen -----------------------------------------------

    def clip_length(self, clip):
        if clip not in self.clip_lengths:
            self.clip_lengths[clip] = channels.probe_duration(clip) or 1.0
        return self.clip_lengths[clip]

    def play_static(self, then=None):
        """Play a burst of static. With a channel, queue that channel's
        programme straight after it, starting where it will be once the static
        ends, so there's no gap."""
        clips = mpvctl.static_clips()
        if not clips:
            if then is not None:
                mpvctl.play(then.upcoming(self.clock(), 2))
            else:
                mpvctl.send('stop')
            return
        choices = [clip for clip in clips if clip != self.last_static] or clips
        self.last_static = random.choice(choices)
        items = [(self.last_static, None)]
        if then is not None:
            items += then.upcoming(self.clock() + self.clip_length(self.last_static), 2)
        mpvctl.play(items)

    def sync(self):
        """Make the screen show what's on air now on the current channel."""
        if not self.power_on:
            return
        playing = mpvctl.get('path')  # None when mpv is idle
        if mpvctl.is_interstitial(playing):
            return  # static playing; the channel is queued after it
        channel = self.current_channel()
        if channel is None:
            if not playing:
                self.play_static()  # nothing to watch yet: snow
            return
        now = self.clock()
        episode, offset = channel.on_air(now)
        if playing == episode:
            position = mpvctl.get('time-pos')
            if position is None or abs(position - offset) < DRIFT_SECONDS:
                self.keep_next_queued(channel, now)
                return
        # Tune in, with the next episode queued so it follows on seamlessly.
        mpvctl.play(channel.upcoming(now, 2))

    @staticmethod
    def keep_next_queued(channel, now):
        """Once the last queued item is playing, queue the episode after it."""
        count = mpvctl.get('playlist-count')
        position = mpvctl.get('playlist-pos')
        if count is None or position is None or position < count - 1:
            return
        mpvctl.send('playlist-clear')  # drop played entries; keeps the current one
        mpvctl.send(*mpvctl.loadfile_command(channel.upcoming(now, 2)[1][0], 'append'))

    # --- power and shutdown ---------------------------------------------

    def wanted_power(self):
        return self.override if self.override is not None else bool(self.switch_on)

    def update_power(self, force=False):
        """Turn the TV on or off to match the switch, or the tvctl override."""
        wanted = self.wanted_power()
        if force or wanted != self.power_on:
            self.set_power(wanted)

    def set_power(self, on):
        self.power_on = on
        if on:
            print('TV on')
            pinctrl('set', AUDIO_PWM_PIN, 'a5')  # reconnect PWM audio
            self.amplifier.on()
            self.sync()
        else:
            print('TV off')
            mpvctl.send('stop')
            self.amplifier.off()
            pinctrl('set', AUDIO_PWM_PIN, 'ip')  # disconnect PWM audio to stop hiss

    def play_switch_off(self):
        """Play the CRT switch-off clip and wait for it to finish."""
        clip = mpvctl.interstitial('crt_off.mp4')
        if not clip:
            return
        # Hold the last (black) frame instead of going idle.
        mpvctl.send('set', 'keep-open', 'yes')
        if not mpvctl.load(clip):
            return
        time.sleep(0.3)  # let the clip start before checking for its end
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline and mpvctl.get('eof-reached') is not True:
            time.sleep(0.1)

    def test_switch_off(self):
        """Play the switch-off without powering off, then carry on watching."""
        self.play_switch_off()
        mpvctl.send('set', 'keep-open', 'no')
        mpvctl.send('stop')
        self.sync()

    def shutdown(self):
        print('Power off')
        if self.power_on:
            self.play_switch_off()
        subprocess.run(['systemctl', 'poweroff'], check=False)

    # --- tvctl commands ---------------------------------------------------

    def status(self):
        def on_off(value):
            return 'on' if value else 'off'
        source = 'tvctl override (tvctl auto to follow the switch)' if self.override is not None \
            else 'power switch'
        lines = ['Power:   %s, set by %s' % (on_off(self.power_on), source),
                 'Switch:  %s' % on_off(self.switch_on)]
        with self.lineup_lock:
            lineup = self.lineup
        channel = self.current_channel(lineup)
        if channel is None:
            lines.append('Channel: none (no videos found yet)')
        else:
            episode, offset = channel.on_air(self.clock())
            lines.append('Channel: %d %s' % (lineup.index(channel) + 1, channel.name))
            lines.append('On air:  %s, %d:%02d in' % (
                os.path.relpath(episode, mpvctl.VIDEO_DIR), offset // 60, offset % 60))
        playing = mpvctl.get('path')
        lines.append('Playing: %s' % (os.path.basename(playing) if playing else 'nothing'))
        lines.append('Channels:')
        for number, item in enumerate(lineup, 1):
            count = len(item.paths)
            lines.append('  %s %d %s (%d episode%s)' % (
                '>' if item is channel else ' ', number, item.name, count, '' if count == 1 else 's'))
        if not lineup:
            lines.append('  none')
        return '\n'.join(lines)

    def command(self, text):
        """Run a tvctl command. Returns (reply, action to run after replying)."""
        name = text.strip().lower()
        if name == 'on':
            self.override = True
            self.update_power()
            return 'TV on (power switch ignored until: tvctl auto)', None
        if name == 'off':
            self.override = False
            self.update_power()
            return 'TV off (power switch ignored until: tvctl auto)', None
        if name == 'auto':
            self.override = None
            self.update_power()
            return 'Following the power switch, which is %s' % ('on' if self.switch_on else 'off'), None
        if name in ('up', 'right'):
            return self.change_channel(+1), None
        if name in ('down', 'left'):
            return self.change_channel(-1), None
        if name == 'switchoff':
            if not self.power_on:
                return 'The TV is off; turn it on first (tvctl on)', None
            self.test_switch_off()
            return 'Played the switch-off; still running', None
        if name in ('shutdown', 'both'):
            return 'Shutting down', self.shutdown
        if name == 'status':
            return self.status(), None
        return 'Unknown command: %r (try: tvctl help)' % text.strip(), None


def open_control_socket():
    """Socket for tvctl, usable by the owner of the install folder (and root)."""
    if os.path.exists(CONTROL_SOCKET):
        os.remove(CONTROL_SOCKET)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(CONTROL_SOCKET)
    os.chown(CONTROL_SOCKET, os.stat(mpvctl.BASE_DIR).st_uid, -1)
    os.chmod(CONTROL_SOCKET, 0o600)
    server.listen(4)
    server.setblocking(False)
    return server


def serve_commands(server, tv):
    """Answer any waiting tvctl commands without blocking the button loop."""
    while True:
        try:
            connection, _ = server.accept()
        except (BlockingIOError, InterruptedError):
            return
        after = None
        with connection:
            try:
                connection.settimeout(2)
                text = connection.recv(1024).decode('utf-8', 'replace')
                print('tvctl: ' + text.strip())
                reply, after = tv.command(text)
                connection.sendall((reply + '\n').encode('utf-8'))
            except OSError as error:
                print('tvctl connection failed: %s' % error)
        if after:
            after()


def main():
    from gpiozero import Button, OutputDevice

    power_switch = Button(POWER_SWITCH_PIN, pull_up=True)
    up_button = Button(CHANNEL_UP_PIN, pull_up=True)
    down_button = Button(CHANNEL_DOWN_PIN, pull_up=True)
    amplifier = OutputDevice(AMP_SHUTDOWN_PIN, initial_value=False)

    mpvctl.ensure_dirs()
    tv = TV(amplifier)
    threading.Thread(target=tv.scan_forever, daemon=True).start()
    control = open_control_socket()

    mpv = None
    up_was_pressed = False
    down_was_pressed = False
    both_pressed_since = None
    combo_used = False  # both buttons were pressed together; ignore the releases
    last_sync = 0.0
    first_pass = True

    while True:
        now = time.monotonic()

        if mpv is None or mpv.poll() is not None:
            if mpv is not None:
                print('mpv stopped (exit code %s); restarting' % mpv.returncode)
                time.sleep(2)
            mpv = mpvctl.start()
            last_sync = 0.0

        tv.switch_on = power_switch.is_pressed != POWER_SWITCH_INVERT
        tv.update_power(force=first_pass)  # follows the switch unless tvctl overrides it
        first_pass = False

        serve_commands(control, tv)

        up_pressed = up_button.is_pressed
        down_pressed = down_button.is_pressed

        if up_pressed and down_pressed:
            combo_used = True
            if both_pressed_since is None:
                both_pressed_since = now
            elif now - both_pressed_since >= SHUTDOWN_HOLD_SECONDS:
                tv.shutdown()
                return
        else:
            both_pressed_since = None

        # Single-button actions fire on release.
        if not combo_used:
            if up_was_pressed and not up_pressed:
                tv.change_channel(+1)
            if down_was_pressed and not down_pressed:
                tv.change_channel(-1)
        if not up_pressed and not down_pressed:
            combo_used = False
        up_was_pressed = up_pressed
        down_was_pressed = down_pressed

        if now - last_sync >= SYNC_SECONDS:
            tv.sync()
            last_sync = now

        time.sleep(POLL_SECONDS)


if __name__ == '__main__':
    main()
