# What closes the model: the crate's formal gaps

Each public function of the crate is checked by some of:

- **Lean**: its behaviour is stated and proved in Lean, with the theorem named. Every file is built by
  `proofs/build.sh` with no `sorry` and no axiom beyond core's three. The proof is over a Lean definition of
  the same shape; the Rust is tied to it by cases, not by extraction (last section).
- **TLA+**: a spec in [`models/tla/`](../../models/tla) model-checks it under every interleaving TLC
  reaches, with a planted break TLC must catch (`tools/tla_check.sh`).
- **cases**: the Python models' own cases, or a reference in the tests (`tools/kernel_conformance.sh`).

A function with none of the three is **neither**. Every function in the table is also run against cases.
The lists give the stronger checks.

## The classification

| Function | Lean | TLA+ | Class |
|---|---|---|---|
| `layers::kept` | `kept_is_least`, `door_any_order`, `close_saturated`, `door_spec`, `door_perm` (Causal) | `Door` | Lean, TLA+ |
| `layers::arrive` | `door_any_order`, `door_perm` (Causal) | `Door` (states replayed through the crate) | Lean, TLA+ |
| `layers::conclude` | `conclOf_unique`, `concl_final`, `concl_new_row` (Causal) | | Lean |
| `derived::wins` | `wins_unique` (Causal) | | Lean |
| `derived::slot` | `holder_both_or_neither`, `Slot.descendant_decides` (Causal) | | Lean |
| `derived::counts` | `only_removals_stop_counting`, `sign_after_removal_never_counts` (Causal) | `Cut` | Lean, TLA+ |
| `derived::live_edges`, `reach`, `means` | `two_readers`, `no_own_edge_no_reach` (Causal) | | Lean |
| `derived::tally` | | | cases (`check.py`, `check_cut.py` worlds) |
| `derived::fold_default` | | | neither (CC 3.5.1's four rules as tests, and every order of six rows) |
| `cut::Cut::new`, `status`, `counts` | `CutFix.cut_wfs`, `cut_counts_not_void`, `step_antitone`, `stopped_counts`, `total_between` | `Cut` (the removal half) | Lean, TLA+ |
| `cut::Cut::holder` | `Causal.holder_both_or_neither` over the counting rows | | Lean |
| `line::settle`, `void`, `own_line`, `counted_acts` | `line_voids_old_fork`, `old_fork_void_for_ever`, `sibling_by_acknowledgement`, `sibling_void`, `sibling_waits`, `merge_accepted` (Reader) | `ReaderLine` | Lean, TLA+ |
| `line::versions` | `Versions.counts_built_on`, `counts_fuel_mono`, `void_down_the_line` | | Lean |
| `seat::Seats::new`, `stands` | `SeatWalk.walk_iff_chain`, `unlive_never_reached`, `falls_with_upstream`; `Consent`, `Seat`, `Duty` | | Lean |
| `seat::Seats::holders`, `tips`, `tips_common`, `one` | `SeatWalk.holder_every_tip`, `another_tip_adds_nobody`, `tips_list_no_one_new` | | Lean |
| `seat::seat_rule` (the counts), and `seat::group_count`, the code of those counts, which `seat_rule` calls. `group_count` is correct given members equal to `seat::count_members` and voices equal to `seat::voices` (its `# Contract`); `SeatCount`'s `yes U signed mem named` counts over a list, which equals the Rust's set count when the list has no duplicates and holds every voice; `wsum` is over `Nat`, and the Rust sums in `u128` | `SeatCount.no_key_admits_itself`, `yes_mono`, `met_mono`, `unanimous_two_removes_nobody`, `unanimous_others_remove`, `self_admit_one_never_removes`, `duty_withdrawal_needs_two`, `weighted_mono`; `count_is_final_against_members`, `one_signature_never_removes` | | Lean |
| `seat::met` | `SeatCount.met_mono`, `strict_one_voice`; `Duty.majority_iff` | | Lean |
| `seat::members_at`, `members_in`, `members_in_scopes`, `count_members`, `seat::conclude` (`members_at` read once per heads, object and scope within one pass) | `membersAt_function`, `counted_over_named_head` (RosterHead) | | Lean |
| `seat::left_in_past` | `leaving_binds_by_past` (RosterHead) | | Lean |
| `seat::voices` | the cosignature rule of `Harden.lean` | | Lean |
| `window::rule`, `outcome` | `dishonest_never_stands`, `stands_is_table_over_all_not_late`, `quorum_closed_final` (Recount); `WindowTable.before_close`, `at_once_ignores_close`, `default_needs_close`, `landings_agree` | | Lean |
| `head::View::counts_at`, `settled`, `missing`, `receipts`, `carried` | `ack_blocking_quorum`, `say_settled_final`, `countsAt_final`, `countsAt_local`, `symmetric_say_forced`, `say4_closed`, `later_head_changes_nothing` (Settled) | `Purge` | Lean, TLA+ |
| `head::purge` | `checkpoint_conclusions`, `checkpoint_resume`, `pruned_view_closed`, `pruned_view_answers` (Settled) | `Purge` | Lean, TLA+ |
| `head::View::window`, `answers`, `tips` | | | cases (`check_purge.py`, 400 replays) |
| `key_end::live`, `ended`, `well_formed` | `live_own_rows`, `live_perm`, `ended_not_live`, `ended_stays_ended`, `bound_reads_row` (KeyEnd) | | Lean |
| `key_end::retained` | `Retained.retained_down_closed`, `named_retained`, `revocations_kept`, `dropped_unnamed`, `retained_mono` | | Lean |
| `key_end::conclude_rule`, `successor` | | | cases (`check_key_end.py`, 5,670 worlds) |
| `trust::reaches`, `honours` | `TrustSet.reaches_mono_budget`, `verdict_is_the_capped_walk` (parent) | `TrustWalk` (termination with cycles, and agreement with the Lean walk) | Lean, TLA+ |
| `trust::EdgeIndex` (`new`, `reaches`, `honours`) | the theorems of `trust::reaches` and `honours`: the same walk, each key's edges read as their run in the index | | cases (against the walk as first written, `tests/fast_paths.rs`) |
| `ranked::ranked` | `Election.free_perm`, `free_agrees` (parent), without a declared order | | Lean (no declared order); cases (declared) |
| `ops::least`, `greatest` | `Ops.leastNoTie_perm` (G1), `leastNoTie_none_iff` (G2), `leastNoTie_some_iff` | | Lean |
| `ops::sel`, `sel_before`, `group_by`, `min_of`, `max_of`, `one`, `count`, `sum_per`, `in_range`, `fix` | | | cases (`kernel_lib.py`, 7,968 inputs; `reexpress.py`, 17,886) |
| `graph::Graph` (`in_past`, `concurrent`, `frontier`, `past`, `ancestors`) | | | cases (the eager closure as oracle, 301,219; the frontier's walk against the pairwise frontier and duplicate ids, `tests/fast_paths.rs`, 24,373; rows with cycles of names wait exactly when `kept` leaves them out, `tests/cycle.rs`, 54,160) |
| `graph::Graph::waiting`; the waiting rule of `layers::conclude`, `Concluded::with` and `head::View::new` (a row on a cycle of names, or naming one, concludes nothing and a view leaves it out) | no theorem: the proofs assume a kept set, which has no cycle | | cases only (`tests/cycle.rs`: rows wait, and views hold, exactly what `kept` keeps; 54,160 and 3,000 cases) |
| `ops::rule`, `seat::covers`, `seat::Obj::from_reference`, `is_identity_reference` | | | neither (unit tests) |

**Counts**, by row of the table:

| Class | Rows |
|---|---|
| proved in Lean | 26 |
| of which also model-checked in TLA+ | 8 |
| model-checked in TLA+ only | 0 |
| cases only | 5 |
| neither | 2 |

The three statements proposed earlier (G1, G2, G3) are proved: `Ops.leastNoTie_perm`, `Ops.leastNoTie_none_iff`
and `Versions.counts_built_on`. None was false. Core Lean 4.14 has no lemmas for `List.eraseDups`, so
`Ops.lean` proves the ones G1 and G2 need. `proofs/proposed/` is gone.

## What the new proofs and specs state

| File | What it proves or checks |
|---|---|
| `proofs/CutFix.lean` | For any antitone step, the iteration from the empty set climbs and stays below its image, and where it stops it is a fixed point of the step applied twice. What it reports as counting counts whatever the undecided cuts do. The cut's step (not voided, and enough voices not voided) is antitone. |
| `proofs/SeatWalk.lean` | Within `n` passes the walk reaches a pair at depth `d` iff a chain of `d` links leads to it from a root and `d < n`. A pair not live by the two consents is never reached, and a conferred seat falls with its upstream. With several tips, a holder is held at every tip, and a further tip adds nobody. |
| `proofs/SeatCount.lean` | No key admits itself, and a further signature never lowers a count. Every non-exact policy is met by more voices whenever fewer met it. Under `unanimous` two members remove nobody, while every other member of three or more does. Under `open:self_admit` one voice never removes, and a duty withdrawal never stands on one voice. |
| `proofs/WindowTable.lean` | Before the close the outcome is "open" or an at-once clause's, and an at-once outcome ignores the close. The default needs the close, and landings over one past agree. |
| `proofs/Retained.lean` | The retained rows are closed downwards, so compaction leaves a kept set. Every revocation is kept, a dropped row is in no seed's past, and fewer seeds retain fewer rows. |
| `proofs/Versions.lean` | Built on, with the recursion's fuel not mattering once it suffices, and void down the line. |
| `proofs/Ops.lean` | The least element does not depend on the list's order, and a refused tie is a real tie. |
| `models/tla/Door.tla` | Under any arrival order, with repeats and a row naming one never offered, the held set is the least closed set over what was offered. Rows wait and are never refused, held only grows, and everything eventually kept is kept. |
| `models/tla/Cut.tla` | Under any arrival order, an incremental verdict kept as rows arrive equals removal by causal past. Another key's rows are untouched, and a row signed after the removal it names never counts. A row stops counting only when a removal lacking it arrives, and then for good. |
| `models/tla/ReaderLine.tla` | Per reader, the void set is a function of what that reader holds and acknowledged. With no acknowledgement nothing is void, so two versions of one head wait as tips. With one, every version that names only heads in the acknowledged act's past is void for that reader, the fork and a sibling of the acknowledged act included. The reader's own line is never void, and void lasts for ever. |
| `models/tla/Purge.tla` | Under any order of three receipts and two cuts, purging once the act is settled changes no answer. A settled act counts, the threshold is exact, and settled is final. |
| `models/tla/TrustWalk.tla` | Over a graph with two cycles and a short path with no budget, the walk always terminates, takes keys in any order, and agrees with the Lean `walk` when it stops. Budgets only rise. |
| `models/tla/MinorVoid.tla` | A rule of the Constitution, not of the crate: CC 3.2 at v1.0-rc21, the void of a duty appointment made to a minor. A store keeps a running summary as rows arrive in any order with its clock ticking; its verdict is the fold over the held rows, and a node folding the same rows at any other instant agrees. Backdating D only voids it, a retraction changes nothing, a minor row superseded by its signer's newer adult row still voids, a self-declared adult lifts nothing, and a later adult proof never revives a void. `proofs/MinorVoid.lean` proves the same over lists. |
| `models/tla/MinorSuspend.tla` | A rule of the Constitution, not of the crate: the current age band about a person at an act's own instant, which holds a duty seat suspended while it reads minor (CC 3.4.11 read-union at v1.0-rc21, CC 3.5.1 rules 2 and 3, CC 2.4.1.1, as ruled on 2026-11-20). A store keeps each signer's rows and the retractions it has seen as rows arrive in any order, a retraction before its row included. Its reading at an act's `asserted_at` is the set function, and a node reading at any reader clock agrees. A row or retraction dated later changes nothing; per signer the newest row stands and the lowest id at one instant; graduation leaves the void untouched; the subject lowers and never raises, a higher level outranks a lower, and at an equal level minor wins. |
| `models/tla/StandingProtection.tla` | CC 5.4.6: a federation-scope owner-binding concludes nothing while a minor row about the person stands, read on the rows held now, never at an instant. Two nodes, each taking the rows in any order: they agree on the same rows; the kept announcement is the set function; no order leaves a minor announced; a minor row after the binding pulls it back, and the last withdrawal restores it. |

TLC at this commit. The small configuration (`<Spec>.cfg`) runs in `./check.sh` and CI. The large one
(`<Spec>_large.cfg`) is run locally with `bash tools/tla_check.sh --large`. Both are on a 32-core machine, with
`-workers auto`, and every plant is caught at both bounds.

| Spec | Small: constants | Distinct states, diameter, time | Large: constants | Distinct states, diameter, time | Plant |
|---|---|---|---|---|---|
| `Door` | 10 rows | 1,024, 11, 1 s | 17 rows | 131,072, 18, 104 s | the door drops a row not yet placeable |
| `Cut` | 2 keys, chains of 3 | 2,048, 12, 1 s | 3 keys, chains of 4 (19 rows) | 524,288, 20, 31 s | judged once, on arrival |
| `ReaderLine` | 2 readers, lineage of 4 | 13,924, 19, 1 s | 3 readers, lineage of 5, SYMMETRY over readers | 551,300, 31, 21 s | one reader's acknowledgement voids for all |
| `Purge` | 2 acts, 3 members, 2 cuts each | 2,304, 13, 1 s | 2 acts, 5 members, t = 3, 3 cuts each | 147,456, 19, 2 s | purging before settled |
| `TrustWalk` | every subgraph of 9 edges over 4 keys | 2,480, 5, 2 s | every subgraph of 16 edges over 7 keys (65,536 graphs) | 454,016, 8, 8 s | each key expanded once |
| `MinorVoid` | 1 witness, D dated 1..4 (11 rows), clock 0..6 | 14,336, 18, 2 s | 2 witnesses, D dated 1..6 (16 rows), clock 0..8 | 589,824, 25, 7 s | the adult proof judged at the node's clock |
| `MinorSuspend` | 2 provider witnesses (one with a same-instant tie), X dated 1..4 (12 rows), clock 0..5 | 24,576, 18, 2 s | and a government witness, X dated 1..6 (17 rows), clock 0..7 | 1,048,576, 25, 116 s | the band read at the reader's clock |
| `StandingProtection` | 2 nodes, a binding, 2 minor rows and their withdrawals (5 rows) | 1,024, 11, 1 s | and a third minor row, its withdrawal and the binding's (8 rows) | 65,536, 17, 5 s | judged once, at the binding's arrival |

Each space is exhausted at its bound: TLC ends with no state left on the queue. In Door and Cut the state is
the set of rows offered, so the count is 2^rows exactly. A GitHub-hosted runner, with fewer cores, takes about
a minute for the small set; the large set takes about three minutes here.

**Tied to the Rust by trace.** `tools/tla_door_fixture.py` dumps every reachable state of `Door.tla` with TLC.
`tests/tla_door.rs` then replays each state through `layers::kept` and `layers::arrive` in two orders, 384
comparisons with no disagreement. `tools/tla_check.sh` fails if the dump no longer matches the committed fixture.

## The sibling of the acknowledged head: one reading

Two models once read the reader's line differently. `checkpoint.py` (and `line.rs`, `Reader.lean`) let a
sibling of the acknowledged version wait as a tip. `purge.py` (and `head.rs`) held it void. CC 2.7.8 settles
it with two sentences, each for one reader state:

- "Two versions of one head wait as tips." This is for a reader with no acknowledgement on that line.
- "A reader that has acknowledged a head holds void every counted act that names an older head and is not in
  that head's past … That voiding is the reader's own and binds nobody else."

A sibling S of the acknowledged act H names their common predecessor, which is older than H, and S is not in
H's past. So S is void for the reader that acknowledged H, and waits as a tip for a reader that did not. A
version built on S is void for the first reader too (CC 2.7.7, built on). KERNEL.md 7 states the same.
KERNEL.md 8a's "a sibling of the acknowledged head waits as a tip" is now read as the case of a reader with no
acknowledgement.

The crate now carries one reading. `line.rs` compares a version's heads with the acknowledged act itself, so
`checkpoint.py` (`line_behind`, `versions`), `Reader.lean` (`olderThan`, `behind`) and `purge.py` agree.
`Reader.sibling_by_acknowledgement` states both cases; `sibling_void` and `sibling_waits` state each.
`ReaderLine.tla` checks `Inv_TipsWaitWithoutAck`, `Inv_OlderVoidWithAck` and `Inv_SiblingVoid`.
`attacks.py` test 4 now records that a reader who acknowledged the newest honest row is not moved even by a
fork from the head that row is counted over.

## What is still open, ranked by risk

| Rank | Gap | Smallest statement or model that closes it |
|---|---|---|
| 1 | `graph::Graph`, the lazy, budgeted closure | `theorem in_past_iff (G a b) : G.in_past a b = true ↔ TransGen G.parent a b`, through Kani harnesses on the Rust (it is the crate's own algorithm, not the model's) |
| 2 | `key_end::successor` | `theorem successor_both_or_neither : two concurrent rotations name different keys → successor = none` (P5a, run today) |
| 3 | `head::View::window` and the purge of an open window | `theorem purge_keeps_open : window S o now = .open → whole (purge S now) o`, or a `Purge.tla` variant with a window and a clock |
| 4 | `derived::fold_default` | `theorem fold_default_perm` and `theorem fold_default_per_signer` (no row of one signer moves another's winner) |
| 5 | `ranked::ranked` with a declared order | `theorem ranked_declared_function : ballots.Perm b' → ranked ballots opts = ranked b' opts` |
| 6 | `Obj::from_reference` | test vectors generated from `signed_object_v2.cddl` (parent), every form, valid and not |
| 8 | tables as data (`SeatLaw`, `WindowSpec`) | a check that every cell traces to a table cell or a quoted sentence |

## Tying the Rust to the Lean

| Way | What it gives | Cost | Fit to this crate |
|---|---|---|---|
| Differential tests generated from the Lean definitions | the Rust agrees with the definitions the theorems are about, case by case, to a bound | days per module; a Lean `main` prints the fixtures' JSON | good: the test side exists |
| Traces from TLC (this round, `Door`) | the Rust agrees with every reachable state of a spec | hours per spec, as `tla_door_fixture.py` shows | good, for specs with state |
| Aeneas or hax | a proof that the Rust is a Lean function | months; closures, `dyn Fn`, `OnceCell` and `BTreeMap` are outside their comfortable subset | poor today |
| Verus | proofs about the Rust itself | months, with the proofs done again in a second system | poor |
| Kani | bounded model checking of the Rust | days; harnesses for the closure and `from_reference` | good for gaps 2 and 7 |

**Recommendation, unchanged:** differential tests generated from the Lean definitions. TLC traces give the
same tie for each spec at little cost, so the two together cover the Lean files and the specs. Kani is worth a
day or two for the closure.
