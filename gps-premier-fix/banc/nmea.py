"""Hand-written NMEA 0183 decoder (standard library only).

Usage:
  python3 nmea.py [--en] checksum '<phrase>'     XOR recomputed, character by character
  python3 nmea.py [--en] champs '<phrase>'       field-by-field decoding (GGA, RMC, GSA, GSV)
  python3 nmea.py [--en] chrono <fichier.log>    one cycle per GGA: quality, satellites, HDOP, sky seen through GSV
--en: labels in English (default: French).
"""
import sys

EN = "--en" in sys.argv
ARGS = [a for a in sys.argv[1:] if a != "--en"]


def L(fr, en):
    return en if EN else fr


QUALITE = {"0": L("pas de fix", "no fix"), "1": L("fix GPS", "GPS fix"), "2": L("fix différentiel", "differential fix")}
VIDE = L("(vide)", "(empty)")


def xor(corps):
    x = 0
    for c in corps:
        x ^= ord(c)
    return x


def coupe(phrase):
    """Returns (body between $ and *, announced checksum)."""
    phrase = phrase.strip()
    assert phrase.startswith("$"), phrase
    corps, _, annonce = phrase[1:].partition("*")
    return corps, annonce.upper()


def cmd_checksum(phrase):
    corps, annonce = coupe(phrase)
    print(f"{L('phrase  ', 'sentence')} : {phrase.strip()}")
    print(f"{L('XOR sur ', 'XOR over')} : {corps}  ({len(corps)} {L('caractères', 'characters')}, "
          f"{L('sans', 'without')} '$' {L('ni', 'or')} '*')")
    x = 0
    pas = []
    for c in corps:
        x ^= ord(c)
        pas.append(f"{c}:{x:02X}")
    for i in range(0, len(pas), 8):
        print("  " + "  ".join(pas[i:i + 8]))
    etat = "OK" if f"{x:02X}" == annonce else L("FAUX", "WRONG")
    print(f"{L('calculé', 'computed')} {x:02X}, {L('annoncé', 'announced')} {annonce} : {etat}")


def cmd_champs(phrase):
    corps, annonce = coupe(phrase)
    f = corps.split(",")
    tag = f[0]
    ok = "OK" if f"{xor(corps):02X}" == annonce else L("FAUX", "WRONG")
    print(f"{tag}  (talker {tag[:2]}, type {tag[2:]})  checksum {annonce} {ok}")
    v = lambda i: f[i] if i < len(f) and f[i] != "" else VIDE
    if tag.endswith("GGA"):
        noms = [L("heure UTC", "UTC time"), "latitude", "N/S", "longitude", "E/W", L("qualité du fix", "fix quality"),
                L("satellites utilisés", "satellites used"), "HDOP", "altitude", L("unité", "unit"),
                L("écart géoïde", "geoid separation"), L("unité", "unit"),
                L("âge DGPS", "DGPS age"), L("station DGPS", "DGPS station")]
        for i, n in enumerate(noms, 1):
            extra = f"  -> {QUALITE.get(f[6], '?')}" if i == 6 else ""
            print(f"  {i:2d}  {n:20s} {v(i)}{extra}")
    elif tag.endswith("RMC"):
        noms = [L("heure UTC", "UTC time"), L("statut", "status"), "latitude", "N/S", "longitude", "E/W",
                L("vitesse (nœuds)", "speed (knots)"), L("route vraie", "true course"), "date",
                L("déclinaison", "magnetic variation"), "E/W", "mode"]
        for i, n in enumerate(noms, 1):
            extra = ""
            if i == 2:
                extra = "  -> " + {"A": L("valide", "valid"), "V": L("invalide (warning)", "invalid (warning)")}.get(f[2], "?")
            if i == 12:
                extra = "  -> " + {"A": L("autonome", "autonomous"), "N": L("pas valide", "not valid"),
                                   "D": L("différentiel", "differential")}.get(f[12] if len(f) > 12 else "", "?")
            print(f"  {i:2d}  {n:20s} {v(i)}{extra}")
    elif tag.endswith("GSA"):
        print(f"   1  {L('sélection', 'selection'):20s} {v(1)}")
        print(f"   2  {'mode':20s} {v(2)}  -> " + {"1": L("pas de fix", "no fix"), "2": L("fix 2D", "2D fix"),
                                                   "3": L("fix 3D", "3D fix")}.get(f[2], "?"))
        ids = [x for x in f[3:15] if x]
        print(f"3-14  {L('satellites utilisés', 'satellites used'):20s} {', '.join(ids) if ids else L('(aucun)', '(none)')}")
        print(f"  15  {'PDOP':20s} {v(15)}")
        print(f"  16  {'HDOP':20s} {v(16)}")
        print(f"  17  {'VDOP':20s} {v(17)}")
    elif tag.endswith("GSV"):
        print(f"   1  {L('phrases du groupe', 'sentences in group'):20s} {v(1)}")
        print(f"   2  {L('numéro de phrase', 'sentence number'):20s} {v(2)}")
        print(f"   3  {L('satellites visibles', 'satellites in view'):20s} {v(3)}")
        q = f[4:]
        for k in range(0, len(q) - 3, 4):
            prn, el, az, snr = q[k:k + 4]
            if not prn:
                continue
            inconnu = el in ("", "00") and az in ("", "000")
            pos = L("position inconnue", "position unknown") if inconnu else L("position connue", "position known")
            print(f"      PRN {prn:>2}  {L('élévation', 'elevation')} {el or '-':>3}  {L('azimut', 'azimuth')} {az or '-':>3}  "
                  f"SNR {snr or '-':>2} dB  -> {pos}")
    else:
        for i, x in enumerate(f[1:], 1):
            print(f"  {i:2d}  {x or VIDE}")


