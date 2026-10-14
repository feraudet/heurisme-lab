#!/bin/bash
# Replays the bench of the deck https://heurisme.fr/en/blog/adressage-ip-radioamateur/
# Needs python3 (standard library only) and network access. No account, no key.
#   bash rejouer.sh          downloads raw/ again, then rewrites sorties/
#   bash rejouer.sh hors-ligne   rewrites sorties/ from the raw/ already there (no network)
set -eu
cd "$(dirname "$0")"

if [ "${1:-}" != hors-ligne ]; then
  rm -rf raw
  python3 -I collecte.py
fi
(cd raw >/dev/null && shasum -a 256 -c SHA256SUMS --quiet)

mkdir -p sorties
for etape in rdap bgp france; do
  case $etape in rdap) n=01;; bgp) n=02;; france) n=03;; esac
  { echo "\$ python3 analyse.py $etape"; python3 -I analyse.py $etape; echo "(exit $?)"; } > "sorties/$n-$etape.txt"
done
echo "Outputs in sorties/. Compare with git diff."
