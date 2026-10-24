# eBUS bench: the boiler talks on two wires

This bench goes with the article https://heurisme.fr/en/blog/ebus-trames/ : the eBUS CRC, the escaping of `AA` and `A9`, five real frames taken from public ebusd logs, the 25 master addresses and the arbitration, all recomputed in pure Python. No eBUS hardware: the frames come from the ebusd wiki and issues.

File names and outputs are in French because the original article is. Useful names: `rejouer.sh` = replay script, `raw/` = raw outputs, `ebus_trames.py` = eBUS frames, `maître` = master, `esclave` = slave, `échappement` = escaping, `fil` = wire, `lu` = read, `recalculé` = recomputed, `FAUX` = wrong.

## How to replay

- Docker.
- Image `python:3.13-slim-bookworm`, pinned by digest `sha256:e32be0e55814a08977501ca863271d9bd02443710db8f2afaf8372e2c4508530`. Inside: Python 3.13.17, no package.

Single command:

```bash
bash rejouer.sh
```

It reruns `ebus_trames.py` and rewrites `raw/ebus_trames.txt`. The output does not change from one run to the next. Without Docker, `python3 ebus_trames.py` gives the same lines.

`bash rejouer.sh refs` downloads the two eBUS specifications into `ref/` and checks their sha256.

## The CRC is not the textbook CRC-8

ebusd computes `crc = T[crc] ^ byte` (`src/lib/ebus/symbol.cpp`, `updateCrc`), where `T` is the CRC-8 table of polynomial 0x9B. The textbook form, `crc = T[crc ^ byte]`, gives other values: section 1 of the output shows both on the ebusd unit test vector. The CRC runs over the bytes as they go on the wire, after escaping (specification OSI 1/2, 5.7): frame 3 only checks out that way.

## File to slide

| Section of `raw/ebus_trames.txt` | Slide |
|---|---|
| 6 (durations at 2400 baud) | 2 |
| 2 (escaping) | 4 |
| 5 (arbitration, AND of the address bytes) | 5 |
| 4 (25 master addresses, slave address = master + 5) | 5, 6 |
| 3 (real frames, CRC recomputed) | 6, 7 |
| 1 (CRC on the ebusd test vector) | 7 |

## Sources of the frames

| Frame | Source |
|---|---|
| 1, 2 | ebusd wiki, TCP client commands, raw logging: https://github.com/john30/ebusd/wiki/3.1.-TCP-client-commands |
| 3, 4 | ebusd issue 1800: https://github.com/john30/ebusd/issues/1800 |
| 5 | ebusd issue 419: https://github.com/john30/ebusd/issues/419 |
| CRC test vector | ebusd `src/lib/ebus/test/test_symbol.cpp`, lines 71-85, commit 38db2d28: https://github.com/john30/ebusd/blob/38db2d28bd5622cadb6078c1662c6f7da5cef891/src/lib/ebus/test/test_symbol.cpp |

## Third-party data

It is not in this repo. `rejouer.sh refs` downloads it into `ref/` from the Wayback Machine (ebus-wiki.org no longer answers) and checks the sha256.

| File | URL | License |
|---|---|---|
| `spec_prot_12_v1_3_1_e.pdf` | eBUS Specification, Physical Layer OSI 1, Data-Link Layer OSI 2, V1.3.1 (2007): https://web.archive.org/web/20231110032014/https://ebus-wiki.org/lib/exe/fetch.php/ebus/spec_prot_12_v1_3_1_e.pdf | eBUS Interest Group's rights |
| `spec_prot_7_v1_6_1_e.pdf` | eBUS Specification, Application Layer OSI 7, V1.6.1 (2007): https://web.archive.org/web/20240616075418/https://ebus-wiki.org/lib/exe/fetch.php/ebus/spec_prot_7_v1_6_1_e.pdf | eBUS Interest Group's rights |

If a sha256 differs, the script stops, and `TOLERE=1` carries on (`TOLERE` = tolerate).
