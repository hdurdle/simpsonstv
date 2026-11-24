# Simpsons TV (Raspberry Pi Zero 2 W)

A tiny TV that plays episodes on a loop. Flick the power switch to pause, press the VCR buttons to change channel (with static) or rewind, and hold both to switch off with an old CRT "dot" effect.

This version runs on a **Raspberry Pi Zero 2 W** with current **Raspberry Pi OS Lite**, using **mpv** to play the videos.

- **Building the TV** (parts, 3D model, wiring): [docu/hardware.md](docu/hardware.md)
- **What's changed** from earlier versions: [docu/changes.md](docu/changes.md)

Credits: the original project is by buba447 ([build guide](https://withrow.io/simpsons-tv-build-guide), [source](https://github.com/buba447/simpsonstv), [3D model](https://www.thingiverse.com/thing:4943159)). The 3D model for the 4" Waveshare HDMI display is [here](https://www.thingiverse.com/thing:5019648). johnyHV added the VCR buttons, the playlist player and more ([source](https://github.com/johnyHV/simpsonstv), [video](https://www.youtube.com/watch?v=3tjLVFxXQzM)).

---

## 1. Which OS to install

Install **Raspberry Pi OS Lite (32-bit)**. That's the current release with no desktop.

- **Lite:** the TV doesn't need a desktop, and leaving it out saves memory and boot time on the Zero 2 W.
- **32-bit:** it uses less memory than 64-bit, which matters with 512 MB. 64-bit also works.
- **Not "Legacy" / Buster:** the older versions of this project used omxplayer, which only runs on Raspberry Pi OS Buster. Buster no longer gets updates, and this version doesn't need it.

## 2. Write the SD card

Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/):

1. **Device:** Raspberry Pi Zero 2 W
2. **OS:** Raspberry Pi OS (other) → **Raspberry Pi OS Lite (32-bit)**
3. **Storage:** your micro SD card
4. When asked, choose **Edit settings** and set:
   - a **hostname** (for example `simpsonstv`)
   - a **username and password**; any username works
   - your **Wi-Fi** network and **Wi-Fi country**
   - on the **Services** tab, **enable SSH**

Older guides say to put `wpa_supplicant.conf` and `ssh` files on the boot partition. That no longer works; use the Imager settings instead.

## 3. First boot and update

Put the card in the Pi and power it on. The first boot takes a few minutes. Then connect from your computer:

```
ssh <username>@<hostname>.local
```

Update everything and reboot:

```
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

Don't run `rpi-update`; it installs pre-release firmware.

## 4. Install the TV software

```
sudo apt install -y git
git clone https://github.com/hdurdle/simpsonstv.git ~/simpsonstv
cd ~/simpsonstv
sudo ./install.sh
sudo reboot
```

Until [PR #1](https://github.com/hdurdle/simpsonstv/pull/1) is merged, the new code is on a branch, so clone with `git clone -b pi-zero-2w-mpv ...` instead.

`install.sh` asks before changing anything. It:

- installs **mpv** and the GPIO libraries (**gpiozero**, **lgpio**)
- turns on **PWM audio** on GPIO18/19 in `/boot/firmware/config.txt`
- sets the **LCD mode** (480×800) and hides the text console in `/boot/firmware/cmdline.txt`. Both files are backed up first, next to the originals.
- creates `~/simpsonstv/simpsonstv.conf` with the default settings
- installs and starts the **tvplayer** and **tvbutton** services, which run at every boot
- installs **Samba** and shares the `videos` folder on your network as `videos`, **with no password** (see the next step). `/etc/samba/smb.conf` is backed up first.

It's safe to run again (for example after `git pull`); changes it has already made aren't repeated.

## 5. Add videos

**Convert** your videos to mp4 on your computer (it's much faster than on the Pi). `videos/encode.py` needs [ffmpeg](https://ffmpeg.org/) installed. It converts every video in the `videos` folder to 480p H.264 in `videos/encoded/`:

```
cd videos
python3 encode.py
```

**Upload** them to the TV's network share, in **one folder per show**. Season folders inside a show are fine too:

```
videos
├── The Simpsons
│   ├── S01E01.mp4
│   └── S01E02.mp4
└── Futurama
    └── S01E01.mp4
```

Open the share from your computer:

- **Windows:** in File Explorer's address bar, type `\\<hostname>.local\videos` (for example `\\simpsonstv.local\videos`).
- **Mac:** in Finder, choose *Go → Connect to Server*, enter `smb://<hostname>.local/videos`, and connect as **Guest**.
- **Linux:** `smb://<hostname>.local/videos` in your file manager.

New episodes are picked up automatically; no restart needed. If the TV reaches an episode that's still copying, it may skip it or stop early.

**The share has no password.** Anyone on your local network can add, rename and delete episodes. It only accepts connections from private (home network) addresses, never from the internet.

**Windows 11 says "You can't access this shared folder" or asks for a password:** Windows blocks password-free shares by default. To allow them, run this once in PowerShell as administrator:

```
Set-SmbClientConfiguration -EnableInsecureGuestLogons $true -RequireSecuritySignature $false
```

This setting applies to every share that PC connects to, not just the TV's. If you'd rather not change it, copy files with `scp` or WinSCP instead (`scp *.mp4 <username>@<hostname>.local:"~/simpsonstv/videos/The Simpsons/"`).

## 6. Settings

Settings are in `~/simpsonstv/simpsonstv.conf`. After changing it, run:

```
sudo systemctl restart tvbutton tvplayer
```

| Setting | What it does |
|---|---|
| `PLAYER_SCRIPT` | `player.py` plays all shows mixed together in random order (default). `player-playlist.py` plays show by show, in name order, and continues from the last episode after a reboot. |
| `MPV_ARGS` | Display and audio options for mpv: rotation, video output, sound card. See *Troubleshooting* below. |
| `POWER_SWITCH_INVERT` | Set to `1` if the TV plays when switched off. |

---

## Controls

| Control | GPIO | What it does |
|---|---|---|
| Power switch | 26 | **On:** plays with sound. **Off:** pauses and mutes the amplifier. |
| Right VCR button | 6 | **Next video**, after a short burst of channel-change static. Press again during the static for more static, like flicking channels. With the TV switched off it skips without static. |
| Left VCR button | 5 | **Rewind** 15 seconds. |
| Both VCR buttons, held 3 seconds | 5 + 6 | Plays the **CRT switch-off**, then **shuts down**. With the TV switched off it shuts down straight away. Wait for the Pi to finish shutting down before unplugging it. |

The audio amplifier uses GPIO19 (audio) and GPIO13 (mute). Wiring details are in [docu/hardware.md](docu/hardware.md).

## Static and switch-off clips

The channel-change static (`interstitials/static_*.mp4`) and the switch-off (`interstitials/crt_off.mp4`) are included. To change them, run `interstitials/make_interstitials.py` on your computer (needs ffmpeg, numpy and Pillow). `--help` lists the options, such as more variants, the maximum length, or the full 800 px screen width.

## Troubleshooting

See what's happening:

```
journalctl -u tvplayer -f
journalctl -u tvbutton -f
```

- **Black screen:** check the screen's modes with `cat /sys/class/drm/card*-HDMI-A-1/modes`. If mpv reports errors, change `--vo=gpu --gpu-context=drm` to `--vo=drm` in `MPV_ARGS`.
- **Picture upside down:** change `--video-rotate=270` to `--video-rotate=90`.
- **Picture partly hidden by the case:** add, for example, `--video-margin-ratio-right=0.0625` to `MPV_ARGS`.
- **No sound:** find the card name with `aplay -l`, and test with `speaker-test -D plughw:CARD=Headphones -c 1 -t sine`.
- **Power switch works backwards:** set `POWER_SWITCH_INVERT=1`.
- **"No videos found" in the log:** check that the mp4 files are in `~/simpsonstv/videos` or one of its show folders.
- **Can't connect to the share:** check Samba is running with `systemctl status smbd`, and see the Windows 11 note in step 5. If your computer is on an unusual network range, adjust `hosts allow` in the `simpsonstv` block of `/etc/samba/smb.conf`, then run `sudo systemctl restart smbd`.

## Updating

```
cd ~/simpsonstv
git pull
sudo ./install.sh
sudo systemctl restart tvbutton tvplayer
```
