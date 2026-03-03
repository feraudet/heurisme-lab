"""Why the even/odd pair must be recent: same aircraft, two pairs.
Local decoding (with a reference position) of each message to check."""
import pyModeS as pms

import adsb_main as H

BONNE = ("8D4D20235873E0B5E99AA7481C68", "8D4D20235873F44C9F86FDABDEF4")   # 22150 / 22175 ft
MAUVAISE = ("8F4D20235877B0BC01996FF7B3F2", "8F4D2023587F345E35837E2218B2")  # 22875 / 24275 ft

for nom, (e, o) in (("close pair", BONNE), ("far pair", MAUVAISE)):
    alt_e, alt_o = pms.adsb.altitude(e), pms.adsb.altitude(o)
    dt = abs(alt_e - alt_o) / 1920 * 60
    print(f"{nom}: altitudes {alt_e} / {alt_o} ft -> about {dt:.0f} s apart at 1920 ft/min")
    print(f"  global (even newest) by hand {H.position(e, o, 1, 0)}   pyModeS {pms.adsb.position(e, o, 1, 0)}")
ref = H.position(*BONNE, 1, 0)
print(f"reference = close pair = {ref}")
for m in MAUVAISE + BONNE:
    print(f"  local {m}  F={pms.adsb.oe_flag(m)}  {pms.adsb.altitude(m)} ft  ->  {pms.adsb.position_with_ref(m, *ref)}")
