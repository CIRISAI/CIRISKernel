#!/bin/bash
# THE FINAL JOB on the final wip head (one grace job): fixtures (regenerate + --check, fail on drift), clippy -D
# warnings over every target, then ./check.sh with the crate plants skipped (it runs: Lean proofs, the full Python
# suite, family_placement --check, fixtures --check, plant targets, the no_std build and cargo doc -D warnings, the
# conformance cargo test --release, and TLC with its plants). The crate plants run as separate shard jobs
# (plants_shard.sh). Prints one line per stage; exits 1 on the first stage that fails.
set -u
T=/home/emoore/CIRISKernel/.claude/worktrees/release-0.5.0
L=/tmp/claude-1000/-home-emoore-CIRISKernel/9f476e19-79a3-4f60-8019-6f13a6523575/scratchpad/int/final-logs
mkdir -p "$L"; cd "$T" || exit 1
echo "head: $(git log --oneline -1)"
[ -n "$(git status --short -- crates models tools proofs data)" ] && { echo "tree not clean:"; git status --short | head; exit 1; }

python3 -I tools/kernel_fixtures.py > "$L/fixtures.log" 2>&1; rc=$?
echo "fixtures regenerate rc=$rc: $(tail -1 "$L/fixtures.log")"; [ $rc -ne 0 ] && { tail -30 "$L/fixtures.log"; exit 1; }
python3 -I tools/kernel_fixtures.py --check > "$L/fixtures_check.log" 2>&1; rc=$?
echo "fixtures --check rc=$rc: $(tail -1 "$L/fixtures_check.log")"; [ $rc -ne 0 ] && { echo "fixtures drift after regeneration"; exit 1; }
echo "fixtures moved (to commit):"; git status --short crates/ciris-kernel/tests | head -40

cargo clippy --offline --manifest-path crates/ciris-kernel/Cargo.toml --all-targets -- -D warnings > "$L/clippy.log" 2>&1; rc=$?
echo "clippy -D warnings rc=$rc"; [ $rc -ne 0 ] && { grep -E "^(error|warning)" -A4 "$L/clippy.log" | head -60; exit 1; }

CHECK_SKIP_PLANTS=1 ./check.sh > "$L/check.log" 2>&1; rc=$?
echo "./check.sh (plants skipped) rc=$rc"; grep -vE "^ok " "$L/check.log" | tail -30
exit $rc
