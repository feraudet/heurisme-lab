#!/usr/bin/env python3
"""Builds the AX.25 UI frame of p1.txt byte by byte, computes the FCS (CRC-16/X-25),
compares it with the hex dump of `atest -h`, then demodulates p1.wav by hand (AFSK 1200, NRZI,
bit stuffing) and checks that the FCS received over the air is the one computed.
Also writes signal.json: instantaneous frequency over an excerpt, for the deck."""
import json, os, re, sys, wave
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))  # work/ folder
RAW = os.path.join(ICI, "..", "raw")
print("Python", sys.version.split()[0], " numpy", np.__version__)

# ---------- 1. addresses ----------
def adresse(indicatif, ssid, bit7, dernier):
    """6 characters shifted one bit to the left, then the SSID byte: bit7 (C or H), RR=11, SSID, extension."""
    champ = indicatif.ljust(6).encode("ascii")
    octets = bytes(c << 1 for c in champ)
    s = (bit7 << 7) | (0b11 << 5) | (ssid << 1) | (1 if dernier else 0)
    return octets + bytes([s])

# bit 7: direwolf sets C=1 in destination AND source (seen in `atest -h`: c/r=1 twice)
ADR = [("APRS", 0, 1), ("F1TMV", 7, 1), ("WIDE1", 1, 0), ("WIDE2", 1, 0)]
trame = b""
print("\n== 1. Champ adresse (indicatif << 1, puis octet SSID)")
for k, (ind, ssid, b7) in enumerate(ADR):
    a = adresse(ind, ssid, b7, k == len(ADR) - 1)
    nom = ["dest  ", "source", "digi 1", "digi 2"][k]
    print(f"{nom} {ind + '-' + str(ssid):9} {a[:6].hex(' ')}  SSID {a[6]:02x} = {a[6]:08b}")
    trame += a
trame += bytes([0x03, 0xF0])
info = b"!4903.50N/07201.75W-Test"
trame += info
print(f"contrôle 03 (UI, P=0)   PID f0 (pas de couche 3)   info {len(info)} octets")
print(f"'F' = 0x{ord('F'):02x} -> 0x{ord('F') << 1:02x}   '1' = 0x{ord('1'):02x} -> 0x{ord('1') << 1:02x}   ' ' = 0x20 -> 0x40")

# ---------- 2. comparison with atest -h ----------
txt = open(os.path.join(RAW, "01-aller-retour.txt")).read()
hexa = bytes.fromhex("".join(m.group(1) for m in re.finditer(r"^  0[0-9a-f]{2}:  ((?:[0-9a-f]{2} ?)+)", txt, re.M)).replace(" ", ""))
print("\n== 2. Contre l'hexa affiché par `atest -h p1.wav`")
print(f"construit : {len(trame)} octets   atest : {len(hexa)} octets   identique : {'OUI' if trame == hexa else 'NON'}")

