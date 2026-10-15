#!/usr/bin/env python3
"""Reads the nec2c outputs in raw/ and prints the stable outputs of the bench (sorties/).

Coupling between two ports t (transmit) and r (receive), from the port impedance matrix Z:
    G = P_received / P_input = |Z_rt|^2 / (4 Re(Z_tt) Re(Z_rr))
i.e. the transmit port is driven, the receive port feeds a conjugate-matched load. This is
the usual weak-coupling form (the receive load does not change the transmit current), valid
here: at 10 wavelengths the coupling is below -30 dB.
Z is the inverse of the admittance matrix Y read from nec2c (one excitation per port).
Standard library only.
"""
import cmath
import math
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import modele  # noqa: E402  (constants of the bench)

ICI = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ICI, "raw")
PORT_SEG = (modele.NSEG + 1) // 2


def lire(nom):
    """List of (comment, {tag: current at port segment}, [pattern rows])."""
    texte = open(os.path.join(RAW, nom + ".out"), encoding="utf-8", errors="replace").read()
    blocs = texte.split("---------------- COMMENTS ----------------")[1:]
    res = []
    for b in blocs:
        commentaire = b.strip().split("\n")[0].strip()
        courants, compte = {}, {}
        m = b.split("CURRENTS AND LOCATION")
        if len(m) > 1:
            for ligne in m[1].split("\n"):
                c = ligne.split()
                if len(c) == 10 and c[0].isdigit() and c[1].isdigit():
                    tag = int(c[1])
                    compte[tag] = compte.get(tag, 0) + 1
                    if compte[tag] == PORT_SEG:
                        courants[tag] = complex(float(c[6]), float(c[7]))
        rp = []
        for ligne in b.split("\n"):
            c = ligne.split()
            if len(c) == 12 and c[7] in ("LINEAR", "RIGHT", "LEFT"):
                rp.append(c)
        res.append((commentaire, courants, rp))
    return res


def param(commentaire, nom):
    return re.search(nom + r"=(\S+)", commentaire).group(1)


