#!/usr/bin/env python3
"""Writes the four NEC2 input files of the bench into nec/ (standard library only).

All antennas are vertical, made of perfectly conducting wire 2 mm in diameter, in free space, at 1090 MHz.
Lengths were tuned once so that the feed reactance is close to zero (resonance); they are fixed here.
Wires are cut into about 121 segments per wavelength, with the extended thin-wire kernel (EK card):
with 41 segments per wavelength and radials at 45 degrees, the whip (fed at a junction of five wires)
gave an average power gain of 1.09 instead of 1, which `analyse.py conservation` makes visible.

  dipole.nec      half-wave dipole, the 0 dBd reference
  fouet.nec       quarter-wave whip with four radials drooping at 30 degrees (ground plane)
  yagi.nec        3-element Yagi (reflector, driven element, director), boom along +x
  colineaire.nec  idealised collinear: N half-wave dipoles stacked on the z axis, all fed in phase

Each file ends with four RP cards:
  RP 1: vertical cut, phi = 0, theta 0..180 step 1 degree
  RP 2: vertical cut, phi = 180, theta 0..180 step 1 degree
  RP 3: horizontal cut, theta = 90, phi 0..359 step 1 degree
  RP 4: whole sphere, theta 0..180 and phi 0..359 step 1 degree, with NEC's average power gain (XNDA = 1001)
"""
import math
import os
import sys

FREQ_MHZ = 1090.0
C = 299.792458                       # speed of light, in m per microsecond
LAMBDA = C / FREQ_MHZ                # wavelength in m (0.2750 m)
RAYON = 0.001                        # wire radius in m (2 mm diameter)
SEG_PAR_LAMBDA = 121                 # segments per wavelength, odd per element so the feed is at the centre

# Dimensions in metres, tuned once (see README).
DIPOLE_LONG = 0.1278                 # half-wave dipole, tip to tip
FOUET_LONG = 0.0630                  # quarter-wave radiator
FOUET_RADIAL = 0.0650                # each of the 4 radials
FOUET_PENTE = 30.0                   # radial droop, degrees below horizontal
YAGI = {                             # element: (x position, length)
    "reflecteur": (-0.0550, 0.1380),
    "pilote": (0.0, 0.1278),
    "directeur": (0.0410, 0.1120),
}
COLI_N = 2                           # number of stacked half-wave dipoles
COLI_PAS = 0.2100                    # centre-to-centre spacing in m

ICI = os.path.dirname(os.path.abspath(__file__))


def nseg(longueur):
    n = max(5, round(longueur / LAMBDA * SEG_PAR_LAMBDA))
    return n if n % 2 else n + 1


def cartes_rp():
    return [
        f"FR 0 1 0 0 {FREQ_MHZ:.1f} 0",
        "RP 0 181 1 1000 0 0 1 0",
        "RP 0 181 1 1000 0 180 1 0",
        "RP 0 1 360 1000 90 0 0 1",
        "RP 0 181 360 1001 0 0 1 1",
        "EN",
    ]


def gw(tag, n, x1, y1, z1, x2, y2, z2):
    return f"GW {tag} {n} {x1:.5f} {y1:.5f} {z1:.5f} {x2:.5f} {y2:.5f} {z2:.5f} {RAYON:.4f}"


def dipole():
    n = nseg(DIPOLE_LONG)
    l = [f"CM half-wave dipole, vertical, {DIPOLE_LONG * 1000:.1f} mm, free space, {FREQ_MHZ:.0f} MHz", "CE",
         gw(1, n, 0, 0, -DIPOLE_LONG / 2, 0, 0, DIPOLE_LONG / 2), "GE 0", "EK 0",
         f"EX 0 1 {n // 2 + 1} 0 1.0 0.0"]
    return l + cartes_rp()


def fouet():
    nv = nseg(FOUET_LONG * 2) // 2 + 1         # odd number, feed on the bottom segment
    nr = nseg(FOUET_RADIAL * 2) // 2 + 1
    l = [f"CM quarter-wave whip {FOUET_LONG * 1000:.1f} mm, 4 radials {FOUET_RADIAL * 1000:.1f} mm at {FOUET_PENTE:.0f} deg, free space",
         "CE", gw(1, nv, 0, 0, 0, 0, 0, FOUET_LONG)]
    a = math.radians(FOUET_PENTE)
    for k in range(4):
        phi = math.radians(90 * k)
        x = FOUET_RADIAL * math.cos(a) * math.cos(phi)
        y = FOUET_RADIAL * math.cos(a) * math.sin(phi)
        z = -FOUET_RADIAL * math.sin(a)
        l.append(gw(2 + k, nr, 0, 0, 0, x, y, z))
    l += ["GE 0", "EK 0", "EX 0 1 1 0 1.0 0.0"]
    return l + cartes_rp()


def yagi():
    l = ["CM 3-element Yagi, vertical elements, boom along +x, free space", "CE"]
    tags = {}
    for tag, (nom, (x, long_)) in enumerate(YAGI.items(), start=1):
        n = nseg(long_)
        tags[nom] = (tag, n)
        l.append(gw(tag, n, x, 0, -long_ / 2, x, 0, long_ / 2))
    tag, n = tags["pilote"]
    l += ["GE 0", "EK 0", f"EX 0 {tag} {n // 2 + 1} 0 1.0 0.0"]
    return l + cartes_rp()


def colineaire():
    n = nseg(DIPOLE_LONG)
    l = [f"CM idealised collinear: {COLI_N} half-wave dipoles {DIPOLE_LONG * 1000:.1f} mm, centres {COLI_PAS * 1000:.1f} mm apart, fed in phase",
         "CE"]
    z0 = -(COLI_N - 1) * COLI_PAS / 2
    for k in range(COLI_N):
        zc = z0 + k * COLI_PAS
        l.append(gw(k + 1, n, 0, 0, zc - DIPOLE_LONG / 2, 0, 0, zc + DIPOLE_LONG / 2))
    l += ["GE 0", "EK 0"]
    for k in range(COLI_N):
        l.append(f"EX 0 {k + 1} {n // 2 + 1} 0 1.0 0.0")
    return l + cartes_rp()


MODELES = {"dipole": dipole, "fouet": fouet, "yagi": yagi, "colineaire": colineaire}


def main():
    dossier = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ICI, "nec")
    os.makedirs(dossier, exist_ok=True)
    for nom, f in MODELES.items():
        with open(os.path.join(dossier, nom + ".nec"), "w", encoding="ascii") as sortie:
            sortie.write("\n".join(f()) + "\n")
    print("wrote", ", ".join(n + ".nec" for n in MODELES))


if __name__ == "__main__":
    main()
