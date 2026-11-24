#!/usr/bin/env bash
# Build crates/ciris-kernel for the host, and for a target with no standard library when one is installed
# (thumbv7em-none-eabihf, or wasm32-unknown-unknown), which shows the crate is no_std with alloc only.
set -u
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root" || exit 1
cargo build --offline --release -p ciris-kernel || exit 1
built="host"
for t in thumbv7em-none-eabihf wasm32-unknown-unknown; do
  if rustup target list --installed 2>/dev/null | grep -qx "$t"; then
    cargo build --offline --release -p ciris-kernel --target "$t" || exit 1
    built="$built, $t"
  fi
done
# the docs build with no warning: a broken or ambiguous link in the crate's docs fails here
RUSTDOCFLAGS="-D warnings" cargo doc --offline --no-deps -p ciris-kernel >/dev/null 2>&1 || { echo "cargo doc: warnings"; exit 1; }
deps=$(cargo tree --offline -p ciris-kernel -e normal --prefix none 2>/dev/null | sort -u | grep -vc '^ciris-kernel ')
echo "ciris-kernel built: $built; dependencies: $deps"
