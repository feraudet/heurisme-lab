# antenne-quart-onde

This bench goes with the deck https://heurisme.fr/en/blog/antenne-quart-onde/ : why the vertical element of a 868 MHz LoRa ground plane antenna is cut at about 8 cm, and not at the quarter wave of 8.63 cm. Nothing was measured on a real antenna: every figure comes from NEC2 (`nec2c`), the method-of-moments wire antenna code, run on simple wire models.

File names are in French because the original article is. Useful names: `rejouer.sh` = replay script, `modele.py` = model (writes the NEC2 input decks), `analyse.py` = analysis, `sorties/` = outputs, `longueur` = length, `epaisseur` = wire thickness, `radians` = radials, `passerelle` = gateway. The outputs themselves are in English.

## How to replay

- Python 3.9 or later, standard library only.
- Docker. `nec2c` runs in `debian:bookworm` pinned by digest, and is installed from snapshot.debian.org at the date 2026-10-10.

Single command:

```bash
bash rejouer.sh
```

It rewrites the four decks of `nec/` (`modele.py`), runs `nec2c` on each of them inside the container (raw outputs in `raw/`, not in this repo: they carry the run time), then rewrites `sorties/01-longueur.txt` to `sorties/04-passerelle.txt` (`analyse.py`). Compare with `git diff`: the `.nec` files and the outputs should not change.

| Tool | Version | Where it comes from |
|---|---|---|
| Docker image | `debian@sha256:2c037a04925515fdd6ea85ea14a682d0e79931f5e9f5d07b6dbfc6ba12f9e858` (debian:bookworm, built 2026-10-05) | Docker Hub |
| nec2c | 1.3-4 | `http://snapshot.debian.org/archive/debian/20261010T000000Z bookworm main` |

sha256 of the package as served by snapshot.debian.org: `nec2c_1.3-4_amd64.deb` `157eb7d3b048fe867c3d748eac75dd8c784f8cd96fb89a2692f9bc0bf16209aa`, `nec2c_1.3-4_arm64.deb` `e94caaca5277dba28a90f36a2873a4d48ba02adf8a1af240efbf80d6a6058325`. The outputs of this folder were produced on arm64.

## The models

All wires are perfect conductors (no loss), in metres, feed point at the origin, vertical element along +z, 15 segments per wire, excitation on the first segment of the vertical (`EX 0 1 1`), one structure per length or angle, separated by `NX` cards. Frequency: 868 MHz (the three default LoRaWAN EU863-870 channels are 868.1, 868.3 and 868.5 MHz).

- `nec/01-longueur.nec`: monopole over a perfect ground plane (`GE 1`, `GN 1`), wire 1 mm in diameter, length 7.6 to 8.8 cm by 0.1 cm.
- `nec/02-epaisseur.nec`: the same, length 7.0 to 9.0 cm, for wire diameters 0.5, 1, 1.5 and 2 mm.
- `nec/03-radians.nec`: ground plane antenna in free space (`GE 0`): the vertical plus 4 radials of 8.6 cm, drooping 0, 15, 30, 45 and 60 degrees below horizontal, length 7.0 to 9.0 cm.
- `nec/04-passerelle.nec`: the gateway antenna, radials at 45 degrees, vertical cut at 7.8 cm and at 8.6 cm, swept from 856 to 880 MHz by 2 MHz.

The resonant length (reactance X = 0) is found by linear interpolation between the two lengths where X changes sign. SWR is computed on 50 ohm: `G = |(Z - 50) / (Z + 50)|`, `SWR = (1 + G) / (1 - G)`, return loss `-20 log10 G`, mismatch loss `-10 log10 (1 - G^2)`.

What the models leave out: the coax and the mast (no current on the outside of the braid), the connector, the real ground under the antenna, conductor loss, insulation on the wire.

Segmentation: a segment is about 5.3 mm long (0.015 wavelength). For the 1 mm wire, segment length / radius is about 10, above the value of 8 the NEC-2 user's guide gives for errors below 1 % with the thin-wire kernel. For the 2 mm wire it is about 5. Running `modele.py` with 9 and with 25 segments per wire moves the resonant lengths of `sorties/` by 0.04 cm at most and the resistances by 0.6 ohm at most.

## File to slide

| File | Slide |
|---|---|
| `modele.py` | 2 (wavelength and quarter wave at 868 MHz) |
| `sorties/01-longueur.txt` | 3 (X = 0 at 8.14 cm, R = 35.9 ohm on a perfect ground plane) |
| `sorties/02-epaisseur.txt` | 4 (resonant length from 8.22 cm to 8.03 cm as the wire gets thicker) |
| `sorties/03-radians.txt` | 5 (flat radials: 24.2 ohm) and 6 (45 degrees: 51.1 ohm, SWR 1.02) |
| `sorties/04-passerelle.txt` | 7 (gateway antenna cut at 7.8 cm and at 8.6 cm) |

## References

- NEC-2 Manual, Part III: User's Guide (G. J. Burke, A. J. Poggio), for the cards `GW`, `GE`, `GN`, `EX`, `FR`, `PT`, `XQ`, `NX`: https://www.nec2.org/other/nec2prt3.pdf
- nec2c in Debian: https://packages.debian.org/bookworm/nec2c

No third-party data is used: the bench only runs nec2c on models written by `modele.py`.
