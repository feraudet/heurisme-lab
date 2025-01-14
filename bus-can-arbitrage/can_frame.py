#!/usr/bin/env python3
"""Classic CAN frame (base frame, 11 bits) built bit by bit.

Section 1: CRC-15/CAN, checked against the check value of the reveng catalogue.
Section 2: full frame, checked bit by bit against the frame captured by Ken Tindell
           (ID 0x014, data 0x01, CRC 0x7753).
Section 3: arbitration of three nodes, wired-AND bus, bit stuffing included.
Section 4: TEC error counters following the fault confinement rules (Bosch CAN 2.0 part A, ch. 5).
"""
import sys

POLY = 0x4599  # x15 + x14 + x10 + x8 + x7 + x4 + x3 + 1


def crc15(bits):
    """Algorithm of the Bosch spec (3.2.1.5): 15-bit shift register."""
    crc = 0
    for b in bits:
        nxt = b ^ ((crc >> 14) & 1)
        crc = (crc << 1) & 0x7FFF
        if nxt:
            crc ^= POLY
    return crc


def to_bits(v, n):
    return [(v >> (n - 1 - k)) & 1 for k in range(n)]


def champs(can_id, data, rtr=0):
    """Unstuffed fields, from SOF to the end of the CRC. Returns [(name, [bits])]."""
    f = [("SOF", [0]), ("ID", to_bits(can_id, 11)), ("RTR", [rtr]), ("IDE", [0]), ("r0", [0]),
         ("DLC", to_bits(len(data), 4))]
    for k, octet in enumerate(data):
        f.append((f"D{k}", to_bits(octet, 8)))
    flat = [b for _, bs in f for b in bs]
    crc = crc15(flat)
    f.append(("CRC", to_bits(crc, 15)))
    return f, crc


def stuffing(etiquetes):
    """etiquetes: [(name, bit)]. Inserts an inverted bit after 5 identical bits.
    The stuff bit counts toward the next run."""
    out, last, run = [], None, 0
    for nom, b in etiquetes:
        out.append((nom, b))
        run = run + 1 if b == last else 1
        last = b
        if run == 5:
            s = 1 - b
            out.append(("stuff", s))
            last, run = s, 1
    return out


def trame(can_id, data, rtr=0):
    f, crc = champs(can_id, data, rtr)
    etiq = [(nom, b) for nom, bs in f for b in bs]
    st = stuffing(etiq)
    # fixed-form parts, never stuffed; ACK as seen on the bus (a receiver drove 0)
    queue = [("CRCdel", 1), ("ACK", 0), ("ACKdel", 1)] + [("EOF", 1)] * 7 + [("IFS", 1)] * 3
    return st + queue, crc, len(etiq)


def section1():
    print("== 1. CRC-15/CAN, polynôme 0x4599")
    msg = b"123456789"
    bits = [b for o in msg for b in to_bits(o, 8)]
    c = crc15(bits)
    print(f'crc15(b"123456789") = 0x{c:04x}   reveng check = 0x059e   {"OK" if c == 0x059E else "ECHEC"}')
    return c == 0x059E


# Reference frame, copied from Ken Tindell's figure (capture on a real bus,
# kentindell.github.io/2020/01/03/canframe_py_tool/), stuff bits included, from SOF to IFS.
REF_TINDELL = ("0" "0000" "1" "0010100" "0" "0" "0" "1" "0001" "00000" "1" "001"
               "111011101010011" "1" "0" "1" "1111111" "111")


def section2():
    print("\n== 2. Trame ID 0x014, données 01, contre la capture de Ken Tindell")
    t, crc, n_brut = trame(0x014, [0x01])
    flux = "".join(str(b) for _, b in t)
    print(f"CRC calculé      : 0x{crc:04x} ({crc:015b})   publié : 0x7753 (111011101010011)")
    print(f"flux calculé     : {flux}")
    print(f"flux publié      : {REF_TINDELL}")
    ok = flux == REF_TINDELL and crc == 0x7753
    n_stuff = sum(1 for nom, _ in t if nom == "stuff")
    print(f"bits SOF..CRC    : {n_brut} avant stuffing, {n_brut + n_stuff} après ({n_stuff} stuff bits)")
    print(f"bits SOF..IFS    : {len(t)}")
    print(f"identique        : {'OUI' if ok else 'NON'}")
    print("\nchamp   bits")
    cur, acc = None, []
    for nom, b in t + [(None, None)]:
        base = "D" if nom and nom.startswith("D") and nom != "DLC" else nom
        if base != cur and cur is not None:
            print(f"{cur:<7} {''.join(acc)}")
            acc = []
        cur = base
        if b is not None:
            acc.append(str(b))
    return ok


