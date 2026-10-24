#!/bin/bash
# Replays the eBUS bench of the article https://heurisme.fr/en/blog/ebus-trames/
# Needs Docker only. Image pinned by digest: python:3.13-slim-bookworm (Python 3.13.17).
# The references (eBUS specifications) are not used by the computation: bash rejouer.sh refs downloads them into ref/.
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
  prendre spec_prot_12_v1_3_1_e.pdf https://web.archive.org/web/20231110032014id_/https://ebus-wiki.org/lib/exe/fetch.php/ebus/spec_prot_12_v1_3_1_e.pdf c7dbee29aec443bceb0348374507dc9d996a10b561d204c8eb4a18a90c2f628a
  prendre spec_prot_7_v1_6_1_e.pdf https://web.archive.org/web/20240616075418id_/https://ebus-wiki.org/lib/exe/fetch.php/ebus/spec_prot_7_v1_6_1_e.pdf d1b0d86a4a58554afd95184712a1eca40d7ea5ad14aeb79797460879d214d92b
  echo "références dans ref/"
  exit 0
fi

PY=python:3.13-slim-bookworm@sha256:e32be0e55814a08977501ca863271d9bd02443710db8f2afaf8372e2c4508530
docker pull -q "$PY" >/dev/null
docker run --rm --name ebus-trames -v "$PWD":/w -w /w "$PY" sh -c 'echo "\$ python3 ebus_trames.py"; python3 --version; python3 ebus_trames.py; echo "exit=$?"' > raw/ebus_trames.txt

echo "Sortie dans raw/ebus_trames.txt. Comparer avec git diff."
