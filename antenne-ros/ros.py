#!/usr/bin/env python3
"""SWR arithmetic of the bench, Python standard library only.

  python3 ros.py ros      reflection coefficient, SWR, return loss, reflected power
                          for a few load impedances on a 50 ohm line, 25 W forward
  python3 ros.py cable    what the SWR meter at the transmitter shows at the end of 20 m
                          of coax, for the antennas simulated by NEC2 (nec/*.out)

Formulas (any VNA application note):
  gamma = (Z - Z0) / (Z + Z0)            reflection coefficient, complex
  SWR   = (1 + |gamma|) / (1 - |gamma|)
  RL    = -20 log10 |gamma|              return loss, dB
  reflected power = forward power * |gamma|^2

A line with matched loss A dB attenuates the forward wave by A on the way up and the
reflected wave by A again on the way down: |gamma| seen at the transmitter = |gamma_load| * 10^(-2A/20).
The transmitter is assumed not to re-reflect what comes back (no tuner between them).

Cable attenuation, at 144.8 MHz, from the manufacturer data sheets:
  Belden 8240 (RG-58): 3.8 dB/100 ft at 100 MHz, 5.6 dB/100 ft at 200 MHz. In between, the bench
    uses the usual model a*sqrt(f) + b*f fitted through these two points.
  Times Microwave LMR-400: 0.122290*sqrt(F) + 0.000260*F dB/100 ft (formula of the data sheet).
"""
import math
import os
import sys

Z0 = 50.0
C_M_S = 299_792_458      # speed of light, m/s (exact, SI)
P_EMISSION_W = 25.0      # forward power of the packet radio transmitter (hypothesis of the deck)
F_MHZ = 144.8
LONGUEUR_M = 20.0        # coax from the radio to the roof (hypothesis of the deck)
PIEDS_PAR_100M = 100 / 0.3048 / 100   # 100 m = 3.2808 x 100 ft


def gamma(z):
    return (z - Z0) / (z + Z0)


def ros(g):
    g = abs(g)
    return math.inf if g >= 1 else (1 + g) / (1 - g)


def rl(g):
    g = abs(g)
    return math.inf if g == 0 else -20 * math.log10(g)


def att_rg58_db_100ft(f):
    # a*sqrt(f) + b*f through (100 MHz, 3.8) and (200 MHz, 5.6), Belden 8240 data sheet
    s1, s2 = math.sqrt(100), math.sqrt(200)
    b = (5.6 - 3.8 * s2 / s1) / (200 - 100 * s2 / s1)
    a = (3.8 - b * 100) / s1
    return a * math.sqrt(f) + b * f


def att_lmr400_db_100ft(f):
    return 0.122290 * math.sqrt(f) + 0.000260 * f


CABLES = [
    ("RG-58 (Belden 8240)", att_rg58_db_100ft),
    ("LMR-400 (Times)", att_lmr400_db_100ft),
]


def fz(z):
    if z == math.inf:
        return "open"
    signe = "+" if z.imag >= 0 else "-"
    return f"{z.real:.1f} {signe} j{abs(z.imag):.1f}"


def fros(v):
    return "inf" if v == math.inf else f"{v:.2f}"


def frl(v):
    return "inf" if v == math.inf else f"{v:.1f}"


def bilan(nom, z, perte_db):
    g_ant = 1.0 if z == math.inf else abs(gamma(z))
    a = 10 ** (-perte_db / 10)
    g_tx = g_ant * a
    p_ant = P_EMISSION_W * a
    p_acc = p_ant * (1 - g_ant ** 2)
    p_ret = P_EMISSION_W * a * a * g_ant ** 2
    return nom, fz(z), fros(ros(g_ant)), fros(ros(g_tx)), p_ant, p_acc, p_ret


