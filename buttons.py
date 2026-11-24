"""Power switch and VCR buttons.

- Power switch (GPIO26): on = play with sound, off = pause and mute the amplifier.
- Right VCR button (GPIO6): next video.
- Left VCR button (GPIO5): rewind 15 seconds.
- Hold both VCR buttons for 3 seconds: shut down.
"""
import os
import subprocess
import time

from gpiozero import Button, OutputDevice

import mpvctl

POWER_SWITCH_PIN = 26    # switch to GND; closed = TV on
NEXT_BUTTON_PIN = 6      # right VCR button to GND
REWIND_BUTTON_PIN = 5    # left VCR button to GND
AMP_SHUTDOWN_PIN = 13    # PAM8302 SD pin: high = amplifier on
AUDIO_PWM_PIN = 19       # PWM audio output (set by the audremap overlay)

REWIND_SECONDS = 15
SHUTDOWN_HOLD_SECONDS = 3
POLL_SECONDS = 0.05
# Re-send the pause state this often, so a video that starts while the
# switch is being flipped still ends up in the right state.
REASSERT_SECONDS = 2

# Set POWER_SWITCH_INVERT=1 in simpsonstv.conf if the switch works backwards.
POWER_SWITCH_INVERT = os.environ.get('POWER_SWITCH_INVERT', '0') == '1'

power_switch = Button(POWER_SWITCH_PIN, pull_up=True)
next_button = Button(NEXT_BUTTON_PIN, pull_up=True)
rewind_button = Button(REWIND_BUTTON_PIN, pull_up=True)
amplifier = OutputDevice(AMP_SHUTDOWN_PIN, initial_value=False)


def pinctrl(*args):
    subprocess.run(['pinctrl'] + [str(arg) for arg in args], check=False)


def set_paused(paused):
    if paused:
        open(mpvctl.PAUSE_FLAG, 'w').close()
    elif os.path.exists(mpvctl.PAUSE_FLAG):
        os.remove(mpvctl.PAUSE_FLAG)
    mpvctl.send('set_property', 'pause', paused)


def turn_on():
    print('TV on')
    pinctrl('set', AUDIO_PWM_PIN, 'a5')  # reconnect PWM audio
    set_paused(False)
    amplifier.on()


def turn_off():
    print('TV off')
    set_paused(True)
    amplifier.off()
    pinctrl('set', AUDIO_PWM_PIN, 'ip')  # disconnect PWM audio to stop hiss


def play_next_video():
    print('Next video')
    mpvctl.send('quit')  # the player script moves on to the next video


def rewind_video():
    print('Rewind %d seconds' % REWIND_SECONDS)
    mpvctl.send('seek', -REWIND_SECONDS, 'relative')


def shutdown_system():
    print('Power off')
    subprocess.run(['systemctl', 'poweroff'], check=False)


def main():
    mpvctl.ensure_run_dir()
    tv_on = None
    next_was_pressed = False
    rewind_was_pressed = False
    both_pressed_since = None
    combo_used = False  # both buttons were pressed together; ignore the releases
    last_reassert = 0.0

    while True:
        now = time.monotonic()

        switch_on = power_switch.is_pressed != POWER_SWITCH_INVERT
        if switch_on != tv_on:
            tv_on = switch_on
            turn_on() if tv_on else turn_off()
            last_reassert = now
        elif now - last_reassert >= REASSERT_SECONDS:
            mpvctl.send('set_property', 'pause', not tv_on)
            last_reassert = now

        next_pressed = next_button.is_pressed
        rewind_pressed = rewind_button.is_pressed

        if next_pressed and rewind_pressed:
            combo_used = True
            if both_pressed_since is None:
                both_pressed_since = now
            elif now - both_pressed_since >= SHUTDOWN_HOLD_SECONDS:
                shutdown_system()
                return
        else:
            both_pressed_since = None

        # Single-button actions fire on release, like the original script.
        if not combo_used:
            if next_was_pressed and not next_pressed:
                play_next_video()
            if rewind_was_pressed and not rewind_pressed:
                rewind_video()
        if not next_pressed and not rewind_pressed:
            combo_used = False

        next_was_pressed = next_pressed
        rewind_was_pressed = rewind_pressed
        time.sleep(POLL_SECONDS)


if __name__ == '__main__':
    main()
