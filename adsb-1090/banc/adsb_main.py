"""Hand decoding of ADS-B (DF17), without pyModeS: fields, CRC, callsign,
altitude, global CPR position and speed. Standard library only.

Usage: python3 adsb_main.py
"""
import math
import sys

# Public messages taken from "The 1090 Megahertz Riddle" (Junzi Sun), https://mode-s.org/decode/
MSG_ID = "8D4840D6202CC371C32CE0576098"
MSG_EVEN = "8D40621D58C382D690C8AC2863A7"
MSG_ODD = "8D40621D58C386435CC412692AD6"
T_EVEN, T_ODD = 1457996402, 1457996400   # the book's example: the even frame is the newest
MSG_VEL = "8D485020994409940838175B284F"

GEN = 0x1FFF409          # Mode S generator polynomial, 25 bits (24 parity bits)
CHARSET = "#ABCDEFGHIJKLMNOPQRSTUVWXYZ##### ###############0123456789######"
NZ = 15


def bits(hexmsg):
    return bin(int(hexmsg, 16))[2:].zfill(len(hexmsg) * 4)


def crc_remainder(hexmsg):
    """Remainder of dividing the first 88 bits (followed by 24 zeros) by GEN."""
    b = bits(hexmsg)
    n = int(b[:88], 2) << 24
    for i in range(111, 23, -1):
        if n >> i & 1:
            n ^= GEN << (i - 24)
    return n


def crc_ok(hexmsg):
    """Division of the full 112 bits: zero remainder if the message is intact."""
    n = int(hexmsg, 16)
    for i in range(111, 23, -1):
        if n >> i & 1:
            n ^= GEN << (i - 24)
    return n


def champs(hexmsg):
    b = bits(hexmsg)
    return {"DF": int(b[0:5], 2), "CA": int(b[5:8], 2), "ICAO": hexmsg[2:8].upper(),
            "ME": b[32:88], "TC": int(b[32:37], 2), "PI": int(b[88:112], 2)}


def callsign(me):
    return "".join(CHARSET[int(me[8 + 6 * k:14 + 6 * k], 2)] for k in range(8))


def altitude(me):
    a = me[8:20]
    q = a[7]
    n = int(a[:7] + a[8:], 2)
    return a, q, n, 25 * n - 1000


def nl(lat):
    if lat == 0:
        return 59
    if abs(lat) == 87:
        return 2
    if abs(lat) > 87:
        return 1
    a = 1 - math.cos(math.pi / (2 * NZ))
    b = math.cos(math.pi / 180 * abs(lat)) ** 2
    return math.floor(2 * math.pi / math.acos(1 - a / b))


def cpr_fields(me):
    return int(me[21], 2), int(me[22:39], 2), int(me[39:56], 2)


def position(m_even, m_odd, t_even, t_odd):
    """Global CPR, compact version of the step by step in main()."""
    _, a, b = cpr_fields(champs(m_even)["ME"])
    _, c, d = cpr_fields(champs(m_odd)["ME"])
    le, lo, oe, oo = a / 131072, c / 131072, b / 131072, d / 131072
    j = math.floor(59 * le - 60 * lo + 0.5)
    lat_e = 6 * (j % 60 + le)
    lat_o = 360 / 59 * (j % 59 + lo)
    lat_e -= 360 if lat_e >= 270 else 0
    lat_o -= 360 if lat_o >= 270 else 0
    if nl(lat_e) != nl(lat_o):
        return None
    if t_even >= t_odd:
        lat, n, lc = lat_e, nl(lat_e), oe
        mm = math.floor(oe * (n - 1) - oo * n + 0.5)
        ni = max(n, 1)
    else:
        lat, n, lc = lat_o, nl(lat_o), oo
        mm = math.floor(oe * (n - 1) - oo * n + 0.5)
        ni = max(n - 1, 1)
    lon = 360 / ni * (mm % ni + lc)
    lon -= 360 if lon >= 180 else 0
    return round(lat, 5), round(lon, 5)


def vitesse(me):
    st = int(me[5:8], 2)
    sew, vew = int(me[13]), int(me[14:24], 2) - 1
    sns, vns = int(me[24]), int(me[25:35], 2) - 1
    vx = -vew if sew else vew
    vy = -vns if sns else vns
    gs = math.hypot(vx, vy)
    trk = math.degrees(math.atan2(vx, vy)) % 360
    svr, vr = int(me[36]), int(me[37:46], 2)
    vrate = (-1 if svr else 1) * (vr - 1) * 64
    return st, sew, vew, sns, vns, vx, vy, gs, trk, int(me[35]), vrate


