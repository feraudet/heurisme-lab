#!/usr/bin/env bash
# Replays the whole bench in a python:3.12.12-slim container, in French (sorties/) and in English (sorties-en/).
# One output per command. Requirements: Docker, curl, shasum (or sha256sum), network access.
# The two logs come from gpsd, test/daemon/ (https://gitlab.com/gpsd/gpsd, BSD license).
# They are downloaded into banc/logs/ (pinned commit), checked by sha256, never copied into the repo.
set -euo pipefail
cd "$(dirname "$0")"

COMMIT=f6f1088671cfe9da7075bedd4639046672e05a8e
BASE=https://gitlab.com/gpsd/gpsd/-/raw/$COMMIT/test/daemon
sha() { if command -v sha256sum >/dev/null; then sha256sum "$1"; else shasum -a 256 "$1"; fi | cut -d' ' -f1; }
prendre() { # file name, expected sha256
  mkdir -p logs
  [ -f "logs/$1" ] || curl -fsSL "$BASE/$1" -o "logs/$1"
  [ "$(sha "logs/$1")" = "$2" ] || { echo "sha256 inattendu pour $1" >&2; exit 1; }
}
prendre telit-he910.log 784c3be18d97cb8aa5d5995146c06e9d720519f79bdd7c37b99a6e4fd2bcb0cf
prendre rx210.log       82aaf0a0c3342e5033f2cc9af060d32e85ead338a67d1098371917232f53db93

R="docker run --rm -v $PWD:/b -w /b python:3.12.12-slim"

for langue in fr en; do
  if [ "$langue" = fr ]; then S=sorties; OPT=""; else S=sorties-en; OPT="--en"; fi
  rm -rf "$S" && mkdir -p "$S"
  n() { $R python3 -I nmea.py $OPT "$@"; }

  n chrono logs/telit-he910.log > $S/chrono-telit.txt
  n chrono logs/rx210.log > $S/chrono-rx210.txt

  n checksum '$GPGGA,,,,,,0,,,,M,,M,,*66' > $S/checksum-gga-vide.txt
  n checksum '$GPGGA,105153.71,5050.4122,N,00420.8266,E,1,04,2.25,109.44,M,,M,,*77' > $S/checksum-gga-fix.txt

  n champs '$GPGGA,,,,,,0,,,,M,,M,,*66' > $S/champs-gga-vide.txt
  n champs '$GPGGA,105153.71,5050.4122,N,00420.8266,E,1,04,2.25,109.44,M,,M,,*77' > $S/champs-gga-fix.txt
  n champs '$GPRMC,,V,,,,,,,,,,N*53' > $S/champs-rmc-vide.txt
  n champs '$GPRMC,105153.71,A,5050.4122,N,00420.8266,E,0.14,303.60,120319,,,A*59' > $S/champs-rmc-fix.txt
  n champs '$GPGSV,2,1,05,13,00,000,37,15,00,000,44,17,00,000,37,24,00,000,38*72' > $S/champs-gsv-avant.txt
  n champs '$GPGSV,2,1,06,13,00,000,39,15,45,282,44,17,19,211,36,19,00,000,35*7E' > $S/champs-gsv-apres-1.txt
  n champs '$GPGSV,2,2,06,24,39,316,36,28,55,198,48,,,,,,,,*74' > $S/champs-gsv-apres-2.txt
  n champs '$GPGSA,A,1,,,,,,,,,,,,,,,*1E' > $S/champs-gsa-vide.txt
  n champs '$GPGSA,A,3,15,17,24,28,,,,,,,,,4.00,2.25,3.25*09' > $S/champs-gsa-fix.txt

  # cross-check with a third-party library
  $R sh -c "pip install -q --root-user-action=ignore --disable-pip-version-check pynmea2==1.19.0 && python3 -I verif_pynmea2.py $OPT logs/telit-he910.log logs/rx210.log" > $S/pynmea2.txt

  # raw log content, identical in both languages
  # telit: end of cycle 36, cycle 37, start of cycle 38
  sed -n 246,262p logs/telit-he910.log > $S/telit-autour-du-fix.txt
  # rx210: the proprietary sentence that gives the receiver uptime
  grep -n uptime logs/rx210.log > $S/rx210-uptime.txt
done
