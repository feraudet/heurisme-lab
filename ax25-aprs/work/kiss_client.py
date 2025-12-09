#!/usr/bin/env python3
"""Minimal KISS TCP client: connects to direwolf (port 8001), reads for N seconds,
prints the bytes received as they are, then the AX.25 frame after unescaping."""
import socket, sys, time

port, duree = 8001, float(sys.argv[1]) if len(sys.argv) > 1 else 6
for _ in range(50):
    try:
        s = socket.create_connection(("127.0.0.1", port)); break
    except OSError:
        time.sleep(0.1)
s.settimeout(0.2)
brut = b""
fin = time.time() + duree
while time.time() < fin:
    try:
        d = s.recv(4096)
        if not d: break
        brut += d
    except socket.timeout:
        pass
print(f"octets reçus sur TCP {port} : {len(brut)}")
print(brut.hex(" "))
# split on FEND (C0), unescape FESC TFEND -> C0, FESC TFESC -> DB
for bloc in brut.split(b"\xc0"):
    if not bloc: continue
    out, esc = bytearray(), False
    for b in bloc:
        if esc: out.append({0xDC: 0xC0, 0xDD: 0xDB}.get(b, b)); esc = False
        elif b == 0xDB: esc = True
        else: out.append(b)
    print(f"type 0x{out[0]:02x} (port {out[0] >> 4}, commande {out[0] & 15} = data frame), trame AX.25 : {len(out) - 1} octets, sans FCS")
