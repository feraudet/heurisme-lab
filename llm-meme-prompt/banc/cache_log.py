"""Prompt tokens reused from the cache, for each request of tout.sh, read from the Ollama server log.
Older Ollama versions do not return prompt_eval_cached_count in the API answer: their runner writes it
in the server log instead, at debug level (OLLAMA_DEBUG=1): 'loading cache slot ... prompt=31 used=30'.
The log lines come in the order of the requests, so they are grouped by step of tout.sh.
usage: python3 cache_log.py <server.log> [--lang en]"""
import re, sys

ETAPES = [("01-candidats", 1), ("03-t08", 50), ("04-t0-seed", 50), ("04b-t08-seed", 50), ("06-long-serie", 50),
          ("07-long-parallele", 50), ("08-trace-serie", 8), ("09-trace-parallele", 16), ("10-repete", 6),
          ("11-divergence", 2)]
en = "--lang" in sys.argv and sys.argv[sys.argv.index("--lang") + 1] == "en"
slots = [(int(m[2]), int(m[1])) for m in re.finditer(r'msg="loading cache slot" .*?prompt=(\d+) used=(\d+)', open(sys.argv[1]).read())]
if len(slots) != sum(n for _, n in ETAPES):
    sys.exit(f"{len(slots)} requests in the log, {sum(n for _, n in ETAPES)} expected")
print("step                requests  prompt tokens reused from the cache (used/prompt)" if en else
      "étape               requêtes  tokens du prompt repris du cache (repris/prompt)")
i = 0
for nom, n in ETAPES:
    groupes = []  # consecutive runs of the same value, in request order
    for u, p in slots[i:i + n]:
        if groupes and groupes[-1][0] == (u, p): groupes[-1][1] += 1
        else: groupes.append([(u, p), 1])
    i += n
    print(f"{nom:<20}{n:>8}  " + ", ".join(f"{u}/{p} ×{k}" for (u, p), k in groupes))
