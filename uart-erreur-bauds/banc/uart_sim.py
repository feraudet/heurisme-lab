#!/usr/bin/env python3
"""UART bench: transmitter at a given baud rate, simulated 16x receiver (AVR model).

The receiver follows the ATmega328P datasheet description (§ 20.8, DS40002061B):
- it samples the line 16 times per bit (U2X=0) or 8 times (U2X=1);
- the first sample at 0 after idle is sample 1 of the start bit;
- each bit is decided by majority vote of samples 8, 9, 10 (4, 5, 6 with U2X=1);
- if the start bit vote gives 1, it is a glitch: back to waiting;
- if the stop bit vote gives 0: framing error (FE);
- after the last voted sample of the stop bit, it waits for a new falling edge.

Usage: python3 uart_sim.py trame|derive|seuils|quartz|pc|deux-avr|tout [--en]
"""
import bisect
import sys

TEXTE = b"Hello World!\r\n"
EN = "--en" in sys.argv  # English output for en.html


def L(fr, en):
    return en if EN else fr


def trame(octet, data_bits=8):
    """Bits of an 8N1 frame: start (0), data LSB first, stop (1)."""
    return [0] + [(octet >> k) & 1 for k in range(data_bits)] + [1]


class Ligne:
    """Level of the TX line as a function of time (idle at 1)."""

    def __init__(self, octets, baud_tx, repos_bits=0.0, debut=1e-4):
        self.t, self.v = [0.0], [1]
        tb = 1.0 / baud_tx
        t = debut
        for o in octets:
            for b in trame(o):
                self.t.append(t)
                self.v.append(b)
                t += tb
            t += repos_bits * tb
        self.t.append(t)
        self.v.append(1)
        self.fin = t + 20 * tb

    def niveau(self, t):
        return self.v[bisect.bisect_right(self.t, t) - 1]


def recepteur(ligne, baud_rx, phase=0.0, u2x=False, trace=None):
    """Decodes the line. phase: offset of the sampling clock, as a fraction of a tick.

    Returns a list of (byte, framing_error)."""
    S = 8 if u2x else 16
    vote = (4, 5, 6) if u2x else (8, 9, 10)
    tick = 1.0 / (baud_rx * S)
    n_max = int(ligne.fin / tick) + 1
    sortie = []
    n = 0
    prec = 1
    while n < n_max:
        t = (n + phase) * tick
        v = ligne.niveau(t)
        if prec == 1 and v == 0:
            # n = sample 1 of the start bit
            def bit(k):
                ech = [n + k * S + (j - 1) for j in vote]
                vals = [ligne.niveau((e + phase) * tick) for e in ech]
                if trace is not None:
                    trace.append((k, [(e + phase) * tick for e in ech], vals))
                return 1 if sum(vals) >= 2 else 0

            if bit(0) == 1:  # glitch
                n += 1
                prec = 1
                continue
            octet = 0
            for k in range(8):
                octet |= bit(1 + k) << k
            stop = bit(9)
            sortie.append((octet, stop == 0))
            n = n + 9 * S + vote[-1] - 1 + 1  # resumes right after the last voted sample of the stop bit
            prec = ligne.niveau((n - 1 + phase) * tick)
            continue
        prec = v
        n += 1
    return sortie


def affiche(res):
    car = []
    for o, fe in res:
        c = chr(o) if 32 <= o < 127 else "\\r" if o == 13 else "\\n" if o == 10 else "[%02X]" % o
        car.append(c + ("!" if fe else ""))
    return "".join(car)


def nb_fe(res):
    return sum(1 for _, fe in res if fe)


def nb_faux(res, attendu):
    if len(res) != len(attendu):
        return None
    return sum(1 for (o, _), a in zip(res, attendu) if o != a)


# ---------------------------------------------------------------- commands

def cmd_trame():
    o = ord("H")
    bits = trame(o)
    print(L("octet 'H' = 0x%02X = %s (binaire, bit 7 à gauche)", "byte 'H' = 0x%02X = %s (binary, bit 7 on the left)") % (o, format(o, "08b")))
    noms = ["start"] + ["d%d" % k for k in range(8)] + ["stop"]
    print(L("sur le fil, dans l'ordre : ", "on the wire, in order: ") + " ".join("%s=%d" % (n, b) for n, b in zip(noms, bits)))
    print(L("115200 bauds : 1 bit = %.2f us, 1 trame de 10 bits = %.1f us", "115200 baud: 1 bit = %.2f us, 1 frame of 10 bits = %.1f us") % (1e6 / 115200, 1e7 / 115200))
    print(L("  9600 bauds : 1 bit = %.2f us, 1 trame de 10 bits = %.1f us", "  9600 baud: 1 bit = %.2f us, 1 frame of 10 bits = %.1f us") % (1e6 / 9600, 1e7 / 9600))


