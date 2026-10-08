# Third-party notices

The root MIT license covers project-owned material. It does not replace third-party licenses or grant trademark rights.

## Bundled Espressif components

These components retain their copyright headers and original **Apache License 2.0** texts, preserved without modification:

- `lib/esp_lcd_ek79007`: [license](lib/esp_lcd_ek79007/license.txt).
- `lib/esp_lcd_st7701`: [license](lib/esp_lcd_st7701/license.txt).
- `lib/esp_lcd_touch`: [license](lib/esp_lcd_touch/license.txt).
- `lib/esp_lcd_touch_gt911`: [license](lib/esp_lcd_touch_gt911/license.txt).

These are Espressif display/touch components. Original ownership and Apache-2.0 redistribution obligations continue to apply. Component source/manifests contain upstream attribution and version information.

## Downloaded dependencies

- [LVGL](https://github.com/lvgl/lvgl), v9.6.0: MIT; retain upstream copyright/license. Fonts and assets included by LVGL retain the terms supplied with LVGL; this project does not relicense fonts.
- [ArduinoJson](https://github.com/bblanchon/ArduinoJson), 7.4.3: MIT, copyright Benoit Blanchon and contributors; retain upstream notices.
- [pyserial](https://github.com/pyserial/pyserial), 3.5: BSD-style license supplied by upstream.
- [pioarduino](https://github.com/pioarduino/platform-espressif32), Arduino-ESP32 and ESP-IDF: obtained through PlatformIO. Component-specific licenses/notices continue to apply; consult the installed distributions before redistributing toolchains or combined artifacts.

Dependencies are downloaded by build/setup, not vendored into this public source package.

## Protocol reference

AIM1/JSON follows [tobymarks/esp32-ai-monitor](https://github.com/tobymarks/esp32-ai-monitor). This attribution acknowledges interoperability and does not imply affiliation or transfer copyright. Project extensions include refresh and local token-activity signaling.

## Provider logos and artwork

The OpenAI mark originates from the [OpenAI brand archive](https://cdn.openai.com/brand/OpenAI-Logos-2025.zip). The ZCode mark originates from [ZCodeAboutLogo](https://github.com/zai-org/ZCode/blob/main/packages/ui/src/components/ui/ZCodeAboutLogo.tsx). SVG sources and references remain in `assets/nova`.

OpenAI and ZCode names/logos remain their owners' property. The root MIT license does not grant trademark rights or relicense these marks. They identify displayed providers; no sponsorship or endorsement is implied. Check applicable source and brand terms before reusing or redistributing marks in another product.

Original NOVA artwork is project-owned and covered by MIT. Generated C++ arrays retain this distinction: robot artwork is MIT; embedded provider marks retain their owners' rights.