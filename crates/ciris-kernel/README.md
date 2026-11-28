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
bash tools/kernel_crate_plants.sh         # the planted breaks, each must be caught
python3 -I tools/kernel_fixtures.py       # regenerate the fixtures from the Python models
```

`./check.sh` at the repository root runs all of these as its last four steps.

## Layout

| Module | KERNEL.md | What it states |
|---|---|---|
| [`ops`](src/ops.rs) | 4 | select, group and reduce (least, greatest, min, max, one, count, sum), interval, table cell, bounded repeat |
| [`graph`](src/graph.rs) | 2, 4 | the closure over what rows name: a row's past, concurrency, the frontier |
| [`layers`](src/layers.rs) | 3 | **kept** (the monotone door), **concluded**, and the same two run as rows arrive |
| [`derived`](src/derived.rs) | 4, 5, 6 | the order on kinds, the slot, removal by causal past, the walk over live edges, the tally, the fold default of CC 3.5.1 |
| [`cut`](src/cut.rs) | 6 rule 4, 5 | the cut, solved by the well-founded fixed point; who holds a slot under it |
| [`line`](src/line.rs) | 7, 8a | built on; the reader's own acknowledged line; roster versions |
| [`seat`](src/seat.rs) | 5 (**stands**), 7 | the seat as two consents, the bounded walk, members at the head a row names, tips wait, the duty law as data |
| [`window`](src/window.rs) | 5 (**window**) | receipt, landing and recount |
| [`head`](src/head.rs) | 3, 3a | answers by head, receipts, one say, **settled**, **missing**; checkpoint and purge |
| [`key_end`](src/key_end.rs) | 5 (two notions of time) | a key's own end; the rows that lapse |
| [`trust`](src/trust.rs) | 5 (**stands**), CC 4.4.3.34 | the reader's trust walk over acceptance edges |
| [`ranked`](src/ranked.rs) | 5 (the door's parameters) | the ranked count, with a declared order and without |

Which functions are proved in Lean, model-checked in TLA+, checked only by cases, or neither, is in
[`FORMAL_GAPS.md`](FORMAL_GAPS.md). How the crate and persist differ, and what each difference means, is in
[`DIFFERENCES.md`](DIFFERENCES.md).

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
| `line::versions` | 7, two versions of one head wait | none; run in `roster_fork` | `checkpoint.versions` (group off) |
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
`tests/fixtures/`. The Rust tests rebuild the same rows and compare answer by answer. Each run prints its
name, its cases and its disagreements, and the step fails if a listed run does not report. The figures below
are the `conformance` lines of CI's `cargo test --release` on commit 69920cf (PR #45), sorted; the script is the authority:

| Run, as `tools/kernel_conformance.sh` names it | Cases | Disagreements |
|---|---|---|
| a key's own end (check_key_end.py worlds) | 215,460 | 0 |
| a signer's claim by what its rows name (the rule's cases and every order of seven rows) | 5,053 | 0 |
| a view of a store with cycles of names, against what kept keeps | 3,000 | 0 |
| a weighted count with a further voice | 12 | 0 |
| causal (check.py worlds) | 60,016 | 0 |
| checkpoint and purge (check_purge.py replays) | 2,122 | 0 |
| conclude over rows with cycles of names, against conclude over what kept keeps | 54,160 | 0 |
| cut (check_cut.py worlds) | 20,985 | 0 |
| fold default (CC 3.5.1 rules and every order of six rows) | 724 | 0 |
| group_count against the seat rule over the ballot's rows and the count it replaced | 40,000 | 0 |
| head::View read through its indexes against the scanned one (purge.json histories) | 5,980 | 0 |
| held_view::differential over purge.json histories (in order, reversed, shuffled; resumed) | 1,456 | 0 |
| kernel_lib operators | 7,968 | 0 |
| key_end::retained against the per-row reading of ended | 18,000 | 0 |
| lazy closure against the eager closure | 301,219 | 0 |
| line::settle against the settle it replaced | 12,000 | 0 |
| line::versions (roster_fork worlds, every set to three versions, every reader) | 77,402 | 0 |
| members at a head, count_members and seat::conclude against the rows | 40,875 | 0 |
| one offer seating many: its consenting keys | 2,000 | 0 |
| one row under a root grant and an owner binding (check_conferral_two.py case table, acc) | 52 | 0 |
| one row under a root grant and an owner binding, one row not held (undecided, never a wrong bit) | 161 | 0 |
| recorded rules: other_rules | 848 | 0 |
| recorded rules: rosters | 52,238 | 0 |
| recorded rules: witnesses | 484 | 0 |
| reexpress.py decisions over the operators | 17,886 | 0 |
| room content after a seat ends (conferral_content.py case table) | 172 | 0 |
| room content, folded row by row with changed | 34,751 | 0 |
| room content, histories built row by row (conferral_content.py) | 37,643 | 0 |
| room content, one row not held (undecided, never a wrong bit) | 382 | 0 |
| room content with no end held (counted where seated; in force unless retracted) | 37,643 | 0 |
| seat, line, tips, window (attacks.py and window.py scenarios) | 7,944 | 0 |
| the counts CC 3.3.4 and CC 4.4.3.6 state, on their own cases | 24 | 0 |
| the cycle reading: a walk that passes no key twice, against the Lean walk | 46,800 | 0 |
| the end of a conferral (conferral_end.py case table) | 127 | 0 |
| the end of a conferral: one receipt naming several acts, presented as one row per act | 9 | 0 |
| the end of a conferral, one row not held (undecided, never a wrong bit) | 336 | 0 |
| the fold at tips: self-admission, a head one key wrote, tips that differ in policy | 7 | 0 |
| the frontier's walk against the pairwise frontier; duplicate ids | 24,373 | 0 |
| TLC's reachable states of Door.tla, replayed through the crate's door | 3,072 | 0 |
| trust::reaches and derived::reach against the walks they replaced | 6,012,046 | 0 |
| trust walk against the Lean walk | 127,008 | 0 |
| trust walk, TrustSet.lean worked world | 7 | 0 |
| **total, 42 runs** | **7,272,445** | **0** |

A **recorded rule** is how a world whose conclusion rule belongs to the instance is brought in. The rule of
a witness or a roster instance is table data and the model's own code, not the kernel. So the model's verdict
for every (row, concluded ancestors) is recorded. The crate's own layers then run over that table and must
ask no question the table lacks. What these runs check is the kernel's door, recursion and arrival, and the
derived answers over the model's conclusions. The answers the witnesses compute are per-case functions of
the model and are not ported.

`tools/kernel_crate_plants.sh` plants 387 breaks, one at a time on a copy of the crate, and each must fail a
test. Count them with `grep -c '^plant' tools/kernel_crate_plants.sh`; the script prints how many were caught.

**The cycle reading.** "A cycle is visited once" (CC 2.7.5) has two readings. Under the first, a walk never
passes the same key twice. It equals the Lean `walk` on every case, since a key reached again has no more
budget than before (`reaches_mono_budget`). Under the second, each key is expanded once in the whole walk,
with the budget it was first reached with. That reading differs from the Lean `walk` on 48 of 46,800 cases. The witness has no cycle:
the reader reaches A first by an edge allowing no further hop, then through B with budget to spare, and
only the second path reaches C. The crate implements the first reading: a key is expanded again only with
more budget.

### The end of a conferral

`conferral::answers` is checked against the case table of `models/causal_kernel/conferral_end.py`
(`tests/fixtures/conferral_end.json`; 43 cases, each with its rows listed in every order the fixture gives
and in reverse). That reference is the weakR reading of `models/tla/ConferralEnd.tla`, and is compared with
that spec state by state.

A second run withholds one row at a time from the caller's past. Every act is then either undecided, naming
the row that is missing, or judged exactly as it is over the rows that are held.

The deputy gates (an act under an onward hop needs sub-delegation on the edge above that hop; at most
`Standing::deputy_depth` `via` hops from the grantee's edge; both read from the rows' `via`, with no mark of
an edge) are in seven of those cases. The TLA+ spec has one deputy edge and does not reach them.

### One row under a root grant and an owner binding

`standing::answers` is checked against the case table of `models/causal_kernel/check_conferral_two.py`
(`tests/fixtures/conferral_two.json`; 42 cases, 21 under its reading `acc`, 6 of two owners and 15 of a deputy, rows as listed and in reverse): per
act and owner whether it counts and is in force, the binding it stands under and the rule that decides under
each record, or why it counts for nobody. A second run withholds one row at a time. Cases only: the Python
run of every state checks the reference, not the crate.

The fixture is also for adopters. Each case has `rows` (`id`, `kind`, `signer`, `names`, and `head`, `of`,
`lifts`, `target`, `via` where a rule reads them), `reader_acks`, `other_standing`, `who`, `orders`, and
`answers`: for every act `counted`, `in_force` and the `rule` that decides it. A case whose `refused` is not
null holds a row the Constitution's text refuses at the door (`act_names_no_head`); an adopter runs the cases
whose `refused` is null.

### A private room's row door, for a verifier

`tests/fixtures/room_keys.json` is written from `models/causal_kernel/room_key_vectors.py` (61 cases: 16 of a
voice's row, 45 of a node's,
CIRISConstitution#224, CC 3.1.3.2) for a verifier's pure check of one row of a room: the signer is a room key at
all (its key record names a room), its record names this room, the row names exactly one head of the voice's key
roster under `refs.also.voice`, and the key is a live key of the voice at that head. The roster fold stays the
kernel's: each case carries the view it gives.

- `roster_rows`: the voices' own rosters (seat rows of scope `key` over the voice, as `seat.py` writes them),
  from which every view is folded; `records`: every key record (`key`, `room` or null, `identity_type`).
- each case: `name`, `ledger`, `membership` (`private` or `public`), `room`, `row` (`id`, `kind`, `room`, `iss`
  the voice, `kid` the key that signed, `refs.also.voice` the heads named), `records` (the signer's record, or
  none), `view` (`voice`, `heads`, `live_keys`: the voice's live room keys at that head by `seat.members_at`,
  empty unless exactly one head is named), `verdict` (`admitted`, `refused` or `concludes_nothing`), `refusal`
  (`room_row_signer_not_room_key`, `room_key_other_room`, `room_row_voice_head_malformed`, or null), and `kernel` (the kernel's own reading of the
  live-key clause, `roomkey.rule`, which the generator checks against the verdict).
- a node's row (`arm` `node`; ruled on #224): one signed by a room key whose record says `node`, `iss` = `kid`,
  naming exactly one owner-binding under `refs.also.under` (else refused `room_row_owner_binding_malformed`) and
  exactly one head of the owning voice's key roster under `refs.also.voice` (else `room_row_voice_head_malformed`).
  `node_rows` is the room it is read in, each case's `rows` the rows added to it, and `view` the facts the kernel
  folds over the row's own past with rule 4 for a concurrent end: `binding_held`, `binding_ended`,
  `live_bindings`, `owner`, `owner_record`, `owner_voice`, `owner_live` (live at the head named, no eviction
  reaching the row), `voice_seated` (the voice holds its room seat, no removal reaching the row), `node_revoked`
  and `owner_revoked` (either key's own revocation reaching the row). The signer's own record is checked first, as
  for a voice's row: none, refused `room_row_signer_not_room_key`; another room's, `room_key_other_room`; `iss`
  must be `kid`, and the record's `identity_type` must be `node` (a voice's room key never acts as a node: it
  concludes nothing). The binding is held only as a live owner seat read by the seat walk, and the named binding
  must itself seat its owner by the owner's own signature: the owner cosigned it, or accepted it by its own
  acceptance in the row's past. Another row that seats the same owner lends it nothing, so a duplicate the owner
  never signed is none, and one naming two owners is none. Its ends are read as the seat walk reads the owner seat,
  by past with rule 4: a withdrawal of this binding, or of the owner's acceptance of it, ends this binding only
  (another binding of the same owner stands); a stay-level end, the owner's revocation of the owner seat (an unseat
  of it over the node key), ends every binding of that owner not having it in its own past. An end in the binding's
  own past is before it and ends nothing of it (the owner may bind the node again). The owner is read through
  the one owner reading, `Seats::owner` (two live owners is none; a re-binding, an owner offer over the node key
  with the earlier binding in its past, ends the binding before it): the named binding must be the owner's current
  one, so a row under a re-bound binding concludes nothing and a row under the re-binding stands. It concludes (`admitted`) only
  where the binding is held and not ended, it is the one live binding, neither key revoked itself, the owner is a
  room key of this room whose record is not a node's, the owner is live and its voice seated; otherwise it
  concludes nothing.
- a row naming no voice head, or several, is refused, `room_row_voice_head_malformed` (CC 2.7.3). The text names
  no refusal for a key that is not live at the head: such a row concludes nothing, with `refusal` null. The checks
  run in the order above; no case meets two. A public room's row is not checked.

### Room content after a member's seat ends

`content::answers` is checked against `models/causal_kernel/conferral_content.py`:
- its case table (`tests/fixtures/conferral_content.json`; the 54 cases under `count_first`, each with its rows
  listed in every order the fixture gives and in reverse). The one case under `merge: union` states what a
  rejected reading gives and is not run;
- 22,700 histories built row by row (`conferral_content_worlds.json`), 37,643 answers: over two roster heads,
  every history of up to three rows and every 53rd of four; with the member admitted again at the second
  head and a co-member signing, every history of up to three rows; with a head between at which the member
  is not listed, every history of up to two;
- with one roster head or end withheld from the caller's past: undecided, naming the missing row, or judged
  as over the rows held;
- `content::changed` folded over each history in its build order, and in reverse where the door allows: it
  ends at `content::answers`.

The rule itself is checked by `check_conferral_content.py` (a `./check.sh` step): every history of up to four
rows, with what the member alone and one counted row can change. It is a run in Python, not a TLA+ model.

In the fixture an act has `prev` (its predecessors), and `target` with `compose` for an edit or a retraction;
an end has `trusted_through`; a row of kind `tips` adds tips to the end in `extends`. Neither a predecessor nor
a tip is in `names`: nothing waits on content.

## What this crate leaves out, and why

- **Two ends of one standing held together.** The model has one end. `conferral::answers` refuses several.

- **The rejected rules.** The group checkpoint (`checkpoint.py` with `group=True`) and the window's `void` and
  `contest` rules are kept in the models only to show why they are refused. KERNEL.md 5 and 8a, and
  `Recount.ruleI_concluder_decides` and `ruleII_never_final`, state them as rejected. So they are not here.
- **The models' plants.** The `MUT` switches in `seat.py`, `key_end.py` and `roster.py` are deliberate breaks
  for the Python checks; the crate implements the rule only.
- **Copying and audience** (`route.py`, the **missing** answer as routing, the copy rule of KERNEL.md 5). The
  differential tests conclude `route.py`'s message and acknowledgement rows with the crate's `members_at`,
  but routing itself is not stated here. It reads placement data that KERNEL.md 9 lists as not yet table data.
- **A writer's keys** (`keyplane.py`) and **private rooms** (`roomkey.py`). KERNEL.md 7b says the kernel is not
  changed by a room key, and the binding is cryptography. The key plane is a fold the caller can write with `ops`.
- **The fold default** (CC 3.5.1: one signer's own chain, the later signed instant, the lower id on a tie). It is
  a cell of the expression language, which is not carried here.
- **What KERNEL.md marks open**: a roster version naming several heads on the wire, how a second consent
  travels, the cosignature attached against a node's clock, the least set a node must keep, whether a withdrawn
  receipt still blocks (treated as blocking, as the models do), and the eight folds a reaction calls that no
  cell defines.
- **Signature verification, CBOR and COSE decoding, storage and transport.** The caller's.

## Costs a caller should know

Building a `graph::Graph` is linear in the rows and the names: it records each row's held names and its level.
A row's past is computed when first asked, from the pasts already known, and kept. A question of concurrency
between two rows first compares levels, then searches at most 256 rows above the lower one, and only then
computes the past. `examples/closure_bench.rs` runs it at the sizes persist's own benches use
(`benches/scores_read.rs`: 256 to 16,000 rows) and at 64,000, against the eager closure the crate first shipped.
On this machine (release build; ms):

| Shape | Rows | Eager: build | Eager: 10,000 queries | Lazy: build | Lazy: 10,000 queries | Lazy: one head's past | Lazy: every past |
|---|---|---|---|---|---|---|---|
| narrow (each row names up to two of the last eight) | 16,000 | 19.4 | 0.22 | 3.9 | 16.1 | 4.6 | 19.3 |
| narrow | 64,000 | 169.4 | 0.32 | 12.5 | 33.6 | 15.1 | 203.6 |
| wide (up to three of the last 4,096) | 16,000 | 12.3 | 0.12 | 3.8 | 20.0 | 4.1 | 16.5 |
| wide | 64,000 | 205.9 | 0.33 | 16.3 | 1,410.6 | 20.2 | 241.7 |

One run with every column at every size peaked at 553 MB. The same run, with the eager closure and "every past" left out at
64,000 rows, peaked at 52 MB. So the build is linear and memory follows what is asked. Asking every past (a
whole-set `conclude`) is still quadratic in time and memory, as its output is. Eager queries are faster once
built, since every past is held; lazy point queries on a wide graph cost up to 0.14 ms each. The seat and the window build nested
graphs over a row's past to read the members at a head. `head::View` keeps each row's past as a set and is
quadratic too. So a store should still call the kernel over the rows an answer reads.

## Objects: a row or a key, by the form of the reference

`seat::Obj::from_reference` reads the form the signed object gives a reference. A SHA-256 `hash-digest`,
`[-16, digest]` of 32 bytes, names a row. An identity reference, `urn:ietf:params:oauth:ckt:sha-256:` and 43
base64url characters, names a key. Anything else names nothing. The seat fixtures write every object in
those forms, and the tests type each one from its form alone.

## Building

`rust-version = "1.89"` is the minimum supported Rust version, built and tested in CI (`crate.yml`, job
`msrv`). `deny.toml` at the repository root holds CIRISPersist's licence allow-list, and `cargo deny check`
passes under it.
