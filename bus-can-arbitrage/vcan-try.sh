#!/bin/bash
# vcan trial in the privileged container (kernel of Docker Desktop). The kernel version is not printed:
# it is the one of the Docker Desktop in use, not part of the bench (hence modprobe -q).
set -x
apt-get -o Acquire::Check-Valid-Until=false update -qq >/dev/null 2>&1
apt-get install -y -qq can-utils iproute2 kmod >/dev/null 2>&1
dpkg -s can-utils | grep -E '^Version'
modprobe -q vcan; echo "modprobe exit=$?"
ip link add dev vcan0 type vcan; echo "ip link add exit=$?"
ip link set up vcan0
ip -details link show vcan0
