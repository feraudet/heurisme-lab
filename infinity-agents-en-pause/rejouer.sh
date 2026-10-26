#!/usr/bin/env bash
# Replays the infinity-agents-en-pause bench in a Linux container.
#   bash rejouer.sh infinity   # Infinity's own agent_scale example (agents idle between turns)
#   bash rejouer.sh pending    # same, plus a last tool call that never answers (agents waiting on a tool)
#   bash rejouer.sh naive      # same history in a Vec (none), held by a waiting tokio task (task) or OS thread (thread)
#   bash rejouer.sh all
set -euo pipefail
cd "$(dirname "$0")"

INFINITY_REPO=https://github.com/hydro-project/infinity
INFINITY_COMMIT=341f6c2        # 2026-10-23, release 0.2.0 + THIRD-PARTY fixes
RUST_IMAGE=rust:1.90-bookworm@sha256:3914072ca0c3b8aad871db9169a651ccfce30cf58303e5d6f2db16d1d8a7e58f   # rustc 1.90.0
AGENTS=${AGENTS:-10000}
TURNS=${TURNS:-20}
WAVE=${WAVE:-500}

run() { docker run --rm --platform linux/arm64 \
  -v "$PWD":/bench -v infinity-cargo:/usr/local/cargo/registry \
  -e AGENTS="$AGENTS" -e TURNS="$TURNS" -e WAVE="$WAVE" -w "$1" "$RUST_IMAGE" bash -c "$2"; }

infinity() {
  [ -d src/infinity ] || git clone -q "$INFINITY_REPO" src/infinity
  git -C src/infinity checkout -q "$INFINITY_COMMIT"
  run /bench/src/infinity \
    "cargo run -q --release -p infinity-agent-core --example agent_scale" \
    > "raw/infinity_${AGENTS}x${TURNS}.csv" 2> "raw/infinity_${AGENTS}x${TURNS}.log"
  tail -1 "raw/infinity_${AGENTS}x${TURNS}.log"
}

pending() {
  [ -d src/infinity ] || git clone -q "$INFINITY_REPO" src/infinity
  git -C src/infinity checkout -q "$INFINITY_COMMIT"
  ex=src/infinity/crates/infinity-agent-core/examples/agent_scale_pending.rs
  cp patches/agent_scale_pending.rs "$ex"
  run /bench/src/infinity \
    "cargo run -q --release -p infinity-agent-core --example agent_scale_pending" \
    > "raw/pending_${AGENTS}x${TURNS}.csv" 2> "raw/pending_${AGENTS}x${TURNS}.log" || true
  rm -f "$ex"
  tail -1 "raw/pending_${AGENTS}x${TURNS}.log"
}

naive() {
  run /bench "echo vm.max_map_count=\$(cat /proc/sys/vm/max_map_count) kernel.threads-max=\$(cat /proc/sys/kernel/threads-max) kernel=\$(uname -r)" \
    > raw/limites_noyau.txt
  for mode in none task thread; do
    run /bench/naive "cargo run -q --release -- $mode" \
      > "raw/naive_${mode}_${AGENTS}x${TURNS}.csv" 2> "raw/naive_${mode}_${AGENTS}x${TURNS}.log"
    tail -1 "raw/naive_${mode}_${AGENTS}x${TURNS}.log"
  done
}

case "${1:-all}" in
  infinity) infinity ;;
  pending) pending ;;
  naive) naive ;;
  all) infinity; pending; naive ;;
  *) echo "usage: $0 [infinity|pending|naive|all]" >&2; exit 2 ;;
esac
