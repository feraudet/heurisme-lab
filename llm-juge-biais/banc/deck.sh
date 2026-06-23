#!/bin/bash
# Produces the outputs shown in the deck, in French (sorties/) then in English (sorties-en/).
# Run after tout.sh (the verdicts must exist). The only call to the judge here is the rerun
# of qwen naif in English (translated display, same prompts), for slide 3 of en.html.
cd "$(dirname "$0")"; export HF_HUB_OFFLINE=1
SORTIES=sorties-en ./tourne.sh 01-qwen-naif "python3 juge.py --juge qwen --protocole naif --lang en" >/dev/null
for L in fr en; do
  if [ $L = fr ]; then export SORTIES=sorties; o=""; else export SORTIES=sorties-en; o=" --lang en"; fi
  ./tourne.sh 10-paires "python3 paires.py$o" >/dev/null
  ./tourne.sh 11-paire-1 "python3 brut.py paire 1$o" >/dev/null
  ./tourne.sh 13-fausses "python3 brut.py paire 28$o; grep -E '^(2[1-9]|30) ' $SORTIES/01-qwen-naif.txt" >/dev/null
  ./tourne.sh 14-brut-grille-7 "python3 brut.py qwen grille 7 BA$o" >/dev/null
  ./tourne.sh 16-brut-phi4-grille-1 "python3 brut.py phi4 grille 1 AB$o" >/dev/null
  for a in ordre longueur parades notes; do ./tourne.sh 15-analyse-$a "python3 analyse.py $a$o" >/dev/null; done
done
