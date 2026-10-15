#!/usr/bin/env python3
"""Coax loss bench: decibels, datasheet interpolation, the ADS-B example and the system noise figure.

Usage: python3 pertes.py db | fiches | tableau | adsb | bruit
Standard library only. No network: the figures are in fiches.py.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python3 -I does not add it
from fiches import ANTENNA_DBI, CABLES, CONNECTORS, DB100FT_TO_DB100M, DIPOLE_DBI, LNA  # noqa: E402

FREQS = (144, 868, 1090)  # MHz: 2 m band (APRS 144.800), LoRa EU868, ADS-B
EXEMPLE_M = 15  # roof antenna to the Raspberry Pi
NF_RECEPTEUR = (3.0, 5.0, 8.0)  # assumed receiver noise figures, dB (no datasheet value used)


def ratio(db):
    """Power ratio for a loss of db decibels (ITU-R V.574: 10 lg(P1/P2))."""
    return 10 ** (-db / 10)


def fit(points):
    """Least squares fit of alpha(f) = a*sqrt(f) + b*f on the points from 50 MHz up (dB/100 ft)."""
    pts = [(f, a) for f, a in points if f >= 50]
    s11 = sum(f for f, _ in pts)                 # sum sqrt(f)^2
    s12 = sum(f ** 1.5 for f, _ in pts)          # sum sqrt(f)*f
    s22 = sum(f * f for f, _ in pts)
    t1 = sum(a * math.sqrt(f) for f, a in pts)
    t2 = sum(a * f for f, a in pts)
    det = s11 * s22 - s12 * s12
    return (t1 * s22 - t2 * s12) / det, (s11 * t2 - s12 * t1) / det


def modele(nom):
    """Coefficients (a, b) in dB/100 ft and how they were obtained."""
    c = CABLES[nom]
    if "formula_db_100ft" in c:
        return c["formula_db_100ft"], "manufacturer formula"
    return fit(c["points_db_100ft"]), "least squares fit, points >= 50 MHz"


def alpha_100m(nom, f):
    (a, b), _ = modele(nom)
    return (a * math.sqrt(f) + b * f) * DB100FT_TO_DB100M


def loglog(nom, f):
    """Cross-check: straight line in log-log between the two datasheet points around f
    (the last two points when f is past the end of the table)."""
    pts = CABLES[nom]["points_db_100ft"]
    for (f1, a1), (f2, a2) in zip(pts, pts[1:]):
        if f1 <= f <= f2:
            break
    else:
        (f1, a1), (f2, a2) = pts[-2], pts[-1]
    k = math.log(a2 / a1) / math.log(f2 / f1)
    return a1 * (f / f1) ** k * DB100FT_TO_DB100M


def statut(nom, f):
    fmax = max(p for p, _ in CABLES[nom]["points_db_100ft"])
    return "extrapolated" if f > fmax else "interpolated"


def cmd_db():
    print("Loss (dB)   power left   (10 lg(P1/P2), ITU-R V.574)")
    for db in (0.5, 1, 3, 6, 7.5, 10, 20):
        print(f"{db:>8.1f}   {100 * ratio(db):>9.1f} %")
    print()
    print(f"3 dB: {ratio(3):.4f} of the power, i.e. half. 10 dB: a tenth. 20 dB: a hundredth.")


def cmd_fiches():
    for nom in CABLES:
        (a, b), comment = modele(nom)
        print(f"{nom}: {CABLES[nom]['datasheet']}")
        print(f"  model: alpha(f) = {a:.5f}*sqrt(f) + {b:.6f}*f  dB/100 ft  ({comment})")
        print("  f (MHz)  datasheet dB/100 m  model dB/100 m  gap")
        for f, att in CABLES[nom]["points_db_100ft"]:
            if f < 50:
                continue
            fiche = att * DB100FT_TO_DB100M
            mod = alpha_100m(nom, f)
            print(f"  {f:>7}  {fiche:>18.1f}  {mod:>14.1f}  {mod - fiche:>+5.1f}")
        print()


def cmd_tableau():
    print(f"Attenuation in dB/100 m, and loss of {EXEMPLE_M} m of cable (model of 'fiches')")
    print("cable    f (MHz)  dB/100 m  log-log check  status        "
          f"{EXEMPLE_M} m loss  power left")
    for nom in CABLES:
        for f in FREQS:
            a = alpha_100m(nom, f)
            perte = a * EXEMPLE_M / 100
            print(f"{nom:<8} {f:>7}  {a:>8.1f}  {loglog(nom, f):>13.1f}  {statut(nom, f):<12}  "
                  f"{perte:>7.2f} dB  {100 * ratio(perte):>8.1f} %")
        print()
    print("1090 MHz is past the end of the Belden RG174 and RG58 tables (1000 MHz): extrapolated.")


def connecteurs(f_ghz):
    return sum(c["max_db"](f_ghz) for c in CONNECTORS.values())


def cmd_adsb():
    f = 1090
    print(f"ADS-B receiver, {f} MHz: roof antenna, coax down to the Raspberry Pi")
    print(f"Antenna: {ANTENNA_DBI} dBi, i.e. {ANTENNA_DBI - DIPOLE_DBI:.2f} dB more than a half-wave dipole "
          f"({DIPOLE_DBI} dBi)")
    print("Connectors (maximum insertion loss):")
    for nom, c in CONNECTORS.items():
        print(f"  {nom}: {c['rule']} -> {c['max_db'](f / 1000):.3f} dB")
    pc = connecteurs(f / 1000)
    print(f"  both: {pc:.3f} dB")
    print()
    print("cable    length  cable loss  with 2 conn.  power left  vs antenna gain over dipole")
    for nom in ("RG174", "RG58", "RG213", "LMR400"):
        for m in (5, 10, 15, 20):
            pl = alpha_100m(nom, f) * m / 100
            tot = pl + pc
            ecart = tot - (ANTENNA_DBI - DIPOLE_DBI)
            print(f"{nom:<8} {m:>4} m  {pl:>7.2f} dB  {tot:>9.2f} dB  {100 * ratio(tot):>8.1f} %  "
                  f"{'loses' if ecart > 0 else 'keeps'} {abs(ecart):.2f} dB")
        print()
    pl = alpha_100m("RG58", f) * EXEMPLE_M / 100 + pc
    print(f"Example: {EXEMPLE_M} m of RG58 + 2 connectors = {pl:.2f} dB, more than the whole {ANTENNA_DBI} dBi "
          f"of the antenna.")


def nf_db(f):
    return 10 * math.log10(f)


def lin(db):
    return 10 ** (db / 10)


def cmd_bruit():
    f = 1090
    pc = connecteurs(f / 1000)
    l58 = alpha_100m("RG58", f) * EXEMPLE_M / 100 + pc
    l400 = alpha_100m("LMR400", f) * EXEMPLE_M / 100 + pc
    g = LNA["gain_db"]
    print(f"System noise figure at {f} MHz, {EXEMPLE_M} m of cable + 2 connectors, line at 290 K")
    print("ITU-R P.372, eq. (1) and (5): a line of loss lt at 290 K in front of a receiver of factor fr gives lt*fr.")
    print("Friis cascade: F = F1 + (F2 - 1)/G1.")
    print(f"LNA {LNA['name']}: NF {LNA['nf_db']} dB, gain {g} dB (typical at 1.0 GHz)")
    print(f"Line loss: RG58 {l58:.2f} dB, LMR400 {l400:.2f} dB")
    print()
    fl = lin(LNA["nf_db"])
    gl = lin(g)
    for fr_db in NF_RECEPTEUR:
        fr = lin(fr_db)
        cas = [
            ("receiver at the antenna (no cable)", fr),
            ("antenna > RG58 > receiver", lin(l58) * fr),
            ("antenna > RG58 > LNA > receiver", lin(l58) * (fl + (fr - 1) / gl)),
            ("antenna > LNA > RG58 > receiver", fl + (lin(l58) * fr - 1) / gl),
            ("antenna > LMR400 > receiver", lin(l400) * fr),
            ("antenna > LNA > LMR400 > receiver", fl + (lin(l400) * fr - 1) / gl),
        ]
        print(f"Receiver noise figure assumed: {fr_db:.0f} dB")
        for nom, ft in cas:
            print(f"  {nom:<36} NF {nf_db(ft):>5.2f} dB")
        print()
    fr = lin(5.0)
    gmin = lin(LNA["gain_min_db"])
    print(f"Same with the minimum LNA gain ({LNA['gain_min_db']} dB), receiver 5 dB: "
          f"antenna > LNA > RG58 > receiver NF {nf_db(fl + (lin(l58) * fr - 1) / gmin):.2f} dB")


def main():
    cmds = {"db": cmd_db, "fiches": cmd_fiches, "tableau": cmd_tableau, "adsb": cmd_adsb, "bruit": cmd_bruit}
    if len(sys.argv) != 2 or sys.argv[1] not in cmds:
        sys.exit("usage: pertes.py " + " | ".join(cmds))
    cmds[sys.argv[1]]()


if __name__ == "__main__":
    main()
