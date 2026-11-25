# RGBWYV

Six-channel (Red, Green, Blue, White, Amber, Violet) LED light built on two Seeed XIAO nRF52840 boards.

- `RGB_Peripheral_Device_R2/` – firmware for the light (PWM, MSGEQ7 audio mode, AHT20 temp, fan via PCF8574)
- `RGB_Central_Remote_R2/` – firmware for the BLE remote that bridges USB serial to the light
- `console.py/` – Tkinter desktop console (light/dark theme) that talks to the remote over USB at 921600 baud
- `RGBYVW_Schematic_PCB/` – KiCad schematics, PCB, and Gerbers
- `old/` – archived R2 version
