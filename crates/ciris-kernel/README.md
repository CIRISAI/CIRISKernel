# `ciris-kernel`

The causal kernel of [`kernel/KERNEL.md`](../../kernel/KERNEL.md) (CC 2.7 "The kernel") as a Rust crate of pure
functions over an abstract row graph. It has no I/O, no clock, no cryptography and no serialisation. It is
`#![no_std]` with `alloc`, has no dependencies, and forbids `unsafe`. It builds for a target with no standard
library (`thumbv7em-none-eabihf`) and for `wasm32-unknown-unknown`.

The caller supplies rows through the [`Row`](src/lib.rs) trait: a digest, the digests the row names, and its
signer. Each answer reads further fields through a small trait or through closures, as `kernel_lib` takes field
names as parameters. The caller verifies signatures and decodes bytes before a row reaches the kernel. Every
role, scope, policy, window and constant is data the caller passes in ([`SeatLaw`](src/seat.rs),
[`WindowSpec`](src/window.rs)). A reduce that meets a tie between two different rows refuses with
[`Tie`](src/ops.rs); nothing is broken by position.

```
cargo build --offline --release -p ciris-kernel
bash tools/kernel_conformance.sh          # the differential tests, one line per run and a total
bash tools/kernel_crate_plants.sh         # eight planted breaks, each must be caught
python3 -I tools/kernel_fixtures.py       # regenerate the fixtures from the Python models
```

`./check.sh` at the repository root runs all of these as its last four steps.

## Layout

