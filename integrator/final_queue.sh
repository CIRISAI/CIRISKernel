#!/bin/bash
# Queue the final job, then the plant shards, one grace job at a time (each waits for the one before).
# usage: final_queue.sh [n]   (n shards, default 8)
set -u
n="${1:-8}"
S=/tmp/claude-1000/-home-emoore-CIRISKernel/9f476e19-79a3-4f60-8019-6f13a6523575/scratchpad/int
run() { grace-sched run --owner CIRISKernel --kind "$1" --peak "$2" --priority low -- bash "${@:3}" 2>&1 | grep -v "waits:"; return "${PIPESTATUS[0]}"; }
run "release-0.5.0 final: fixtures, clippy, check.sh" 4 "$S/final.sh"; frc=$?
echo "== final job rc=$frc"
for k in $(seq 1 "$n"); do
  run "release-0.5.0 crate plants $k/$n" 3 "$S/plants_shard.sh" "$k" "$n"
  echo "== plants shard $k/$n rc=$?"
done
echo "== final queue done"
