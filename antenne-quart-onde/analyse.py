#!/usr/bin/env python3
"""Reads the nec2c outputs in raw/ and prints one stable text report per step.

usage: python3 analyse.py longueur|epaisseur|radians|passerelle
Standard library only. No time, no host name: the output depends on raw/*.out only.
"""
import math
import os
import re
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ICI, "raw")
Z0 = 50.0
C = 299_792_458.0
F_MHZ = 868.0
QUART_CM = C / (F_MHZ * 1e6) / 4 * 100


def lire(nom):
    """List of (comment, [(freq_MHz, R, X), ...]) for every structure of raw/<nom>.out."""
    texte = open(os.path.join(RAW, nom + ".out"), encoding="ascii", errors="replace").read()
    blocs = texte.split("---------------- COMMENTS ----------------")[1:]
    res = []
    for b in blocs:
        commentaire = b.strip().split("\n")[0].strip()
        points = []
        for morceau in b.split("--------- FREQUENCY --------")[1:]:
            f = float(re.search(r"FREQUENCY :\s*(\S+) MHz", morceau).group(1))
            m = re.search(r"ANTENNA INPUT PARAMETERS.*?\n.*?\n.*?\n\s*1\s+1\s+(.*)", morceau)
            champs = m.group(1).split()
            points.append((f, float(champs[4]), float(champs[5])))
        res.append((commentaire, points))
    return res


def param(commentaire, cle):
    return float(re.search(cle + r"=?\s*([0-9.]+)", commentaire).group(1))


def ros(r, x):
    g = abs(complex(r - Z0, x) / complex(r + Z0, x))
    return (1 + g) / (1 - g), g


def resonance(serie):
    """serie: [(L_cm, R, X)] sorted by L. Linear interpolation where X changes sign."""
    for (l1, r1, x1), (l2, r2, x2) in zip(serie, serie[1:]):
        if x1 <= 0 < x2 or x1 < 0 <= x2:
            t = -x1 / (x2 - x1)
            return l1 + t * (l2 - l1), r1 + t * (r2 - r1)
    return None, None


def tableau_longueur(serie):
    print("  L (cm)    R (ohm)    X (ohm)   SWR on 50 ohm")
    for l, r, x in serie:
        s, _ = ros(r, x)
        print(f"  {l:6.1f}  {r:9.1f}  {x:+9.1f}   {s:6.2f}")


def etape_longueur():
    print(f"Monopole on a perfect ground plane (GN 1), wire 1 mm diameter, {F_MHZ:g} MHz")
    print(f"lambda = {4 * QUART_CM:.2f} cm, lambda/4 = {QUART_CM:.2f} cm")
    serie = [(param(c, "L"), p[0][1], p[0][2]) for c, p in lire("01-longueur")]
    tableau_longueur(serie)
    l, r = resonance(serie)
    print(f"X = 0 at L = {l:.2f} cm, R = {r:.1f} ohm, SWR on 50 ohm = {ros(r, 0)[0]:.2f}")
    print(f"L / (lambda/4) = {l / QUART_CM:.3f}, {QUART_CM - l:.2f} cm shorter than lambda/4")


def etape_epaisseur():
    print(f"Resonant length vs wire diameter, perfect ground plane, {F_MHZ:g} MHz")
    print(f"lambda/4 = {QUART_CM:.2f} cm")
    groupes = {}
    for c, p in lire("02-epaisseur"):
        groupes.setdefault(param(c, "r"), []).append((param(c, "L"), p[0][1], p[0][2]))
    print("  diameter   lambda/d   L at X=0   L/(lambda/4)   R at X=0")
    for r_mm, serie in sorted(groupes.items()):
        l, r = resonance(sorted(serie))
        d = 2 * r_mm
        print(f"  {d:5.1f} mm  {4 * QUART_CM * 10 / d:8.0f}   {l:6.2f} cm   {l / QUART_CM:10.3f}   {r:6.1f} ohm")


def etape_radians():
    print(f"Ground plane in free space: vertical + 4 radials of 8.6 cm, wire 1 mm, {F_MHZ:g} MHz")
    print("droop = angle of the radials below horizontal")
    groupes = {}
    for c, p in lire("03-radians"):
        groupes.setdefault(param(c, "droop"), []).append((param(c, "L"), p[0][1], p[0][2]))
    print("  droop   L at X=0   R at X=0   SWR on 50 ohm")
    for a, serie in sorted(groupes.items()):
        l, r = resonance(sorted(serie))
        print(f"  {a:3.0f} deg  {l:6.2f} cm  {r:6.1f} ohm   {ros(r, 0)[0]:6.2f}")


def etape_passerelle():
    (c1, p1), (c2, p2) = lire("04-passerelle")
    l1, l2 = param(c1, "L"), param(c2, "L")
    print("Gateway antenna: 4 radials of 8.6 cm drooping 45 deg, wire 1 mm, two cuts of the vertical")
    print(f"           L = {l1:.1f} cm                    L = {l2:.1f} cm")
    print("  f (MHz)   R (ohm)  X (ohm)  SWR       R (ohm)  X (ohm)  SWR")
    for (f, r1, x1), (_, r2, x2) in zip(p1, p2):
        print(f"  {f:6.0f}   {r1:7.1f}  {x1:+7.1f}  {ros(r1, x1)[0]:4.2f}      {r2:7.1f}  {x2:+7.1f}  {ros(r2, x2)[0]:4.2f}")
    for l, p in ((l1, p1), (l2, p2)):
        bande = [ros(r, x)[0] for f, r, x in p if 862 <= f <= 870]
        (_, r, x), = [q for q in p if q[0] == F_MHZ]
        s, g = ros(r, x)
        print(f"L = {l:.1f} cm: SWR {min(bande):.2f} to {max(bande):.2f} from 862 to 870 MHz; at 868 MHz "
              f"return loss {-20 * math.log10(g):.1f} dB, mismatch loss {-10 * math.log10(1 - g * g):.2f} dB")


ETAPES = {"longueur": etape_longueur, "epaisseur": etape_epaisseur, "radians": etape_radians, "passerelle": etape_passerelle}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ETAPES:
        sys.exit("usage: python3 analyse.py " + "|".join(ETAPES))
    ETAPES[sys.argv[1]]()
