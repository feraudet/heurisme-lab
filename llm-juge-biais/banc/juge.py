"""Has an LLM judge the 30 pairs, in both orders, temperature 0.

  python3 juge.py --juge qwen --protocole naif
  python3 juge.py --juge phi4 --protocole grille

Judges:
  qwen: mlx-community/Qwen2.5-7B-Instruct-4bit, locally through mlx_lm (greedy sampling)
  phi4: phi4 through the local Ollama API (temperature 0, seed 0)

Protocols:
  naif      : "Which answer is better? Answer A or B." (the actual prompt is in French)
  egalite   : the same question, with "egalite" (tie) allowed (no criteria)
  grille    : explicit criteria (accuracy, information, concision), tie allowed, JSON output
  reference : the grid, plus a reference answer
  note      : each answer scored alone from 1 to 10 (no pair, so no order)

Each call (full prompt, raw output, parsed verdict) goes to verdicts/<judge>-<protocol>.jsonl.
"""
import argparse
import json
import os
import re
import urllib.request
from pathlib import Path

ICI = Path(__file__).parent
PAIRES = json.loads((ICI / "paires.json").read_text())

NAIF = """Voici une question technique et deux réponses.

Question : {q}

[Réponse A]
{a}

[Réponse B]
{b}

Quelle réponse est la meilleure ? Réponds uniquement par la lettre A ou B."""

GRILLE = """Tu évalues deux réponses à une question technique.

Question : {q}
{ref}
[Réponse A]
{a}

[Réponse B]
{b}

Applique ces critères, dans cet ordre :
1. Exactitude : une réponse qui contient une erreur technique perd, quelle que soit sa longueur.
2. Information : compte seulement les faits utiles pour répondre à la question.
3. Concision : une phrase qui n'ajoute aucun fait (introduction, reformulation, conclusion, politesse) ne rapporte rien.
Si les deux réponses sont exactes et donnent les mêmes faits, le verdict est "egalite".

Réponds uniquement avec un objet JSON, sans texte autour :
{{"exacte_A": true ou false, "exacte_B": true ou false, "faits_en_plus": "A" ou "B" ou "aucun", "verdict": "A" ou "B" ou "egalite"}}"""

EGALITE = NAIF.replace("Réponds uniquement par la lettre A ou B.",
                      "Réponds uniquement par A, par B, ou par egalite si elles se valent.")

REF = "\nRéponse de référence (exacte, à utiliser pour juger) : {r}\n"

NOTE = """Voici une question technique et une réponse.

Question : {q}

Réponse :
{a}

Note la qualité de cette réponse de 1 à 10. Réponds uniquement par le nombre."""


class Qwen:
    nom = "mlx-community/Qwen2.5-7B-Instruct-4bit"

    def __init__(self):
        from mlx_lm import load
        self.model, self.tok = load(self.nom)

    def __call__(self, prompt, max_tokens):
        from mlx_lm import generate
        texte = self.tok.apply_chat_template([{"role": "user", "content": prompt}],
                                             tokenize=False, add_generation_prompt=True)
        # no sampler: greedy decoding, the equivalent of temperature 0
        return generate(self.model, self.tok, prompt=texte, max_tokens=max_tokens, verbose=False)


