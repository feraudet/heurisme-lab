"""Sends the same prompt N times to Ollama and counts the distinct answers.
usage: python3 essais.py --n 50 --temperature 0.8 [--seed 42] [--parallele 8] [--long]
                          [--sortie f.json] [--depuis f.json] [--lang fr|en]
--sortie saves the raw answers; --depuis redisplays a saved run without calling the model again
(used to produce the English version of the same measurement)."""
import argparse, os, collections, hashlib, json, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

COURT = "Donne un prénom pour un chat. Réponds par un seul mot."
LONG = "Écris un paragraphe de cinq phrases sur un chat qui s'appelle Mia."

a = argparse.ArgumentParser()
a.add_argument("--n", type=int, default=50); a.add_argument("--temperature", type=float, default=0.8)
a.add_argument("--seed", type=int); a.add_argument("--parallele", type=int, default=1)
a.add_argument("--long", action="store_true"); a.add_argument("--modele", default="phi4")
a.add_argument("--sortie"); a.add_argument("--depuis"); a.add_argument("--lang", default="fr")
a = a.parse_args()

if a.depuis:
    d = json.load(open(a.depuis))
    for k in ("n", "temperature", "seed", "parallele", "long"): setattr(a, k, d[k])
    res, duree = [(json.dumps(x[0]) if isinstance(x[0], dict) else x[0], x[1]) for x in d["res"]], d["duree"]
else:
    opts = {"temperature": a.temperature, "num_predict": 200 if a.long else 8}
    if a.seed is not None: opts["seed"] = a.seed
    corps = json.dumps({"model": a.modele, "prompt": LONG if a.long else COURT, "stream": False, "options": opts}).encode()

    def un(_):
        for essai in range(3):  # the server is shared: retry a request that got no answer
            t = time.time()
            try:
                r = urllib.request.urlopen(urllib.request.Request(os.environ.get("OLLAMA_URL", "http://localhost:11434") + "/api/generate", corps,
                                           {"Content-Type": "application/json"}), timeout=180)
                return json.load(r)["response"].strip(), time.time() - t
            except OSError:
                if essai == 2: raise

    t0 = time.time()
    with ThreadPoolExecutor(a.parallele) as ex:
        res = list(ex.map(un, range(a.n)))
    duree = time.time() - t0
    if a.sortie:
        json.dump({"n": a.n, "temperature": a.temperature, "seed": a.seed, "parallele": a.parallele,
                   "long": a.long, "duree": duree, "res": res}, open(a.sortie, "w"), ensure_ascii=False)

rep = collections.Counter(r for r, _ in res)
moy = sum(d for _, d in res) / a.n
if a.lang == "en":
    print(f"{a.n} runs, temperature={a.temperature}, seed={a.seed}, parallel={a.parallele}, prompt={'long' if a.long else 'short'}")
    print(f"distinct answers: {len(rep)}")
else:
    print(f"{a.n} essais, temperature={a.temperature}, seed={a.seed}, en parallèle={a.parallele}, prompt={'long' if a.long else 'court'}")
    print(f"réponses distinctes : {len(rep)}")
for r, k in rep.most_common():
    car = "characters" if a.lang == "en" else "caractères"
    if a.long and r.startswith('{"sha"'):  # run reread by log2json: hash already computed
        e = json.loads(r); vu = e["sha"] + f"  ({e['len']} {car})"
    else:
        vu = json.dumps(r, ensure_ascii=False) if not a.long else hashlib.sha256(r.encode()).hexdigest()[:12] + f"  ({len(r)} {car})"
    print(f"{k:>4} × {vu}")
if a.lang == "en":
    print(f"total time {duree:.1f} s, mean time per request {moy:.2f} s")
else:
    print(f"durée totale {duree:.1f} s, durée moyenne d'une requête {moy:.2f} s")
