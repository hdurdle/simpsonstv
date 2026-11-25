# Changes

## This version (Pi Zero 2 W)

- Runs on current **Raspberry Pi OS Lite** on a **Pi Zero 2 W**. The player is **mpv**, which replaces omxplayer (omxplayer only exists on the old Buster release).
- One installer (`install.sh`), one service (`simpsonstv`) and a settings file (`simpsonstv.conf`).
- **Live channels** (`tv.py`, `channels.py`): each show folder is a channel airing its episodes in order on a real-time schedule. Changing channel joins whatever is on now. The TV remembers its channel.
- **Controls:** the VCR buttons are channel up and down. The power switch turns sound and picture off while the channels keep going. Holding both buttons for 3 seconds shuts down.
- **CRT look** (`crt.py`): a see-through overlay that adds scanlines, a phosphor grille, a vignette, glare and rounded corners. It's sized to the picture, adjustable in `simpsonstv.conf`, and switched with `tvctl crt on/off`.
- **`tvctl`** command-line control (test mode): power on/off (overriding the switch), channel up/down, test switch-off, shutdown and status, over SSH.
- Channel-change **static** plays between channels, and a **CRT switch-off** plays before shutdown (`interstitials/`).
- Episodes are uploaded to a **Samba network share** (`videos`, login `tv` with a password chosen at install), in one folder per show.
- Removed: USB stick autocopy and its LED; the random and playlist players (`player.py`, `player-playlist.py`) and rewind, all replaced by live channels.

## johnyHV's version

My changes, all tested on the RPI ZERO:
- added pause video, when is button not pulled.
- added mute audio amplifier if is button not pulled
- minor improvements to 3D models
- added button to 3D model VCR
- used different speaker
- design improvement. is more solid
- added space for USB port in the 3D model, and script for autocopy movie from USB mass storage devices to RPI 
- added feature "next movie" for right button on the VCR
- added feature rewid 15second back for the left button on the VCR
- added usb A connector for autocopy movie from USB flash drive to micro SD card
- new scriprt and service for autocopy movie from USB stick to micro SD card
- added second player script player-playlist.py. This script saving last played video, and after reboot can continue playing last video 

### TODO (johnyHV)
- add continue playing the last movie

### Old SD card image

The old RPI ZERO image on my [gdrive](https://drive.google.com/drive/folders/1mnJnrXVBaZO_8UrxD8tn1eNyA690npIP?usp=sharing) is Raspberry Pi OS Buster with omxplayer. It doesn't match the current code and isn't tested on the Zero 2 W; follow the [README](../README.md) instead.

- OS: raspberry-pi OS 32bit
- username: pi
- password: raspberry
