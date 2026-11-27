#!/usr/bin/env bash
# Round two: regenerate fixtures, the verification list, then the two gate plants on a copy of the crate.
set -u
root="$1"
cd "$root"
python3 -I tools/kernel_fixtures.py > /dev/null; echo "EXIT kernel_fixtures (regenerate) $?"
python3 -I models/causal_kernel/check_conferral_end.py | tail -1 | cut -c1-80; echo "EXIT check_conferral_end ${PIPESTATUS[0]}"
python3 -I models/causal_kernel/check_conferral_two.py | tail -2; echo "EXIT check_conferral_two ${PIPESTATUS[0]}"
python3 -I tools/kernel_plants_targets.py; echo "EXIT kernel_plants_targets $?"
python3 -I tools/kernel_fixtures.py --check | tail -1; echo "EXIT kernel_fixtures --check ${PIPESTATUS[0]}"
cd crates/ciris-kernel
cargo fmt; cargo fmt --check; echo "EXIT cargo fmt --check $?"
cargo clippy --offline --all-targets 2>&1 | grep -E "^(warning|error)" | sort | uniq -c; echo "EXIT cargo clippy ${PIPESTATUS[0]}"
cargo test --offline --release 2>&1 | grep -E "test result" | awk '{p+=$4; f+=$6} END {print "tests passed " p ", failed " f}'; echo "EXIT cargo test ${PIPESTATUS[0]}"
cd "$root"
bash tools/kernel_conformance.sh | grep -E "end of a conferral|^ciris-kernel"; echo "EXIT kernel_conformance ${PIPESTATUS[0]}"
bash tools/kernel_crate_build.sh 2>&1 | tail -1; echo "EXIT kernel_crate_build ${PIPESTATUS[0]}"
python3 -I tools/kernel_plants_targets.py; echo "EXIT kernel_plants_targets (after fmt) $?"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
cp -a "$root/crates/ciris-kernel" "$work/ciris-kernel"
rm -rf "$work/ciris-kernel/target"
export CARGO_TARGET_DIR="$work/target"
(cd "$work/ciris-kernel" && cargo test --offline --release -q > "$work/log" 2>&1) || { echo "the unbroken copy fails"; exit 1; }
echo "unbroken copy passes"
plant() {
  local name="$1" f="$work/ciris-kernel/$2"
  cp "$f" "$f.orig"
  python3 -I -c 'import sys; p,a,b=sys.argv[1:4]; s=open(p).read(); assert a in s, a; open(p,"w").write(s.replace(a,b,1))' "$f" "$3" "$4" || { echo "plant $name: text not found"; exit 1; }
  if (cd "$work/ciris-kernel" && cargo test --offline --release -q > "$work/log" 2>&1); then
    echo "NOT CAUGHT  $name"
  else
    echo "caught      $name"
    echo "   compile errors: $(grep -cE '^error(\[E|: could not compile)' "$work/log"); cases that differ: $(grep -oE '^deputy[a-z_]*: got' "$work/log" | sort -u | tr '\n' ' ')"
  fi
  mv "$f.orig" "$f"
}
eval "$(grep -E "passes as its signer|asked of the act's own edge|chain of deputies" "$root/tools/kernel_crate_plants.sh")"
