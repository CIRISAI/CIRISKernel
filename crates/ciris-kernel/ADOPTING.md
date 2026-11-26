# Adopting `ciris-kernel` in persist

This note is for the persist refactor onto the kernel. It was written from a read of persist's worktree
`CIRISPersist-wkernel` at `8c011511` (version 61.3.0, branch `fsd/kernel-seams`). Persist anchors below are
`file:line` in that tree under `src/`. Nothing in persist was changed or run. Persist's own design for the seam
is `FSD/KERNEL_SEAMS.md` (§5); this crate is meant to sit under that interface, not to replace it.

## What persist implements

One trait, [`Row`](src/lib.rs), and for each answer persist asks, the spec trait of that answer.

| Trait | What persist supplies | From |
|---|---|---|
| `Row` | `Id` = `persist_row_hash` (or the `RowId([u8; 32])` of KERNEL_SEAMS §5.2); `Key` = key id; `names()` = every digest the row's signed bytes name; `signer()` = `attesting_key_id` | `Attestation` (`federation/types.rs:1632`): `persist_row_hash` `:1669`, `attesting_key_id` `:1636`; the named digests are `references_attestation_id` (`federation/precedence.rs:71`), `prev_head_digest` and `charter_digest` on a group version (`federation/types.rs:3191`, `:3200`) |
| `seat::SeatRow` | the kind (offer, accept, withdraw, unseat, cosign, ballot, ack), `to`, `scope`, `obj`, `conf`, `under`, `cosigners`, `subjects`, `head`, `policy` | `attestation_type` `:1642`; `subject_key_ids` `:1684`; `additional_scrubs` (verified cosignatures) `:1768`; the body members the family's grammar names |
| `cut::CutSpec` | the slots a row is on and cuts, and what it says | the family tables (`family_model.json`); the slot of a seat is `(seat, key, scope, object)` |
| `window::WindowRow` | the opener's window name, an answer's word, a landing's receipt and its signer's own instant | the window families; the instant is the signed `asserted_at` of one signer, compared only with that signer's own (`:1647`) |
| `key_end::KeyEndRow` | a key record's `valid_from`, `valid_until`, the old key of a rotation and the signatures it carries | `KeyRecord` (`federation/types.rs:1343`): `valid_from` `:1362`, `valid_until` `:1365`, `identity_type` `:1358` (persist maps it to `EndRule`) |
| `head::Entry` | the header a rule reads: kind, head, act, members and count of a roster version, a cut's signatures, a window's length and first-held instant, the duties that pin bytes | the same rows, plus `first_held_instant` (`federation/attestation_admit.rs:98`) for an opener |

`names()` returns a slice, so persist builds a small view per row that owns its named digests. The view is
the "one typed view of a verified, well-formed row" of KERNEL_SEAMS §5.2, with `refs` as `names`.

The tables are data persist passes in: [`SeatLaw`](src/seat.rs) (what a seat holds and may confer, the duties,
the policy counts, the depth) and [`WindowSpec`](src/window.rs) (the clauses, the default, the length). They
come from `governance_policy.json` and the family tables that persist already vendors.

## Which persist decisions map onto which kernel functions

