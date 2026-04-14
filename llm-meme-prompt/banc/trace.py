"""Diagnostic: for each request of the long prompt (temperature 0, seed 42), the hash of the answer,
the model load time, the prompt tokens reused from the cache, and the settings of the llama-server (or ollama runner)
started by Ollama at that moment (-c context, -b batch, -ub micro-batch).
usage: python3 trace.py --n 10 [--parallele 8] [--sortie f.json] [--depuis f.json] [--lang en]"""
import argparse, os, hashlib, json, re, subprocess, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

LONG = "Écris un paragraphe de cinq phrases sur un chat qui s'appelle Mia."
a = argparse.ArgumentParser(); a.add_argument("--n", type=int, default=10); a.add_argument("--parallele", type=int, default=1)
a.add_argument("--sortie"); a.add_argument("--depuis"); a.add_argument("--lang", default="fr"); a = a.parse_args()

def reglages():
    ps = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True).stdout
    out = []
    for l in ps.splitlines():
        if "llama-server" in l and "--model" in l:
            g = lambda f: (re.search(rf" {f} (\S+)", l) or [None, "?"])[1]
            out.append(f"c={g('-c')} b={g('-b')} ub={g('-ub')}")
        elif "ollama runner" in l and "--model" in l:  # older Ollama: its own runner, context read from /api/ps
            api = json.load(urllib.request.urlopen(os.environ.get("OLLAMA_URL", "http://localhost:11434") + "/api/ps"))
            out.append("ollama runner c=" + ",".join(str(m.get("context_length", "?")) for m in api["models"]))
    return " + ".join(out) or "aucun"

corps = json.dumps({"model": "phi4", "prompt": LONG, "stream": False,
                    "options": {"temperature": 0, "seed": 42, "num_predict": 200}}).encode()
def un(k):
    d = json.load(urllib.request.urlopen(urllib.request.Request(os.environ.get("OLLAMA_URL", "http://localhost:11434") + "/api/generate", corps,
                                         {"Content-Type": "application/json"}), timeout=600))
    return [k, hashlib.sha256(d["response"].strip().encode()).hexdigest()[:12], round(d["load_duration"] / 1e9, 2),
            d.get("prompt_eval_cached_count", "-"), reglages(), round(time.time() - t0, 1)]

if a.depuis:
    d = json.load(open(a.depuis)); a.parallele, lignes = d["parallele"], d["lignes"]
else:
    t0 = time.time()
    with ThreadPoolExecutor(a.parallele) as ex:
        lignes = list(ex.map(un, range(1, a.n + 1)))
    if a.sortie: json.dump({"parallele": a.parallele, "lignes": lignes}, open(a.sortie, "w"))
en = a.lang == "en"
print(f"parallel={a.parallele}" if en else f"en parallèle={a.parallele}")
print("req  t(s)   load(s)  cached  sha256        runner" if en else
      "req  t(s)   load(s)  cached  sha256        runner")
for k, h, ld, c, rg, t in sorted(lignes, key=lambda x: x[5]):
    print(f"{k:>3}  {t:>5}  {ld:>7}  {c:>6}  {h}  {rg}")
