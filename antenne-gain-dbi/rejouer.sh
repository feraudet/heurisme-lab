#!/bin/bash
# Replays the bench of the deck https://heurisme.fr/en/blog/antenne-gain-dbi/
# Needs Docker only. Image debian:bookworm-20261005 pinned by digest, apt pointed at the Debian snapshot
# of 2026-10-14 (the day before the article): nec2c 1.3-4, Python 3.11. No other network access.
#   bash rejouer.sh     writes nec/*.nec, runs nec2c into travail/, then rewrites sorties/
set -eu
cd "$(dirname "$0")"

# Container: Debian 12 arm64 (remove --platform on an x86_64 machine).
IMAGE=debian:bookworm-20261005@sha256:2c037a04925515fdd6ea85ea14a682d0e79931f5e9f5d07b6dbfc6ba12f9e858
SNAP=20261014T000000Z
NOM=deck-antenne-gain
docker rm -f $NOM >/dev/null 2>&1 || true
docker run -d --name $NOM --platform linux/arm64 -v "$PWD":/w -w /w "$IMAGE" sleep infinity >/dev/null
docker exec $NOM bash -c "rm -f /etc/apt/sources.list.d/debian.sources && printf '%s\\n' \
  'deb http://snapshot.debian.org/archive/debian/$SNAP bookworm main' \
  'deb http://snapshot.debian.org/archive/debian/$SNAP bookworm-updates main' \
  'deb http://snapshot.debian.org/archive/debian-security/$SNAP bookworm-security main' > /etc/apt/sources.list"
docker exec $NOM bash -c 'apt-get -o Acquire::Check-Valid-Until=false update -qq && apt-get install -y -qq nec2c python3 >/dev/null'

# 1. NEC2 input files (versioned in nec/)
docker exec $NOM python3 -I modeles.py nec

# 2. nec2c, one run per antenna. The .out files print run times in msec: they stay in travail/, not versioned.
rm -rf travail && mkdir -p travail
for a in dipole fouet yagi colineaire; do
  docker exec $NOM nec2c -inec/$a.nec -otravail/$a.out
done

# 3. Outputs
mkdir -p sorties
{ echo '$ nec2c -v; python3 --version; dpkg-query -W nec2c'
  docker exec $NOM bash -c 'nec2c -v; python3 --version; dpkg-query -W nec2c'; echo "(exit $?)"; } > sorties/00-versions.txt
n=1
for etape in gains conservation toit; do
  { echo "\$ python3 analyse.py $etape"; docker exec $NOM python3 -I analyse.py $etape; echo "(exit $?)"; } > "sorties/0$n-$etape.txt"
  n=$((n + 1))
done
docker exec $NOM python3 -I analyse.py json > sorties/diagrammes.json

docker rm -f $NOM >/dev/null
echo "Outputs in sorties/. Compare with git diff."
