#!/usr/bin/env bash
# Run the crate's differential tests (crates/ciris-kernel/tests/) and print one line per conformance run and a
# total. Exits 1 if a test fails, any run reports a disagreement, a run on tools/kernel_conformance_runs.txt did
# not report, a run reported that is not on that list, or one reported twice. Needs cargo (no network:
# --offline). KERNEL_CRATE_DIR runs another copy of the crate (the plants step's).
set -u
root="$(cd "$(dirname "$0")/.." && pwd)"
crate="${KERNEL_CRATE_DIR:-$root/crates/ciris-kernel}"
expected="$root/tools/kernel_conformance_runs.txt"
out="$(cd "$crate" && cargo test --offline --release -- --nocapture 2>&1)"
code=$?
# a report line wherever it stands on its line (a test's own output may precede it)
lines="$(printf '%s\n' "$out" | grep -oE 'conformance .+: [0-9]+ cases, [0-9]+ disagreements')"
printf '%s\n' "$lines"
cases=$(printf '%s\n' "$lines" | sed -E 's/.*: ([0-9]+) cases, ([0-9]+) disagreements/\1/' | awk '{s+=$1} END {print s+0}')
bad=$(printf '%s\n' "$lines" | sed -E 's/.*: ([0-9]+) cases, ([0-9]+) disagreements/\2/' | awk '{s+=$1} END {print s+0}')
runs=$(printf '%s\n' "$lines" | grep -c .)
if [ $code -ne 0 ]; then printf '%s\n' "$out" | grep -E 'FAILED|panicked' | head -20; fi
# every run the list names reported, once, and no other
got="$(printf '%s\n' "$lines" | sed -E 's/^conformance (.*): [0-9]+ cases, [0-9]+ disagreements$/\1/' | LC_ALL=C sort)"
want="$(grep -v '^#' "$expected" | grep -v '^$' | LC_ALL=C sort)"
missing="$(LC_ALL=C comm -23 <(printf '%s\n' "$want") <(printf '%s\n' "$got" | uniq))"
extra="$(LC_ALL=C comm -13 <(printf '%s\n' "$want") <(printf '%s\n' "$got" | uniq))"
twice="$(printf '%s\n' "$got" | uniq -d)"
listed=ok
if [ -n "$missing" ]; then printf 'did not report: %s\n' "$missing"; listed=no; fi
if [ -n "$extra" ]; then printf 'reported but not on %s: %s\n' "tools/kernel_conformance_runs.txt" "$extra"; listed=no; fi
if [ -n "$twice" ]; then printf 'reported twice: %s\n' "$twice"; listed=no; fi
echo "ciris-kernel: $runs conformance runs (of $(printf '%s\n' "$want" | grep -c .) listed), $cases cases, $bad disagreements"
[ $code -eq 0 ] && [ "$bad" -eq 0 ] && [ "$listed" = ok ]
