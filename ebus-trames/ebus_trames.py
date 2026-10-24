#!/usr/bin/env python3
"""eBUS : CRC, échappement, trames réelles, adresses et arbitrage, recalculés sans matériel.

Pur Python, aucune librairie. Chaque section produit une slide de l’article
https://heurisme.fr/blog/ebus-trames/ . Les trames viennent de sources publiques (URL en commentaire).
"""

SYN, ESC, ACK, NAK, BROADCAST = 0xAA, 0xA9, 0x00, 0xFF, 0xFE


def table_crc(poly=0x9B):
    t = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = ((c << 1) ^ poly) & 0xFF if c & 0x80 else (c << 1) & 0xFF
        t.append(c)
    return t


T = table_crc()


def crc_ebus(octets):
    """CRC eBUS tel que le calcule ebusd (symbol.cpp, updateCrc) : crc = T[crc] ^ octet, départ à 0."""
    crc = 0
    for o in octets:
        crc = T[crc] ^ o
    return crc


def crc8_manuel(octets):
    """CRC-8 « de manuel » sur le même polynôme : crc = T[crc ^ octet]."""
    crc = 0
    for o in octets:
        crc = T[crc ^ o]
    return crc


def echappe(octets):
    out = []
    for o in octets:
        if o == ESC:
            out += [ESC, 0x00]
        elif o == SYN:
            out += [ESC, 0x01]
        else:
            out.append(o)
    return out


def desechappe(octets):
    out, i = [], 0
    while i < len(octets):
        if octets[i] == ESC:
            out.append({0x00: ESC, 0x01: SYN}[octets[i + 1]])
            i += 2
        else:
            out.append(octets[i])
            i += 1
    return out


def hx(octets):
    return " ".join(f"{o:02x}" for o in octets)


def h(s):
    return list(bytes.fromhex(s.replace(" ", "")))


def ok(calc, lu):
    return "OK" if calc == lu else "FAUX"


def decode_ms(fil_maitre, fil_esclave=None):
    """Une trame maître-esclave telle qu'elle passe sur le fil (échappée), sans les ACK ni le SYN."""
    m = desechappe(fil_maitre[:-1])
    qq, zz, pb, sb, nn = m[:5]
    db = m[5:5 + nn]
    crc_lu = fil_maitre[-1]
    crc_calc = crc_ebus(fil_maitre[:-1])
    print(f"  maître   QQ={qq:02x} ZZ={zz:02x} PB={pb:02x} SB={sb:02x} NN={nn:02x} DB=[{hx(db)}]")
    print(f"           CRC lu {crc_lu:02x}, recalculé {crc_calc:02x} : {ok(crc_calc, crc_lu)}")
    if fil_esclave:
        e_fil = fil_esclave[:-1]
        e = desechappe(e_fil)
        nn2 = e[0]
        crc_lu = fil_esclave[-1]
        crc_fil = crc_ebus(e_fil)
        crc_brut = crc_ebus(e)
        print(f"  esclave  NN={nn2:02x} DB=[{hx(e[1:])}] ({len(e) - 1} octets utiles, {len(e_fil) - 1} sur le fil)")
        print(f"           CRC lu {crc_lu:02x}, sur les octets du fil {crc_fil:02x} : {ok(crc_fil, crc_lu)}"
              + ("" if e == e_fil else f" ; sur les octets non échappés {crc_brut:02x} : {ok(crc_brut, crc_lu)}"))


def titre(t):
    print()
    print("== " + t)


print("eBUS, recalculs de l’article « eBUS : la chaudière parle sur deux fils »")

