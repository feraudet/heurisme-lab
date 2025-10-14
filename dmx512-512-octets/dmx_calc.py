#!/usr/bin/env python3
"""DMX512: timing calculations, example frame, Art-Net and sACN packets.

No hardware: everything is computed or built in memory, then sent
only to 127.0.0.1 to be read back by a local socket and decoded
by a home-made dissector (tshark is not installed).

Sources of the values:
  - ANSI E1.11-2004, tables 6 et 7 (tsp.esta.org/tsp/documents/docs/E1-11.pdf)
  - Art-Net 4, rev. 1.4dp, ArtDmx (art-net.org.uk/downloads/art-net.pdf)
  - ANSI E1.31-2016, table 1 (tsp.esta.org/tsp/documents/docs/E1-31-2016.pdf)
  - ENTTEC DMX USB Pro API v1.44, label 6
"""
import socket
import struct
import uuid

BIT_US = 4.0                  # 250 kbit/s
SLOT_BITS = 1 + 8 + 2         # start bit + 8 data + 2 stop bits
SLOT_US = SLOT_BITS * BIT_US  # 44 µs
TX = {"break": 92, "mab": 12}  # E1.11 table 6, transmitter minimums
RX = {"break": 88, "mab": 8}   # E1.11 table 7, receiver minimums
BREAK_TO_BREAK_MIN_TX = 1204   # µs, table 6 designator 11/13


def trame_us(n_slots, t):
    """BREAK + MAB + (start code + n slots) * 44 µs, with no idle time."""
    return t["break"] + t["mab"] + (1 + n_slots) * SLOT_US


def section(titre):
    print("\n" + "=" * 70 + "\n" + titre + "\n" + "=" * 70)


def hexdump(data, largeur=16):
    for off in range(0, len(data), largeur):
        bloc = data[off:off + largeur]
        print(f"  {off:04x}  " + " ".join(f"{b:02x}" for b in bloc))


# ---------------------------------------------------------------- 1. timing
section("1. Durée de trame et rafraîchissement max (calculé)")
print(f"slot = {SLOT_BITS} bits x {BIT_US:g} µs = {SLOT_US:g} µs")
for nom, t in (("émetteur E1.11 (92/12)", TX), ("récepteur E1.11 (88/8)", RX)):
    print(f"\n{nom}")
    for n in (512, 128, 24, 18):
        us = trame_us(n, t)
        hz = 1e6 / max(us, BREAK_TO_BREAK_MIN_TX) if t is TX else 1e6 / us
        note = ""
        if t is TX and us < BREAK_TO_BREAK_MIN_TX:
            note = f"  < {BREAK_TO_BREAK_MIN_TX} µs : bourrer à 24 slots ou allonger"
        print(f"  {n:3d} slots : {us:8.0f} µs  -> {1e6 / us:7.1f} Hz brut, "
              f"{hz:6.1f} Hz conforme{note}")

# ---------------------------------------------------------- 2. frame + patch
section("2. Patch de 3 fixtures et trame DMX (construit en local)")
PATCH = [
    # (name, start address, [(channel, value)])
    ("PAR LED 7 canaux", 1, [("dimmer", 255), ("rouge", 255), ("vert", 64),
                             ("bleu", 0), ("strobe", 0), ("programme", 0), ("vitesse", 0)]),
    ("PAR LED 3 canaux RGB", 8, [("rouge", 0), ("vert", 80), ("bleu", 255)]),
    ("Lyre 8 canaux 16 bits", 11, None),  # filled in below
]
pan, tilt = 0x8A3C, 0x4000
PATCH[2] = (PATCH[2][0], 11, [("pan", pan >> 8), ("pan fine", pan & 0xFF),
                              ("tilt", tilt >> 8), ("tilt fine", tilt & 0xFF),
                              ("dimmer", 200), ("shutter", 255), ("couleur", 0), ("gobo", 0)])
N_SLOTS = 24  # 18 useful, padded to 24 to respect 1204 µs break-to-break
slots = bytearray(N_SLOTS)
for nom, adr, canaux in PATCH:
    fin = adr + len(canaux) - 1
    print(f"{nom:24s} adresse {adr:3d} -> slots {adr}..{fin}")
    for k, (c, v) in enumerate(canaux):
        slots[adr - 1 + k] = v
        print(f"    slot {adr + k:3d}  {c:10s} = {v:3d} (0x{v:02x})")
print(f"\npan 16 bits = 0x{pan:04x} = {pan}  -> coarse {pan >> 8}, fine {pan & 0xFF}")
print(f"résolution pan : 1/{2**16} du débattement (8 bits : 1/256)")
trame = bytes([0x00]) + bytes(slots)
print(f"\ntrame : start code 0x00 + {N_SLOTS} slots = {len(trame)} octets sur le fil")
print("(précédée d'un BREAK >= 92 µs et d'un MAB >= 12 µs, qui ne sont pas des octets)")
hexdump(trame)
print(f"durée : {trame_us(N_SLOTS, TX):.0f} µs (émetteur, minimums)")

# ---------------------------------------------------------------- 3. Art-Net
section("3. Paquet ArtDmx (construit en local)")
PORT_ADDRESS = 1  # Net 0, Sub-Net 0, Universe 1 (Port-Address 0 is deprecated)
artdmx = (b"Art-Net\x00" + struct.pack("<H", 0x5000) + bytes([0, 14])
          + bytes([1, 0]) + struct.pack("<H", PORT_ADDRESS)
          + struct.pack(">H", len(slots)) + bytes(slots))