def inverse(a):
    n = len(a)
    m = [list(r) + [1.0 if i == j else 0.0 for j in range(n)] for i, r in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        m[col], m[piv] = m[piv], m[col]
        p = m[col][col]
        m[col] = [v / p for v in m[col]]
        for r in range(n):
            if r != col:
                fac = m[r][col]
                m[r] = [v - fac * w for v, w in zip(m[r], m[col])]
    return [r[n:] for r in m]


def matrice_z(blocs, ports):
    """blocs: one per excited port, in the order of ports. Returns Z as dict[(i, j)]."""
    y = [[blocs[j][1][i] for j in range(len(ports))] for i in ports]
    z = inverse(y)
    return {(pi, pj): z[a][b] for a, pi in enumerate(ports) for b, pj in enumerate(ports)}


def db(x):
    return 10 * math.log10(x) if x > 0 else float("-inf")


def couplage(z, t, r):
    return abs(z[(r, t)]) ** 2 / (4 * z[(t, t)].real * z[(r, r)].real)


def par_angle(nom, ports=(1, 2)):
    groupes = {}
    for b in lire(nom):
        if "angle=" in b[0]:
            groupes.setdefault(int(param(b[0], "angle")), []).append(b)
    return {a: matrice_z(bl, ports) for a, bl in sorted(groupes.items())}


def fmt_db(x):
    if x < -200:
        return "  < -200"   # numerical zero: nec2c rounding, not a physical value
    return f"{x:8.2f}"


def etape_rotation():
    lam = modele.LAMBDA
    print(f"Two dipoles of {modele.L_DIPOLE * 100:.1f} cm at {modele.F_MHZ:g} MHz (lambda = {lam * 100:.2f} cm), "
          f"{modele.D_LIEN:.2f} m apart (10 lambda), free space")
    print("Transmit dipole vertical. Receive dipole rotated by an angle about the line between them.")
    print("Coupling = power into a matched load / power fed to the transmit dipole")
    zs = par_angle("01-rotation")
    ref = couplage(zs[0], 1, 2)
    print("  angle   coupling   vs 0 deg   cos^2 law   difference")
    for a, z in zs.items():
        g = db(couplage(z, 1, 2))
        rel = g - db(ref)
        loi = 20 * math.log10(abs(math.cos(math.radians(a)))) if a != 90 else float("-inf")
        loi_txt = f"{fmt_db(loi)} dB" if a != 90 else "    -inf   "
        diff = f"{rel - loi:+8.2f} dB" if a != 90 else ""
        print(f"  {a:3d} deg  {fmt_db(g)} dB {fmt_db(rel)} dB {loi_txt}  {diff}".rstrip())
    print("< -200 dB: numerical zero (rounding in nec2c), the coupling is nil by symmetry")
    z90 = zs[90]
    print(f"At 90 deg: |Z21| = {abs(z90[(2, 1)]):.2e} ohm, against {abs(zs[0][(2, 1)]):.2e} ohm at 0 deg")
    rp = [b for b in lire("01-rotation") if b[2]][0][2][0]
    gain = float(rp[4])
    print(f"Lone vertical dipole, toward +y (nec2c): E(theta) = {float(rp[8]):.4f} V/m, E(phi) = {float(rp[10]):.4f} V/m, "
          f"polarization {rp[7]}: the field is vertical, parallel to the wire")
    friis = 2 * gain + 20 * math.log10(lam / (4 * math.pi * modele.D_LIEN))
    print(f"Check: dipole gain {gain:.2f} dBi (nec2c), Friis 2 x {gain:.2f} dBi + 20 log(lambda / 4 pi d) "
          f"= {friis:.2f} dB, bench at 0 deg = {db(ref):.2f} dB")


def etape_reflet():
    print("Same link, plus a metal wire of 1 m (1 mm diameter) tilted 45 deg,")
    print(f"halfway along the link ({modele.D_LIEN / 2:.2f} m) and 50 cm to the side of it")
    sans = par_angle("01-rotation")
    avec = par_angle("02-reflet")
    print("  angle   without wire   with wire")
    for a in (0, 90):
        print(f"  {a:3d} deg  {fmt_db(db(couplage(sans[a], 1, 2)))} dB   {fmt_db(db(couplage(avec[a], 1, 2)))} dB")
    iso = db(couplage(avec[0], 1, 2)) - db(couplage(avec[90], 1, 2))
    print(f"Isolation between 0 and 90 deg with the wire: {iso:.1f} dB")


def etape_portee():
    print("Free-space range scales as the square root of the received power:")
    print("range factor = 10^(-loss / 20)")
    sans = par_angle("01-rotation")
    avec = par_angle("02-reflet")
    ref0 = db(couplage(sans[0], 1, 2))
    cas = [("tilted 45 deg", ref0 - db(couplage(sans[45], 1, 2))),
           ("horizontal, wire nearby", db(couplage(avec[0], 1, 2)) - db(couplage(avec[90], 1, 2))),
           ("horizontal, 10 dB (*)", 10.0)]
    print("  case                       loss     range factor   200 km becomes")
    for nom, perte in cas:
        k = 10 ** (-perte / 20)
        print(f"  {nom:24s} {perte:6.2f} dB    {k:6.3f}          {200 * k:6.1f} km")
    print("(*) ITU-R P.1406-2, 5.1.1: average XPD over 10 dB in open areas, 5 to 8 dB in towns (900 MHz)")


def etape_circulaire():
    k = 2 * math.pi / modele.LAMBDA
    print(f"Turnstile: two crossed dipoles fed 90 deg apart, at each end, {modele.D_LIEN:.2f} m apart")
    print(f"The horizontal dipole sits {modele.DELTA * 1000:.0f} mm behind the vertical one; the feed phase includes it.")
    blocs = lire("03-circulaire")
    z = matrice_z([b for b in blocs if "port=" in b[0]], (1, 2, 3, 4))
    sens = {}
    for c, _, rp in blocs:
        if c.startswith("sense"):
            sens[c] = rp[0][7]
            print(f"  nec2c, {c}: axial ratio {rp[0][5]}, sense {rp[0][7]}")
    dec = cmath.exp(1j * k * modele.DELTA)
    poids = {"plus90": 1j * dec, "minus90": -1j * dec}
    tx = {sens[f"sense tx {n}"]: w for n, w in poids.items()}
    rx = {sens[f"sense rx {n}"]: w for n, w in poids.items()}
    r_rx = (z[(3, 3)].real + z[(4, 4)].real) / 2
    print(f"  |Z34| = {abs(z[(3, 4)]):.2e} ohm (crossed dipoles do not couple), R33 = {z[(3, 3)].real:.2f} ohm, "
          f"R44 = {z[(4, 4)].real:.2f} ohm")

    def p_in(i):
        v1 = z[(1, 1)] * i[0] + z[(1, 2)] * i[1]
        v2 = z[(2, 1)] * i[0] + z[(2, 2)] * i[1]
        return 0.5 * (v1 * i[0].conjugate() + v2 * i[1].conjugate()).real

    def v_rx(i):
        return (z[(3, 1)] * i[0] + z[(3, 2)] * i[1], z[(4, 1)] * i[0] + z[(4, 2)] * i[1])

    def g_lin(i):
        v3, _ = v_rx(i)
        return abs(v3) ** 2 / (8 * z[(3, 3)].real) / p_in(i)

    def g_horiz(i):
        _, v4 = v_rx(i)
        return abs(v4) ** 2 / (8 * z[(4, 4)].real) / p_in(i)

    def g_circ(i, c):
        v3, v4 = v_rx(i)
        return abs(v3 + c * v4) ** 2 / (16 * r_rx) / p_in(i)

    vert = (1, 0)
    ref = db(g_lin(vert))
    print("  transmit         receive          coupling   vs vertical/vertical")
    lignes = [("vertical", "vertical", g_lin(vert)),
              ("vertical", "circular RIGHT", g_circ(vert, rx["RIGHT"])),
              ("circular RIGHT", "vertical", g_lin((1, tx["RIGHT"]))),
              ("circular RIGHT", "horizontal", g_horiz((1, tx["RIGHT"]))),
              ("circular RIGHT", "circular RIGHT", g_circ((1, tx["RIGHT"]), rx["RIGHT"])),
              ("circular RIGHT", "circular LEFT", g_circ((1, tx["RIGHT"]), rx["LEFT"])),
              ("circular LEFT", "circular LEFT", g_circ((1, tx["LEFT"]), rx["LEFT"]))]
    for a, b, g in lignes:
        print(f"  {a:16s} {b:16s} {fmt_db(db(g))} dB {fmt_db(db(g) - ref)} dB")


ETAPES = {"rotation": etape_rotation, "reflet": etape_reflet, "portee": etape_portee, "circulaire": etape_circulaire}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ETAPES:
        sys.exit("usage: python3 analyse.py " + "|".join(ETAPES))
    ETAPES[sys.argv[1]]()
