# cable-coaxial-pertes

This bench goes with the deck https://heurisme.fr/en/blog/cable-coaxial-pertes/ : how much signal a coax loses between the antenna and the receiver, at 144, 868 and 1090 MHz, for RG174, RG58, RG213 and LMR-400, and what that loss does to the noise figure of an ADS-B receiver with its antenna on the roof and 15 m of cable down to a Raspberry Pi.

File names are in French because the original article is. Useful names: `rejouer.sh` = replay script, `pertes.py` = losses, `fiches.py` = datasheets (the figures transcribed from them), `sorties/` = outputs, `hors-ligne` = offline. The outputs themselves are in English.

## How to replay

- Python 3.9 or later, standard library only. Nothing to install.
- `curl` and network access, only to download the datasheets and check them.

Single command:

```bash
bash rejouer.sh
```

It downloads the ten PDFs listed in `sources-sha256.txt` into `raw/`, checks their sha256, then rewrites `sorties/01-db.txt` to `sorties/05-bruit.txt`. Compare with the files provided.

`bash rejouer.sh hors-ligne` skips the download: the calculation itself needs no network, since the figures it uses are in `fiches.py`.

## What is computed, and how

- **Decibels** (`01-db.txt`): a loss of x dB leaves 10^(-x/10) of the power (ITU-R V.574, 10 lg(P1/P2)). 3 dB leaves 50.1 %.
- **Datasheet model** (`02-fiches.txt`): cable loss in dB per length grows roughly like a·√f (conductor loss, skin effect) plus b·f (dielectric loss). For LMR-400, Times Microwave gives this formula on the datasheet itself (a = 0.122290, b = 0.000260, in dB/100 ft). For the Belden cables, `pertes.py` fits a and b by least squares on the datasheet points from 50 MHz up, and prints the gap between the model and each datasheet point.
- **Table** (`03-tableau.txt`): the model at 144, 868 and 1090 MHz, in dB/100 m (1 dB/100 ft = 3.28084 dB/100 m), then the loss of 15 m. A second column checks the model with a straight line in log-log between the two datasheet points around the frequency. The Belden RG174 and RG58 tables stop at 1000 MHz: their 1090 MHz value is an extrapolation (9 % past the last point), flagged as such. The RG213 table goes to 4000 MHz and the LMR-400 table to 8000 MHz.
- **ADS-B example** (`04-adsb.txt`): 1090 MHz, 5 to 20 m of each cable, plus two connectors at their maximum datasheet insertion loss (an N plug at the antenna, an SMA plug at the receiver), compared with the gain of a 5.5 dBi antenna over a half-wave dipole (2.15 dBi, ITU-R BS.1195-1, eq. 6).
- **Noise figure** (`05-bruit.txt`): ITU-R P.372, eq. (1) and (5): a line of loss lt at 290 K in front of a receiver of noise factor fr gives a noise factor lt·fr, so the cable loss in dB adds directly to the receiver noise figure. With an LNA in front, the Friis cascade F = F1 + (F2 − 1)/G1 applies. LNA: Mini-Circuits PSA4-5043+, typical NF 0.75 dB and gain 18.4 dB at 1.0 GHz (5 V). The receiver noise figure is an assumption (3, 5 and 8 dB): the bench uses no datasheet value for the receiver.

Only the noise added by the installation is counted. The noise picked up by the antenna itself (ITU-R P.372, fa) comes on top and is the same in every case.

## File to slide

| File | Slide |
|---|---|
| `sorties/01-db.txt` | 2 (3 dB is half the power) |
| `sorties/02-fiches.txt` | 3 (datasheet points and model) |
| `sorties/03-tableau.txt` | 4 (four cables at 144, 868 and 1090 MHz) |
| `sorties/04-adsb.txt` | 5 (connectors), 6 (15 m of RG58 against the antenna gain) |
| `sorties/05-bruit.txt` | 7 (noise figure, LNA at the top of the mast) |
| `fiches.py` | figures transcribed from the datasheets |
| `pertes.py` | prints the five outputs |

## Third-party data

The PDFs are not in this repo: only their address and sha256 are, in `sources-sha256.txt`. `fiches.py` holds the few figures the bench uses, each with the datasheet, page and table it comes from; compare them with the PDFs in `raw/` after `bash rejouer.sh`.

- Belden 8240 (RG-58), 8216 (RG-174), 8267 (RG-213): catalog.belden.com, revision date 02-20-2026.
- Times Microwave LMR-400: the Times website refuses automated downloads (HTTP 403), so the bench downloads the same catalog pages from the distributor Talley (talleycom.com). The official page is https://www.timesmicrowave.com/DataSheets/CableProducts/LMR-400.pdf.
- Rosenberger 53S107-106N5 (N plug, RG 58 C/U) and 32S107-307L5 (SMA plug): Rosenberger datasheets as hosted by RS Components.
- Mini-Circuits PSA4-5043+: minicircuits.com.
- ITU-R P.372-18, V.574-5, BS.1195-1: itu.int.
- FlightAware 1090 MHz antenna, 5.5 dBi: product page https://flightaware.store/products/antenna-1090mhz (HTML, no sha256).

Each document keeps the terms of its publisher.
