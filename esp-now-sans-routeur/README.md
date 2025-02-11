# ESP-NOW without a router

Bench of the deck https://heurisme.fr/en/blog/esp-now-sans-routeur/ . Nothing was measured or captured: no board was used. The deck relies on the Espressif documentation (ESP-IDF v5.4), and `trame.py` assembles by hand the bytes of an example ESP-NOW frame.

File names and part of the outputs are in French because the original article is. Useful names: `rejouer.sh` = replay script, `trame.py` = frame, `sorties/` = outputs, `sorties/trame.out` = frame output, `octets` (in the output) = bytes, `octets utiles` = payload bytes.

## What you need to replay

- Python 3 (tested with 3.13.2), standard library only.
- `bash`, `curl` and `shasum` for `rejouer.sh`.

## Replay everything

```bash
bash rejouer.sh
```

The script downloads the cited Espressif sources into `src/`, checks their sha256, then runs `python3 trame.py > sorties/trame.out`.

## File → slide

| File | Slide |
|---|---|
| `trame.py`, `sorties/trame.out` | 2 "An ESP-NOW message is an 802.11 action frame" (the bytes of the animation) |
| `src/espnow_example_main.c` | 3 "Five calls are enough to send a message" (downloaded) |
| `src/esp_now.h`, `src/Kconfig.esp_wifi` | 4 "20 peers at most, 7 of them encrypted by default" (downloaded) |
| `src/esp_wifi.h` | 9 "Sending while sleeping is easy, receiving is not" (name of the Interval API, downloaded) |

Slides 5 to 8 and 10 to 12 do not rely on any file in this folder: they summarize the Espressif documentation cited at the foot of the slide.

## Third-party data (downloaded, not copied into the repo)

ESP-IDF, tag `v5.4` (released 2025-01-04), Apache-2.0 license: https://github.com/espressif/esp-idf

| Local file | URL | sha256 |
|---|---|---|
| `src/espnow_example_main.c` | https://raw.githubusercontent.com/espressif/esp-idf/v5.4/examples/wifi/espnow/main/espnow_example_main.c | `200eb211e322ce9a65d100bf7d55236fbd59ccc473a4c5960b793d772278ca00` |
| `src/esp_now.h` | https://raw.githubusercontent.com/espressif/esp-idf/v5.4/components/esp_wifi/include/esp_now.h | `868d6e464cd8c100bf0f654192353bc2777d18a36cb629ba4952e7809d214f8b` |
| `src/esp_wifi.h` | https://raw.githubusercontent.com/espressif/esp-idf/v5.4/components/esp_wifi/include/esp_wifi.h | `aff32efe4b8ee582677ca94b0f6a13eed69b2dea745406db83b4d26aa11c2463` |
| `src/Kconfig.esp_wifi` | https://raw.githubusercontent.com/espressif/esp-idf/v5.4/components/esp_wifi/Kconfig | `3d339ff155d07659a5b283a68d6b6d5d1314aac3645a7ed056f29f1b7fe4c24a` |

The documentation pages cited by the deck are online and are not downloaded:

- API Reference "ESP-NOW": https://docs.espressif.com/projects/esp-idf/en/v5.4/esp32/api-reference/network/esp_now.html
- Wi-Fi Driver (Long Range, Connectionless Modules Power-saving): https://docs.espressif.com/projects/esp-idf/en/v5.4/esp32/api-guides/wifi.html
- ESP-WIFI-MESH Programming Guide: https://docs.espressif.com/projects/esp-idf/en/v5.4/esp32/api-guides/esp-wifi-mesh.html
- RF Coexistence: https://docs.espressif.com/projects/esp-idf/en/v5.4/esp32/api-guides/coexist.html
- ESP-FAQ "ESP-NOW" (not versioned): https://docs.espressif.com/projects/esp-faq/en/latest/application-solution/esp-now.html

The deprecation of `esp_wifi_config_espnow_rate()` (slide 8) is read in `src/esp_now.h` (v5.4).

The `esp-now` component (https://github.com/espressif/esp-now), version `2.5.2` (component registry, 2024-08-20, commit `610b24544ca3ac880720b9f0c61f33641a007fea`), is cited for `espnow.h` (`espnow_frame_head_t`) and the User Guide, not downloaded.

Assumption to keep in mind: the `01` version byte of the frame is an assumption of the deck, the docs do not give its value.