def cmd_derive():
    """Where the central sample (no. 9) of each bit falls, depending on the baud rate gap."""
    baud_rx = 115200
    print(L("récepteur 16x à 115200 bauds, deux octets 0x55 collés, front du start détecté sans retard", "16x receiver at 115200 baud, two back-to-back 0x55 bytes, start edge detected with no delay"))
    print(L("écart = débit émetteur / débit récepteur - 1", "offset = transmitter rate / receiver rate - 1"))
    print(L("position de l'échantillon 9 dans le bit émis (0 % = début du bit, 100 % = fin)", "position of sample 9 within the transmitted bit (0 % = start of bit, 100 % = end)"))
    noms = ["start"] + ["d%d" % k for k in range(8)] + ["stop"]
    print(L("écart    ", "offset   ") + " ".join("%6s" % n for n in noms) + L("   résultat", "   result"))
    for ecart in (0.0, 2.0, 4.0, 6.0, -4.0, -6.0):
        baud_tx = baud_rx * (1 + ecart / 100)
        lg = Ligne([0x55, 0x55], baud_tx, debut=100 / (baud_rx * 16))
        tr = []
        res = recepteur(lg, baud_rx, phase=0.0, trace=tr)
        t0 = lg.t[1]
        pos = []
        for k, temps, _ in tr[:10]:
            tm = temps[1] - t0  # sample 9
            pos.append(100 * (tm * baud_tx - k))
        cases = " ".join(("%5.0f%%" % p) if 0 <= p < 100 else ("%5.0f!" % p) for p in pos)
        o, fe = res[0]
        verdict = "0x%02X%s" % (o, "  FRAMING ERROR" if fe else "  ok" if o == 0x55 else L("  faux", "  wrong"))
        print("%+5.1f %%  %s   %s" % (ecart, cases, verdict))


def tolere(ratio, u2x=False, phases=16):
    """True if all bytes get through, whatever the receiver phase."""
    baud_rx = 115200
    octets = list(range(256))
    lg = Ligne(octets, baud_rx * ratio)  # back-to-back frames, the worst case
    for p in range(phases):
        res = recepteur(lg, baud_rx, phase=p / phases, u2x=u2x)
        if len(res) != 256 or nb_fe(res) or nb_faux(res, octets):
            return False
    return True


def cmd_seuils():
    print(L("256 octets collés (0x00 à 0xFF), 16 phases d'horloge testées par écart", "256 back-to-back bytes (0x00 to 0xFF), 16 clock phases tested per offset"))
    for u2x in (False, True):
        S = 8 if u2x else 16
        SF, SM = (4, 5) if u2x else (8, 9)
        D = 8
        rslow = (D + 1) * S / (S - 1 + D * S + SF)
        rfast = (D + 2) * S / ((D + 1) * S + SM)
        # sweep in 0.1 % steps
        oks = [r for r in range(850, 1151) if tolere(r / 1000, u2x)]
        print(L("U2X=%d (%2dx) : passe de %+.1f %% à %+.1f %% | datasheet, équation 1 : Rslow %.2f %%, Rfast %.2f %%",
                "U2X=%d (%2dx): passes from %+.1f %% to %+.1f %% | datasheet, equation 1: Rslow %.2f %%, Rfast %.2f %%")
              % (int(u2x), S, oks[0] / 10 - 100, oks[-1] / 10 - 100, 100 * rslow, 100 * rfast))


def ubrr(fosc, baud, u2x):
    div = 8 if u2x else 16
    u = round(fosc / (div * baud) - 1)
    reel = fosc / (div * (u + 1))
    return u, reel, 100 * (reel / baud - 1)


QUARTZ = [(16e6, False), (16e6, True), (8e6, False), (8e6, True), (11.0592e6, False), (20e6, False)]


def cmd_quartz():
    print(L("UBRR = round(fosc / (16 ou 8 x baud) - 1) ; débit réel = fosc / (16 ou 8 x (UBRR + 1))", "UBRR = round(fosc / (16 or 8 x baud) - 1); actual rate = fosc / (16 or 8 x (UBRR + 1))"))
    print(L("quartz        U2X    baud  UBRR  débit réel   erreur", "crystal       U2X    baud  UBRR  actual rate  error"))
    for fosc, u2x in QUARTZ:
        for baud in (9600, 115200):
            u, reel, err = ubrr(fosc, baud, u2x)
            print("%8.4f MHz   %d  %6d  %4d  %10.1f  %+5.1f %%" % (fosc / 1e6, int(u2x), baud, u, reel, err))


def cmd_pc():
    print(L("'Hello World!\\r\\n' x 2 émis par l'ATmega, lu par un récepteur 16x réglé à 115200 ; ! = framing error", "'Hello World!\\r\\n' x 2 sent by the ATmega, read by a 16x receiver set to 115200; ! = framing error"))
    for fosc, u2x in QUARTZ:
        _, reel, err = ubrr(fosc, 115200, u2x)
        res = recepteur(Ligne(TEXTE * 2, reel), 115200, phase=0.5)
        print("%7.4f MHz U2X=%d  %+4.1f %% : %s  FE=%d" % (fosc / 1e6, int(u2x), err, affiche(res), nb_fe(res)))


def cmd_deux_avr():
    print(L("Deux ATmega328P à 16 MHz, 115200 demandés des deux côtés ; ! = framing error", "Two ATmega328P at 16 MHz, 115200 requested on both sides; ! = framing error"))
    _, tx0, _ = ubrr(16e6, 115200, False)
    _, tx1, _ = ubrr(16e6, 115200, True)
    for nom_tx, tx, nom_rx, rx, u2x_rx in [("U2X=0", tx0, "U2X=0", tx0, False), ("U2X=0", tx0, "U2X=1", tx1, True),
                                           ("U2X=1", tx1, "U2X=0", tx0, False)]:
        res = recepteur(Ligne(TEXTE * 2, tx), rx, phase=0.5, u2x=u2x_rx)
        print(L("%s -> %s  écart %+4.1f %% : %s  FE=%d", "%s -> %s  offset %+4.1f %%: %s  FE=%d") % (nom_tx, nom_rx, 100 * (tx / rx - 1), affiche(res), nb_fe(res)))


if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else "tout"
    cmds = {"trame": cmd_trame, "derive": cmd_derive, "seuils": cmd_seuils, "quartz": cmd_quartz, "pc": cmd_pc, "deux-avr": cmd_deux_avr}
    for nom, f in cmds.items():
        if c in (nom, "tout"):
            if c == "tout":
                print("== " + nom)
            f()