NOEUDS = [("A", 0x245, [0x10]), ("B", 0x241, [0x0F, 0xA0]), ("C", 0x2C0, [0x01])]


def section3():
    print("\n== 3. Arbitrage : trois noeuds partent ensemble, bus = ET logique")
    flux = {n: trame(i, d)[0] for n, i, d in NOEUDS}
    for n, i, _ in NOEUDS:
        print(f"noeud {n} : ID 0x{i:03x} = {i:011b}")
    actifs = [n for n, _, _ in NOEUDS]
    print("\n t  champ  " + "  ".join(n for n, _, _ in NOEUDS) + "  bus  événement")
    t = 0
    lignes = []
    while True:
        emis = {n: flux[n][t][1] if n in actifs else 1 for n, _, _ in NOEUDS}
        nom = flux[actifs[0]][t][0]
        bus = min(emis.values())  # wired-AND: a single 0 is enough
        perdants = [n for n in actifs if emis[n] == 1 and bus == 0]
        ev = ", ".join(f"{p} lit 0 après avoir émis 1 : se tait" for p in perdants)
        cell = "  ".join(str(emis[n]) if n in actifs else "." for n, _, _ in NOEUDS)
        print(f"{t:2d}  {nom:<5}  {cell}   {bus}   {ev}")
        lignes.append((t, nom, {n: (emis[n] if n in actifs else None) for n, _, _ in NOEUDS}, bus))
        actifs = [n for n in actifs if n not in perdants]
        t += 1
        if nom == "RTR":
            break
    print(f"\ngagnant : {actifs[0]}, sans délai ; il continue avec IDE, r0, DLC...")
    return lignes


def section4():
    print("\n== 4. TEC (transmit error counter), règles Bosch CAN 2.0 partie A ch. 5")

    def etat(tec, rec=0):
        if tec >= 256:
            return "bus-off"
        if tec >= 128 or rec >= 128:
            return "error-passive"
        return "error-active"

    print("cas 1 : bit error à chaque envoi (ex. CANH en court-circuit), +8 par erreur")
    tec, k, vu = 0, 0, set()
    while tec < 256:
        tec += 8; k += 1
        e = etat(tec)
        if e not in vu or k in (1, 2):
            print(f"  erreur {k:2d} : TEC = {tec:3d}  {e}")
            vu.add(e)
    print("cas 2 : noeud seul sur le bus, personne ne pose l'ACK")
    tec, k = 0, 0
    for k in range(1, 41):
        if etat(tec) == "error-passive":
            pass  # exception 1: ACK error in error-passive, TEC unchanged
        else:
            tec += 8
        if k in (1, 16, 17, 40):
            print(f"  essai {k:2d} : TEC = {tec:3d}  {etat(tec)}")
    print("succès d'émission : TEC - 1 ; retour error-active si TEC et REC <= 127")
    print("sortie de bus-off : 128 x 11 bits récessifs = 1408 bits, soit 2,816 ms à 500 kbit/s")


def section5():
    print("\n== 5. Durée sur le fil (trame 0x241, 2 octets)")
    t, _, _ = trame(0x241, [0x0F, 0xA0])
    n = len(t)
    for debit in (125_000, 250_000, 500_000, 1_000_000):
        print(f"  {debit // 1000:4d} kbit/s : {n} bits (IFS compris) = {n / debit * 1e6:7.1f} µs")


if __name__ == "__main__":
    ok1 = section1()
    ok2 = section2()
    section3()
    section4()
    section5()
    sys.exit(0 if ok1 and ok2 else 1)
