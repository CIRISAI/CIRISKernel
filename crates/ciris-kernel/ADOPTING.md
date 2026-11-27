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
| `seat::SeatRow` | the kind (offer, accept, withdraw, unseat, cosign, ballot, decline, ack), `to`, `scope`, `obj`, `conf`, `under`, `cosigners`, `subjects`, `head`, `policy` | `attestation_type` `:1642`; `subject_key_ids` `:1684`; `additional_scrubs` (verified cosignatures) `:1768`; the body members the family's grammar names |
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
| `trust_root_valid` (`federation/trust_root.rs:1407`) and `check_federation` (`federation/replication/admission.rs:133`) | `trust_rows::read_licence` (edges, charter and issuer standing from rows; persist supplies no edges), `charter::declared`; `derived::reach` and `means` for a reader | the reader's view filters held rows; nothing is dropped at replication for trust |
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
- **A proposal's stated end** (`expires_at`). The kernel reads none: it is a door check on the acceptance row,
  not a window rule.
- **A poll** (CC 4.5.13, CC 6.1.9). A poll is a tally signed by the period's tally member: its rule and its close
  are stated by its own opening row. It is not a window here.

**The act-to-policy binding** (unreleased).
- `SeatLaw::acts` is the Constitution's `governance_policy_acts.tsv` as `ActRule`s, and `SeatLaw::kinds` maps a
  founding row's scope to its object's kind. A law with `acts: None` binds no act to a policy; the binding is
  then the caller's, as before.
- `seat::act_of(law, get, row)` is the act a counted row is, and `seat::policy_for(law, act, scope, kind)` the
  policy rows it may take: ask these rather than keeping a list of your own.
