#!/usr/bin/env bash
# Run the crate's differential tests (crates/ciris-kernel/tests/) and print one line per conformance run and a
# total. Exits 1 if a test fails or any run reports a disagreement. Needs cargo (no network: --offline).
set -u
root="$(cd "$(dirname "$0")/.." && pwd)"
out="$(cd "$root" && cargo test --offline --release -p ciris-kernel -- --nocapture 2>&1)"
code=$?
lines="$(printf '%s\n' "$out" | grep '^conformance ')"
printf '%s\n' "$lines"
cases=$(printf '%s\n' "$lines" | sed -E 's/.*: ([0-9]+) cases, ([0-9]+) disagreements/\1/' | awk '{s+=$1} END {print s+0}')
bad=$(printf '%s\n' "$lines" | sed -E 's/.*: ([0-9]+) cases, ([0-9]+) disagreements/\2/' | awk '{s+=$1} END {print s+0}')
runs=$(printf '%s\n' "$lines" | grep -c .)
if [ $code -ne 0 ]; then printf '%s\n' "$out" | grep -E 'FAILED|panicked' | head -20; fi
echo "ciris-kernel: $runs conformance runs, $cases cases, $bad disagreements"
[ $code -eq 0 ] && [ "$bad" -eq 0 ]
