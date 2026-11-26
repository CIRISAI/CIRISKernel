# Changelog — ciris-kernel

## Unreleased

**A member who left and was re-admitted counts** (CIRISConstitution#218, pin list: a re-admitted member counts).

- `seat::left_in_past` read a key's own leaving and ignored a later admission, unlike `stay_ended_in_past`. So
  a member who resigned and was re-admitted stood as a member, but was in no count's base and no voice of any
  count, for ever. Now a key is out of a count by its leaving only while no seating of it in that scope after the
  leaving is in the counted row's past: no offer seating the key that has the leaving in its own past. The test
  is one function, `seated_after`, read by both `left_in_past` and `stay_ended_in_past` (the scope's own seat for
  the one, the roster's seat for the other). No public name changes.
- **Answers change** (0.4.0 answers), each where a member resigned and the room re-admitted it before the
  counted row:
  - the member's voice counts: of six, an admission signed by A, B, C (re-admitted) and D, 4 of 6, concludes;
    before it read 3 of 5 and did not;
  - the member is in the base: of four, an admission or removal signed by A and B alone, 2 of 4, does not
    conclude; before it read 2 of 3 and did;
  - a removal: of six, F removed by A, B, C and D concludes; before it did not.
  The same holds for every count that reads `left_in_past`: `count_members`, `group_count` callers that subtract
  it, and the duty counts.
- Not changed: a re-admission beside the counted row (not in its past) is not read by it; a leaving after the
  re-admission puts the key out again. A counted removal followed by re-admission was never affected, since the
  removal acts through `members_at` at the head. A window's clause reads no leaving and was never affected.
  Private rooms are not special-cased: room-key finality refuses the re-admission there.
- The reference: `models/causal_kernel/check_readmit.py`, 10 hand-written cases in every arrival order, all in
  the `seat` fixture, and one planted break. Two plants in the crate.

**The recall, and ranked choice** (CC 4.5.13; CIRISConstitution#241, split out of the election's PR, which does not
merge for this tag). Two public variants and a function are added. **BREAKING for an exhaustive match on
`seat::Policy`.**

- **The recall** is strictly more than two thirds, with a floor of two voices, over the roster less the holder
  it recalls ("A recall is one row cosigned by more than two thirds of the standing roster ... The floor is two
  voices"; #241 O5, C1).
  - `Policy::StrictFloor(num, den, least)` is a plain threshold: strictly more than `num / den` of the base, and
    never fewer than `least` voices. The member a removal names is a voice of it, as on any plain count.
  - `Policy::Recall(num, den, least)` uses the same comparison and floor (`seat::met` delegates to StrictFloor).
    It judges one holder: `count_of` counts it over the members less the key it removes, and that key is no
    voice. The exclusion keys on the variant.
  - The reference's table and the fixture law give `moderator_recall` as `Recall(2, 3, 2)`; the data's cell
    reads `2/3`, read before as at least. An adopter's table must do the same.
  - **Answers change** (holder A):
    - one or two members: no recall is possible;
    - three: both others recall;
    - four: all three others recall, and two of three do not;
    - five: three of four;
    - six: four of five;
    - seven: five of six.
  - One case shows the two counts side by side: of three, B and C do not remove A under StrictFloor(2, 3, 2).
  - `models/causal_kernel/check_recall.py` has 14 cases in every arrival order, in the `seat` fixture, with five
    planted breaks. Five plants in the crate.
- **Options holding no first choice are struck together**, in every round of every ranked count, before the
  weakest is sought (#241 E1). `ranked::ranked`'s answers change:
  - with a declared order no winner changes, only the rounds;
  - with none, a count that seated nobody on a tie at zero now reaches a winner, with four or more options.
  The `reexpress` fixture now holds 600 cases of four to six options beside its 480 of three, and no case of
  three options moves. Over the new cases:
  - with a declared order, the rounds change in 101 of 552;
  - without one, the rounds change in 96 of 528, and 11 counts that seated nobody now seat someone.
- **`ranked::runoff`** (new) is the runoff order: the one count repeated. The first is the count's winner, the
  next is the winner of the same count over the same ballots with those ahead of it struck, and so on; a step
  that ties ends the order there. Each step is `ranked`. Its reference is `reexpress.runoff`; the fixture
  carries each case's order, and `tests/lib_ops.rs` replays it. The seat rule does not use it in this tag.
- `models/causal_kernel/check_ranked.py` has eight hand-written cases and three planted breaks in `reexpress.py`.
  There are three plants in the crate.

**A moderator's lone removal: the four receipt items** (CIRISConstitution#218, pin list). New: one trait method,
`SeatRow::lifts` (default `false`), additive. Answers change only for rows no case had before:
- No cascade: a lone removal that is out of force ends no standing. A moderator's lone removal whose signer is an
  agent removed in turn by a lone removal out of force stays in force. The acts are decided after the lone
  removals of their signers' keys. Where two agent moderators remove each other at one head the two are decided
  together, each an end of the other's standing (CC 2.7.7 rule 5: "Two cuts by keys of equal standing that undo
  each other stay contested. A voice that the other cannot remove settles them"): each counts at its own head,
  neither is in force, and both agents stay seated and keep their duty, until a person holding the duty
  receipts one of them (or removes one), or the members' count does.
- A count's own receipt: a `SeatKind::Ack` naming the removal with `Conf::Group`, counted over the persons at its
  heads, keeps it in force where its count is met, beside a duty holder's receipt.
- A receipt by a key removed at the same time is void: a duty holder's receipt keeps nothing where a counted
  unseat of a seat that holder holds over the room does not have the receipt in its past (conferral's key_cut).
- A count end that lifts receipts (`lifts()`, conferral's word), in CC 2.4.1.1's three cases: (i) a counted unseat
  ending the moderator's standing may lift, and (iii) a conferrer ending its own offer (its withdrawal of an offer
  that seats the moderator, counted or not) may lift; then every receipt but the count's own keeps nothing.
  (ii) The holder's own end never lifts: the text refuses such a row at the door (`lifts_on_own_end`), and the
  kernel, handed one, reads no lift. A moderator's lone removal lifts nothing.
- A counted receipt that fails its count keeps nothing, and is not read as its signer's own receipt (confirmed).
- Fixes from the review of #48: the count's receipt is a count over the persons of the removal's room, at heads
  none older than the removal's, the remover no voice of it (before: any room, any head, any `counted` scope, so
  a remover alone, or an agent, could keep its own removal). The acts are decided one strongly connected
  component at a time, in rounds, against every act decided out of force before (before: an act outside a
  mutual pair was decided with it, and only an act's own waits were left out). An ordered pair is not mutual
  (its order is the review of #54's, below). A receipter's duty from a founding record is a seat a counted
  unseat ends, as one from an offer.
- Ruled: an agent's receipt is no receipt (CC 2.4.1.1: never the act's own signer's and never a node's; keeping
  another's act in force is a voice). For every lone removal, a mutual pair's included, the receipts that keep it
  are a person duty holder's other than the remover's, or the count's. One answer changes: an agent moderator's
  receipt kept a lone removal and now keeps nothing. A lone removal of a receipter no longer orders anything,
  since a receipter is a person and a lone removal removes only an agent.
- Ruled (R5): the count's own receipt is over the persons of the room at the removal's head or later, the remover
  apart in the base as in the voices (as the overturn and the lift). Four persons with the remover one: two of
  the other three keep the removal; one does not.
- Ruled: a ring of three or more concurrent lone removals, each undone by another, is read as the pair is (CC
  2.7.7 rule 5 read for a set): all out of force, all seats kept, until a person's receipt or the count's
  settles it.
- Fixes from the review of #54. The count's receipt is read under one fixed rule, the members' check of one
  member's act (the lift's own arithmetic): more than half of the persons of the room less the remover, never
  fewer than two, whatever `policy()` or `need()` the row states. Before, the row's own policy was read, so one
  person's ack under `accord_halt`, or the remover's or an agent's under a declared need of none, was the count's
  receipt, which no lift lifts. Changed answer: each of those rows now keeps nothing.
- No cascade through an earlier act: an act's verdict now waits for every lone removal that could end its
  remover's standing, the ones in its past included (before, an act was decided before an earlier act in its
  past, reading that act as an end, E4, before its own verdict was known). An ordered pair (y has x in its past,
  and each removes the other's remover) is decided x first, without y, and y then reads x's verdict: x in force
  ends y's standing; x out of force on its own (its remover lays the duty down) ends nothing, and y is in force.
  Changed answers: in those two shapes the later act was out of force and is now in force.
- Not built: the owner's statement on an agent's duty seat (CC 4.5.4).

The reference: `seat.receipts_of`, `lifts_receipts` and the ordering in `out_of_force`; thirteen cases and six
planted breaks in `check_removal_in_force.py`, each named for its row of the pin list. Six crate plants; the
review of #54 adds thirteen cases, three planted breaks in the reference and three crate plants.

**A duty is conferred by its holders, the founding record or an election** (CC 4.5.4; CIRISConstitution#241). This
follows #48. **Answers of 0.4.0 change.** **Breaking:** one required trait method (`SeatRow::word`, below).
- The gate, `seat::seat_rule`: a counted offer of a duty scope over a community concludes only where it is the duty
  holders' count or an election's acceptance (`Policy::Ranked`). The duty holders' count is over all the duty
  holders of the room it confers in: `SeatRow::counted` the duty holders' scope itself (`duty`; one duty's holders,
  `moderate` say, are not all of them), under `duty_confer`, and `SeatRow::over` absent or the room. A members'
  count under an admission-style policy (`community_invite`, counted `member`), a count under another policy
  (`accord_halt`, one of n), and a count over another room (one a key founded alone, say) confer no duty, whether
  or not a duty holder lives. A counted unseat of a duty scope over a community is likewise counted over that
  room (`over` absent or the room).
- The own-offer rule: a single key's own offer of a duty (`Conf::Own`, or one under its seat, `Conf::Seat`)
  concludes only where its signer is the lone person duty holder, with the new holder's acceptance ("or by the
  lone holder with the new holder's acceptance"), in every community, not only where the record seats duty
  holders.
- **The one-founder room** (CC 4.5.4: "A record one person signs MAY name none, and that person then holds every
  declared duty"). A community's founding row (scope `member`) whose `to` is one key, signed by that key alone,
  with no `duty_holders` map, seats that key as a member and as holder of `moderate` always, and of each duty its
  record declares (`SeatRow::duties`), not the law's other named duties. Such a room is one where the duty rules
  engage. A one-signer record with a map: the map decides, as before. Several signers and no map: members and no
  duty, as before. The older presentation, a lone founder's row of scope `duty` with no map, still holds the
  law's named duties through `holds["duty"]`; it is left as it is (three cases of `check_duty_seats.py`, two
  tests of `attacks.py` and one world of `window.py` use it; seven scenarios of the seat fixture).
- **Breaking:** `SeatRow::word(s: &'static str) -> Self::Word`, required, the caller's word for a scope the crate
  names itself (only `moderate`, for the one-founder room's seat). For a `String` word:
  `fn word(s: &'static str) -> String { s.into() }`; for a `&'a str` word: `fn word(s: &'static str) -> &'a str
  { s }`.
- A counted row (offer or unseat, `Conf::Group`) whose heads are not each of its own object's line concludes
  nothing: a head is of object `o`'s line where it is `o`'s founding row, a row whose `obj()` is `o`, a
  withdrawal (`target()`), acceptance or receipt (`of()`) of such a row, or a row of no object of its own that
  names one (a version of the roster, as persist's `consensus::ballot_rows` presents a ballot's head). A row
  whose `obj()` is another object is of that object's line. No answer of a case changes.
- A moderator's lone removal exists only over a community (CC 4.5.13: a room's moderator, an agent's key in
  that room). Over any other object (a key's own roster) a moderator's unseat of an agent's key is an ordinary
  counted unseat. The one test of a community, read by the duty gate, the duty-room rule, the one-founder rule
  and lone removal: an object that names a held offer whose object is itself (a founding row), whatever its
  scope.
- `moderate` is always a declared duty of a community ("a duty every community's record declares", CC 4.5.4),
  whatever `SeatLaw::duties` names: under a law that omits it, the one-founder room's founder still holds a
  duty.
- A record's declared duties (`SeatRow::duties`) are never a roster scope: an entry `member` or `agent` is
  ignored (before, several signers declaring `member` made every member a duty holder, and a lone founder
  declaring `agent` held an agent's seat).
- `window::outcome`: a withdrawal that names a scope departs its signer (its later answers are a departed key's)
  only where it ends the signer's stay as a member over the object, as `Seats` reads a stay's end: one naming a
  duty (a founder laying it down) leaves its roster seat and its voice; the older presentation's founding seat of
  scope `duty`, laid down by a withdrawal naming `duty`, ends the stay, and so departs it; one naming `member` of
  an offer that seats no member (an `author` seat) ends no stay, and departs no one (before 0.5.0 it did).
- Changed answers of 0.4.0, `check_duty_seats.py`: "the same conferral on a member seats it" (a member-only
  room's members' count of moderate on D) seated D and now seats nobody; the member-only cases that rested on it
  ("that member resigns", "re-admitted after that, nothing revives", "a counted removal from the roster ends the
  member's moderate seat") are rebuilt on a room whose one founding moderator has laid the duty down, where an
  election seats a member and the members' count seats none. One member-only case stays, stated as "handed
  one". "A member-only founding, handed one: a founder's own offer of moderate seats a member" seated D and now
  seats nobody (no lone holder there).
- Changed answers of 0.4.0, the one-founder room. Its founder holds `moderate`, so it removes an agent's key
  alone, at once (in 0.4.0 it held no duty there, and the removal took the room's count). Its own offer of a
  seat the duty holders place (any scope but the roster's, `author` included, as in a room whose record names its
  holders) concludes only while it is the lone person duty holder, and its withdrawal of such an offer no longer
  ends the seat (the holders are equals: the seat ends by its holder or a count). `author` is no duty: its holder
  is no duty holder. And the duty holders read off a room founded by one key with no map, in the seat fixture
  (four scenarios of `check_removal_in_force.py`'s reviewer rows over the room `h`, and one of `attacks.py` over a
  room `z`): that key now holds `moderate` there.
- `check_agent_removal.py` world A: its moderator was conferred `moderate` by the members' count; it is now the
  founding moderator's own count (`duty_confer`), the founder then laying its duty down. No answer of world A
  changes.
- `check_removal_in_force.py`: the two cases of a moderate seat hanging under another (Z's) were built on
  members' counts. Inside a community the chain cannot arise (a seat conferred under one's own seat is the lone
  person holder's, and an agent is none); they are removed, with the wait on the seats a standing hangs under
  and its plant. CC 2.4.1.1 (iii), a conferrer ending its own offer, is reachable: in a room whose record seats
  no duty holder, an elected moderator, then the lone person holder, confers `moderate` by its own offer, and its
  withdrawal of that offer ends the seat. Its cases are rebuilt on that room.
- `check_rosters.py`: the property "when no duty holder is left the members' count seats one (and one member
  does not)" is now "when no duty holder is left an election seats one, and the members' admission count none
  (and one ballot does not)".
Plants: `duty_gate_off`, `duty_gate_wrong_row`, `own_duty_ungated`, `lone_founder_unread`, `duty_over_unread`,
`gate_counted_any_duty`, `gate_policy_unread`, `declared_roster_kept`, `heads_any_object`, `lone_any_object` and
`window_scope_roster_only` in the reference, each with a crate plant; and the crate's `SeatRow::word` read as
another scope than `moderate`.

**The act-to-policy binding, steps 1 and 2** (the Constitution's `governance_policy_acts.tsv`). Nothing refuses yet:
no answer of any case changes.

- The policy data moves to the Constitution's rc23 (commit `f1773bf`, table pin `8d58a472`; `data/README.md`). It
  adds two rows, `duty_confer` and `duty_withdraw`, and changes the wording of `moderator_recall`'s base, a
  `moderator_election` floor rule, and two `self_roster_*` `at_window` cells. No rule reads the changed cells, and
  the fixture law is unchanged: `seat.py` already reads the two duty rows as the duty counts.
- `data/governance_policy_acts.tsv` is new (rc23 at `dd358a3`): which policy rows each counted act may take. `seat.py` loads it
  (`ACTS`), and the seat fixture's law carries it (`acts`). No rule reads it yet.
- New, read by no rule yet: `seat::Act`, `seat::ScopeClass`, `seat::CommunityKind`, `seat::Choice` (each
  `#[non_exhaustive]`, with `word()` and `from_word()`), `seat::ActRule`, `seat::kind_of`, `seat::act_of` and
  `seat::policy_for`. `act_of` decides a counted row's act from its kind, scope and object:
  - the lift: an offer naming a removal of the same seat; the table binds the agent's re-seating;
  - an admission or a removal: of a roster seat;
  - the holders' conferral or withdrawal of a detector seat: `detect:*` (CC 4.5.7);
  - a conferral: another duty;
  - a withdrawal or a recall: by `counted()`, the body the row counts (the duty holders, or the members).
  An accord's rows are standing acts; a self roster's rows admit or remove a key. Any other scope is no act.
  `policy_for(law, act, scope, kind)` is the store's query: the policy rows an act may take, and whether the row
  chooses.
- **The one act read from the stated policy**: an offer of a duty under the ranked count (`Policy::Ranked`) is the
  election's seating. **The election is not answered safely by this tag, and a caller must not rely on a ranked
  seating** (CIRISConstitution#241: the election is out of 0.5.0).
- **BREAKING for an exhaustive struct literal of `SeatLaw`**: two new fields. `acts: Option<Vec<ActRule>>` is
  `None` where a law binds no act to a policy: the behaviour before, with the binding left to the caller.
  `kinds` maps a founding row's scope to an object's kind. The seat fixture's law carries `Some(acts)` and the
  kinds. A literal with `..Default::default()` is unaffected.
- Gap: the roster instances of `roster.py` (the `tables` fixture's `R:...` policy names) are not bound to acts
  yet; their law carries `None`. The windows' specs stay the caller's.
- The reference: `models/causal_kernel/check_acts.py`, with 23 cases and 15 queries, six planted breaks, and the
  `acts` fixture, which `tests/acts.rs` replays. Seven plants in the crate. Every existing scenario of every
  fixture is unchanged; the seat law gains `acts` and `kinds` only.

**A deputy under two standings** (CIRISConstitution#218, in no issue). New: `StandingRow::via` (default `None`)
and `StandingRow::sub_delegation` (default `false`), additive. `standing::answers` now judges a deputy's act:
- It stands on its deputy edge (`via`), the node's own act that names the owner's acceptance; it names no
  acceptance itself, and stands where its edges' root stands (or on no acceptance, for a cycle of edges).
- Both records read it with its edges through conferral's own deputy walk (E6.depth, E6.no_sub, E6.upstream);
  no second walk. It counts for the binding's owner where it and its edges count under the grant and under the
  binding, and is in force likewise.
- A re-binding of the node reaches the deputy's act as it reaches the edge: with the re-binding in its past it
  does not count for the old owner (E4 under the binding); concurrent with it, it counts and is not in force
  unless receipted under the binding by its owner. Because E6 passes both bits down, the act is in force only
  where its edge is too: a receipt of the act alone does not keep it.
- Two owners is none for the edge, and so for every act under it.
- The module header's "Not read here: a deputy edge under such an act" is gone.
- A root edge (an act standing directly on an acceptance, with no `via`) counts only where its signer is the
  grant's grantee (`Role::Grantee` under the grant's `role`); another key's root-shaped act counts for nobody:
  `Nobody::NotTheGrantee` (`"not_the_grantee"`), new. Without it a deputy skipped E6 by naming the acceptance
  itself. This is also the check that the node's own acts are the grantee's.
- A `via` naming a held row that is no act: `Nobody::EdgeNotAnAct` (`"edge_not_an_act"`), new (before: undecided on
  a row already held). A chain longer than the deputy depth by more than one hop: `Nobody::TooDeep`
  (`"too_deep"`), new; the walk to the root edge is at most `deputy_depth + 1` lookups in an index of the rows, so
  `answers` is O(acts · deputy_depth · log rows) for this walk. A cycle of edges stands on no acceptance.
- **Breaking:** `standing::Nobody` gains three variants.
- The reference: conferral_end.py's deputy walk is bounded as the crate's is (it hung on a cycle of `via`) and an
  edge not held is undecided there (it raised).
The reference: `chain_answers` in `check_conferral_two.py`, with fifteen cases (`DEPUTY_CASES`, in the
`conferral_two` fixture, read as listed and in reverse; the plants compare reasons as well as bits) and four
planted breaks; four crate plants (142 after merging main). `tests/conferral_two.rs` now withholds any row, a deputy edge among them, and
reads an undecided act as the fixture does.

**The moderation windows land by signed rows; the fallback's vote is a ballot** (CIRISConstitution#221). One
public enum gains a variant (`window::Base::Stated`: an exhaustive match breaks); five public functions; no name
changes.

- The ruling on #221: a member's vote on a moderation action where no moderator acts is a ballot of
  `ballot:moderation_action` (dimension `ballot:moderation_action:v1`), `for` or `against`. A contrary voice is a
  vote against. There is one ballot a person, folded as `ballot:moderator` is. The family is the caller's, so the
  name is in the reference's table (`WINDOWS["moderation_fallback"]["ballot"]`) and the fixtures, not in crate
  logic. The fallback's at-close clause reads `for` where it read `act`: **an answer changes** for a caller whose
  table still says `act` (an `act` answer is then no ballot). The reference's cases, `attacks.py` and
  `roomkey.py` now say `for`.
- New: `window::unwithdrawn`, `window::own_withdrawals` and `window::ballot_words`. A ballot is an answer that a
  `How::MoreOfVoted` clause reads (its value or its `against`). A ballot whose own signer withdrew it is no
  ballot. The withdrawal is a seat withdrawal naming the ballot. Another key's withdrawal withdraws nothing. A
  cosigner's withdrawal of the ballot does conclude (the seat rule reads every signer of the row it names); only
  the match on the ballot's own signer (`own_withdrawals`) refuses it. A case and a plant in each language cover
  it. The fold of what is left is `ops::one` per signer: agreeing ballots are
  one, and disagreeing ones say nothing. This is the rule `ranked.rs` writes inline for `ballot:moderator`. A
  withdrawal concurrent with a landing is recounted with it, as an answer is. **Answers change** only where a
  ballot is withdrawn: no case before this one had such a withdrawal. Only a ballot is read so (ruled): an
  objection or an approval its signer withdrew is still a voice.
- One landing family for every window (ruling W1): the receipt is `window:held` and the landing `window:landed`,
  which states the outcome. These are the caller's table entries. The crate reads a row's `WinKind`, never its
  family, and checks none. No code here reads them.
- Who signs (ruling W2): the fallback's landing by any member at the opener's head; the overturn's by any member
  but the act's author. New: `window::author_apart`. Where every counted clause of a table is over
  `Base::Others`, the opener's signer concludes no receipt and no landing of that window. **An answer changes:** an
  overturn's receipt or landing by the act's author concluded before. No earlier case had one. New cases show that
  a key with no seat at the head lands nothing.
- `halt_fuse` is the holders' confirmation of a halt, a count (CC 4.2.1.1); the halted node's own fuse, on its own clock with no landing, is the node's and is not read here (ruling W3, as corrected). A met confirmation count gives `confirmed` with no
  landing, and a concurrent `lapsed` landing does not undo it. The table's answers are unchanged, and it is
  marked so in `window.py`, `window.rs` and ADOPTING.md. The name `halt_fuse` is a misnomer, kept for now: the
  adversary table and the fixtures carry it.
- `head::View::window(now)` is a per-node reading that decides nothing that counts (ruling W5). This is in its doc
  comment only; the code is unchanged.
- W4, the overturn's landing binding the objections it was counted over, was tried and is withdrawn. Two rows of
  the adversary table break under it ("a majority's objections are not overridden by a landing"). Today's reading
  stands: an objection concurrent with the landing is recounted with it, and one that names the landing counts
  for nothing.
- New: `window::Base::Stated(n)`, the base `active` above the base law's `k`: the caller's stated count, the
  census's figure (CC 6.1.9), which the kernel takes and does not check. The voices are those of `Base::All`. The
  size counted over is `n` where `n` is larger than the members at the head, and never smaller. With it,
  `default_content`, `default_standing`, `default_irreversible` and `community_invite` are expressible above `k`
  as the self roster's lone path, by the same shape. Only `default_content` has a table and cases: the reference
  has `("stated", n)` and the spec `default_content@active` (a room of thirteen members counted over twenty), with
  five cases, one of them on the clamp. The crate also has a unit test of the size computation past `u32::MAX`.
- The count is read in `u128` on every target. New: `seat::met_wide`, which is `seat::met` over `u128` counts;
  `met` calls it. A window's thresholds read the members, the voices and a stated `u64` through it, so no cast
  truncates: a 32-bit target (wasm32, thumbv7em) reads a stated 2^32 as 2^32, not as 0. Two cases (a stated 2^32
  and 2^32 + 13, thirteen members, nine approvals: open) and a plant on a 32-bit cast cover it. The unit test
  that compares reading the scopes walked at once with reading each when asked now also draws clauses counted
  over those who voted, stated bases (some past 32 bits) and withdrawals.
- `window::author_apart` assumes that a table every counted clause of which is over `others` is a judgment of its
  opener's signer. That holds for the members' check, where the act opens its own window. Nothing ties the opener
  to an act. Two cases of a table built for it (`proposal@others`, whose opener proposes) show what the code gives:
  the proposer concludes nothing, and another member lands it. ADOPTING states the assumption.
- A table built to reach the path with no landing (`ballot@once`, a ballot count met at once) shows a ballot's
  withdrawal read there too. No policy row's table has such a clause.
- A withdrawn ballot stays withdrawn (ruling C2): a withdrawal of the withdrawal revives nothing, and the way back
  is a new ballot. Two cases (a withdrawal of a withdrawal; a withdrawal and then a new ballot) and a plant in
  each language cover it.
- A poll is outside the kernel (a tally whose rule and close its own opening row states). ADOPTING.md says so.
- OPEN: the door model (the Constitution's `door.py`, not in this repository).
- The reference: `window.unwithdrawn`, `window.ballot_words` and `window.author_apart`; 31 new rows of
  `window_adversary.tsv` (112 now, every earlier row unchanged); and `models/causal_kernel/check_window_rows.py`
  (those rows in arrival orders, eleven planted breaks, the OPEN list). Eleven new crate plants in
  `tools/kernel_crate_plants.sh`.

**The act-to-policy binding, step 3: the refusal, and the room's declared protocol** (the Constitution's
`governance_policy_acts.tsv`).

- **The refusal.** With a law that carries the acts table (`SeatLaw::acts` `Some`), a counted row is counted
  under the policy its act may take, never one it states otherwise (`seat_rule`'s count and the fold at tips read
  it through one function). The act comes from `act_of`.
  - For a `fixed` act the row may state the one row or none, and is counted under that row.
  - For a `row` act it must state one of the rows listed.
  - A counted row over an object with a kind whose act has no row, or that states another policy, concludes
    nothing.
  - A law with `acts: None` leaves the binding to the caller, as before. The `tables` fixture's law is such a law:
    the roster instances (`roster.py`'s `R:...` names) are not bound to acts yet.
- **The room's declared protocol.**
  - New: `SeatRow::consensus_protocol()` (default `None`), the protocol a community's founding record declares
    (CC 3.3.4), read on the founding record only. New: `seat::protocol_of(get, obj)`, the one read of it, for the
    refusal and the room-key rules. The door refuses a record that declares none, or one outside the protocol
    table (`federation_community_consensus_protocol_violation`); handed one, the kernel concludes nothing under
    `cosigned_act`.
  - **BREAKING for an exhaustive match on `seat::Policy`**: `Policy::Protocol` is new. It is the policy table's
    protocol rows (`cosigned_act`, `community_remove`, `wa_adjudication`, whose enact cell reads `protocol`),
    counted under the founding record's protocol and never one a row states. Where the record declares none,
    they conclude nothing.
  - A counted admission or removal over a community therefore concludes only under `community_invite` (the
    two-path) or the room's declared protocol. The protocol words are policy words of the law (`majority`,
    `two_thirds`, `one`, `quorum` in the reference).
  - The reference's communities declare `two_thirds` on their founding records (the builders' default). Before,
    `seat.py` read `community_remove` as two thirds for every room.
- **Answers change:**
  - an admission or removal stating a policy its act may not take (`accord_halt`, say) concludes nothing;
  - a removal is counted under the room's own protocol: of four under `majority`, three remove and two do not;
  - a room whose record declares no protocol concludes no removal and no `cosigned_act` admission;
  - a counted row of a scope that is no act (a seat no act names) concludes nothing.
  `check_agent_removal.py`'s case of a non-member seat presents that seat as a detector seat (`detect:author`),
  the one such seat the table binds. Its answers are unchanged. `check_duty_seats.py`'s `gate_policy_unread` and
  the crate's "the duty gate reads no policy" are retired: with the table the refusal does that work first.
- **An infrastructure community** (the acts table at rc23 `4c165f8`):
  - New: `SeatRow::cohort_subkind()` (default `None`), on a community's founding record. `infrastructure` makes
    the object `CommunityKind::Infrastructure` (new); any other value, or none, makes it a community.
  - Its acts are the admission and removal of a founder's seat (`ScopeClass::Founder`) and of a node's seat
    (`ScopeClass::Node`), each under the group's declared protocol, fixed.
  - New: `seat::NODE` (`node`), a roster seat of its own. It is on the roster (`Seats::roster`), no voice, and
    in no base, as an agent's seat is.
  - A node's seat over a community is no act the table binds: it concludes nothing there. Whether a node's seat
    needs its own consent is the room-key lane's rule.
- Built in later steps: a change of a room's protocol and `SeatRow::regime()` (step 5), and the narrow gates
  (step 4).
- The reference: `check_acts.py`'s 16 refusal cases, each with the table and without, and four planted breaks in
  `seat.py` (the binding, the stated policy, the protocol, the cohort_subkind). `tests/acts.rs` replays them.
  Five plants in the crate.

**The act-to-policy binding, step 4: the dispatch reads the act.** Where the law binds acts, the count is no longer
told what act it is by the policy a row states.
- The members' lift is told by its act (`act_of`: an offer naming a removal of the same seat), in the count and in
  the fold at tips. With no acts table, or over an object with no kind, it is told by its policy, as before.
- The duty gate reads the policy in force, not the stated one. A duty conferral stating no policy is counted under
  its act's fixed row, `duty_confer`. **An answer changes**: before, the gate refused such a conferral.
- The recall is told by its act: an unseat of a duty counted over the members (`counted()`, the body the row
  counts), as against the duty holders' withdrawal. The exclusion of the recalled holder from its base and voices
  keys on `Act::Recall`, and `Policy::Recall` is only the threshold the fixed `moderator_recall` row maps to.
  Under the table the two always coincide, because the table fixes each act's policy: a duty holders' unseat
  stating `moderator_recall`, or a members' unseat stating another policy, concludes nothing. So no planted break
  can tell them apart; the keying matters for a law whose table maps the acts otherwise.
- Unchanged, and the one exception: the election's seating is still told by `Policy::Ranked` (see step 3).
- One case in `check_acts.py`, one planted break in `seat.py`, two in the crate. No other answer of any case
  changes.

**The act-to-policy binding, step 5: a change of the room's protocol, and the regime.**
- **A change of the record** is the act `record_change`: a counted offer of scope `record` over a community
  (`ScopeClass::Record`), counted under one of the table's listed paths. `cosigned_act` is the protocol in force
  in its own past. A change that states `consensus_protocol` changes the room's protocol.
- **The protocol in force** (`seat::protocol_of(p, obj)`, which now takes the row's past `p`): the newest change
  in the row's own past, or the founding record's. A row that names the change, or has it in its past, is
  counted under the new protocol; a row beside it is counted under the old one. Where the newest changes
  disagree (two concurrent changes naming different protocols), no protocol is in force, and the row concludes
  nothing under `cosigned_act` or `community_remove`. A seat outlasts a change of protocol (CC 4.5.4): no seat is
  judged again under the new one. The notice `hard_case:community_consensus_protocol_change` is the caller's to
  emit.
- **The regime** (the reading: the room's protocol in force in the row's past; the act's policy is already fixed
  by the table). A counted row's regime is the room's protocol in force in its past, once the binding reads it.
  Each act's own policy is fixed by the table, so it is no part of the room's regime.
  - Tips that differ in it wait at the fold: tips on either side of a change of protocol do not fold, and tips
    of an admission and a conferral do.
  - A stated `SeatRow::regime()` is a consistency check only: one other than the protocol in force concludes
    nothing.
  - With no acts table the stated regime is read as before.
- **Answers change**: a removal or a `cosigned_act` admission naming a change is counted under the changed
  protocol, and tips across a change wait.
- The reference: `check_acts.py` has seven protocol-change cases, two tip cases, four planted breaks, and an act
  case and a query for `record_change`; all are in the fixtures. Four plants in the crate.

**One of each** (no public name changes; the fixtures and conformance runs are unchanged).

- `content` reads `conferral`'s three-way `any`, later-head test and stale-head test; its own copies are gone.
- `trust::reaches` and `EdgeIndex::reaches` are one walk over two sources of a key's edges.
- `window`'s thresholds are the seat's two comparisons (CC 4.5.13: strictly more than a fraction, at least a
  fraction), read by `seat::met`, each with a floor in voices and a choice of base. One answer changes in
  principle: `How::AtLeast` over an empty base is never met (before, a floor of zero was met by nobody). No
  case of the reference or the fixtures takes one. The fold's duty arm goes through the seat rule's count.
- `key_end::live` reads `covers_at`.
- `kernel/TEXT.md` was a copy of CC 2.7 at 1.0-rc19 and is a pointer to the Constitution's section.

**The end of a key record is outside it** (CC 2.6.2: "covers an instant t when its `asserted_at` <= t < its
`valid_until` ... an equal one covers nothing"; CC 2.4.1.1 on a rotation: "at or after its `asserted_at` and
before its `valid_until`"). Three answers change, all at the exact end; no generated world of the reference
reached one, so no earlier fixture answer moves.

- A rotation whose old-key instant equals the old record's end concluded and now does not (it names no
  successor). A row whose own instant equals the end of the record it names concluded and now does not.
- The door refuses a record whose end equals its own instant (`well_formed`: `from < until`; it was `<=`).
- One test, `covers_at`, for a key's liveness, a row's own instant and a rotation's; `key_end`'s closed test is
  gone. Reference: `key_end.covers`; five boundary worlds (`check_key_end.BOUNDARY`, in the `key_end` fixture),
  attack K11, plant `end_closed`; one crate plant on the door.

**The review of room-keys** (derived from CC 3.1.3.2, CC 3.2 and CC 4.5.13 on CIRISConstitution#224). Answers that
change, each with a case in `check_room_keys.py` and a plant in each language:

- F1: in a private room an ended stay in any roster seat bars every roster seat of that key (a room key is one
  presence in one room), after a removal as after a resignation. Before, a removed member could be admitted as an
  agent.
- F2: a scope that holds `member` (`founder`) is a roster seat for finality. Before, it was read as `registered`.
- F3: seats are compared by what they hold, not by name: a founder of scope `duty` admitted as a member too ends
  both by one withdrawal. Before, the two were two presences.
- F4: a key's own end of its stay voids its own consents that do not have the end in its past, a standing
  acceptance given earlier included, in every room. Before, a re-admission concurrent with a resignation that named
  the key's earlier standing acceptance seated it.
- F5: a withdrawal of an offer the key never consented to is a decline, and no end of a stay (`seat::stay_end`;
  a standing acceptance withdrawn before any offer named it, likewise). Before, declining an invitation, or an
  unsigned listed founding member withdrawing the founding record, barred the key for ever in a private room.
- RK1: a roster seat over a community needs the key's own consent under every protocol: an offer waiving it
  (`consent_one`) concludes nothing, except a node's seat over an infrastructure community (never a founder's).
  New: `CommunityKind::Infrastructure`, the kind of a founding row of scope `founder` (`seat.KINDS`; the enum is
  `#[non_exhaustive]`).
- RK2: over a group a member or agent seat is placed or removed only by a counted row, the founding record, the
  key's own end, or (an agent's key) a moderator's lone removal: one key's own row (`Conf::Own`) or a row under a
  seat (`Conf::Seat`) of such a seat concludes nothing, offer and unseat alike. A room of one still grows by its
  member's counted proposal and the newcomer's acceptance (a case); an `open:self_admit` admission is a counted row
  and is unchanged (`tests/policies.rs`). Whether a counted row meets the room's DECLARED protocol is the binding's
  read (`act_of`), not this one.
- R-a: a counted row concludes whole or not at all: in a private room an admission naming several keys, one of whose
  stays has ended, concludes nothing for any of them (a case).
- Existing answers that move: `check_duty_seats.py`'s two lone-founder cases with an own offer of `member` (`ms`
  now concludes nothing; the first case's founder is no member after its withdrawal); `check_rosters.py`'s
  Inv_JoinerConsented mutation worlds (an admission with `consent` `one` over a community concludes nothing) and
  Inv_LeavingNotUndone, "leaving read as a withdrawal of the seat" (it now holds: the old standing acceptance is
  void; `roster_expected.tsv` updated in all three instances). The crate tests that seated roster seats by
  `Conf::Own` (`fast_paths.rs`'s ballot and seat world, `policies.rs`'s founders, `window.rs`'s and `seat.rs`'s
  generated groups) now seat them by the founding record or counted rows.
- Not changed: the unreachable arm "a non-counted unseat is final" is gone (every roster unseat over a community that
  concludes is counted).

**A removed room key is not seated again** (CIRISConstitution#224, the steward's decision of 2026-11-25: "a removed
room key is not seated again. A person removed from a private room returns only under a new room key, by a new
admission", of any end of the seat, a resignation included; CC 3.1.3.2: "a member admitted again makes a fresh one").

- New: `SeatRow::private_room` (default false), the founding row's `membership` `private`. A founding row with no
  `membership` reads public.
- `SeatLaw::final_scopes` names `member` and `agent` as well as `registered` (the fixtures' law). A roster seat
  named there is final over a private room only, by an end that stands: a counted unseat of that seat (its count
  met over its own past, or not counted) with an offer seating the key in that scope in its past, or the key's own
  end of its stay (its withdrawal of the offer, of its acceptance, or of the founding row). The one mechanism,
  `revoked_before`, reads it; a scope that is no roster seat (`registered`) reads as before.
- **Answers that change**, over a private room only: an offer that seats such a key again in that seat with the
  end in its past concludes nothing (a re-admission after a counted removal of a person's or an agent's room key,
  after a resignation, after a founder's end of its stay); an acceptance of an offer seating the key with the end
  in its past concludes nothing (before, accepting the same offer again after withdrawing the acceptance re-seated
  the key). No existing case of the reference or the fixtures has a private room, so no existing answer changes.
- Unchanged: a public room's re-admission stands; a moderator's lone removal of an agent's key is never final (ruled
  on #224: finality is of a counted end or the holder's own end): the members' lift restores the same key and
  concludes, out of force the key is seated with no row, and a counted admission of the key under a lone removal in
  force and not lifted seats it; a duty laid down may be conferred again (a duty seat is not the room key's seat in
  the room: a reading).
- A row concurrent with the end concludes (the rule is by past). Beside a counted removal it does not seat: the cut
  voids it, a row naming both leaves the key out, and a later admission naming that row concludes nothing.
- Not built: the move of a room from private to public (no seat row carries it; whether a voice seated before the
  move keeps a final end is not stated); the voice's own key roster (#224: "a device key of a voice ended by the
  voice's own count is final for that device key"; a voice is a key object with no founding row, so no seat row
  says it is a private room's). The text's name for the refusal is `membership_room_key_ended`; the crate concludes
  nothing and names no refusal. A room is private or public by its founding row (a rule: no record change moves
  it), so no later version is read.
- **A key's own end voids its own concurrent voices**, in every room (ruled on #224: the rule a removed key's
  concurrent rows have, read for the key's own end). In `Seats`, a key's signature on an offer of a roster seat, or
  its acceptance of one, that is concurrent with its own end of its stay in that room (neither in the other's past)
  is no voice: the offer lacks that key's consent and seats nobody. The end is of one seat (the scope the withdrawal
  names, else its target's): the key's voices on its other roster seats are untouched, as are other keys' rows. **Answers that
  change**: a re-admission concurrent with the key's resignation concludes and seats nobody (before, it seated the
  key, also after a row naming both); a second acceptance of the same offer concurrent with the withdrawal of the
  first seats nobody (before, it seated: the key un-resigned by not naming its own withdrawal). The test is by past,
  never by what a row names. No existing case of the reference or the fixtures moves (every room was compared).

**A second seat row of one room key** (derived from CC 3.1.3.2 on CIRISConstitution#224). A second seat row of a key
already seated is a second basis for the same seat: one key, one voice, no refusal (as built). An end is the key's end
of its stay in that scope, not of a row: one resignation, like one counted removal, ends every seating of the key in
that scope in the end's past (`Seats`; the duty-seat reading of a resignation, read for the roster seat's own scope).
A seating concurrent with the key's own end is void by the rule above; one concurrent with a counted removal is cut,
as before; in a private room the end is final. **Answers that change**: a key seated by two rows that withdraws one
of them is out (before, the other kept it seated); a key that withdraws its acceptance and accepts the same offer
again seats nothing, in every room (the offer is in the end's past), and returns by a new admission (a public room)
or not at all under that key (a private room). A counted removal already cut every offer on the slot in its past. No
existing case of the reference or the fixtures moves (every room was compared).

**Two admissions of one person at once** (derived from CC 3.1.3.2 on CIRISConstitution#224, a residual): no answer
changes. Two admissions under two room keys at concurrent heads both seat, and each key is a voice in the room's count.
The kernel counts voices as presented; which keys are one person's is the binding, never a row, so the collapse is
the caller's until the voice's own key roster is built (ADOPTING.md).

A counted row concludes whole or not at all: in a private room an admission naming several keys, one of whose stays
has ended, concludes nothing for any of them.

The reference: `seat._revoked_before`, `seat.room_key_ended`, `seat.private_room` in `models/causal_kernel/seat.py`;
`check_room_keys.py` has 54 cases and no OPEN row in every arrival order (up to six rows, else 41 orders) and twenty
planted breaks; `roomkey.py` states the finding of re-admission under the same key for a public room and the refusal
for the same room declared private. Twenty-one plants in `tools/kernel_crate_plants.sh`.

## [0.4.0]

The first tag of the 0.4 line (`kernel-v0.4.0`), after `kernel-v0.3.0`. Several answers change, one public
enum gains a variant (`standing::Nobody::TwoOwners`: an exhaustive match breaks), and `SeatRow` gains
`duty_holders`. Known to be missing, each stated below where it belongs: the owner's statement on an agent's
duty seat is not read; four ruled readings of a receipt of a lone removal are not built; a counted window
clause over a duty that leaves an agent out has a case in the reference only (no policy table has such a
clause, so no fixture carries one).

**A founding record seats its listed members and its named duty holders** (CC 4.5.4: "A founding record seats
the duty holders it names, each by their own signature on it. ... The record names them in `duty_holders`, a
map from a duty to the set of members who hold it, each a listed member who signed the record.").

- New: `SeatRow::duty_holders` (default empty), a founding record's map from a duty to its holders, as
  `&[(Word, Vec<Key>)]`. A founding row (an offer whose object is its own id) with a non-empty map seats each
  key of `to` that signed it (signer or cosigner) in the row's own scope, `member` as presented, and each such
  key an entry names in that entry's duty. No count is taken, so no floor is asked and "no key admits itself"
  is not engaged: one, two or twelve founders run alike.
- A founding row seats by the signatures on it, with or without a map: a key of `to` that did not sign it is
  seated in nothing, and a later acceptance of the row does not seat it (CC 3.1.3.2's terminal reason
  `membership_founding_member_unsigned`); it joins by an ordinary admission. **An answer changes** for a founding
  row with no map: before, an unsigned key of `to` that accepted it later was seated. An entry naming a key that
  is not a listed signer seats nothing; the text refuses such a record at the door
  (`founding_duty_holder_not_signer`, CC 4.5.4), and the crate, handed one, seats nothing for that key.
- `SeatRow::scope` is now read on a withdrawal: a withdrawal of a founding record naming a scope ends that one
  seat of its signer's (a founder laying down a duty), and is no end of its stay. With no scope it ends every
  seat the row gives its signer, which is an end of its stay and ends the duty seats conferred on it in that
  withdrawal's past. A withdrawal naming a scope of an ordinary offer ends nothing unless the scope is the
  offer's. `seat::left_in_past` reads the withdrawal's scope where it names one.
- `seat::Live::scope` is the seat's scope. For an ordinary offer that is its scope as before; a founding record
  gives one `Live` per seat, with the same `offer`.
- The duty rules engage over a community whose founding row has a map naming a holder, as over a founding row
  of scope `duty`. A founding row of scope `duty` with no map is read as before.
- The chained founding presentation (one counted `member` row per founding holder; a lone founder's own
  `member` offer to itself) is withdrawn from ADOPTING.md, and with it the note that two founders had no
  presentation. Its cases in `check_duty_seats.py` that only showed that presentation are gone; the founding
  record's cases replace them.

The reference: `seat.found`, `seat.seat_scopes`, and `withdraw(..., scope=)` in `models/causal_kernel/seat.py`;
`check_duty_seats.py` has 58 cases (the founding record with one, two and three founders, a duty laid down, the
stay ended, a duty conferred after the founding, a counted removal, a counted duty withdrawal of a founding seat,
a founder with no entry, an unsigned listed member, an entry naming a key that is not listed) in every arrival
order, and ten planted breaks. Four new plants in `tools/kernel_crate_plants.sh`.

**The duty-seat rule reaches every room.** "Under the text a duty seat conferred by any path stands only while its
holder is a member." Before, the membership condition and the no-revival half engaged only over a community whose
founding row seats duty holders. Now, over any community (an object that is its own founding row), a seat whose
scope makes its holder a duty holder (`duty`, a duty the law names, one the record declares) is live only where
its holder holds the roster's seat (`member`, or `agent`) at the same reading, and a holder's own end of its stay
ends the duty seats conferred before it, as a counted removal does. `seat::stay_ended_in_past` reads every
community. Who may confer a duty is unchanged (the duty holders' count or the lone holder where the founding row
seats duty holders; the room's count otherwise, and "the members' count seats one" where no duty holder is
left). A node's detector seat is still not asked for membership. Answers that change: a room founded with
members only whose members' count confers `moderate` on a key that is no member seats nobody (the case of
`check_duty_seats.py` that said "not reached" now answers no); in `check_agent_removal.py` world A the moderator
is admitted before its conferral, so the roster there gains it, and no conclusion or window outcome of that world
changes. New cases: a member-only founding, a counted conferral of `moderate` on a non-member (nobody) and on a
member (seated), that member's resignation (the duty ends), its re-admission (nothing revives), and a counted
removal. Two plants in the crate.

**Two owners is none, in `standing::answers`** (CC 3.2: a key with two live owner-bindings naming different owners
has no owner; `seat::Seats::one` runs that rule). Where the rows hold a binding of the node to another owner than
the one the act's acceptance names, neither re-binding the other (one in the other's past without re-binding it is
still live), and no re-binding of that other binding in the act's past, the act counts for nobody: `Answer::Nobody(Nobody::TwoOwners)` (`"two_owners"`), new. Before,
the two bindings were read as two stints and the act counted under the one its acceptance names. Several live
bindings to the same owner are one owner, and a re-binding that names the binding before it is unchanged. A
binding is live at the act unless a re-binding of it is in the act's past, the reading `chain_answers` already
gives a stint's end; so an act whose past holds only the first owner's binding counts for nobody once the reader
holds a concurrent binding to another owner, and one whose past holds a re-binding of that other binding stands.
**Breaking:** `standing::Nobody` gains `TwoOwners`, so an exhaustive `match` on it must add the arm. The
reference: `chain_answers` in `check_conferral_two.py`, with six cases (`TWO_CASES`) in the `conferral_two`
fixture; two plants.

**Fixes from the review of 2026-11-25** (each with a case that failed before it and a plant):
- A moderator's lone removal concludes only where the key it removes holds an `agent` seat at the head the row
  names. Before, an unseat in scope `agent` of a person's key, signed by a moderator alone, concluded and cut the
  person's duty seats while its member seat stood. The lift's "restores" test is this same test now (a
  re-seating stands only on a lone removal), so the separate test in `Policy::Lift`'s count is gone.
- A counted unseat of a roster scope ends a key's duty seats only where an offer in its past seats the key in that
  scope: an unseat in scope `agent` of a person ends no stay and no duty. The same reading for an end of a
  moderator's standing.
- A withdrawal naming a roster scope is an end of the signer's stay only where its target gives the signer that
  seat (`seat::stay_ended_in_past` and `left_in_past` agree on it).
- `standing::answers`: two bindings to different owners where one is in the other's past without re-binding it
  are two live owners, so none (above).
- `window`: `Base::Scope(s)` leaves the agents at the opener's head out, as `Base::All` and `Base::Others` do and
  as `seat::count_members` does for every counted scope (ruled: "in no count" is out of the base and the voices
  for every scope a counted clause reads (a fraction, a floor). A clause one holder's act resolves
  (`How::One`) still reads an agent holder's act (ruled 2026-11-25): an agent holding `moderate` answers a
  moderation fallback, and the window closes as `answered`; and the moderators a window hears through
  `moderate` include it. A counted clause over `moderate` leaves it out of the base and the voices.
- E3 over seat rows: an end's head that is not held makes nothing later, in the reference and the crate alike.
- A chain of lone removals is read in polynomial time: `Seats::new` keeps the members at a head for the builds
  below it, and the seats that give a remover its standing at a head once per (head, object, remover) (PERF.md). The reference read a chain of six in 6.9 s; it reads twenty-four in 0.18 s.
- `Seats::holders("member", o)` may hold an agent that holds a seat whose `holds` include `member` (a duty of
  scope `duty` under such a table); a caller wanting persons applies `seat::persons` with the agents. Ruled: an
  agent's key may hold a duty and is no voice in any count, the duty's own included.
- The kernel does not read the owner's statement on an agent's duty seat yet (CC 4.5.4,
  `founding_duty_holder_agent_owner_unsigned`): the seat rows carry no owner of an agent's key. Until it does, a
  caller must not present an agent's duty seat without the owner's statement having been checked at the door.

**A moderator's lone removal is in force only while the end rule says so** (CC 4.5.13 with CC 2.4.1.1 and CC
4.5.5). Before, the seat walk asked only whether the removal concluded; nothing in `seat` read the end of the
moderator's standing. No signature changes.

Answers that change, in `seat::Seats` (`recs`, `stands`, `holders`, `roster`, and through them `members_at`,
`count_members` and `seat_rule`):
- A moderator's lone removal of an agent's key (a counted unseat of an `agent` seat that concludes on the
  moderator's one voice, and whose count is not met) is an act under its `moderate` standing. It is a live unseat
  only where the end rule of `conferral` (E2 to E8, `models/tla/CONFERRAL_END.md`), re-expressed over seat rows,
  gives it in force over the rows held. Out of force, it ends nothing, and the agent's key is seated again for that
  reader. The window it opens is unchanged.
- E7: the removal is in force where a seat that gave the moderator `moderate` at the head the removal names is
  live and has no end held. Nothing else keeps it standing (CC 2.4.1.1: "from the end's head on it is not in
  force"; "A receipt changes what is in force, never what counted, and it revives no act"): a seat taken up after
  the removal's head authorises nothing earlier, so neither the same offer accepted again nor a new conferral puts
  it back in force. A moderator seated again who still wants the key out signs the removal again. An end in the
  past of the head the removal names is not read (the seat was live there again).
- The ends read: the moderator's withdrawal of the offer that seats it in `moderate`, of its acceptance of it, or
  of its stay; the room's counted removal of it from the roster; the other holders' counted withdrawal of its
  duty. Each takes the removal out of force from the end's head on (E2), unless a receipt of it is held: a
  `SeatKind::Ack` whose `of` is the removal, by a duty holder at the head the removal names other than the
  moderator, without the end in its past (E8). A removal that has the end in its past (E4), or names a head that
  has the end's head in its past (E3), does not count. The end's head: the heads a counted end names; for a
  withdrawal, the newest counted acts on the room in its past.
- Before: a removal signed after the moderator's duty ended, naming the older head, removed the key for a reader
  holding the end; a removal made while it held the duty stayed in force after the duty ended. Now neither does,
  unless receipted.
- The three kinds of end, the moderator's own laying down, the counted removal and the counted withdrawal of its
  duty, answer alike: out of force unless receipted, for good. No seat row lifts receipts, so a co-holder's
  receipt keeps the removal in force after a counted end as after a self end.
- At tips each line reads a lone removal as the whole set judges it.

Not done: a count's own receipt (only duty holders' acks are read); a receipt by a key removed concurrently is not
voided; an end that is itself a lone removal out of force still counts as an end (no cascade).

The reference: `seat.removal_in_force`, `out_of_force`, `lone_act` and `count_met` (the group count, factored out of
`seat_rule`) in `seat.py`, which re-express the rule on seat rows rather than call `conferral_end.answers`; it reads
the rows' past only, so it is a function of the set. `check_removal_in_force.py` is new: 26 cases in arrival orders
and four planted breaks (the end not read; a receipt by the remover keeps it; a remover seated again revives
its removal; a removal the room's count carries read as the moderator's). Plants in
`tools/kernel_crate_plants.sh`. No earlier case changes its answer: no case before had a moderator's duty end
after its lone removal.

**An AI agent's key has a seat of its own kind: on the roster, in no count** (CC 4.5.13: an agent "acts under its
own key and has no vote"; "a recall and an election count its persons alone").

What a caller must change to compile:
- `SeatRow::removes_agent` is removed (it was added earlier in this Unreleased section and never released). An
  implementation that defines it deletes it.

New:
- `seat::AGENT` (`"agent"`): the scope of an agent's seat over a room. The reference's law names it a roster
  seat (`SeatLaw::roster_seats` is `["member", "agent"]` in the fixtures' law): a seat the room's persons place,
  not the duty holders.
- `Seats::roster(o)`: the room's whole roster, the keys holding `member` and the keys holding `agent`. Content,
  wraps and audience read it. `Seats::holders("member", o)` holds no agent.
- `seat::persons(m, agents)`: `m` less the agents' keys, public so that a caller counting over its own roster
  does the same.

Answers that change:
- `seat::count_members`, and through it `seat_rule`, `group_count`'s contract and `Seats::tips_fold`'s count:
  the members a count is taken of are the keys of the counted scope at the heads less the keys holding `agent`
  there. An agent's key is no voice and is not counted over in any count of the room (an admission, a removal,
  a duty conferral or withdrawal), whatever other seat it holds. A key in `member` is counted as before. A
  caller of `group_count` subtracts the agents itself.
- A duty seat conferred alone (`Conf::Own` or `Conf::Seat`) stands only if its signer is the one duty holder
  who is a person: an agent holding a duty is no holder that rule reads.
- `window::rule` and `window::outcome`: `Base::All` and `Base::Others` are the counted scope less the agents at
  the opener's head. The window's context no longer carries the keys an opener removes: the key a lone removal
  removes is an agent's and so in no count.
- A moderator's lone removal (above, CC 4.5.13) is a counted unseat of one key's `agent` seat; the seat's scope
  says the key is an agent's. Its lift's re-seating row is an offer of scope `agent`, and the "restores" test
  reads that scope at the head.
- The duty-seat rule asks for the roster's seat: for an agent that is its `agent` seat. An agent's withdrawal of
  its `agent` seat is an end of its stay (it ends the duty seats in its past), and a counted unseat of that seat
  ends them as a removal of a member's does. At tips the duty seat of an agent follows the folded `agent` seat.
- `content` reads no seat row, and is unchanged: the caller's `SeatAt` marks for an agent's rows come from its
  `agent` seat, and a host reads the audience from `Seats::roster`.

The reference: `seat.AGENT`, `Seats.roster`, `seat.counted_keys` and `agents_at` in `seat.py`; `window._base`
reads `counted_keys`. `check_agent_seat.py` is new: 28 cases in arrival orders and seven planted breaks (an
agent a voice; an agent counted over; a lone removal that reaches a person's seat; one that reaches a key with
no agent's seat; a roster cut of a scope the key does not hold; a withdrawal naming a roster scope its target
does not give; a window scope that keeps its agents). In `check_agent_removal.py`
every agent's key is admitted in scope `agent` and its removal is of that scope, and the case table reads
`Seats.roster`. One answer changed there: after the lift, an admission signed by one person and the agent (of
two persons) was counted over the agent and concluded, two voices of three; the agent is no voice and is not
counted over, so it is one of two and concludes nothing. A case beside it, the same admission signed by both
persons, concludes. The plants `seated_voice` and `removed_counted_over` of that file are the plants
`agent_voice` and `agent_counted_over` of `seat.py` now, since the rule they broke is the agent's being in no
count. In the crate the plants on the removed-key code are replaced by plants on the agents' subtraction (in a
count and in a window), on the lone-holder rule and on the roster; the fixture's seat answers carry the roster.

**A duty seat stands only on a member** (CC 4.5.4, "a non-member holds no duty"). Answers change; no signature
does, and one function is added (`seat::stay_ended_in_past`).

Reached: a community whose founding row is of scope `duty`, and there a seat that makes its holder a duty
holder (`duty`, a duty the law names, a duty the founding row declares). Not reached: any other community (now
reached: see "The duty-seat rule reaches every room" above); a seat the duty holders place that is no duty (a
node's detector seat); a count over a scope that is no duty.

- `seat::Seats::recs`, `stands`, `holders`, `holders_at`, `stands_at`, `one`, and through them
  `seat::members_at`, `members_in`, `count_members` and `seat_rule`: a duty seat conferred on a key that holds
  no roster seat over the community (a `member` seat, or the founding seat where it holds `member`) is not
  live. Before, `duty_confer` on a non-member seated it. When the key's widening lands the seat is live with no
  further row. Such a key is no duty holder, so it is not counted in, and is no voice of, a duty count.
- A holder's own withdrawal of a seat that holds `member` over the community (its member seat, its acceptance of
  one, or the founding row) ends the duty seats whose offers are in that withdrawal's past. Before, a member
  had to withdraw each offer. A counted removal from the roster ended them already and still does.
- Nothing revives: a later admission of the key does not make live a duty offer so ended. A conferral that is
  not in the end's past (made after it, or concurrent with it) is not ended by it: it waits for the next
  admission like any conferral on a non-member.
- At several tips a duty seat is live only where the folded roster (`tips_fold("member", ..)`) seats its
  holder.
- `seat::count_members` (and so `seat_rule`): a count over duty holders also leaves out a holder whose own end
  of its stay as a member is in the counted row's past with no admission of it after (`stay_ended_in_past`,
  new and public). A caller of `group_count` that subtracts `left_in_past` itself subtracts this too for a
  count over duty holders.
- A founding holder whose duty the others withdraw is no member afterwards (its membership was its founding
  seat, as before), so conferring its duty again now takes its admission first.

The reference: `models/causal_kernel/seat.py`, with `check_duty_seats.py` (37 hand-written cases, every arrival
order, five planted breaks). The cases are in the `seat` fixture with the standing each asks for, the cases of
persist's table (`HOLDS.duty = ("member",)`) under that table. Nine plants in `tools/kernel_crate_plants.sh`.
The worlds of `attacks.py`, `window.py` and `check_rosters.py` that conferred a duty on a key that was no
member now admit that key first, so the moderator of the two moderation windows is one of four members. With
the members' check counted over the members less the act's author (below), the overturn world's original answers
stand: two objections of the three other members lift, and the moderator's own objection is no voice. With the
duty holder a member, the overturn world no longer told the opener's scope from the counted one, so it gains a
case: a member who holds no duty opens the check, and nothing is opened. The fallback rows of four members that
conferred `moderate` on a key off the roster now admit it first; one keeps it off the roster to show that its
vote is no vote. `check_agent_removal.py` gains two cases in a community founded with scope `duty`: a moderator
conferred on a non-member removes nothing, and the same key admitted first removes an agent's key alone. Its
world A, founded with scope `member`, was not reached by this rule then; it is now, and its moderator is a member.

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
- A counted unseat (`Conf::Group`) of one key's `agent` seat concludes on its signer's one voice where that
  signer holds `moderate` over the object at the head the row names, whatever the room's protocol and however
  many holders. An unseat of a person's seat, or one signed by a key that is no moderator there, is counted as
  any removal is and fails where it failed. (This entry first keyed the removal on a mark the caller set,
  `SeatRow::removes_agent`; the mark is removed before release, and the seat's scope says it: see "An AI
  agent's key" above.)
- That removal is the opener of a `moderation_overturn` window: the caller presents it with
  `win_kind() == Some(WinKind::Open)` and `window()` naming the table.
- `Policy::Lift` and `seat::lift_voices`: the lift's effect is a counted row. An offer of this policy that seats
  the key again, cites the removal (`SeatRow::content`), names the head the removal names and names objections,
  each presented as a cosignature whose `of` is the removal. Its voices are those objections' signers and no
  other key; the removal's author is no voice and is not counted over, and neither is the key seated (below).
  It concludes where those voices are more than half of the members at the head the removal names, the
  removal's author apart and the key removed apart, and never fewer than two; and only where the key seated
  held that seat at that head (it restores and does not admit). `lift_voices` returns the author and the
  voices; `GroupCount`'s contract says what `members` and `voices` are under this policy. `Seats::tips_fold`
  reads the same count over the members the fold seats.
- **The removed agent's key is apart from the lift of its own removal, on every path.** Ruled on 2026-11-25
  from the Constitution's sentence that an AI agent "acts under its own key and has no vote": the count is the
  members seated at the head the act names, the act's author apart and the removed key apart, so the count
  with no landing, a landing's own count, the recount and the re-seating row all read it so. A room of the
  moderator, the agent and two persons lifts on both persons (two of two) and not on one. This first rested on
  the mark (`removes_agent`) and a set of removed keys in the window's context; it now follows from the
  agent's seat, which is in no count of the room (see "An AI agent's key" above).
- No reading of the roster reads a window. Until that row is written the window reads `lifted` and the key is
  out. That gap is accepted.

Checked: `models/causal_kernel/check_agent_removal.py` (38 cases in 8,975 arrival orders, eight planted breaks
in the seat rule, five in the window tables), whose rows are in the seat fixture and run the crate's rules; the
adversary table is 81 rows and 71 checks over five windows (recount breaks none, the voiding rule twelve, the
contesting rule two); ten planted breaks in the crate, which CI's plants jobs run. A moderator whose duty ended
after the head the removal names is read by the end rule: see "A moderator's lone removal is in force" above.

Deputy chains in `conferral`, and a new module `standing`.

- `conferral::answers` reads two gates on a deputy's chain, both from the rows' `via` and nothing else. A row
  is a deputy edge exactly when another act's `via` names it, and an edge that itself has a `via` is an
  onward hop. An act whose edge is an onward hop counts only if the edge above that one carries
  sub-delegation: rule `E6.no_sub`. No act counts more than `Standing::deputy_depth` `via` hops from the
  grantee's own edge: rule `E6.depth`. The grantee's own edge needs no sub-delegation, and a deputy still
  ends with the seat (`E6.upstream`). No mark of an edge is read, so no presentation of the onward row passes
  a gate. The onward row itself is its signer's own act one hop higher and counts as that.
- **Source-breaking:** `conferral::Standing` gains the field `deputy_depth: usize`; a struct literal must
  state it. `conferral::DEPUTY_DEPTH` (5) is the text's cap. `conferral::Rule` gains `Depth` and `NoSub`; a
  `match` over it without a wildcard must name them.
- `ConferralRow` gains `sub_delegation()`, defaulting to false: a fact the edge row states. **An answer of
  0.3.0 changes** where a caller already presented a chain two edges deep: an act whose `via` names a row
  that has a `via` itself counted in 0.3.0, and now counts only if the row above carries `sub_delegation()`
  and the chain is within the cap. A chain one edge deep is unchanged at a cap of at least 1.
- `standing::answers`: one row that needs two standings, a root grant and an owner binding (CC 3.1.2.1). The
  act names its bundle version and the owner's acceptance of the grant; the acceptance names its binding; a
  re-binding ends the binding before it. The function runs `conferral::answers` under the grant and under the
  binding and joins the bits, and returns per act the binding and its owner, `counted`, `in_force` and the
  rule under each record (`Answer::Stands`), or why the act counts for nobody (`Answer::Nobody`), or the row to
  fetch (`Answer::Undecided`). It reads the causal past as the rows name it.
- Fixtures: `conferral_end.json` has 42 cases and 93 act answers (seven deputy-chain cases; each case states
  `deputy_depth`, and a row may state `sub_delegation`; rows no longer state `sub`, which marked a deputy
  edge and was read by nothing). `conferral_two.json` has 21 cases, each row states
  the fields a rule reads (`head`, `on`, `owner`), and each case states `reader_acks` and `why`.
  `tests/conferral_two.rs` replays it.
- Checked by cases only. The TLA+ spec has one deputy edge, where neither gate applies; TLC was not run for
  this change.

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
