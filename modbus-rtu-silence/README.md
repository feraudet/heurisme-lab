# Modbus RTU bench: the silence between frames

This bench goes with the deck https://heurisme.fr/en/blog/modbus-rtu-silence/ : a pymodbus master and slave talk through a relay that logs every byte with its time, the CRC is recomputed, then a frame is cut in two (as a USB pause does) in front of a strict slave and in front of pymodbus.

File names and part of the outputs are in French because the original article is. Useful names: `rejouer.sh` = replay script, `raw/` = raw outputs, `src/` = sources, `maitre` = master, `esclave` = slave, `capture` = capture, `COMMANDES.txt` = commands, `pty-parite.txt` = pty parity.

## How to replay

- Docker.
- Image `python:3.12.9-slim-bookworm`, pinned by digest `sha256:48a11b7ba705fd53bf15248d1f94d36c39549903c5d59edcfa2f3f84126e7b44` (pushed 2025-04-08). Inside: Python 3.12.9, pymodbus 3.8.6 (2025-02-10), pyserial 3.5 (2020-11-23), socat 1.7.4.4 from the Debian snapshot `https://snapshot.debian.org/archive/debian/20250408T000000Z/` (bookworm).
- Simulated line at 19200 baud 8N2 (the Linux pty refuses even parity: `raw/pty-parite.txt`), 9600 baud for the last series.

Single command:

```bash
bash rejouer.sh
```

It sets up the virtual serial ports in the container, reruns the seven series of `raw/COMMANDES.txt` and rewrites `raw/`. The times in milliseconds vary from one run to the next, the bytes do not. The slave log (`raw/*-esclave.txt` for pymodbus) shows the time in ms since the slave started, not the wall clock. `bash rejouer.sh refs` downloads the references (specifications, `ftdi_sio.c`) into `ref/` and checks their sha256.

## Why pymodbus 3.8.6 and not 3.9.0

pymodbus 3.9.0 came out on 2025-04-07, the day before the article. It dropped the datastore range check (`validate`): asked for the absent address 0x0FA0, a 3.9.0 slave answers `11 03 00 21 35`, a normal response with zero registers, instead of exception 02. That is not what a Modbus slave should do, so the bench uses 3.8.6, the last release before it. In 3.8.6 the holding register block of `src/server.py` covers only 0x6B..0x6D, and any other address gets `11 83 02 c1 34`. The frame gluing after a 16 ms pause is the same in both versions.

API notes for 3.8.x: the slave is a `ModbusServerContext(slaves={0x11: ModbusSlaveContext(hr=...)}, single=False)`, the master passes `slave=0x11`. `ModbusSlaveContext` adds 1 to the protocol address, hence the block starts at `0x6B + 1`. The `Exception response 131 / 0` line at the top of `raw/*-maitre.txt` is logged by pymodbus when it builds the exception object, before it reads the code: the next lines show the decoded code 0x02.

## File to slide

| File | Slide |
|---|---|
| `src/timing.py`, `raw/timing.txt` | 3 (t1.5 and t3.5 by baud rate, 11-bit character) |
| `src/run.sh`, `src/tap.py`, `src/server.py`, `src/client.py` | 5 (the bench: two `socat` pairs, relay in the middle, slave 0x11) |
| `raw/normal-capture.txt`, `raw/normal-maitre.txt`, `raw/normal-esclave.txt` | 5, 7 (read of 3 registers, error response) |
| `src/crc.py`, `raw/crc-normal.txt` | 6 (CRC16, low byte first) |
| `src/tap.py` (option `--gap-after`), `raw/gap16-pymodbus-*.txt` | 8, 9 (16 ms gap, pymodbus glues the frame back together) |
| `src/strict_slave.py`, `raw/strict-normal-*.txt`, `raw/strict-gap1ms-*.txt`, `raw/strict-gap16-*.txt`, `raw/strict9600-gap1500us-*.txt` | 9 (the strict slave rejects) |
| `raw/pty-parite.txt` | 10 (limit of the bench: no even parity on a pty) |
| `raw/COMMANDES.txt` | 9, 10 (exact commands) |

## Third-party data

It is not in this repo. `rejouer.sh refs` downloads it into `ref/` and checks the sha256.

| File | URL | License |
|---|---|---|
| `modbusoverserial.pdf` | https://www.modbus.org/file/secure/modbusoverserial.pdf (Modbus over Serial Line V1.02) | Modbus Organization's rights |
| `modbusprotocolspecification.pdf` | https://www.modbus.org/file/secure/modbusprotocolspecification.pdf (Application Protocol V1.1b3) | Modbus Organization's rights |
| `ftdi_sio.c` | https://github.com/torvalds/linux/blob/18e0885bd2ca738407036434418a26a58394a60e/drivers/usb/serial/ftdi_sio.c (Linux commit 18e0885, 2025-03-12, the last one on this file before the article; downloaded from `raw.githubusercontent.com`) | GPL v2, Linux kernel |

The modbus.org site may refuse `curl`: then download the PDF by hand into `ref/`, and the script will check it. If a sha256 differs, the script stops, and `TOLERE=1` carries on (`TOLERE` = tolerate).

References read but not downloaded by the script:

- FTDI AN232B-04, latency timer: https://ftdichip.com/wp-content/uploads/2020/08/AN232B-04_DataLatencyFlow.pdf ;
- pymodbus 3.8.6, `pymodbus/framer/rtu.py` (installed by `pip` in the container, not copied here): https://github.com/pymodbus-dev/pymodbus/blob/v3.8.6/pymodbus/framer/rtu.py .
