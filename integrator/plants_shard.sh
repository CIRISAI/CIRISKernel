#!/bin/bash
# One shard of the crate plants (tools/kernel_crate_plants.sh, PLANTS_SHARD=k/n) on the final head, as its own grace
# job: usage plants_shard.sh k n. Each plant is a release rebuild of a copy of the crate plus its whole test suite.
# Prints the NOT CAUGHT lines, any "text not found" (a plant whose target moved: retarget it), and the tally.
set -u
k="$1"; n="$2"
T=/home/emoore/CIRISKernel/.claude/worktrees/release-0.5.0
L=/tmp/claude-1000/-home-emoore-CIRISKernel/9f476e19-79a3-4f60-8019-6f13a6523575/scratchpad/int/final-logs
mkdir -p "$L"; cd "$T" || exit 1
echo "head: $(git log --oneline -1); shard $k of $n"
PLANTS_SHARD="$k/$n" bash tools/kernel_crate_plants.sh > "$L/plants_$k.log" 2>&1; rc=$?
grep -E "NOT CAUGHT|text not found|unbroken|failed" "$L/plants_$k.log" | head -40
tail -1 "$L/plants_$k.log"
exit $rc
