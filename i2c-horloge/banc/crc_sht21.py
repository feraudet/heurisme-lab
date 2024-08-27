#!/usr/bin/env python3
"""SHT21 CRC-8: polynomial x^8 + x^5 + x^4 + 1 (0x31), SHT21 datasheet § 5.7, initial value 0."""
import sys as _sys
EN = '--en' in _sys.argv
if EN:
    _sys.argv.remove('--en')


def L(fr, en):
    """Text depending on the language: --en on the command line gives English."""
    return en if EN else fr


def crc8(octets):
    crc = 0
    for o in octets:
        crc ^= o
        for _ in range(8):
            crc = ((crc << 1) ^ 0x31) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc
for donnees, recu in (([0x66, 0xF0], 0x8D), ([0x74, 0x2E], 0x21), ([0xFF, 0xFF], 0xFF)):
    c = crc8(donnees)
    print(f"{donnees[0]:02X} {donnees[1]:02X}  " + L(f"CRC reçu {recu:02X}  calculé {c:02X}  {'OK' if c == recu else 'FAUX'}", f"CRC received {recu:02X}  computed {c:02X}  {'OK' if c == recu else 'WRONG'}"))
