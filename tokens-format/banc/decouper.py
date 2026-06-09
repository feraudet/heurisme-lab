"""Splits ONE row of the inventory, in each format, token by token.

Tokens are separated by « · ». A space is shown as « ␣ », a line break as « ↵ ».
Usage: python banc/decouper.py [o200k_base|cl100k_base|qwen2.5]
"""
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

import yaml

from langue import ARGS, f as fmt, t as tr
from tok import morceaux

DATA = Path(__file__).resolve().parent.parent / "data"
nom = ARGS[0] if ARGS else "o200k_base"
l = json.loads((DATA / "inventaire.json").read_text())[0]
C = list(l.keys())

fragments = {
    "json-indente": "  " + json.dumps(l, indent=2).replace("\n", "\n  ") + ",\n",
    "json-minifie": json.dumps(l, separators=(",", ":")) + ",",
    "yaml": yaml.safe_dump([l], sort_keys=False),
    "csv": ",".join(str(l[c]) for c in C) + "\n",
    "markdown": "| " + " | ".join(str(l[c]) for c in C) + " |\n",
    "xml": "  <server>\n" + "".join(f"    <{c}>{escape(str(l[c]))}</{c}>\n" for c in C) + "  </server>\n",
}

def vis(m):
    return m.replace(" ", "␣").replace("\n", "↵")

print(tr(f"tokenizer : {nom}", f"tokenizer: {nom}"))
for f, t in fragments.items():
    m = morceaux(t, nom)
    print(tr(f"\n{f} : {len(m)} tokens", f"\n{fmt(f)}: {len(m)} tokens"))
    print("·".join(vis(x) for x in m))
