# The GPS takes 30 seconds to know where it is

Bench for the deck https://heurisme.fr/en/blog/gps-premier-fix/ : two public NMEA logs (a Telit HE910 cellular module, a u-blox RX210 receiver) decoded by a hand-written decoder, `banc/nmea.py`, then cross-checked with the pynmea2 library. There is no real receiver in this bench.

File names and part of the outputs are in French because the original article is. Useful names: `banc/` = bench, `rejouer.sh` = replay script, `sorties/` = outputs in French (`sorties-en/` = outputs in English), `champs` = fields, `chrono` = timeline, `vide` = empty (no fix), `avant` / `apres` = before / after, `cherche_logs.py` = log finder.

## What you need

- Docker (image `python:3.12.12-slim`)
- `curl` and `shasum` (or `sha256sum`)
- network access: for the two logs, and for `pip install pynmea2==1.19.0` in the container at every run

`nmea.py` only uses the Python standard library.

## Replay everything

```bash
bash banc/rejouer.sh
```

The script downloads the two logs into `banc/logs/` (pinned gpsd commit), checks their sha256, then runs twice: in French in `banc/sorties/`, in English in `banc/sorties-en/` (`--en` option). One output per command.

## File to slide

| File | Produces | Slide |
|---|---|---|
| `banc/nmea.py chrono` | `banc/sorties/chrono-telit.txt`, `chrono-rx210.txt`: cycles, tracked satellites, first fix | 2, 7, 10 |
| `banc/verif_pynmea2.py` | `banc/sorties/pynmea2.txt`: cross-check with pynmea2 | 2 |
| `banc/nmea.py checksum` | `checksum-gga-vide.txt`, `checksum-gga-fix.txt`: XOR of the characters between `$` and `*` | 3 |
| `banc/nmea.py champs` | `champs-gga-vide.txt`, `champs-gga-fix.txt`: GGA fields | 4 |
| `banc/nmea.py champs` | `champs-rmc-vide.txt`, `champs-rmc-fix.txt`, `champs-gsa-vide.txt`, `champs-gsa-fix.txt` | 5 |
| `banc/nmea.py champs` | `champs-gsv-avant.txt`, `champs-gsv-apres-1.txt`, `champs-gsv-apres-2.txt` | 6 |
| `sed -n` on `telit-he910.log` | `telit-autour-du-fix.txt`: lines 246 to 262 | 6 |
| `grep -n uptime` on `rx210.log` | `rx210-uptime.txt`: the proprietary sentence that gives the uptime | 10 |
| `banc/cherche_logs.py` | the sort used to pick the gpsd logs (GGA going from quality 0 to a fix) | not on a slide |

The Telit has no time before the fix: "about 37 s" is an estimate (37 cycles of 1 s). The RX210 is not a cold start: its uptime is 9 minutes.

## Third-party data (downloaded, not copied here)

Both logs come from gpsd, folder `test/daemon/`, at commit `f6f1088671cfe9da7075bedd4639046672e05a8e`. Their header says: BSD license, see `COPYING` in gpsd.

- `telit-he910.log`: https://gitlab.com/gpsd/gpsd/-/raw/f6f1088671cfe9da7075bedd4639046672e05a8e/test/daemon/telit-he910.log
  - sha256 `784c3be18d97cb8aa5d5995146c06e9d720519f79bdd7c37b99a6e4fd2bcb0cf`
- `rx210.log`: https://gitlab.com/gpsd/gpsd/-/raw/f6f1088671cfe9da7075bedd4639046672e05a8e/test/daemon/rx210.log
  - sha256 `82aaf0a0c3342e5033f2cc9af060d32e85ead338a67d1098371917232f53db93`

Documents cited by the deck, to be read at the publisher (not used by the script):

- IS-GPS-200N (1 August 2022): https://www.gps.gov/sites/default/files/2025-07/IS-GPS-200N.pdf (sha256 `54ec544bfe7e6acd97daaa1de0ca248e5abec6b418f23c1a69991e5c7bcf749a`)
- GPS Compendium GPS-X-02007-D (u-blox): https://content.u-blox.com/sites/default/files/products/documents/GPS-Compendium_Book_%28GPS-X-02007%29.pdf (sha256 `be67e4421e118b7e28a560f11d7531b494a874eacd9dffe73545c808d82d93b5`)
- "NMEA Revealed" (gpsd): https://gpsd.gitlab.io/gpsd/NMEA.html
- pynmea2 1.19.0, installed from PyPI at every run
