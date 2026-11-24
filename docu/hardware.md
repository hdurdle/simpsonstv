# Hardware build

How to print and wire the TV. This is the build guide from johnyHV's version, which this version uses unchanged except for the note below.

> **Not needed in this version:** the USB stick port and its LED. Videos are copied over the network instead (see the [README](../README.md)). You can skip the **USB A connector**, the **micro USB plug** that wires it to the Pi, the **3 mm LED**, and assembly steps **9 (micro USB male), 11, 12, 13, 17, 20 and 23**.

## 3D model

My 3D model is stored on the [Printables](https://www.prusaprinters.org/prints/90361-simpsons-tv) page

---
## HW parts

- 1k potentiometer [here](https://www.tme.eu/en/details/pc16bu-1k-lin/cond-plastic-single-turn-potentiometers/omeg/)
<img src="HW_parts/potentiometer.jpg" width="256"/>

- 7x7mm switch [here](https://www.aliexpress.com/item/32704922363.html)
<img src="HW_parts/switch_7x7.jpg" width="256"/>

- 4" HDMI Waveshare LCD 800x400 [here](https://rlx.sk/sk/9-5-lcd-display/5454-4inch-hdmi-lcd-800480-ips-waveshare-4-touch-screen-lcd-hdmi-interface-ips-screen-designed-for-raspberry-pi-12030.html)
<img src="HW_parts/lcd.jpg" width="256"/>

- HDMI connector DIY [here](https://rpishop.cz/redukce/2176-waveshare-mini-hdmi-adapter-pro-diy-hdmi-kabel.html)
<img src="HW_parts/HDMI_connector.jpg" width="256"/>

- MINI HDMI connector DIY [here](https://rpishop.cz/redukce/1205-waveshare-hdmi-adapter-pro-diy-hdmi-kabel-pravouhy.html)
<img src="HW_parts/micro_hdmi_connector.jpg" width="256"/>

- HDMI cable DIY [here](https://rpishop.cz/hdmi/1209-waveshare-diy-hdmi-plochy-kabel-02m.html)
<img src="HW_parts/hdmi_cable.jpg" width="256"/>
<img src="HW_parts/hdmi_final.jpg" width="256"/>

- speaker [here](https://rpishop.cz/reproduktory/1204-waveshare-8-5w-reproduktor.html)
<img src="HW_parts/speaker.jpg" width="256"/>

- rpi zero [here](https://rpishop.cz/zero/632-raspberry-pi-zero.html)
<img src="HW_parts/RASP_PI_ZERO_00.png" width="256"/>

- audio amplifier PAM8302 [here](https://rlx.sk/sk/audio-voice-boards-speech-recognition/3397-mono-25w-class-d-audio-amplifier-pam8302-adafruit-2130.html)
<img src="HW_parts/audio_amplifier.jpg" width="256"/>

- capacitor 2.2uF/50V
<img src="HW_parts/capacitor.jpg" width="256"/>

- screw M3 4x
<img src="HW_parts/screw.jpg" width="256"/>

- switch 6x6mm 2x [here](https://www.tme.eu/en/details/tact-64k/microswitches-tact/ninigi/) **watch out for the length of the button**
<img src="HW_parts/button.jpg" width="256"/>

- micro USB connector [here](https://www.aliexpress.com/item/32916571891.html?spm=a2g0o.productlist.0.0.284c68canDNCGE&algo_pvid=d8468b46-a429-405d-a448-26761076313c&algo_exp_id=d8468b46-a429-405d-a448-26761076313c-5&pdp_ext_f=%7B%22sku_id%22%3A%2266023288418%22%7D)
<img src="HW_parts/micro_usb.jpg" width="256"/>

- PCB with micro USB connector [here](https://www.aliexpress.com/item/4000484202812.html?spm=a2g0o.productlist.0.0.52451297eW2VB6&algo_pvid=d8623308-0e8e-433a-b8c3-d0a98947ac72&aem_p4p_detail=202111260636579663439259216280013679493&algo_exp_id=d8623308-0e8e-433a-b8c3-d0a98947ac72-9&pdp_ext_f=%7B%22sku_id%22%3A%2210000002007513401%22%7D)
<img src="HW_parts/microUSB.jpg" width="256"/>

- magnet circle 6x2mm
<img src="HW_parts/magnet.jpg" width="256"/>

- 3mm LED
<img src="HW_parts/led.jpg" width="256"/>

- USB A connector [here](https://www.aliexpress.com/item/4000806581109.html?spm=a2g0o.productlist.0.0.2c402a18K0POfK&algo_pvid=fe076f0d-f35f-4749-a6fb-6e73d8c0a93d&algo_exp_id=fe076f0d-f35f-4749-a6fb-6e73d8c0a93d-11&pdp_ext_f=%7B%22sku_id%22%3A%2210000008096938788%22%7D)
<img src="HW_parts/usbA.jpg" width="256"/>

- Wires
<img src="HW_parts/wires.jpg" width="256"/>

- long pin header 25mm, male, 2.54MM PITCH [here](https://www.aliexpress.com/item/32851444441.html)
<img src="HW_parts/pin_header.jpg" width="256"/>

---
## HW construction

Approximate schematic. Missing USB and LCD parts
<img src="block schematic_schem.png" width="768"/>
<img src="block schematic_bb.png" width="768"/>

### Pinout
<img src="RPIpinout.jpg" width="768"/>

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

BUTTON REWIND PIN A -> GPIO5
BUTTON REWIND PIN B -> GND
```
LED (not used by this version)
```
LED FOR INDICATE USB COMMUNICATION ANODE -> GPIO27
LED FOR INDICATE USB COMMUNICATION CATODE -> GND
```

## Soldering and connecting components
1. Connect switch to LCD display (for enable/disable blacklight). Switch the switch on the LCD to the off position 
<img src="hw/LCD_1.jpg" width="512"/>
<img src="hw/LCD_2.jpg" width="512"/>

2. Connect switch to RPI. for RPI pause information
<img src="hw/RPI_switch.jpg" width="512"/>

```
- one switch pole to GPIO26
- second pole to GND
```

3. Solder 4pcs long pin header male to RPI board, to connect power to LCD from RPI. long connectors are used for better air circulation, and cooling RPI. You can use heatsink for better cooling
<img src="hw/lcd_supply1.jpg" width="512"/>
<img src="hw/lcd_supply2.jpg" width="512"/>

4. Connect speaker to potentiometer and audio amplifier.
<img src="hw/audio1.jpg" width="512"/>
<img src="hw/audio6.jpg" width="512"/>

5. Connect audio amplifier to RPI
<img src="hw/audio2.jpg" width="512"/>

```
- A+ -> audio input -> RPI pin GPIO19
- A- -> audio GND -> RPI pin GND
- SD -> shut down -> RPI pin GPIO13
- Vin -> voltage input -> RPI pin +5V
- Gnd -> ground -> RPI pin GND
```

<img src="hw/audio4.jpg" width="512"/>
<img src="hw/audio5.jpg" width="512"/>

6. Connect 2.2uF capacitor during A+ and GND pin, for a clearer sound
<img src="hw/audio3.jpg" width="512"/>

7. Connect HDMI cable
<img src="hw/hdmi.jpg" width="512"/>
<img src="hw/hdmi2.jpg" width="512"/>

8.current view of HW

<img src="hw/total.jpg" width="512"/>

9. Micro USB connector female
<img src="hw/microusb.jpg" width="512"/>

9. Micro USB connector male
<img src="microUSB.jfif" width="512"/>
<img src="hw/microusbmale.jpg" width="512"/>

10. Button in VCR recorder. We need only 3 wire. One wire is common (GND). Second wire is for next movie, and next wire is for rewind. solder and glue
<img src="hw/vcr2.jpg" width="512"/>
<img src="hw/vcr1.jpg" width="512"/>

11. Soldering USB A connector for USB masstorage devices. We need an old micro USB cable or micro USB connector and solder 4 wires. VCC, DATA+, DATA-, GND
<img src="usb_wire_pinout.jpg" width="512"/>
<img src="hw/usbA.jpg" width="512"/>

12. Soldering LED for indication of copying files from USB stick to microSD card. 
<img src="led.png" width="512"/>
<img src="hw/LED.jpg" width="512"/>

13. And soldering LED to RPI PCB. When maximum output voltage from GPIO is 3.3V and maximum current is 16mA, then we don't need resistor for current limitation. But you can use it if you want


```
LED Anode -> GPIO27
LED Catode -> GND
```

<img src="hw/LED_RPI.jpg" width="512"/>

14. Stick the VCR to the top of the box with the super glue
<img src="hw/vcr_case.jpg" width="512"/>

15. Stick the speaker holder to the box with the super glue
<img src="hw/speaker_holder.jpg" width="512"/>

16. Stick the PCB with micro USB connector to the box with the glue
<img src="hw/microusb_box.jpg" width="512"/>

17. Stick the PCB with micro A connector to the box with the glue
<img src="hw/usb_box.jpg" width="512"/>

18. Stick the speaker to the box with the glue
<img src="hw/speaker.jpg" width="512"/>

19. Now we can soldering wire from VCR to RPI PCB

```
Wire from button for next movie -> GPIO6
Common wire -> GND
Wire from button for rewind -> GPIO5
```

<img src="hw/vcr_rpi1.jpg" width="512"/>
<img src="hw/vcr_rpi2.jpg" width="512"/>

20. Stick the LED to the box with the glue
<img src="hw/led_box.jpg" width="512"/>

21. Stick the magnet to the box with the glue
<img src="hw/magnet_box.jpg" width="512"/>

22. Connect micro USB connector with power supply to RPI
<img src="hw/microusb_psu_rpi.jpg" width="512"/>

23. Connect micro USB connector for USB stick to RPI
<img src="hw/usba_stick_rpi.jpg" width="512"/>

24. Final pictures
<img src="hw/final1.jpg" width="512"/>
<img src="hw/final2.jpg" width="512"/>
<img src="hw/final3.jpg" width="512"/>
