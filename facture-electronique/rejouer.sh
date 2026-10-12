#!/bin/sh
# Replay the whole bench (Docker required). Downloads Mustang CLI, checks its sha256, builds the images, writes banc/sortie/.
cd "$(dirname "$0")/banc" && sh tout.sh
