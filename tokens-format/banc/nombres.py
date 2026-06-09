"""What numbers, dates and UUIDs cost, then a UUID column added to the CSV.

Usage: python banc/nombres.py
"""
import csv
import io
import json
import random
import uuid
from pathlib import Path

from langue import t as tr
from tok import compte, morceaux

DATA = Path(__file__).resolve().parent.parent / "data"
rnd = random.Random(7)
u = str(uuid.UUID(int=rnd.getrandbits(128), version=4))

VALEURS = ["running", "maintenance", "37.49", "1781015527", "3.14159265",
           "10.1.71.190", "2026-06-09T14:32:07Z", u]
print(f"{tr('valeur', 'value'):<38}{tr('car.', 'chars'):>5}{'o200k':>7}{'qwen':>6}   " + tr("découpage o200k_base", "o200k_base split"))
for v in VALEURS:
    c = compte(v)
    print(f"{v:<38}{len(v):>5}{c['o200k_base']:>7}{c['qwen2.5']:>6}   " + "·".join(morceaux(v)))

# Same CSV, with a UUID v4 id column at the front
lignes = json.loads((DATA / "inventaire.json").read_text())
buf = io.StringIO()
w = csv.writer(buf, lineterminator="\n")
w.writerow(["id"] + list(lignes[0].keys()))
for l in lignes:
    w.writerow([str(uuid.UUID(int=rnd.getrandbits(128), version=4))] + list(l.values()))
avant = compte((DATA / "inventaire.csv").read_text())["o200k_base"]
apres = compte(buf.getvalue())["o200k_base"]
print(tr(f"\nCSV 100 lignes        : {avant} tokens (o200k_base)", f"\nCSV 100 rows         : {avant} tokens (o200k_base)"))
print(tr(f"CSV + colonne id UUID : {apres} tokens, +{apres - avant} soit +{(apres - avant) / avant:.0%}, {(apres - avant) / 100:.1f} tokens par UUID",
         f"CSV + UUID id column : {apres} tokens, +{apres - avant} i.e. +{(apres - avant) / avant:.0%}, {(apres - avant) / 100:.1f} tokens per UUID"))
