"""Walks through the gpsd test logs and lists those where the GGA goes from "no fix" (quality 0) to a fix.

Usage: python3 -I cherche_logs.py <test/daemon folder>
"""
import os
import sys

dossier = sys.argv[1]
for nom in sorted(os.listdir(dossier)):
    if not nom.endswith(".log"):
        continue
    try:
        lignes = open(os.path.join(dossier, nom), "rb").read().decode("ascii", "replace").splitlines()
    except Exception:
        continue
    q = []
    for i, l in enumerate(lignes):
        p = l.find("GGA,")
        if p < 0 or p < 3 or l[p - 3] != "$":
            continue
        champs = l[p - 3:].split(",")
        if len(champs) > 6:
            q.append((i, champs[6]))
    if not q:
        continue
    zero = [i for i, v in q if v in ("0", "")]
    fix = [i for i, v in q if v not in ("0", "")]
    if zero and fix and zero[0] < fix[0]:
        print(f"{nom:45s} GGA={len(q):4d} sans_fix={len(zero):4d} premier_fix_ligne={fix[0]} premier_sans_fix={zero[0]}")