def section_ros():
    print(f"Z0 = {Z0:.0f} ohm, forward power {P_EMISSION_W:.0f} W")
    print()
    print(f"{'load Z (ohm)':<16}{'|gamma|':>8}{'SWR':>7}{'RL (dB)':>9}{'reflected':>11}{'accepted':>10}")
    charges = [complex(50, 0), complex(60, 0), complex(75, 0), complex(100, 0), complex(25, 0),
               complex(50, 30), complex(50, -30), complex(150, 0), complex(10, 0)]
    for z in charges:
        g = abs(gamma(z))
        print(f"{fz(z):<16}{g:>8.3f}{fros(ros(g)):>7}{frl(rl(g)):>9}{P_EMISSION_W * g * g:>9.2f} W{P_EMISSION_W * (1 - g * g):>8.2f} W")
    print(f"{'open':<16}{1:>8.3f}{'inf':>7}{0:>9.1f}{P_EMISSION_W:>9.2f} W{0:>8.2f} W")
    print()
    print("SWR -> power that reaches the antenna and is not sent back:")
    for s in (1.2, 1.5, 2.0, 3.0, 5.0):
        g = (s - 1) / (s + 1)
        print(f"  SWR {s:.1f} : |gamma| {g:.3f}, RL {rl(g):4.1f} dB, accepted {100 * (1 - g * g):5.1f} %, mismatch loss {-10 * math.log10(1 - g * g):.2f} dB")
    print()
    lam = C_M_S / (F_MHZ * 1e6)
    print(f"Wavelength at {F_MHZ} MHz: {lam * 100:.1f} cm in free space, quarter wave {lam * 25:.1f} cm")
    print("Standing wave maxima repeat every half wavelength in the cable (velocity factor from the data sheet):")
    for nom, vf in (("RG-58 (Belden 8240)", 0.66), ("LMR-400 (Times)", 0.84)):
        print(f"  {nom:<20} VF {vf:.2f} : every {lam * vf / 2 * 100:.1f} cm")


def section_cable():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import lit_nec
    antennes = lit_nec.impedances_a(F_MHZ)
    print(f"Transmitter: {P_EMISSION_W:.0f} W forward at {F_MHZ} MHz, {LONGUEUR_M:.0f} m of coax to the antenna")
    pertes = []
    for nom, f in CABLES:
        par100m = f(F_MHZ) * PIEDS_PAR_100M
        perte = par100m * LONGUEUR_M / 100
        pertes.append((nom, perte))
        print(f"  {nom:<20} {f(F_MHZ):.2f} dB/100 ft = {par100m:.2f} dB/100 m -> {perte:.2f} dB over {LONGUEUR_M:.0f} m")
    print()
    for nom_cable, perte in pertes:
        print(f"--- {nom_cable}, {perte:.2f} dB matched loss ---")
        print(f"{'antenna':<14}{'Z at antenna':<17}{'SWR ant':>8}{'SWR at TX':>10}{'reaches ant':>12}{'radiated':>10}{'back to TX':>11}")
        lignes = [(f"rod {l:.1f} cm", z) for l, z in antennes] + [("disconnected", math.inf)]
        for nom, z in lignes:
            n, zs, s_ant, s_tx, p_ant, p_acc, p_ret = bilan(nom, z, perte)
            print(f"{n:<14}{zs:<17}{s_ant:>8}{s_tx:>10}{p_ant:>10.2f} W{p_acc:>8.2f} W{p_ret:>9.2f} W")
        print()
    print("Same disconnected antenna (|gamma| = 1), SWR read at the transmitter vs RG-58 length:")
    att = att_rg58_db_100ft(F_MHZ) * PIEDS_PAR_100M / 100
    for longueur in (0, 5, 10, 20, 30, 50):
        g_tx = 10 ** (-2 * att * longueur / 20)
        print(f"  {longueur:>3} m : loss {att * longueur:5.2f} dB, SWR at TX {fros(ros(g_tx))}")


def main():
    quoi = sys.argv[1] if len(sys.argv) > 1 else ""
    if quoi == "ros":
        section_ros()
    elif quoi == "cable":
        section_cable()
    else:
        sys.exit("usage: ros.py ros|cable")


if __name__ == "__main__":
    main()