| Persist today | Kernel | What changes |
|---|---|---|
| the door: `plan_put_attestation` (`federation/attestation_admit.rs:654`) and its gates | `layers::kept`, then `layers::conclude` with the family's rule | a row that names an unheld row waits; a check that reads another row becomes a conclusion, never a drop (KERNEL_SEAMS §0) |
| `owner_of` (`federation/admission.rs:12694`, fails closed on two owners) | `seat::Seats::one("owner", key)`; `reexpress.owner_of` is the same rule over `ops` | the same answer, read from the held set: two live owners give none |
| `consensus::evaluate`, `eligible`, `counted` (`federation/consensus.rs:213`, `:161`, `:180`) | `seat::members_at` (the members at the head the row names), `seat::voices`, `seat::met`, `ranked::ranked` | the count is over the head the row names, never the roster at receipt |
| `trust_root_valid` (`federation/trust_root.rs:1407`) and `check_federation` (`federation/replication/admission.rs:133`) | `trust::honours`, `trust::reaches`; `derived::reach` and `means` for a reader | the reader's view filters held rows; nothing is dropped at replication for trust |
| `check_delegation_cycle_admission` (`federation/admission.rs:18517`) | `trust::reaches` (a cycle is visited once) and the seat walk's depth | no edge is refused for closing a cycle |
| `is_roster_key_at` and `check_roster_act_fresh` (`federation/self_roster.rs:321`, `:553`) | `seat::members_at` at the head the act names; `window::rule` and `window::outcome` | standing is read at the named head, not at receipt; the lone eviction lands only under recount |
| `self_roster::execute_due` and `cosign::execute_due` (`federation/self_roster.rs:1408`, `federation/cosign.rs:1199`); `cosign::hold` (`federation/cosign.rs:853`) | `window::outcome` on this node's clock; `seat::voices` for the cosignatures | a lapse is an answer read at `now`, not a sweep that deletes pending rows |
| `held_head_verdict` (`federation/group_supersede_admit.rs:77`), which refuses a fork | `seat::Seats::tips`, `tips_common`; `line::settle`, `line::void` for a reader's own line | two versions of one head are both held and wait as tips |
| `stamp_entitles` and the `withdraws_admission_rule` stamp (`federation/precedence.rs:269`; `federation/types.rs:1702`) | `seat::seat_rule` on a withdrawal, read at every evaluation | the stamp goes |
| `purge_finalize` (`engine.rs:9415`, `federation/steward_purge.rs:2423`) | `head::purge` says which rows may become stubs; `head::View` answers over the stubs | persist keeps the bytes, the deletion and the duties' enforcement; the kernel says what a stub must keep |
| key liveness against `valid_until` (`KeyRecord`, `federation/types.rs:1365`) | `key_end::well_formed`, `conclude_rule`, `live`, `ended`, `retained` | a row of an ended key lapses only when no live row has it in its past |

## What persist would delete, and what it keeps

Delete, once each family's rule runs through the crate: the gates that refuse for what another row says (the
21 breakers of KERNEL_SEAMS §2.2); the `withdraws` stamp; the fork refusal in `held_head_verdict`; the
sweeps that delete pending cosign and self-roster rows; and the hand-rolled roster-at-receipt reads.

Keep, as KERNEL_SEAMS §8 already says: bytes at rest, the codec and `RowId`, hybrid verification and KEM,
replication and quotas, first-held stamping, the effect executor, SQL indexes and paging, schema and
migrations, and the local operational store.

## What the crate does not cover

- **Signature verification.** A row reaches the kernel verified (`verify_federation_tier_ingest`,
  `federation/attestation_admit.rs:1015`). `cosigners()` must list verified signatures only.
- **CBOR and COSE decoding, canonical bytes and hashing.** The kernel takes the digest persist computed
  (`compute_persist_row_hash`, `federation/types.rs:5138`). A checkpoint's digest of folded state is
  persist's to compute and sign; `head::purge` returns only what the checkpoint names.
- **Storage and incremental evaluation.** There is no `HeldSource`, no read set and no answer cache here
  (KERNEL_SEAMS §5.4). Persist calls the crate over the rows an answer reads. `graph::Graph` is quadratic in
  the rows it is built over, so a call over the whole store is the wrong shape.
- **Transport and routing.** `route` (hold, offer, serve, relay, park, discard) is not stated; KERNEL.md 9
  lists placement as table data not yet written.
- **The fold default** (CC 3.5.1), which `precedence_winner` (`federation/precedence.rs:145`) implements for
  one signer's chain. It stays persist's until the expression language is carried.
