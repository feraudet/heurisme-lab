"""The same request 6 times in a row (temperature 0, seed 42): exact logprob of the 'M' token,
and number of prompt tokens reused from the server cache.
usage: python3 repete.py [--lang en] [--depuis sorties/repete.json]"""
import argparse, os, json, urllib.request

PROMPT = "Donne un prénom pour un chat. Réponds par un seul mot."
a = argparse.ArgumentParser(); a.add_argument("--lang", default="fr"); a.add_argument("--depuis"); a = a.parse_args()
if a.depuis:
    lignes = json.load(open(a.depuis))
else:
    corps = json.dumps({"model": "phi4", "prompt": PROMPT, "stream": False, "logprobs": True, "top_logprobs": 3,
                        "options": {"temperature": 0, "num_predict": 1, "seed": 42}}).encode()
    lignes = []
    for k in range(1, 7):
        d = json.load(urllib.request.urlopen(urllib.request.Request(os.environ.get("OLLAMA_URL", "http://localhost:11434") + "/api/generate", corps,
                                             {"Content-Type": "application/json"}), timeout=300))
        lp = d["logprobs"][0]["top_logprobs"][0]
        lignes.append([k, d["prompt_eval_count"], d.get("prompt_eval_cached_count", "-"), lp["token"], lp["logprob"]])
    json.dump(lignes, open("sorties/repete.json", "w"), ensure_ascii=False)
print("run  prompt_eval_count  prompt_eval_cached_count  logprob('M')" if a.lang == "en" else
      "essai  prompt_eval_count  prompt_eval_cached_count  logprob('M')")
w = 3 if a.lang == "en" else 5
for k, n, c, tok, lp in lignes:
    print(f"{k:>{w}}  {n:>17}  {c:>24}  {tok!r} {lp!r}")
