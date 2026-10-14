# adressage-ip-radioamateur

This bench goes with the deck https://heurisme.fr/en/blog/adressage-ip-radioamateur/ : who holds 44.0.0.0/8 today (ARIN RDAP), what is announced in BGP inside it (RIPEstat, RIS dump of 2026-10-14 16:00 UTC), and how the French subnet 44.151.0.0/16 is reached.

File names are in French because the original article is. Useful names: `rejouer.sh` = replay script, `collecte.py` = collection (network), `analyse.py` = analysis (offline), `raw/` = raw answers, `sorties/` = outputs, `hors-ligne` = offline. The outputs themselves are in English.

## How to replay

- Python 3.9 or later, standard library only. Nothing to install.
- Network access to `rdap.arin.net`, `stat.ripe.net` and `portal.ampr.org`. No account, no API key.

Single command:

```bash
bash rejouer.sh
```

It deletes `raw/`, downloads every answer again (`collecte.py`, a few minutes: about 40 routing-status queries and one as-overview query per origin AS), checks `raw/SHA256SUMS`, then rewrites `sorties/01-rdap.txt`, `sorties/02-bgp.txt` and `sorties/03-france.txt`. Compare with the files provided.

`bash rejouer.sh hors-ligne` skips the download and rebuilds `sorties/` from the `raw/` already there (after a first `bash rejouer.sh`).

`raw/` is not in this repo: third-party data is never copied here. The sha256 of every file downloaded on 2026-10-14 is in `raw-sha256-2026-10-14.txt`, and the list of RIPEstat prefixes queried that day is in `ripestat-queries.txt`. On the `raw/` of 2026-10-14, `analyse.py` gives the outputs of this folder byte for byte.

What can change when you download again:

- RIPEstat answers are pinned to the RIS dump of `2026-10-14T16:00:00` UTC (`timestamp=` parameter), so the BGP figures should not move. The JSON still carries a query time and a query id, so the sha256 of `raw/ripestat/*.json` differ from run to run.
- ARIN RDAP, the AS holder names (`as-overview`) and the AMPRNet geofeed have no history parameter: they give today's state. The geofeed in `raw/ampr/geofeed.csv` is the one of 2026-10-14.

## Method

- RDAP: `https://rdap.arin.net/registry/ip/<prefix>` for 44.0.0.0/8, 44.0.0.0/9, 44.151.0.0/16 and 44.192.0.0/10, and `https://rdap.arin.net/registry/entity/ARDC`.
- BGP: RIPEstat `routing-status` returns at most 50 more-specifics per query. `collecte.py` queries 44.0.0.0/8, and wherever the list is full, queries both halves of the prefix, down to the level where the list is no longer full. The list of prefixes actually queried is in `raw/ripestat/queries.txt`. `analyse.py` takes the union of all (prefix, origin AS) pairs. Only routes seen by at least 10 RIS peers are counted (default of the endpoint).
- `ris-prefixes` for AS56508 (ARDC): number of IPv4 and IPv6 prefixes it originates.
- Geofeed: `https://portal.ampr.org/storage/geofeed.csv`, the URL given in the remark of the ARIN record NET-44-0-0-0-1. One line per AMPRNet subnet: prefix, country, region, city.
- Addresses "in more specifics" are counted once even when prefixes overlap (`ipaddress.collapse_addresses`).

## File to slide

| File | Slide |
|---|---|
| `sorties/01-rdap.txt` | 2 (NET44 registered 1992-07-01), 3 (44.192.0.0/10 at Amazon since 2019-07-18), 7 (no IPv6 at ARDC) |
| `sorties/02-bgp.txt` | 5 (608 prefixes, 374 origin AS, UCSD and Amazon covering routes) |
| `sorties/03-france.txt` | 4 (geofeed, 44.151.0.0/16), 6 (44.151.0.0/16 covered by 44.128.0.0/10 AS7377), 7 (9 French entries announced in BGP) |
| `collecte.py` | downloads `raw/` |
| `analyse.py` | prints the three outputs from `raw/` |

## Layout of raw/ (created by `collecte.py`)

- `raw/rdap/*.json`: ARIN RDAP answers.
- `raw/ripestat/routing-status_*.json`, `raw/ripestat/france_routing-status_44.151.0.0_16.json`, `raw/ripestat/ris-prefixes_AS56508.json`, `raw/ripestat/as-overview_AS*.json`: RIPEstat answers.
- `raw/ampr/geofeed.csv`: AMPRNet geofeed.
- `raw/SHA256SUMS`: sha256 of every file above, checked by `rejouer.sh`.

## Personal data

Some origin AS that announce AMPRNet prefixes are held by private persons. The outputs give the AS number only for the French prefixes, never the holder name. The geofeed and the RIPEstat answers are not stored here.

## Third-party data

ARIN RDAP data: ARIN terms of use (https://www.arin.net/resources/registry/whois/tou/). RIPEstat data: RIPE NCC terms (https://www.ripe.net/about-us/legal/ripestat-service-terms-and-conditions/). AMPRNet geofeed: published by ARDC, no license stated in the file.
