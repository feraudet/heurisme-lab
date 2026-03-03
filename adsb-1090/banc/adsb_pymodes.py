"""The same messages decoded by pyModeS, then compared with the hand decoding."""
import pyModeS as pms
from importlib.metadata import version

import adsb_main as H

print(f"pyModeS {version('pyModeS')}")
print()
for m in (H.MSG_ID, H.MSG_EVEN, H.MSG_ODD, H.MSG_VEL):
    print(f"{m}  DF {pms.df(m)}  ICAO {pms.icao(m)}  TC {pms.typecode(m)}  crc {pms.crc(m):06X}")
print(f"callsign  {pms.adsb.callsign(H.MSG_ID)}")
print(f"altitude  {pms.adsb.altitude(H.MSG_EVEN)} ft  {pms.adsb.altitude(H.MSG_ODD)} ft")
pos = pms.adsb.position(H.MSG_EVEN, H.MSG_ODD, H.T_EVEN, H.T_ODD)
print(f"position  {pos}")
print(f"cprNL(52.25720) = {pms.cprNL(52.2572)}")
print(f"velocity  {pms.adsb.velocity(H.MSG_VEL)}")
print()

# agreement with adsb_main.py
fe, late, lone = H.cpr_fields(H.champs(H.MSG_EVEN)["ME"])
fo, lato, lono = H.cpr_fields(H.champs(H.MSG_ODD)["ME"])
lat_h, lon_h = H.position(H.MSG_EVEN, H.MSG_ODD, H.T_EVEN, H.T_ODD)
v = H.vitesse(H.champs(H.MSG_VEL)["ME"])
checks = [
    ("ICAO", H.champs(H.MSG_ID)["ICAO"], pms.icao(H.MSG_ID)),
    ("callsign", H.callsign(H.champs(H.MSG_ID)["ME"]).replace("#", ""), pms.adsb.callsign(H.MSG_ID).replace("_", " ")),
    ("altitude", H.altitude(H.champs(H.MSG_EVEN)["ME"])[3], pms.adsb.altitude(H.MSG_EVEN)),
    ("lat", lat_h, round(pos[0], 5)),
    ("lon", lon_h, round(pos[1], 5)),
    ("speed", round(v[7]), pms.adsb.velocity(H.MSG_VEL)[0]),
    ("track", round(v[8], 2), round(pms.adsb.velocity(H.MSG_VEL)[1], 2)),
    ("vrate", v[10], pms.adsb.velocity(H.MSG_VEL)[2]),
]
for m in (H.MSG_ID, H.MSG_EVEN, H.MSG_ODD, H.MSG_VEL):
    checks.append((f"crc {m[:8]}", H.crc_ok(m), pms.crc(m)))
for nom, a, b in checks:
    print(f"{nom:14s} by hand {str(a):>10s}   pyModeS {str(b):>10s}   {'OK' if str(a).strip() == str(b).strip() else 'DIFF'}")
