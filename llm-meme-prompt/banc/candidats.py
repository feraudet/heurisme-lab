"""Probabilities of the candidate tokens for the first token of the answer (Ollama, logprobs).
usage: python3 candidats.py [--lang en] [--depuis sorties/candidats.json]
Without --depuis, queries Ollama and saves sorties/candidats.json."""
import argparse, os, json, math, urllib.request

PROMPT = "Donne un prénom pour un chat. Réponds par un seul mot."
a = argparse.ArgumentParser(); a.add_argument("--lang", default="fr"); a.add_argument("--depuis")
a.add_argument("--modele", default="phi4"); a = a.parse_args()
en = a.lang == "en"

if a.depuis:
    top = json.load(open(a.depuis))
else:
    corps = {"model": a.modele, "prompt": PROMPT, "stream": False, "logprobs": True, "top_logprobs": 10,
             "options": {"temperature": 0, "num_predict": 1, "seed": 42}}
    req = urllib.request.Request(os.environ.get("OLLAMA_URL", "http://localhost:11434") + "/api/generate", json.dumps(corps).encode(),
                                 {"Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=300))
    top = d["logprobs"][0]["top_logprobs"]
    json.dump(top, open("sorties/candidats.json", "w"), ensure_ascii=False, indent=1)

print(f"prompt{'' if en else ' '}: {PROMPT}")
print(f"token chosen at temperature 0: {top[0]['token']!r}" if en else f"token choisi à temperature 0 : {top[0]['token']!r}")
print("rank  token     logprob   probability" if en else "rang  token     logprob   probabilité")
total = 0
for k, t in enumerate(top, 1):
    p = math.exp(t["logprob"]); total += p
    print(f"{k:>4}  {t['token']!r:<8} {t['logprob']:>8.3f}   {p:6.1%}")
print(f"sum of the top 10: {total:.1%}" if en else f"somme des 10 premiers : {total:.1%}")
