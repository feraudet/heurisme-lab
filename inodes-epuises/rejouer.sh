#!/bin/bash
# Replays the inode bench of the deck https://heurisme.fr/en/blog/inodes-epuises/
# Needs Docker. Image debian:bookworm-20261005 pinned by digest, apt pointed at the Debian snapshot
# of 2026-10-14 (the day before the article): e2fsprogs, xfsprogs and php8.2-cli.
# The container is privileged because it mounts small filesystem images through loop devices.
# Nothing is written outside this folder and the container. No third-party data is downloaded.
set -eu
cd "$(dirname "$0")"

# Container: Debian 12 arm64 (remove --platform on an x86_64 machine).
IMAGE=debian:bookworm-20261005@sha256:2c037a04925515fdd6ea85ea14a682d0e79931f5e9f5d07b6dbfc6ba12f9e858
SNAP=20261014T000000Z
NOM=deck-inodes-epuises
docker rm -f "$NOM" >/dev/null 2>&1 || true
docker run -d --name "$NOM" --privileged --platform linux/arm64 -v "$PWD":/w "$IMAGE" sleep infinity >/dev/null
docker exec "$NOM" bash -c "rm -f /etc/apt/sources.list.d/debian.sources && printf '%s\\n' \
  'deb http://snapshot.debian.org/archive/debian/$SNAP bookworm main' \
  'deb http://snapshot.debian.org/archive/debian-security/$SNAP bookworm-security main' > /etc/apt/sources.list"
docker exec "$NOM" bash -c 'apt-get -o Acquire::Check-Valid-Until=false update -qq && apt-get install -y -qq --no-install-recommends xfsprogs php8.2-cli >/dev/null 2>&1'
mkdir -p sorties
docker exec "$NOM" bash -c 'dpkg-query -W e2fsprogs xfsprogs coreutils php8.2-cli php-common' > sorties/00-versions.txt

# builds the images, fills them, writes sorties/01 to 06
docker exec "$NOM" bash /w/calcule.sh

docker rm -f "$NOM" >/dev/null
echo "Outputs in sorties/. Compare with git diff."
