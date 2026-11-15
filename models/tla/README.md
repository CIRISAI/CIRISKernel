# `models/tla` — the kernel's concerns where state and interleaving matter, model-checked by TLC

One spec per concern. Each states its invariants and temporal properties, and its `.cfg` runs them with
`MUT = FALSE`. Its `_plant.cfg` runs the same spec with `MUT = TRUE`, one planted break that TLC must catch.
`bash tools/tla_check.sh` runs all of them with the pinned tla2tools v1.7.4 and prints the state counts;
`./check.sh` runs it as a step.

| Spec | Concern | Small (CI): distinct states | Large (local): distinct states | Plant (caught at both) |
|---|---|---|---|---|
| `Door.tla` | the monotone door under any arrival order, with repeats, a missing name and malformed rows | 1,024 | 131,072 | the door drops a row whose named rows are not held on arrival |
| `Cut.tla` | removal by causal past under concurrent acts: an incremental verdict equals the set function | 2,048 | 524,288 | a row is judged once, on arrival |
| `ReaderLine.tla` | the roster head and the acknowledged-head voiding, per reader, as CC 2.7.8 reads it | 13,924 | 551,300 (SYMMETRY over readers) | one reader's acknowledgement voids for every reader |
| `Purge.tla` | finality by receipts, one say, checkpoint and purge | 2,304 | 147,456 | the node purges before the act is settled |
| `TrustWalk.tla` | the trust walk's termination with cycles, on every subgraph of a candidate set, against the Lean `walk` | 2,480 | 454,016 | each key is expanded once, with its first budget |

The constants, diameters and times are in `crates/ciris-kernel/FORMAL_GAPS.md`. `bash tools/tla_check.sh`
runs the small set, and `bash tools/tla_check.sh --large` runs the large one (about three minutes on 32 cores).
`tools/tla_door_fixture.py` dumps every reachable state of
`Door.tla`, and `crates/ciris-kernel/tests/tla_door.rs` replays each through the crate's door.
These are runs to a bound over models written by the authors of the rules, as the Python checks are.
