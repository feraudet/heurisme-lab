# heurisme-lab

Every technical article on https://heurisme.fr shows real outputs: decoders, simulations, measurements on local models. This repo holds the test benches that produced them, so any reader can read the scripts and replay the measurements.

One folder per article. In each one:

- `README.md`: what to install, the single command that replays everything, and which file produces which slide;
- the scripts, under the name and path the article cites;
- the outputs, as they appear in the article;
- a `rejouer.sh` script (French for "replay") that downloads third-party data (captures, specs, models) from its public source, checks its sha256, then runs the bench again.

The articles were written in French first, so file names and some outputs are in French. Each README maps the names that matter.

Third-party data is not copied here: only its address and its sha256 are. Its license is the one of its original repository, given in each README.

| Bench | Article |
|---|---|
| [i2c-horloge](i2c-horloge/) | [I²C: who holds the clock](https://heurisme.fr/en/blog/i2c-horloge/) |
| [bus-can-arbitrage](bus-can-arbitrage/) | [The CAN bus: the lowest ID wins, with no collision](https://heurisme.fr/en/blog/bus-can-arbitrage/) |
| [esp-now-sans-routeur](esp-now-sans-routeur/) | [ESP-NOW: ESP32 boards talking without a router](https://heurisme.fr/en/blog/esp-now-sans-routeur/) |

Scripts and outputs in this repo are released under the MIT license (see `LICENSE`).
