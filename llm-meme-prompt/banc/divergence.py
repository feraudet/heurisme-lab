"""Two identical requests sent at the same time (temperature 0, seed 42, long prompt).
Shows where the two answers split, with the two best candidates at that token in each answer.
usage: python3 divergence.py [--lang en] [--depuis sorties/divergence.json]"""
import argparse, os, hashlib, json, math, urllib.request
from concurrent.futures import ThreadPoolExecutor

LONG = "Écris un paragraphe de cinq phrases sur un chat qui s'appelle Mia."
a = argparse.ArgumentParser(); a.add_argument("--lang", default="fr"); a.add_argument("--depuis"); a = a.parse_args()
corps = json.dumps({"model": "phi4", "prompt": LONG, "stream": False, "logprobs": True, "top_logprobs": 2,
                    "options": {"temperature": 0, "seed": 42, "num_predict": 200}}).encode()
def un(_):
    return json.load(urllib.request.urlopen(urllib.request.Request(os.environ.get("OLLAMA_URL", "http://localhost:11434") + "/api/generate", corps,
                                            {"Content-Type": "application/json"}), timeout=600))
if a.depuis:
    rs = json.load(open(a.depuis))
else:
    with ThreadPoolExecutor(2) as ex: rs = list(ex.map(un, range(2)))
    rs = [{"cached": r.get("prompt_eval_cached_count", "-"), "response": r["response"],
           "logprobs": [{"token": t["token"], "top": [[x["token"], x["logprob"]] for x in t["top_logprobs"]]}
                        for t in r["logprobs"]]} for r in rs]
    json.dump(rs, open("sorties/divergence.json", "w"), ensure_ascii=False)
en = a.lang == "en"
for k, r in enumerate(rs, 1):
    h = hashlib.sha256(r["response"].strip().encode()).hexdigest()[:12]
    print(f"{'answer' if en else 'réponse'} {k}: cached={r['cached']} sha256={h} tokens={len(r['logprobs'])}")
i = next((i for i, (x, y) in enumerate(zip(rs[0]["logprobs"], rs[1]["logprobs"])) if x["token"] != y["token"]), None)
if i is None:
    print("same tokens from start to end" if en else "mêmes tokens du début à la fin"); raise SystemExit
debut = "".join(t["token"] for t in rs[0]["logprobs"][max(0, i - 12):i])
print(f"{'first different token: no.' if en else 'premier token différent : n°'} {i + 1}")
print(f"{'common text before' if en else 'texte commun juste avant'}: …{debut!r}")
for k, r in enumerate(rs, 1):
    t = r["logprobs"][i]
    cand = "   ".join(f"{tok!r} {math.exp(lp):.4f}" for tok, lp in t["top"])
    print(f"{'answer' if en else 'réponse'} {k} {'picks' if en else 'prend'} {t['token']!r:<10} | {'top 2' if en else '2 meilleurs'}: {cand}")
