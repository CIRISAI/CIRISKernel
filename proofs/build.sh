#!/usr/bin/env bash
# Compiles the stack in order into a temporary directory. Exits 1 on any compile error, any use of
# sorry, or an axiom beyond the three of core Lean (propext, Quot.sound, Classical.choice). Run from anywhere.
set -u
here="$(cd "$(dirname "$0")" && pwd)"
out="$(mktemp -d)"
trap 'rm -rf "$out"' EXIT
rc=0
files="Order Causal Seat Window Recount Harden Harden2 Harden3 SeatG Terms Reader Merge Consent Carry RosterHead TwoMechanisms KeyEnd Duty Settled CutFix SeatWalk SeatCount WindowTable Retained Versions Ops Repurge Admission MinorVoid KeyOfIssuer DerivedCircle"
for f in $files; do
  if ! LEAN_PATH="$out" lean -M 6000 -T 200000 --root="$here" -o "$out/$f.olean" "$here/$f.lean" > "$out/$f.log" 2>&1; then
    echo "does not compile: $f"; grep -m5 "error" "$out/$f.log"; rc=1
  fi
  if grep "depends on axioms" "$out/$f.log" | sed 's/propext//g; s/Quot\.sound//g; s/Classical\.choice//g' | grep -q "\[[ ,]*[A-Za-z]"; then
    echo "sorry or an axiom beyond the three of core: $f"; rc=1
  fi
done
# a sorry the compiler reports, whether or not a printed theorem depends on it
if grep -l "declaration uses 'sorry'" "$out"/*.log >/dev/null 2>&1; then
  echo "sorry in: $(grep -l "declaration uses 'sorry'" "$out"/*.log | xargs -n1 basename | sed 's/\.log$//' | tr '\n' ' ')"; rc=1
fi
n=$(cat "$out"/*.log | grep -c "depend")
# the semantic audit: every declaration of the stack, printed or not, on core axioms only (Audit.lean, with the
# imports and module list filled in from $files)
imports="$(for f in $files; do printf 'import %s\\n' "$f"; done)"
mods="$(for f in $files; do printf '`%s, ' "$f"; done | sed 's/, $//')"
sed -e "s/^-- IMPORTS:.*$/$imports/" -e "s/:= \[\] -- MODULES:.*$/:= [$mods]/" "$here/Audit.lean" > "$out/Audit.lean"
if LEAN_PATH="$out" lean -M 6000 -T 200000 --root="$out" "$out/Audit.lean" > "$out/audit.out" 2>&1; then
  audited="$(grep -o "audit: [0-9]* declarations" "$out/audit.out" | grep -o "[0-9]*")"
else
  echo "audit failed:"; grep "audit:" "$out/audit.out" | head -20; rc=1; audited=0
fi
# the audit's plant: a module with an unused sorry and a minted axiom, which the audit must refuse
cat > "$out/AuditPlant.lean" <<'PLANT'
theorem audit_plant_gap : 1 = 2 := sorry
axiom audit_plant_axiom : False
PLANT
sed -e 's/^import Lean$/import Lean\nimport AuditPlant/' -e 's/^def stackModules : List Lean.Name := \[/def stackModules : List Lean.Name := [`AuditPlant, /' \
  "$out/Audit.lean" > "$out/AuditPlanted.lean"
LEAN_PATH="$out" lean --root="$out" -o "$out/AuditPlant.olean" "$out/AuditPlant.lean" > /dev/null 2>&1
if LEAN_PATH="$out" lean -M 6000 -T 200000 --root="$out" "$out/AuditPlanted.lean" > "$out/plant.out" 2>&1 \
  || [ "$(grep -c "audit: audit_plant" "$out/plant.out")" -ne 2 ]; then
  echo "the audit's plant was not caught (a sorry and an axiom in an unprinted declaration)"; rc=1
fi
echo "proofs: $(echo $files | wc -w) files, $n theorems reported, $audited declarations audited, plant caught, rc=$rc"
exit $rc
