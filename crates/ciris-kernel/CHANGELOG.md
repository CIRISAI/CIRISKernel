# Changelog — ciris-kernel

## Unreleased

Held views, slice 4 (issue #4, `HELD.md`): the head layer held (`held_view::HeldView`), its checkpoint (ids
only, rows re-attached by id), foreign rows on `Held`, and `proofs/Held.lean`; and the conferral end
(`models/tla/CONFERRAL_END.md`, approved for persist v62.0). One existing answer changes:
`head::View::counts_at` (below, "Behaviour change: a cut at an older head").

### Behaviour change: a cut at an older head (2026-11-22)

KERNEL.md section 6 rule 4: once a cut counts, rows on its slot concurrent with it do not count **from the head
the cut names**. Through 0.3.0, `head::View::counts_at` (and so `Answers::counts_at`, `carried`, which reads it, and
`HeldView`) read a cut only when it named the act's own head (`c.head == act.head`). It now also reads a cut naming
a head **older** than the act's (one in the past of the act's head), concurrent with the act: counted over the
members at the cut's head against that head's count, with one say (rule 6) as at the act's own head (a signer
holding a clean receipt of the act concurrent with the cut has no say). This is CONFERRAL_END.md E3. `purge.py`
had the same gap and was fixed first (`check_purge.py`, plant `own_head_only`).

- What changed, an example: roster versions v0 and v1 (v1 names v0), members A, B, C and count 2 at both; act E
  by A at v1; a cut of E by B and C naming v0, concurrent with E. Through 0.3.0 `counts_at(E)` was `true`; now it
  is `false` (and `carried(E)` with it). With a clean receipt of E by B concurrent with the cut, B has no say, and
  E counts. For a reader that acknowledged v1, the cut is void (the line, CC 2.7.8), and E counts, as before.
  (`head::tests::a_cut_reaches_forward_from_the_head_it_names`; `purge.py` histories "a cut at an earlier head
  reaches a later head", "a settled act and cuts at an earlier head".)
- What did not change: a cut at the act's own head; a cut at a later head (it acts forward: the act still counts
  at its own head and is out of force, `carried`); a cut at a head concurrent with the act's, or one the act has
  in its past; and every store with no cut at an older head than its act's. `Settled.later_head_changes_nothing`
  and the one-say theorems hold as they were, and `Settled.later_head_changes_nothing_from` states the forward
  property for the new reading (`countsFrom`).
- Settled acts: n − t + 1 receipts at the act's head make its count final against cuts at that head, not against
  a cut at an older head, whose members may differ. So `purge` stores in `Entry::final_counts` the answer against
  same-head cuts only (`counts_own`), records `Entry::acks` (the clean receipt digests) for every final act, not
  only a settled one, and keeps every cut at another head than its act's whole; `counts_at` reads cuts at older
  heads again over a stub. A checkpoint from an earlier purge resumes as before (its `final_counts` was the same
  answer for every store without such a cut).

### Adopting (from 0.3.0)

The modules `conferral` and `content`, released as 0.2.1 on the 0.2.x line (tag `kernel-v0.2.1`), are here too,
unchanged:

New module `conferral`: the causal end of a conferral (CC 2.4.1.1, CC 4.5.5; rules E1 to E8 of
`models/tla/CONFERRAL_END.md`).
- `conferral::answers(rows, &standing, &past)` gives, for every act among the rows, `Judged { counted,
  in_force, rule }`: whether it counts at the head it names, whether it is in force now, and the rule that
  decides. It covers any-standing, receipts, one say, `lifts`, a deputy's act, key removals and the reader's
  line on the end.
- The caller supplies rows through `ConferralRow`, who each key is to the standing through `Standing::role`,
  and the causal past as a function `in_past(a, b) -> Result<bool, Id>`. `Err(id)` means "cannot tell until
  this row is held", and the acts that need it come back `Answer::Undecided(id)`, never as a wrong bit. No
  lineage is materialised.
- One end per call. Two ends of one standing are outside the model, and `answers` refuses them
  (`Refused::SeveralEnds`).
- `tests/fixtures/conferral_end.json` (35 cases, 51 act answers) is the module's own test and an adopter's
  conformance fixture. `conferral_end.tsv` is the same table in plain text.
