#!/usr/bin/env python3
"""Reads the nec2c outputs in travail/*.out and prints stable text outputs (standard library only).

  python3 analyse.py gains          max gain in dBi and dBd, gain at the horizon, -3 dB beamwidths
  python3 analyse.py conservation   power budget, NEC average gain and our own integral over the sphere
  python3 analyse.py toit           rooftop ADS-B example: whip versus collinear, for aircraft at several distances
  python3 analyse.py json           vertical and horizontal cuts, for the polar plots of the deck

No time, no host name, no version is printed: the outputs depend only on the .out files.
"""
import json
import math
import os
import re
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
TRAVAIL = os.path.join(ICI, "travail")
ANTENNES = [("dipole", "half-wave dipole"), ("fouet", "quarter-wave whip"),
            ("yagi", "3-element Yagi"), ("colineaire", "collinear, 2 dipoles")]
DIPOLE_DBI = 2.15            # gain of an ideal half-wave dipole, the 0 dBd reference


def lire(nom):
    """Returns impedances, power budget, average gain and the four RP blocks of one .out file."""
    texte = open(os.path.join(TRAVAIL, nom + ".out"), encoding="ascii").read()
    entree = texte.split("ANTENNA INPUT PARAMETERS")[1].split("CURRENTS AND LOCATION")[0]
    imp = []
    for ligne in entree.splitlines():
        champs = ligne.split()
        if len(champs) == 11 and champs[0].isdigit():
            imp.append((float(champs[6]), float(champs[7])))
    budget = {}
    for cle, motif in (("in", r"INPUT POWER\s*=\s*(\S+)"), ("rad", r"RADIATED POWER=\s*(\S+)"),
                       ("eff", r"EFFICIENCY\s*=\s*(\S+)")):
        budget[cle] = float(re.search(motif, texte).group(1))
    moyenne = re.search(r"AVERAGE POWER GAIN:\s*(\S+) - SOLID ANGLE USED IN AVERAGING: \((\S+)\)\*PI", texte)
    blocs = []
    for morceau in texte.split("RADIATION PATTERNS")[1:]:
        points = []
        for ligne in morceau.splitlines()[5:]:
            champs = ligne.split()
            if len(champs) < 5:
                break
            try:
                points.append((float(champs[0]), float(champs[1]), float(champs[4])))
            except ValueError:
                break
        blocs.append(points)
    return {"imp": imp, "budget": budget, "moy": float(moyenne.group(1)), "angle_solide": float(moyenne.group(2)),
            "blocs": blocs, "lignes_moy": moyenne.group(0)}


def coupe_verticale(d):
    """Gain (dBi) by elevation angle, -90..+90, for phi = 0 (front) and phi = 180 (back)."""
    avant = {round(90 - t): g for t, p, g in d["blocs"][0]}
    arriere = {round(90 - t): g for t, p, g in d["blocs"][1]}
    return avant, arriere


def coupe_horizontale(d):
    return {round(p): g for t, p, g in d["blocs"][2]}


def maximum(d):
    tous = [pt for b in d["blocs"] for pt in b]
    t, p, g = max(tous, key=lambda x: x[2])
    return g, t, p


def largeur(coupe, centre, pas_max):
    """-3 dB width around 'centre' in a dict angle -> dB (1 degree steps), linear interpolation."""
    g0 = coupe[centre]
    bords = []
    for sens in (1, -1):
        a = centre
        while True:
            b = a + sens
            if abs(b - centre) > pas_max or b not in coupe and (b % 360) not in coupe:
                return None
            gb = coupe.get(b, coupe.get(b % 360))
            ga = coupe.get(a, coupe.get(a % 360))
            if gb <= g0 - 3:
                bords.append(a + sens * (ga - (g0 - 3)) / (ga - gb))
                break
            a = b
    return abs(bords[0] - bords[1])


def integrale(d):
    """Average of the linear power gain over the sphere, from the 2-degree grid (trapezoids in theta)."""
    grille = {}
    for t, p, g in d["blocs"][3]:
        grille.setdefault(t, []).append(0.0 if g < -900 else 10 ** (g / 10))
    thetas = sorted(grille)
    dphi = math.radians(360 / len(grille[thetas[0]]))
    somme = 0.0
    for k in range(len(thetas) - 1):
        t1, t2 = thetas[k], thetas[k + 1]
        f1 = sum(grille[t1]) * dphi * math.sin(math.radians(t1))
        f2 = sum(grille[t2]) * dphi * math.sin(math.radians(t2))
        somme += (f1 + f2) / 2 * math.radians(t2 - t1)
    return somme / (4 * math.pi)


