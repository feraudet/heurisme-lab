#!/bin/bash
# Runs inside the container: installs the pinned packages, then writes sorties/.
set -eu
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")"
pip install -q --no-cache-dir --no-deps --root-user-action=ignore --disable-pip-version-check -r requirements.txt
mkdir -p sorties
{ python3 --version; pip list --format=freeze --disable-pip-version-check | grep -Ei '^(tiktoken|tokenizers|regex)=='; } > sorties/00-versions.txt
for s in corpus accents decoupe exemple; do
  case $s in corpus) n=01;; accents) n=02;; decoupe) n=03;; exemple) n=04;; esac
  { echo "\$ python3 $s.py"; python3 $s.py; echo "(exit $?)"; } > sorties/$n-$s.txt
done
