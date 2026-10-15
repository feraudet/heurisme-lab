#!/usr/bin/env python3
"""Reads the nec2c outputs (nec/gp-*.out) and prints what the deck uses, standard library only.

  python3 lit_nec.py      for each length of the vertical element: resonant frequency (X = 0),
                          impedance and SWR at 144.800 MHz, maximum gain and its elevation,
                          then the SWR from 140 to 150 MHz, every MHz.
"""
import glob
import os
import re

ICI = os.path.dirname(os.path.abspath(__file__))
NEC = os.path.join(ICI, "nec")
Z0 = 50.0
F_MHZ = 144.8

RE_FREQ = re.compile(r"FREQUENCY :\s*([0-9.E+-]+) MHz")
RE_LONG = re.compile(r"gp-([0-9.]+)cm\.out$")


def lire(chemin):
    """Returns (list of (f MHz, complex Z)), (max total gain dBi, theta deg) of the RP block."""
    lignes = open(chemin, encoding="ascii", errors="replace").read().split("\n")
    points, f, gain = [], None, None
    k = 0
    while k < len(lignes):
        ligne = lignes[k]
        m = RE_FREQ.search(ligne)
        if m:
            f = float(m.group(1))
        if "ANTENNA INPUT PARAMETERS" in ligne:
            champs = lignes[k + 3].split()
            points.append((f, complex(float(champs[6]), float(champs[7]))))
            k += 3
        if "RADIATION PATTERNS" in ligne:
            meilleur = None
            j = k + 5
            while j < len(lignes) and lignes[j].strip():
                c = lignes[j].split()
                theta, total = float(c[0]), float(c[4])
                if meilleur is None or total > meilleur[0]:
                    meilleur = (total, theta)
                j += 1
            gain = meilleur
            k = j
        k += 1
    # the last impedance point is the one of the RP run (144.8 MHz), already in the sweep
    balayage = points[:-1]
    return balayage, gain


def fichiers():
    res = []
    for chemin in glob.glob(os.path.join(NEC, "gp-*.out")):
        res.append((float(RE_LONG.search(chemin).group(1)), chemin))
    return sorted(res)


def z_a(balayage, f):
    for fr, z in balayage:
        if abs(fr - f) < 1e-6:
            return z
    raise SystemExit(f"{f} MHz not in the sweep")


def impedances_a(f):
    return [(l, z_a(lire(c)[0], f)) for l, c in fichiers()]


def ros(z):
    g = abs((z - Z0) / (z + Z0))
    return (1 + g) / (1 - g)


def resonance(balayage):
    for (f1, z1), (f2, z2) in zip(balayage, balayage[1:]):
        if z1.imag <= 0 <= z2.imag:
            return f1 + (f2 - f1) * (-z1.imag) / (z2.imag - z1.imag)
    return None


def fz(z):
    signe = "+" if z.imag >= 0 else "-"
    return f"{z.real:.1f} {signe} j{abs(z.imag):.1f}"


def main():
    donnees = [(l, *lire(c)) for l, c in fichiers()]
    print(f"Quarter-wave ground plane, 4 radials 52 cm at 45 deg, free space, Z0 = {Z0:.0f} ohm")
    print()
    print(f"{'rod':<9}{'resonance':>11}   {'Z at 144.8 MHz':<16}{'SWR':>6}{'max gain':>11}{'elev.':>8}")
    for l, bal, gain in donnees:
        fres = resonance(bal)
        if fres:
            fres_txt = f"{fres:.1f} MHz"
        else:
            fres_txt = "> 150 MHz" if bal[-1][1].imag < 0 else "< 140 MHz"
        z = z_a(bal, F_MHZ)
        elevation = 90 - gain[1]
        print(f"{l:>4.1f} cm {fres_txt:>11}   {fz(z):<16}{ros(z):>6.2f}{gain[0]:>7.2f} dBi{elevation:>5.0f} deg")
    print()
    print("SWR vs frequency (MHz), one column per rod length (cm):")
    print("  f    " + "".join(f"{l:>7.1f}" for l, _, _ in donnees))
    for n in range(0, 11):
        f = 140.0 + n
        print(f"{f:6.1f}" + "".join(f"{ros(z_a(bal, f)):>7.2f}" for _, bal, _ in donnees))


if __name__ == "__main__":
    main()