def gains():
    print("antenna               Z (ohm)       max dBi  max dBd  behind dBi  -3 dB vert  -3 dB horiz")
    print(f"{'isotropic (theory)':20}  {'-':12}  {0:7.2f}  {-DIPOLE_DBI:7.2f}  {0:10.2f}  {'none':>10}  {'none':>11}")
    for nom, titre in ANTENNES:
        d = lire(nom)
        r, x = d["imp"][0]
        g, t, p = maximum(d)
        avant, _ = coupe_verticale(d)
        hor = coupe_horizontale(d)
        e_max = max(avant, key=avant.get)
        lv = largeur(avant, e_max, 90)
        ecart = max(hor.values()) - min(hor.values())
        lh = largeur(hor, max(hor, key=hor.get), 180) if ecart > 3 else None
        txt_h = f"{lh:.0f} deg" if lh else f"omni {ecart:.1f}"
        z = f"{r:.1f} {x:+.1f}j"
        print(f"{titre:20}  {z:12}  {g:7.2f}  {g - DIPOLE_DBI:7.2f}  {hor[180]:10.2f}  {lv:6.0f} deg  {txt_h:>11}")
    print()
    print("Free space, 1090 MHz, perfect conductors. dBd = dBi - 2.15 (ideal half-wave dipole).")
    print("behind: horizon, opposite the Yagi beam (phi = 180). -3 dB vert: main lobe width in")
    print("the vertical plane. omni x: gain varies by x dB around the antenna (less than 3 dB).")


def conservation():
    print("antenna               input W     radiated W  eff. %  max dBi  NEC avg  our avg")
    for nom, titre in ANTENNES:
        d = lire(nom)
        b = d["budget"]
        g, _, _ = maximum(d)
        print(f"{titre:20}  {b['in']:.4E}  {b['rad']:.4E}  {b['eff']:6.2f}  {g:7.2f}  {d['moy']:7.4f}  {integrale(d):7.4f}")
    print()
    print("1 V per source. avg = power gain averaged over the whole sphere, in linear units:")
    print("1.0000 means all the input power leaves as radiation, whatever the shape.")
    print("NEC avg: NEC2's own sum (solid angle 3.9889 pi). our avg: 1-degree grid, trapezoids")
    print("in theta, sin(theta) weighting, divided by 4 pi.")


RAYON_TERRE_KM = 6371.0      # mean Earth radius, spherical Earth, no refraction
ALTITUDE_M = 10000.0         # example aircraft altitude
DISTANCES_KM = [5, 10, 25, 50, 100, 200, 300]


def interpole(coupe, e):
    a = math.floor(e)
    if a == e:
        return coupe[a]
    return coupe[a] + (coupe[a + 1] - coupe[a]) * (e - a)


def geometrie(x):
    """Ground distance x (km) -> elevation (deg) and slant distance (km) of an aircraft at ALTITUDE_M."""
    phi = x / RAYON_TERRE_KM                       # angle at the Earth centre
    r = RAYON_TERRE_KM + ALTITUDE_M / 1000
    dx = r * math.sin(phi)
    dz = r * math.cos(phi) - RAYON_TERRE_KM
    return math.degrees(math.atan2(dz, dx)), math.hypot(dx, dz)


def sol_pour_elevation(e):
    """Ground distance (km) at which the aircraft is seen at elevation e (bisection)."""
    a, b = 0.001, 1000.0
    for _ in range(100):
        m = (a + b) / 2
        if geometrie(m)[0] > e:
            a = m
        else:
            b = m
    el, d = geometrie(a)
    return a, el, d


