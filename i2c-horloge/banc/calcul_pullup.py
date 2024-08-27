#!/usr/bin/env python3
"""Worked example: rise time of an I²C line pulled up by a pull-up resistor.

Formulas from NXP UM10204 rev. 7.0, § 7.1 (p. 50):
  rise from 0.3 VDD to 0.7 VDD: tr = 0.8473 x Rp x Cb
  Rp(max) = tr(max) / (0,8473 x Cb)          (equation 1)
  Rp(min) = (VDD - VOL(max)) / IOL            (equation 2)
Limits from table 11 (p. 44): tr max 1000 ns (Standard-mode), 300 ns (Fast-mode),
Cb max 400 pF, VOL max 0.4 V at IOL = 3 mA.
"""

import sys as _sys
EN = '--en' in _sys.argv
if EN:
    _sys.argv.remove('--en')


def L(fr, en):
    """Text depending on the language: --en on the command line gives English."""
    return en if EN else fr


K = 0.8473
TR = {'standard (100 kHz)': 1000e-9, 'fast (400 kHz)': 300e-9}


def main():
    vdd, vol, iol = 3.3, 0.4, 3e-3
    print(L(f"Rp(min) à {vdd} V : ", f"Rp(min) at {vdd} V: ") + f"({vdd} - {vol}) / {iol * 1e3:.0f} mA = {(vdd - vol) / iol:.0f} ohms")
    print()
    print(L("Rp(max) selon la capacité du bus :", "Rp(max) versus bus capacitance:"))
    print("   Cb     standard   fast")
    for cb in (50e-12, 100e-12, 200e-12, 400e-12):
        print(f"  {cb * 1e12:3.0f} pF " + "  ".join(f"{t / (K * cb) / 1e3:6.2f} k" for t in TR.values()))
    print()
    print(L("tr = 0,8473 x Rp x Cb :", "tr = 0.8473 x Rp x Cb:"))
    print("   Rp       100 pF     200 pF     400 pF")
    for rp in (1e3, 2.2e3, 4.7e3, 10e3):
        cases = []
        for cb in (100e-12, 200e-12, 400e-12):
            tr = K * rp * cb
            marque = 'ok' if tr <= 300e-9 else ('std' if tr <= 1000e-9 else 'KO')
            cases.append(f"{tr * 1e9:5.0f} ns {marque:3}")
        print(f"  {rp / 1e3:4.1f} k  " + "  ".join(cases))
    print()
    print(L("ok = fast et standard, std = standard seulement, KO = hors spec", "ok = fast and standard, std = standard only, KO = out of spec"))


if __name__ == '__main__':
    main()
