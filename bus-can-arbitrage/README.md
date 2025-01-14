# CAN bus bench: arbitration

This bench goes with the deck https://heurisme.fr/en/blog/bus-can-arbitrage/ : a classic CAN frame (11 bits) built bit by bit, CRC-15 and bit stuffing recomputed, arbitration between three nodes on a wired-AND bus, error counters, then a virtual bus trial in Docker.

File names and part of the outputs are in French because the original article is. Useful names: `rejouer.sh` = replay script, `raw/` = raw outputs, `vcan-clean` = clean vcan run, `COMMANDES.txt` = commands.

## How to replay

- Docker only. Everything runs in images and packages that existed at the date of the article (2025-01-14), pinned by digest in `rejouer.sh`:
  - `python:3.13.1-slim-bookworm` (Python 3.13.1, released 2024-12-03) for `can_frame.py` (pure Python, no library) and for python-can 4.5.0 (2024-11-28; dependencies pinned: wrapt 1.17.1, packaging 24.2, typing_extensions 4.12.2, msgpack 1.1.0);
  - `debian:bookworm-20241223-slim` with `apt` on the Debian snapshot of 2025-01-14 (`https://snapshot.debian.org/archive/debian/20250114T000000Z/`) for the vcan trials: can-utils 2020.11.0-1.
- The bench does not print the kernel version (Docker Desktop's kernel is whatever your Docker Desktop ships): no `uname -r`, `modprobe -q`. `pycan_demo.py` prints timestamps relative to the first send, not wall-clock time.
- No CAN hardware.

Single command:

```bash
bash rejouer.sh
```

It rewrites `raw/01` to `raw/04`. Then compare with the files provided. `bash rejouer.sh refs` downloads the two reference PDFs into `ref/` and checks their sha256.

## File to slide

| File | Slide |
|---|---|
| `can_frame.py` section 2 | 2 (levels of the pair), 5 (19 header bits, frame fields) |
| `can_frame.py` section 3, `raw/02-can_frame.txt` | 4 (three nodes, the lowest ID wins) |
| `can_frame.py` sections 1 and 2, `raw/02-can_frame.txt` lines 1-12 | 6 (stuffing and CRC-15 recomputed) |
| `can_frame.py` section 4, `raw/02-can_frame.txt` | 8 (error counters, a faulty node removes itself) |
| `vcan-try.sh`, `raw/01-vcan-try.txt` | 9 (first vcan trial) |
| `vcan-try2.sh`, `raw/04-vcan-clean.txt` | 9 (vcan: the module does not exist in the Docker Desktop kernel) |
| `pycan_demo.py`, `raw/03-pycan-virtual.txt` | 9 (python-can virtual bus, three transmitters) |
| `raw/COMMANDES.txt` | 9 (exact commands) |

## Third-party data

It is not in this repo. `rejouer.sh refs` downloads the PDFs and checks their sha256 (recorded when the bench was built).

| File | URL | License |
|---|---|---|
| `ref/bosch-can2.pdf` | https://www.nxp.com/docs/en/reference-manual/BCANPSV2.pdf (Bosch CAN 2.0, NXP reissue) | publisher's rights, not redistributed here |
| `ref/sloa101b.pdf` | https://www.ti.com/lit/an/sloa101b/sloa101b.pdf (TI SLOA101B, May 2016) | Texas Instruments' rights, not redistributed here |

Two references are only for reading, with no file downloaded by the script:

- the frame by Ken Tindell (ID 0x014, data 0x01, CRC 0x7753) that `can_frame.py` checks itself against: https://kentindell.github.io/2020/01/03/canframe_py_tool/ , Wikimedia image under CC BY-SA 4.0 license: https://commons.wikimedia.org/wiki/File:CAN-bus-frame-with-stuff-bit-and-correct-CRC.png ;
- the check value of CRC-15/CAN: https://reveng.sourceforge.io/crc-catalogue/1-15.htm (`crc15(b"123456789") = 0x059e`).

Kernel documentation for vcan: https://docs.kernel.org/networking/can.html .

## What is not provided

The crops of Tindell's image (`crop1` to `crop3`) were used to read the bits by hand: they derive from an image under CC BY-SA and are not included.
