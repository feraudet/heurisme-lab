#!/bin/bash
# Runs in the client container (deck-dns-poste). Waits for the instant t0 + N seconds, then runs dig.
# Usage: requete.sh <N> <dig arguments...>     (N = 0 sets t0)
#        requete.sh <N> -                      (only waits for t0 + N, for a change on the server)
#
# Timing: t0 is a whole second of the clock, and every query leaves 0.3 s after
# t0 + N. Unbound counts TTLs in whole seconds, so the remaining TTL it returns
# is the same from one run to the next.
#
# Normalised fields (they change from one run to the next and say nothing about the cache):
# the message id becomes "id: <id>", the query time becomes "Query time: <n> msec".
# The lines ";; SERVER", ";; WHEN" and ";; MSG SIZE" are removed.
set -eu
n=$1; shift
t0_fichier=/tmp/t0
if [ "$n" = 0 ]; then
  # next whole second
  maintenant=$(date +%s%N)
  t0=$(( maintenant / 1000000000 + 1 ))
  echo "$t0" > "$t0_fichier"
else
  t0=$(cat "$t0_fichier")
fi
cible=$(( (t0 + n) * 1000000000 + 300000000 ))
reste=$(( cible - $(date +%s%N) ))
if [ "$reste" -lt 0 ]; then
  echo "late by $(( -reste / 1000000 )) ms for t = $n s" >&2
  exit 1
fi
sleep "$(printf '%d.%09d' $(( reste / 1000000000 )) $(( reste % 1000000000 )))"
if [ "$1" = - ]; then exit 0; fi
echo "# t = $n s"
echo "\$ dig $*"
dig "$@" | sed -E \
  -e 's/id: [0-9]+/id: <id>/' \
  -e 's/Query time: [0-9]+ msec/Query time: <n> msec/' \
  -e '/^;; (SERVER|WHEN|MSG SIZE)/d'
