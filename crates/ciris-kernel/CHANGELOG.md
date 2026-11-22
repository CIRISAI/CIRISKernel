# Changelog — ciris-kernel

## Unreleased

Held views, slice 4 (issue #4, `HELD.md`): the head layer held (`held_view::HeldView`), its checkpoint (ids
only, rows re-attached by id), foreign rows on `Held`, and `proofs/Held.lean`. No existing answer changes.

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

- `seat::exercised_stands(c, law, spec, x, k, scope, obj) -> Exercised`: whether act `x`, which `k` exercises
  under its seat (`k`, `scope`, `obj`), stands, as CC 2.4.1.1 was ruled on 2026-11-21 (a withdrawal retires its
  target as a cut does, CC 2.7.7). It stands iff (a) the seat walk over x's own concluded past seats `k`
  (`Seats::holders`; `left_in_past` is not read, so a re-acceptance re-seats `k` for its acts) and (b) no counting
  ending cut on the seat is concurrent with `x`. The ending cuts are every way the seat ends: `k`'s own withdrawal of
  the acceptance or offer that seats it (a resignation), the conferrer's withdrawal where the walk honours it, and an
  unseat of the seat that is not stale. (b) runs under the rule-4 fixed point over the caller's `spec`, with each
  ending withdrawal made a cut on one slot the kernel adds and no row is on: a withdrawal that a concurrent counting
  removal of `k` voids does not cut, and no other row's status changes. `Exercised` is `ConcludesNothing`,
  `NotSeated`, `Cut`, `Contested` (rule 5; does not stand) or `Stands`; `Exercised::stands()`.
- What changed is a reading, not an answer: before this, an act under a seat could only be judged by the walk over
  its own past (`Seats`, `members_at`), which still answers exactly as it did, and an act concurrent with the
  withdrawal found the seat standing. A caller that wants CC 2.4.1.1 as ruled calls `exercised_stands`.
  `Seats`, `members_at`, `count_members`, `left_in_past`, `seat_rule` and `Cut` are unchanged; the members at a head
  and n stay by past (`RosterHead.leaving_binds_by_past`; `SeatCut.cut_acts_members_hold`).
- Precondition: the answer reads ancestry rows must carry (an act names the standing it is exercised under; a
  withdrawal names its head). Persist's rows as signed today do not, and persist does not call this before v62.0;
  until the wire carries it, persist uses CC 2.6.7's freshness window, which the kernel does not model.
- Open: a withdrawal naming its head under the reader's line (CC 2.7.8), against backdating; one say (rule 6) for
  seats under a cut.
- Checked: `check_seat_cut.py` (17 cases, every kept set of two pools, two model plants), conformance run
  `exercised_stands and the members at a head` (fixture `seat_cut.json`), two crate plants, `proofs/SeatCut.lean`.

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
