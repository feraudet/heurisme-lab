#!/bin/bash
# Replays the AX.25 / APRS bench of the deck https://heurisme.fr/en/blog/ax25-aprs/
# Needs Docker. Image debian:trixie-20251117 pinned by digest, apt pointed at the Debian snapshot
# of 2025-12-09 (the date of the article). No network call outside apt in the container. Third-party references (PDFs, Dire Wolf sources) are
# downloaded separately into ref/ by: bash rejouer.sh refs
set -eu
cd "$(dirname "$0")"

prendre() { # prendre <fichier> <url> <sha256>
  mkdir -p ref
  [ -f "ref/$1" ] || curl -fsSL -o "ref/$1" "$2"
  got=$(shasum -a 256 "ref/$1" | cut -d' ' -f1)
  if [ "$got" != "$3" ]; then
    echo "sha256 différent pour $1 (attendu $3, obtenu $got) : la source en ligne a changé depuis l'enregistrement du sha256" >&2
    [ "${TOLERE:-0}" = 1 ] || exit 1
  fi
}

if [ "${1:-}" = refs ]; then
  prendre APRS101.pdf https://raw.githubusercontent.com/wb2osz/aprsspec/main/APRS101.pdf 53c2dd1c5d7ac3e55c71c1e15037b67340178244245f67e30c079f4278a5ba2c
  prendre APRS12c.pdf https://raw.githubusercontent.com/wb2osz/aprsspec/main/APRS12c.pdf f769ab07a30b982b4da761cc9b4e2f53e252bafe5fa9bce999e6a6bb360a0f03
  prendre APRS-Digipeater-Algorithm.pdf https://raw.githubusercontent.com/wb2osz/aprsspec/main/APRS-Digipeater-Algorithm.pdf 6f0014badfeaa6fedb5f72a53aa59958137618e7fb78baa7c12e287277ad3699
  prendre ax25-2.2.pdf "https://www.ax25.net/AX25.2.2-Jul%2098-2.pdf" 5a4aac0bc10a69c5c983c35d5a84cc47ff204fa785a765fa1d2d6dd620131350
  prendre User-Guide.pdf https://raw.githubusercontent.com/wb2osz/direwolf/master/doc/User-Guide.pdf 6aac1013529b750ab93274a04b1aeee6ada37a59544b6a2ff5a76d1def7982ed
  prendre kiss.aspx http://www.ax25.net/kiss.aspx d4a9c4f56295407da0fefd3a68ebd631d2333e6f1d07bac45726d8217868f949
  prendre hdlc_send.c https://raw.githubusercontent.com/wb2osz/direwolf/master/src/hdlc_send.c e3f8bc114e947b296e0774b9709042cd30be61a9f2d9b9332a0937b6fdc510ca
  prendre fcs_calc.c https://raw.githubusercontent.com/wb2osz/direwolf/master/src/fcs_calc.c c6fa259b6132228ca2437e403172e89fff26b4fbb31a2fe41054eee03b0af4bd
  prendre demod_9600.h https://raw.githubusercontent.com/wb2osz/direwolf/master/src/demod_9600.h bb985f97423c0e331b49877cb25591fe52e99e5d15e5afeac8a12a2f93c40ec7
  echo "références dans ref/"
  exit 0
fi

# Container: Debian 13 arm64 (remove --platform on an x86_64 machine).
# Image of 2025-11-17 pinned by digest; apt reads the snapshot of 2025-12-09 (packages of that day).
IMAGE=debian:trixie-20251117@sha256:8f6a88feef3ed01a300dafb87f208977f39dccda1fd120e878129463f7fa3b8f
SNAP=20251209T000000Z
docker rm -f deck-ax25-dw >/dev/null 2>&1 || true
docker run -d --name deck-ax25-dw --platform linux/arm64 --privileged -v "$PWD":/w "$IMAGE" sleep infinity
docker exec deck-ax25-dw bash -c "rm -f /etc/apt/sources.list.d/debian.sources && printf '%s\\n' \
  'deb http://snapshot.debian.org/archive/debian/$SNAP trixie main' \
  'deb http://snapshot.debian.org/archive/debian/$SNAP trixie-updates main' \
  'deb http://snapshot.debian.org/archive/debian-security/$SNAP trixie-security main' > /etc/apt/sources.list"
docker exec deck-ax25-dw bash -c 'apt-get -o Acquire::Check-Valid-Until=false update -qq && apt-get install -y -qq direwolf python3 python3-numpy kmod pv'
docker exec deck-ax25-dw useradd -m ham

# 00 to 05: run.sh writes raw/00 to raw/05 (.ansi and .txt)
docker exec -u ham deck-ax25-dw bash /w/run.sh

# 06: the Docker kernel has no ax25 module (a single attempt, as root)
# modprobe -q: the error message would print the Docker Desktop kernel version, which is not part of the bench
C6='modprobe -q ax25; echo "modprobe ax25 : exit $?"; python3 -c "import socket; socket.socket(3, socket.SOCK_SEQPACKET)"'
{ echo "\$ $C6"
  rc=0
  docker exec deck-ax25-dw bash -c "$C6" 2>&1 || rc=$?
  echo "(exit $rc)"; } > raw/06-noyau.txt

# 07: hand-built frame, FCS, demodulation of p1.wav (writes work/signal.json)
{ echo '$ python3 ax25_frame.py'; docker exec -u ham -w /w/work deck-ax25-dw python3 ax25_frame.py; echo "(exit $?)"; } > raw/07-ax25_frame.txt

docker rm -f deck-ax25-dw >/dev/null
echo "Sorties dans raw/. Comparer avec git diff."
