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
| `MinorVoid.tla` | CC 3.2 (v1.0-rc21): a duty appointment made to a minor is void, as a fold over the held rows; in every arrival order (a retraction before its row included) and at every clock the verdict is the same, backdating only voids, a retracted or superseded minor row still counts, a self-declared adult lifts nothing | 14,336 | 589,824 | the adult proof is judged unexpired at the node's clock, not at D's `asserted_at` (persist's K2-fix11); caught as two instants disagreeing (`Inv_NodesAgree`) |
| `MinorSuspend.tla` | the current age band about a person at an act's own `asserted_at` (CC 3.4.11 read-union; each signer's newest non-retracted row, if it covers the instant): the seat held but not counted while it reads minor. Every order, a retraction before its row included, and every reader clock give the same reading; a self-declared band never raises; a suspension needs a minor row held | 12,288 | 524,288 | the band read at the reader's clock, not the act's `asserted_at`; caught as `Inv_NodesAgree` |

The constants, diameters and times are in `crates/ciris-kernel/FORMAL_GAPS.md`. `bash tools/tla_check.sh`
runs the small set, and `bash tools/tla_check.sh --large` runs the large one (about three minutes on 32 cores).
`MinorVoid_expiry.cfg` is not part of either run: it adds "and unexpired at D's `asserted_at`" to clause 2, a reading
the rc21 text does not have, and TLC finds `Inv_BackdateOnlyVoids` violated (a minor row, an assured adult proof
dated 2 expiring at 4: D dated 4 is void, the same D dated 3 is not). The Constitution withdrew that clause
because of it, and the configuration is kept as a regression plant. `MinorVoid_retracted_adult.cfg` and
`MinorVoid_retracted_adult_large.cfg` run an open question's other answer, a retracted adult proof proving
nothing (`RETRACTED_ADULT_LIFTS = FALSE`); both pass, and they are not part of either run either.
`tools/tla_door_fixture.py` dumps every reachable state of
`Door.tla`, and `crates/ciris-kernel/tests/tla_door.rs` replays each through the crate's door.
These are runs to a bound over models written by the authors of the rules, as the Python checks are.
