"""The example of the article: a system prompt and an internal runbook, written in French and in English,
sent to an LLM with every question. How many tokens, and what does the difference add up to?

Usage: python3 exemple.py
"""
from pathlib import Path

import po
from tok import NOMS, compte

EX = Path(__file__).resolve().parent / "exemple"
FICHIERS = ["prompt-systeme", "doc-interne"]
textes = {(f, l): (EX / f"{f}.{l}.md").read_text(encoding="utf-8") for f in FICHIERS for l in ("fr", "en")}

print("Files (exemple/): words and characters")
for f in FICHIERS:
    fr, en = textes[(f, "fr")], textes[(f, "en")]
    print(f"  {f + '.fr.md':<22}{po.mots(fr):>5} words {len(fr):>6} chars    "
          f"{f + '.en.md':<22}{po.mots(en):>5} words {len(en):>6} chars")
print()
print("Tokens sent with every question (system prompt + runbook)")
print(f"{'tokenizer':<17}{'prompt FR':>10}{'prompt EN':>10}{'doc FR':>8}{'doc EN':>8}{'total FR':>10}{'total EN':>10}{'FR/EN':>7}")
tot = {}
for n in NOMS:
    c = {k: compte(n, t) for k, t in textes.items()}
    fr = c[("prompt-systeme", "fr")] + c[("doc-interne", "fr")]
    en = c[("prompt-systeme", "en")] + c[("doc-interne", "en")]
    tot[n] = (fr, en)
    print(f"{n:<17}{c[('prompt-systeme', 'fr')]:>10}{c[('prompt-systeme', 'en')]:>10}"
          f"{c[('doc-interne', 'fr')]:>8}{c[('doc-interne', 'en')]:>8}{fr:>10}{en:>10}{fr / en:>6.2f}x")
print()
print("For 10,000 questions, the input tokens of these two files alone")
print(f"{'tokenizer':<17}{'french':>12}{'english':>12}{'difference':>12}")
for n in NOMS:
    fr, en = tot[n]
    print(f"{n:<17}{fr * 10000:>12,}{en * 10000:>12,}{(fr - en) * 10000:>+12,}")
