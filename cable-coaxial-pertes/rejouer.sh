#!/bin/bash
# Replays the bench of the deck https://heurisme.fr/en/blog/cable-coaxial-pertes/
# Needs python3 (standard library only) and curl. No account, no key.
#   bash rejouer.sh              downloads the datasheets into raw/, checks their sha256, rewrites sorties/
#   bash rejouer.sh hors-ligne   rewrites sorties/ only (the figures are in fiches.py, no network)
set -eu
cd "$(dirname "$0")"

if [ "${1:-}" != hors-ligne ]; then
  mkdir -p raw
  grep -v '^#' sources-sha256.txt | while read -r sum name url; do
    curl -sSL --compressed -A "Mozilla/5.0" -o "raw/$name" "$url"
    echo "$sum  $name"
  done > raw/SHA256SUMS
  (cd raw >/dev/null && shasum -a 256 -c SHA256SUMS)
fi

mkdir -p sorties
n=0
for etape in db fiches tableau adsb bruit; do
  n=$((n + 1))
  { echo "\$ python3 pertes.py $etape"; python3 -I pertes.py $etape; echo "(exit $?)"; } > "sorties/0$n-$etape.txt"
done
echo "Outputs in sorties/. Compare with git diff."
