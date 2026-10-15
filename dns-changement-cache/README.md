# dns-changement-cache

This bench goes with the deck https://heurisme.fr/en/blog/dns-changement-cache/ : a DNS change that "does not propagate". Nothing propagates: each resolver keeps the answer in its cache for the TTL of the record. The bench switches the site `www.exemple.test` from an old server (192.0.2.10) to a new one (192.0.2.20) and watches, with `dig`, what the authoritative server and the resolver answer, second by second. It also shows negative caching (an NXDOMAIN kept for the SOA minimum, RFC 2308) and the method that works: lower the TTL first, wait for the old TTL, then switch.

File names are in French because the original article is. Useful names: `rejouer.sh` = replay script, `requete.sh` = query (runs `dig` at a given second), `zones/` = the successive versions of the zone (`depart` = start, `bascule` = switch, `v2-cree` = v2 created, `ttl-baisse` = TTL lowered), `sorties/` = outputs. The outputs themselves are in English, apart from what `dig` prints.

## How to replay

- Docker. `rejouer.sh` builds a local image from `Dockerfile`: `debian:bookworm-20261005` in arm64, pinned by digest. On x86_64, remove `--platform linux/arm64` in `rejouer.sh`.
- `apt` in the image reads the Debian snapshot of 2026-10-14 (`https://snapshot.debian.org/archive/debian/20261014T000000Z/`), so the packages are the ones of that day: NSD `4.6.1-1`, Unbound `1.17.1-2+deb12u4`, dig from `bind9-dnsutils 1:9.18.49-1~deb12u1` (see `sorties/00-versions.txt`).
- Nothing to install on the host machine apart from Docker.

Single command (about 3 minutes, the bench waits for real TTLs to run out):

```bash
bash rejouer.sh
```

It creates an internal Docker network `172.30.153.0/24` (no Internet access while the bench runs) and three containers:

| Container | Address | Role |
|---|---|---|
| `deck-dns-autorite` | 172.30.153.10 | NSD, authoritative for `exemple.test` (`nsd.conf`) |
| `deck-dns-resolveur` | 172.30.153.20 | Unbound, recursive resolver with its cache (`unbound.conf`) |
| `deck-dns-poste` | 172.30.153.30 | the client, runs `dig` through `requete.sh` |

Then it rewrites `sorties/01-bascule.txt`, `sorties/02-negatif.txt` and `sorties/03-ttl-baisse.txt`, and removes the containers and the network. Compare with the files provided: they come out byte for byte (checked on two runs in a row).

## What makes the outputs stable

- Times are relative: `t = 0` is a whole second of the clock, chosen by `requete.sh` at the first query of each scenario. Every query leaves 0.3 s after `t0 + N`. Unbound counts TTLs in whole seconds, so the remaining TTL it returns is the same from one run to the next.
- `requete.sh` normalises the fields that change on every run and say nothing about the cache: the message id becomes `id: <id>`, the query time becomes `Query time: <n> msec`, and the `;; SERVER`, `;; WHEN` and `;; MSG SIZE` lines are removed. Everything else is what `dig` prints.
- Zone changes are made with `nsd-control reload` on the authoritative server, right after the second named in the output (`# t = 2 s: the zone ... is now ...`).

## Settings worth knowing

- The SOA of every zone version has a TTL of 60 s and a MINIMUM of 30 s. The negative caching TTL is the smaller of the two (RFC 2308, sections 3 and 5): 30 s.
- Unbound has no trust anchor (no DNSSEC validation; the test zone is not signed) and its cache settings are the defaults, written out in `unbound.conf`: no `prefetch`, no `serve-expired`, `cache-min-ttl: 0`, `cache-max-negative-ttl: 3600`.
- Unbound answers NXDOMAIN for the reserved name `test.` by default (RFC 6761); `local-zone: "test." nodefault` lifts that default so the stub zone is used.
- 192.0.2.0/24 is the TEST-NET-1 documentation range (RFC 5737): the "servers" of the example are only addresses, nothing listens there.

## File to slide

| File | Slide |
|---|---|
| `nsd.conf`, `unbound.conf` | 2 (the setup) |
| `zones/01-depart.zone` | 3 (the TTL and the SOA in the zone file) |
| `sorties/01-bascule.txt` | 4 (lines 1-19: the authoritative server has the new address, the resolver still the old one), 5 (lines 1-31: the TTL counted down to 0, then the new address) |
| `sorties/02-negatif.txt` | 6 (lines 1-20: NXDOMAIN cached), 7 (lines 1-50: NXDOMAIN counted down to 0) |
| `sorties/03-ttl-baisse.txt` | 8 (lowering the TTL to 5 s before the switch), with `zones/04` to `06` |
| `sorties/00-versions.txt` | versions of NSD, Unbound and dig in the image |

## Third-party data

None. The bench only uses Debian packages from the snapshot above. The RFCs and the Unbound documentation cited by the deck are at https://www.rfc-editor.org/ and https://unbound.docs.nlnetlabs.nl/ .
