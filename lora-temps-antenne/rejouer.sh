#!/usr/bin/env bash
# Replays the bench of the "LoRa" deck: downloads the TTN calculator and the cited documents,
# checks their sha256, then reruns airtime.py (SX1276 formula, no radio).
set -euo pipefail
cd "$(dirname "$0")"
telecharger() { # url fichier sha256
  if [ -f "$2" ] && [ "$(shasum -a 256 "$2" | cut -d' ' -f1)" = "$3" ]; then echo "déjà là : $2"; return; fi
  mkdir -p "$(dirname "$2")"
  curl -fsSL -A "Mozilla/5.0" "$1" -o "$2" || { echo "échec du téléchargement : $1" >&2; exit 1; }
  [ "$(shasum -a 256 "$2" | cut -d' ' -f1)" = "$3" ] || { echo "sha256 différent pour $2 (le fichier a changé en ligne ?)" >&2; exit 1; }
  echo "ok : $2"
}
AB=https://raw.githubusercontent.com/avbentem/airtime-calculator/af41bc53c7ce61da27237ba24756ebcf94314440/src/lora
telecharger $AB/Airtime.ts raw/Airtime.ts bdab86547bad3fd5e2d66fe3ac49ddee1e64fb1062542bba57b6d913a3afd5e2
telecharger $AB/Airtime.test.ts raw/Airtime.test.ts e4b66d51720f13343d5f92f5f36cd106f9c4e57eda6bcf94c839700cebad37f6
telecharger https://cdn.sparkfun.com/assets/7/7/3/2/2/SX1276_Datasheet.pdf raw/SX1276_Datasheet.pdf 330745f933df00015d2de3efd582608339350ba3a21001d11b9d449839ce016b
telecharger https://lora-alliance.org/wp-content/uploads/2021/05/RP002-1.0.3-FINAL-1.pdf raw/RP002-1.0.3.pdf 7babdb743e051fdc86bce8fdf99716c4f275da6b31f6495ccba9ce956373715c
telecharger https://www.etsi.org/deliver/etsi_en/300200_300299/30022001/03.01.01_60/en_30022001v030101p.pdf raw/en_30022001v030101p.pdf 42e0b9924e63c64f4e0606b716635946e2b36f7c5ced5dbf128222d02c022178
telecharger https://www.etsi.org/deliver/etsi_en/300200_300299/30022002/03.02.01_60/en_30022002v030201p.pdf raw/en_30022002v030201p.pdf df54e88af3879f143d1d22cfbe3cc90657b0fecd85c2afb054f1ba79c67ec2e3
telecharger https://www.epfl.ch/labs/tcl/wp-content/uploads/2020/02/Reverse_Eng_Report.pdf raw/Reverse_Eng_Report.pdf 63142f77b27260b4adb99d3997ca16bbde0988df970fe3ea9f1433a596105432
python3 airtime.py > raw/airtime.out
echo "sortie écrite dans raw/airtime.out"
