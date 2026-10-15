#!/bin/bash
# Replays the TLS chain bench of the deck https://heurisme.fr/en/blog/chaine-tls-incomplete/
# Needs Docker. Image debian:bookworm-20261005 pinned by digest, apt pointed at the Debian snapshot
# of 2026-10-14 (the day before the article): OpenSSL, nginx, curl and Python of that day.
# No other network call: the PKI is created inside the container, at each replay.
set -eu
cd "$(dirname "$0")"

# Container: Debian 12 arm64 (remove --platform on an x86_64 machine).
# www.exemple.test (the internal API) and pki.exemple.test (where the intermediate is published)
# both point to the container itself.
IMAGE=debian:bookworm-20261005@sha256:2c037a04925515fdd6ea85ea14a682d0e79931f5e9f5d07b6dbfc6ba12f9e858
SNAP=20261014T000000Z
docker rm -f deck-chaine-tls >/dev/null 2>&1 || true
docker run -d --name deck-chaine-tls --platform linux/arm64 -v "$PWD":/w \
  --add-host www.exemple.test:127.0.0.1 --add-host pki.exemple.test:127.0.0.1 "$IMAGE" sleep infinity >/dev/null
docker exec deck-chaine-tls bash -c "rm -f /etc/apt/sources.list.d/debian.sources && printf '%s\\n' \
  'deb http://snapshot.debian.org/archive/debian/$SNAP bookworm main' \
  'deb http://snapshot.debian.org/archive/debian-security/$SNAP bookworm-security main' > /etc/apt/sources.list"
docker exec deck-chaine-tls bash -c 'apt-get -o Acquire::Check-Valid-Until=false update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends openssl nginx-light curl python3 >/dev/null'
mkdir -p sorties
docker exec deck-chaine-tls bash -c 'dpkg-query -W openssl nginx-light curl python3; curl -V | head -n 1; python3 -c "import ssl; print(ssl.OPENSSL_VERSION)"' > sorties/00-versions.txt

# creates pki/ (root, intermediate, leaf), starts nginx with the leaf alone, then with the full chain
docker exec deck-chaine-tls bash /w/banc.sh

docker rm -f deck-chaine-tls >/dev/null
echo "Outputs in sorties/. Compare with git diff."
