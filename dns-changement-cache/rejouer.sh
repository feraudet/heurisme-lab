#!/bin/bash
# Replays the DNS cache bench of the deck https://heurisme.fr/en/blog/dns-changement-cache/
# Needs Docker. Image debian:bookworm-20261005 pinned by digest, apt pointed at the Debian snapshot
# of 2026-10-14 (the day before the article): NSD 4.6.1, Unbound 1.17.1, dig 9.18.
# Three containers on an internal Docker network (no Internet access while the bench runs):
#   deck-dns-autorite  172.30.153.10  NSD, authoritative for exemple.test
#   deck-dns-resolveur 172.30.153.20  Unbound, recursive resolver with a cache
#   deck-dns-poste     172.30.153.30  the client, runs dig
# Takes about 3 minutes: the bench waits for real TTLs to run out.
set -eu
cd "$(dirname "$0")"

IMAGE=heurisme-dns-cache-banc
RESEAU=deck-dns-reseau
AUT=deck-dns-autorite RES=deck-dns-resolveur POSTE=deck-dns-poste
R=172.30.153.20 A=172.30.153.10

menage() { docker rm -f $AUT $RES $POSTE >/dev/null 2>&1 || true; docker network rm $RESEAU >/dev/null 2>&1 || true; }
menage
# On x86_64, remove --platform linux/arm64.
docker build -q --platform linux/arm64 -t $IMAGE . >/dev/null
docker network create --internal --subnet 172.30.153.0/24 $RESEAU >/dev/null

demarre_autorite() {
  docker run -d --name $AUT --network $RESEAU --ip $A -v "$PWD":/w:ro $IMAGE bash -c \
    "mkdir -p /etc/nsd/zones && cp /w/zones/$1 /etc/nsd/zones/exemple.test.zone && exec nsd -d -c /w/nsd.conf" >/dev/null
}
demarre_resolveur() { docker run -d --name $RES --network $RESEAU --ip $R -v "$PWD":/w:ro $IMAGE unbound -d -c /w/unbound.conf >/dev/null; }
# loads a new version of the zone on the authoritative server (NSD rereads the file)
zone() {
  docker exec $AUT cp /w/zones/$1 /etc/nsd/zones/exemple.test.zone
  docker exec $AUT nsd-control -c /w/nsd.conf reload exemple.test >/dev/null
  echo "# t = $2 s: the zone on the authoritative server is now zones/$1 ($3)"
  echo
}
q() { docker exec $POSTE bash /w/requete.sh "$@"; echo; }
attend() { docker exec $POSTE bash /w/requete.sh "$1" -; }

demarre_autorite 01-depart.zone
demarre_resolveur
docker run -d --name $POSTE --network $RESEAU --ip 172.30.153.30 -v "$PWD":/w:ro $IMAGE sleep infinity >/dev/null
sleep 2

mkdir -p sorties
docker exec $POSTE dpkg-query -W nsd unbound bind9-dnsutils > sorties/00-versions.txt

# 1. The switch: www moves from 192.0.2.10 (old server) to 192.0.2.20 (new server), TTL 60 s.
{
  q 0 @$R www.exemple.test A +noall +answer
  attend 2; zone 02-bascule.zone 2 "www 192.0.2.10 -> 192.0.2.20, TTL 60 s"
  q 3 @$A www.exemple.test A +norecurse +noall +comments +answer +noedns
  q 10 @$R www.exemple.test A +noall +answer
  q 30 @$R www.exemple.test A +noall +answer
  q 59 @$R www.exemple.test A +noall +answer
  q 61 @$R www.exemple.test A +noall +answer
} > sorties/01-bascule.txt

# 2. Negative caching: v2.exemple.test is asked for before it exists, then created.
{
  q 0 @$R v2.exemple.test A +noall +comments +answer +authority +noedns
  attend 2; zone 03-v2-cree.zone 2 "v2.exemple.test created, 192.0.2.20"
  q 3 @$A v2.exemple.test A +norecurse +noall +comments +answer +noedns
  q 10 @$R v2.exemple.test A +noall +comments +answer +authority +noedns
  q 29 @$R v2.exemple.test A +noall +comments +answer +authority +noedns
  q 31 @$R v2.exemple.test A +noall +comments +answer +authority +noedns
} > sorties/02-negatif.txt

# 3. The method: lower the TTL first, wait for the old TTL, then switch.
# Fresh start: new authoritative server on the original zone, resolver with an empty cache.
docker rm -f $AUT $RES >/dev/null
demarre_autorite 04-depart.zone
demarre_resolveur
sleep 2
{
  q 0 @$R www.exemple.test A +noall +answer
  attend 2; zone 05-ttl-baisse.zone 2 "www keeps 192.0.2.10, TTL 60 s -> 5 s"
  q 30 @$R www.exemple.test A +noall +answer
  q 61 @$R www.exemple.test A +noall +answer
  attend 62; zone 06-bascule-ttl-5.zone 62 "www 192.0.2.10 -> 192.0.2.20, TTL 5 s"
  q 64 @$R www.exemple.test A +noall +answer
  q 67 @$R www.exemple.test A +noall +answer
} > sorties/03-ttl-baisse.txt

menage
echo "Outputs in sorties/. Compare with git diff."
