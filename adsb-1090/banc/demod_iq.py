"""PPM demodulation of a real IQ recording (testfiles/modes1.bin from the
antirez/dump1090 repo): unsigned 8 bits, I then Q, 2 million samples per second.
One bit = 1 µs = 2 samples. No error correction: a message is kept
only if its CRC is good.

Usage: python3 demod_iq.py [--court] modes1.bin [extrait.json]
--court: stops after the first 6 messages (what the deck shows)
"""
import json
import sys
from collections import Counter

import numpy as np
import pyModeS as pms

import adsb_main as H

FS = 2_000_000
COURT = "--court" in sys.argv
if COURT:
    sys.argv.remove("--court")
path = sys.argv[1]
raw = np.fromfile(path, dtype=np.uint8).astype(np.float32) - 127.5
mag = np.hypot(raw[0::2], raw[1::2])
print(f"file {path.rsplit('/', 1)[-1]}: {raw.size} bytes = {mag.size} IQ samples = {mag.size / FS * 1000:.1f} ms at 2 MS/s")
print(f"noise floor (median magnitude) {np.median(mag):.1f}   max {mag.max():.1f}")


def preambule(m, i):
    """Pulses at 0; 1; 3.5; 4.5 µs = samples 0, 2, 7, 9."""
    p = m[i:i + 16]
    hauts = min(p[0], p[2], p[7], p[9])
    bas = max(p[1], p[3], p[4], p[5], p[6], p[8], p[10:16].max())
    return hauts > 2 * bas and hauts > 3 * np.median(m)


def bits_ppm(m, i, n=112):
    d = m[i + 16:i + 16 + 2 * n]
    return "".join("1" if d[2 * k] > d[2 * k + 1] else "0" for k in range(n))


trouves, cand, i = [], 0, 0
while i < mag.size - 16 - 224:
    if preambule(mag, i):
        cand += 1
        b = bits_ppm(mag, i)
        df = int(b[:5], 2)
        n = 112 if df >= 16 else 56
        hx = f"{int(b[:n], 2):0{n // 4}X}"
        if df == 17 and H.crc_ok(hx) == 0:
            trouves.append((i, hx))
            i += 16 + 224
            continue
    i += 1

print(f"preamble candidates {cand}   DF17 with CRC = 0: {len(trouves)}")
c = Counter(h for _, h in trouves)
print(f"distinct DF17 messages {len(c)}   aircraft (ICAO) {sorted(set(h[2:8] for h in c))}")
print()
for k, (pos, hx) in enumerate(trouves):
    if COURT and k == 6:
        sys.exit(0)
    tc = pms.typecode(hx)
    if 1 <= tc <= 4:
        info = f"callsign {pms.adsb.callsign(hx)}"
    elif 9 <= tc <= 18:
        info = f"alt {pms.adsb.altitude(hx)} ft  F={pms.adsb.oe_flag(hx)}"
    elif tc == 19:
        info = f"velocity {pms.adsb.velocity(hx)}"
    else:
        info = ""
    print(f"t={pos / FS * 1000:7.3f} ms  {hx}  ICAO {hx[2:8]}  TC {tc:2d}  {info}")

# first even/odd pair of the same aircraft: global position, by hand and with pyModeS
print()
vus = {}
for pos, hx in trouves:
    tc = pms.typecode(hx)
    if not 9 <= tc <= 18:
        continue
    f = pms.adsb.oe_flag(hx)
    autre = vus.get((hx[2:8], 1 - f))
    if autre:
        (p0, h0) = autre if f == 1 else (pos, hx)
        (p1, h1) = (pos, hx) if f == 1 else autre
        t0, t1 = p0 / FS, p1 / FS
        print(f"pair even {h0} (t={t0 * 1000:.3f} ms)  odd {h1} (t={t1 * 1000:.3f} ms)")
        print(f"  by hand  {H.position(h0, h1, t0, t1)}")
        print(f"  pyModeS  {pms.adsb.position(h0, h1, t0, t1)}")
        print(f"  altitudes {pms.adsb.altitude(h0)} / {pms.adsb.altitude(h1)} ft")
        break
    vus[(hx[2:8], f)] = (pos, hx)

# The file is spliced together: the altitude drops by 4250 ft in 176 ms. The times
# in the file are therefore not real time. We take instead the neighbouring pair whose
# altitudes are closest (25 ft: under one second at -1920 ft/min).
print()
alt = [(pos, hx, pms.adsb.altitude(hx), pms.adsb.oe_flag(hx)) for pos, hx in trouves if 9 <= pms.typecode(hx) <= 18]
print(f"altitude in file: first {alt[0][2]} ft at {alt[0][0] / FS * 1000:.3f} ms, last {alt[-1][2]} ft at {alt[-1][0] / FS * 1000:.3f} ms")
best = min(((a, b) for a, b in zip(alt, alt[1:]) if a[3] != b[3]), key=lambda p: abs(p[0][2] - p[1][2]))
(pa, ha, aa, fa), (pb, hb, ab, fb) = best
h0, h1 = (ha, hb) if fa == 0 else (hb, ha)
t0, t1 = (pa, pb) if fa == 0 else (pb, pa)
print(f"closest pair: even {h0} odd {h1}, altitudes {aa} / {ab} ft")
print(f"  by hand  {H.position(h0, h1, t0, t1)}")
print(f"  pyModeS  {pms.adsb.position(h0, h1, t0 / FS, t1 / FS)}")

if len(sys.argv) > 2 and trouves:
    pos, hx = trouves[0]
    ext = mag[pos - 4:pos + 16 + 2 * 112 + 4]
    json.dump({"hex": hx, "debut": 4, "mag": [round(float(v), 1) for v in ext],
               "bits": H.bits(hx)}, open(sys.argv[2], "w"))
    print(f"\nexcerpt written: {hx}, {len(ext)} samples from t={(pos - 4) / FS * 1000:.4f} ms")
