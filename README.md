
The original project was created by the user buba447. Manual is [here](https://withrow.io/simpsons-tv-build-guide) and source is [here](https://github.com/buba447/simpsonstv). Original 3D model is [here](https://www.thingiverse.com/thing:4943159)

Second user created new 3D model for 4" Waveshare HDMI display. Original 3D model is [here](https://www.thingiverse.com/thing:5019648)

Presentation video is [here](https://www.youtube.com/watch?v=3tjLVFxXQzM)

---
# Manual Content
1. [ My changes ](#my_changes)
2. [ 3D model ](#3d_model)
3. [ HW parts ](#hw_parts)
4. [ HW construction ](#hw_construction)
5. [ Instalation ](#instalation)
6. [ Image ](#images_url)
7. [ How to use ](#howtouse)

---
<a name="my_changes"></a>
# My changes

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

# TODO
- add continue playing the last movie

---
<a name="3d_model"></a>
# 3D model

My 3D model is stored on the [Printables](https://www.prusaprinters.org/prints/90361-simpsons-tv) page

---
<a name="hw_parts"></a>
# HW parts

- 1k potentiometer [here](https://www.tme.eu/en/details/pc16bu-1k-lin/cond-plastic-single-turn-potentiometers/omeg/)
<img src="docu/HW_parts/potentiometer.jpg" width="256"/>

- 7x7mm switch [here](https://www.aliexpress.com/item/32704922363.html)
<img src="docu/HW_parts/switch_7x7.jpg" width="256"/>

- 4" HDMI Waveshare LCD 800x400 [here](https://rlx.sk/sk/9-5-lcd-display/5454-4inch-hdmi-lcd-800480-ips-waveshare-4-touch-screen-lcd-hdmi-interface-ips-screen-designed-for-raspberry-pi-12030.html)
<img src="docu/HW_parts/lcd.jpg" width="256"/>

- HDMI connector DIY [here](https://rpishop.cz/redukce/2176-waveshare-mini-hdmi-adapter-pro-diy-hdmi-kabel.html)
<img src="docu/HW_parts/HDMI_connector.jpg" width="256"/>

- MINI HDMI connector DIY [here](https://rpishop.cz/redukce/1205-waveshare-hdmi-adapter-pro-diy-hdmi-kabel-pravouhy.html)
<img src="docu/HW_parts/micro_hdmi_connector.jpg" width="256"/>

- HDMI cable DIY [here](https://rpishop.cz/hdmi/1209-waveshare-diy-hdmi-plochy-kabel-02m.html)
<img src="docu/HW_parts/hdmi_cable.jpg" width="256"/>
<img src="docu/HW_parts/hdmi_final.jpg" width="256"/>

- speaker [here](https://rpishop.cz/reproduktory/1204-waveshare-8-5w-reproduktor.html)
<img src="docu/HW_parts/speaker.jpg" width="256"/>

- rpi zero [here](https://rpishop.cz/zero/632-raspberry-pi-zero.html)
<img src="docu/HW_parts/RASP_PI_ZERO_00.png" width="256"/>

- audio amplifier PAM8302 [here](https://rlx.sk/sk/audio-voice-boards-speech-recognition/3397-mono-25w-class-d-audio-amplifier-pam8302-adafruit-2130.html)
<img src="docu/HW_parts/audio_amplifier.jpg" width="256"/>

- capacitor 2.2uF/50V
<img src="docu/HW_parts/capacitor.jpg" width="256"/>

- screw M3 4x
<img src="docu/HW_parts/screw.jpg" width="256"/>

- switch 6x6mm 2x [here](https://www.tme.eu/en/details/tact-64k/microswitches-tact/ninigi/) **watch out for the length of the button**
<img src="docu/HW_parts/button.jpg" width="256"/>

- micro USB connector [here](https://www.aliexpress.com/item/32916571891.html?spm=a2g0o.productlist.0.0.284c68canDNCGE&algo_pvid=d8468b46-a429-405d-a448-26761076313c&algo_exp_id=d8468b46-a429-405d-a448-26761076313c-5&pdp_ext_f=%7B%22sku_id%22%3A%2266023288418%22%7D)
<img src="docu/HW_parts/micro_usb.jpg" width="256"/>

- PCB with micro USB connector [here](https://www.aliexpress.com/item/4000484202812.html?spm=a2g0o.productlist.0.0.52451297eW2VB6&algo_pvid=d8623308-0e8e-433a-b8c3-d0a98947ac72&aem_p4p_detail=202111260636579663439259216280013679493&algo_exp_id=d8623308-0e8e-433a-b8c3-d0a98947ac72-9&pdp_ext_f=%7B%22sku_id%22%3A%2210000002007513401%22%7D)
<img src="docu/HW_parts/microUSB.jpg" width="256"/>

- magnet circle 6x2mm
<img src="docu/HW_parts/magnet.jpg" width="256"/>

- 3mm LED
<img src="docu/HW_parts/led.jpg" width="256"/>

- USB A connector [here](https://www.aliexpress.com/item/4000806581109.html?spm=a2g0o.productlist.0.0.2c402a18K0POfK&algo_pvid=fe076f0d-f35f-4749-a6fb-6e73d8c0a93d&algo_exp_id=fe076f0d-f35f-4749-a6fb-6e73d8c0a93d-11&pdp_ext_f=%7B%22sku_id%22%3A%2210000008096938788%22%7D)
<img src="docu/HW_parts/usbA.jpg" width="256"/>

- Wires
<img src="docu/HW_parts/wires.jpg" width="256"/>

- long pin header 25mm, male, 2.54MM PITCH [here](https://www.aliexpress.com/item/32851444441.html)
<img src="docu/HW_parts/pin_header.jpg" width="256"/>

---
<a name="hw_construction"></a>
# HW construction

Approximate schematic. Missing USB and LCD parts
<img src="docu/block schematic_schem.png" width="768"/>
<img src="docu/block schematic_bb.png" width="768"/>

## Pinout
<img src="docu/RPIpinout.jpg" width="768"/>

Power switch
```
POWER SWITCH PIN A -> GPIO26
POWER SWITCH PIN B -> GND
```
Audio amplifier
```
AUDIO AMPLIFIER SIGNAL -> GPIO19
AUDIO AMPLIFIER SHUT DOWN -> GPIO13
AUDIO AMPLIFIER POWER -> +5V
AUDIO AMPLIFIER GROUND -> GND
```
Buttons
```
BUTTON NEXT VIDEO PIN A -> GPIO6
BUTTON NEXT VIDEO PIN B -> GND

BUTTON XXX PIN A -> GPIO5
BUTTON XXX PIN B -> GND
```
LED
```
LED FOR INDICATE USB COMMUNICATION ANODE -> GPIO27
LED FOR INDICATE USB COMMUNICATION CATODE -> GND
```

# Soldering and connecting components
1. Connect switch to LCD display (for enable/disable blacklight). Switch the switch on the LCD to the off position 
<img src="docu/hw/LCD_1.jpg" width="512"/>
<img src="docu/hw/LCD_2.jpg" width="512"/>

2. Connect switch to RPI. for RPI pause information
<img src="docu/hw/RPI_switch.jpg" width="512"/>

```
- one switch pole to GPIO26
- second pole to GND
```

3. Solder 4pcs long pin header male to RPI board, to connect power to LCD from RPI. long connectors are used for better air circulation, and cooling RPI. You can use heatsink for better cooling
<img src="docu/hw/lcd_supply1.jpg" width="512"/>
<img src="docu/hw/lcd_supply2.jpg" width="512"/>

4. Connect speaker to potentiometer and audio amplifier.
<img src="docu/hw/audio1.jpg" width="512"/>
<img src="docu/hw/audio6.jpg" width="512"/>

5. Connect audio amplifier to RPI
<img src="docu/hw/audio2.jpg" width="512"/>

```
- A+ -> audio input -> RPI pin GPIO19
- A- -> audio GND -> RPI pin GND
- SD -> shut down -> RPI pin GPIO13
- Vin -> voltage input -> RPI pin +5V
- Gnd -> ground -> RPI pin GND
```

<img src="docu/hw/audio4.jpg" width="512"/>
<img src="docu/hw/audio5.jpg" width="512"/>

6. Connect 2.2uF capacitor during A+ and GND pin, for a clearer sound
<img src="docu/hw/audio3.jpg" width="512"/>

7. Connect HDMI cable
<img src="docu/hw/hdmi.jpg" width="512"/>
<img src="docu/hw/hdmi2.jpg" width="512"/>

8.current view of HW

<img src="docu/hw/total.jpg" width="512"/>

9. Micro USB connector female
<img src="docu/hw/microusb.jpg" width="512"/>

9. Micro USB connector male
<img src="docu/microUSB.jfif" width="512"/>
<img src="docu/hw/microusbmale.jpg" width="512"/>

10. Button in VCR recorder. We need only 3 wire. One wire is common (GND). Second wire is for next movie, and next wire is for XXX function. solder and glue
<img src="docu/hw/vcr2.jpg" width="512"/>
<img src="docu/hw/vcr1.jpg" width="512"/>

11. Soldering USB A connector for USB masstorage devices. We need an old micro USB cable or micro USB connector and solder 4 wires. VCC, DATA+, DATA-, GND
<img src="docu/usb_wire_pinout.jpg" width="512"/>
<img src="docu/hw/usbA.jpg" width="512"/>

12. Soldering LED for indication of copying files from USB stick to microSD card. 
<img src="docu/led.png" width="512"/>
<img src="docu/hw/LED.jpg" width="512"/>

13. And soldering LED to RPI PCB. When maximum output voltage from GPIO is 3.3V and maximum current is 16mA, then we don't need resistor for current limitation. But you can use it if you want


```
LED Anode -> GPIO27
LED Catode -> GND
```

<img src="docu/hw/LED_RPI.jpg" width="512"/>

14. Stick the VCR to the top of the box with the super glue
<img src="docu/hw/vcr_case.jpg" width="512"/>

15. Stick the speaker holder to the box with the super glue
<img src="docu/hw/speaker_holder.jpg" width="512"/>

16. Stick the PCB with micro USB connector to the box with the glue
<img src="docu/hw/microusb_box.jpg" width="512"/>

17. Stick the PCB with micro A connector to the box with the glue
<img src="docu/hw/usb_box.jpg" width="512"/>

18. Stick the speaker to the box with the glue
<img src="docu/hw/speaker.jpg" width="512"/>

19. Now we can soldering wire from VCR to RPI PCB

```
Wire from button for next movie -> GPIO6
Common wire -> GND
Wire from button for XXX -> GPIO5
```

<img src="docu/hw/vcr_rpi1.jpg" width="512"/>
<img src="docu/hw/vcr_rpi2.jpg" width="512"/>

20. Stick the LED to the box with the glue
<img src="docu/hw/led_box.jpg" width="512"/>

21. Stick the magnet to the box with the glue
<img src="docu/hw/magnet_box.jpg" width="512"/>

22. Connect micro USB connector with power supply to RPI
<img src="docu/hw/microusb_psu_rpi.jpg" width="512"/>

23. Connect micro USB connector for USB stick to RPI
<img src="docu/hw/usba_stick_rpi.jpg" width="512"/>

24. Final pictures
<img src="docu/hw/final1.jpg" width="512"/>
<img src="docu/hw/final2.jpg" width="512"/>
<img src="docu/hw/final3.jpg" width="512"/>

---

<a name="instalation"></a>
# Instalation

These steps are for a **Raspberry Pi Zero 2 W** running **Raspberry Pi OS Lite** (Bookworm or newer). The video player is **mpv**; the older omxplayer version only ran on Raspberry Pi OS Buster.

1. **Install the OS.** In [Raspberry Pi Imager](https://www.raspberrypi.com/software/) pick:
   - Device: *Raspberry Pi Zero 2 W*
   - OS: *Raspberry Pi OS (other) → Raspberry Pi OS Lite (32-bit)*
   - In *Edit settings*: set a hostname, a username and password, your Wi-Fi network and Wi-Fi country, and on the *Services* tab enable SSH.

   The old `wpa_supplicant.conf` and `ssh` files in the boot partition no longer work, and there is no default `pi` user. Any username works.

2. **Boot and update.** Put the card in the Pi, power on, wait a couple of minutes, then SSH in (`ssh <user>@<hostname>.local`).
```
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```
   Don't run `rpi-update`; it installs pre-release firmware.

3. **Get the code and install.** Clone your copy of this repository into your home folder and run the installer. It installs mpv and the GPIO libraries, adds PWM audio to `/boot/firmware/config.txt`, sets the LCD mode in `/boot/firmware/cmdline.txt` (both are backed up first), and installs the services. It asks before making changes.
```
sudo apt install -y git
cd ~
git clone <repository URL> simpsonstv
cd simpsonstv
sudo ./install.sh
sudo reboot
```

4. **Settings.** Display rotation, audio device, player mode and the power-switch direction are in `~/simpsonstv/simpsonstv.conf`. After editing it:
```
sudo systemctl restart tvbutton tvplayer
```

5. **Convert videos to mp4.** Use `videos/encode.py` on your computer (it needs `ffmpeg`). It's much faster there than on the Pi. It writes 480p H.264 files to `videos/encoded/`.
```
python3 encode.py
```

6. **Copy videos to the Pi.**
   - **Over the network**: copy the mp4 files to `~/simpsonstv/videos` with `scp` or WinSCP.
   - **From a USB stick**: create a folder called **simpsonstv** in the root of the stick and put the mp4 files in it. Plug the stick into the TV. The LED near the USB port lights up while copying and turns off when it's done; then you can unplug the stick. A log (`simpsontv_log.txt`) is written to the stick.

     **Warning:** the copy is a mirror. Videos on the TV that aren't in the stick's `simpsonstv` folder are deleted.

<img src="docu/hw/usb_stick_port.jpg" width="512"/>

7. **Two player modes.** Set `PLAYER_SCRIPT` in `simpsonstv.conf`:
   - `player.py`: plays videos in random order (default)
   - `player-playlist.py`: plays in name order and continues with the last video after a reboot

## Controls

- **Power switch**: on plays with sound; off pauses the video and mutes the amplifier.
- **Right VCR button**: next video.
- **Left VCR button**: rewind 15 seconds.
- **Hold both VCR buttons for 3 seconds**: shut down.

## Troubleshooting

- Logs: `journalctl -u tvplayer -f`, `journalctl -u tvbutton -f`, `journalctl -u 'tvautocopy@*'`
- **Black screen**: check the screen's modes with `cat /sys/class/drm/card*-HDMI-A-1/modes`. If mpv reports errors, change `--vo=gpu --gpu-context=drm` to `--vo=drm` in `MPV_ARGS`.
- **Picture upside down**: change `--video-rotate=270` to `--video-rotate=90`.
- **No sound**: run `aplay -l` to find the card name, and test with `speaker-test -D plughw:CARD=Headphones -c 1 -t sine`.
- **Power switch works backwards**: set `POWER_SWITCH_INVERT=1`.

---
<a name="images_url"></a>
# Image
The old RPI ZERO image on my [gdrive](https://drive.google.com/drive/folders/1mnJnrXVBaZO_8UrxD8tn1eNyA690npIP?usp=sharing) is Raspberry Pi OS Buster with omxplayer. It doesn't match the current code and isn't tested on the Zero 2 W. For a Zero 2 W, follow the installation steps above.

- OS: raspberry-pi OS 32bit
- username: pi
- password: raspberry

---
<a name="howtouse"></a>
# How to use

***TODO***
