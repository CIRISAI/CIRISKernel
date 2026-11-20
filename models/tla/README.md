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
| `MinorVoid.tla` | CC 3.2 (v1.0-rc21) as ruled: a duty appointment made to a minor is void (a minor row held, live or retracted, and no un-retracted assured adult proof before it), as a fold over the held rows; in every arrival order (a retraction before its row included) and at every clock the verdict is the same, backdating only voids, a retracted or superseded minor row still counts, a retracted adult proof lifts nothing and its late retraction voids a seated appointment, a self-declared adult lifts nothing | 14,336 | 589,824 | the adult proof judged unexpired at the node's clock (persist's K2-fix11), caught as `Inv_NodesAgree`; and `_plant_retracted_adult_lifts`, a retracted proof still lifting, caught as `Inv_RetractedProofLiftsNothing` |
| `MinorSuspend.tla` | the current age band about a person at an act's own `asserted_at` (CC 3.4.11 read-union, CC 3.5.1 rules 2 and 3, CC 2.4.1.1): per signer the newest row stands, the lowest id at one instant, a retraction counts from its own instant, and the row counts only if it covers the instant; the seat is held but not counted while it reads minor. Every order, a retraction before its row included, and every reader clock give the same reading; a minor graduates by its signer's newer adult row and the void is untouched; the cross-signer rules hold | 24,576 | 1,048,576 | the band read at the reader's clock, not the act's `asserted_at`; caught as `Inv_NodesAgree` |
| `StandingProtection.tla` | CC 5.4.6 and CC 3.2 l.961 as ruled: the person's CURRENT band, read from the rows held now with `MinorSuspend`'s band function, decides three standing relations: a federation-scope owner-binding concludes nothing while it reads minor (a superseded or outranked minor row stops blocking, the subject's minor and an equal-level minor still block); the owner-binding counts for nothing at every scope while it reads minor; a guardianship ends only when it reads adult, which needs an assured row. Expiry on the reading node's own clock; two nodes with their own clocks take the rows in any order; they agree at equal clocks and differ only across a held row's expiry, and the void still counts what the protection lets go | 147,456 | 2,359,296 | the announcement judged once, at the binding's instant; caught as `Inv_Fold` |

The constants, diameters and times are in `crates/ciris-kernel/FORMAL_GAPS.md`. `bash tools/tla_check.sh`
runs the small set, and `bash tools/tla_check.sh --large` runs the large one (about five minutes on 32 cores).
`MinorVoid_expiry.cfg` is not part of either run: it adds "and unexpired at D's `asserted_at`" to clause 2, a reading
the rc21 text does not have, and TLC finds `Inv_BackdateOnlyVoids` violated (a minor row, an assured adult proof
dated 2 expiring at 4: D dated 4 is void, the same D dated 3 is not). The Constitution withdrew that clause
because of it, and the configuration is kept as a regression plant. A spec may have further plants,
`<Spec>_plant_<name>.cfg` (and `_large_plant_<name>.cfg`), each of which `tools/tla_check.sh` requires caught:
`MinorVoid_plant_retracted_adult_lifts.cfg` runs the earlier reading of the void, a retracted adult proof still
lifting it (`RETRACTED_ADULT_LIFTS = TRUE`), which the ruling of 2026-11-20 rejected.
`StandingProtection_void_witness.cfg`, also outside both runs, is meant to fail: TLC shows a node announced while
it holds a witness's minor row that the same witness's newer adult row superseded, a row the void still counts.
`tools/tla_door_fixture.py` dumps every reachable state of
`Door.tla`, and `crates/ciris-kernel/tests/tla_door.rs` replays each through the crate's door.
These are runs to a bound over models written by the authors of the rules, as the Python checks are.