- With `acts: Some(..)`, the seat rule refuses a counted row whose stated policy its act may not take
  (`act_of`, `policy_for`). A fixed act refuses a different stated policy and accepts its own or none; a row's
  choice (`row`) is one of those listed, stated. A protocol row (`cosigned_act`, `community_remove`,
  `wa_adjudication`: `Policy::Protocol`) is counted under the room's protocol in force, over the protocol's body
  (the members; an infrastructure community's founders): a row counting another body concludes nothing.
- You MUST implement `SeatRow::consensus_protocol()` on a community's records. It defaults to `None`, and with
  `None` no room has a protocol: no removal and no admission under the room's protocol concludes in any room.
  Present the founding record with its protocol, a word of the closed set (`seat::RoomProtocol::parse`:
  `unanimous`, `majority`, `quorum:{m}/{n}`, `weighted:{rubric}`, `open:self_admit` for a community), and its
  `cohort_subkind()` (`infrastructure` for an infrastructure community). A quorum's `m` is the word's; a weighted
  protocol's weights and threshold are the declaring record's `weights()` and `need()`. A counted row's `need()`
  is never read under the protocol. Read the protocol with `seat::protocol_of(p, obj)` or `seat::protocol_record`
  (the row's past) rather than from any other row: it gives the newest change of the record there (a counted
  `record` offer carrying `consensus_protocol`, ordered over the concluded rows), or the founding record's. Emit
  the notice `hard_case:community_consensus_protocol_change` for a change.
- An infrastructure community counts M founder voices, the record's M (absolute, at least 2, never lowered), over the
  `founder` seats at the row's heads (`counted()` `founder`; nodes in no base); it is live while its active founders
  number at least M + 1, and stalled its founders admit and remove nothing. Found it in scope `founder`, entrenched,
  its word stating N = the founders it seats and M their strict majority. Add a founder only by a founders' amendment:
  a change of the record naming the key in `to()` with `role()` `founder`, signed by it, restating `quorum:{M}/{N}`
  for the founders after it, counted at the present M. Refuse any other word at your door
  (`federation_community_consensus_protocol_violation`). A stalled room's recovery widening (`SeatRow::bundle()`) is
  undecided: ask `seat::stalled_recovery` and settle it against the trust root's bundle yourself.
- A community's protocol is a word of the set under which no one voice decides (`seat::community_protocol`): not
  `quorum:1/{n}`, not `founder_only` (a family's; families are not built), not a weighted record one of whose
  weights reaches its threshold. A change of its record states no policy and meets both the protocol in force and
  `default_standing`.
- Under `open:self_admit` the room's protocol counts admissions alone (an offer of the member seat): no removal
  concludes (open, with Eric). Where a room's protocol states no rule for an act (`RoomProtocol::states`), the
  `cosigned_act` half of an `&` is no condition: an open room's record changes under `default_standing` alone, with
  `SeatLaw::community_floor` (set it from the policy table's `min_count.community`; 0 sets no floor).
- A family: present its founding record with `group_kind()` `family`, its founders as the `duty_holders` entry
  `founder` (no other entry: a duty map refuses the family), and its `consensus_protocol` (any of the set). Nothing
  signs as the family. Under `founder_only` state `counted()` `founder`; a promotion is an offer of scope `founder`
  the member accepts, a demotion an unseat of `founder`; a one-row admission with the role is an offer of `member`
  carrying `role()` `founder`. Present `protocol_entrenched()` and `dissolves()` where the
  record carries them, and ask `Seats::dissolved` whether a group is gone. No last-founder rule is the kernel's.
- A demotion and a removal are both counted as a removal, and differ in what they end. In a family, an unseat of
  scope `founder` is a DEMOTION: the founder role ends and the member seat stays. An unseat of the member seat is a
  REMOVAL: it ends every seat the key holds in the room, member and founder alike (one end ends every seat in its
  class). In an infrastructure community the founder seat is the founding seat itself (founded in scope
  `founder`), so an unseat of `founder` there is the removal, and the key holds no seat after.
- State `counted()` as the act's own body or not at all: the members for an admission, a removal, the recall, the
  lift, the election and a change of the record; `duty` for the duty holders' acts; `founder` in an infrastructure
  community; the accord's holders; a self roster's own seat. Any other `counted()`, or an `over()` naming another
  object, concludes nothing.
- A weighted record's `weights()` name each key once.
- The edge: two concurrent changes of a room's protocol that disagree leave no protocol in force, so removals wait
  until a change names both tips under the protocol the common members had (CC 2.7.8's wait, from the protocol
  side; an old past is the weak-subjectivity edge).
- A counted row's `regime()`, where you state one, must be the protocol in force in its past, or it concludes
  nothing; the kernel derives the regime it waits on at tips.
- A node's seat (`seat::NODE`) over an infrastructure community is on the roster, no voice and in no base. A
  counted seat of scope `node` there stands on the founders' count alone (no acceptance asked); every other seat
  needs the seated key's own consent. `SeatRow::consent_one` is gone: no flag on a row waives an acceptance.
- `seat::kind_of` gives every founding row a kind: a scope `SeatLaw::kinds` does not name founds a community.
- The store's query: `seat::policy_for(law, act, scope, kind)` gives the policy rows an act may take and whether
  the row chooses. `seat::act_of(law, get, row)` gives a row's act; `seat::kind_of` gives an object's kind.
- The windows' specs (`window::WindowSpec`, chosen by a row's `window()` name) stay the caller's: no act binding
  reads them in this tag.
- The election's seating is the one act read from the policy the row states (`Policy::Ranked`), and of
  `moderate` only.

**The moderator election** (C1 to C5, E1 to E3, F1 to F4; CHANGELOG). Present:
- each ballot as `SeatKind::Ballot`, its `ranking()` best first (up to three), `of()` its election's id row: the
  room's founding row for the first election, then the seating of the one before; naming the end of the last
  holder's seat it votes on;
- RULE: each election row a key signs (ballot, withdrawal, decline, receipt, seating) builds on that key's earlier
  rows of that election: a row that does not is the key saying two things, and the key is out of the election (a
  device restored from an old backup included). The
  fork is per verified signing key: return from `SeatRow::signing_key` the key whose signature the door verified
  (the room key in a private room), never a client-supplied value; return `None` where the signer signed;
- a decline as `SeatKind::Decline`, `of()` its election;
- a holder's lay-down of `moderate` (its withdrawal of its own seat) is a roster change: it names the newest
  heads, as any roster change (H4). A seat ends once: an end (a lay-down, a counted recall, a
  withdrawal of the offer) with an end of the same seat in its past concludes nothing;
- GUIDANCE (not a rule): build every other row a key signs on that key's own tips, so the rule above holds
  whatever later becomes an election row;
- the winner's own seating: an Offer of `moderate`, `Conf::Group`, policy `moderator_election`, signed by the
  winner, `to()` the winner, `of()` its election, naming its whole set: the ballots, the voters' own withdrawals
  of their ballots, the declines, the leavings it reads, and the end or ends of the last holder's seat it reads
  the electorate at. Nothing it does not name is read for the count. No `options()`;
- each member's receipt of the seating as `SeatKind::Ack` with `of()` the seating: a strict majority of the
  electorate, the winner and the departed apart, closes the election. A room re-closes an election an equivocator
  reopened by removing it by count and a receipt after the removal.

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
- Each node names the heads it extends in `names` and in `head`. **How a store presents a count (the heads ruling
  of 2026-11-26):** by its real rows, the founding record and the counted changes over the room. A counted
  row's `head` is exactly the newest counted changes over its own object in its own past (or the founding row
  where there are none), and it names them. A counted change is a `Conf::Group` offer or unseat on the object
  that names a head; a self-admission is none. A row of no object (a synthesised version row), a note, an
  acceptance, a withdrawal or a cosignature naming itself is no head, and a count naming one concludes nothing.
  `over` is not read for a count: a counted row stating another object concludes nothing. A moderator's lone
  removal, a self-admission, a resignation (a withdrawal of a seat over a room) and a lift name the newest
  counted changes too. A reader's line is drawn from every row the reader signed or cosigned over the room, so
  pass `own` for a member reading its own roster. A reader with no row over the room is the stated
  weak-subjectivity edge, and the text already says where such a reader's first acknowledgement comes from (CC
  3.3.4): "A node does not rebuild a group's past from old signatures. The state of a roster is known when a node is
  admitted to it. A node new to the group, or one with no acknowledged head of its own, takes the group's past from
  a current member, who vouches for it under their own signature. That member is one the node already knows, the
  member whose proposal a newcomer accepted or, for a person's further device, a device of theirs already in the
  group." A store serving such a reader passes that member's acknowledged head as the reader's first.
  **A reader's roster** (the ruling of 2026-11-27): build it over the rows as they conclude for that reader:
  `let (rows, void) = seat::for_reader(&c, law, spec, Some(&own)); Seats::for_reader(&rows, law, spec, &own, &void)`;
  for a reader with no row of its own, `let (rows, _) = seat::for_reader(&c, law, spec, None); Seats::new(&rows, law,
  spec, None)` (every reader holds the concurrent founders' amendments it is given: C2). A
  count can stand for its reader and not for a reader with no row (the changes void for the reader leave the
  count's fold): CC 2.7.9, "A reader's own acknowledged head closes older heads for that reader only". Show such a
  count as in force for that reader, and say that a reader with no acknowledgement of its own reads it otherwise.
  The line is sibling-safe: a row at the head of the reader's acknowledged change is no row behind it. The members
  at several heads are the fold of their lines, and a counted change self-forked by all its voices is void for a
  count that has it in its past (S'') where T at its fork point says so: of the members seated at its heads, those
  who signed only the other side outnumber those who signed only its side (a key's own acceptance, or its yes on an
  offer seating it, counts it for neither; a tie, none on either side included, voids neither, so depth decides
  nothing). That is the only automatic effect of a key signing two things outside an election, and it voids a
  change, never a key. A lone holder's window is closed for a reader by any later counted change that reader has
  acknowledged, and for every reader once the lone holder itself signs a later change.
  **Acknowledging never un-voids** (CC 2.7.9: an acknowledgement closes older heads, and nothing reopens them): a
  row the reader signs acknowledges only the changes in its past not already void for its line, so naming a change
  as a head adopts nothing. A client does not build on a change that is void for it: its next row names only the
  honest newest heads and is simply concurrent with the void change. That breaks no rule (it is no self-fork, the
  void change not being the client's row, and H1 does not ask for a change that is not in its past).
  **Founders' lines:** when a reader that held one founders' line later holds the other (two concurrent records'
  versions), what it had read as concluded on the first line is then waiting, like any tip that turns out to have a
  sibling (the regime wait). A store should not treat a founders' act over an infrastructure room as final on the
  strength of one line.
  A reader's roster (`Seats::new`, `Seats::for_reader`) reads S'' over the rows it holds: a change self-forked
  there neither adds nor removes members. The readings of one line inside the kernel do not.
  **The residual, stated:** one residual, in three shapes, each only for a reader with no row of its own: (1) no member
  seated at the fork point signed exactly one chain (a room founded by one key; every founder colluding); (2) a silent
  colluder's packing chain under the same protocol; (3) a newcomer admitted on the fork, which takes its past from its
  admitter (CC 3.3.4). A store serving such a reader gives it the past of the member that admitted it.
  A seat is two consents: an admission the joiner does not sign
  seats it where its own acceptance (a `SeatKind::Accept` by the joiner, `of` the admission) is in the counted
  row's past, even when the acceptance is in no head's past. Present the acceptance as the joiner's own row; a
  cosignature is no acceptance. A counted change is any roster-changing row that concludes under the policy the
  room's record binds to its act: a lone duty holder's conferral (counted, or its own offer) and an election's
  seating are heads too, and a seating names the newest counted changes as its heads like any roster change. A lone
  duty holder with an offer of a duty seat standing confers no other alone until that offer is accepted or
  withdrawn: to seat two new holders at once, present one row naming both.
- Each counted node carries its real voices (signer, cosigners, cosign rows it names), its policy word and its
  threshold. `members_at` does not read them; `Seats::tips_fold` does, for every addition not common to the
  tips, and an addition with no member's voice waits.
- A resignation is a `SeatKind::Withdraw` by the member, targeting the offer that seats it or its own
  acceptance, and naming the newest counted changes. It is no tip and no head. A counted row with it in its own
  past reads it with the heads it names; a row that does not have it in its past does not.
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
- **Breaking (0.5.0):** implement `SeatRow::word(s: &'static str) -> Self::Word`, the crate's way to name the one
  scope it seats itself (`moderate`, for a lone founder). For a `String` word `fn word(s: &'static str) -> String
  { s.into() }`; for a `&'a str` word `fn word(s: &'static str) -> &'a str { s }`.
- A founding record one key signs with no `duty_holders` map seats that key in `member`, `moderate`, and each duty
  its `duties()` declares. Where the record has a map, the map decides. A record's `duties()` never name a roster
  scope: an entry `member` or `agent` is ignored.
- A duty is placed by the founding record, by the duty holders' count, or by an election's acceptance
  (`Policy::Ranked`). The duty holders' count is a counted Offer with `counted()` exactly `duty` (all the duty
  holders, not one duty's), `policy()` `duty_confer`, and `over()` absent or the room it confers in. Any other
  counted offer of a duty scope concludes nothing (CIRISConstitution#241): a members' admission count
  (`community_invite`, `counted()` `member`), a count under another policy, a count over another room. A
  counted unseat of a duty scope is likewise counted over the room (`over()` is read for no count). Where no
  holder is left, present the election.
- Every head a counted row names is a counted change over its own object, or its founding row (see "How a
  store presents a count" above). A count naming another room's row, or any other row, as a head concludes
  nothing.
- A community, for every rule that asks (the duty gate, the duty room, the one-founder room, a lone removal): an
  object that names a held offer whose object is itself. A moderator's lone removal of an agent's key is read
  only over a community; elsewhere present the removal as the room's counted unseat.
- A single key's own offer of a duty (`Conf::Own`, or `Conf::Seat` under its own seat) concludes only where its
  signer is then the lone person duty holder over the room (an agent holding a duty is not counted), with the new
  holder's acceptance, in every community. Where there are two holders or more, present the holders' count.
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
  receipt as a `SeatKind::Ack` row with `of()` the removal and no `room()`, signed by a person duty holder other
  than the moderator; an agent's receipt keeps nothing. A reader's acknowledgement of a head keeps `room()` and `head()` as before. The room's count's
  receipt is the same row with `conf()` `Conf::Group`, `obj()` the removal's room, `head()` (each the removal's
  head or later), and the counting persons as signer and cosigners; it keeps the removal where more than half of
  the room's persons less the remover sign it, never fewer than two (the remover is no voice of it and not
  counted over). That rule is fixed: the row's `policy()` and `need()` are not read. Any other room, an older
  head, or a `counted()` scope other than the persons, and it keeps nothing. A duty holder's receipt
  is void where a counted unseat of a seat that holder holds does not have the receipt in its past. An end of
  the moderator's standing that lifts receipts states `SeatRow::lifts()`: a counted end (a conferrer's
  withdrawal of a duty seat ends nothing, so it lifts nothing); then only the count's receipt keeps. The holder's own end never lifts
  (`lifts_on_own_end`): refuse such a row at the door; handed one, the kernel reads no lift.
- `content::answers` reads no seat row: the caller marks each roster version (`ContentRow::seat`, `SeatAt`)
  for the author. For an agent's rows mark it by its `agent` seat (in `Seats::roster`), as a member's by its
  member seat; its stay begins at the version that admits it in `agent` and ends at its removal or
  resignation. The audience of a room is `Seats::roster`.

**A private room.** The signer of every row is the voice, not the room key that signed. `to`, cosigners,
members and voices are in one key space, and the crate does not collapse keys. Before presenting a row as its
voice's, check that the room key is a live `key` seat of the voice at the head of the voice's roster the row
names (`models/causal_kernel/roomkey.py`, `rule`).
- Give the founding row's `membership` as `SeatRow::private_room` (true for `private`; default false, read
  public). Over a private room the room key's seat is final once its end stands (unreleased; see the CHANGELOG):
  a re-admission of a removed or resigned room key, or its acceptance of the same offer again, concludes nothing:
  the text's refusal is `membership_room_key_ended` (a seating of a room key whose stay in that room has ended),
  the door's to name. Keep `SeatLaw::final_scopes` as the table gives it (`registered`, `member`, `agent`): a store
  whose table lacks `member` and `agent` gets no room-key finality, silently; a store that listed `member` before
  (as an unseat that is final in every room) now gets it in private rooms only. In a private room an ended stay in
  any roster seat (`member`, `agent`, or a scope holding `member`, `founder` included) bars every roster seat of that
  key there: a room key is one presence in one room. A room
  is private or public by its founding row, and no record change moves it (people found a new room): give
  `private_room` from the founding row only.
- An end is the key's end of its stay in a scope, not of a row: one resignation or one counted removal ends every
  seating of the key in that scope in the end's past. A second seat row of a key already seated is a second basis
  for the same seat: one key, one voice.
- In every room, a key's own signature on an offer of a roster seat, or its acceptance of one, that does not have
  its own end of its stay there in its past (concurrent with it, or before it: a standing acceptance given earlier)
  is no voice (`Seats`): present the rows as they are; nothing to mark. Seats are compared by what they hold: the
  founding `duty` seat, `founder` and `member` are one presence. A withdrawal of an offer the key never consented to
  (declining an invitation, an unsigned listed founder withdrawing the founding record) is no end of a stay.
- Over a group (an object that is its own founding row) a member or agent seat is placed or removed only by a
  counted row, the founding record, the key's own end, or (an agent's key) a moderator's lone removal: a
  `Conf::Own` or `Conf::Seat` row of such a seat concludes nothing, offer and unseat alike. A roster seat needs the
  key's own consent: `SeatRow::consent_one` places one only for a node's seat (scope `node`, in `roster_seats`) over
  an infrastructure community (the founding record's `cohort_subkind`; until the binding's batch gives `kind_of`
  that field, the crate takes a group that is no community by its kind), never a founder's seat.
  Present a lone founder's later admissions as counted rows (a room of one grows by its member's proposal and the
  newcomer's acceptance).
