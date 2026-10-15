#!/bin/bash
# Replays the SWR bench of the deck https://heurisme.fr/en/blog/antenne-ros/
# Needs Docker. Image debian:bookworm-20261005 pinned by digest, apt pointed at the Debian snapshot
# of 2026-10-14 (the day before the article): nec2c 1.3-4 and Python 3.11.
# No other network call. The cable data sheets are cited in README.md (address and sha256), not copied.
set -eu
cd "$(dirname "$0")"

# Container: Debian 12 arm64 (remove --platform on an x86_64 machine).
IMAGE=debian:bookworm-20261005@sha256:2c037a04925515fdd6ea85ea14a682d0e79931f5e9f5d07b6dbfc6ba12f9e858
SNAP=20261014T000000Z
docker rm -f deck-antenne-ros >/dev/null 2>&1 || true
docker run -d --name deck-antenne-ros --platform linux/arm64 -v "$PWD":/w "$IMAGE" sleep infinity >/dev/null
docker exec deck-antenne-ros bash -c "rm -f /etc/apt/sources.list.d/debian.sources && printf '%s\\n' \
  'deb http://snapshot.debian.org/archive/debian/$SNAP bookworm main' > /etc/apt/sources.list"
docker exec deck-antenne-ros bash -c 'apt-get -o Acquire::Check-Valid-Until=false update -qq && apt-get install -y -qq nec2c python3 >/dev/null'
mkdir -p sorties
docker exec deck-antenne-ros bash -c 'dpkg-query -W nec2c python3' > sorties/00-versions.txt

# writes nec/*.nec, runs nec2c on each deck (nec/*.out), then sorties/01 to 03
docker exec deck-antenne-ros bash /w/calcule.sh

docker rm -f deck-antenne-ros >/dev/null
echo "Outputs in sorties/. Compare with git diff."
