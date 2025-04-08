"""Modbus CRC16: init 0xFFFF, reflected polynomial 0xA001, low byte sent first.

python crc.py raw/normal-capture.txt: recomputes the CRC of each captured frame.
"""
import sys


def crc16(data: bytes) -> bytes:
    crc = 0xFFFF
    for octet in data:
        crc ^= octet
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, "little")  # low byte first


if __name__ == "__main__":
    for ligne in open(sys.argv[1], encoding="utf-8"):
        hexa = ligne.split("  ")[-1].split()
        trame = bytes.fromhex("".join(hexa))
        calc, lu = crc16(trame[:-2]), trame[-2:]
        verdict = "OK" if calc == lu else "FAUX"
        print(f"{trame[:-2].hex(' '):<26}  capturé {lu.hex(' ')}  calculé {calc.hex(' ')}  {verdict}")