- The kernel counts voices as presented. Which keys are one person's is the binding, never a row, so collapsing
  them (two admissions of one person under two room keys both seat) is the caller's until the voice's own key
  roster is built; the cosigners' checks of the binding are the caller's too.

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

**A deputy under two standings**, for `standing::answers`: present the node's edge as its own act with `on()` the
owner's acceptance, and a deputy's act with `via()` its edge and no `on()`; `sub_delegation()` on an edge that
may be passed on. For the deputy's act to stay in force after a re-binding, the old owner receipts the act and
its edge. An act on the acceptance itself (no `via`) must be the grantee's: a deputy's act presented so stands on
nothing (`Nobody::NotTheGrantee`).

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
the counted one). `window::outcome` answers a met at-once count with no landing row. A ballot (an answer a
`How::MoreOfVoted` clause reads; the fallback's `ballot:moderation_action`, `for` or `against`) withdrawn by its
own signer is a seat withdrawal naming it (`SeatKind::Withdraw`, `target()`): `window::unwithdrawn` reads it.
Every window's receipt is a `window:held` row and its landing a `window:landed` row stating the outcome
(CIRISConstitution#221). Those names are entries of the caller's table: the crate reads a row's `WinKind` and
never its family, and checks no family. Where every counted clause is over `Base::Others` (the members' check), the opener's
signer is no concluder (`window::author_apart`). A table for the accord's halt is the holders' confirmation of a
halt, a count (CC 4.2.1.1); the halted node's own fuse, on its own clock with no landing, is the node's and is not
read through `window::outcome`. A clause over
`Base::Stated(n)` (the base `active` above the base law's `k`) takes `n` from the caller: it is the census's
figure (CC 6.1.9), and the kernel does not check it (a stated `n` below the members at the head counts as those members).
`Base::Stated` is a new variant of a public enum: a caller's exhaustive `match` on `window::Base` breaks and needs
an arm for it. `window::author_apart` takes the opener's signer out of the concluders of a table every counted
clause of which is over `others`: such a table is a judgment of its opener's signer (the members' check, where the
act opens its own window). Present an opener whose signer is a proposer, and not the subject, under a table that
counts some clause over another base.
