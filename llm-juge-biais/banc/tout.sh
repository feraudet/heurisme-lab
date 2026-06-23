#!/bin/bash
# Replay the whole bench, sequentially (one model call at a time).
cd "$(dirname "$0")"; export HF_HUB_OFFLINE=1
python3 paires.py >/dev/null
i=1
for j in ${JUGES:-qwen phi4}; do
  i=1
  for p in naif egalite grille reference note; do
    ./tourne.sh "0$i-$j-$p" python3 juge.py --juge $j --protocole $p >/dev/null; i=$((i+1))
  done
done
