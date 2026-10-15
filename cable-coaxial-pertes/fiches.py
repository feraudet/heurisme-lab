"""Figures transcribed by hand from the manufacturer datasheets listed in sources-sha256.txt.

Only the numbers the bench needs are here, each with the datasheet and table it comes from.
rejouer.sh downloads the PDFs into raw/ and checks their sha256: open them to compare.
"""

# Attenuation tables, "Nom. Attenuation" (Belden) or "Attenuation dB/100 ft" (Times), in dB per 100 ft.
# Belden tables stop at 1000 MHz except 8267 (RG-213), which goes to 4000 MHz.
CABLES = {
    "RG174": {
        "datasheet": "Belden 8216 (RG-174), raw/belden-8216.pdf, page 1, Electrical Characteristics, Attenuation",
        "points_db_100ft": [(1, 1.9), (10, 3.3), (50, 5.8), (100, 8.4), (200, 12.5), (400, 19.0),
                            (700, 27.0), (900, 31.0), (1000, 34.0)],
    },
    "RG58": {
        "datasheet": "Belden 8240 (RG-58), raw/belden-8240.pdf, page 1, Electrical Characteristics, Attenuation",
        "points_db_100ft": [(1, 0.3), (10, 1.1), (50, 2.5), (100, 3.8), (200, 5.6), (400, 8.4),
                            (700, 11.7), (900, 13.7), (1000, 14.5)],
    },
    "RG213": {
        "datasheet": "Belden 8267 (RG-213), raw/belden-8267.pdf, page 1, Electrical Characteristics, Attenuation",
        "points_db_100ft": [(1, 0.17), (10, 0.55), (50, 1.3), (100, 1.9), (200, 2.7), (400, 4.1),
                            (700, 6.5), (900, 7.6), (1000, 8.0), (4000, 21.5)],
    },
    "LMR400": {
        "datasheet": "Times Microwave LMR-400, raw/times-lmr400.pdf, page 2, Attenuation vs. Frequency (typical)",
        "points_db_100ft": [(30, 0.7), (50, 0.9), (150, 1.5), (220, 1.9), (450, 2.7), (900, 3.9),
                            (1500, 5.1), (1800, 5.7), (2000, 6.0), (2500, 6.8), (5800, 10.8), (8000, 13.0)],
        # Same page: "Calculate Attenuation = (0.122290) x sqrt(FMHz) + (0.000260) x FMHz", in dB/100 ft.
        "formula_db_100ft": (0.122290, 0.000260),
    },
}

# Connectors, maximum insertion loss (Rosenberger datasheets).
CONNECTORS = {
    "N plug for RG 58 C/U (Rosenberger 53S107-106N5)": {
        "datasheet": "raw/rosenberger-53S107-106N5.pdf, page 2, Electrical data, Insertion loss",
        "max_db": lambda f_ghz: 0.05,  # "<= 0.05 dB"
        "rule": "<= 0.05 dB",
    },
    "SMA plug (Rosenberger 32S107-307L5)": {
        "datasheet": "raw/rosenberger-32S107-307L5.pdf, page 2, Electrical data, Insertion loss",
        "max_db": lambda f_ghz: 0.04 * f_ghz ** 0.5,  # "<= 0.04 x sqrt(f) dB, DC to 5 GHz"
        "rule": "<= 0.04 x sqrt(f/GHz) dB",
    },
}

# FlightAware 1090 MHz antenna, product page (flightaware.store): "5.5 dBi gain", "Length 66cm/26in".
ANTENNA_DBI = 5.5
# ITU-R BS.1195-1, equation (6): Gd = Gi - 2.15 dB (gain over a half-wave dipole).
DIPOLE_DBI = 2.15

# Mini-Circuits PSA4-5043+ (LNA), raw/minicircuits-psa4-5043.pdf, page 2, Vd = +5.0 V, typical at 1.0 GHz.
LNA = {"name": "PSA4-5043+", "nf_db": 0.75, "gain_db": 18.4, "gain_min_db": 16.5}

DB100FT_TO_DB100M = 100 / 30.48  # 100 m = 328.084 ft, so x dB/100 ft = 3.28084 x dB/100 m
