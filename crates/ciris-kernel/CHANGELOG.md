# Changelog — ciris-kernel

## Unreleased

**Answers change in two windows; a moderator's lone removal of an AI agent's key and its lift (CC 4.5.13).**
Three public types change, and one trait gains a method.

What a caller must change to compile:
- `window::How` is no longer `Copy` (it is `Clone`), and gains `How::MoreOfVoted(num, den, least, against)`: an
  exhaustive `match` adds an arm, and code that copied a `How` clones it;
- an exhaustive `match` on `seat::Policy` adds `Policy::Lift`.
`window::Base`, `window::Clause` and `window::WindowSpec` are unchanged.

Answers that change:
- **The members' check (`moderation_overturn`) is counted over the members less the act's author.** The
  reference's clause is now `("object", ("more", 1, 2, 2), "others", "lifted")`; it was over `all`. This is the
  Constitution's rc22 text, ruled by Eric on 2026-11-25: "The act is lifted when a strict majority of the members
  seated at the head the act names, the act's author apart, has objected within the 48-hour window. ... The floor
  is two voices. The author's own objection is no voice, and the author is not among the members the majority is
  taken of. Where the author is one of two members no lift is possible." Where the moderator is not on the roster
  nothing changes. Where it is: its objection no longer counts, and the majority is of one member fewer. A room
  of three with the moderator a member lifts on both others (two of two) and not on one other with the moderator;
  a room of four lifts on two of the three others; a room of two cannot lift. This is table data: the crate's
  `Base::Others` already said it, and a caller's own `WindowSpec` for this window moves to `Base::Others`.
- **The moderation fallback (`moderation_fallback`) is a strict majority of the members who voted, floor two.**
  The reference's at-close clause is now `("act", ("voted", 1, 2, 2, "against"), "all", "fallback")`; it was a
  strict majority of all members. `act` is a vote for; the new answer word `against` is a vote against (the same
  row with the other polarity, not an objection); a silent member is not counted over. Ruled by the Constitution
  session on 2026-11-25; `data/governance_policy.tsv`, row `moderation_action`, already said it. Four members
  with two votes for and none against now fall back, where they did not; two for and two against do not; one
  vote for alone does not (the floor). In the crate this is `How::MoreOfVoted`.
- **`window::rule` and `window::outcome`: a duty holder's answer is what that key said.** A value that an
  at-once clause reads as `How::One` over a `Base::Scope`, said by a holder of that scope, is that key's voice,
  and any other answer of the same key is moot. Before, a moderator who was also a member and both answered and
  voted had said two things and so nothing. Tables with no such clause are read as before. A moderator's answer
  that names the fallback's landing changes nothing (a row of the table now says so).
- **`window::rule`: an opener that is also an offer or an unseat** (`win_kind() == Some(Open)` and
  `seat_kind()` `Offer` or `Unseat`) concludes only where `seat::seat_rule` concludes it too. Before, the
  opener's rule alone was read for such a row. A row that is only an opener is read as before.
- **`seat::seat_rule`: a counted row of a policy the table reads as `Policy::Lift`** concludes only as a
  re-seating (below). The reference's table reads `moderation_overturn` so; a counted row of that policy was a
  strict majority of the members before, and no fixture or check had one.

New:
- `SeatRow::removes_agent` (default `false`). An unseat of a roster seat (`SeatLaw::roster_seats`) of one key,
  `Conf::Group`, that the caller marks so concludes on its signer's one voice where that signer holds `moderate`
  over the object at the head the row names, whatever the room's protocol and however many holders. The kernel
  cannot see a key record, so the caller states the mark. Unmarked, or signed by a key that is no moderator
  there, the row is counted as any removal is and fails where it failed.
- That removal is the opener of a `moderation_overturn` window: the caller presents it with
  `win_kind() == Some(WinKind::Open)` and `window()` naming the table.