def toit():
    lam_km = 299792.458 / 1090e6                       # wavelength in km (c in km/s, f in Hz)
    fouet, _ = coupe_verticale(lire("fouet"))
    coli, _ = coupe_verticale(lire("colineaire"))
    print(f"Aircraft at {ALTITUDE_M:.0f} m, antenna at ground level, 1090 MHz, free space.")
    print("ground  elev.  slant   path    whip   coll.  coll.    whip     coll.")
    print("km      deg    km      loss dB dBi    dBi    - whip   G-L dB   G-L dB")
    lignes = []
    for x in DISTANCES_KM:
        e, d = geometrie(x)
        perte = 20 * math.log10(4 * math.pi * d / lam_km)
        gf, gc = interpole(fouet, e), interpole(coli, e)
        lignes.append((x, e, d, perte, gf, gc))
        print(f"{x:<6}  {e:5.1f}  {d:5.1f}  {perte:6.1f}  {gf:5.2f}  {gc:6.2f}  {gc - gf:+6.2f}  {gf - perte:7.1f}  {gc - perte:7.1f}")
    print()
    for nom, k in (("whip", 4), ("collinear", 5)):
        faible = min(lignes, key=lambda l: l[k] - l[3])
        print(f"Weakest aircraft in the table, {nom}: the one at {faible[0]} km, {faible[k] - faible[3]:.1f} dB.")
    e_trou = min(range(1, 90), key=lambda e: coli[e])
    x_trou, _, d_trou = sol_pour_elevation(e_trou)
    perte_trou = 20 * math.log10(4 * math.pi * d_trou / lam_km)
    print(f"Collinear dip: {coli[e_trou]:.2f} dBi at {e_trou} deg elevation (whip: {fouet[e_trou]:.2f} dBi),")
    print(f"  aircraft {x_trou:.1f} km away on the ground: collinear G-L {coli[e_trou] - perte_trou:.1f} dB, whip {fouet[e_trou] - perte_trou:.1f} dB.")
    trou = [e for e in range(1, 90) if coli[e] < fouet[e] - 10]
    xa, xb = sol_pour_elevation(trou[-1])[0], sol_pour_elevation(trou[0])[0]
    print(f"Collinear more than 10 dB below the whip: {trou[0]} to {trou[-1]} deg ({xa:.1f} to {xb:.1f} km on the ground).")
    print()
    print("Below the horizon (antenna on a high point, stations further down):")
    print("elev. deg    " + "  ".join(f"{e:6d}" for e in (-5, -15, -30, -45, -60)))
    print("whip dBi     " + "  ".join(f"{fouet[e]:6.2f}" for e in (-5, -15, -30, -45, -60)))
    print("coll. dBi    " + "  ".join(f"{coli[e]:6.2f}" for e in (-5, -15, -30, -45, -60)))
    print()
    print("G-L = antenna gain minus path loss. Path loss = 20 log10(4 pi d / lambda).")
    print("Spherical Earth, radius 6371 km, no refraction, no ground reflection.")


def donnees_json():
    sortie = {}
    for nom, titre in ANTENNES:
        d = lire(nom)
        avant, arriere = coupe_verticale(d)
        hor = coupe_horizontale(d)
        g, _, _ = maximum(d)
        sortie[nom] = {
            "titre": titre,
            "max": round(g, 2),
            # vertical cut: elevation -90..90 in front (phi = 0), then behind (phi = 180)
            "avant": [round(avant[e], 2) for e in range(-90, 91)],
            "arriere": [round(arriere[e], 2) for e in range(-90, 91)],
            "horizontal": [round(hor[p], 2) for p in range(360)],
        }
    # rooftop example: aircraft at ALTITUDE_M, ground distance x -> elevation, path loss, G-L whip and collinear
    lam_km = 299792.458 / 1090e6
    fouet, _ = coupe_verticale(lire("fouet"))
    coli, _ = coupe_verticale(lire("colineaire"))
    xs = [k / 2 for k in range(4, 60)] + list(range(30, 401, 2))
    toit_pts = []
    for x in xs:
        e, d = geometrie(x)
        perte = 20 * math.log10(4 * math.pi * d / lam_km)
        toit_pts.append([x, round(e, 2), round(perte, 2), round(interpole(fouet, e) - perte, 2), round(interpole(coli, e) - perte, 2)])
    sortie["toit"] = {"altitude_m": ALTITUDE_M, "colonnes": ["ground km", "elev deg", "path loss dB", "whip G-L", "coll G-L"],
                      "points": toit_pts}
    print(json.dumps(sortie, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    {"gains": gains, "conservation": conservation, "toit": toit, "json": donnees_json}[sys.argv[1]]()
