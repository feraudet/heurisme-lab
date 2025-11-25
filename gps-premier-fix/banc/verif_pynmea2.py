"""Cross-check with pynmea2: checksums and first-fix cycle.

Usage: python3 verif_pynmea2.py [--en] <fichier.log> [...]
--en: labels in English (default: French).
"""
import sys

import pynmea2

EN = "--en" in sys.argv
for chemin in [a for a in sys.argv[1:] if a != "--en"]:
    total = erreurs = 0
    gga = 0
    premier = None
    for ligne in open(chemin, encoding="ascii", errors="replace"):
        ligne = ligne.strip()
        if not ligne.startswith("$"):
            continue
        total += 1
        try:
            m = pynmea2.parse(ligne, check=True)
        except pynmea2.ParseError:
            erreurs += 1
            continue
        if isinstance(m, pynmea2.types.talker.GGA):
            gga += 1
            if premier is None and m.gps_qual not in (None, 0):
                premier = (gga, m.timestamp, m.num_sats, m.horizontal_dil)
    nom = chemin.split('/')[-1]
    if EN:
        print(f"{nom}: {total} sentences, {erreurs} rejected by pynmea2, "
              f"first fix at GGA no. {premier[0]} (time {premier[1]}, {premier[2]} satellites, HDOP {premier[3]})")
    else:
        print(f"{nom} : {total} phrases, {erreurs} rejetées par pynmea2, "
              f"premier fix au GGA n° {premier[0]} (heure {premier[1]}, {premier[2]} satellites, HDOP {premier[3]})")
