# antenne-gain-dbi

This bench goes with the deck https://heurisme.fr/en/blog/antenne-gain-dbi/ : what dBi and dBd mean, and why an antenna "with gain" creates no energy. Four vertical antennas are simulated at 1090 MHz with NEC2 (`nec2c`): a half-wave dipole, a quarter-wave whip with four radials, a 3-element Yagi and an idealised collinear (two half-wave dipoles stacked and fed in phase). The bench prints their maximum gain, their -3 dB beamwidths, checks that the gain averaged over the whole sphere stays at 1 (all input power is radiated, whatever the shape), and works out a rooftop ADS-B example: whip or collinear for aircraft at 10 000 m, from 5 to 300 km away.

File names are in French because the original article is. Useful names: `rejouer.sh` = replay script, `modeles.py` = models (writes the NEC2 input files), `analyse.py` = analysis, `sorties/` = outputs, `travail/` = work folder, `dipole` = dipole, `fouet` = whip, `colineaire` = collinear, `toit` = roof, `gains` = gains, `conservation` = conservation. The outputs themselves are in English.

## How to replay

- Docker only. Nothing to install on the host.
- The container is `debian:bookworm-20261005`, pinned by digest in `rejouer.sh`, in arm64 (remove `--platform linux/arm64` on an x86_64 machine).
- `apt` in the container reads the Debian snapshot of 2026-10-14 (`https://snapshot.debian.org/archive/debian/20261014T000000Z/` and `debian-security`), so the packages are the ones of that day: `nec2c 1.3-4`, Python 3.11.2 (see `sorties/00-versions.txt`).

Single command:

```bash
bash rejouer.sh
```

It writes `nec/*.nec` (`modeles.py`), runs `nec2c` once per antenna into `travail/*.out`, then rewrites `sorties/`. Compare with `git diff`: the outputs are byte for byte the same from one run to the next.

`travail/*.out` (about 8 MB each) is not in this repo: `nec2c` prints its run time in msec in it. Everything the deck shows comes from `sorties/`.

No third-party data: the bench downloads nothing apart from the Debian packages.

## Method

- Free space, perfect conductors, wire radius 1 mm, 1090 MHz (wavelength 275.0 mm). Lengths were tuned once for a feed reactance close to zero; they are fixed in `modeles.py`.
- About 121 segments per wavelength with the extended thin-wire kernel (`EK` card). With 41 segments per wavelength and radials at 45 degrees, the whip, fed at a junction of five wires, gave an average power gain of 1.09: the power check of `analyse.py conservation` is what showed the model was wrong.
- Each `.nec` file asks for four patterns (`RP` cards): two vertical cuts (phi = 0 and 180, 1 degree steps), one horizontal cut (theta = 90, 1 degree steps), and the whole sphere at 1 degree steps with NEC's own average power gain (`XNDA = 1001`).
- `analyse.py conservation` integrates the linear power gain over the sphere itself (trapezoids in theta, sin(theta) weighting, divided by 4 pi). NEC's own sum covers a solid angle of 3.9889 pi and gives 0.9947 for the Yagi where our integral gives 1.0001.
- dBd = dBi - 2.15 (ITU-R BS.1195, Gd = Gi - 2.15 dB).
- Rooftop example (`analyse.py toit`): aircraft at 10 000 m (an example value), spherical Earth of radius 6371 km (NASA Earth Fact Sheet, volumetric mean radius), no refraction, roof height ignored, no ground reflection. Path loss = 20 log10(4 pi d / lambda), the free-space basic transmission loss of ITU-R P.525. "G-L" = antenna gain in the direction of the aircraft minus path loss.

## File to slide

| File | Slide |
|---|---|
| `nec/dipole.nec` | 3 (the NEC2 input cards) |
| `sorties/01-gains.txt` | 2 (dipole at 2.14 dBi), 3 (table), 4 (Yagi), 5 (whip and collinear) |
| `sorties/02-conservation.txt` | 6 (average gain of 1 for all four antennas) |
| `sorties/03-toit.txt` | 5 (collinear dip at 41 degrees), 7 and 8 (rooftop example, angles below the horizon) |
| `sorties/diagrammes.json` | 2, 4, 5 (polar plots) and 7 (G-L curves), drawn by the deck from this file |
| `sorties/00-versions.txt` | 9 (nec2c and Python versions) |
| `modeles.py` | writes `nec/*.nec` |
| `analyse.py` | reads `travail/*.out`, prints the outputs |

## References

- NEC-2 user's guide, part III, cards GW, EX, FR, RP (field XNDA), EK: https://www.nec2.org/
- ITU-R BS.1195, section 3 (directivity, Gi, Gd): https://www.itu.int/rec/R-REC-BS.1195/en
- ITU-R P.525, free-space attenuation: https://www.itu.int/rec/R-REC-P.525/en
- NASA Earth Fact Sheet: https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html
