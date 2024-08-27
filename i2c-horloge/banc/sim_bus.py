#!/usr/bin/env python3
"""Simulated I²C bus with a 1 µs step: two open-collector lines (wired AND).

A master reads a temperature sensor in "hold master" mode: the sensor
holds SCL low during its measurement (clock stretching). The master
either respects this stretching or not, depending on the --respecte / --ignore option.

The sensor is a model written for this bench, modelled on the sequence of
figure 15 of the SHT21 datasheet (address 0x40, command 0xE3, 3 bytes read). The
bytes returned (66 F0 8D) and the measurement time (65.25 ms) are those of the
real sigrok-dumps capture i2c-sht21-100khz-read-serial-hold.sr.

Outputs: a VCD file (bus lines, 1 µs per step) that sigrok-cli -I vcd can
decode, and the master's log on standard output.
"""
import argparse

import sys as _sys
EN = '--en' in _sys.argv
if EN:
    _sys.argv.remove('--en')


def L(fr, en):
    """Text depending on the language: --en on the command line gives English."""
    return en if EN else fr


ADR = 0x40
REPONSE = [0x66, 0xF0, 0x8D]
DEMI = 5            # clock half-period in µs: 100 kHz


class Capteur:
    """I²C slave: reacts to the edges seen on the bus, pulls the lines to 0."""

    def __init__(self, maintien_us):
        self.maintien = maintien_us
        self.scl, self.sda = 1, 1          # 1 = released, 0 = pulls to ground
        self.etat = 'repos'
        self.mesure_demandee = False
        self.journal = []

    def log(self, t, msg):
        self.journal.append((t, msg))

    def pas(self, t, p_scl, p_sda, scl, sda):
        if p_scl and scl and p_sda and not sda:          # START
            self.etat, self.bits, self.octet = 'adresse', 0, 0
            self.sda = 1
            return
        if p_scl and scl and not p_sda and sda:          # STOP
            self.etat, self.sda = 'repos', 1
            return
        if self.etat == 'maintien':
            if t >= self.fin_maintien:
                self.sda = (self.tx[0] >> 7) & 1
                self.pos, self.idx = 1, 0
                self.etat = 'relache'
            return
        if self.etat == 'relache':                       # 1 µs after the data
            self.scl = 1
            self.etat = 'emission'
            self.log(t, L('relâche SCL, mesure prête', 'releases SCL, measurement ready'))
            return
        montant = not p_scl and scl
        descendant = p_scl and not scl
        if montant and self.etat in ('adresse', 'reception'):
            self.octet = (self.octet << 1) | sda
            self.bits += 1
        elif montant and self.etat == 'ack_maitre':
            self.ack_recu = (sda == 0)
        elif descendant:
            self.front_descendant(t)

    def front_descendant(self, t):
        e = self.etat
        if e in ('adresse', 'reception') and self.bits == 8:
            if e == 'adresse':
                self.lecture = self.octet & 1
                ok = (self.octet >> 1) == ADR
                if ok and self.lecture and not self.mesure_demandee:
                    ok = False                           # nothing to send: NACK
                if not ok:
                    self.etat = 'ignore'
                    return
            self.sda = 0                                 # ACK
            self.etat = e + '_ack'
        elif e == 'adresse_ack':
            self.sda = 1
            if self.lecture:
                self.mesure_demandee = False
                self.tx = list(REPONSE)
                self.scl = 0                             # clock stretching
                self.fin_maintien = t + self.maintien
                self.etat = 'maintien'
                self.log(t, L(f'retient SCL à 0 pour {self.maintien / 1000:.2f} ms', f'holds SCL at 0 for {self.maintien / 1000:.2f} ms'))
            else:
                self.etat, self.bits, self.octet = 'reception', 0, 0
        elif e == 'reception_ack':
            self.sda = 1
            if self.octet == 0xE3:
                self.mesure_demandee = True
            self.etat, self.bits, self.octet = 'reception', 0, 0
        elif e == 'emission':
            if self.pos < 8:
                self.sda = (self.tx[self.idx] >> (7 - self.pos)) & 1
                self.pos += 1
            else:
                self.sda = 1
                self.etat = 'ack_maitre'
        elif e == 'ack_maitre':
            self.idx += 1
            if self.ack_recu and self.idx < len(self.tx):
                self.sda = (self.tx[self.idx] >> 7) & 1
                self.pos = 1
                self.etat = 'emission'
            else:
                self.sda = 1
                self.etat = 'ignore'


