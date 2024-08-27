#!/usr/bin/env python3
"""Measures SCL directly in a sigrok capture (.sr = zip + metadata).

Usage:
  python3 mesure_scl.py capture.sr [seuil_us]        frequency + long low levels
  python3 mesure_scl.py capture.sr --fronts debut fin   SCL/SDA edges (samples)

The VCD export of libsigrok 0.5.2 (Debian bookworm) comes out empty on these files,
hence this direct reading of the .sr format.
"""
import configparser
import statistics
import sys
import zipfile


import sys as _sys
EN = '--en' in _sys.argv
if EN:
    _sys.argv.remove('--en')


def L(fr, en):
    """Text depending on the language: --en on the command line gives English."""
    return en if EN else fr


def lire_sr(chemin):
    z = zipfile.ZipFile(chemin)
    meta = configparser.ConfigParser()
    meta.read_string(z.read('metadata').decode())
    dev = meta['device 1']
    taux = dev['samplerate'].split()
    hz = float(taux[0]) * {'Hz': 1, 'kHz': 1e3, 'MHz': 1e6}[taux[1]]
    unite = int(dev['unitsize'])
    voies = {v: int(k[5:]) - 1 for k, v in dev.items() if k.startswith('probe')}
    nom = dev['capturefile']
    morceaux = sorted((n for n in z.namelist() if n.startswith(nom + '-')),
                      key=lambda n: int(n.rsplit('-', 1)[1]))
    data = b''.join(z.read(n) for n in morceaux)
    return hz, unite, voies, data


def fronts(hz, unite, voies, data, nom):
    bit = voies[nom]
    octet, masque = bit // 8, 1 << (bit % 8)
    res, prec = [], None
    for i in range(0, len(data), unite):
        v = 1 if data[i + octet] & masque else 0
        if v != prec:
            res.append((i // unite, v))
            prec = v
    return res


def main():
    hz, unite, voies, data = lire_sr(sys.argv[1])
    scl = fronts(hz, unite, voies, data, 'SCL')
    if len(sys.argv) > 2 and sys.argv[2] == '--fronts':
        a, b = int(sys.argv[3]), int(sys.argv[4])
        sda = fronts(hz, unite, voies, data, 'SDA')
        for nom, f in (('SCL', scl), ('SDA', sda)):
            print(nom, ' '.join(f'{n}:{v}' for n, v in f if a <= n <= b))
        return
    seuil = float(sys.argv[2]) * 1e-6 if len(sys.argv) > 2 else 100e-6
    print(L(f"capture : {len(data) // unite} échantillons à {hz / 1e6:g} MHz ({len(data) // unite / hz * 1e3:.1f} ms), pas de {1e9 / hz:.0f} ns",
            f"capture: {len(data) // unite} samples at {hz / 1e6:g} MHz ({len(data) // unite / hz * 1e3:.1f} ms), {1e9 / hz:.0f} ns step"))
    bas, hauts = [], []
    for (n0, v0), (n1, _) in zip(scl, scl[1:]):
        (bas if v0 == 0 else hauts).append((n0 / hz, (n1 - n0) / hz))
    montees = [n / hz for n, v in scl if v == 1]
    periodes = [b - a for a, b in zip(montees, montees[1:]) if b - a < seuil]
    print(L(f"SCL : {len(montees)} fronts montants", f"SCL: {len(montees)} rising edges"))
    print(L("  période médiane    : ", "  median period      : ") + f"{statistics.median(periodes) * 1e6:6.2f} us"
          f"  ({1 / statistics.median(periodes) / 1e3:.1f} kHz)")
    print(L("  palier haut médian : ", "  median high time   : ") + f"{statistics.median(d for _, d in hauts if d < seuil) * 1e6:6.2f} us")
    print(L("  palier bas médian  : ", "  median low time    : ") + f"{statistics.median(d for _, d in bas if d < seuil) * 1e6:6.2f} us")
    print(L(f"paliers bas de SCL plus longs que {seuil * 1e6:.0f} us :", f"SCL low periods longer than {seuil * 1e6:.0f} us:"))
    for t0, d in bas:
        if d >= seuil:
            print(L(f"  à t = {t0 * 1e3:8.3f} ms   SCL tenu bas {d * 1e3:7.3f} ms", f"  at t = {t0 * 1e3:8.3f} ms   SCL held low {d * 1e3:7.3f} ms"))


if __name__ == '__main__':
    main()
