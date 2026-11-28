#!/bin/bash
# After the last code merge (Eric, 2026-11-28: plants LOCAL through grace; PR #59 stays a draft until they are clean):
#   final_queue.sh plants [n]   the plant shards 1..n (default 8), one grace job at a time, on the committed head
#                               (the fixtures must be regenerated and committed first: final_queue.sh fixtures)
#   final_queue.sh fixtures     regenerate the fixtures + --check, one grace job (then commit what moved)
#   final_queue.sh final        final.sh: fixtures, clippy -D warnings, ./check.sh with the plants skipped
#   final_queue.sh shard k n    one shard again (after a retarget)
set -u
S=/tmp/claude-1000/-home-emoore-CIRISKernel/9f476e19-79a3-4f60-8019-6f13a6523575/scratchpad/int
T=/home/emoore/CIRISKernel/.claude/worktrees/release-0.5.0
run() { grace-sched run --owner CIRISKernel --kind "$1" --peak "$2" --priority low -- bash -c "$3" 2>&1 | grep -v "waits:"; return "${PIPESTATUS[0]}"; }
case "${1:-}" in
  fixtures)
    run "release-0.5.0 fixtures" 2 "cd $T && python3 -I tools/kernel_fixtures.py | tail -3 && python3 -I tools/kernel_fixtures.py --check | tail -1 && git status --short crates/ciris-kernel/tests"
    echo "== fixtures rc=$?" ;;
  plants)
    n="${2:-8}"
    for k in $(seq 1 "$n"); do run "release-0.5.0 crate plants $k/$n" 3 "bash $S/plants_shard.sh $k $n"; echo "== plants shard $k/$n rc=$?"; done
    echo "== plants done" ;;
  shard)
    run "release-0.5.0 crate plants $2/$3" 3 "bash $S/plants_shard.sh $2 $3"; echo "== plants shard $2/$3 rc=$?" ;;
  final)
    run "release-0.5.0 final: fixtures, clippy, check.sh" 4 "bash $S/final.sh"; echo "== final job rc=$?" ;;
  *) echo "usage: final_queue.sh fixtures | plants [n] | shard k n | final"; exit 2 ;;
esac
