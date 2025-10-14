#!/usr/bin/env bash
# Replays the bench of the "DMX512" deck: downloads the cited OLA sources,
# checks their sha256, then reruns dmx_calc.py (no hardware, UDP on 127.0.0.1 only).
set -euo pipefail
cd "$(dirname "$0")"
telecharger() { # url fichier sha256
  if [ -f "$2" ] && [ "$(shasum -a 256 "$2" | cut -d' ' -f1)" = "$3" ]; then echo "déjà là : $2"; return; fi
  mkdir -p "$(dirname "$2")"
  curl -fsSL -A "Mozilla/5.0" "$1" -o "$2" || { echo "échec du téléchargement : $1" >&2; exit 1; }
  [ "$(shasum -a 256 "$2" | cut -d' ' -f1)" = "$3" ] || { echo "sha256 différent pour $2 (le fichier a changé en ligne ?)" >&2; exit 1; }
  echo "ok : $2"
}
OLA=https://raw.githubusercontent.com/OpenLightingProject/ola/cf52b2a58dffec1a28b4c8f19556e99f7134316a
telecharger $OLA/include/ola/rdm/RDMEnums.h src/RDMEnums.h 42e0f985be8fb47ac96c1d89b381f3db561335b6bb1a7c795d0da4fac8134642
telecharger $OLA/include/ola/rdm/UID.h src/UID.h a83de8b44e5dd8ca213145fb30a7638d889cae98e7f2b59df6a601bbe8c06ac7
telecharger $OLA/include/ola/rdm/RDMPacket.h src/RDMPacket.h 43a1869b3c06feb76d9dd651a3f09372011504cc11ddbac61e0cad355817a5b7
telecharger $OLA/plugins/ftdidmx/FtdiDmxThread.cpp src/FtdiDmxThread.cpp c2ec347a30469a7e6526198c75dfa6e64cdd1b2cae9ac2f3137e7709c312fced
mkdir -p sorties
python3 dmx_calc.py > sorties/dmx_calc.out
echo "sortie écrite dans sorties/dmx_calc.out"
