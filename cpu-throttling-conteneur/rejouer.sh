#!/bin/bash
# Replays the CPU throttling bench of the deck https://heurisme.fr/en/blog/cpu-throttling-conteneur/
# Needs Docker. Image debian:bookworm-20261005 pinned by digest, apt pointed at the Debian snapshot
# of 2026-10-14 (the day before the article): gcc 12 and Python 3.11.
# No other network call, no third-party data.
#
# Four ways to run the same API container (api.c), five runs of 20 s each:
#   no-limit   : docker run (no CPU option)
#   cpus-1     : docker run --cpus=1           (CFS quota 100 ms every 100 ms)
#   cpuset-0   : docker run --cpuset-cpus=0    (one core, no quota)
#   cpus-4     : docker run --cpus=4           (CFS quota 400 ms every 100 ms)
# Latencies change from one run to the next (they depend on what else the machine does):
# the outputs give every run, then the median and the range.
set -eu
cd "$(dirname "$0")"

IMAGE=debian:bookworm-20261005@sha256:2c037a04925515fdd6ea85ea14a682d0e79931f5e9f5d07b6dbfc6ba12f9e858
SNAP=20261014T000000Z
RUNS=${RUNS:-5}
REQUESTS=1000
INTERVAL_MS=20
NET=deck-throttling

cleanup() { docker rm -f deck-throttling-build deck-throttling-api deck-throttling-client >/dev/null 2>&1 || true; }
cleanup
trap cleanup EXIT

# 1. Build api and client with gcc from the snapshot (binaries in bin/, not in the repo).
#    Container: Debian 12 arm64 (remove --platform on an x86_64 machine, everywhere in this script).
docker run -d --name deck-throttling-build --platform linux/arm64 -v "$PWD":/w "$IMAGE" sleep infinity >/dev/null
docker exec deck-throttling-build bash -c "rm -f /etc/apt/sources.list.d/debian.sources && printf '%s\\n' \
  'deb http://snapshot.debian.org/archive/debian/$SNAP bookworm main' > /etc/apt/sources.list"
docker exec deck-throttling-build bash -c 'apt-get -o Acquire::Check-Valid-Until=false update -qq && apt-get install -y -qq gcc libc6-dev python3 >/dev/null'
mkdir -p sorties bin brut
docker exec deck-throttling-build bash -c 'dpkg-query -W gcc-12 libc6 python3' > sorties/00-versions.txt
docker exec deck-throttling-build bash -c 'cd /w && gcc -O2 -pthread -o bin/api api.c && gcc -O2 -pthread -o bin/client client.c'

# 2. The runs.
docker network rm "$NET" >/dev/null 2>&1 || true
docker network create "$NET" >/dev/null
rm -f brut/*
for cfg in no-limit cpus-1 cpuset-0 cpus-4; do
  case $cfg in
    no-limit) opt=() ;;
    cpus-1)   opt=(--cpus=1) ;;
    cpuset-0) opt=(--cpuset-cpus=0) ;;
    cpus-4)   opt=(--cpus=4) ;;
  esac
  for run in $(seq 1 "$RUNS"); do
    docker run -d --name deck-throttling-api --platform linux/arm64 --network "$NET" ${opt[@]+"${opt[@]}"} \
      -v "$PWD/bin":/b:ro "$IMAGE" /b/api >/dev/null
    sleep 1
    ip=$(docker inspect -f "{{(index .NetworkSettings.Networks \"$NET\").IPAddress}}" deck-throttling-api)
    docker exec deck-throttling-api sh -c 'cat /sys/fs/cgroup/cpu.max; cat /sys/fs/cgroup/cpuset.cpus.effective' > "brut/$cfg-$run-cpumax.txt"
    docker exec deck-throttling-api sh -c 'cut -d" " -f1 /proc/uptime; cat /sys/fs/cgroup/cpu.stat' > "brut/$cfg-$run-stat-before.txt"
    docker run --rm --name deck-throttling-client --platform linux/arm64 --network "$NET" \
      -v "$PWD/bin":/b:ro "$IMAGE" /b/client "$ip" "$REQUESTS" "$INTERVAL_MS" > "brut/$cfg-$run-latency.txt"
    docker exec deck-throttling-api sh -c 'cut -d" " -f1 /proc/uptime; cat /sys/fs/cgroup/cpu.stat' > "brut/$cfg-$run-stat-after.txt"
    docker logs deck-throttling-api > "brut/$cfg-$run-jobs.txt"
    docker rm -f deck-throttling-api >/dev/null
    echo "$cfg run $run done"
  done
done
docker network rm "$NET" >/dev/null

# 3. Summaries (sorties/01 to 04), from the raw files in brut/.
n=1
for section in cgroup latency cpustat job; do
  out=$(printf 'sorties/%02d-%s.txt' "$n" "$section")
  { echo "\$ python3 resume.py $section"
    docker exec deck-throttling-build bash -c "cd /w && RUNS=$RUNS PYTHONDONTWRITEBYTECODE=1 python3 resume.py $section"
    echo "(exit $?)"; } > "$out"
  n=$((n + 1))
done
echo "Outputs in sorties/. Latencies differ from one run to the next: compare orders of magnitude, not digits."
