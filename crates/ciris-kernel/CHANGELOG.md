# Changelog — ciris-kernel

## Unreleased

**The moderator election, read by the seat rule** (CC 4.5.13; CIRISConstitution#218, waits list: "the election
beyond the ballot count").

- The seat rule's ranked arm (`Policy::Ranked`: a counted offer of `moderate` naming its ballots, which concludes
  where the ranked count over them yields its `to`) had no case in either language. `check_election.py` has 19
  hand-written cases (the count, a transfer, ties, the floor in a room of one and of three, a non-member's and an
  agent's ballot, an unnamed ballot, one ballot a person, the winner's consent, the seat on a member) in every
  arrival order, and one row the text does not decide (OPEN: every member a candidate, two with no first choice
  tie for weakest). All are in the `seat` fixture, so `tests/seat.rs` replays them. No answer changes. Four
  planted breaks in each language.
- **A withdrawn ballot is none** (CC 4.5.13: "Disagreeing ballots neither withdrawn are no ballot until a
  withdrawal leaves one"; a ballot's way back is its author's withdrawal). A ballot whose signer's withdrawal of it
  is among the counted row's concluded ancestors is not counted. **An answer changes**: before, a withdrawn ballot
  counted, so a seating over it could conclude (and one with a withdrawn disagreeing ballot could not). A
  withdrawal beside the row, not in its past, is not read; another key's withdrawal of a ballot concludes nothing.
  Four cases; one plant in each language.
- **A ballot ranking a non-member is not counted** (CC 3.1.4 `ballot:moderator`: "A ballot naming ... a non-member
  is kept and not counted"; its guard, each rank a member). A ballot ranking a key that holds no seat of the counted
  scope (`member`) at the heads the row names is not counted, the whole ballot. **An answer changes**: before, a
  ranked key that was no option was passed over and the ballot counted for its next choice. Read so: an agent's key
  (it holds `agent`) is no member, and a member at the head whose leaving is in the row's past still is (an OPEN
  row in `check_election.py`, with its candidate answers). Four cases; one plant in each language.
- **The room elects only where no duty holder is left** (CC 4.5.4 (v): "With no duty holder left the room locks, and
  the members' count seats one"; rule 2: "While another duty holder remains, a vacant seat is conferred under line
  (iv), and the community does not lock"). A ranked row concludes nothing where a key holds a duty seat at the heads
  it names, less a holder whose own leaving is in the row's past (as a count over the duty holders reads them).
  **An answer changes**: before, an election seated a moderator beside a live one. Four cases (a holder present; the
  last holder laying its duty down, or leaving, and an election at a later head; one of two holders laying down);
  one plant in each language. The holders are read by person (CIRISConstitution#241 B3, derived: "only while >= 1
  member holds the live `moderate` duty"): an AI agent's key holding a duty is no holder, and a room whose only
  holder is an agent elects. One case; one plant in each language.
- Not built, each a row of `check_election.py`'s OPEN list with the model's answer now: the text decides two of
  them, and the crate cannot hold them yet. (1) Several seatings: "the one counted over the larger set stands", and
  two over equal sets of different ballots seat nobody until one is counted over their union. The rows carry no
  election id, so the crate cannot tell which seatings belong to one election. While two seatings are two tips,
  neither stands; once a row names both, both stand. The text does not decide the other four: (2) the decline and
  "the next in runoff order" (striking the decliner and counting again, or the order of the first count, give
  different winners in the case); (3) a ballot ranking more than three; (4) a ranked member whose leaving is in the
  row's past; (5) every member a candidate: two members whom no ballot names tie for weakest and seat nobody. Not
  built, and outside these rows: the lock (nobody posts, admits or acts until a moderator is seated) and the
  node's 24 h since it first held the lock.

**One of each** (no public name changes; the fixtures and conformance runs are unchanged).

- `content` reads `conferral`'s three-way `any`, later-head test and stale-head test; its own copies are gone.
- `trust::reaches` and `EdgeIndex::reaches` are one walk over two sources of a key's edges.
- `window`'s thresholds are the seat's two comparisons (CC 4.5.13: strictly more than a fraction, at least a
  fraction), read by `seat::met`, each with a floor in voices and a choice of base. One answer changes in
  principle: `How::AtLeast` over an empty base is never met (before, a floor of zero was met by nobody). No
  case of the reference or the fixtures takes one. The fold's duty arm goes through the seat rule's count.
- `key_end::live` reads `covers_at`.
- `kernel/TEXT.md` was a copy of CC 2.7 at 1.0-rc19 and is a pointer to the Constitution's section.

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
