"""Simpsons TV: live channels, power switch and VCR buttons.

- Each show folder in videos/ is a channel airing its episodes on a real-time
  schedule (see channels.py). Changing channel shows static, then joins
  whatever is on now.
- Power switch (GPIO26): on = picture and sound; off = sound off and playback
  stopped. The channels keep going, so switching back on rejoins them live.
- Right VCR button (GPIO6): channel up.  Left VCR button (GPIO5): channel down.
- Hold both VCR buttons for 3 seconds: CRT switch-off animation, then shut down.
"""
import json
import os
import random
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
SYNC_SECONDS = 1         # how often to check the screen shows what's on air
RESCAN_SECONDS = 60      # how often to look for new or removed episodes
DRIFT_SECONDS = 15       # re-tune if playback is this far from the schedule

# Set POWER_SWITCH_INVERT=1 in simpsonstv.conf if the switch works backwards.
POWER_SWITCH_INVERT = os.environ.get('POWER_SWITCH_INVERT', '0') == '1'

STATE_FILE = os.path.join(mpvctl.CACHE_DIR, 'state.json')
DURATIONS_FILE = os.path.join(mpvctl.CACHE_DIR, 'durations.json')


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
        self.last_static = None

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
        with self.lineup_lock:
            lineup = self.lineup
        if lineup:
            current = self.current_channel(lineup)
            number = (lineup.index(current) + step) % len(lineup)
            self.channel_name = lineup[number].name
            self.save_state()
            print('Channel %d: %s' % (number + 1, self.channel_name))
        if self.power_on:
            self.play_static()  # sync() tunes in once the static ends

    # --- what's on screen -----------------------------------------------

    def play_static(self):
        clips = mpvctl.static_clips()
        if not clips:
            mpvctl.send('stop')
            return
        choices = [clip for clip in clips if clip != self.last_static] or clips
        self.last_static = random.choice(choices)
        mpvctl.load(self.last_static)

    def sync(self):
        """Make the screen show what's on air now on the current channel."""
        if not self.power_on:
            return
        playing = mpvctl.get('path')  # None when mpv is idle
        if mpvctl.is_interstitial(playing):
            return  # static still playing; tune in when it ends
        channel = self.current_channel()
        if channel is None:
            if not playing:
                self.play_static()  # nothing to watch yet: snow
            return
        episode, offset = channel.on_air(self.clock())
        if playing == episode:
            position = mpvctl.get('time-pos')
            if position is None or abs(position - offset) < DRIFT_SECONDS:
                return
        mpvctl.load(episode, start_at=offset)

    # --- power and shutdown ---------------------------------------------

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

    def shutdown(self):
        print('Power off')
        if self.power_on:
            self.play_switch_off()
        subprocess.run(['systemctl', 'poweroff'], check=False)


def main():
    from gpiozero import Button, OutputDevice

    power_switch = Button(POWER_SWITCH_PIN, pull_up=True)
    up_button = Button(CHANNEL_UP_PIN, pull_up=True)
    down_button = Button(CHANNEL_DOWN_PIN, pull_up=True)
    amplifier = OutputDevice(AMP_SHUTDOWN_PIN, initial_value=False)

    mpvctl.ensure_dirs()
    tv = TV(amplifier)
    threading.Thread(target=tv.scan_forever, daemon=True).start()

    mpv = None
    up_was_pressed = False
    down_was_pressed = False
    both_pressed_since = None
    combo_used = False  # both buttons were pressed together; ignore the releases
    last_sync = 0.0
    switch_was_on = None

    while True:
        now = time.monotonic()

        if mpv is None or mpv.poll() is not None:
            if mpv is not None:
                print('mpv stopped (exit code %s); restarting' % mpv.returncode)
                time.sleep(2)
            mpv = mpvctl.start()
            last_sync = 0.0

        switch_on = power_switch.is_pressed != POWER_SWITCH_INVERT
        if switch_on != switch_was_on:
            switch_was_on = switch_on
            tv.set_power(switch_on)

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
