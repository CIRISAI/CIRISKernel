#!/usr/bin/env bash
# One command: compile every proof in proofs/, run every model check in models/, and build and test the Rust
# crate crates/ciris-kernel against the models' own cases.
# Prints one line per step and a summary. Exits 1 if any step fails. Full logs go to a temporary
# directory, kept and named on failure. Needs Lean 4.14.0 on PATH (see README.md), Python 3.12 and cargo
# (the crate has no dependencies, so cargo runs with --offline), and Java 11 or later for TLC (tools/tla_check.sh
# fetches the pinned tla2tools v1.7.4 once, or reads $TLA2TOOLS_JAR).
# The checks run one after another; some use three worker processes and the calling one.
set -u
root="$(cd "$(dirname "$0")" && pwd)"
logs="$(mktemp -d)"
export GATES_TMP="$logs"
# python3 -I ignores PYTHON* variables, so bytecode caches may appear; .gitignore covers them
rc=0
n=0
bad=0

lv="$(lean --version 2>/dev/null || true)"
case "$lv" in
  *"version 4.14.0"*) ;;
  "") echo "lean not found on PATH: install Lean 4.14.0 (README.md, Build and run)"; exit 1 ;;
  *) echo "note: the proofs are checked under Lean 4.14.0; found: $lv" ;;
esac

step() {  # step <label> <log name> <command...>
  local label="$1" log="$logs/$2.log"; shift 2
  local t0=$SECONDS
  ( cd "$root" && "$@" ) > "$log" 2>&1
  local code=$?
  local last
  last="$(grep -v '^[[:space:]]*$' "$log" | tail -n 1)"
  n=$((n + 1))
  if [ $code -eq 0 ]; then
    printf 'ok    %-34s %4ss  %s\n' "$label" "$((SECONDS - t0))" "$last"
  else
    printf 'FAIL  %-34s %4ss  exit %s: %s\n' "$label" "$((SECONDS - t0))" "$code" "$last"
    bad=$((bad + 1)); rc=1
  fi
}

step "proofs/build.sh"                    lean      bash proofs/build.sh
step "check_purge (checkpoint, purge)"    purge     python3 -I models/causal_kernel/check_purge.py
step "check_time (two notions of time)"   time      python3 -I models/causal_kernel/check_time.py
step "check_key_end (a key's own end)"    key_end   python3 -I models/causal_kernel/check_key_end.py
step "check_conferral_end (an end)"      conferral python3 -I models/causal_kernel/check_conferral_end.py
step "check_conferral_content (tips)"    content   python3 -I models/causal_kernel/check_conferral_content.py
step "check_rosters (one roster)"         rosters   python3 -I models/causal_kernel/check_rosters.py
step "check_attacks (34 attacks)"         attacks   python3 -I models/causal_kernel/check_attacks.py
step "check (order-freeness)"             check     python3 -I models/causal_kernel/check.py
step "check_cut (the cut)"                cut       python3 -I models/causal_kernel/check_cut.py
step "check_roomkey (private rooms)"      roomkey   python3 -I models/causal_kernel/check_roomkey.py
step "fork_check (roster tips)"           fork      python3 -I models/roster_fork/fork_check.py --check
step "key_plane_model (writer's keys)"    keyplane  python3 -I models/key_plane/key_plane_model.py --check
step "divergence list (counts)"           diverge   python3 -I tools/divergence_counts.py
step "kernel_fixtures (fixtures current)"   fixtures  python3 -I tools/kernel_fixtures.py --check
step "ciris-kernel build (no_std)"         crate     bash tools/kernel_crate_build.sh
step "ciris-kernel conformance"            conform   bash tools/kernel_conformance.sh
step "ciris-kernel plants"                 plants    bash tools/kernel_crate_plants.sh
step "tla (TLC, five specs, plants)"       tla       bash tools/tla_check.sh

echo "---"
if [ $rc -eq 0 ]; then
  echo "all $n steps passed"
  rm -rf "$logs"
else
  echo "$bad of $n steps did not pass; logs kept in $logs"
fi
exit $rc
