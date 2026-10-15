"""Same paragraphs, in English and in their official French translation: how many tokens?

Usage: python3 corpus.py
"""
import statistics

import po
from tok import NOMS, compte, taille

paires = po.paires()
EN = "\n".join(e for _, e, _ in paires)
FR = "\n".join(f for _, _, f in paires)
mEN, mFR = po.mots(EN), po.mots(FR)

print("Corpus: French translation of the Python docs (python-docs-fr, commit dda0482a), "
      f"{len(po.FICHIERS)} .po files")
print(f"{len(paires)} paragraph pairs kept, joined with a line break")
print(f"  english: {mEN} words, {len(EN)} characters, {len(EN.encode())} UTF-8 bytes")
print(f"  french:  {mFR} words, {len(FR)} characters, {len(FR.encode())} UTF-8 bytes")
print(f"  french / english: {mFR / mEN:.2f}x words, {len(FR) / len(EN):.2f}x characters")
print()
print(f"{'tokenizer':<17}{'vocab':>8}{'tokens EN':>11}{'tokens FR':>11}{'FR/EN':>7}"
      f"{'tok/word EN':>13}{'tok/word FR':>13}")
res = {}
for n in NOMS:
    te, tf = compte(n, EN), compte(n, FR)
    res[n] = (te, tf)
    print(f"{n:<17}{taille(n):>8}{te:>11}{tf:>11}{tf / te:>6.2f}x{te / mEN:>13.2f}{tf / mFR:>13.2f}")

print()
print(f"FR/EN ratio paragraph by paragraph ({len(paires)} pairs): median and spread")
print(f"{'tokenizer':<17}{'median':>8}{'p10':>7}{'p90':>7}{'FR shorter':>12}")
for n in NOMS:
    r = sorted(compte(n, f) / compte(n, e) for _, e, f in paires)
    d = statistics.quantiles(r, n=10)
    moins = sum(1 for x in r if x < 1)
    print(f"{n:<17}{statistics.median(r):>7.2f}x{d[0]:>6.2f}x{d[-1]:>6.2f}x{moins:>12}")

print()
print("Same window, same content: how much of the corpus fits in 10,000 tokens")
print(f"{'tokenizer':<17}{'english':>9}{'french':>9}{'french vs english':>19}")
for n in NOMS:
    te, tf = res[n]
    pe, pf = 10000 / te * 100, 10000 / tf * 100
    print(f"{n:<17}{pe:>8.1f}%{pf:>8.1f}%{(pf / pe - 1) * 100:>+18.1f}%")