- Since 0.2.1 the fixture has one more case, `receipt_never_withdrawn`: a row withdrawing a receipt is refused
  at the door by the Constitution's text and read by nothing here (`Kind::Other`). The module is unchanged.

Which bit a caller reads: a tally at a head and an as-of answer read `counted`; anything done now on the act's
strength reads `in_force`; an act that authorises a further row passes both down.

New module `content`: room content after a member's seat ends, where the end names the rows it holds good
(CC 2.4.1.1; `models/tla/CONFERRAL_END.md` section I).
- `content::answers(rows, &seat, &past)` gives, for every content row of the member, `Judged { counted,
  in_force, rule }`, where `in_force` means "in the room's content now". It reads the tips of counted rows
  first (`count_first`), follows predecessors as a set among the member's own rows (by member, not by key),
  waits on nothing (an unheld tip or predecessor keeps nothing until it arrives), and applies the member's
  own retraction whenever it is signed.
- Seat by seat: a head says what it is to the member (`SeatAt::Sits`, `Admits`, `Out`). A member seated again
  has a new seat; each seat's content is judged by its own ends and tips, a re-admission restores nothing,
  and a row at a head where the member does not sit is `no_seat`. A caller that gives no `seat` gets one seat.
- `content::changed(rows, &arrived, &seat, &past)` gives the rows whose answer the arrival of one row changes,
  each with its new answer. Folding every arrival with it ends at `answers`. It is computed by reading the
  rows twice: linear in the member's rows in the room for each arrival. A form that visits only what can
  change is not written yet.
- The past is the same three-way function as `conferral`'s.
- `tests/fixtures/conferral_content.json` (55 cases, 128 answers) is the module's test and an adopter's
  fixture; `conferral_content_worlds.json` holds 22,700 histories with the reference's answers, a second seat and a co-member's rows among them.
- The rule is checked by an exhaustive run in Python (`check_conferral_content.py`), not by a TLA+ model. Not
  covered: receipts together with tips, the reader's line on an end, key removals.

### Adopting (from 0.3.0)

Checked against `git diff` of `src/` from 0.3.0. No public enum gained or lost a variant (`held::Refused` is
unchanged), so no exhaustive `match` changes. One public struct changed its fields:

| Type | Change | An adopter's code must become |
|---|---|---|
| `held::Admitted` | new public field `foreign: Vec<I>` | a literal adds `foreign: Vec::new()`, or is built with the new `Admitted::none(waiting, visited)`; a destructure adds `foreign` or `..` |

