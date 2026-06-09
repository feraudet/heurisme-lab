"""Generates an invented inventory of 100 servers (fixed seed) and writes it in 6 formats.

Usage: python banc/gen_data.py   (writes into data/)
"""
import csv
import io
import json
import random
from pathlib import Path
from xml.sax.saxutils import escape

import yaml

ICI = Path(__file__).resolve().parent.parent
DATA = ICI / "data"
DATA.mkdir(exist_ok=True)

rnd = random.Random(42)
ROLES = ["web", "api", "db", "cache", "queue", "batch"]
ENVS = ["prod", "staging", "dev"]
REGIONS = ["eu-west-1", "eu-west-3", "eu-central-1"]
OS = ["debian-12", "ubuntu-22.04", "ubuntu-24.04", "rhel-9"]
STATUTS = ["running", "running", "running", "stopped", "maintenance"]
TAILLES = [(2, 4), (2, 8), (4, 16), (8, 32), (16, 64)]

lignes = []
for i in range(1, 101):
    role = ROLES[(i - 1) % len(ROLES)]
    cpu, ram = rnd.choice(TAILLES)
    lignes.append({
        "hostname": f"{role}-{i:03d}",
        "env": rnd.choice(ENVS),
        "region": rnd.choice(REGIONS),
        "os": rnd.choice(OS),
        "cpu": cpu,
        "ram_gb": ram,
        "disk_gb": rnd.choice([40, 80, 160, 320, 500]),
        "ip": f"10.{rnd.randint(0, 3)}.{rnd.randint(0, 255)}.{rnd.randint(2, 254)}",
        "status": rnd.choice(STATUTS),
        "cost_eur": round(cpu * 11.5 + ram * 2.1 + rnd.uniform(0, 9), 2),
    })
CHAMPS = list(lignes[0].keys())

(DATA / "inventaire.json").write_text(json.dumps(lignes, indent=2) + "\n")
(DATA / "inventaire.min.json").write_text(json.dumps(lignes, separators=(",", ":")) + "\n")
(DATA / "inventaire.yaml").write_text(yaml.safe_dump(lignes, sort_keys=False, allow_unicode=True))

buf = io.StringIO()
w = csv.DictWriter(buf, fieldnames=CHAMPS, lineterminator="\n")
w.writeheader()
w.writerows(lignes)
(DATA / "inventaire.csv").write_text(buf.getvalue())

md = ["| " + " | ".join(CHAMPS) + " |", "|" + "|".join("---" for _ in CHAMPS) + "|"]
md += ["| " + " | ".join(str(l[c]) for c in CHAMPS) + " |" for l in lignes]
(DATA / "inventaire.md").write_text("\n".join(md) + "\n")

xml = ['<?xml version="1.0" encoding="UTF-8"?>', "<servers>"]
for l in lignes:
    xml.append("  <server>")
    xml += [f"    <{c}>{escape(str(l[c]))}</{c}>" for c in CHAMPS]
    xml.append("  </server>")
xml.append("</servers>")
(DATA / "inventaire.xml").write_text("\n".join(xml) + "\n")

print(f"{len(lignes)} lignes, champs : {', '.join(CHAMPS)}")
