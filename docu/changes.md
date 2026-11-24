# Changes

## This version (Pi Zero 2 W)

- Runs on current **Raspberry Pi OS Lite** on a **Pi Zero 2 W**. The player is **mpv**, which replaces omxplayer (omxplayer only exists on the old Buster release).
- One installer (`install.sh`) and a settings file (`simpsonstv.conf`).
- Buttons rewritten with gpiozero. The power switch sets pause and mute explicitly, rewind can't go past the start, and the both-buttons shutdown works (hold for 3 seconds).
- Channel-change **static** plays when you press next, and a **CRT switch-off** plays before shutdown (`interstitials/`).
- Fixes: the random player picks up new videos; the playlist player no longer repeats the last video forever.
- Episodes are uploaded to a password-free **Samba network share** (`videos`), in one folder per show; the player finds episodes in subfolders.
- Removed: USB stick autocopy and its LED.

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