titre("1. CRC-8 eBUS, polynôme 0x9B (x^8 + x^7 + x^4 + x^3 + x + 1), départ 0")
# Vecteur du test unitaire d'ebusd : src/lib/ebus/test/test_symbol.cpp, lignes 71-85 (attendu 0x77)
v = h("10feb5050427a915")
print(f"  message             {hx(v + [SYN])}")
print(f"  sur le fil          {hx(echappe(v + [SYN]))}")
print(f"  CRC ebusd, fil      {crc_ebus(echappe(v + [SYN])):02x}   attendu par test_symbol.cpp : 77")
print(f"  CRC ebusd, brut     {crc_ebus(v + [SYN]):02x}   (sans échappement : faux)")
print(f"  CRC-8 classique     {crc8_manuel(echappe(v + [SYN])):02x}   (crc = T[crc ^ octet] : faux)")

titre("2. Échappement : AA devient A9 01, A9 devient A9 00")
for m in (h("aa"), h("a9"), h("10 aa a9 23")):
    print(f"  {hx(m):<14} -> {hx(echappe(m)):<20} -> {hx(desechappe(echappe(m)))}")

titre("3. Trames réelles, CRC recalculés")
print("Trame 1 : écoute passive, Vaillant (wiki ebusd, 3.1 TCP client commands, ligne <1025b50903290000e4000500009203008900)")
decode_ms(h("1025b50903290000e4"), h("05000092030089"))
print("Trame 2 : lecture envoyée par ebusd (même page, ligne >3115b509030d8700ff<00041545000002>00)")
decode_ms(h("3115b509030d8700ff"), h("041545000002"))
print("Trame 3 : réponse avec un octet AA échappé (ebusd issue 1800, ligne >3108b50905540200c30bf9<00080201c30ba9012300003c>00)")
decode_ms(h("3108b50905540200c30bf9"), h("080201c30ba9012300003c"))
print("Trame 4 : CRC lui-même échappé (même issue, ligne 3115b52406020001000400a900)")
f4 = h("3115b52406020001000400")
print(f"  CRC recalculé {crc_ebus(f4):02x}, envoyé sur le fil comme {hx(echappe([crc_ebus(f4)]))}")
print("Trame 5 : identification 07 04, sans réponse (ebusd issue 419, ligne >31040704006f)")
decode_ms(h("31040704006f"))

titre("4. Adresses maîtres : chaque demi-octet vaut 0, 1, 3, 7 ou F")
N = [0x0, 0x1, 0x3, 0x7, 0xF]
maitres = sorted((hi << 4) | lo for hi in N for lo in N)
print(f"  {len(maitres)} maîtres : {hx(maitres)}")
esclave = lambda a: 0x04 if a == 0xFF else (a + 5) & 0xFF
print("  adresse esclave du maître (+5) : " + ", ".join(f"{a:02x}->{esclave(a):02x}" for a in (0x00, 0x10, 0x31, 0xFF)))

titre("5. Arbitrage : le bus fait un ET des octets, bit de poids faible en premier")
def arbitre(*adr):
    bus = 0xFF
    for a in adr:
        bus &= a
    gagnant = [a for a in adr if a == bus]
    retente = [a for a in adr if (a & 0x0F) == (bus & 0x0F)] if not gagnant else []
    bits = lambda a: "".join(str((a >> k) & 1) for k in range(8))
    for a in adr:
        print(f"  émet {a:02x}  fil (bit 0 d'abord) {bits(a)}")
    print(f"  lit  {bus:02x}  fil (bit 0 d'abord) {bits(bus)}  ->", end=" ")
    if gagnant:
        print(f"{gagnant[0]:02x} gagne au premier tour")
    else:
        print("personne ne se reconnaît ; retente au SYN suivant : " + " ".join(f"{a:02x}" for a in retente))
for k, paire in enumerate(((0x10, 0x30), (0x31, 0x13), (0x03, 0x10))):
    if k:
        print()
    arbitre(*paire)

titre("6. Durées à 2400 bauds, 8N1")
octet_ms = 10 / 2400 * 1000
fil = [SYN] + h("1025b50903290000e4") + [ACK] + h("05000092030089") + [ACK, SYN]
print(f"  un octet = 10 bits = {octet_ms:.2f} ms")
print(f"  trame 1 complète, SYN de tête et de fin compris : {len(fil)} octets = {len(fil) * octet_ms:.0f} ms")
