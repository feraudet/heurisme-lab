"""Displays a pair, or a raw call to the judge (full prompt and output).

  python3 brut.py paire 7                 : the question and the two answers of pair 7
  python3 brut.py qwen grille 7 AB        : the prompt sent and the raw output of the judge
Add --lang en for English labels (the data, prompts and judge outputs stay as they are).
"""
import json
import sys
from pathlib import Path

ICI = Path(__file__).parent
args = sys.argv[1:]
EN = False
if "--lang" in args:
    k = args.index("--lang")
    EN = args[k + 1] == "en"
    del args[k:k + 2]
TYPES = {"longueur": "padding", "fausse": "wrong", "fausse-longue": "wrong-padded"}
QUI = {"bonne": "good", "autre": "other", "egalite": "tie"}


def T(fr, en):
    return en if EN else fr


if args[0] == "paire":
    p = next(x for x in json.loads((ICI / "paires.json").read_text()) if x["id"] == int(args[1]))
    typ = TYPES[p["type"]] if EN else p["type"]
    print(T(f"paire {p['id']} ({typ}) : {p['question']}", f"pair {p['id']} ({typ}): {p['question']}"))
    print(T(f"[bonne, {len(p['bonne'])} car.] {p['bonne']}", f"[good, {len(p['bonne'])} chars] {p['bonne']}"))
    print(T(f"[autre, {len(p['autre'])} car.] {p['autre']}", f"[other, {len(p['autre'])} chars] {p['autre']}"))
else:
    juge, proto, n, ordre = args[:4]
    for l in (ICI / "verdicts" / f"{juge}-{proto}.jsonl").open():
        r = json.loads(l)
        if r["id"] == int(n) and r.get("ordre") == ordre:
            print(T("----- prompt -----", "----- prompt -----"))
            print(r["prompt"])
            print(T("----- sortie brute du juge -----", "----- raw judge output -----"))
            print(r["sortie"])
            g = QUI.get(r["gagnant"], r["gagnant"]) if EN else r["gagnant"]
            print(T(f"----- verdict lu : {r['verdict']} -> gagnant : {g}",
                    f"----- parsed verdict: {r['verdict']} -> winner: {g}"))
