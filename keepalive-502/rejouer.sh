#!/bin/bash
# Replays the keep-alive bench of the deck https://heurisme.fr/en/blog/keepalive-502/
# Needs Docker. Image debian:bookworm-20261005 pinned by digest, apt pointed at the Debian snapshot
# of 2026-10-14 (the day before the article): nginx 1.22.1, Node.js 18.20.4, Python 3.11.
# No other network call, no third-party data. Takes about 30 minutes.
set -eu
cd "$(dirname "$0")"

# Container: Debian 12 arm64 (remove --platform on an x86_64 machine).
IMAGE=debian:bookworm-20261005@sha256:2c037a04925515fdd6ea85ea14a682d0e79931f5e9f5d07b6dbfc6ba12f9e858
SNAP=20261014T000000Z
docker rm -f deck-keepalive-502 >/dev/null 2>&1 || true
docker run -d --name deck-keepalive-502 --platform linux/arm64 -v "$PWD":/w "$IMAGE" sleep infinity >/dev/null
docker exec deck-keepalive-502 bash -c "rm -f /etc/apt/sources.list.d/debian.sources && printf '%s\\n' \
  'deb http://snapshot.debian.org/archive/debian/$SNAP bookworm main' \
  'deb http://snapshot.debian.org/archive/debian-security/$SNAP bookworm-security main' > /etc/apt/sources.list"
docker exec deck-keepalive-502 bash -c 'apt-get -o Acquire::Check-Valid-Until=false update -qq && apt-get install -y -qq nginx-light nodejs python3 >/dev/null 2>&1'
mkdir -p sorties
docker exec deck-keepalive-502 bash -c 'dpkg-query -W nginx-light nodejs python3' > sorties/00-versions.txt

# the four scenarios, then sorties/01 to 04
docker exec deck-keepalive-502 bash /w/calcule.sh

docker rm -f deck-keepalive-502 >/dev/null
echo "Outputs in sorties/. The 502 counts change from run to run: compare the median, not the bytes."
