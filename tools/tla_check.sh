#!/usr/bin/env bash
# Model-check every spec in models/tla/ with TLC: each <Spec>.cfg must pass, and each <Spec>_plant.cfg (the same
# spec with its planted break switched on) must be caught. With --large, the <Spec>_large.cfg and
# <Spec>_large_plant.cfg configurations instead (minutes, run locally; FORMAL_GAPS.md records them). Prints one
# line per spec with the distinct states, the diameter and the time, and a summary; exits 1 on any failure. Needs Java 11 or later. The TLC jar is the pinned
# tla2tools v1.7.4: $TLA2TOOLS_JAR, or a copy cached under ${XDG_CACHE_HOME:-$HOME/.cache}/ciris-kernel,
# fetched once and checked against its SHA-256.
set -u
root="$(cd "$(dirname "$0")/.." && pwd)"
sha="936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88"
jar="${TLA2TOOLS_JAR:-${XDG_CACHE_HOME:-$HOME/.cache}/ciris-kernel/tla2tools-1.7.4.jar}"
if [ ! -f "$jar" ]; then
  mkdir -p "$(dirname "$jar")"
  curl -sSfL -o "$jar.part" https://github.com/tlaplus/tlaplus/releases/download/v1.7.4/tla2tools.jar || { echo "cannot fetch tla2tools"; exit 1; }
  mv "$jar.part" "$jar"
fi
echo "$sha  $jar" | sha256sum -c --status || { echo "tla2tools.jar does not match its pinned SHA-256"; exit 1; }
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
cd "$root/models/tla" || exit 1
bad=0; n=0; total=0
suffix=""
[ "${1:-}" = "--large" ] && suffix="_large"
for spec in $(ls *.tla | sed 's/\.tla$//' | sort); do
  cfg="$spec$suffix.cfg"
  n=$((n + 1))
  t0=$SECONDS
  java -XX:+UseParallelGC -cp "$jar" tlc2.TLC -workers auto -metadir "$work/$spec" -config "$cfg" "$spec.tla" > "$work/$spec.log" 2>&1
  ok=$(grep -c "No error has been found" "$work/$spec.log")
  states=$(grep -o "[0-9]* distinct states found" "$work/$spec.log" | tail -n 1 | cut -d' ' -f1)
  depth=$(grep -o "depth of the complete state graph search is [0-9]*" "$work/$spec.log" | grep -o "[0-9]*$")
  secs=$((SECONDS - t0))
  java -XX:+UseParallelGC -cp "$jar" tlc2.TLC -workers auto -metadir "$work/$spec-plant" -config "$spec${suffix}_plant.cfg" "$spec.tla" > "$work/$spec-plant.log" 2>&1
  caught=$(grep -m1 -oE "(Invariant|Temporal properties|Action property|Property) [A-Za-z_]* (is|was) violated|Temporal properties were violated" "$work/$spec-plant.log")
  if [ "$ok" = 1 ] && [ -n "$caught" ]; then
    printf 'ok    %-12s %8s distinct states, diameter %3s, %4ss   plant caught: %s\n' "$spec" "$states" "$depth" "$secs" "$caught"
  else
    printf 'FAIL  %-12s passes: %s; plant caught: %s\n' "$spec" "$ok" "${caught:-no}"; bad=$((bad + 1))
    tail -n 5 "$work/$spec.log"
  fi
  total=$((total + ${states:-0}))
done
# the reachable states of Door.tla, replayed through the crate (tests/tla_door.rs), must be the ones TLC finds now
if [ -z "$suffix" ] && ! python3 -I "$root/tools/tla_door_fixture.py" --jar "$jar" --check > "$work/fixture.log" 2>&1; then
  cat "$work/fixture.log"; bad=$((bad + 1))
fi
tail=""; [ -z "$suffix" ] && tail="; Door states fixture current"
echo "tla${suffix}: $n specs, $total distinct states, $((n - bad)) pass with their plant caught$tail"
[ $bad -eq 0 ]
