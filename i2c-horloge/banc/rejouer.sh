#!/usr/bin/env bash
# Replays the whole bench. Run it from anywhere: bash banc/rejouer.sh
# Requirements: Docker, curl, shasum (or sha256sum).
# The two sigrok-dumps captures are downloaded into donnees/ (pinned commit), then checked by sha256.
# Outputs: banc/sorties/ (French) and banc/sorties/en/ (English). Our scripts take --en to write
# in English; the sigrok-cli outputs are the same in both folders.
set -euo pipefail
ICI=$(cd "$(dirname "$0")" && pwd)
RACINE=$(cd "$ICI/.." && pwd)

# --- third-party data: downloaded, never copied into the repo ---
COMMIT=e2c49eb88327ac4eaaa41c160b9e3faa1d9ca1da
BASE=https://raw.githubusercontent.com/sigrokproject/sigrok-dumps/$COMMIT/i2c
SHT=sensirion_sht2x
AD=potentiometer/analog_devices_ad5258
SHT_F=i2c-sht21-100khz-read-serial-hold.sr
AD_F=ad5258_write_eeprom_63_readback_nack.sr
SHT_SHA=584a4d12d4a5eddc3bb2c00e4cd6b9437054bc4838a4bf6272be973228e42682
AD_SHA=bac371a27db3f6a150b5602433043d20b99437930cb53fa146e8c639325a7c22
DUMPS="$RACINE/donnees/sigrok-dumps/i2c"

sha() { if command -v sha256sum >/dev/null; then sha256sum "$1"; else shasum -a 256 "$1"; fi | cut -d' ' -f1; }
prendre() { # relative path, expected sha256
  mkdir -p "$DUMPS/$(dirname "$1")"
  [ -f "$DUMPS/$1" ] || curl -fsSL "$BASE/$1" -o "$DUMPS/$1"
  [ "$(sha "$DUMPS/$1")" = "$2" ] || { echo "sha256 inattendu pour $1" >&2; exit 1; }
}
prendre "$SHT/$SHT_F" "$SHT_SHA"
prendre "$AD/$AD_F" "$AD_SHA"

# --- bench ---
docker build -q -t i2c-banc "$ICI" >/dev/null
A="-P i2c:scl=SCL:sda=SDA -A i2c=addr-data --protocol-decoder-samplenum"

# runs a command in the container, in the capture folder ($1), prints "$ command" then the output
run() {
  local dossier=$1; shift
  { echo "\$ $*"; docker run --rm -w "/dumps/$dossier" -v "$DUMPS:/dumps:ro" -v "$ICI:/banc" i2c-banc "$@"; } 2>&1
}

for langue in fr en; do
  SUB=sorties; EN=""
  [ "$langue" = en ] && { SUB=sorties/en; EN="--en"; }
  S="$ICI/$SUB"; mkdir -p "$S"

  docker run --rm i2c-banc sigrok-cli --version > "$S/versions.txt"

  # 1. real SHT21 capture: decoding, then SCL measurement
  run $SHT sigrok-cli -i $SHT_F $A > "$S/sht21-decode.txt"
  run $SHT python3 -I /banc/mesure_scl.py $SHT_F 100 $EN > "$S/sht21-scl.txt"
  C="sigrok-cli -i $SHT_F $A | grep -B4 -A12 'write: E3'"
  { echo "\$ $C"; docker run --rm -w "/dumps/$SHT" -v "$DUMPS:/dumps:ro" i2c-banc sh -c "$C"; } > "$S/sht21-hold.txt" 2>&1

  # 2. real AD5258 capture: write then NACK
  run $AD sigrok-cli -i $AD_F $A > "$S/ad5258-decode.txt"
  run $AD python3 -I /banc/mesure_scl.py $AD_F 100 $EN > "$S/ad5258-scl.txt"
  run $AD python3 -I /banc/mesure_scl.py $AD_F --fronts 0 6227 > "$S/ad5258-fronts.txt"

  # 3. pull-up calculation example, SHT21 CRC
  run . python3 -I /banc/calcul_pullup.py $EN > "$S/pullup.txt"
  run . python3 -I /banc/crc_sht21.py $EN > "$S/crc.txt"

  # 4. simulation: master that respects / ignores clock stretching
  for m in respecte ignore; do
    run . sh -c "cd /banc && python3 -I sim_bus.py --$m --vcd $SUB/sim-$m.vcd $EN" \
      | sed "1s|.*|\$ python3 -I sim_bus.py --$m --vcd sim-$m.vcd${EN:+ $EN}|" > "$S/sim-$m.txt"
    { echo "\$ sigrok-cli -I vcd -i sim-$m.vcd $A"
      docker run --rm -w "/banc/$SUB" -v "$ICI:/banc" i2c-banc sigrok-cli -I vcd -i sim-$m.vcd $A; } > "$S/sim-$m-decode.txt" 2>&1
  done
done
ls -la "$ICI/sorties" "$ICI/sorties/en"