def maitre(respecte, n_lectures, pause_us, journal):
    """Generator: receives the bus state (scl, sda), yields its commands."""
    etat = {'scl': 1, 'sda': 1}
    bus = yield (1, 1)

    def attendre(n):
        nonlocal bus
        for _ in range(n):
            bus = yield (etat['scl'], etat['sda'])

    def monter_scl():
        nonlocal bus
        etat['scl'] = 1
        bus = yield (1, etat['sda'])
        if respecte:
            while bus[0] == 0:                           # waits until SCL really goes high
                bus = yield (1, etat['sda'])
        yield from attendre(DEMI - 1)

    def start():
        etat['sda'] = 1
        yield from attendre(1)
        yield from monter_scl()
        etat['sda'] = 0
        yield from attendre(DEMI)
        etat['scl'] = 0
        yield from attendre(DEMI)

    def ecrire_bit(b):
        etat['sda'] = b
        yield from attendre(DEMI)
        yield from monter_scl()
        etat['scl'] = 0
        yield from attendre(1)

    def lire_bit():
        etat['sda'] = 1
        yield from attendre(DEMI)
        etat['scl'] = 1
        b = yield (1, 1)
        if respecte:
            while b[0] == 0:
                b = yield (1, 1)
        yield from attendre(DEMI // 2)
        v = bus[1]                                       # samples SDA in the middle of the high level
        yield from attendre(DEMI - DEMI // 2 - 1)
        etat['scl'] = 0
        yield from attendre(1)
        return v

    def ecrire_octet(o):
        for k in range(7, -1, -1):
            yield from ecrire_bit((o >> k) & 1)
        return (yield from lire_bit()) == 0              # True = ACK

    def lire_octet(ack):
        v = 0
        for _ in range(8):
            v = (v << 1) | (yield from lire_bit())
        yield from ecrire_bit(0 if ack else 1)
        return v

    def stop():
        etat['sda'] = 0
        yield from attendre(DEMI)
        yield from monter_scl()
        etat['sda'] = 1
        yield from attendre(DEMI)

    yield from attendre(50)
    for n in range(1, n_lectures + 1):
        t0 = horloge[0]
        yield from start()
        a1 = yield from ecrire_octet(ADR << 1)
        a2 = (yield from ecrire_octet(0xE3)) if a1 else False
        if not (a1 and a2):
            yield from stop()
            journal.append((horloge[0], L(f'lecture {n} : NACK sur {"l’adresse" if not a1 else "la commande"}, capteur absent ?', f'read {n}: NACK on {"the address" if not a1 else "the command"}, sensor missing?')))
            yield from attendre(pause_us)
            continue
        yield from start()                               # repeated START
        a3 = yield from ecrire_octet((ADR << 1) | 1)
        if not a3:
            yield from stop()
            journal.append((horloge[0], L(f'lecture {n} : NACK sur l’adresse en lecture', f'read {n}: NACK on the read address')))
            yield from attendre(pause_us)
            continue
        oct_ = [(yield from lire_octet(True)), (yield from lire_octet(True)),
                (yield from lire_octet(False))]
        yield from stop()
        brut = (oct_[0] << 8 | oct_[1]) & 0xFFFC
        temp = -46.85 + 175.72 * brut / 65536
        dur = (horloge[0] - t0) / 1000
        journal.append((horloge[0], L(f'lecture {n} : octets ', f'read {n}: bytes ') + " ".join(f"{o:02X}" for o in oct_)
                            + f'  -> {temp:6.2f} °C   ' + L(f'(transaction : {dur:.2f} ms)', f'(transaction: {dur:.2f} ms)')))
        yield from attendre(pause_us)
    while True:
        yield from attendre(1)


horloge = [0]


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--respecte', action='store_true')
    g.add_argument('--ignore', action='store_true')
    ap.add_argument('--lectures', type=int, default=4)
    ap.add_argument('--pause-ms', type=float, default=100)
    ap.add_argument('--maintien-ms', type=float, default=65.25)
    ap.add_argument('--vcd', required=True)
    a = ap.parse_args()

    jm = []
    capteur = Capteur(int(a.maintien_ms * 1000))
    m = maitre(a.respecte, a.lectures, int(a.pause_ms * 1000), jm)
    m_scl, m_sda = next(m)
    duree = int((a.lectures * (a.maintien_ms + a.pause_ms + 2) + 5) * 1000)
    p_scl = p_sda = 1
    changements = []
    for t in range(duree):
        horloge[0] = t
        scl = m_scl & capteur.scl                        # wired AND: a single 0 is enough
        sda = m_sda & capteur.sda
        if t == 0 or (scl, sda) != (p_scl, p_sda):
            changements.append((t, scl, sda))
        capteur.pas(t, p_scl, p_sda, scl, sda)
        p_scl, p_sda = scl, sda
        m_scl, m_sda = m.send((scl, sda))
    with open(a.vcd, 'w') as f:
        f.write('$timescale 1 us $end\n$scope module bus $end\n'
                '$var wire 1 ! SCL $end\n$var wire 1 " SDA $end\n'
                '$upscope $end\n$enddefinitions $end\n')
        for t, scl, sda in changements:
            f.write(f'#{t}\n{scl}!\n{sda}"\n')
        f.write(f'#{duree}\n')
    print(L(f'maître : {"respecte" if a.respecte else "ignore"} le clock stretching', f'controller: {"honours" if a.respecte else "ignores"} clock stretching'))
    for t, msg in sorted(jm + [(t, L('capteur : ', 'sensor: ') + s) for t, s in capteur.journal]):
        print(f'{t / 1000:9.3f} ms  {msg}')


if __name__ == '__main__':
    main()