- `Policy::Lift` and `seat::lift_voices`: the lift's effect is a counted row. An offer of this policy that seats
  the key again, cites the removal (`SeatRow::content`), names the head the removal names and names objections,
  each presented as a cosignature whose `of` is the removal. Its voices are those objections' signers and no
  other key; the removal's author is no voice and is not counted over; the key seated is counted over and is no
  voice. It concludes on more than half of those members, never fewer than two, and only where the key was on
  the roster at that head (it restores and does not admit). `lift_voices` returns the author and the voices;
  `GroupCount`'s contract says what `members` and `voices` are under this policy. `Seats::tips_fold` reads the
  same count over the members the fold seats.
- No reading of the roster reads a window. Until that row is written the window reads `lifted` and the key is
  out. That gap is accepted.

Checked: `models/causal_kernel/check_agent_removal.py` (31 cases in 9,878 arrival orders, six planted breaks in
the seat rule, five in the window tables), whose rows are in the seat fixture and run the crate's rules; the
adversary table is 76 rows and 66 checks over five windows (recount breaks none, the voiding rule twelve, the
contesting rule two); nine planted breaks in the crate, each confirmed by hand. Not decided here, and stated in that file: the removed
key's own objection is no voice of the count with no landing (the ended-seat rule) nor of the re-seating, but a
landing that has it in its past counts it; and a moderator whose duty ended after the head the removal names
still removes at that head.

## [0.3.0]

The first tag of the 0.3 line (`kernel-v0.3.0`). It follows `kernel-v0.2.2`, which persist pins, and carries
everything below. Several answers change and three public types gain members.

### Adopting 0.3.0 from 0.2.2

Answers that change:
- `seat::Seats::stands`, `holders`, `holders_at`, `stands_at`: at several tips they read the fold of the tips'
  changes (`tips_fold`), not the members common to them. `tips_common` is unchanged.
- `window::outcome`: a met at-once count is the outcome with no landing row.
- `window::rule`: a receipt with a row of the target in its past, beyond the opener's own, is no receipt.
- `head::View::counts_at` (and `carried`, `Answers`, `HeldView`): a counting cut at an older head voids a
  concurrent act at a later head.
- `content::answers`: a content row naming an end of the member's seat as its head is `no_seat`, where it was
  undecided.

What a caller must change to compile:
- a `WindowSpec` literal adds `opener: None`;
- an exhaustive `match` on `window::How` adds `MoreAtLeast`, and on `window::Base` adds `Opener`.