- **The key plane** (`community_dek.rs:545`, epoch identity) and **private-room bindings**.
- **Effects and drafts** (KERNEL_SEAMS §5.6, §5.7). The crate returns answers, not effects.
- **Classification of a raw row into a family**, and the table loader. The crate takes the tables as values.
- **An agent's owner on its duty seat.** The kernel does not read the owner's statement on an agent's duty seat
  yet (CC 4.5.4, `founding_duty_holder_agent_owner_unsigned`). Until it does, a caller must not present an
  agent's duty seat without the owner's statement having been checked at the door.

## Points to settle before adoption

- **Persons and voices.** The adapter presents each signing key as its person's voice (`PersonsAt::voice`) and
  each seat as its person (`seat_person`), as KERNEL.md 7b requires; with that, the per-person count agrees.
- **Objects that are rows and objects that are keys.** `seat::Obj::from_reference` types an object from the
  form of its reference in the signed object: a `[-16, digest]` row id is a row, an identity reference
  `urn:ietf:params:oauth:ckt:sha-256:…` is a key. Persist's adapter passes the reference as written. Today's
  `attested_key_id` and `references_attestation_id` are bare strings, so this holds from the rc20 wire on.
- **Instants.** `window::WindowRow::T` and `key_end::KeyEndRow::T` are any ordered type with subtraction.
  Persist's `Micros` (`i64`) fits. The crate never compares two signers' instants.

## Side by side with persist's own tests

[`DIFFERENCES.md`](DIFFERENCES.md) settles every class of difference found running the crate beside persist's
own lib suite. Each class ends as a named persist change backed by a cited CC sentence, or as zero. The
final run gives:

