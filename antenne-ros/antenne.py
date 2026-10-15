#!/usr/bin/env python3
"""Writes the NEC2 input decks of the bench: a quarter-wave ground plane for 144.800 MHz.

One deck per length of the vertical element (the radiating rod), in nec/gp-<length>cm.nec.
The four radials do not change: 52 cm each, drooping 45 degrees, as on most home-made
ground planes. Free space (GE 0), perfect conductor, rod and radials 3 mm in diameter.

PT -1 turns off the printing of currents. Each deck asks nec2c for two things:
  1. the input impedance from 140 to 150 MHz, every 0.2 MHz (FR + XQ);
  2. the radiation pattern at 144.800 MHz, one vertical cut every 5 degrees (FR + RP).

Usage: python3 antenne.py            (writes the decks listed in LONGUEURS_CM)
       python3 antenne.py 47.5 51    (writes only those lengths, for exploration)
"""
import math
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
NEC = os.path.join(ICI, "nec")

F_MHZ = 144.8          # APRS / packet radio frequency in IARU Region 1
RAYON_M = 0.0015       # 3 mm rod
RADIAL_M = 0.52        # length of each radial
PENTE_DEG = 45         # radials drooping 45 degrees below horizontal
SEG_VERTICAL = 21
SEG_RADIAL = 11

# lengths of the vertical element studied by the deck, in cm
LONGUEURS_CM = [44.0, 46.0, 47.4, 49.0, 51.8, 54.0]


def deck(longueur_cm):
    h = longueur_cm / 100
    c = math.cos(math.radians(PENTE_DEG)) * RADIAL_M
    z = -math.sin(math.radians(PENTE_DEG)) * RADIAL_M
    lignes = [
        f"CM quarter-wave ground plane, vertical element {longueur_cm:.1f} cm, 4 radials {RADIAL_M * 100:.0f} cm at {PENTE_DEG} deg",
        "CM heurisme-lab/antenne-ros, written by antenne.py",
        "CE",
        f"GW 1 {SEG_VERTICAL} 0 0 0 0 0 {h:.4f} {RAYON_M}",
    ]
    for tag, (x, y) in enumerate([(c, 0), (0, c), (-c, 0), (0, -c)], start=2):
        lignes.append(f"GW {tag} {SEG_RADIAL} 0 0 0 {x:.4f} {y:.4f} {z:.4f} {RAYON_M}")
    lignes += [
        "GE 0",
        "EX 0 1 1 0 1.0 0.0",
        "PT -1 0 0 0",
        "FR 0 51 0 0 140.0 0.2",
        "XQ",
        f"FR 0 1 0 0 {F_MHZ} 0",
        "RP 0 37 1 1000 0 0 5 0",
        "EN",
    ]
    return "\n".join(lignes) + "\n"


def nom(longueur_cm):
    return f"gp-{longueur_cm:.1f}cm.nec"


def main():
    os.makedirs(NEC, exist_ok=True)
    longueurs = [float(a) for a in sys.argv[1:]] or LONGUEURS_CM
    for l in longueurs:
        with open(os.path.join(NEC, nom(l)), "w", encoding="ascii") as f:
            f.write(deck(l))
        print(nom(l))


if __name__ == "__main__":
    main()