New, and optional:
- `SeatRow::regime` (default `None`): the protocol and policy in force at a counted act;
- `seat::Seats::tips_fold`; `seat_rule`: a holder may end its own seat by a row under it, where
  `SeatLaw::ends` lists the scope for itself (an owner's revocation of a key);
- two windows in the reference's tables, `moderation_overturn` and `self_roster_add`.

Read `ADOPTING.md`, "Presenting rows: what the functions assume", before writing an adapter. `PERF.md` gives
the fold's cost: join tips before they are many.

### The changes

`seat::seat_rule`: the holder of a seat may end its own seat by a row of its own under that seat, where the
caller's `SeatLaw::ends` lists the seat's scope for itself. That is how an owner's revocation of a key is
presented (CC 2.4.1.1: it "ends the owner-binding's standing", and "only the key's own revocation ends its
liveness"): an Unseat of scope `owner`, `to` the owner, under the owner-binding, with `ends` =
`{owner: [owner]}`. It concludes only for the one live owner over the row's own past, as before. Additive: a
table that lists another scope (the reading until now, `{owner: [registered]}`, which ended the key itself) is
read as before, with `to` the object's key. The reference `seat.py` and `check_rosters.py`'s key instance move
to the text's reading: the owner's revocation ends the binding, the key stays registered, its rows count, and
it can take a new first binding. Eight scenarios in the seat fixture run the crate's rule; two planted breaks.
**A caller whose law table has `owner -> registered` ends keys by their owner's revocation, which the text does
not allow.**

**Answers change: at several tips `seat::Seats` reads the fold, not the common members.** `stands`, `holders`,
`holders_at` and `stands_at` now read `Seats::tips_fold` (CC 2.7.8 as the Constitution adopted it on a run,
2026-11-23; `models/roster_fork/fold.py`):
- a key every tip seats is in;
- a key some tip's line removed is out, unless a later addition of it has that removal in its past (so a key one
  tip admits and another removes is out);
- a key a tip adds is in where the counted offer that adds it meets its count on the voices of keys the fold
  seats, over the members at its heads that the fold seats: a least fixed point from the common keys;
- tips that differ in protocol or policy do not fold and give the common keys. The caller states that value per
  counted act through the new `SeatRow::regime` (default `None`: every tip equal).
`tips_common` is unchanged and still public. With one tip nothing changes.
- `members_at` and `members_in`: a head one key wrote (an `open:self_admit` admission signed by the key it
  seats) is read through to the heads it names, and only the newest counted heads are intersected, so such a
  head narrows no count. Unchanged where no head named is one.
- What moves for a caller: a member one tip admits is listed at once where its admission holds on the common
  members' voices; before, it waited for a version naming both tips. A member any tip removes is out, as before.
- The cost, stated in KERNEL.md section 7: where the one key common to two tips is an adversary's, what it
  signed on either tip folds in at once.
- Reference `seat.py` (`Seats.tips_fold`); `attacks.py` tests 3, 4, 7 and 34 and three measured facts restated;
  `check_rosters.py`'s tips property restated. `tests/fold.rs` (7 cases: self-admission, a head one key wrote,
  tips that differ in policy). `proofs/TipsFold.lean` (7 theorems: the fold's bounds). Five planted breaks.
**Answers change: `window::outcome` reads a met count with no landing; a proposer's withdrawal; a fifth window.**
For the Constitution's rewrite of CC 3.3.6.4 (the self roster's lone path as rows), each checked in `window.py`:
- **A count that is met needs no clock and no concluder.** Where no landing has concluded, `outcome` is the
  outcome an at-once clause gives over the answers held (`Outcome::Landed`), and `Open` only short of that.
  Before, it was `Open` until a landing concluded, a majority's approval included.
- **The proposer's withdrawal.** An answer `withdraw` by the opener's signer is read by a clause over the new
  `Base::Opener`. It never replaces what the proposer said by opening, so a strict majority that has approved
  still lands (a count once met is final), and the tables read the approval first. An approval that has the
  withdrawal in its past approves nothing.
- **`self_roster_add`**: the eviction's table without the target's silence.
- `window.py`'s elapsed test no longer assumes both instants are stated; the crate already did not.
- The adversary table is 57 rows and 47 checks over five windows: recount breaks none, the voiding rule eleven,
  the contesting rule two. Three planted breaks in the crate, and `landing_only` in the model.
- A caller matching `Base` exhaustively adds an arm for `Base::Opener`.

