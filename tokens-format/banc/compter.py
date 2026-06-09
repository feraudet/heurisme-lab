"""Counts the tokens of the same 100 rows in 6 formats, with 3 tokenizers.

Usage: python banc/compter.py
"""
import json
from pathlib import Path

from langue import f as fmt, t as tr
from tok import NOMS, compte

DATA = Path(__file__).resolve().parent.parent / "data"
FORMATS = [("json-indente", "inventaire.json"), ("json-minifie", "inventaire.min.json"),
           ("yaml", "inventaire.yaml"), ("csv", "inventaire.csv"),
           ("markdown", "inventaire.md"), ("xml", "inventaire.xml")]

res = {}
print(f"{'format':<13}{tr("octets", "bytes"):>8}" + "".join(f"{n:>13}" for n in NOMS) + f"{'vs csv':>8}")
base = compte((DATA / "inventaire.csv").read_text())["o200k_base"]
for nom, f in FORMATS:
    t = (DATA / f).read_text()
    c = compte(t)
    res[nom] = {"octets": len(t.encode()), **c}
    print(f"{fmt(nom):<13}{len(t.encode()):>8}" + "".join(f"{c[n]:>13}" for n in NOMS) + f"{c['o200k_base'] / base:>7.2f}x")
(DATA / "comptes.json").write_text(json.dumps(res, indent=2) + "\n")