# ---------- 3. FCS ----------
def crc_x25(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0x8408 if crc & 1 else crc >> 1
    return crc ^ 0xFFFF

print("\n== 3. FCS : CRC-16/X-25 (poly 0x1021 réfléchi = 0x8408, init 0xFFFF, xorout 0xFFFF)")
print(f"crc_x25(b\"123456789\") = 0x{crc_x25(b'123456789'):04x}   reveng check = 0x906e")
fcs = crc_x25(trame)
print(f"FCS de la trame = 0x{fcs:04x} -> envoyé {fcs & 0xFF:02x} puis {fcs >> 8:02x} (octet faible d'abord)")

# ---------- 4. demodulation of p1.wav ----------
w = wave.open(os.path.join(ICI, "p1.wav"))
fs = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(float)
spb = fs / 1200
n = int(round(spb))
t = np.arange(n) / fs
def energie(f):
    c = np.convolve(x, np.cos(2 * np.pi * f * t)[::-1], "same")
    s = np.convolve(x, np.sin(2 * np.pi * f * t)[::-1], "same")
    return c * c + s * s
ton = (energie(2200) > energie(1200)).astype(int)        # 1 = 2200 Hz (space), 0 = 1200 Hz (mark)
debut = int(np.argmax(np.abs(x) > 100))
# clock: first tone change after the signal starts, then a fixed step of 36.75 samples
k0 = debut + int(np.argmax(np.diff(ton[debut:]) != 0)) + 1
centres = [int(k0 + spb / 2 + i * spb) for i in range(int((len(x) - k0 - spb) // spb))]
tons = [ton[c] for c in centres]
nrzi = [1 if tons[i] == tons[i - 1] else 0 for i in range(1, len(tons))]  # same tone = 1, change = 0
flux = "".join(map(str, nrzi))
print("\n== 4. Démodulation de p1.wav (", fs, "Hz,", f"{spb:.2f} échantillons par bit )")
print(f"tonalités lues : {len(tons)}   bits NRZI : {len(nrzi)}   flags 01111110 : {flux.count('01111110')}")
# last flag of the preamble = start of frame
d = flux.find("01111110")
while flux[d + 8:d + 16] == "01111110":
    d += 8
d += 8
f = flux.find("01111110", d)
brut = flux[d:f]
dest, uns, stuff = [], 0, 0
for b in brut:
    if uns == 5:
        uns = 0
        if b == "0":
            stuff += 1
            continue
    dest.append(b)
    uns = uns + 1 if b == "1" else 0
octets = bytes(int("".join(dest[i:i + 8])[::-1], 2) for i in range(0, len(dest) - len(dest) % 8, 8))
print(f"bits entre flags : {len(brut)}   bits de stuffing retirés : {stuff}   octets : {len(octets)}")
recu, fcs_air = octets[:-2], octets[-2:]
print(f"trame reçue == trame construite : {'OUI' if recu == trame else 'NON'}")
print(f"FCS dans l'air : {fcs_air.hex(' ')}   calculé : {fcs & 0xFF:02x} {fcs >> 8:02x}   {'OK' if fcs_air == bytes([fcs & 0xFF, fcs >> 8]) else 'DIFFÉRENT'}")
print(f"CRC sur trame + FCS reçus : 0x{crc_x25(octets) ^ 0xFFFF:04x}   résidu attendu : 0xf0b8")
ou = [i for i in range(len(brut) - 5) if brut[i:i + 5] == "11111"]
o = (ou[0] + 4) // 8
print(f"bit de stuffing : après cinq 1, bits {ou[0]} à {ou[0] + 4}, dans les octets {trame[o - 1]:02x} {trame[o]:02x} ({trame[o - 1:o + 1]!r})")

# ---------- 5. excerpt for the deck ----------
# end of the last flag + first byte (0x82 = 'A' << 1) + second (0xa0 = 'P' << 1): 24 bits
i0 = d - 8
seg_tons = tons[i0 + 1:i0 + 25]
seg_bits = nrzi[i0:i0 + 24]
a, b = centres[i0 + 1] - n // 2, centres[i0 + 24] + n // 2
# instantaneous frequency from zero crossings (interpolated), smoothed over half a period
z = np.where(np.diff(np.signbit(x[a:b])))[0]
zc = [zi + x[a + zi] / (x[a + zi] - x[a + zi + 1]) for zi in z]
fi = [(round((zc[j] + zc[j + 1]) / 2 / spb, 3), round(fs / (2 * (zc[j + 1] - zc[j])))) for j in range(len(zc) - 1)]
json.dump({"bits": seg_bits, "tons": [2200 if v else 1200 for v in seg_tons], "freq": fi,
           "echantillons": [int(v) for v in x[a:b:3]], "pas": 3, "spb": spb},
          open(os.path.join(ICI, "signal.json"), "w"))
print("\n== 5. Extrait : flag 7e puis 82 a0, 24 bits")
print("bits (NRZI décodé) :", "".join(map(str, seg_bits)))
print("tonalité par bit   :", " ".join("H" if v else "B" for v in seg_tons), " (B = 1200 Hz, H = 2200 Hz)")
print(f"fréquence mesurée  : min {min(v for _, v in fi)} Hz, max {max(v for _, v in fi)} Hz")

# ---------- 6. control byte in connected mode (modulo 8, figures 4.1a and 4.4) ----------
def ctl_i(ns, nr, p=0): return (nr << 5) | (p << 4) | (ns << 1)
def ctl_s(ss, nr, pf=0): return (nr << 5) | (pf << 4) | (ss << 2) | 0b01
def ctl_u(mmm, mm, pf): return (mmm << 5) | (pf << 4) | (mm << 2) | 0b11
print("\n== 6. Octet de contrôle, modulo 8 (bit 0 envoyé en premier)")
for nom, v in [("SABM  P=1", ctl_u(0b001, 0b11, 1)), ("UA    F=1", ctl_u(0b011, 0b00, 1)),
               ("I     N(S)=0 N(R)=0", ctl_i(0, 0)), ("I     N(S)=1 N(R)=0", ctl_i(1, 0)),
               ("I     N(S)=2 N(R)=0", ctl_i(2, 0)), ("I     N(S)=3 N(R)=0", ctl_i(3, 0)),
               ("REJ   N(R)=2", ctl_s(0b10, 2)), ("RNR   N(R)=2", ctl_s(0b01, 2)), ("RR    N(R)=4", ctl_s(0b00, 4)),
               ("DISC  P=1", ctl_u(0b010, 0b00, 1)), ("UI    P=0", ctl_u(0b000, 0b00, 0))]:
    print(f"{nom:22} 0x{v:02x}  {v:08b}")
