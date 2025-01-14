#!/bin/bash
# Same trial as vcan-try.sh, clean output: each command preceded by "$ "
# No uname -r and modprobe -q: the Docker Desktop kernel version is not part of the bench
apt-get -o Acquire::Check-Valid-Until=false update -qq >/dev/null 2>&1
apt-get install -y -qq can-utils iproute2 kmod >/dev/null 2>&1
for c in "modprobe -q vcan" "ip link add dev vcan0 type vcan" "candump vcan0"; do
  echo "\$ $c"
  timeout 3 $c 2>&1
  echo "(exit $?)"
done
