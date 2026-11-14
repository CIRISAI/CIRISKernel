# Provenance

**Source.** <https://github.com/CIRISAI/CIRISConstitution>, branch `rc19`, commit `60c741e` ("The decimal
re-cut: four levels, gaps closed"), edition 1.0-rc19, taken on 2026-11-13.

**Status of this repository.** The parent specification is the normative home of everything here. This
repository is an extract for review: the kernel's text, proofs, models and data, carried so that they build and
run without the parent's toolchain. Where this repository and the parent differ, the parent governs.

**What is new here** (written for this repository, not carried): `README.md`, `OBJECT.md`, `CHARACTERISTICS.md`,
`GOVERNANCE.md`, `REVIEW.md`, `PROVENANCE.md`, `check.sh`, `tools/divergence_counts.py`, `.github/workflows/ci.yml`,
`.gitignore`, `models/README.md`, `data/README.md`, the headers of `kernel/KERNEL.md` and `kernel/TEXT.md`, and
the notes added to the carried READMEs.

## Changes to carried code

Paths only, nine lines; no model logic changed. Each points a read at `data/` or a sibling folder here:

| File | Parent path read | Path here |
|---|---|---|
| `models/causal_kernel/causal_kernel.py` | `formal/kernel_lib` | `models/kernel_lib` |
| `models/causal_kernel/seat.py` (2) | `formal/kernel_lib`; `manifests/governance_policy.json` | `models/kernel_lib`; `data/governance_policy.json` |
| `models/causal_kernel/window.py` | `manifests/governance_policy.json` | `data/governance_policy.json` |
| `models/causal_kernel/roster.py` | `manifests/governance_policy.json` | `data/governance_policy.json` |
| `models/causal_kernel/attacks.py` | `formal/roster_fork` | `models/roster_fork` |
| `models/causal_kernel/check.py` | `formal/derivation/order/witnesses.tsv` | `data/witnesses.tsv` |
| `models/causal_kernel/keyplane.py` | `formal/key_plane/key_plane_model.py` | `models/key_plane/key_plane_model.py` |
| `models/key_plane/key_plane_model.py` | `manifests/transitions.json` | `data/transitions.json` |

`proofs/build.sh` prints `proofs:` where the parent's prints `causal_order:`. Comments, docstrings and printed
source strings in the models still name the parent's paths.

## Every file carried

