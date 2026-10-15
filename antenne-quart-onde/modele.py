#!/usr/bin/env python3
"""Writes the NEC2 input decks of the bench into nec/ (one file per sweep).

Every structure of a sweep is one geometry, separated by an NX card (next structure).
Units: metres. Feed point at the origin, vertical element along +z.
Standard library only. Output is deterministic: same script, same files.
"""
import math
import os

C = 299_792_458.0           # speed of light, m/s
F_MHZ = 868.0               # frequency of the example (LoRa EU868)
LAMBDA = C / (F_MHZ * 1e6)  # wavelength, m
QUART = LAMBDA / 4          # quarter wave, m

NSEG = 15                   # segments per wire (about 5.5 mm each at 8 cm)
RAYON = 0.0005              # default wire radius: 0.5 mm (1 mm diameter)
RAYONS = [0.00025, 0.0005, 0.00075, 0.001]   # 0.5, 1, 1.5 and 2 mm diameter
LONGUEURS_CM = [round(7.0 + 0.1 * k, 1) for k in range(21)]          # 7.0 to 9.0 cm
LONGUEURS_01 = [round(7.6 + 0.1 * k, 1) for k in range(13)]          # 7.6 to 8.8 cm, printed in full
ANGLES = [0, 15, 30, 45, 60]                                          # radial droop, degrees below horizontal
RADIAN_CM = 8.6             # radial length, cm (about a quarter wave)

ICI = os.path.dirname(os.path.abspath(__file__))
NEC = os.path.join(ICI, "nec")


def f(x):
    return f"{x:.6f}"


def gw(tag, nseg, p1, p2, rayon):
    return f"GW {tag} {nseg} {' '.join(f(v) for v in p1)} {' '.join(f(v) for v in p2)} {f(rayon)}"


def structure(commentaire, l_m, rayon, sol, angle=None, freqs=(F_MHZ, 1, 0.0)):
    """One NEC2 structure. sol=True: perfect ground (GN 1). Else free space, 4 radials drooping by angle."""
    lignes = [f"CM {commentaire}", "CE"]
    lignes.append(gw(1, NSEG, (0, 0, 0), (0, 0, l_m), rayon))
    if not sol:
        r = RADIAN_CM / 100
        a = math.radians(angle)
        for k in range(4):
            phi = math.radians(90 * k)
            bout = (r * math.cos(a) * math.cos(phi), r * math.cos(a) * math.sin(phi), -r * math.sin(a))
            lignes.append(gw(2 + k, NSEG, (0, 0, 0), bout, rayon))
    lignes.append("GE 1" if sol else "GE 0")
    if sol:
        lignes.append("GN 1")
    lignes.append("PT -1 0 0 0")       # no current table, input impedance only
    lignes.append("EX 0 1 1 0 1.0 0.0")
    f0, n, pas = freqs
    lignes.append(f"FR 0 {n} 0 0 {f0:.3f} {pas:.3f}")
    lignes.append("XQ")
    return lignes


def ecrire(nom, structures):
    lignes = []
    for k, s in enumerate(structures):
        if k:
            lignes.append("NX")
        lignes.extend(s)
    lignes.append("EN")
    with open(os.path.join(NEC, nom), "w", encoding="ascii") as fh:
        fh.write("\n".join(lignes) + "\n")
    print(f"nec/{nom}: {len(structures)} structures")


def main():
    os.makedirs(NEC, exist_ok=True)
    # 01: length sweep, monopole on a perfect ground plane, 1 mm wire
    ecrire("01-longueur.nec", [structure(f"monopole L={l} cm r=0.5 mm perfect ground", l / 100, RAYON, True)
                               for l in LONGUEURS_01])
    # 02: same sweep for four wire radii
    ecrire("02-epaisseur.nec", [structure(f"monopole L={l} cm r={r * 1000:g} mm perfect ground", l / 100, r, True)
                                for r in RAYONS for l in LONGUEURS_CM])
    # 03: ground plane in free space, 4 radials of 8.6 cm, five droop angles
    ecrire("03-radians.nec", [structure(f"ground plane L={l} cm radials {RADIAN_CM} cm droop {a} deg", l / 100, RAYON, False, a)
                              for a in ANGLES for l in LONGUEURS_CM])
    # 04: frequency sweep of the gateway antenna, 856 to 880 MHz: cut at 7.8 cm, then at lambda/4
    ecrire("04-passerelle.nec", [structure(f"gateway antenna L={l} cm radials {RADIAN_CM} cm droop {a} deg", l / 100, RAYON, False, a,
                                           freqs=(856.0, 13, 2.0))
                                 for l, a in [(7.8, 45), (8.6, 45)]])
    print(f"lambda = {LAMBDA * 100:.2f} cm, lambda/4 = {QUART * 100:.2f} cm at {F_MHZ:g} MHz")


if __name__ == "__main__":
    main()
