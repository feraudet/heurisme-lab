"""10 factual questions about the inventory, asked with each format to phi4 (local Ollama).

temperature 0, seed 0, num_ctx 16384. Sequential calls. Free answer up to 1024 tokens;
kept answer: the last number (counting question) or the last line. Raw answers go to
data/qualite.jsonl (resumable: format/question pairs already done are skipped).
Usage: python banc/qualite.py        then   python banc/qualite.py --bilan
"""
import json
import os
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

from langue import f as fmt, t as tr

DATA = Path(__file__).resolve().parent.parent / "data"
SORTIE = DATA / "qualite.jsonl"
MODELE = "phi4-banc"  # local alias of phi4 (same weights), num_ctx 16384: see banc/Modelfile.phi4-banc
FORMATS = [("json-indente", "inventaire.json", "JSON"), ("json-minifie", "inventaire.min.json", "JSON"),
           ("yaml", "inventaire.yaml", "YAML"), ("csv", "inventaire.csv", "CSV"),
           ("markdown", "inventaire.md", "Markdown table"), ("xml", "inventaire.xml", "XML")]

L = json.loads((DATA / "inventaire.json").read_text())
H = {l["hostname"]: l for l in L}
cible_ip = H["api-050"]["ip"]
QUESTIONS = [
    ("q01", "How much RAM (in GB) does db-045 have?", str(H["db-045"]["ram_gb"])),
    ("q02", "What is the IP address of cache-088?", H["cache-088"]["ip"]),
    ("q03", "In which region is queue-017?", H["queue-017"]["region"]),
    ("q04", "What is the status of batch-060?", H["batch-060"]["status"]),
    ("q05", "Which OS does api-032 run?", H["api-032"]["os"]),
    ("q06", "What is the cost_eur of web-097?", str(H["web-097"]["cost_eur"])),
    ("q07", f"Which hostname has the IP address {cible_ip}?", "api-050"),
    ("q08", "How many servers have the status maintenance?",
     str(sum(l["status"] == "maintenance" for l in L))),
    ("q09", "How many servers are in env prod AND region eu-west-3?",
     str(sum(l["env"] == "prod" and l["region"] == "eu-west-3" for l in L))),
    ("q10", "Which hostname has the highest cost_eur?", max(L, key=lambda l: l["cost_eur"])["hostname"]),
]


def retenue(rep, attendu):
    """The kept answer: the last number in the text if an integer is expected, otherwise the last non-empty line."""
    if re.fullmatch(r"\d+", attendu):
        nums = re.findall(r"\d+(?:\.\d+)?", rep)
        return nums[-1] if nums else ""
    lignes = [l for l in rep.strip().splitlines() if l.strip()]
    return lignes[-1].strip() if lignes else ""


def juste(rep, attendu):
    r = retenue(rep, attendu).strip("`*\"'. ").lower()
    if re.fullmatch(r"\d+", attendu):
        return r == attendu
    return r == attendu.lower() or re.search(rf"(?<![\w.-]){re.escape(attendu.lower())}(?![\w-]|\.\d)", r) is not None


def appel(prompt):
    corps = {"model": MODELE, "prompt": prompt, "stream": False,
             "options": {"temperature": 0, "seed": 0, "num_ctx": 16384, "num_predict": 1024}}
    req = urllib.request.Request(os.environ.get("OLLAMA_URL", "http://localhost:11434") + "/api/generate", data=json.dumps(corps).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=3600) as r:
        return json.loads(r.read())


def bilan():
    lignes = [json.loads(x) for x in SORTIE.read_text().splitlines()]
    print(tr(f"modèle phi4 (alias {MODELE}), temperature 0, 10 questions par format\n",
             f"model phi4 (alias {MODELE}), temperature 0, 10 questions per format\n"))
    print(f"{'format':<13}{tr('justes', 'correct'):>7}  {tr('tokens du prompt (phi4)', 'prompt tokens (phi4)'):>23}   " + tr("fausses", "wrong"))
    for f, _, _ in FORMATS:
        r = [x for x in lignes if x["format"] == f]
        ok = sum(x["juste"] for x in r)
        tp = max(x["prompt_eval_count"] for x in r)
        faux = ", ".join(f"{x['q']}={retenue(x['reponse'], x['attendu'])!r}" for x in r if not x["juste"])
        print(f"{fmt(f):<13}{ok:>4}/10  {tp:>23}   {faux}")


if __name__ == "__main__":
    if "--bilan" in sys.argv:
        bilan(); sys.exit()
    fait = set()
    if SORTIE.exists():
        fait = {(j["format"], j["q"]) for j in map(json.loads, SORTIE.read_text().splitlines())}
    for f, fichier, nom in FORMATS:
        donnees = (DATA / fichier).read_text()
        for q, texte, attendu in QUESTIONS:
            if (f, q) in fait:
                continue
            prompt = (f"Here is a server inventory in {nom} format.\n\n{donnees}\n\n"
                      f"Question: {texte}\nAnswer with the value only, no sentence.")
            r = appel(prompt)
            ligne = {"format": f, "q": q, "attendu": attendu, "reponse": r["response"],
                     "juste": juste(r["response"], attendu), "prompt_eval_count": r.get("prompt_eval_count", 0), "eval_count": r.get("eval_count", 0),
                     "secondes": round(r.get("total_duration", 0) / 1e9, 1)}
            with SORTIE.open("a") as o:
                o.write(json.dumps(ligne, ensure_ascii=False) + "\n")
            print(f, q, repr(r["response"].strip()), "attendu", attendu, "OK" if ligne["juste"] else "FAUX", ligne["prompt_eval_count"], ligne["secondes"], flush=True)