**An answer changes: `head::View::counts_at` reads a cut at an older head.** A counting cut at an earlier head
now voids an act at a later head that is concurrent with the cut (KERNEL.md section 6 rule 4, "rows on that slot
concurrent with it do not count from the head the cut names"; `CONFERRAL_END.md` E3). Before, only a cut at the
act's own head was read. `carried`, `Answers` and `HeldView` read `counts_at` and move with it.
- One say still applies: a cutter holding a clean receipt of the act concurrent with the cut has no say on it.
- The reader's line still applies: a reader that acknowledged the later head holds the older cut void.
- Unchanged: a cut at the act's own head, a cut at a later head (it only takes the act out of force), a cut at
  a concurrent head, and a cut the act has in its past.
- Purge: only an act's answer at its own head is stored as final. The digests of its clean receipts are kept,
  and a cut at an older head is read again.
- `purge.py` had the same gap and was fixed first: eleven histories (two new), and the plants `own_head_only`
  and `final_blocks_earlier`. `Settled.lean` gains `countsFrom` with six theorems; the existing ones are untouched.
- Three planted breaks in `head.rs`.
- Persist does not call `counts_at`, `carried`, `Answers` or `HeldView` (its own reading, 2026-11-23).

`seat::exercised_stands`, proposed with this change in PR #21, is not added: `conferral::answers` gives the
whole rule (E1 to E8) and is the one implementation.
**A fourth window, and two additions to the window table's types.** The members' check of CC 4.5.13
(`moderation_overturn`): a duty holder's act opens its own window; a strict majority of the roster at the head
the act names, never fewer than two voices, lifts it by objecting; short of that at the close it stands; the
duty holder has no say in the lift. It lands by a row and is read under recount like the other three, so two
nodes holding the same rows agree. Read by each node's own clock, as the text had it, two nodes holding the
same rows can differ for good.
- `WindowSpec` gains the field `opener: Option<String>`: the scope the opener's signer holds where it is not
  the counted one. **A caller that builds a `WindowSpec` literal adds `opener: None`.**
- `How` gains `MoreAtLeast(num, den, least)`: more than `num / den`, and never fewer than `least` voices.
- `window.py` has the window and eleven adversary rows; the table is now 38 rows and 29 checks. Recount breaks
  none, the voiding rule nine, the contesting rule two. Two planted breaks in the crate.

`window::rule`: a receipt that has a row of the target in its past, beyond what the opener has in its own, is
no receipt, and a landing naming it concludes nothing. "Inside the window" is what the landing has in its past
and the receipt has not, so such a receipt would put the target's row before the window and hide it from the
target's silence (a concluder could delay its receipt and name the target's rows in it). A receipt may name
other rows: in a private room every row names its signer's voice. The Constitution's wire shape for the
receipt (`window:held`, naming the proposal alone) is stricter. `window.py` and `attacks.py` test 12 carry the
case; one planted break. No row built as the model builds a receipt changes its answer.
`content::answers`: a counted removal is the member's end and also a version of the roster that later rows
name. A content row of the member that names an end of its seat as its head now names a head at which the
member is out: not counted, rule `no_seat`. Before, the row came back `Undecided` on that id, since no
`Kind::Head` row carried it, and a caller had to present the removal twice under two ids. A version built on
the removal that admits the member again is a `Kind::Head` marked `Admits`, as before. One new case
(`row_naming_the_removal_as_its_head`; the fixture has 56 cases, 131 answers) and one planted break. The
exhaustive histories of `check_conferral_content.py` do not build such a row; the case and the crate's test
of it are what cover the rule.

**An answer changes: on a plain count, the member removed is a voice of its own removal.** `seat::group_count`,
and so `seat_rule`'s group count, no longer drops the voice of a key the row removes under `quorum`,
`majority`, a declared threshold, `founder_only` or `weighted` (the Constitution's ruling of 2026-11-23 on
CC 2.7.5, rc22 `462260c`: "A member the row removes is a voice of its own removal, except where the group's
policy states otherwise"). A removal that failed by that
one voice now stands. Under `weighted` the removed member's weight counts.
- Unchanged: `unanimous`, `open:self_admit` and the duty withdrawal, whose own sentences exclude the member
  named; and every seating, where a key the row seats is still no voice.
- A caller counting an accord bundle no longer needs to pass an empty `to` for the removed holder.
- No proof changes: `proofs/SeatCount.lean` states the count over the voices given, and which keys are voices
  is the crate's reading, tested by cases (`tests/policies.rs`).

New function `derived::claims`: a signer's claim for a key, by what its rows name and by no instant (the
`holon:claim` family, CC 3.1.11 "How claims are read", rc22 `3f694e4`: "This family is read this way, and
not by the default of CC 3.5.1"). Rows are grouped by signer and a key the
caller gives. The one row of a group that no other row of the group has in its past is the claim
(`Claim::Stands`), or ends it (`Claim::Ended`, a `recants` or `withdraws`). Two such rows are `Claim::Split`:
the signer says two things and has no claim until one of its rows has both in its past. A row of another
signer never voids or replaces a claim. `derived::fold_default`, which breaks such a tie by the signer's own
instants (CC 3.5.1), is unchanged. Checked by cases only: 13 cases and every order of seven rows; four
planted breaks.

Held views, slice 4 (issue #4, `HELD.md`): the head layer held (`held_view::HeldView`), its checkpoint (ids
only, rows re-attached by id), foreign rows on `Held`, and `proofs/Held.lean`. No existing answer changes.

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

### Held views

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
