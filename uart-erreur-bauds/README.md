# UART at 115200 baud, within 2 %

Bench for the deck https://heurisme.fr/en/blog/uart-erreur-bauds/ : an ATmega UART receiver simulated from the datasheet (3-sample vote), two real UART captures decoded by `sigrok-cli` at wrong baud rates, and the calculation of divider errors depending on the crystal.

File names and part of the outputs are in French because the original article is. Useful names: `rejouer.sh` = replay script, `sorties/` = outputs (French; the English ones are in `sorties/en/`), `donnees/` = data (downloaded), `compte.py` = counter, `sim-trame` = frame, `sim-derive` = drift, `sim-seuils` = thresholds, `sim-quartz` = crystal, `sim-pc` = PC vs ATmega, `sim-deux-avr` = two ATmegas.

## What you need

- Docker (container `debian:bookworm-slim` with `sigrok-cli 0.7.2`, `libsigrokdecode 0.5.3`, `libsigrok 0.5.2`, Python 3.11)
- `curl` and `shasum` (or `sha256sum`)
- network access for the first run

## Replay everything

```bash
bash banc/rejouer.sh
```

The script downloads the two captures into `donnees/` (pinned sigrok-dumps commit), checks their sha256, builds the `banc-uart` image, then rewrites the outputs: in French in `banc/sorties/`, in English in `banc/sorties/en/` (`--en` option).

## File to slide

| File | Produces | Slide |
|---|---|---|
| `banc/Dockerfile` | the bench image | 2 |
| `banc/sigrok.sh` | `banc/sorties/sigrok.txt`: decoding of the real captures, right baud rate then wrong ones | 2, 3, 9, 10 |
| `banc/uart_sim.py trame` | `banc/sorties/sim-trame.txt`: duration of a bit and of a frame | 3 |
| `banc/uart_sim.py derive` | `banc/sorties/sim-derive.txt`: drift, position of sample 9, 0x55 versus 0xD5 | 5 |
| `banc/uart_sim.py seuils` | `banc/sorties/sim-seuils.txt`: error limits found by the bench | 6 |
| `banc/uart_sim.py quartz` | `banc/sorties/sim-quartz.txt`: UBRR, actual baud rate and error per crystal | 7 |
| `banc/uart_sim.py pc` | `banc/sorties/sim-pc.txt`: PC at 115200 facing an ATmega | 1, 8 |
| `banc/uart_sim.py deux-avr` | `banc/sorties/sim-deux-avr.txt`: two ATmegas talking to each other | 8 |
| `banc/compte.py` | counts the correct bytes and the framing errors, called by `sigrok.sh` for the sweep | 10 |

The "+8.5 %" decodings (slide 9) and the two sweeps (slide 10) are in `banc/sorties/sigrok.txt`.

The ATmega receiver is simulated, not measured on silicon. The captures come from an STM32 (Olimex STM32-H103, ChronoVu LA8 analyzer), not from an ATmega: they show decoding at a wrong baud rate.

## Third-party data (downloaded, not copied here)

- `uart/hello_world/8n1/hello_world_8n1_115200.sr` (1 MHz)
  - https://raw.githubusercontent.com/sigrokproject/sigrok-dumps/0ad13477abc959d37fc9a5acbd23901c371c9c76/uart/hello_world/8n1/hello_world_8n1_115200.sr
  - sha256 `e72b96efdb30ef33e1a7a2a4e1bd814cd47d5474b67a1d5adb68d4c5ad47ab24`
- `uart/hello_world/8n1/hello_world_8n1_9600.sr` (625 kHz)
  - https://raw.githubusercontent.com/sigrokproject/sigrok-dumps/0ad13477abc959d37fc9a5acbd23901c371c9c76/uart/hello_world/8n1/hello_world_8n1_9600.sr
  - sha256 `b87f1f632ce0684a79e0391c860f8b55c78ce952d3ea10eaede41e8a7ffdf8ea`

Both come from https://github.com/sigrokproject/sigrok-dumps (free sigrok project, license: see the repo).

Document cited by the deck, to be read at the publisher (not used by the script): Microchip datasheet DS40002061B (ATmega48A/PA/88A/PA/168A/PA/328/P): https://ww1.microchip.com/downloads/aemDocuments/documents/MCU08/ProductDocuments/DataSheets/ATmega48A-PA-88A-PA-168A-PA-328-P-DS-DS40002061B.pdf (sha256 `b9b9d83cda56a95d999ea8d54fe5a540748ae9020e5e7ae19b913d384ba9320e`).