Behaviour, not signature:
- `head::View::new`, `void`, `answers` and `closed_for_me` no longer panic when the reader acknowledges a head
  the store does not hold (a reader's acknowledgement not naming its head). Such a head now has no past, so it
  makes nothing behind it or closed. Every store that did not panic answers as before.
- `head::View` is `Clone`. Its private indexes changed form (a sorted buffer, or a map in a held view); its
  answers and `View::new`'s cost did not (same allocations per call in `examples/persist_paths.rs head::`).

### Breaking (0.x)

- `held::Admitted` gains `foreign: Vec<I>`, so a struct literal of it no longer compiles.
- `head::View::counts_at` answers differently for an act with a counted, concurrent cut at an older head (above).

### Added (slice 4)

- `held_view::HeldView<I, K, T>`, `Clone + PartialEq`: `new(store, own, reading, say)` (equal to
  `View::new(store, &[], ..)`), `empty`, `admit(Entry) -> Result<Admitted<I>, Refused>` (transactional: a
  refusal changes nothing), `admit_all`, `view() -> &View` (every `View` answer, unchanged), `len`, `is_empty`,
  `holds`, `waits`, `waiting`, `past_len`. `Admitted::dirty` is every held entry whose answers may have changed,
  ascending, each once; `Admitted::visited` counts the work.
- `held_view::conflict_key(&Entry) -> Option<&I>`: an entry's conflict key (its `of`); conflicts are found through
  the view's index by key, not by a scan of pairs.
- The checkpoint: `CHECKPOINT_VERSION = 1`; `HeldView::checkpoint() -> Vec<u8>` (canonical; ids, stub fields,
  conclusions, acknowledged heads, waiting ids; no row content); `HeldView::resume(bytes, rows: impl Fn(&I) ->
  Option<Entry>) -> Result<HeldView, CheckpointError<I>>`. `CheckpointError { Version(u16), NotCanonical,
  Truncated, Missing(I), Differs(I) }`: `Differs` is a supplied row that concludes otherwise than the checkpoint
  states. `Encode` (`encode`, `decode`), with `DecodeError { Truncated, Invalid }`, implemented for `[u8; N]`
  (fixed width), `u8`, `u16`, `u32`, `u64`, `i64` (big-endian) and `String` (`u32` length prefix).
- `held_view::differential(store, own, reading, say, order, nows) -> Result<(), Mismatch<I>>`: after every
  admission, the held view's answers equal `View::new` over the prefix, a refusal changes nothing, and every
  entry whose answers changed is dirty.
- Foreign rows: `Held::admit_foreign(&R)`, `Held::is_foreign(id)`; `Admitted::foreign`, the concluded foreign
  rows in the read sets of the dirty rows, ascending, each once. A foreign row is held and concluded as a
  member is, and is never in `dirty`. `held::differential_foreign(spec, order, pick)`.
- `proofs/Held.lean`: `admit_eq`, `admits_eq`, `admit_dirty_new`, `admit_derived`, `resume_eq`,
  `resume_concl`, `resume_admits_eq`.

### Added (seat cut, unreleased)

- `seat::exercised_stands(c, law, spec, x, k, scope, obj) -> Exercised`: what act `x`, which `k` exercises
  under its seat (`k`, `scope`, `obj`), is, as CC 2.4.1.1 was ruled on 2026-11-21 (a withdrawal retires its
  target as a cut does, CC 2.7.7), read forward as CONFERRAL_END.md E2 to E4 state it (2026-11-22). Two answers,
  `Exercised::counted()` (at its own head) and `Exercised::in_force()` (from the end's head on). It is in force
  (`Stands`) iff (a) the seat walk over x's own concluded past seats `k`
  (`Seats::holders`; `left_in_past` is not read, so a re-acceptance re-seats `k` for its acts) and (b) no counting
  ending cut on the seat is concurrent with `x`. The ending cuts are every way the seat ends: `k`'s own withdrawal of
  the acceptance or offer that seats it (a resignation), the conferrer's withdrawal where the walk honours it, and an
  unseat of the seat that is not stale. (b) runs under the rule-4 fixed point over the caller's `spec`, with each
  ending withdrawal made a cut on one slot the kernel adds and no row is on: a withdrawal that a concurrent counting
  removal of `k` voids does not cut, and no other row's status changes. When (b) fails, the heads the rows name
  (`SeatRow::head`; persist: `refs.head`) decide: the act's heads with their past strictly containing the end's
  (a later head) give `NotCounted` (E3); otherwise (the end's head, an older or a concurrent one, or none)
  `OutOfForce`, counted at its own head (E2). An act naming the end is `NotSeated` by (a) (E4). `Exercised` is
  `ConcludesNothing`, `NotSeated`, `Stands`, `OutOfForce`, `NotCounted` or `Contested { counted }` (rule 5: not
  in force; not counted where the contested end is at a head the act's is later than).
- Changed since the seat-cut branch (unmerged, so no release had it): `Exercised::Cut` is split into
  `OutOfForce` and `NotCounted`; `Contested` gains `counted`; `Exercised::stands()` is replaced by `counted()` and
  `in_force()` (`in_force()` is what `stands()` answered).
- What changed is a reading, not an answer: before this, an act under a seat could only be judged by the walk over
  its own past (`Seats`, `members_at`), which still answers exactly as it did, and an act concurrent with the
  withdrawal found the seat standing. A caller that wants CC 2.4.1.1 as ruled calls `exercised_stands`.
  `Seats`, `members_at`, `count_members`, `left_in_past`, `seat_rule` and `Cut` are unchanged; the members at a head
  and n stay by past (`RosterHead.leaving_binds_by_past`; `SeatCut.cut_acts_members_hold`).
- Precondition: the answer reads ancestry rows must carry (an act names the standing it is exercised under; a
  withdrawal names its head). Persist's rows as signed today do not, and persist does not call this before v62.0;
  until the wire carries it, persist uses CC 2.6.7's freshness window, which the kernel does not model.
- Open, follow-up: a withdrawal naming its head under the reader's line (CC 2.7.8), against backdating, and E1
  (an end with a newer head in its own past concludes nothing); one say (rule 6, E3's exception) for seats under a
  cut; receipts that keep an act in force (E8, CONFERRAL_END.md section G: the ender's side, `lifts`, a named
  receipter), which need a receipt row the seat rows do not carry. A conformance run over `conferral_end.py`'s
  fixtures, once they are on `conferral-wire-model`.
- Checked: `check_seat_cut.py` (25 cases, every kept set of three pools, one with named heads, three model
  plants), conformance run `exercised_stands and the members at a head` (fixture `seat_cut.json`, both answers),
  four crate plants, `proofs/SeatCut.lean` (`forward_counts_out_of_force`, `later_head_not_counted`,
  `named_cut_not_counted`, `in_force_counted`).

## [0.3.0]

Held views, slices 1 to 3 (issue #4, `HELD.md`): the concluded layer held across admissions, its memory bounded,
and what persist's verdict choke point needs: answers read at a held row, read sets, and derived wake-ups. No
answer changes. The `now` forms remain; they are node-local readings (CC 2.7.9).

### Adopting 0.3.0 (from 0.2.0)

Checked against `git diff kernel-v0.2.0 -- crates/ciris-kernel/src`, not from memory. No public enum gained or
lost a variant, so no exhaustive `match` changes. Every public struct whose fields changed, and what a struct
literal or field access must change to:

| Type | Change | An adopter's code must become |
|---|---|---|
| `layers::Past` | fields `g`, `i`, `p` private; a private `log` added | `Past { g, i, p }` → `Past::new(g, i, p)`; `p.g` → `p.graph()`; `p.i` → `p.index()`; `p.p` → `p.ancestors()` (or `p.rows()` / `p.get(id)`, which a recording past logs) |
| `head::Entry` | new public field `at: Option<T>` | build with `Entry::new(..)` (sets `at: None`) and `.with_at(t)`; a struct literal must add `at: None` or `at: Some(t)`. Set it wherever `View::window_at` / `answers_at` read at that row |
| `held::Admitted` | new public field `wake: Vec<AnswerId>` (the type is new since 0.2.0) | a literal adds `wake: Vec::new()`; a destructure adds `wake` or `..` |
| `graph::Bits` | private field replaced (dense or compact form); `PartialEq` and `Hash` read the set, not the storage | no literal is possible from outside (the field was and is private). Code that compared two `Bits` made for different `n` now gets `true` when they hold the same indices |

Traits:
- `held::HeldSpec` gains `keys` and `can_carry`, both with defaults. Existing impls compile unchanged; an impl
  that declares a method of the same name must match the new signature.
- `Dated` is new. Implement it for a row type to use any `_at` answer.

Additions with no adopter change: `Graph::push`, `reserve`, `instant_of`, `past_bytes`, `past_counts`; `Clone`
for `Graph`, `Concluded` and `Held`; the `held` module (slices 1 to 3); the `_at` answers; `covers_at`.

### Breaking (0.x minor bump)

- `layers::Past`'s fields `g`, `i`, `p` are private. Build one with `Past::new(g, i, p)`; read through `row()`,
  `rows()`, `get(id)`, `past(a, b)`, `index()`, `graph()`, `ancestors()` and `reads()`. A rule that read `p.g`
  reads `p.graph()`, and `p.p` reads `p.ancestors()`.
- `held::Admitted` gains `wake: Vec<AnswerId>`, so a struct literal of it no longer compiles.
- `head::Entry` gains `at: Option<T>`, the instant its signer states. `Entry::new` sets `None`; `with_at(t)` sets
  it. A struct literal of it no longer compiles.
- `HeldSpec` gains `keys(&R) -> Vec<R::Key>` and `can_carry(&R::Key) -> bool`, both with defaults, so an
  existing impl compiles unchanged.

### Added (slice 3)

- `Dated: Row { type Instant; fn asserted_at(); fn valid_until() }` and `covers_at(from, until, t)`, half-open:
  a row's signed instants. `Graph::instant_of(id)`.
- Answers read at a held row, taking their instant from row `at`, never a clock. Each returns `None` when `at` is
  not held or states no instant:
  `Seats::holders_at(scope, obj, root, at)`, `Seats::stands_at(k, scope, obj, root, at)` (a seat counts only
  while its seating offer covers the instant); `key_end::live_at`, `ended_at`, `retained_at`;
  `head::View::window_at`, `answers_at`.
- `Past::recording(g, i, p, &RefCell<Recorded>)`: logs every row a rule reads through its methods. `Recorded {
  read, escaped }`.
- `held::Reads<I, K>`: ids and keys, sorted and each once. `Held::reads_of(id)`: the sound read set (the row and
  its concluded past). `Held::recorded_reads(id) -> Logged { reads, complete }`: what the rule actually read.
- `Held::register(reads) -> AnswerId`, `update`, `unregister`, `registered`, `wakes_for(&R)`; `Admitted::wake`:
  the registered answers whose reads a newly kept row touches (its id, an id it names, a key it carries).
- `Held::named_by(id)`: the by-name index. `Held::unwritable()`: registered keys no row can carry (a read with no
  possible writer).

### Added (slices 1 and 2)

- `held`: the kept and concluded layers held across admissions (issue #4, `HELD.md`). `Held::admit` keeps one row
  and whatever it releases, and concludes only those. `Admitted { kept, waiting, dirty, visited }`. A refusal
  (`Refused::Duplicate`, `NotWellFormed`) changes nothing. `Held` is `Clone`. `held::differential` checks a
  held view against `conclude(kept(..))` after every admission.
- `Graph::push`, `Graph::reserve`; `Clone` for `Graph` and `Concluded`.
- Benches `held::*` in `examples/persist_paths.rs`.
- `Held::set_past_window` / `past_window` and `held::PAST_WINDOW` (64): a held view keeps the pasts of its most
  recently used rows only (kept, or named by a row kept since), so its memory is about `w × n / 64` words, not `n² / 128` (256 MB → 512 KB at 64,000 rows). No
  answer depends on the window.
- `Held::past_counts` / `Graph::past_counts` → `graph::PastCounts { computed, recomputed, walked }`: the window's
  price, measured on the caller's rows.
- `Bits::compact`, `Bits::heap_bytes`, `Graph::past_bytes`. `Bits` has a compact form (runs of whole words and
  single words), used only for a held view's pasts.

### Changed (no answer changes)

- `Bits` equality and hashing read the set, not its storage: two sets with the same indices are equal whatever
  `n` they were made for. Before, `Bits::new(3) != Bits::new(200)`.

## [0.2.0]

Performance for CIRISPersist's adoption (PR #3). See `PERF.md` for the measurements and method.

### Breaking (0.x minor bump)

- `seat::group_count` returns `Option<bool>`; `None` only for a `Ranked` policy, so a misrouted ranked ballot is visible.
- `Seats` and `head::View` fields are private behind getters of the same names (`recs()`, `c()`, `cut()`, `stale()`, `rec()`, `v()`).
- `trust::Index` is renamed `trust::EdgeIndex`.

### Added

- `seat::group_count` / `GroupCount`: the `Conf::Group` count over a resolved roster, with a `# Contract`.
- `seat::count_members(p, law, spec)`: exactly the member set `seat_rule` counts over.
- `seat::members_in_scopes`; `trust::EdgeIndex`; `Graph::waiting(i)`.
- A members-at-head cache scoped to one `conclude`.

### Changed answers

- One deliberate change: a weighted total of 2^64 or more is summed in `u128`. It no longer wraps in release builds, as `SeatCount.weighted_mono` states.
- A row on a name cycle, or naming one, now waits (as `kept` already said) instead of making `Graph::new` / `View::new` run without end. No answer changes for rows closed under `kept`.

### Checks

- `check.sh` now fails unless every conformance run listed in `tools/kernel_conformance_runs.txt` reports exactly once.