| Module | KERNEL.md | What it states |
|---|---|---|
| [`ops`](src/ops.rs) | 4 | select, group and reduce (least, greatest, min, max, one, count, sum), interval, table cell, bounded repeat |
| [`graph`](src/graph.rs) | 2, 4 | the closure over what rows name: a row's past, concurrency, the frontier |
| [`layers`](src/layers.rs) | 3 | **kept** (the monotone door), **concluded**, and the same two run as rows arrive |
| [`derived`](src/derived.rs) | 5, 6 | the order on kinds, the slot, removal by causal past, the walk over live edges, the tally |
| [`cut`](src/cut.rs) | 6 rule 4, 5 | the cut, solved by the well-founded fixed point; who holds a slot under it |
| [`line`](src/line.rs) | 7, 8a | built on; the reader's own acknowledged line; roster versions |
| [`seat`](src/seat.rs) | 5 (**stands**), 7 | the seat as two consents, the bounded walk, members at the head a row names, tips wait, the duty law as data |
| [`window`](src/window.rs) | 5 (**window**) | receipt, landing and recount |
| [`head`](src/head.rs) | 3, 3a | answers by head, receipts, one say, **settled**, **missing**; checkpoint and purge |
| [`key_end`](src/key_end.rs) | 5 (two notions of time) | a key's own end; the rows that lapse |
| [`trust`](src/trust.rs) | 5 (**stands**), CC 4.4.3.34 | the reader's trust walk over acceptance edges |
| [`ranked`](src/ranked.rs) | 5 (the door's parameters) | the ranked count, with a declared order and without |

## Each public function, its clause and its proof

"Model" is the Python function the differential tests compare against. Lean files are in [`proofs/`](../../proofs)
unless marked as the parent's.

| Function | KERNEL.md clause | Lean theorem | Model |
|---|---|---|---|
| `ops::sel`, `sel_before`, `group_by`, `least`, `greatest`, `min_of`, `max_of`, `one`, `count`, `sum_per`, `in_range`, `rule`, `fix` | 4, the operators; "a tie between two different rows is refused" | none (operators) | `kernel_lib.sel`, `group`, `in_range`, `rule`, `fix` |
| `graph::Graph` (`in_past`, `concurrent`, `frontier`, `past`), `ancestor_ids` | 2, "the only order is what rows name"; 4, closure | `Causal.lean` definitions | `kernel_lib.ancestors`, `concurrent`, `frontier`, `past` |
| `layers::kept` | 3, kept: "the least set closed under the door" | `kept_is_least`, `door_any_order`, `close_saturated`, `door_spec`, `door_perm` | `causal_kernel.kept` |
| `layers::conclude` | 3, concluded: "one solution … final once the row is kept" | `conclOf_unique`, `concl_final`, `concl_new_row` | `causal_kernel.concluded` |
| `layers::arrive` | 2, "judging each row as it arrives … is not a function of the rows" (the door waits instead) | `door_any_order`, `concl_final` | `causal_kernel.arrive` |
| `derived::wins` | 6 rule 1, a fixed order on kinds | `wins_unique` | `causal_kernel.wins` |
| `derived::slot` | 6 rules 2 and 3 | `holder_both_or_neither`, `Slot.descendant_decides` | `causal_kernel.slot` |
| `derived::counts` | 6, "a row of a removed key counts when the removal has it among its ancestors" | `only_removals_stop_counting`, `sign_after_removal_never_counts` | `causal_kernel.counts` |
| `derived::live_edges`, `reach`, `means` | 1, "no trust set among the inputs" | `two_readers`, `no_own_edge_no_reach` | `causal_kernel.live_edges`, `reach`, `means` |
| `derived::tally` | 5, **tally**; "a voice that says two things says nothing" | `counted_over_named_head` (RosterHead) | `causal_kernel.tally` |
| `cut::Cut` (`status`, `counts`, `holder`) | 6 rules 4 and 5 | `later_head_changes_nothing`, `Rows.later_seat_is_forward` (Settled); the fixed point is run, not proved | `cut.Cut` |
| `line::settle`, `void`, `own_line`, `counted_acts` | 7, "a reader that has acknowledged a head holds void …"; 8a, "a counted row counts only if every counted row it is built on counts" | `line_voids_old_fork`, `old_fork_void_for_ever` (Reader, Harden3) | `checkpoint.settle`, `void` (group checkpoint off) |
| `line::versions` | 7, two versions of one head wait | `membersAt_function` | `checkpoint.versions` (group off). Not in the fixtures; see below |
| `seat::Seats` (`stands`, `holders`, `one`, `tips`, `tips_common`) | 5, **stands**: the seat, the bounded walk; 7, tips wait | `seat_is_two_consents`, `holder_first_stands`, `only_bound_voices_end` (Consent); `means_is_seat_walk`, `no_acceptance_no_seat`, `third_key_cannot_end` (Seat); `Duty.lean` | `seat.Seats` |
| `seat::seat_rule` | 5, who may place a duty; 8a, the hardening rules | `count_is_final_against_members` (Consent), `one_signature_never_removes`, `readmission_needed` (RosterHead), `Harden*.lean`, `Duty.lean` | `seat.seat_rule` |
| `seat::members_at`, `members_in`, `left_in_past`, `voices`, `met` | 5 and 7, "the members are those at the head the row names" | `membersAt_function`, `counted_over_named_head`, `leaving_binds_by_past` (RosterHead) | `seat.members_at`, `left_in_past`, `voices`, `met` |
| `window::rule`, `outcome` | 5, **window**, recount | `dishonest_never_stands`, `stands_is_table_over_all_not_late`, `quorum_closed_final` (Recount) | `window.rule`, `window.outcome(…, "recount")` |
| `head::View` (`counts_at`, `carried`, `settled`, `missing`, `receipts`, `window`, `answers`) | 3, final by acknowledgement; 6 rule 6, one say | `ack_blocking_quorum`, `say_settled_final`, `countsAt_final`, `countsAt_local`, `symmetric_say_forced`, `say4_closed` (Settled) | `purge.View` |
| `head::purge` | 3a, checkpoint and purge | `checkpoint_conclusions`, `checkpoint_resume`, `pruned_view_closed`, `pruned_view_answers` (sufficient); `count_view_not_closed` (the bare answer is not enough) | `purge.purge` |
| `key_end::well_formed`, `conclude_rule`, `live`, `ended`, `retained`, `successor` | 5, two notions of time; a key's own end | `live_own_rows`, `live_perm`, `ended_not_live`, `ended_stays_ended` (KeyEnd) | `key_end.WF`, `RULE`, `live`, `ended`, `retained`, `successor` |
| `trust::reaches`, `honours` | 5, **stands**: "the remaining depth is the lesser …, the classes intersect, and a cycle is visited once" (TEXT.md; CC 2.7.5) | `TrustSet.lean` (parent repository): `reaches_mono_budget`, `verdict_is_the_capped_walk`, the worked world | none in Python; compared with the Lean `walk` transcribed |
| `ranked::ranked` | 5, "an election declares no order, so its door seats nobody on a tie for weakest" | `Election.free_perm`, `free_agrees` (parent repository) | `reexpress.ranked` |

## Conformance

`tools/kernel_fixtures.py` imports the Python models, runs their own cases and writes every answer to
`tests/fixtures/`. The Rust tests rebuild the same rows and compare answer by answer. At this commit:

| Run | Source of the cases | Cases | Disagreements |
|---|---|---|---|
| operators | every reducer over every set of up to three rows of a pool of 18; every interval over four values | 7,968 | 0 |
| re-expressed decisions | `reexpress.py`'s six decisions over small input spaces, written again with `ops` | 17,886 | 0 |
| causal | `check.py` section 1: 6,606 sets of up to six rows of its two pools; kept, concluded, slots, kinds, counts, reach, meaning, tally; and each set in two further arrival orders | 60,016 | 0 |
| cut | `check_cut.py` section 1 at its own bounds: status of every row, both slot holders, landings, tallies | 20,985 | 0 |
| seat, line, tips, window | 134 scenarios: every scenario `attacks.py`'s 34 tests conclude under the seat, window and route rules, and the 27 rows of the window adversary table; conclusions, cut, live seats for every reader, stale acts, members, duty holders, tips, window outcomes under recount | 3,556 | 0 |
| checkpoint and purge | `check_purge.py`: 400 replays (200 under each reading) over the nine histories, the first purge row by row, and that purging changes no answer | 1,768 | 0 |
| a key's own end | `check_key_end.py`: 5,670 worlds at six instants; kept, concluded, live, ended, successor, reach, score, retained | 215,460 | 0 |
| trust walk | the `TrustSet.lean` worked world, and the Lean `walk` over generated graphs | 127,015 | 0 |
| **total** | | **454,654** | **0** |

Eight planted breaks, one in each of `derived`, `cut`, `seat`, `head`, `key_end`, `line`, `window` and `ranked`,
are each caught (`tools/kernel_crate_plants.sh`, run on a copy).

## What this crate leaves out, and why

- **The rejected rules.** The group checkpoint (`checkpoint.py` with `group=True`) and the window's `void` and
  `contest` rules are kept in the models only to show why they are refused (KERNEL.md 5, 8a). They are not here.
- **The models' plants.** The `MUT` switches in `seat.py` and `key_end.py` are deliberate breaks for the
  Python checks; the crate implements the rule only.
- **Copying and audience** (`route.py`, the **missing** answer as routing, the copy rule of KERNEL.md 5). The
  differential tests conclude `route.py`'s message and acknowledgement rows with the crate's `members_at`,
  but routing itself is not stated here. It reads placement data that KERNEL.md 9 lists as not yet table data.
- **A writer's keys** (`keyplane.py`) and **private rooms** (`roomkey.py`). KERNEL.md 7b says the kernel is not
  changed by a room key, and the binding is cryptography. The key plane is a fold the caller can write with `ops`.
- **The fold default** (CC 3.5.1: one signer's own chain, the later signed instant, the lower id on a tie). It is
  a cell of the expression language, which is not carried here.
- **The roster versions rule** `line::versions` is stated and compiles, but its cases live in
  `models/roster_fork`, whose rows are not the kernel's; it has no fixture yet.
- **What KERNEL.md marks open**: a roster version naming several heads on the wire, how a second consent
  travels, the cosignature attached against a node's clock, the least set a node must keep, whether a withdrawn
  receipt still blocks (treated as blocking, as the models do), and the eight folds a reaction calls that no
  cell defines.
- **Signature verification, CBOR and COSE decoding, storage and transport.** The caller's.

## Costs a caller should know

`graph::Graph` holds each row's past as a bitset, so it is quadratic in the number of rows it is built over.
The seat and window build nested graphs over a row's past to read the members at a head. A store should call
the kernel over the rows an answer reads (its light cone), not over everything it holds.