| Function | Agree | Persist departs |
|---|---|---|
| `consensus::evaluate` | 394 of 429 | 22 (`custom:`, `reverse_quorum`) |
| `owner_of` | 1,723 of 1,924, of which 3 name the same owner | 199 (a binding the node's key never cosigned) |
| `trust_root_valid`, edge leg | 199 of 199 | 0 |
| `held_head_verdict` | 2 of 8 | 5 (persist refuses a fork; CC 2.7.8 holds it as a tip) |

## How persist would depend on it

Recommended: a git dependency on the kernel repository at a tag, the way persist already takes
`ciris-verify-core` (`Cargo.toml:581`):

```toml
ciris-kernel = { git = "https://github.com/CIRISAI/CIRISKernel", tag = "kernel-v0.4.0", version = "0.4" }
```

`deny.toml` has `[sources] allow-git = []` with `unknown-git = "warn"`, so the repository would be added to
`allow-git`. A path dependency through `[patch]` serves local work across the two trees. crates.io can wait
until the API settles; the crate is `publish = false`.

The crate declares `rust-version = "1.89"`, and CI builds and tests it on that toolchain. Persist pins
1.97.0 (`rust-toolchain.toml`), which is newer. The kernel repository's `deny.toml` holds persist's licence
allow-list, and `cargo deny check` passes under it.

## Presenting rows: what the functions assume

The crate takes rows through traits and judges what it is given. It cannot tell a mis-presented row from a
real one, so an adapter that presents rows the wrong way gets a wrong answer and no error. Each rule below was
found by running a caller's first encoding against the crate on 2026-11-23. Reproduce the cases named before
trusting an adapter.

**A roster lineage, for `seat::members_at` and `seat::Seats`.**
- The founding row: an Offer, `Conf::Own`, whose object is its own id, `to` the members, each a cosigner. A
  synthetic signer is fine if it is not in `to`.
- Every later node (a restating version, a widening, a self-admission, a removal): `Conf::Group`. A later node
  given as `Conf::Own` under a signer with no founding seat seats nobody and is not a tip, with no error.
- A restating version is Offers for the keys it adds and Unseats for the keys it drops. Do not offer again a
  member who carries over: an Unseat ends the offers in its past, so a re-offer after it seats the removed key.
- Each node names the heads it extends in `names` and in `head`.
- Each counted node carries its real voices (signer, cosigners, cosign rows it names), its policy word and its
  threshold. `members_at` does not read them; `Seats::tips_fold` does, for every addition not common to the
  tips, and an addition with no member's voice waits.
- A resignation is a `SeatKind::Withdraw` by the member, targeting the offer that seats it or its own
  acceptance. It is no tip. It takes effect at a head only where some node in that head's past names it; a
  node extending the same head does not have it in its past.
- A founder is whatever scope the caller seats it in. `members_at(.., scope)` answers for the scope asked.
- `SeatRow::regime`: the protocol and policy in force at each counted act, on every counted act.

**A community's founding and its duty seats**, for `seat::Seats` (unreleased; see the CHANGELOG).
- The founding record (CC 4.5.4): one Offer, `Conf::Own`, scope `member`, whose object is its own id, `to` the
  listed members, each a cosigner (the signer one of them), and `SeatRow::duty_holders` the record's
  `duty_holders` map: per duty, the members who hold it. It seats each listed member who signed it in
  `member` and each holder an entry names in that duty, with no count, so one, two or twelve founders are
  presented alike. Do not present the founding as chained counted rows.
- A founding row seats by the signatures on it, with a map or without. A listed member who did not sign it is
  seated in nothing, and a later acceptance does not seat it: the text's terminal reason is
  `membership_founding_member_unsigned` (CC 3.1.3.2), and the key joins by an ordinary admission. A record
  whose map names a duty holder who did not sign it the text refuses at the door
  (`founding_duty_holder_not_signer`, CC 4.5.4). The crate does not refuse rows; handed either, it seats
  nothing for that key.
- A founder lays down one duty by a `SeatKind::Withdraw` of the founding row whose `scope()` is that duty: its
  member seat and its other duties stand. A withdrawal of the founding row with no scope ends every seat the
  row gives the founder (an end of its stay), and so every duty seat conferred on it before.
- A founding row of scope `duty` with no map is read as before: every key it seats is a duty holder, and with
  `SeatLaw::holds["duty"]` containing `member` that seat is its membership, so its withdrawal ends both.
- A duty conferred after the founding is a counted row: an Offer, `Conf::Group`, policy `duty_confer`, counted
  `duty`, over the head it extends. Its holder lays it down by withdrawing that offer.
- A duty seat is live only on a member, in every room, whatever its founding row seats (a room founded with
  members only included). Present the widening that admits a key before, or with, the conferral
  on it: a conferral on a key that is not yet a member seats nobody, with no error, and is live once the
  widening is held.
- A member's resignation (a Withdraw by the member of its member offer or of its own acceptance of it) and a
  counted removal (an Unseat of scope `member`) end its duty seats whose offers are in that row's past. Present
  them as that one row; do not also unseat each duty. After a re-admission present fresh conferrals: the old
  offers stay ended.
- A founder's withdrawal of the founding row naming no seat ends the duty seats conferred on it in that
  withdrawal's past too.
- Cases: `models/causal_kernel/check_duty_seats.py`, all in the `seat` fixture.

**The moderator election**, for the seat rule (unreleased; see the CHANGELOG).
- A ballot (`ballot:moderator`) is a row of `SeatKind::Ballot`, `ranking()` its keys best first (at most
  `seat::ELECTION_RANKS`). Its withdrawal is a `SeatKind::Withdraw` by its signer, `target()` the ballot.
- The acceptance (`ballot:moderator_acceptance`) is one Offer of scope `moderate` over the room, `Conf::Group`,
  `policy()` the table's `moderator_election` row (`Policy::Ranked`), `to()` the winner, `head()` the head
  counted at. The candidates are the roster at that head (`options()` is not read). It names every ballot, withdrawal and decline of its set. The winner
  signs it, or accepts it.
- A decline (`ballot:moderator_decline`) is a row whose `SeatRow::decline()` is true (default false), signed by
  the key declining. The count yields the first in the runoff order (`ranked::runoff`) whose decline the
  acceptance does not name.
- The table's `moderator_recall` row is `Policy::StrictFloor(2, 3, 2)`: more than two thirds, and never fewer than
  two voices. BREAKING for an exhaustive match on `Policy`: `StrictFloor` is a new variant.
- The caller's, not the kernel's: the lock (nobody posts, admits or acts until a moderator is seated: a `may`
  answer the caller carries), the node's 24 h since it first held the lock, and the grace a silent winner has
  (`election_grace_secs`). These are node clocks, and the kernel answers only the rows' half.
- Cases: `models/causal_kernel/check_election.py`, all in the `seat` fixture.

**An AI agent's key**, for `seat::Seats` and the counts (unreleased; see the CHANGELOG).
- Seat an agent's key over the room in scope `agent` (`seat::AGENT`): an Offer, `Conf::Group`, by the room's
  count (`community_invite` or the room's protocol), the agent cosigning its own acceptance. Its signature on
  that row is its consent and no voice. Do not seat it in `member`: a key in `member` is a person, counted.
- `Seats::roster(o)` is the whole roster, members and agents. Wrap keys to it, serve content to it and read an
  audience from it. Every count reads the members (or the scope it names) less the agents: `count_members`,
  `Policy::Lift`'s members, and a window's `Base::All`, `Base::Others` and `Base::Scope` in a counted clause (a
  clause one holder's act resolves, `How::One`, reads an agent holder's act). `Seats::holders("member",
  o)` can hold an agent that holds a duty whose scope holds `member`; for persons apply `seat::persons` with the
  holders of `agent`.
- The kernel does not read the owner's statement on an agent's duty seat yet (CC 4.5.4,
  `founding_duty_holder_agent_owner_unsigned`): the seat rows carry no owner of an agent's key. Until it does, a
  caller must not present an agent's duty seat without the owner's statement having been checked at the door.
- A duty conferred on an agent is a duty seat of its own (a counted `duty_confer` row), live while its `agent`
  seat is. It acts alone within that duty. It is still no voice in any count, the duty holders' own included.
- A moderator's lone removal of an agent's key is an Unseat of its `agent` seat, `Conf::Group`, signed by the
  moderator alone, at the head it names. There is no mark to set: the seat's scope says whose key it is. An
  Unseat of a `member` seat so signed is counted as any removal is, and fails where it failed. The re-seating
  row of the lift is an Offer of scope `agent`.
- That removal is in force only while the moderator's `moderate` standing is, by the end rule: once an end of
  the standing is held (its own withdrawal, a counted removal of it, the holders' counted withdrawal of its
  duty), the removal ends nothing for that reader unless a receipt of it is held, and nothing puts it back: a
  moderator seated again (the same offer accepted again, or a new conferral) signs the removal again. Present a duty holder's
  receipt as a `SeatKind::Ack` row with `of()` the removal and no `room()`, signed by a holder other than the
  moderator. A reader's acknowledgement of a head keeps `room()` and `head()` as before.
- `content::answers` reads no seat row: the caller marks each roster version (`ContentRow::seat`, `SeatAt`)
  for the author. For an agent's rows mark it by its `agent` seat (in `Seats::roster`), as a member's by its
  member seat; its stay begins at the version that admits it in `agent` and ends at its removal or
  resignation. The audience of a room is `Seats::roster`.

**A private room.** The signer of every row is the voice, not the room key that signed. `to`, cosigners,
members and voices are in one key space, and the crate does not collapse keys. Before presenting a row as its
voice's, check that the room key is a live `key` seat of the voice at the head of the voice's roster the row
names (`models/causal_kernel/roomkey.py`, `rule`).

**A delegation chain**, for `Seats::stands`.
- The counted grant: an Offer, `Conf::Group`, counted over the holders, `sub()` true where it carries
  sub-delegation.
- Each onward grant: an Offer, `Conf::Seat` (not `Conf::Own`), `under()` the offer that seats the delegator,
  the same object, a scope the delegator's covers, the delegate's own acceptance, `sub()` where it may be
  passed on again.
- The depth cap is `SeatLaw::depth`. A term is the caller's to check at the door; `stands_at` reads only the
  seating offer's own instants.

**Receipts**, for `conferral::answers`. One wire receipt naming several acts is one row per act named, each
with `of` that act, all under the wire row's own id (`tests/conferral_end.rs`,
`one_receipt_naming_several_acts`).

**Two bindings of one node**, for `standing::answers`: present every binding of the node you hold, a re-binding
with `on()` the binding it ends. Two bindings to different owners that do not name each other leave the node with
no owner (`Nobody::TwoOwners`) until a re-binding of one is in the act's past, also where one is in the other's
past without re-binding it. `Nobody::TwoOwners` is a new variant: an exhaustive `match` adds the arm.

**Withdrawals and live seats.** A withdrawal's `SeatRow::scope()` names the one seat of its target it ends (a
founder laying down a duty); `None` ends every seat the target gives its signer. A scope naming a roster seat
ends the stay only where the target gives the signer that seat. `Live::scope` is the seat's own scope: one
founding record gives one `Live` per seat, with the same `offer`.

