"""Builds locally an example ESP-NOW v1.0 frame, following the format
described in the ESP-IDF docs (API Reference > ESP-NOW > Frame Format).
No radio capture: the bytes are assembled by hand."""
import struct, zlib

dst = bytes.fromhex("246f28aabbcc")      # MAC of the recipient (fictitious)
src = bytes.fromhex("246f28112233")      # MAC of the sender (fictitious)
bcast = b"\xff" * 6                      # 3rd address: broadcast, according to the docs

fc = struct.pack("<H", 0x00D0)           # type management, subtype action (13), ToDS=FromDS=0
duration = b"\x00\x00"
seq = struct.pack("<H", 0x0010)
mac_header = fc + duration + dst + src + bcast + seq          # 24 bytes

category = b"\x7f"                        # 127 : vendor-specific
oui = bytes.fromhex("18fe34")             # OUI Espressif
rand = bytes.fromhex("5a3c9e01")          # 4 random bytes (anti-replay)

body = b"temp=21.5"
element = b"\xdd"                         # Element ID 221
etype = b"\x04"                           # Type 4 = ESP-NOW
version = b"\x01"                         # bits 3..0 = version (assumption: 1 for v1.0)
length = bytes([len(oui) + 1 + 1 + len(body)])
vendor = element + length + oui + etype + version + body

frame = mac_header + category + oui + rand + vendor
fcs = struct.pack("<I", zlib.crc32(frame) & 0xFFFFFFFF)

parts = [("MAC header", mac_header), ("Category", category), ("OUI", oui),
         ("Random", rand), ("Elem ID", element), ("Length", length), ("OUI", oui),
         ("Type", etype), ("Version", version), ("Body", body), ("FCS", fcs)]
for name, b in parts:
    print(f"{name:11s} {len(b):3d}  {b.hex(' ')}")
print("total", len(frame + fcs), "octets pour", len(body), "octets utiles")
