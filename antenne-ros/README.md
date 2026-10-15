# antenne-ros

This bench goes with the deck https://heurisme.fr/en/blog/antenne-ros/ : what happens when an antenna is not 50 ohms. Reflection coefficient, SWR, return loss and reflected power for a few loads; a quarter-wave ground plane for 144.800 MHz (the APRS frequency in IARU Region 1) simulated with NEC2 at six lengths of its vertical element; and what the SWR meter at the transmitter shows at the end of 20 m of coax.

File names are in French because the original article is. Useful names: `rejouer.sh` = replay script, `calcule.sh` = compute (runs in the container), `antenne.py` = antenna (writes the NEC2 decks), `lit_nec.py` = reads the nec2c outputs, `ros.py` = SWR (French: ROS, *rapport d'ondes stationnaires*), `sorties/` = outputs. The outputs themselves are in English.

## How to replay

- Docker, for the `debian:bookworm-20261005` container in arm64 (pinned by digest in `rejouer.sh`). On x86_64, remove `--platform linux/arm64` in `rejouer.sh`.
- `apt` in the container reads the Debian snapshot of 2026-10-14 (`https://snapshot.debian.org/archive/debian/20261014T000000Z/`), so the packages are the ones of that day: nec2c `1.3-4`, Python `3.11.2` (see `sorties/00-versions.txt`).
- Nothing to install on the host machine apart from Docker. The Python scripts use the standard library only.

Single command:

```bash
bash rejouer.sh
```

It recreates the container, writes the NEC2 decks `nec/gp-*.nec` (`antenne.py`), runs `nec2c -i nec/gp-<length>cm.nec -o nec/gp-<length>cm.out` on each, then rewrites `sorties/01-ros.txt`, `sorties/02-nec.txt` and `sorties/03-cable.txt`. Compare with the files provided: they come out byte for byte. The raw `nec/*.out` files are not in the repo because nec2c prints its run time in them; the outputs in `sorties/` do not.

## The model

- Quarter-wave ground plane: one vertical element (the radiating rod) and four radials of 52 cm drooping 45 degrees, all 3 mm in diameter, perfect conductor, free space (`GE 0`), fed at the base of the rod (`EX 0 1 1`).
- Six lengths of the rod: 44.0, 46.0, 47.4, 49.0, 51.8 and 54.0 cm. 51.8 cm is the textbook quarter wave at 144.8 MHz (c / f / 4); 47.4 cm is the length that resonates at 144.6 MHz in this model.
- Each deck asks for the input impedance from 140 to 150 MHz every 0.2 MHz (`FR 0 51 0 0 140.0 0.2`, `XQ`), then a vertical cut of the pattern at 144.8 MHz (`RP 0 37 1 1000 0 0 5 0`, power gain).
- Card reference: NEC-2 manual, part III, https://nec2.org/part_3/cards/

## The cables

The attenuation of each cable at 144.8 MHz comes from the manufacturer's data sheet, not from a generic table:

| Cable | Data sheet | What the bench uses |
|---|---|---|
| RG-58, Belden 8240 | https://catalog.belden.com/techdata/en/8240_techdata.pdf (served gzip-compressed; sha256 of the decompressed PDF on 2026-10-15: `cc9bc1419ad3f21a46c049f0f859ae42ddc5bae3f6abd63a48abc34630b1ff23`) | 3.8 dB/100 ft at 100 MHz and 5.6 dB/100 ft at 200 MHz; in between, `a*sqrt(f) + b*f` fitted through these two points: 4.67 dB/100 ft at 144.8 MHz. Velocity of propagation 66 %. |
| LMR-400, Times Microwave | https://www.talleycom.com/images/pdf/lmr400.pdf (Times Microwave data sheet as served by the distributor Talley; sha256 on 2026-10-15: `c3b84312e70e997f95b308730fa0b3c4fb47eff3f95e674888be9b9225a5c409`) | the formula of the data sheet, `0.122290*sqrt(F) + 0.000260*F` dB/100 ft: 1.51 dB/100 ft at 144.8 MHz. Velocity of propagation 84 %. |

The transmitter (25 W forward) and the 20 m of coax are the hypotheses of the deck. The transmitter is assumed not to re-reflect the power that comes back (no tuner).

## File to slide

| File | Slide |
|---|---|
| `sorties/01-ros.txt` | 3 (gamma, SWR, return loss, reflected power), 4 (standing wave maxima every 68.3 cm in RG-58), 5 (mismatch loss) |
| `sorties/02-nec.txt` | 6 (impedance and SWR vs rod length, SWR vs frequency, gain) |
| `sorties/03-cable.txt` | 7 (SWR at the antenna and at the transmitter, 20 m of RG-58 and LMR-400), 8 (disconnected antenna vs cable length) |
| `nec/gp-*.nec` | the NEC2 decks, written by `antenne.py` |
| `sorties/00-versions.txt` | versions of nec2c and Python in the container |

## Third-party data

None is copied here. The two cable data sheets above are cited by address and sha256 only (license: that of their publishers). The IARU Region 1 VHF band plan (144.800 MHz APRS) is at https://www.iaru-r1.org/wp-content/uploads/2020/12/VHF-Bandplan.pdf (sha256 on 2026-10-15: `f99ab6dce8aa40a435cf6101530580b142405d383de1fd953e455d418ce7f6c7`).
