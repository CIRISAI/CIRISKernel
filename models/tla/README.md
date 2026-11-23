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
| `MinorSuspend.tla` | the current age band about a person at an act's own `asserted_at` (CC 3.4.11 read-union, CC 3.5.1 rules 2 and 3, CC 2.4.1.1, with the age-row rulings of 2026-11-20), and the band function `StandingProtection.tla` reuses: no expiry; per signer the newest row stands, the lowest id at one instant, a retraction counts from its own instant; the subject's younger band lowers; a higher level outranks a lower whatever the dates; over the band ladder (under_13 < 13_15 < 16_17 < adult, `minor` the coarse reading of the first three), between assured rows at the same level the row with the later `asserted_at` stands, and at the same instant the younger band stands (checked as a table: `Inv_LaterAssuredStands`, `Inv_SameInstantYoungerStands`, `Inv_Ladder*`). Every order, a retraction before its row included, and every reader clock give the same reading | 49,152 | 2,097,152 | the band read at the reader's clock, not the act's `asserted_at`, caught as `Inv_NodesAgree`; and `_plant_equal_level_minor_wins` (the younger band winning whatever the dates), caught as `Inv_Ladder15Then19` |
| `StandingProtection.tla` | CC 5.4.6, CC 3.2 l.961 and the guardianship rule, as ruled: the person's CURRENT band, read from the rows held now with `MinorSuspend`'s band function and no expiry, decides three standing relations: a federation-scope owner-binding concludes nothing while it reads minor; the owner-binding counts for nothing at every scope while it reads minor; a guardianship ends only when it reads adult, which needs an assured row. Two nodes take the rows in any order; holding the same rows they agree; a superseded or outranked minor row stops blocking, a later assured adult lifts (13_15 at 15, then adult at 19), the subject's minor and a contradiction still block; the void still counts what the protection lets go | 16,384 | 1,048,576 | the announcement judged once, when the binding arrives, caught as `Inv_Fold`; and `_plant_equal_level_minor_wins`, caught as `Inv_LaterAssuredAdultLifts` |

| `ConferralEnd.tla` | the causal end of a conferral (CC 2.4.1.1 as ruled, read forward as the Constitution intends it, 2026-11-21; CC 4.5.5), for persist v62.0: B's acts on two devices, each naming the head it is at (an old one included), an end by the grantor or by B (a resignation) naming its head, receipts by the conferrer (for a count, the count), a single co-holder, a receipter the grant names (whose seat the body can end) or the grantee, and a count end that may lift single receipts (compromise) or not (rotation); in the large run an uncited act (names nothing) and a removal of a key. Four readings side by side: the proposal (`under`, `prev`, `ack`), an `ack` set, weak (acts name their head), and weak + the ender's-side receipts. Two nodes in any arrival order (a late act, a re-fold). An act in the end's past stands, one naming the end does not count, nothing concurrent is in force from the end's head unless the ender's side receipted it, the end never voids an act at or before its own head, receipts never revive a later act and never change a count, one say, the member set untouched, convergence. Verdict and traces in `CONFERRAL_END.md` | 1,170,592 | 11,917,636 | `_plant` the end applied to the member set (`Inv_MembersByPast`); `_plant_say` the ender's receipt ignored (`Inv_OneSay`); `_plant_naming` naming the end read as concurrent (`Inv_NamingEndVoid`); `_plant_arrival` an answer latched on arrival (`Inv_Fold`); `_plant_converge` the same, between nodes (`Inv_NodesAgree`); `_plant_own_head` the end voids an act at its own head (`Inv_ForwardNeverVoidsAtOwnHead`); `_plant_receipts` a receipt ignored (`Inv_ReceiptedStays`); `_plant_self` the grantee's own receipt keeps its act (`Inv_NotInForceFromEnd`); `_plant_selflift` a resignation that lifts receipts (`Inv_ReceiptedStays`); `_plant_after_rx` a receipt after the receipter's seat ended (`Inv_NotInForceFromEnd`); `_plant_bulk_after` a receipt after the end (`Inv_NotInForceFromEnd`) |

The constants, diameters and times are in `crates/ciris-kernel/FORMAL_GAPS.md`. `bash tools/tla_check.sh`
runs the small set, and `bash tools/tla_check.sh --large` runs the large one (about five minutes on 32 cores, plus about twenty-five minutes for `ConferralEnd_large`).
`MinorVoid_expiry.cfg` is not part of either run: it adds "and unexpired at D's `asserted_at`" to clause 2, a reading
the rc21 text does not have, and TLC finds `Inv_BackdateOnlyVoids` violated (a minor row, an assured adult proof
dated 2 expiring at 4: D dated 4 is void, the same D dated 3 is not). The Constitution withdrew that clause
because of it, and the configuration is kept as a regression plant. A spec may have further plants,
`<Spec>_plant_<name>.cfg` (and `_large_plant_<name>.cfg`), each of which `tools/tla_check.sh` requires caught:
`MinorVoid_plant_retracted_adult_lifts.cfg` runs the earlier reading of the void, a retracted adult proof still
lifting it (`RETRACTED_ADULT_LIFTS = TRUE`), which the ruling of 2026-11-20 rejected; the two
`_plant_equal_level_minor_wins.cfg` run the earlier equal-level rule, minor winning whatever the dates.
`StandingProtection_void_witness.cfg`, also outside both runs, is meant to fail: TLC shows a node announced while
it holds a witness's minor row that the same witness's newer adult row superseded, a row the void still counts.
`ConferralEnd_prev.cfg`, `_weak_seen.cfg`, `_weak_reaccept.cfg`, `_tie_any.cfg`, `_line_tips.cfg`, `_line_acts.cfg`,
`_receipts_resign.cfg`, `_receipts_past_rotation.cfg`, `_who_none.cfg` and `_receipts_any.cfg`, outside both runs, are meant to fail: each records where two
readings of the end differ, with TLC's trace (`CONFERRAL_END.md`). `_tie_bound.cfg`, `_receipts_past_sound.cfg`,
`_receipt_removed.cfg`, `_reaccept.cfg` and `_owner.cfg`, also outside, pass.
`tools/conferral_xcheck.py` dumps every reachable state of `ConferralEnd_xcheck_all.cfg` and
`_xcheck_none.cfg`, which carry the spec's own answers (`DUMPANS`), and requires
`models/causal_kernel/conferral_end.py` to give the same answer for every act; `tools/tla_check.sh` runs it.
That reference writes persist's fixture `crates/ciris-kernel/tests/fixtures/conferral_end.json`.
`_xcheck_removal.cfg` and `_xcheck_two.cfg` are larger, and are run by hand.
`tools/tla_door_fixture.py` dumps every reachable state of
`Door.tla`, and `crates/ciris-kernel/tests/tla_door.rs` replays each through the crate's door.
These are runs to a bound over models written by the authors of the rules, as the Python checks are.
