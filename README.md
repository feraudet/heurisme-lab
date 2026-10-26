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
| [modbus-rtu-silence](modbus-rtu-silence/) | [Modbus RTU: the silence between frames](https://heurisme.fr/en/blog/modbus-rtu-silence/) |
| [lora-temps-antenne](lora-temps-antenne/) | [LoRa: why 20 bytes take more than a second](https://heurisme.fr/en/blog/lora-temps-antenne/) |
| [uart-erreur-bauds](uart-erreur-bauds/) | [UART at 115200 baud, within 2 %](https://heurisme.fr/en/blog/uart-erreur-bauds/) |
| [dmx512-512-octets](dmx512-512-octets/) | [DMX512: 512 bytes, 44 times a second](https://heurisme.fr/en/blog/dmx512-512-octets/) |
| [gps-premier-fix](gps-premier-fix/) | [GPS takes 30 seconds to know where it is](https://heurisme.fr/en/blog/gps-premier-fix/) |
| [ax25-aprs](ax25-aprs/) | [Packet radio: what really goes over the air](https://heurisme.fr/en/blog/ax25-aprs/) |
| [adsb-1090](adsb-1090/) | [The planes above your house: what they broadcast on 1090 MHz](https://heurisme.fr/en/blog/adsb-1090/) |
| [llm-meme-prompt](llm-meme-prompt/) | [Same prompt, two answers](https://heurisme.fr/en/blog/llm-meme-prompt/) |
| [tokens-format](tokens-format/) | [JSON, YAML or CSV: what a prompt costs](https://heurisme.fr/en/blog/tokens-format/) |
| [llm-juge-biais](llm-juge-biais/) | [The LLM judge that prefers the longest answer](https://heurisme.fr/en/blog/llm-juge-biais/) |
| [facture-electronique](facture-electronique/) | [An electronic invoice, seen from the inside](https://heurisme.fr/en/blog/facture-electronique/) |
| [adressage-ip-radioamateur](adressage-ip-radioamateur/) | [44Net: the amateur radio IP network](https://heurisme.fr/en/blog/adressage-ip-radioamateur/) |
| [antenne-quart-onde](antenne-quart-onde/) | [Quarter-wave antenna: why 8 cm at 868 MHz](https://heurisme.fr/en/blog/antenne-quart-onde/) |
| [antenne-ros](antenne-ros/) | [SWR: what the antenna sends back to the transmitter](https://heurisme.fr/en/blog/antenne-ros/) |
| [antenne-gain-dbi](antenne-gain-dbi/) | [An antenna with gain creates no energy](https://heurisme.fr/en/blog/antenne-gain-dbi/) |
| [antenne-polarisation](antenne-polarisation/) | [Polarization: the ADS-B antenna mounted flat](https://heurisme.fr/en/blog/antenne-polarisation/) |
| [cable-coaxial-pertes](cable-coaxial-pertes/) | [Coax cable: 15 m of RG58 lose more than the antenna gains](https://heurisme.fr/en/blog/cable-coaxial-pertes/) |
| [inodes-epuises](inodes-epuises/) | [Out of inodes: “No space left on device” with free space](https://heurisme.fr/en/blog/inodes-epuises/) |
| [cpu-throttling-conteneur](cpu-throttling-conteneur/) | [CPU limit: an API slowed down on an idle machine](https://heurisme.fr/en/blog/cpu-throttling-conteneur/) |
| [dns-changement-cache](dns-changement-cache/) | [A DNS change does not propagate: caches expire](https://heurisme.fr/en/blog/dns-changement-cache/) |
| [keepalive-502](keepalive-502/) | [Rare 502s that nobody can reproduce](https://heurisme.fr/en/blog/keepalive-502/) |
| [chaine-tls-incomplete](chaine-tls-incomplete/) | [Incomplete TLS chain: the browser gets through, curl and Python do not](https://heurisme.fr/en/blog/chaine-tls-incomplete/) |
| [tokens-francais-anglais](tokens-francais-anglais/) | [In French, the same prompt costs more tokens](https://heurisme.fr/en/blog/tokens-francais-anglais/) |
| [policy-iam-evaluation](policy-iam-evaluation/) | [An Allow is not enough: IAM still says no](https://heurisme.fr/en/blog/policy-iam-evaluation/) |
| [ebus-trames](ebus-trames/) | [eBUS: a self-powered bus on 2 wires](https://heurisme.fr/en/blog/ebus-trames/) |

Scripts and outputs in this repo are released under the MIT license (see `LICENSE`).
| [infinity-agents-en-pause](infinity-agents-en-pause/) | [Infinity: 75,000 paused agents in 8 GB](https://heurisme.fr/en/blog/infinity-agents-en-pause/) |
| [scion-git-agents](scion-git-agents/) | [Scion: 30,000 merges a day, git can't keep up](https://heurisme.fr/en/blog/scion-git-agents/) |
