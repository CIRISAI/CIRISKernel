# Changelog — ciris-kernel

## [0.2.2]

**One answer changes: on a plain count, the member removed is a voice of its own removal.** `seat::group_count`,
and so `seat_rule`'s group count, no longer drops the voice of a key the row removes under `quorum`,
`majority`, a declared threshold, `founder_only` or `weighted` (CC 2.7.5 at rc22 `462260c`: "A member the row
removes is a voice of its own removal, except where the group's policy states otherwise"). A removal that
failed by that one voice now stands. Under `weighted` the removed member's weight counts.
- Unchanged: `unanimous`, `open:self_admit` and the duty withdrawal, whose own sentences exclude the member
  named; and every seating, where a key the row seats is still no voice.
- A caller counting an accord bundle no longer needs to pass an empty `to` for the removed holder.
- Persist (its own reading, 2026-11-23): one caller, the room ballot; no stored answer; room removals under a
  plain count now count the removed member's voice.
- No proof changes. Which keys are voices is the crate's reading, tested by cases (`tests/policies.rs`, 24).

New function `derived::claims`: a signer's claim for a key, by what its rows name and by no instant (the
`holon:claim` family, CC 3.1.11 "How claims are read", rc22 `3f694e4`). Rows are grouped by signer and a key
the caller gives. The one row of a group that no other row of the group has in its past is the claim
(`Claim::Stands`), or ends it (`Claim::Ended`, a `recants` or `withdraws`). Two such rows are `Claim::Split`:
no claim until one row of the signer has both in its past. A row of another signer never voids or replaces a
claim. `derived::fold_default` (CC 3.5.1) is unchanged. Checked by cases only: 13 cases and every order of
seven rows; four planted breaks.

Fixtures:
- `conferral_end.json` gains the case `receipt_never_withdrawn` (35 cases, 51 act answers): a row withdrawing
  a receipt is refused at the door by the text (`federation_withdraws_not_admitted`) and read by nothing here
  (`Kind::Other`). `conferral` is unchanged.
- `conferral_two.json` is new: one row that needs two standings, an owner binding and a root grant
  (CC 3.1.2.1), 11 cases from `models/causal_kernel/check_conferral_two.py`, now a step of `./check.sh`. No
  Rust test reads it; a caller runs `conferral::answers` once per record and joins the answers bit by bit.

`conferral` and `content` are unchanged from 0.2.1.

## [0.2.1]

Additive: no existing function, type or answer changes. A caller on 0.2.0 moves the tag and nothing else.

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
- `tests/fixtures/conferral_end.json` (34 cases, 49 act answers) is the module's own test and an adopter's
  conformance fixture. `conferral_end.tsv` is the same table in plain text.

Which bit a caller reads: a tally at a head and an as-of answer read `counted`; anything done now on the act's
strength reads `in_force`; an act that authorises a further row passes both down.

New module `content`: room content after a member's seat ends, where the end names the rows it holds good
(CC 2.4.1.1; `models/tla/CONFERRAL_END.md` section I on the main branch).
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
