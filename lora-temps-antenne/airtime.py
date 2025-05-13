#!/usr/bin/env python3
"""LoRa airtime, SX1276 datasheet Rev. 7 formula, section 4.1.1.7.

Assumptions (LoRaWAN uplink EU868): BW 125 kHz, 8-symbol preamble,
explicit header (IH=0), CRC present, CR 4/5, LowDataRateOptimize
when the symbol lasts more than 16 ms.
"""
import math

BW = 125_000
NPREAMBLE = 8
CR = 1          # 1 = 4/5
CRC = 1
IH = 0
DUTY = 0.01     # 1%: sub-band M, 868.0 to 868.6 MHz (ETSI EN 300 220-2)
TOBS_S = 3600   # Tobs = 1 hour (ETSI EN 300 220-1, 5.4.1)
FUP_S = 30      # TTN Fair Use Policy: 30 s of uplink per day
LORAWAN_OVERHEAD = 13  # MHDR 1 + DevAddr 4 + FCtrl 1 + FCnt 2 + FPort 1 + MIC 4


def toa(pl, sf, bw=BW, npre=NPREAMBLE, cr=CR, crc=CRC, ih=IH, de=None):
    tsym = 2 ** sf / bw
    if de is None:
        de = 1 if tsym > 0.016 else 0
    tpre = (npre + 4.25) * tsym
    num = 8 * pl - 4 * sf + 28 + 16 * crc - 20 * ih
    nb = 8 + max(math.ceil(num / (4 * (sf - 2 * de))) * (cr + 4), 0)
    return tsym, de, tpre, nb, nb * tsym, tpre + nb * tsym


def table(pl, titre):
    print(f"== {titre} : PL = {pl} octets, BW 125 kHz, CR 4/5, préambule 8, en-tête explicite, CRC ==")
    print(f"{'SF':>4} {'DR':>3} {'Ts ms':>7} {'LDRO':>4} {'Tpre ms':>8} {'Nsym':>4} {'Tpay ms':>8} {'ToA ms':>8} {'attente s':>9} {'msg/h':>5} {'msg/j FUP':>9}")
    for sf in range(7, 13):
        tsym, de, tpre, nb, tpay, t = toa(pl, sf)
        attente = t / DUTY - t
        par_h = math.floor(DUTY * TOBS_S / t)
        par_j = math.floor(FUP_S / t)
        print(f"{'SF'+str(sf):>4} {12-sf:>3} {tsym*1e3:7.3f} {de:>4} {tpre*1e3:8.3f} {nb:>4} {tpay*1e3:8.3f} {t*1e3:8.3f} {attente:9.1f} {par_h:>5} {par_j:>9}")
    print()


print("SX1276 Rev. 7, 4.1.1.7 : Ts = 2^SF/BW ; Tpre = (npre + 4,25) Ts ;")
print("Npayload = 8 + max(ceil((8PL - 4SF + 28 + 16CRC - 20IH) / (4(SF - 2DE))) (CR + 4), 0)")
print("attente = ToA / 1 % - ToA ; msg/h = floor(36 s / ToA) ; msg/j FUP = floor(30 s / ToA)")
print()
table(20, "20 octets de payload radio")
table(20 + LORAWAN_OVERHEAD, "20 octets applicatifs en LoRaWAN (+13 octets d'en-tête et MIC)")

print("== Contrôle contre les tests du calculateur TTN (avbentem/airtime-calculator, src/lora/Airtime.test.ts) ==")
attendus = [(14, 7, 46.336), (16, 7, 51.456), (25, 7, 61.696), (14, 8, 82.432),
            (25, 8, 113.152), (14, 11, 659.456), (25, 11, 823.296)]
for size, sf, ms in attendus:
    t = toa(size, sf)[-1] * 1e3
    ok = "OK" if abs(t - ms) < 0.005 else "ÉCART"
    print(f"size={size:>2} SF{sf:<2} BW125  publié {ms:8.3f} ms  calculé {t:8.3f} ms  {ok}")
print()
r = toa(20, 12)[-1] / toa(20, 7)[-1]
print(f"rapport ToA SF12 / SF7 pour 20 octets : {r:.1f}")
print(f"budget 1 % sur 24 h : {DUTY * TOBS_S * 24:.0f} s ; Fair Use Policy TTN : {FUP_S} s")
