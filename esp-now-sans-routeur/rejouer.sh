#!/usr/bin/env bash
# Replays the bench of the "ESP-NOW" deck: downloads the cited Espressif sources (ESP-IDF v5.4),
# checks their sha256, then rebuilds the example frame with trame.py (no radio).
set -euo pipefail
cd "$(dirname "$0")"
telecharger() { # url fichier sha256
  if [ -f "$2" ] && [ "$(shasum -a 256 "$2" | cut -d' ' -f1)" = "$3" ]; then echo "déjà là : $2"; return; fi
  mkdir -p "$(dirname "$2")"
  curl -fsSL -A "Mozilla/5.0" "$1" -o "$2" || { echo "échec du téléchargement : $1" >&2; exit 1; }
  [ "$(shasum -a 256 "$2" | cut -d' ' -f1)" = "$3" ] || { echo "sha256 différent pour $2 (le fichier a changé en ligne ?)" >&2; exit 1; }
  echo "ok : $2"
}
IDF=https://raw.githubusercontent.com/espressif/esp-idf/v5.4
telecharger $IDF/examples/wifi/espnow/main/espnow_example_main.c src/espnow_example_main.c 200eb211e322ce9a65d100bf7d55236fbd59ccc473a4c5960b793d772278ca00
telecharger $IDF/components/esp_wifi/include/esp_now.h src/esp_now.h 868d6e464cd8c100bf0f654192353bc2777d18a36cb629ba4952e7809d214f8b
telecharger $IDF/components/esp_wifi/include/esp_wifi.h src/esp_wifi.h aff32efe4b8ee582677ca94b0f6a13eed69b2dea745406db83b4d26aa11c2463
telecharger $IDF/components/esp_wifi/Kconfig src/Kconfig.esp_wifi 3d339ff155d07659a5b283a68d6b6d5d1314aac3645a7ed056f29f1b7fe4c24a
mkdir -p sorties
python3 trame.py > sorties/trame.out
echo "sortie écrite dans sorties/trame.out"
