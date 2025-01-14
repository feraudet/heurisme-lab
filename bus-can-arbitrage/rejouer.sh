#!/bin/bash
# Replays the CAN bench of the deck https://heurisme.fr/en/blog/bus-can-arbitrage/
# Needs Docker only. Images pinned by digest and packages of the time of the article (2025-01-14):
# python:3.13.1-slim-bookworm, debian:bookworm-20241223-slim with apt on the Debian snapshot of 2025-01-14,
# python-can 4.5.0 (2024-11-28) and its dependencies pinned. The kernel version is not printed.
# The references (Bosch and TI PDFs) are not used by the computation: bash rejouer.sh refs downloads them into ref/.
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
  prendre bosch-can2.pdf https://www.nxp.com/docs/en/reference-manual/BCANPSV2.pdf 4cdadf8a70719f30b9c4bb34866424593d5b123e3c1cb27ad4015f0a5031975f
  prendre sloa101b.pdf https://www.ti.com/lit/an/sloa101b/sloa101b.pdf 32abab14388402ec313f77648f0b4dd3e986cc1ff18988f2e7549db3a665a694
  echo "références dans ref/"
  exit 0
fi

PY=python:3.13.1-slim-bookworm@sha256:031ebf3cde9f3719d2db385233bcb18df5162038e9cda20e64e08f49f4b47a2f
DEB=debian:bookworm-20241223-slim@sha256:d365f4920711a9074c4bcd178e8f457ee59250426441ab2a5f8106ed8fe948eb
SNAP=20250114T000000Z
# apt on the snapshot of the article date (bookworm, bookworm-updates, bookworm-security)
SOURCES="rm -f /etc/apt/sources.list.d/debian.sources; printf '%s\n' \
 'deb http://snapshot.debian.org/archive/debian/$SNAP bookworm main' \
 'deb http://snapshot.debian.org/archive/debian/$SNAP bookworm-updates main' \
 'deb http://snapshot.debian.org/archive/debian-security/$SNAP bookworm-security main' > /etc/apt/sources.list"
# pull first, so that the pull messages do not end up in raw/
docker pull -q "$PY" >/dev/null; docker pull -q "$DEB" >/dev/null
PIP="python-can==4.5.0 wrapt==1.17.1 packaging==24.2 typing_extensions==4.12.2 msgpack==1.1.0"

# 02: the computation (CRC-15, frame, arbitration, error counters), pure Python, no library
docker run --rm --name deck-can-calc -v "$PWD":/w -w /w "$PY" sh -c 'echo "\$ python3 can_frame.py"; python3 --version; python3 can_frame.py; echo "exit=$?"' > raw/02-can_frame.txt

# 01 and 04: kernel virtual bus (vcan), privileged container
docker run --rm --name deck-can-vcan --privileged -v "$PWD":/w "$DEB" bash -c "$SOURCES; bash /w/vcan-try.sh" > raw/01-vcan-try.txt 2>&1 || true
docker run --rm --name deck-can-vcan2 --privileged -v "$PWD":/w "$DEB" bash -c "$SOURCES; bash /w/vcan-try2.sh" > raw/04-vcan-clean.txt 2>&1 || true

# 03: python-can virtual bus (no CAN kernel support needed)
docker run --rm --name deck-can-pycan -v "$PWD":/w "$PY" sh -c "pip install -q $PIP >/dev/null 2>&1; echo '\$ python /w/pycan_demo.py'; python /w/pycan_demo.py" > raw/03-pycan-virtual.txt 2>&1

echo "Sorties dans raw/. Comparer avec git diff."
