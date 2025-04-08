#!/bin/sh
# Usage: sh src/run.sh <name> [tap.py options]
# Sets up two pty pairs with socat: client <-> tapA, tapB <-> server, then starts the relay, the slave and the master.
nom=$1; shift
cd "$(dirname "$0")/.."
rm -f /tmp/cli /tmp/tapA /tmp/tapB /tmp/srv
socat pty,raw,echo=0,link=/tmp/cli pty,raw,echo=0,link=/tmp/tapA & S1=$!
socat pty,raw,echo=0,link=/tmp/tapB pty,raw,echo=0,link=/tmp/srv & S2=$!
sleep 0.5
python src/tap.py /tmp/tapA /tmp/tapB "$@" > raw/$nom-capture.txt 2>&1 & T=$!
${SLAVE:-python src/server.py} /tmp/srv > raw/$nom-esclave.txt 2>&1 & P=$!
sleep 1.5
python src/client.py /tmp/cli > raw/$nom-maitre.txt 2>&1
sleep 0.5
kill $P $T $S1 $S2 2>/dev/null
wait 2>/dev/null
echo "== capture"; cat raw/$nom-capture.txt
echo "== maître"; cat raw/$nom-maitre.txt
echo "== esclave"; cat raw/$nom-esclave.txt
