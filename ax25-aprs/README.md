# AX.25 / APRS bench

This bench goes with the deck https://heurisme.fr/en/blog/ax25-aprs/ : an APRS frame built byte by byte, its FCS recomputed, the 1200 baud AFSK signal demodulated by hand, a Dire Wolf digipeater and the switch to KISS over TCP.

File names and part of the outputs are in French because the original article is. Useful names: `rejouer.sh` = replay script, `raw/` = raw outputs, `work/` = working directory, `00-versions` = versions, `01-aller-retour` = round trip, `03-trame-digi` = digipeated frame, `06-noyau` = kernel, `COMMANDES.txt` = commands.

## How to replay

- Docker, for the `debian:trixie-20251117` container in arm64 (pinned by digest in `rejouer.sh`). On x86_64, remove `--platform linux/arm64` in `rejouer.sh`.
- `apt` in the container reads the Debian snapshot of 2025-12-09, the date of the article (`https://snapshot.debian.org/archive/debian/20251209T000000Z/` and `debian-security`), so the packages are the ones of that day: Debian 13.2, Dire Wolf 1.7 (package `1.7+dfsg-2+b3`), Python 3.13.5, numpy 2.2.4, pv.
- The bench does not print the kernel version (Docker Desktop's kernel is whatever your Docker Desktop ships). `raw/06` uses `modprobe -q` for that reason; the result does not depend on it as long as the kernel has no `ax25` module.
- Nothing to install on the host machine apart from Docker.

Single command:

```bash
bash rejouer.sh
```

It recreates the container, reruns the commands of `raw/COMMANDES.txt`, rewrites `raw/00` to `raw/07` and `work/signal.json`. Then compare with the files provided. Decoding durations (`x realtime`) vary from run to run.

`bash rejouer.sh refs` downloads the third-party references into `ref/` and checks their sha256 (see below). It is not needed to replay the bench.

## Layout

The names cited by the deck are the ones in this folder. The deck writes `ax25_frame.py`, `kiss.conf`, `p1.wav` without a prefix: they live in `work/`, the working directory of the commands. `ax25_frame.py` finds `raw/` and `work/` from its own path, wherever it is launched from (outside the container, `python3 work/ax25_frame.py` with numpy is enough; the WAV files provided are sufficient).

## File to slide

| File | Slide |
|---|---|
| `raw/00-versions.txt` (`.ansi`: raw output with Dire Wolf colours) | versions cited throughout the deck |
| `work/p1.txt`, `work/p1.wav`, `raw/01-aller-retour.txt` | 2 (frame fields), 3 (address bytes) |
| `work/ax25_frame.py`, `raw/07-ax25_frame.txt` | 3, 4 (FCS redone by hand), 5 (demodulation), 6 (control bytes of connected mode) |
| `work/signal.json` | 5 (instantaneous frequency plotted on the slide) |
| `work/digi.conf`, `work/p3.txt`, `raw/02-digi.txt` | 7 (a digipeater consumes one hop) |
| `work/p2.txt`, `raw/03-trame-digi.txt` | 7 (byte `e2`, H bit) |
| `raw/02-digi.txt` (lines 34 and 37) | 8 (decoded APRS position) |
| `work/kiss.conf`, `work/kiss_client.py`, `raw/05-kiss.txt` | 9 (KISS over TCP) |
| `work/p9600.wav`, `raw/04-9600.txt` | 9 (9600 baud, descrambler) |
| `raw/06-noyau.txt` | 9 (the Docker kernel has no `ax25` module) |
| `run.sh` | chains the commands of outputs 00 to 05 |

## Callsigns

`F1TMV-7` is the author's real amateur radio callsign, published at his request. `N0CALL-1`, `N0CALL-2` and `N0CALL-3` are fictitious, `APRS`, `WIDE1-1` and `WIDE2-1` are generic aliases. The position is the example from the APRS specification (4903.50N/07201.75W).

## Third-party data

It is not in this repo. `rejouer.sh refs` downloads it into `ref/` and checks its sha256 (recorded when the bench was built). The files on `master` were last changed before 2025-12-09.

| File | URL | License |
|---|---|---|
| `APRS101.pdf` | https://raw.githubusercontent.com/wb2osz/aprsspec/main/APRS101.pdf | not stated in the file |
| `APRS12c.pdf` | https://raw.githubusercontent.com/wb2osz/aprsspec/main/APRS12c.pdf | not stated in the file |
| `APRS-Digipeater-Algorithm.pdf` | https://raw.githubusercontent.com/wb2osz/aprsspec/main/APRS-Digipeater-Algorithm.pdf | not stated in the file |
| `ax25-2.2.pdf` | https://www.ax25.net/AX25.2.2-Jul%2098-2.pdf | not stated (AX.25 v2.2, TAPR/ARRL) |
| `User-Guide.pdf` | https://raw.githubusercontent.com/wb2osz/direwolf/master/doc/User-Guide.pdf | Dire Wolf, GPL v2 or later |
| `kiss.aspx` | http://www.ax25.net/kiss.aspx | not stated (KISS, Chepponis and Karn, 1987) |
| `hdlc_send.c`, `fcs_calc.c`, `demod_9600.h` | https://github.com/wb2osz/direwolf/tree/master/src (files `raw.githubusercontent.com/wb2osz/direwolf/master/src/…`) | Dire Wolf, GPL v2 or later |

The expected sha256 values are in `rejouer.sh`. The Dire Wolf `master` files move: if a sha256 differs, the script stops, and `TOLERE=1 bash rejouer.sh refs` carries on anyway (`TOLERE` = tolerate). Dire Wolf itself (Debian package) is installed in the container by `apt`.

## What is not provided

The WAV files `p2.wav` and `p3.wav` (same size as `p1.wav`) can be regenerated with `gen_packets`. No exchange in connected mode was run: slide 6 is a diagram based on the standard, only the control bytes are computed by `ax25_frame.py`.
