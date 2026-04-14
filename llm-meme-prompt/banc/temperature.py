"""Worked example: the same distribution (real logprobs from candidats.json) seen at several temperatures,
then what top-k and top-p keep. Renormalized over the 10 known candidates.
usage: python3 temperature.py [--lang en]"""
import json, math, sys

en = "--lang" in sys.argv and sys.argv[sys.argv.index("--lang") + 1] == "en"
c = json.load(open("sorties/candidats.json"))
toks = [t["token"] for t in c]
lp = [t["logprob"] for t in c]

def dist(T):
    z = [l / T for l in lp]; m = max(z); e = [math.exp(v - m) for v in z]; s = sum(e)
    return [v / s for v in e]

print("token     " + "".join(f"T={T:<7}" for T in (0.2, 0.5, 0.8, 1.0, 1.5)))
ds = {T: dist(T) for T in (0.2, 0.5, 0.8, 1.0, 1.5)}
for k, t in enumerate(toks):
    print(f"{t!r:<9} " + "".join(f"{ds[T][k]:6.1%}  " for T in ds))
print()
p = dist(0.8)
print(("top_k=3   keeps: " if en else "top_k=3   garde : ") + ", ".join(repr(t) for t in toks[:3]))
cum, garde = 0, []
for t, v in zip(toks, p):
    garde.append(t); cum += v
    if cum >= 0.9: break
if en:
    print(f"top_p=0.9 at T=0.8 keeps: {', '.join(repr(t) for t in garde)} (cumulative {cum:.1%})")
else:
    print(f"top_p=0.9 à T=0.8 garde : {', '.join(repr(t) for t in garde)} (cumul {cum:.1%})")
json.dump({str(T): v for T, v in ds.items()} | {"tokens": toks}, open("sorties/temperature.json", "w"), ensure_ascii=False)
