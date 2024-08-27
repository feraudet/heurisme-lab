# I²C: who holds the clock

Bench for the deck https://heurisme.fr/en/blog/i2c-horloge/ : two real I²C captures (an SHT21 that holds SCL low for 65 ms, an AD5258 that answers NACK after a write), a pull-up calculation, a CRC, and a simulation of a master that ignores clock stretching.

File names and part of the outputs are in French because the original article is. Useful names: `rejouer.sh` = replay script, `sorties/` = outputs (French; the English ones are in `sorties/en/`), `donnees/` = data (downloaded), `mesure_scl.py` = SCL measurement, `calcul_pullup.py` = pull-up calculation, `sim-respecte` = simulation where the master respects stretching, `sim-ignore` = simulation where it ignores it.

## What you need

- Docker (the container is `debian:bookworm-slim`, with `sigrok-cli 0.7.2`, `libsigrokdecode 0.5.3`, `libsigrok 0.5.2`, Python 3.11 and poppler-utils)
- `curl` and `shasum` (or `sha256sum`) to download and check the captures
- network access for the first run

## Replay everything

```bash
bash banc/rejouer.sh
```

The script downloads the two captures into `donnees/` (pinned sigrok-dumps commit), checks their sha256, builds the Docker image `i2c-banc`, then rewrites all the outputs: in French in `banc/sorties/`, in English in `banc/sorties/en/` (`--en` option of the scripts). The `sigrok-cli` outputs are identical in both languages.

## File to slide

| File | Produces | Slide |
|---|---|---|
| `banc/Dockerfile` | the image with sigrok-cli | 2 |
| `banc/sorties/versions.txt` | versions of sigrok-cli and the libraries | 2 |
| `banc/mesure_scl.py` | reads the `.sr` and measures the SCL levels | 2, 5, 7 |
| `banc/sorties/ad5258-scl.txt` | clock frequency of the AD5258 capture | 2 |
| `banc/calcul_pullup.py` | `banc/sorties/pullup.txt`: pull-up calculation example | 4 |
| `banc/sorties/ad5258-fronts.txt` | real SCL and SDA edges of the frame | 5 |
| `banc/sorties/ad5258-decode.txt` | sigrok-cli decoding: acknowledged write then NACK | 5, 6 |
| `banc/sorties/sht21-decode.txt` | full decoding of the SHT21 capture | 7 |
| `banc/sorties/sht21-hold.txt` | the excerpt around `write: E3` | 7 |
| `banc/sorties/sht21-scl.txt` | SCL held low 65.250 ms and 21.593 ms | 7 |
| `banc/sim_bus.py` | `banc/sorties/sim-respecte.txt`, `sim-ignore.txt` and the `.vcd` files: wired-AND bus, 1 µs step | 9 |
| `banc/crc_sht21.py` | `banc/sorties/crc.txt`: SHT21 CRC-8 | 9 |
| `banc/sorties/sim-ignore-decode.txt`, `sim-respecte-decode.txt` | sigrok-cli on the simulated VCD files | 10 |

The simulation is not a measurement: the sensor is a model written from the SHT21 datasheet, with the bytes and the hold time copied from the real capture.

## Third-party data (downloaded, not copied here)

- `i2c/sensirion_sht2x/i2c-sht21-100khz-read-serial-hold.sr`
  - https://raw.githubusercontent.com/sigrokproject/sigrok-dumps/e2c49eb88327ac4eaaa41c160b9e3faa1d9ca1da/i2c/sensirion_sht2x/i2c-sht21-100khz-read-serial-hold.sr
  - sha256 `584a4d12d4a5eddc3bb2c00e4cd6b9437054bc4838a4bf6272be973228e42682`
- `i2c/potentiometer/analog_devices_ad5258/ad5258_write_eeprom_63_readback_nack.sr`
  - https://raw.githubusercontent.com/sigrokproject/sigrok-dumps/e2c49eb88327ac4eaaa41c160b9e3faa1d9ca1da/i2c/potentiometer/analog_devices_ad5258/ad5258_write_eeprom_63_readback_nack.sr
  - sha256 `bac371a27db3f6a150b5602433043d20b99437930cb53fa146e8c639325a7c22`

Both come from the repo https://github.com/sigrokproject/sigrok-dumps (free sigrok project, license: see the repo, no license file comes with the `i2c/` folder).

Documents cited by the deck, to be read at the publisher (not used by the script):

- NXP UM10204 rev. 7.0: https://www.nxp.com/docs/en/user-guide/UM10204.pdf (sha256 `dc91f00f65584e06ef36e26c93bf9d91a95fb3c8a1830a9223e53caf678b36af`)
- Sensirion SHT21 datasheet version 5: https://sensirion.com/media/documents/120BBE4C/63500094/Sensirion_Datasheet_Humidity_Sensor_SHT21.pdf (sha256 `e5905c92060a0e0ae0e40712fee0933ef3ce6392b0419ec88abd9ba5c3cab3ee`)

## Limits

The explanation "the AD5258 is busy writing its EEPROM" is an interpretation drawn from the name of the capture file. The device datasheet was not checked.
