# DMX512: 512 bytes on one pair

Bench for the deck https://heurisme.fr/en/blog/dmx512-512-octets/ . No signal was measured, for lack of hardware: the script computes the frame durations, builds in memory a DMX frame, an Art-Net packet, an sACN packet and an ENTTEC message, then sends the two network packets to `127.0.0.1` only and decodes them.

File names and part of the outputs are in French because the original article is. Useful names: `rejouer.sh` = replay script, `sorties/` = outputs, `dmx_calc.py` = the calculation script, `dmx_calc.out` = its full output.

## What you need to replay

- Python 3 (tested with 3.13.8), standard library only.
- `bash`, `curl` and `shasum` for `rejouer.sh` (macOS or Linux with `shasum`).
- UDP ports 6454 and 5568 free on `127.0.0.1`.

## Replay everything

```bash
bash rejouer.sh
```

The script downloads the cited OLA sources into `src/`, checks their sha256, then runs `python3 dmx_calc.py > sorties/dmx_calc.out`.

## File to slide

| File | Slide |
|---|---|
| `dmx_calc.py`, section 1 (frame duration, refresh rate) | 5 "Fewer slots, more frames per second" |
| `dmx_calc.py`, section 2 (patch of 3 fixtures, 24-slot frame) | 6 and 7 "Each fixture reads its slots from its address", "Patching three fixtures, byte by byte" |
| `dmx_calc.py`, sections 3 and 4 (Art-Net and sACN packets, local round trip) | 10 "From XLR cable to UDP, the same universe" |
| `dmx_calc.py`, section 5 (ENTTEC label 6 message) | 11 "From code, the BREAK is the tricky part" |
| `sorties/dmx_calc.out` | full output of the script, the one whose values the slides reuse |
| `src/RDMEnums.h`, `src/UID.h`, `src/RDMPacket.h` | 9 "RDM: the same pair, in both directions" (downloaded) |
| `src/FtdiDmxThread.cpp` | 11 (OLA excerpt about the BREAK, downloaded) |

## Third-party data (downloaded, not copied into the repo)

Repo OpenLightingProject/ola, pinned at commit `cf52b2a58dffec1a28b4c8f19556e99f7134316a` (2025-09-20), LGPL license: https://github.com/OpenLightingProject/ola

| Local file | URL | sha256 |
|---|---|---|
| `src/RDMEnums.h` | https://raw.githubusercontent.com/OpenLightingProject/ola/cf52b2a58dffec1a28b4c8f19556e99f7134316a/include/ola/rdm/RDMEnums.h | `42e0f985be8fb47ac96c1d89b381f3db561335b6bb1a7c795d0da4fac8134642` |
| `src/UID.h` | https://raw.githubusercontent.com/OpenLightingProject/ola/cf52b2a58dffec1a28b4c8f19556e99f7134316a/include/ola/rdm/UID.h | `a83de8b44e5dd8ca213145fb30a7638d889cae98e7f2b59df6a601bbe8c06ac7` |
| `src/RDMPacket.h` | https://raw.githubusercontent.com/OpenLightingProject/ola/cf52b2a58dffec1a28b4c8f19556e99f7134316a/include/ola/rdm/RDMPacket.h | `43a1869b3c06feb76d9dd651a3f09372011504cc11ddbac61e0cad355817a5b7` |
| `src/FtdiDmxThread.cpp` | https://raw.githubusercontent.com/OpenLightingProject/ola/cf52b2a58dffec1a28b4c8f19556e99f7134316a/plugins/ftdidmx/FtdiDmxThread.cpp | `c2ec347a30469a7e6526198c75dfa6e64cdd1b2cae9ac2f3137e7709c312fced` |

If a file differed from the pinned commit, the sha256 would no longer match and `rejouer.sh` stops with a message.

The standards and documents cited by the deck are not in this repo and are not read by the script: ANSI E1.11-2004, E1.20, E1.31-2016 (https://tsp.esta.org), Art-Net 4 (https://art-net.org.uk/downloads/art-net.pdf), ENTTEC DMX USB Pro API v1.44 (https://support.enttec.com). The values in the script come from the tables of these documents, cited at the top of `dmx_calc.py`.
