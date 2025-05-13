# LoRa: airtime

Bench of the deck https://heurisme.fr/en/blog/lora-temps-antenne/ . Nothing was measured on a radio: `airtime.py` computes packet durations from the SX1276 datasheet formula, compares them with the tests of a published calculator, and derives the airtime budgets (1% ETSI, TTN Fair Use Policy).

File names and part of the outputs are in French because the original article is. Useful names: `rejouer.sh` = replay script, `raw/` = raw outputs, `temps-antenne` = airtime, `attente` = wait, `msg/j FUP` = messages per day under the FUP.

## What you need to replay

- Python 3 (tested with 3.13.3), standard library only.
- `bash`, `curl` and `shasum` for `rejouer.sh`.

## Replay everything

```bash
bash rejouer.sh
```

The script downloads the calculator and the cited documents into `raw/`, checks their sha256, then runs `python3 airtime.py > raw/airtime.out`. The result is identical to the `raw/airtime.out` provided here (`raw/airtime.cmd` records the command and the Python version).

## File to slide

| File | Slide |
|---|---|
| `airtime.py`, `raw/airtime.out` | 3 and 4 (symbol and packet durations by SF), 5 "At SF12, 20 bytes occupy the antenna for 1.32 s", 7 and 8 (1% per hour, messages per hour), 9 (TTN Fair Use Policy) |
| `raw/airtime.out` | 6 "The script falls back on a published calculator" (full output, including the check against the tests) |
| `raw/Airtime.ts` | 5 (the comment on the 13 LoRaWAN header bytes, downloaded) |
| `raw/Airtime.test.ts` | 6 (expected values, cited in the deck under its original path `src/lora/Airtime.test.ts`, downloaded) |
| `raw/SX1276_Datasheet.pdf` | 2 to 4 (formula section 4.1.1.7, downloaded) |
| `raw/RP002-1.0.3.pdf`, `raw/en_30022001v030101p.pdf`, `raw/en_30022002v030201p.pdf`, `raw/Reverse_Eng_Report.pdf` | 2, 3, 5 and 7 (downloaded) |

## Third-party data (downloaded, not copied into the repo)

| Local file | Original URL | sha256 |
|---|---|---|
| `raw/Airtime.ts` (avbentem calculator, license of the original repo) | https://raw.githubusercontent.com/avbentem/airtime-calculator/af41bc53c7ce61da27237ba24756ebcf94314440/src/lora/Airtime.ts | `bdab86547bad3fd5e2d66fe3ac49ddee1e64fb1062542bba57b6d913a3afd5e2` |
| `raw/Airtime.test.ts` | https://raw.githubusercontent.com/avbentem/airtime-calculator/af41bc53c7ce61da27237ba24756ebcf94314440/src/lora/Airtime.test.ts | `e4b66d51720f13343d5f92f5f36cd106f9c4e57eda6bcf94c839700cebad37f6` |
| `raw/SX1276_Datasheet.pdf` (Semtech, Rev. 7) | https://cdn.sparkfun.com/assets/7/7/3/2/2/SX1276_Datasheet.pdf | `330745f933df00015d2de3efd582608339350ba3a21001d11b9d449839ce016b` |
| `raw/RP002-1.0.3.pdf` (LoRa Alliance) | https://lora-alliance.org/wp-content/uploads/2021/05/RP002-1.0.3-FINAL-1.pdf | `7babdb743e051fdc86bce8fdf99716c4f275da6b31f6495ccba9ce956373715c` |
| `raw/en_30022001v030101p.pdf` (ETSI EN 300 220-1 V3.1.1) | https://www.etsi.org/deliver/etsi_en/300200_300299/30022001/03.01.01_60/en_30022001v030101p.pdf | `42e0b9924e63c64f4e0606b716635946e2b36f7c5ced5dbf128222d02c022178` |
| `raw/en_30022002v030201p.pdf` (ETSI EN 300 220-2 V3.2.1) | https://www.etsi.org/deliver/etsi_en/300200_300299/30022002/03.02.01_60/en_30022002v030201p.pdf | `df54e88af3879f143d1d22cfbe3cc90657b0fecd85c2afb054f1ba79c67ec2e3` |
| `raw/Reverse_Eng_Report.pdf` (J. Tapparel, EPFL) | https://www.epfl.ch/labs/tcl/wp-content/uploads/2020/02/Reverse_Eng_Report.pdf | `63142f77b27260b4adb99d3997ca16bbde0988df970fe3ea9f1433a596105432` |

These documents remain the property of their authors: they are downloaded from their publisher, never redistributed here. The TTN pages cited by the deck (Fair Use Policy, ADR) are online at https://www.thethingsnetwork.org/docs/lorawan/ and are not downloaded.
