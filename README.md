# Simpsons TV (Raspberry Pi Zero 2 W)

A tiny TV that works like an old analogue set. Each show is a **channel** that keeps airing in real time, whether you're watching it or not. Press the VCR buttons to flick through channels (with static), and hold both to switch off with an old CRT "dot" effect.

This version runs on a **Raspberry Pi Zero 2 W** with current **Raspberry Pi OS Lite**, using **mpv** to play the videos.

- **Building the TV** (parts, 3D model, wiring): [docu/hardware.md](docu/hardware.md)
- **What's changed** from earlier versions: [docu/changes.md](docu/changes.md)

Credits: the original project is by buba447 ([build guide](https://withrow.io/simpsons-tv-build-guide), [source](https://github.com/buba447/simpsonstv), [3D model](https://www.thingiverse.com/thing:4943159)). The 3D model for the 4" Waveshare HDMI display is [here](https://www.thingiverse.com/thing:5019648). johnyHV added the VCR buttons and more ([source](https://github.com/johnyHV/simpsonstv), [video](https://www.youtube.com/watch?v=3tjLVFxXQzM)).

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

- installs **mpv**, **ffmpeg** (to read episode lengths) and the GPIO libraries (**gpiozero**, **lgpio**)
- turns on **PWM audio** on GPIO18/19 in `/boot/firmware/config.txt`
- sets the **LCD mode** (480×800) and hides the text console in `/boot/firmware/cmdline.txt`. Both files are backed up first, next to the originals.
- creates `~/simpsonstv/simpsonstv.conf` with the default settings
- installs and starts the **simpsonstv** service, which runs at every boot
- installs **Samba** and shares the `videos` folder on your network as `videos`, **with no password** (see the next step). `/etc/samba/smb.conf` is backed up first.

It's safe to run again (for example after `git pull`); changes it has already made aren't repeated.

## 5. Add videos

**Convert** your videos to mp4 on your computer (it's much faster than on the Pi). `videos/encode.py` needs [ffmpeg](https://ffmpeg.org/) installed. It converts every video in the `videos` folder to 480p H.264 in `videos/encoded/`:

```
cd videos
python3 encode.py
```

**Upload** them to the TV's network share, in **one folder per show**. Each show folder becomes a channel. Season folders inside a show are fine, and episodes play in name order, so name them so they sort correctly (`S01E01`, `S01E02`, …):

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

New shows and episodes appear automatically within a couple of minutes; no restart needed. Files still being copied are left out until they've finished.

**The share has no password.** Anyone on your local network can add, rename and delete episodes. It only accepts connections from private (home network) addresses, never from the internet.

**Windows 11 says "You can't access this shared folder" or asks for a password:** Windows blocks password-free shares by default. To allow them, run this once in PowerShell as administrator:

```
Set-SmbClientConfiguration -EnableInsecureGuestLogons $true -RequireSecuritySignature $false
```

This setting applies to every share that PC connects to, not just the TV's. If you'd rather not change it, copy files with `scp` or WinSCP instead (`scp *.mp4 <username>@<hostname>.local:"~/simpsonstv/videos/The Simpsons/"`).

## 6. Settings

Settings are in `~/simpsonstv/simpsonstv.conf`. After changing it, run:

```
sudo systemctl restart simpsonstv
```

| Setting | What it does |
|---|---|
| `MPV_ARGS` | Display and audio options for mpv: rotation, video output, sound card. See *Troubleshooting* below. |
| `POWER_SWITCH_INVERT` | Set to `1` if the TV plays when switched off. |

---

## Channels

The TV behaves like analogue broadcast TV:

- **Every show folder is a channel**, numbered in name order. Episodes loose in `videos/` itself form a channel called *Mixed*.
- **Channels air live.** Each one plays its episodes in order and loops, on a schedule based on the real time. Changing channel drops you into whatever is on now, part-way through. Come back later and the show has moved on.
- **Each channel is at a different point** in its run, so they don't all change episode together.
- **The TV remembers its channel** after a reboot.
- **No videos yet** (or while the first scan is still running) shows snow, like an untuned channel.

Things to know:

- The schedule depends on the Pi's clock, which it sets from the internet at startup. Without a network the channels still play, just at a different point.
- Adding or removing episodes changes that show's schedule, so the channel jumps to a different point.
- The first scan reads every episode's length with `ffprobe`, which takes a moment per episode on a Pi Zero; you'll see snow until it's done. Lengths are saved in `cache/`, so later startups are quick.

## Controls

| Control | GPIO | What it does |
|---|---|---|
| Power switch | 26 | **On:** picture and sound, tuned to whatever is on now. **Off:** sound off and playback stopped; the channels carry on without you. |
| Right VCR button | 6 | **Channel up**, with a short burst of static. Flick quickly for continuous static. |
| Left VCR button | 5 | **Channel down**, with static. |
| Both VCR buttons, held 3 seconds | 5 + 6 | Plays the **CRT switch-off**, then **shuts down**. With the TV switched off it shuts down straight away. Wait for the Pi to finish shutting down before unplugging it. |

The audio amplifier uses GPIO19 (audio) and GPIO13 (mute). Wiring details are in [docu/hardware.md](docu/hardware.md).

## Static and switch-off clips

The channel-change static (`interstitials/static_*.mp4`) and the switch-off (`interstitials/crt_off.mp4`) are included. To change them, run `interstitials/make_interstitials.py` on your computer (needs ffmpeg, numpy and Pillow). `--help` lists the options, such as more variants, the maximum length, or the full 800 px screen width.

## Troubleshooting

See what's happening:

```
journalctl -u simpsonstv -f
```

The log lists the channels after each scan and every channel change.

- **Black screen:** check the screen's modes with `cat /sys/class/drm/card*-HDMI-A-1/modes`. If mpv reports errors, change `--vo=gpu --gpu-context=drm` to `--vo=drm` in `MPV_ARGS`.
- **Picture upside down:** change `--video-rotate=270` to `--video-rotate=90`.
- **Picture partly hidden by the case:** add, for example, `--video-margin-ratio-right=0.0625` to `MPV_ARGS`.
- **No sound:** find the card name with `aplay -l`, and test with `speaker-test -D plughw:CARD=Headphones -c 1 -t sine`.
- **Power switch works backwards:** set `POWER_SWITCH_INVERT=1`.
- **Only snow, or "Channels: none" in the log:** check that the mp4 files are in show folders in `~/simpsonstv/videos`, that the copy finished more than a minute ago, and that `ffprobe <file>` can read them.
- **Can't connect to the share:** check Samba is running with `systemctl status smbd`, and see the Windows 11 note in step 5. If your computer is on an unusual network range, adjust `hosts allow` in the `simpsonstv` block of `/etc/samba/smb.conf`, then run `sudo systemctl restart smbd`.

## Updating

```
cd ~/simpsonstv
git pull
sudo ./install.sh
sudo systemctl restart simpsonstv
```