| Parent path | Path here | Change |
|---|---|---|
| `formal/causal_order/Carry.lean` | `proofs/Carry.lean` | unchanged |
| `formal/causal_order/Causal.lean` | `proofs/Causal.lean` | unchanged |
| `formal/causal_order/Consent.lean` | `proofs/Consent.lean` | unchanged |
| `formal/causal_order/Duty.lean` | `proofs/Duty.lean` | unchanged |
| `formal/causal_order/Harden.lean` | `proofs/Harden.lean` | unchanged |
| `formal/causal_order/Harden2.lean` | `proofs/Harden2.lean` | unchanged |
| `formal/causal_order/Harden3.lean` | `proofs/Harden3.lean` | unchanged |
| `formal/causal_order/KeyEnd.lean` | `proofs/KeyEnd.lean` | unchanged |
| `formal/causal_order/Merge.lean` | `proofs/Merge.lean` | unchanged |
| `formal/causal_order/Order.lean` | `proofs/Order.lean` | unchanged |
| `formal/causal_order/README.md` | `proofs/README.md` | title, pointers, run line and a carried note changed |
| `formal/causal_order/Reader.lean` | `proofs/Reader.lean` | unchanged |
| `formal/causal_order/Recount.lean` | `proofs/Recount.lean` | unchanged |
| `formal/causal_order/RosterHead.lean` | `proofs/RosterHead.lean` | unchanged |
| `formal/causal_order/Seat.lean` | `proofs/Seat.lean` | unchanged |
| `formal/causal_order/SeatG.lean` | `proofs/SeatG.lean` | unchanged |
| `formal/causal_order/Settled.lean` | `proofs/Settled.lean` | unchanged |
| `formal/causal_order/Terms.lean` | `proofs/Terms.lean` | unchanged |
| `formal/causal_order/TwoMechanisms.lean` | `proofs/TwoMechanisms.lean` | unchanged |
| `formal/causal_order/Window.lean` | `proofs/Window.lean` | unchanged |
| `formal/causal_order/build.sh` | `proofs/build.sh` | label of the last line changed |
| `formal/causal_kernel/README.md` | `models/causal_kernel/README.md` | a carried note added under the title |
| `formal/causal_kernel/arrival.py` | `models/causal_kernel/arrival.py` | unchanged |
| `formal/causal_kernel/attack_expected.tsv` | `models/causal_kernel/attack_expected.tsv` | unchanged |
| `formal/causal_kernel/attacks.py` | `models/causal_kernel/attacks.py` | one path changed |
| `formal/causal_kernel/causal_kernel.py` | `models/causal_kernel/causal_kernel.py` | one path changed |
| `formal/causal_kernel/check.py` | `models/causal_kernel/check.py` | one path changed |
| `formal/causal_kernel/check_attacks.py` | `models/causal_kernel/check_attacks.py` | unchanged |
| `formal/causal_kernel/check_cut.py` | `models/causal_kernel/check_cut.py` | unchanged |
| `formal/causal_kernel/check_key_end.py` | `models/causal_kernel/check_key_end.py` | unchanged |
| `formal/causal_kernel/check_purge.py` | `models/causal_kernel/check_purge.py` | unchanged |
| `formal/causal_kernel/check_roomkey.py` | `models/causal_kernel/check_roomkey.py` | unchanged |
| `formal/causal_kernel/check_rosters.py` | `models/causal_kernel/check_rosters.py` | unchanged |
| `formal/causal_kernel/check_time.py` | `models/causal_kernel/check_time.py` | unchanged |
| `formal/causal_kernel/checkpoint.py` | `models/causal_kernel/checkpoint.py` | unchanged |
| `formal/causal_kernel/cut.py` | `models/causal_kernel/cut.py` | unchanged |
| `formal/causal_kernel/key_end.py` | `models/causal_kernel/key_end.py` | unchanged |
| `formal/causal_kernel/key_end_expected.tsv` | `models/causal_kernel/key_end_expected.tsv` | unchanged |
| `formal/causal_kernel/keyplane.py` | `models/causal_kernel/keyplane.py` | one path changed |
| `formal/causal_kernel/purge.py` | `models/causal_kernel/purge.py` | unchanged |
| `formal/causal_kernel/purge_expected.tsv` | `models/causal_kernel/purge_expected.tsv` | unchanged |
| `formal/causal_kernel/roomkey.py` | `models/causal_kernel/roomkey.py` | unchanged |
| `formal/causal_kernel/roster.py` | `models/causal_kernel/roster.py` | one path changed |
| `formal/causal_kernel/roster_expected.tsv` | `models/causal_kernel/roster_expected.tsv` | unchanged |
| `formal/causal_kernel/route.py` | `models/causal_kernel/route.py` | unchanged |
| `formal/causal_kernel/seat.py` | `models/causal_kernel/seat.py` | two paths changed |
| `formal/causal_kernel/time_expected.tsv` | `models/causal_kernel/time_expected.tsv` | unchanged |
| `formal/causal_kernel/window.py` | `models/causal_kernel/window.py` | one path changed |
| `formal/causal_kernel/window_adversary.tsv` | `models/causal_kernel/window_adversary.tsv` | unchanged |
| `formal/causal_kernel/witness_runs.tsv` | `models/causal_kernel/witness_runs.tsv` | unchanged |
| `formal/causal_kernel/witnesses.py` | `models/causal_kernel/witnesses.py` | unchanged |
| `formal/kernel_lib/README.md` | `models/kernel_lib/README.md` | a carried note added under the title |
| `formal/kernel_lib/kernel_lib.py` | `models/kernel_lib/kernel_lib.py` | unchanged |
| `formal/kernel_lib/reexpress.py` | `models/kernel_lib/reexpress.py` | unchanged |
| `formal/roster_fork/README.md` | `models/roster_fork/README.md` | a carried note added under the title |
| `formal/roster_fork/fork.py` | `models/roster_fork/fork.py` | unchanged |
| `formal/roster_fork/fork_check.py` | `models/roster_fork/fork_check.py` | unchanged |
| `formal/key_plane/key_plane_model.py` | `models/key_plane/key_plane_model.py` | one path changed |
| `constitution/governance_policy.tsv` | `data/governance_policy.tsv` | unchanged |
| `manifests/governance_policy.json` | `data/governance_policy.json` | unchanged |
| `manifests/governance_policy_vectors.json` | `data/governance_policy_vectors.json` | unchanged |
| `manifests/transitions.json` | `data/transitions.json` | unchanged |
| `formal/derivation/order/witnesses.tsv` | `data/witnesses.tsv` | unchanged |
| `manifests/divergences.json` | `data/divergences.json` | unchanged |
| `manifests/divergences.tsv` | `data/divergences.tsv` | unchanged |
| `manifests/divergences/agent.json` | `data/divergences/agent.json` | unchanged |
| `manifests/divergences/agent.md` | `data/divergences/agent.md` | unchanged |
| `manifests/divergences/edge.json` | `data/divergences/edge.json` | unchanged |
| `manifests/divergences/edge.md` | `data/divergences/edge.md` | unchanged |
| `manifests/divergences/persist.json` | `data/divergences/persist.json` | unchanged |
| `manifests/divergences/persist.md` | `data/divergences/persist.md` | unchanged |
| `manifests/divergences/tooling.json` | `data/divergences/tooling.json` | unchanged |
| `manifests/divergences/tooling.md` | `data/divergences/tooling.md` | unchanged |
| `formal/KERNEL.md` | `kernel/KERNEL.md` | file pointers rewritten; a header added |
| constitution/part_2_the_grammar.md, lines 1066–1253 (CC 2.7) | `kernel/TEXT.md` | verbatim, below a header |
| `LICENSE` | `LICENSE` | unchanged |

- `manifests/ui_primitives.json` → `data/ui_primitives.json` (unchanged).
