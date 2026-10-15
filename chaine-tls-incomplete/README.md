# chaine-tls-incomplete

This bench goes with the deck https://heurisme.fr/en/blog/chaine-tls-incomplete/ : why curl, Python and OpenSSL say `unable to get local issuer certificate` on a site that a browser opens without a warning. A local PKI (a root, an intermediate, a leaf for `www.exemple.test`), an internal API served by nginx, first with the leaf alone, then with the full chain, and clients that trust the root only.

File names are in French because the original article is. Useful names: `rejouer.sh` = replay script, `banc.sh` = bench (runs in the container), `pki.sh` = creates the PKI, `masque.py` = masks what changes at each replay, `client.py` = the Python script that calls the API, `racine` = root, `intermediaire` = intermediate, `feuille` = leaf, `feuille-seule` = leaf alone, `fullchain-a-l-envers` = full chain in the wrong order, `sorties/` = outputs. The outputs themselves are in English.

## How to replay

- Docker, for the `debian:bookworm-20261005` container in arm64 (pinned by digest in `rejouer.sh`). On x86_64, remove `--platform linux/arm64` in `rejouer.sh`.
- `apt` in the container reads the Debian snapshot of 2026-10-14 (`https://snapshot.debian.org/archive/debian/20261014T000000Z/` and `debian-security` at the same date), so the packages are the ones of that day: OpenSSL `3.0.22`, nginx `1.22.1`, curl `7.88.1`, Python `3.11.2` (see `sorties/00-versions.txt`).
- Nothing to install on the host machine apart from Docker. `client.py` uses the Python standard library only.

Single command:

```bash
bash rejouer.sh
```

It recreates the container (with `www.exemple.test` and `pki.exemple.test` pointing to `127.0.0.1`), then `banc.sh`:

1. `pki.sh` creates `pki/`: the three keys and certificates, `fullchain.pem` (leaf then intermediate) and `fullchain-a-l-envers.pem` (intermediate then leaf);
2. starts nginx with `nginx-feuille-seule.conf` (the leaf alone), runs `openssl s_client`, `curl`, `client.py` and `openssl verify`;
3. follows by hand the address written in the leaf (Authority Information Access, caIssuers), as a browser does, and verifies again with the downloaded intermediate;
4. restarts nginx with `nginx-fullchain.conf` (leaf then intermediate) and runs the same clients;
5. tests `nginx-fullchain-a-l-envers.conf` (the two certificates in the wrong order).

The three nginx files differ by one line, `ssl_certificate`.

## What changes at each replay, and what does not

The keys are generated again at each replay. So the signatures, the key identifiers, the fingerprints and the base64 of each certificate change every time. The outputs never show them:

- `masque.py` replaces the base64 body of each certificate printed by `openssl s_client -showcerts` with the line `(base64 masked: new keys at each replay)`, and the byte counts of the handshake (they follow the length of the signatures) with `(masked)`;
- the `nginx -t` error line starts with the date and the process id: both are replaced by `(date masked)` and `(pid masked)`.

What does not change: subjects, issuers, serial numbers (fixed by the `pki/serial` file: 1001, 2001, 3001) and validity dates. `pki.sh` uses `openssl ca` with `-startdate 20261001000000Z -enddate 20361001000000Z` rather than `openssl x509 -req -days N`, whose dates depend on the day of the replay: `openssl ca` takes fixed start and end dates. The certificates are valid from 2026-10-01 to 2036-10-01: a replay after 2036-10-01 gets `certificate has expired` instead.

Apart from these masks, the files of `sorties/` come out byte for byte: compare with `git diff`. `pki/` is not in the repo (`.gitignore`): it holds private keys, created again at each replay.

## File to slide

| File | Slide |
|---|---|
| `sorties/01-pki.txt` | 3 (root, intermediate, leaf: subject, issuer, serial, dates, CA flag, Authority Information Access) |
| `sorties/02-feuille-seule-s_client.txt` | 4 (nginx serves the leaf alone: one certificate in the chain, verify return code 21) |
| `sorties/03-feuille-seule-clients.txt` | 5 (curl error 60, Python `CERTIFICATE_VERIFY_FAILED`, `openssl verify` error 20) |
| `sorties/04-aia-a-la-main.txt` | 6 (what a browser does: download the intermediate from the caIssuers address) |
| `sorties/05-fullchain-s_client.txt` | 7 (nginx serves leaf then intermediate: two certificates, verify return code 0) |
| `sorties/06-fullchain-clients.txt`, `sorties/07-ordre-inverse.txt` | 8 (curl and Python pass; nginx refuses the wrong order) |
| `sorties/00-versions.txt` | versions of OpenSSL, nginx, curl and Python in the container, and the OpenSSL that curl and Python are linked to (5: the three clients share the same error) |

## Third-party data

None. The PKI, the names (`exemple.test`, a reserved name that never resolves on the Internet, RFC 2606) and the API are created by the bench.
