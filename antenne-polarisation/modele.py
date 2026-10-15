#!/usr/bin/env python3
"""Writes the NEC2 input decks of the bench into nec/ (one file per scenario).

Method: every "port" is the centre segment of a dipole. Each NEC2 structure of a file
(structures are separated by NX cards) excites ONE port with 1 V; the other ports are
plain wire segments, i.e. short circuits. The currents read at all ports then give one
column of the port admittance matrix Y. analyse.py inverts Y into Z and computes the
power transferred between ports with conjugate-matched loads (see README.md).

Units: metres. Link along +y. Frequency 1090 MHz (ADS-B).
Standard library only. Output is deterministic: same script, same files.
"""
import math
import os

C = 299_792_458.0
F_MHZ = 1090.0
LAMBDA = C / (F_MHZ * 1e6)       # 27.50 cm
L_DIPOLE = 0.130                 # dipole length, m (about 0.47 lambda)
RAYON = 0.0005                   # wire radius, m (1 mm diameter)
NSEG = 21                        # segments per dipole, port = segment 11
D_LIEN = 10 * LAMBDA             # distance between the two antennas: 10 lambda, 2.75 m
DELTA = 0.004                    # turnstile: the second dipole sits 4 mm behind the first
ANGLES = [0, 15, 30, 45, 60, 75, 80, 85, 89, 90]
# scatterer for scenario 02: a 1 m wire (a guy wire, a gutter), tilted 45 deg,
# halfway along the link and 50 cm to the side of it
FIL = ((0.50 - 0.3536, D_LIEN / 2, -0.3536), (0.50 + 0.3536, D_LIEN / 2, 0.3536))
NSEG_FIL = 151

ICI = os.path.dirname(os.path.abspath(__file__))
NEC = os.path.join(ICI, "nec")


def f(x):
    return f"{x:.6f}"


def dipole(tag, centre, direction, nseg=NSEG, longueur=L_DIPOLE):
    cx, cy, cz = centre
    ux, uy, uz = direction
    h = longueur / 2
    p1 = (cx - h * ux, cy - h * uy, cz - h * uz)
    p2 = (cx + h * ux, cy + h * uy, cz + h * uz)
    return f"GW {tag} {nseg} {' '.join(f(v) for v in p1)} {' '.join(f(v) for v in p2)} {f(RAYON)}"


def fil(tag, p1, p2, nseg):
    return f"GW {tag} {nseg} {' '.join(f(v) for v in p1)} {' '.join(f(v) for v in p2)} {f(RAYON)}"


def structure(commentaire, fils, sources, rp=None):
    """sources: list of (tag, real, imag) voltage sources on the centre segment."""
    lignes = [f"CM {commentaire}", "CE"] + fils + ["GE 0"]
    for k, (tag, re, im) in enumerate(sources):
        lignes.append(f"EX 0 {tag} {(NSEG + 1) // 2} 0 {re:.6f} {im:.6f}")
    lignes.append(f"FR 0 1 0 0 {F_MHZ:.3f} 0.000")
    if rp:
        theta, phi = rp
        lignes.append(f"RP 0 1 1 0000 {theta:.1f} {phi:.1f} 0.0 0.0")
    else:
        lignes.append("XQ")
    return lignes


def ecrire(nom, structures):
    lignes = []
    for k, s in enumerate(structures):
        if k:
            lignes.append("NX")
        lignes += s
    lignes.append("EN")
    with open(os.path.join(NEC, nom + ".nec"), "w") as fh:
        fh.write("\n".join(lignes) + "\n")


def rotation(theta_deg):
    t = math.radians(theta_deg)
    return (math.sin(t), 0.0, math.cos(t))   # rotated about the link axis (y), 0 = vertical


def main():
    os.makedirs(NEC, exist_ok=True)
    vert, horiz = (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)

    # 01: tx vertical at the origin, rx rotated by theta at 10 lambda
    s = []
    for a in ANGLES:
        fils = [dipole(1, (0, 0, 0), vert), dipole(2, (0, D_LIEN, 0), rotation(a))]
        for port in (1, 2):
            s.append(structure(f"rotation angle={a} port={port}", fils, [(port, 1.0, 0.0)]))
    s.append(structure("lone dipole gain toward +y", [dipole(1, (0, 0, 0), vert)], [(1, 1.0, 0.0)], rp=(90.0, 90.0)))
    ecrire("01-rotation", s)

    # 02: same link, with a tilted wire beside it
    s = []
    for a in (0, 90):
        fils = [dipole(1, (0, 0, 0), vert), dipole(2, (0, D_LIEN, 0), rotation(a)), fil(3, *FIL, NSEG_FIL)]
        for port in (1, 2):
            s.append(structure(f"reflection angle={a} port={port}", fils, [(port, 1.0, 0.0)]))
    ecrire("02-reflet", s)

    # 03: turnstile (two crossed dipoles) at each end. Ports: 1 tx vertical, 2 tx horizontal
    # (4 mm behind), 3 rx vertical, 4 rx horizontal (4 mm behind, seen from the tx)
    fils = [dipole(1, (0, 0, 0), vert), dipole(2, (0, -DELTA, 0), horiz),
            dipole(3, (0, D_LIEN, 0), vert), dipole(4, (0, D_LIEN + DELTA, 0), horiz)]
    s = [structure(f"circular port={port}", fils, [(port, 1.0, 0.0)]) for port in (1, 2, 3, 4)]
    # sense check: each turnstile alone, horizontal dipole fed +90 deg / -90 deg, pattern
    # toward the other end (+y for the tx, -y for the rx). Weights include the 4 mm offset.
    k = 2 * math.pi / LAMBDA
    for signe, nom in ((1, "plus90"), (-1, "minus90")):
        ph = signe * math.pi / 2 + k * DELTA
        s.append(structure(f"sense tx {nom}", fils[:2], [(1, 1.0, 0.0), (2, math.cos(ph), math.sin(ph))], rp=(90.0, 90.0)))
        tx = [dipole(3, (0, 0, 0), vert), dipole(4, (0, DELTA, 0), horiz)]
        s.append(structure(f"sense rx {nom}", tx, [(3, 1.0, 0.0), (4, math.cos(ph), math.sin(ph))], rp=(90.0, 270.0)))
    ecrire("03-circulaire", s)


if __name__ == "__main__":
    main()
