#!/bin/bash
# tourne.sh <name> <command...>: runs the command from banc/, writes "$ command" then its output
# into $SORTIES/<name>.txt (sorties/ by default, sorties-en/ for the English version).
cd "$(dirname "$0")"; S=${SORTIES:-sorties}; mkdir -p "$S"; n=$1; shift
{ echo "\$ $*"; bash -c "$*" 2>&1; echo "[exit $?]"; } | tee "$S/$n.txt"
