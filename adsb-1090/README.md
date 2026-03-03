# ADS-B at 1090 MHz

Bench for the deck https://heurisme.fr/en/blog/adsb-1090/ : hand decoding of a 112-bit ADS-B message (fields, CRC, identification, altitude, CPR position, speed), then demodulation of a real IQ file from dump1090. No radio: the only real signal is `modes1.bin`.

File names and part of the outputs are in French because the original article is. Useful names: `banc/` = bench, `rejouer.sh` = replay script, `sorties/` = outputs, `donnees/` = data (downloaded).

## What you need

- Docker (image `python:3.12.12-slim` with `pyModeS 2.21.1` and `numpy 2.2.6`)
- `curl` and `shasum` (or `sha256sum`)
- network access for the first run

## Replay everything

```bash
cd banc && sh rejouer.sh
```

The script downloads `modes1.bin` into `donnees/`, checks its sha256, builds the `adsb-banc` image, then rewrites all the outputs in `banc/sorties/`.

## File to slide

Script and output names are the ones used in the deck, relative to `banc/`.

| File | Produces | Slide |
|---|---|---|
| `adsb_pymodes.py` | `sorties/03-pymodes.txt`: agreement between the hand decoding and pyModeS | 2 |
| `demod_iq.py` | `sorties/02-demod.txt` (full list of messages) and `sorties/extrait.json` (preamble samples) | 3, 4, 10 |
| `demod_iq.py --court` | `sorties/02b-demod-court.txt`: excerpt of the list | 4 |
| `adsb_main.py 1 2` | `sorties/05-champs-crc.txt`: fields and CRC (generator 1FFF409) | 5, 6 |
| `adsb_main.py 3 4` | `sorties/06-ident-alt.txt`: callsign and altitude (Q bit) | 7 |
| `adsb_main.py 5` | `sorties/07-cpr.txt`: CPR position step by step | 8 |
| `paire_cpr.py` | `sorties/04-paire.txt`: close pair and old pair | 9 |
| `adsb_main.py 6` | `sorties/08-vitesse.txt`: speed, heading, climb rate | 10 |
| `Dockerfile`, `sorties/00-versions.txt` | Python and numpy versions | 11 |

`sorties/01-main.txt` is the output of `adsb_main.py` with no argument (all sections).

The demodulator is minimal: comparison of the two half-bits, simple thresholds, no error correction. The IQ file is clearly spliced end to end, so its internal times are not real time.

## Third-party data (downloaded, not copied here)

- `modes1.bin` (713,736 bytes, 8-bit IQ, 2 MS/s) from the repo https://github.com/antirez/dump1090 (BSD license, see the repo)
  - https://github.com/antirez/dump1090/raw/master/testfiles/modes1.bin
  - sha256 `3a33e16025da8669149c780075950b4e908ca036ea21f9583c113f60d5fb3094`

Source of the message formats, read online and not copied: https://mode-s.org/1090mhz/ (Junzi Sun, "The 1090 Megahertz Riddle").