**A deputy edge**, for `conferral::answers`. This is the deputy of an exercised standing, not the delegation
chain of `Seats::stands` above.
- The edge is a `Kind::Act` signed by whoever deputizes, naming the head it is at. Nothing marks it: a row is
  an edge exactly when another act's `via` names it. `sub_delegation()` is true on it where the deputy may
  deputize onward.
- The grantee's own edge has no `via`. An onward edge, signed by a deputy, has `via` the edge that deputy is
  under. A deputy's act has `via` its edge.
- The gates are read from `via` alone. An act whose edge has a `via` itself counts only if the row above
  that edge has `sub_delegation()`, however the onward row is presented
  (`conferral_end.json`, `deputy_chain_no_sub`).
- The onward row itself is judged as its signer's own act, one hop higher, and counts there. Do not read its
  `counted` as "this deputation stands": ask about an act under it.
- What the crate cannot check is the `via` itself. An act presented with a `via` nearer the seat than the
  edge it was made under passes: derive `via` from the signed row, never from the caller's own reckoning.
- `Standing::deputy_depth` is the cap, `conferral::DEPUTY_DEPTH` (5) by the text. The depth is the `via` hops
  from a row up to the grantee's own edge. Every edge of the chain must be among the rows; one that is not
  is the row an `Undecided` names.
