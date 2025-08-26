#!/bin/sh
# Decodes real UART captures (sigrok-dumps, folder uart/hello_world/8n1) with sigrok-cli,
# at the right baud rate then at wrong ones. Meant to run inside the banc-uart container:
#   bash banc/rejouer.sh   (it mounts the captures on /d and this folder on /b)
set -e
EN=${1:-}   # --en: compte.py outputs in English
F=hello_world_8n1_115200.sr
F9=hello_world_8n1_9600.sr

echo '== version'
sigrok-cli --version | head -1

echo '== capture'
echo "\$ sigrok-cli -i $F --show | grep -v '^- [1-7]:'"
sigrok-cli -i $F --show | grep -v '^- [1-7]:'

echo '== bon debit'
echo "\$ sigrok-cli -i $F -P uart:rx=TX:baudrate=115200 -B uart=rx | od -An -c | head -2"
sigrok-cli -i $F -P uart:rx=TX:baudrate=115200 -B uart=rx | od -An -c | head -2

echo '== bits du premier octet'
echo "\$ sigrok-cli -i $F -P uart:rx=TX:baudrate=115200:format=ascii -A uart --protocol-decoder-samplenum | head -11"
sigrok-cli -i $F -P uart:rx=TX:baudrate=115200:format=ascii -A uart --protocol-decoder-samplenum | head -11

echo '== +8.5 % (125000)'
echo "\$ sigrok-cli -i $F -P uart:rx=TX:baudrate=125000 -A uart=rx-data:rx-warnings | head -12"
sigrok-cli -i $F -P uart:rx=TX:baudrate=125000 -A uart=rx-data:rx-warnings | head -12

echo '== balayage 115200'
for b in 104000 106000 108000 110000 111111 112000 113000 115200 117647 119000 120000 121000 122000 123000 125000; do
  sigrok-cli -i $F -P uart:rx=TX:baudrate=$b -A uart=rx-data:rx-warnings | python3 /b/compte.py "$b" $EN
done

echo '== balayage 9600'
for b in 8800 9000 9100 9200 9600 10000 10100 10200 10416; do
  sigrok-cli -i $F9 -P uart:rx=TX:baudrate=$b -A uart=rx-data:rx-warnings | python3 /b/compte.py "$b" $EN
done

echo '== debit reel (premier et dernier start bit, nombre de trames)'
echo "\$ sigrok-cli -i $F -P uart:rx=TX:baudrate=115200 -A uart=rx-start --protocol-decoder-samplenum | sed -n '1p;\$p'"
sigrok-cli -i $F -P uart:rx=TX:baudrate=115200 -A uart=rx-start --protocol-decoder-samplenum | sed -n '1p;$p'
sigrok-cli -i $F -P uart:rx=TX:baudrate=115200 -A uart=rx-start --protocol-decoder-samplenum | wc -l
sigrok-cli -i $F9 -P uart:rx=TX:baudrate=9600 -A uart=rx-start --protocol-decoder-samplenum | sed -n '1p;$p'
sigrok-cli -i $F9 -P uart:rx=TX:baudrate=9600 -A uart=rx-start --protocol-decoder-samplenum | wc -l
