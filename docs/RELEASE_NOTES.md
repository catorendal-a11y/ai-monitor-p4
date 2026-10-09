# AI Monitor v1.13.0

Choose GUITION ESP32-P4 or the original Waveshare ESP32-S3-Touch-LCD-4.3 in the same portable Windows app. New users explicitly choose their board and AI providers. Both firmware builds share NOVA/ORBIT, four themes and the existing usage dashboard.

- Separate S3 RGB/GT911/CH422G backend, memory-conscious buffers and matching PSRAM XIP SDK. P4 retains its existing MIPI DSI backend.
- Board-aware UART/USB discovery, handshake validation and firmware selection. Chip headers, offsets, checksums and matching factory/application images are verified before flashing.
- S3 visual brightness, idle fades and night schedule; the original board's LED backlight supports on/off only. Connect **USB TO UART** for flashing and host use.
- CI builds both targets; synthetic host, protocol and native LVGL regressions cover board selection and dimming. No maintainer configuration, API credentials or local activity records are distributed.

**S3 is experimental and has not been tested on physical hardware.** Only the original CH422G Waveshare model is targeted; B/C variants are unsupported. Touch alignment, RGB stability, tearing and sustained operation need board testing. See [board guide](https://github.com/catorendal-a11y/ai-monitor-p4/blob/main/docs/BOARDS.md).

Download the **ai-monitor-p4-v1.13.0-windows.zip** asset, extract everything, open **AI-Monitor.exe**, select your board in First-time setup and install its firmware. Existing P4 v1.12.0+ displays can keep their firmware; old private host configurations without a board field retain P4. Stop the old host before starting one from a new folder. Keep your own tools/aim_host.json private.
