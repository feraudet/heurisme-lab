"""The first runs (sorties/0[3467]*.txt) were launched before the --sortie option existed.
This script rereads their text output and rebuilds the raw JSON (answers and counts, total duration;
each individual duration is replaced by the displayed mean), so that essais.py --depuis
can redisplay the same measurement in English without calling the model again.
usage: python3 log2json.py sorties/03-t08.txt sorties/03-t08.json"""
import json, re, sys

src, dst = sys.argv[1], sys.argv[2]
txt = open(src).read().splitlines()
txt = [l for l in txt if not l.startswith("$ ")]
m = re.match(r"(\d+) essais, temperature=([\d.]+), seed=(\w+), en parallèle=(\d+), prompt=(\w+)", txt[0])
n, temp, seed, par, prompt = m.groups()
res = []
for l in txt[2:]:
    mm = re.match(r"\s*(\d+) × (.*)$", l)
    if not mm: break
    k, rep = int(mm.group(1)), mm.group(2)
    if prompt == "long":  # only the hash was displayed: keep hash and length
        h, lg = re.match(r"([0-9a-f]{12})  \((\d+) caractères\)", rep).groups()
        res += [{"sha": h, "len": int(lg)}] * k
    else:
        res += [json.loads(rep)] * k
mm = re.search(r"durée totale ([\d.]+) s, durée moyenne d'une requête ([\d.]+) s", txt[-1])
tot, moy = float(mm.group(1)), float(mm.group(2))
assert len(res) == int(n)
json.dump({"n": int(n), "temperature": float(temp), "seed": None if seed == "None" else int(seed),
           "parallele": int(par), "long": prompt == "long", "duree": tot, "res": [[r, moy] for r in res]},
          open(dst, "w"), ensure_ascii=False)
print(f"{dst} : {len(res)} réponses")
