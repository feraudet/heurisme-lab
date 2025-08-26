#!/usr/bin/env bash
# Replays the whole bench. Run it from anywhere: bash banc/rejouer.sh
# Requirements: Docker, curl, shasum (or sha256sum).
# The two sigrok-dumps captures are downloaded into donnees/ (pinned commit), then checked by sha256.
# Outputs: banc/sorties/ (French) and banc/sorties/en/ (English, --en option).
set -euo pipefail
ICI=$(cd "$(dirname "$0")" && pwd)
RACINE=$(cd "$ICI/.." && pwd)

# --- third-party data: downloaded, never copied into the repo ---
COMMIT=0ad13477abc959d37fc9a5acbd23901c371c9c76
BASE=https://raw.githubusercontent.com/sigrokproject/sigrok-dumps/$COMMIT/uart/hello_world/8n1
D="$RACINE/donnees/sigrok-dumps/uart/hello_world/8n1"
sha() { if command -v sha256sum >/dev/null; then sha256sum "$1"; else shasum -a 256 "$1"; fi | cut -d' ' -f1; }
prendre() { # file name, expected sha256
  mkdir -p "$D"
  [ -f "$D/$1" ] || curl -fsSL "$BASE/$1" -o "$D/$1"
  [ "$(sha "$D/$1")" = "$2" ] || { echo "sha256 inattendu pour $1" >&2; exit 1; }
}
prendre hello_world_8n1_115200.sr e72b96efdb30ef33e1a7a2a4e1bd814cd47d5474b67a1d5adb68d4c5ad47ab24
prendre hello_world_8n1_9600.sr   b87f1f632ce0684a79e0391c860f8b55c78ce952d3ea10eaede41e8a7ffdf8ea

# --- bench ---
docker build -q -t banc-uart "$ICI" >/dev/null
mkdir -p "$ICI/sorties/en"

# ATmega simulator: outputs banc/sorties/sim-*.txt (and en/ with --en)
for c in trame derive seuils quartz pc deux-avr; do
  docker run --rm -v "$ICI:/b:ro" banc-uart python3 /b/uart_sim.py $c > "$ICI/sorties/sim-$c.txt"
  docker run --rm -v "$ICI:/b:ro" banc-uart python3 /b/uart_sim.py $c --en > "$ICI/sorties/en/sim-$c.txt"
done

# real captures decoded by sigrok-cli
docker run --rm -v "$D:/d:ro" -v "$ICI:/b:ro" -w /d banc-uart sh /b/sigrok.sh > "$ICI/sorties/sigrok.txt" 2>&1
docker run --rm -v "$D:/d:ro" -v "$ICI:/b:ro" -w /d banc-uart sh /b/sigrok.sh --en > "$ICI/sorties/en/sigrok.txt" 2>&1

ls -la "$ICI/sorties" "$ICI/sorties/en"
