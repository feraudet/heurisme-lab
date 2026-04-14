#!/bin/bash
# Replay the whole bench. Ollama 0.20.7 must be running with phi4 (OLLAMA_URL, default localhost:11434).
# The English outputs redisplay the same measurements (--depuis) without calling the model again.
cd "$(dirname "$0")" && mkdir -p sorties
r() { local f=$1; shift; { echo "\$ python3 $*"; python3 "$@"; } | tee "sorties/$f"; }
r 01-candidats.txt candidats.py
r 02-temperature.txt temperature.py
r 03-t08.txt essais.py --n 50 --temperature 0.8 --sortie sorties/03-t08.json
r 04-t0-seed.txt essais.py --n 50 --temperature 0 --seed 42 --sortie sorties/04-t0-seed.json
r 04b-t08-seed.txt essais.py --n 50 --temperature 0.8 --seed 42 --sortie sorties/04b-t08-seed.json
r 06-long-serie.txt essais.py --n 50 --temperature 0 --seed 42 --long --sortie sorties/06-long-serie.json
r 07-long-parallele.txt essais.py --n 50 --temperature 0 --seed 42 --long --parallele 8 --sortie sorties/07-long-parallele.json
r 05-flottants.txt flottants.py
r 08-trace-serie.txt trace.py --n 8 --sortie sorties/08-trace-serie.json
r 09-trace-parallele.txt trace.py --n 16 --parallele 8 --sortie sorties/09-trace-parallele.json
r 10-repete.txt repete.py
r 11-divergence.txt divergence.py
# English versions
r 01-candidats.en.txt candidats.py --depuis sorties/candidats.json --lang en
r 02-temperature.en.txt temperature.py --lang en
for f in 03-t08 04-t0-seed 04b-t08-seed 06-long-serie 07-long-parallele; do r $f.en.txt essais.py --depuis sorties/$f.json --lang en; done
r 05-flottants.en.txt flottants.py --lang en
for f in 08-trace-serie 09-trace-parallele; do r $f.en.txt trace.py --depuis sorties/$f.json --lang en; done
r 10-repete.en.txt repete.py --depuis sorties/repete.json --lang en
r 11-divergence.en.txt divergence.py --depuis sorties/divergence.json --lang en
# Prompt tokens reused from the cache, read from the server log (Ollama started with OLLAMA_DEBUG=1)
if [ -n "$OLLAMA_LOG" ]; then
  r 12-cache.txt cache_log.py "$OLLAMA_LOG"
  r 12-cache.en.txt cache_log.py "$OLLAMA_LOG" --lang en
fi