def cmd_chrono(chemin):
    lignes = open(chemin, encoding="ascii", errors="replace").read().splitlines()
    total = bons = 0
    cycles = []  # one cycle = one GGA
    ciel = {}    # talker -> {PRN: (elevation, azimuth, snr)}, last complete GSV group
    groupe = {}
    for n, l in enumerate(lignes, 1):
        if not l.startswith("$") or "*" not in l:
            continue
        corps, annonce = coupe(l)
        total += 1
        if f"{xor(corps):02X}" == annonce:
            bons += 1
        f = corps.split(",")
        tag = f[0]
        if tag.endswith("GSV") and len(f) > 3 and f[1] and f[2]:
            q = f[4:]
            for k in range(0, len(q) - 3, 4):
                if q[k]:
                    groupe[q[k]] = tuple(q[k + 1:k + 4])
            if f[1] == f[2]:
                ciel[tag[:2]], groupe = dict(groupe), {}
        if tag.endswith("GGA"):
            tout = {(t, p): v for t, d in ciel.items() for p, v in d.items()}
            suivis = [k for k, (el, az, snr) in tout.items() if snr]
            connus = [k for k in suivis if not (tout[k][0] in ("", "00") and tout[k][1] in ("", "000"))]
            cycles.append((n, f[1], f[6], f[7], f[8], len(suivis), len(connus)))
    print(f"{chemin.split('/')[-1]} : {total} {L('phrases, checksum juste sur', 'sentences, checksum correct on')} {bons}")
    premier = next((i for i, c in enumerate(cycles, 1) if c[2] not in ("0", "")), None)
    # cycles are grouped while quality, sats, HDOP, tracked and known positions do not change;
    # stop 3 cycles after the first fix
    fin = len(cycles) if premier is None else min(len(cycles), premier + 2)
    print(L(" cycles   heure UTC (début .. fin)   qualité  sats   HDOP  suivis  position connue",
            " cycles   UTC time (start .. end)    quality  sats   HDOP  tracked  position known"))
    i = 0
    while i < fin:
        j = i
        while j + 1 < fin and cycles[j + 1][2:] == cycles[i][2:]:
            j += 1
        _, h1, q, s, hd, sv, cn = cycles[i]
        h2 = cycles[j][1]
        num = f"{i + 1}" if i == j else f"{i + 1}-{j + 1}"
        heure = (h1 or VIDE) if i == j else f"{h1 or VIDE} .. {h2 or VIDE}"
        print(f" {num:>6}   {heure:25s}  {q:>7}  {s or '-':>4}  {hd or '-':>5}  {sv:6d}  {cn:6d}")
        i = j + 1
    if premier is None:
        print(L("aucun fix", "no fix"))
        return
    print(L(f"premier fix : cycle {premier}, après {premier - 1} cycles sans fix",
            f"first fix: cycle {premier}, after {premier - 1} cycles without a fix"))
    avant = [c for c in cycles[:premier - 1] if c[1]]
    if avant:
        t = lambda h: int(h[0:2]) * 3600 + int(h[2:4]) * 60 + float(h[4:])
        d = t(cycles[premier - 1][1]) - t(avant[0][1])
        print(L(f"horodatage : premier GGA daté sans fix {avant[0][1]}, premier fix {cycles[premier - 1][1]} : {d:.2f} s",
                f"timestamps: first dated GGA without a fix {avant[0][1]}, first fix {cycles[premier - 1][1]}: {d:.2f} s"))
    else:
        print(L("horodatage : aucun GGA sans fix ne porte d'heure, durée non mesurable depuis le log",
                "timestamps: no GGA without a fix carries a time, duration not measurable from the log"))


if __name__ == "__main__":
    {"checksum": cmd_checksum, "champs": cmd_champs, "chrono": cmd_chrono}[ARGS[0]](ARGS[1])