class Phi4:
    nom = "phi4 (Ollama)"

    def __call__(self, prompt, max_tokens):
        corps = json.dumps({"model": "phi4", "stream": False,
                            "messages": [{"role": "user", "content": prompt}],
                            "options": {"temperature": 0, "seed": 0, "num_predict": max_tokens}}).encode()
        req = urllib.request.Request(os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434") + "/api/chat", data=corps,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.loads(r.read())["message"]["content"]


def lit_lettre(sortie):
    m = re.search(r"\b([AB])\b", sortie)
    return m.group(1) if m else "?"


def lit_json(sortie):
    m = re.search(r"\{.*\}", sortie, re.S)
    if not m:
        return "?"
    try:
        v = json.loads(m.group(0)).get("verdict", "?")
    except json.JSONDecodeError:
        m2 = re.search(r'"verdict"\s*:\s*"(\w+)"', sortie)
        v = m2.group(1) if m2 else "?"
    v = str(v).strip().lower()
    return {"a": "A", "b": "B", "egalite": "egalite", "égalité": "egalite"}.get(v, "?")


def contenu(verdict, ordre):
    """Translates A/B into bonne/autre (good/other) according to the presentation order."""
    if verdict in ("egalite", "?"):
        return verdict
    if ordre == "AB":  # the good answer is in A
        return "bonne" if verdict == "A" else "autre"
    return "autre" if verdict == "A" else "bonne"


# Displayed labels. --lang en translates the display only: prompts and data stay in French.
EN = {"bonne": "good", "autre": "other", "egalite": "tie", "longueur": "padding", "fausse": "wrong",
      "fausse-longue": "wrong-padded", "accord": "agree", "DÉSACCORD": "DISAGREE"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--juge", choices=["qwen", "phi4"], required=True)
    ap.add_argument("--protocole", choices=["naif", "egalite", "grille", "reference", "note"], required=True)
    ap.add_argument("--lang", choices=["fr", "en"], default="fr")
    a = ap.parse_args()
    t = (lambda x: EN.get(x, x)) if a.lang == "en" else (lambda x: x)
    juge = Qwen() if a.juge == "qwen" else Phi4()
    rep = ICI / ("verdicts" if a.lang == "fr" else "verdicts-en")
    rep.mkdir(exist_ok=True)
    out = (rep / f"{a.juge}-{a.protocole}.jsonl").open("w")
    if a.lang == "fr":
        print(f"juge={juge.nom} protocole={a.protocole} paires={len(PAIRES)}")
    else:
        print(f"judge={juge.nom} protocol={a.protocole} pairs={len(PAIRES)}")
    for p in PAIRES:
        if a.protocole == "note":
            notes = {}
            for qui in ("bonne", "autre"):
                prompt = NOTE.format(q=p["question"], a=p[qui])
                brut = juge(prompt, 4)
                m = re.search(r"\d+", brut)
                notes[qui] = int(m.group(0)) if m else None
                out.write(json.dumps({"id": p["id"], "type": p["type"], "reponse": qui, "prompt": prompt,
                                      "sortie": brut, "note": notes[qui]}, ensure_ascii=False) + "\n")
            print(f"{p['id']:02d} {t(p['type']):13s} {t('bonne')}={notes['bonne']} {t('autre')}={notes['autre']}")
            continue
        lu = {}
        for ordre in ("AB", "BA"):
            x, y = (p["bonne"], p["autre"]) if ordre == "AB" else (p["autre"], p["bonne"])
            if a.protocole == "naif":
                prompt = NAIF.format(q=p["question"], a=x, b=y)
                brut = juge(prompt, 4)
                v = lit_lettre(brut)
            elif a.protocole == "egalite":
                prompt = EGALITE.format(q=p["question"], a=x, b=y)
                brut = juge(prompt, 5)
                v = "egalite" if "egalit" in brut.lower() else lit_lettre(brut)
            else:
                ref = REF.format(r=p["reference"]) if a.protocole == "reference" else ""
                prompt = GRILLE.format(q=p["question"], ref=ref, a=x, b=y)
                brut = juge(prompt, 80)
                v = lit_json(brut)
            lu[ordre] = (v, contenu(v, ordre))
            out.write(json.dumps({"id": p["id"], "type": p["type"], "ordre": ordre, "prompt": prompt,
                                  "sortie": brut, "verdict": v, "gagnant": lu[ordre][1]},
                                 ensure_ascii=False) + "\n")
        accord = t("accord" if lu["AB"][1] == lu["BA"][1] else "DÉSACCORD")
        ga, gb = ("bonne-en-A", "bonne-en-B") if a.lang == "fr" else ("good-in-A", "good-in-B")
        print(f"{p['id']:02d} {t(p['type']):13s} {ga}:{t(lu['AB'][0]):7s} {gb}:{t(lu['BA'][0]):7s} "
              f"-> {t(lu['AB'][1]):7s}/{t(lu['BA'][1]):7s} {accord}")
    out.close()


if __name__ == "__main__":
    main()