print(f"{len(artdmx)} octets = 18 d'en-tête + {len(slots)} de données (sans start code)")
hexdump(artdmx)

# ------------------------------------------------------------------- 4. sACN
section("4. Paquet sACN E1.31 Data (construit en local)")
UNIVERSE = 1
CID = uuid.UUID("5a1b0c1d-2e3f-4051-8263-748596a7b8c9").bytes  # fixed for reproducibility
props = bytes([0x00]) + bytes(slots)  # start code + slots
total = 126 + len(slots)


def fl(n):
    return struct.pack(">H", 0x7000 | n)


name = b"deck-dmx".ljust(64, b"\x00")
sacn = (struct.pack(">HH", 0x0010, 0x0000) + b"ASC-E1.17\x00\x00\x00"
        + fl(total - 16) + struct.pack(">I", 0x00000004) + CID
        + fl(total - 38) + struct.pack(">I", 0x00000002) + name
        + bytes([100]) + struct.pack(">H", 0) + bytes([1]) + bytes([0])
        + struct.pack(">H", UNIVERSE)
        + fl(total - 115) + bytes([0x02, 0xA1]) + struct.pack(">HHH", 0, 1, len(props))
        + props)
assert len(sacn) == total
mcast = f"239.255.{UNIVERSE >> 8}.{UNIVERSE & 0xFF}"
print(f"{len(sacn)} octets = 126 d'en-tête + {len(slots)} slots ; multicast {mcast}:5568")
hexdump(sacn)

# -------------------------------------------------------------- 5. ENTTEC Pro
section("5. Message ENTTEC DMX USB Pro, label 6 (construit en local)")
pro = bytes([0x7E, 0x06]) + struct.pack("<H", len(trame)) + trame + bytes([0xE7])
print(f"{len(pro)} octets : 0x7E, label 6, longueur {len(trame)} (LSB, MSB), trame, 0xE7")
hexdump(pro)


# ------------------------------------------------------ 6. local round trip
def recevoir(paquet, port):
    rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    rx.bind(("127.0.0.1", port))
    rx.settimeout(2)
    tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tx.sendto(paquet, ("127.0.0.1", port))
    data, _ = rx.recvfrom(2048)
    rx.close()
    tx.close()
    return data


def dissect_artnet(p):
    assert p[:8] == b"Art-Net\x00", "pas un paquet Art-Net"
    op, = struct.unpack_from("<H", p, 8)
    pa, = struct.unpack_from("<H", p, 14)
    ln, = struct.unpack_from(">H", p, 16)
    print(f"  ID         : {p[:7].decode()}")
    print(f"  OpCode     : 0x{op:04x} (OpDmx), little endian")
    print(f"  ProtVer    : {p[10]}.{p[11]}")
    print(f"  Sequence   : {p[12]}   Physical : {p[13]}")
    print(f"  Port-Addr  : {pa} = Net {pa >> 8 & 0x7F}, Sub-Net {pa >> 4 & 0xF}, Universe {pa & 0xF}")
    print(f"  Length     : {ln} (big endian)")
    print(f"  Data[0:18] : {' '.join(str(b) for b in p[18:36])}")


def dissect_sacn(p):
    assert p[4:16] == b"ASC-E1.17\x00\x00\x00", "pas un paquet ACN"
    v_root, = struct.unpack_from(">I", p, 18)
    v_fr, = struct.unpack_from(">I", p, 40)
    uni, = struct.unpack_from(">H", p, 113)
    cnt, = struct.unpack_from(">H", p, 123)
    print(f"  Root       : preamble 0x{struct.unpack_from('>H', p, 0)[0]:04x}, "
          f"vector 0x{v_root:08x} (E1.31 data), CID {uuid.UUID(bytes=p[22:38])}")
    print(f"  Framing    : vector 0x{v_fr:08x}, source '{p[44:108].rstrip(bytes(1)).decode()}'")
    print(f"  Priority   : {p[108]}   Sync addr : {struct.unpack_from('>H', p, 109)[0]}   "
          f"Seq : {p[111]}   Options : 0x{p[112]:02x}")
    print(f"  Universe   : {uni} -> 239.255.{uni >> 8}.{uni & 0xFF}")
    print(f"  DMP        : vector 0x{p[117]:02x}, type 0x{p[118]:02x}, count {cnt} "
          f"(start code + {cnt - 1} slots)")
    print(f"  Start code : 0x{p[125]:02x}   Slots[1:18] : {' '.join(str(b) for b in p[126:144])}")


section("6. Aller-retour UDP sur 127.0.0.1 et décodage (dissecteur maison)")
r = recevoir(artdmx, 6454)
print(f"Art-Net reçu sur 127.0.0.1:6454, {len(r)} octets, identique : {r == artdmx}")
dissect_artnet(r)
r = recevoir(sacn, 5568)
print(f"\nsACN reçu sur 127.0.0.1:5568, {len(r)} octets, identique : {r == sacn}")
dissect_sacn(r)
print("\nMême univers, mêmes 24 slots : "
      f"{r[126:150] == artdmx[18:42] == trame[1:]}")