- In the fixture an edge that may be passed on is `sub_delegation: true`.

**A grant chain**, for `standing::answers`: the rows of one node under one root grant.
- Each bundle version: `Kind::Bundle`. The causal past must have an earlier version in a later one's past.
- Each owner binding: `Kind::Binding`, `owner()` the owner. A re-binding has `on()` the binding it ends. Two
  re-bindings of one binding are refused (`Refused::SeveralEnds`).
- Each owner's acceptance of the grant: `Kind::Acceptance`, signed by that owner, `on()` its binding. One
  signed by another key is nobody's acceptance.
- Each act: `Kind::Act`, `head()` the bundle version it names, `on()` the acceptance it stands on. An act
  with `on()` a binding, or none, counts for nobody.
- The grant's end: `Kind::GrantEnd`, `head()` its bundle version. A receipt: `Kind::Receipt`, `on()` the act.
  The grant's `Standing::role` says who receipts under the grant; under a binding only its owner does.
- Give the real past. An act that reaches a re-binding through any row it names has that end in its past and
  does not count under the binding it ended (`conferral_two.json`,
  `backdated_after_an_act_under_the_new_owner`).
- Not checked here: that the act's signer is the node the binding binds. Present one node's acts.

**A removal in a room's content**, for `content::answers`. Give a member's removal once, as `Kind::End`. A
content row that names it as its head is read as naming a head at which the member is out.

**Windows.** A `WindowSpec` literal states `opener` (`None` unless the opener's signer holds another scope than
the counted one). `window::outcome` answers a met at-once count with no landing row.