def main():
    print(f"Python {sys.version.split()[0]}  (standard library only)")
    print()
    m = MSG_ID
    f = champs(m)
    b = bits(m)
    print(f"== 1. Fields of {m}  ({len(b)} bits)")
    print(f"DF   bits 1-5     {b[0:5]}  = {f['DF']}")
    print(f"CA   bits 6-8     {b[5:8]}  = {f['CA']}")
    print(f"ICAO bits 9-32    {b[8:32]}  = {f['ICAO']}")
    print(f"TC   bits 33-37   {b[32:37]}  = {f['TC']}")
    print(f"ME   bits 33-88   {int(f['ME'], 2):014X}")
    print(f"PI   bits 89-112  {f['PI']:06X}")
    print()
    print("== 2. CRC-24, generator 0x1FFF409")
    for x in (MSG_ID, MSG_EVEN, MSG_ODD, MSG_VEL):
        r = crc_remainder(x)
        print(f"{x}  computed {r:06X}  sent {champs(x)['PI']:06X}  112-bit remainder {crc_ok(x):06X}")
    bad = f"{int(MSG_ID, 16) ^ (1 << 60):028X}"
    print(f"{bad}  one bit flipped  112-bit remainder {crc_ok(bad):06X}")
    print()
    print("== 3. Identification (TC 1-4), 8 characters of 6 bits")
    me = f["ME"]
    for k in range(8):
        s = me[8 + 6 * k:14 + 6 * k]
        print(f"  {s} = {int(s, 2):2d} -> '{CHARSET[int(s, 2)]}'")
    print(f"callsign = {callsign(me)}")
    print()
    print("== 4. Altitude (TC 9-18), 12 bits, Q bit")
    for x, t in ((MSG_EVEN, T_EVEN), (MSG_ODD, T_ODD)):
        a, q, n, alt = altitude(champs(x)["ME"])
        print(f"{x}  TC {champs(x)['TC']}  bits {a}  Q={q}  N={n}  25*N-1000 = {alt} ft")
    print()
    print("== 5. CPR global decoding, NZ = 15")
    fe, late, lone = cpr_fields(champs(MSG_EVEN)["ME"])
    fo, lato, lono = cpr_fields(champs(MSG_ODD)["ME"])
    print(f"even  F={fe}  LAT-CPR={late}  LON-CPR={lone}  t={T_EVEN}")
    print(f"odd   F={fo}  LAT-CPR={lato}  LON-CPR={lono}  t={T_ODD}")
    le, lo = late / 131072, lato / 131072
    oe, oo = lone / 131072, lono / 131072
    print(f"/2^17 : lat_e={le:.6f}  lat_o={lo:.6f}  lon_e={oe:.6f}  lon_o={oo:.6f}")
    dle, dlo = 360 / (4 * NZ), 360 / (4 * NZ - 1)
    print(f"dLat_e = 360/60 = {dle:.6f}   dLat_o = 360/59 = {dlo:.6f}")
    j = math.floor(59 * le - 60 * lo + 0.5)
    print(f"j = floor(59*lat_e - 60*lat_o + 0.5) = floor({59 * le - 60 * lo + 0.5:.6f}) = {j}")
    lat_e = dle * (j % 60 + le)
    lat_o = dlo * (j % 59 + lo)
    if lat_e >= 270:
        lat_e -= 360
    if lat_o >= 270:
        lat_o -= 360
    print(f"lat_even = 6 * ({j % 60} + {le:.6f}) = {lat_e:.6f}")
    print(f"lat_odd  = 360/59 * ({j % 59} + {lo:.6f}) = {lat_o:.6f}")
    print(f"NL(lat_even) = {nl(lat_e)}   NL(lat_odd) = {nl(lat_o)}   same zone: {nl(lat_e) == nl(lat_o)}")
    lat = lat_e if T_EVEN >= T_ODD else lat_o
    n = nl(lat)
    ni = max(n, 1)
    mm = math.floor(oe * (n - 1) - oo * n + 0.5)
    lon = 360 / ni * (mm % ni + oe)
    if lon >= 180:
        lon -= 360
    print(f"newest = even -> lat = {lat:.5f}, ni = max(NL, 1) = {ni}")
    print(f"m = floor(lon_e*(NL-1) - lon_o*NL + 0.5) = floor({oe * (n - 1) - oo * n + 0.5:.6f}) = {mm}")
    print(f"lon = 360/{ni} * ({mm % ni} + {oe:.6f}) = {lon:.5f}")
    print(f"position = {lat:.5f}, {lon:.5f}")
    print()
    print("== 6. Airborne velocity (TC 19)")
    v = champs(MSG_VEL)
    st, sew, vew, sns, vns, vx, vy, gs, trk, src, vrate = vitesse(v["ME"])
    print(f"{MSG_VEL}  ICAO {v['ICAO']}  TC {v['TC']}  subtype {st}")
    print(f"S_ew={sew} V_ew={vew}  S_ns={sns} V_ns={vns}  -> vx={vx} vy={vy} kt")
    print(f"ground speed = sqrt(vx^2 + vy^2) = {gs:.2f} kt   track = {trk:.2f} deg")
    print(f"vertical rate = {vrate} ft/min (source bit {src})")


if __name__ == "__main__":
    # No argument: everything. With numbers (e.g. "3 4"): only those sections.
    if len(sys.argv) == 1:
        main()
    else:
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            main()
        blocs = buf.getvalue().strip("\n").split("\n\n")
        voulus = [b for b in blocs if b.startswith("== ") and b[3:].split(".")[0] in sys.argv[1:]]
        print("\n\n".join(voulus))
