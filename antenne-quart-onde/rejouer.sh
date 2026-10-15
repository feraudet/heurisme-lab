#!/bin/bash
# Replays the bench of the deck https://heurisme.fr/en/blog/antenne-quart-onde/
# Needs python3 (standard library only) and Docker. nec2c runs in a pinned Debian image.
#   bash rejouer.sh     rewrites nec/, runs nec2c into raw/, then rewrites sorties/
set -eu
cd "$(dirname "$0")"

IMAGE=debian@sha256:2c037a04925515fdd6ea85ea14a682d0e79931f5e9f5d07b6dbfc6ba12f9e858   # debian:bookworm, 2026-10-05
SNAPSHOT=http://snapshot.debian.org/archive/debian/20261010T000000Z                     # nec2c 1.3-4

python3 -I modele.py
rm -rf raw && mkdir -p raw sorties
docker run --rm -v "$PWD":/banc -w /banc "$IMAGE" bash -c "
  set -e
  echo 'deb [check-valid-until=no] $SNAPSHOT bookworm main' > /etc/apt/sources.list
  rm -f /etc/apt/sources.list.d/*
  apt-get update -qq && apt-get install -y -qq nec2c >/dev/null
  dpkg-query -W nec2c > raw/nec2c-version.txt
  for f in nec/*.nec; do nec2c -i \$f -o raw/\$(basename \$f .nec).out; done"

n=0
for etape in longueur epaisseur radians passerelle; do
  n=$((n + 1))
  { echo "\$ python3 analyse.py $etape"; python3 -I analyse.py $etape; echo "(exit $?)"; } > "sorties/0$n-$etape.txt"
done
echo "nec2c: $(cat raw/nec2c-version.txt)"
echo "Outputs in sorties/. Compare with git diff."
