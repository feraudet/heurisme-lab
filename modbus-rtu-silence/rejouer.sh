#!/bin/bash
# Replays the Modbus RTU bench of the deck https://heurisme.fr/en/blog/modbus-rtu-silence/
# Needs Docker. In the container (python:3.12.9-slim-bookworm, pinned by digest, pushed 2025-04-08):
# Python 3.12.9, pymodbus 3.8.6, pyserial 3.5, socat 1.7.4.4 (Debian snapshot of 2025-04-08).
# The references (Modbus specifications, ftdi_sio.c, AN232B-04) are not used by the computation:
# bash rejouer.sh refs downloads them into ref/ and checks their sha256.
set -eu
cd "$(dirname "$0")"

prendre() { # prendre <file> <url> <sha256>   (prendre = fetch)
  mkdir -p ref
  [ -f "ref/$1" ] || curl -fsSL -o "ref/$1" "$2"
  got=$(shasum -a 256 "ref/$1" | cut -d' ' -f1)
  if [ "$got" != "$3" ]; then
    echo "sha256 différent pour $1 (attendu $3, obtenu $got)" >&2
    [ "${TOLERE:-0}" = 1 ] || exit 1
  fi
}

if [ "${1:-}" = refs ]; then
  # modbus.org may refuse curl: then download the PDF by hand into ref/ and rerun
  prendre modbusoverserial.pdf https://www.modbus.org/file/secure/modbusoverserial.pdf 85a91e278b26d68c94a2f61a5300cd39c9e4c855034833f391abc6541fbdf7e5
  prendre modbusprotocolspecification.pdf https://www.modbus.org/file/secure/modbusprotocolspecification.pdf f80d0d7132fd035104c3f21b01026470e3310ca3d8d493d9a9737d0d32ad2eb1
  prendre ftdi_sio.c https://raw.githubusercontent.com/torvalds/linux/18e0885bd2ca738407036434418a26a58394a60e/drivers/usb/serial/ftdi_sio.c 15b0c7508014dd374975ef1d05518a9d0ff274eee739631156ef233d4f772cb8
  echo "références dans ref/ (AN232B-04 : https://ftdichip.com/wp-content/uploads/2020/08/AN232B-04_DataLatencyFlow.pdf, sans sha256 relevé)"
  exit 0
fi

docker rm -f deck-modbus-lab >/dev/null 2>&1 || true
IMAGE=python:3.12.9-slim-bookworm@sha256:48a11b7ba705fd53bf15248d1f94d36c39549903c5d59edcfa2f3f84126e7b44
SNAPSHOT=https://snapshot.debian.org/archive/debian/20250408T000000Z/
docker run -d --name deck-modbus-lab -v "$PWD":/work -w /work "$IMAGE" sleep 7200
docker exec deck-modbus-lab sh -c "rm -f /etc/apt/sources.list.d/debian.sources && echo 'deb [check-valid-until=no] $SNAPSHOT bookworm main' > /etc/apt/sources.list.d/snapshot.list && apt-get update -qq && apt-get install -y -qq socat >/dev/null && pip install -q pymodbus==3.8.6 pyserial==3.5"

d() { docker exec "$@"; }
d deck-modbus-lab sh src/run.sh normal
d deck-modbus-lab python src/crc.py raw/normal-capture.txt > raw/crc-normal.txt
d deck-modbus-lab sh src/run.sh gap16-pymodbus --gap-after 4 --gap-ms 16
d -e SLAVE="python src/strict_slave.py" deck-modbus-lab sh src/run.sh strict-normal
d -e SLAVE="python src/strict_slave.py" deck-modbus-lab sh src/run.sh strict-gap1ms --gap-after 4 --gap-ms 1.2
d -e SLAVE="python src/strict_slave.py" deck-modbus-lab sh src/run.sh strict-gap16 --gap-after 4 --gap-ms 16
d -e BAUD=9600 -e SLAVE="python src/strict_slave.py" deck-modbus-lab sh src/run.sh strict9600-gap1500us --gap-after 4 --gap-ms 1.5
d deck-modbus-lab python src/timing.py > raw/timing.txt

docker rm -f deck-modbus-lab >/dev/null
echo "Sorties dans raw/. Comparer avec git diff."
