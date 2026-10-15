"""What the accents cost: the French corpus as it is, without its accents, and with decomposed accents (NFD).

Removing the accents is only a measurement: the text becomes incorrect French.
Usage: python3 accents.py
"""
import re
import unicodedata

import po
from tok import NOMS, compte

paires = po.paires()
EN = "\n".join(e for _, e, _ in paires)
FR = "\n".join(f for _, _, f in paires)


def sans_accents(t):
    d = unicodedata.normalize("NFD", t)
    return unicodedata.normalize("NFC", "".join(c for c in d if unicodedata.category(c) != "Mn"))


SANS = sans_accents(FR)
NFD = unicodedata.normalize("NFD", FR)
accentues = [c for c in FR if c != sans_accents(c)]
mots = re.findall(r"\w+", FR)
avec = [m for m in mots if m != sans_accents(m)]

print(f"French corpus ({len(paires)} paragraphs of the Python docs)")
print(f"  already in NFC form: {'yes' if unicodedata.normalize('NFC', FR) == FR else 'no'}")
print(f"  accented letters: {len(accentues)} of {len(FR)} characters ({len(accentues) / len(FR) * 100:.1f} %)")
print(f"  words with at least one accent: {len(avec)} of {len(mots)} ({len(avec) / len(mots) * 100:.1f} %)")
print(f"  most frequent: " + ", ".join(f"{c} {accentues.count(c)}" for c in sorted(set(accentues), key=lambda c: -accentues.count(c))[:6]))
print(f"  UTF-8 bytes: as is {len(FR.encode())}, without accents {len(SANS.encode())}, NFD {len(NFD.encode())}")
print()
print("no acc. = accents removed, NFD = accents decomposed")
print("gap = share of the FR-EN gap closed by removing the accents")
print(f"{'tokenizer':<17}{'EN':>6}{'FR':>7}{'no acc.':>8}{'diff':>7}{'NFD':>7}{'diff':>8}{'gap':>6}")
for n in NOMS:
    e, f, s, d = compte(n, EN), compte(n, FR), compte(n, SANS), compte(n, NFD)
    print(f"{n:<17}{e:>6}{f:>7}{s:>8}{(s - f) / f * 100:>+6.1f}%{d:>7}{(d - f) / f * 100:>+7.1f}%"
          f"{(f - s) / (f - e) * 100:>5.0f}%")

print()
print("Tokens per word, French words with and without an accent (each word alone, after a space)")
print(f"{'tokenizer':<17}{'with accent':>13}{'without':>9}")
for n in NOMS:
    a = sum(compte(n, " " + m) for m in avec) / len(avec)
    sa = [m for m in mots if m == sans_accents(m)]
    b = sum(compte(n, " " + m) for m in sa) / len(sa)
    print(f"{n:<17}{a:>13.2f}{b:>9.2f}")
