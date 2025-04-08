"""Minimal RTU slave that enforces t1.5 and t3.5 (Modbus over Serial Line V1.02, 2.5.1.1).

19200 baud: above 19200 the spec fixes t1.5 = 750 us and t3.5 = 1.75 ms; at 19200 we
compute 11 bits / 19200 = 573 us per character, so t1.5 = 859 us and t3.5 = 2005 us.
On a pty, the bytes of a single write() arrive together: we only measure the silences
between packets, not the bit time of each byte.
"""
import os
import select
import sys
import time

from crc import crc16

BAUD = int(os.environ.get("BAUD", "19200"))
T_CHAR = 11 / BAUD
T15, T35 = 1.5 * T_CHAR, 3.5 * T_CHAR
REGS = {0x6B: 0x022B, 0x6C: 0x0000, 0x6D: 0x0064}
fd = os.open(sys.argv[1], os.O_RDWR | os.O_NOCTTY)
print(f"{BAUD} bauds : t1.5 = {T15 * 1e6:.0f} us, t3.5 = {T35 * 1e6:.0f} us", flush=True)

while True:
    select.select([fd], [], [])
    trame, trous, last = b"", [], None
    while True:
        r, _, _ = select.select([fd], [], [], T35)
        if not r:
            break  # silence >= t3.5: end of frame
        now = time.monotonic()
        if last is not None:
            trous.append(now - last)
        trame += os.read(fd, 256)
        last = time.monotonic()
    pire = max(trous, default=0)
    crc_ok = len(trame) >= 4 and crc16(trame[:-2]) == trame[-2:]
    etat = []
    if pire > T15:
        etat.append(f"trou de {pire * 1e6:.0f} us > t1.5 : trame incomplète, rejetée")
    if not crc_ok:
        etat.append("CRC faux : rejetée")
    print(f"reçu {len(trame)} octets : {trame.hex(' ')}", flush=True)
    if etat:
        print("  " + " ; ".join(etat), " -> pas de réponse", flush=True)
        continue
    if trame[0] != 0x11 or trame[1] != 0x03:
        print("  pas pour moi -> pas de réponse", flush=True)
        continue
    adr, n = int.from_bytes(trame[2:4], "big"), int.from_bytes(trame[4:6], "big")
    if all(a in REGS for a in range(adr, adr + n)):
        pdu = bytes([0x11, 0x03, 2 * n]) + b"".join(REGS[a].to_bytes(2, "big") for a in range(adr, adr + n))
    else:
        pdu = bytes([0x11, 0x83, 0x02])
    rep = pdu + crc16(pdu)
    print(f"  trame valide -> réponse {rep.hex(' ')}", flush=True)
    os.write(fd, rep)
