# Adopting `ciris-kernel` in persist

This note is for the persist refactor onto the kernel. It was written from a read of persist's worktree
`CIRISPersist-wkernel` at `8c011511` (version 61.3.0, branch `fsd/kernel-seams`). Persist anchors below are
`file:line` in that tree under `src/`. Nothing in persist was changed or run. Persist's own design for the seam
is `FSD/KERNEL_SEAMS.md` (§5); this crate is meant to sit under that interface, not to replace it.

The field-by-field map from a signed `ceg-row/2` statement to each row view is [`WIRE_MAP.md`](WIRE_MAP.md).

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
| `owner_of` (`federation/admission.rs:12694`, fails closed on two owners) | `seat::Seats::owner(key)`, the one owner reading (`Seats::one` of scope `owner` with the re-binding rule); `reexpress.owner_of` is the same rule over `ops` | the same answer, read from the held set: two live owners give none |
| `consensus::evaluate`, `eligible`, `counted` (`federation/consensus.rs:213`, `:161`, `:180`) | `seat::members_at` (the members at the head the row names), `seat::voices`, `seat::met`, `ranked::ranked` | the count is over the head the row names, never the roster at receipt |
| `trust_root_valid` (`federation/trust_root.rs:1407`) and `check_federation` (`federation/replication/admission.rs:133`) | `trust_rows::read_licence` (edges, charter and issuer standing from rows; persist supplies no edges), `charter::declared`; `derived::reach` and `means` for a reader | the reader's view filters held rows; nothing is dropped at replication for trust |
| `check_delegation_cycle_admission` (`federation/admission.rs:18517`) | `trust::reaches` (a cycle is visited once) and the seat walk's depth | no edge is refused for closing a cycle |
| `is_roster_key_at` and `check_roster_act_fresh` (`federation/self_roster.rs:321`, `:553`) | `seat::members_at` at the head the act names; `window::rule` and `window::outcome` | standing is read at the named head, not at receipt; the lone eviction lands only under recount |
| `self_roster::execute_due` and `cosign::execute_due` (`federation/self_roster.rs:1408`, `federation/cosign.rs:1199`); `cosign::hold` (`federation/cosign.rs:853`) | `window::outcome` on this node's clock; `seat::voices` for the cosignatures | a lapse is an answer read at `now`, not a sweep that deletes pending rows |
| `held_head_verdict` (`federation/group_supersede_admit.rs:77`), which refuses a fork | `seat::Seats::tips`, `tips_common`; `line::settle`, `line::void` for a reader's own line | two versions of one head are both held and wait as tips |
| `stamp_entitles` and the `withdraws_admission_rule` stamp (`federation/precedence.rs:269`; `federation/types.rs:1702`) | `seat::seat_rule` on a withdrawal, read at every evaluation | the stamp goes |
| `purge_finalize` (`engine.rs:9415`, `federation/steward_purge.rs:2423`) | `head::purge` says which rows may become stubs; `head::View` answers over the stubs | persist keeps the bytes, the deletion and the duties' enforcement; the kernel says what a stub must keep |
| key liveness against `valid_until` (`KeyRecord`, `federation/types.rs:1365`) | `key_end::well_formed`, `conclude_rule`, `live`, `ended`, `counts`, `retained` | every count reads an ended key's row by the end rule, `key_end::counts` (in the past of each of the key's own ends: a self-revocation, before its `revoked_after`, and a rotation; a cited row counts nothing more). `retained` is for storage only and names the rows whose STUB persist keeps for good (every row a count reads); `bytes_retained` the rows whose bytes it keeps (what a live row names, rows of keys not ended, revocations and rotations); the bytes of a counted, settled row of an ended key may drop to its stub, as the purge's. Nothing counts by either |
| every seat count's voices (the key lane against the seat lane) | `cut::CutSpec::key_view`, returning a `key_end::KeyReading` over one `Concluded` of persist's key records, rotations and revocations and the seat rows, in the store's one causal order (`key_end::conclude_rule`; each seat row's `KeyEndRow::instant` its signed instant); `seat::voices_with` reads each voice by `key_end::counts_by`, as do a window's answers (`window`, the table's voices) and an election's ballots (`seat::election`): every lane that counts a voter reads it through the one key view, a lift's objections, a lone removal's single-key receipts and a lone act (a moderator's lone removal) included. Override `KeyEndRow::instant` to give each seat row its signed instant: the default reads a statement's only, and a row stating no instant is judged by its past alone (a revocation's `revoked_after` reaches only rows that state one). When the key-person map (`persons_of`) is merged at the voices step too, the ORDER is the key view first (drop dead keys), then persons (map the living keys to their persons) | **a store with key records MUST supply the key view**, one per reader (`KeyReading { reader, final_ }`: the reader's own line, and the counts final by acknowledgement, `seat::final_by_ack` over the rows as they conclude with no key view), passed in the spec given to `seat::for_reader` and `Seats::for_reader`. A key end is a cut: a row of the key stands for a reader if it is in the end's past, or on the reader's own line from before it held the end, or part of a count final by acknowledgement. A revocation by a key of which any concluded rotation is held is no end; two rotations of one key are a fork (both ends, no successor); an eviction from the person's self roster ends the key AS A KEY OF THAT PERSON, never its liveness (G33): the person map reads it at each count's voices, and a row the key signs as itself is read as any unowned key's. The self roster's count settles a rotation: its counted removal of the rotated-to key citing the rotation VOIDS it (no end; its successor does not stand; the rotated-to key's rows fall by the cut rule), and the old key is no voice of that count; `seat::self_roster_ends` gives the roster's concluded acts for `KeyReading::roster`. Caller duty: present the person's self-roster rows, and each key's rotation record among them (`SeatRow::rotates`). Finality (`seat::final_by_ack(c, law, spec, i, Some((key lane, roster)))`) counts only clean receipts, and a final count protects only voices valid when cast; a `declared` need is never final by acknowledgement. Residual: a person with one key, whose key is stolen, cannot be told from the thief. Caller duty: an honest rotation or revocation names the key's last rows. The cost: a thief's vote a reader took up before holding the end stands for that reader, and one in a final count stands for everyone; the remedy is the members' later count. A newcomer reads the plain cut and the final counts: with none (the default) every voice counts, which is only for a caller with no key lane. `key_end_counts.json` carries the per-(row, key) answers to replay either way |

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
  `unanimous`, `majority`, `quorum:{m}/{n}`, `weighted:{rubric}` for a community), and its
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
  undecided with no trust root read: give the seat rule one (`CutSpec::trust_root`, returning a
  `root::RootReading` over a `root::Root` of the bundles, revocations and the root's lane rows you hold, this node as
  its `Reader`, and each key's identity type from its key record), and `seat::recovery_verdict` judges it.
- The trust root (`root`): present each bundle as a `RootBundle`, its statements' signatures checked; present root
  grants and acceptance edges as rows of the root's lane (`RootGrant`, naming the rows in their own past). When a
  holder's own node signs a bundle, have it also write an acceptance edge to that bundle, so the bundle is in the
  past of whatever the holder signs next: that closes, for an honest holder and at no cost, the residual the kernel
  states: "a holder's statement over a sibling bundle is not ordered against its grant, so it is not read; a grant on one tip is judged by the rows in its own past". It can matter only where that holder's voice is the deciding one of an exact majority, and the
  statement over the sibling and the grant on the one tip are held evidence the other holders can cite when they name
  both tips.
- A holder's halt is a row of the root's lane with `RootGrant::halts()` true, its signer the holder; `Root::halt_in_force`
  says whether it halts for a reader. A halt counts nobody, so it halts wherever its signer is a holder in force,
  a rule-6 double signer included. In every count at a head (a grant resolving there, a rule-3 bundle settling
  it) a double signer at that head has no say, under either key, and at a later head it counts as any holder. The
  residual: "a reader stalled at b0 leaves it by acknowledging a bundle that counts over its own past without the
  double signers, or by re-rooting. So a strict majority that double-signs can stall a reader that saw the bad
  side first, and cannot capture it."
- A settler of a contested head is a bundle at that head naming the contested siblings, with `RootBundle::settles`
  the one that stands, and carrying that sibling's holders, seats, charter and recovery commitments unchanged (it
  states nothing of its own); it is counted over the holders with a say there. Holders a later line removed can halt
  a reader that has not yet settled onto that line.
- Once the node holds a settler that decides a head for its reader, it re-acknowledges the reader's newest held
  line on the sibling that stands (b2 and b3 in the stall world) as its own mechanical act, with no step for the
  person: an acknowledgement settles only over its own past, so the earlier ones made before the settler do not.
  A holder that signs two settlers at one head naming different siblings has no say in settling that head.
- The fork-point residual: "At a fork point the honest line's removals are not yet in force, so the holders it
  removed keep a say there. With one turncoat (a double signer of the bare-majority step), they can force a split
  among those with a say, and hold a reader whose devices saw both sides at the fork point, where it reads them as
  holders and they can halt it. The exit is re-rooting, or one of them signing the honest settler."
- The per-device cost: "The settler's protection is per device, not per person: if one of a person's devices settled
  past a contest while another concurrently acknowledged the other side, the person is stalled at the fork point,
  and a say-majority there (which can include holders the honest line removed, plus one of its own signers turning)
  can decide it the other way, overturning the settled device."
- A community's protocol is a word of the set under which no one voice decides (`seat::community_protocol`): not
  `quorum:1/{n}`, not `founder_only` (a family's; families are not built), not a weighted record one of whose
  weights reaches its threshold. A change of its record states no policy and meets both the protocol in force and
  `default_standing`.
- There is no open admission (Eric cut `open:self_admit` for 1.0): a public room is an ordinary invitation-only
  community anyone may read, and membership comes only by `community_invite`. A record still declaring
  `open:self_admit` names no protocol. A key's own signature on the row that seats it is its acceptance, never a
  voice of the count (CC 2.7.5).
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

**The countersign of a one-seat affiliation** (CC 4.4.3.12; the Constitution's formal/affiliation/Affiliation.lean).
Present:
- the affiliation's record (its founding row, and each counted change of scope `record`) with `SeatRow::official`, the
  designated official's key, and `SeatRow::overseen_by`, the record member `overseen_by` (optional, one group id: the
  body that conferred or oversees it), whose `review` holders may countersign. Each version is a whole record: one
  stating no official names none;
- a countersign as the outside key's own voice on the act's row (the Constitution's G15): a cosigner of the act
  (`SeatRow::cosigners`), not a separate row. The act names, for an overseer's voice, the overseeing body's rows its
  `review` seat stands on (its basis);
- a removal of a member of an affiliation as a counted Unseat of scope `member` under `affiliation_member_action` or
  `cosigned_act`, `counted` `officer`. The deciding seats are the officers: a member whose seat carries `role:
  officer` (`seat::OFFICER`; the founding record lists the first officers in a `duty_holders` entry `officer`, and an
  appointment carrying the role, with the appointee's acceptance, seats one later). Every counted act of an
  affiliation is counted over its officers (`counted` `officer`); with no officer it is dissolved. With one officer
  the removal on the officer's voice alone concludes as a proposal (held) and is in force only with an eligible
  outside voice on its own row (the designated official, or a review holder of `overseen_by`, read in the act's own
  past); an ineligible outside voice refuses it; with two or more officers it decides on two voices at least, the
  member removed apart.
- with one officer, every other counted act of the affiliation but an admission of a member (no role) is a proposal
  the same way: a lone act, an appointment carrying the officer role, any unseat, a change of the record, a
  dissolution, a license seat. Its countersign is a voice on that act's own row; a change of the official is
  countersigned by the official it replaces or an overseer. An onward trust edge on behalf of the affiliation, and its
  own licence, are such acts: present `SeatRow::edge_body()` (the group a `delegates_to` row speaks for, or a
  licence's authority); `trust_rows` walks or honours it only where `seat::countersigned` holds.
- officers are counted by person (`seat::Persons`): another live key of an officer's person on its act is the officer
  itself, never its countersign. The person relation is read in the act's OWN past, as every count reads it: a
  verdict for a presented row is fixed by its past, so a binding of the official as the officer's own device written
  concurrently with the act, or after it, leaves the countersign standing (the unlinked-keys residual).

**A duty holder's lone acts** (CC 4.5.5, CC 3.1.9.2; CHANGELOG). Present each by its family, its parameter as
`family_param()`: a quarantine marker (`quarantine:{state}`) as `SeatKind::Quarantine` (`target_key()` the key, the
state `withhold` or `release`, a release's `target()` the withhold it supersedes, signed by the holder that withheld it), a slashing verdict (`slashing:{outcome}`) as
`SeatKind::Slashing` (`target_key()`, the outcome `proven_rogue` or `not_proven`), a takedown notice
(`takedown_notice:{basis}`, the basis opaque) as `SeatKind::TakedownNotice` (`of()` the content row), each with `obj()` the room, `head()` the newest
counted changes in its past, and the members' `moderation_overturn` window named (its `window()`, and its
`WinKind::Open`); a reconsideration (`reconsideration:{grounds}`) as `SeatKind::Reconsideration` (`cites()` the takedown, `outcome()`
`reversed`, `partial` or `upheld`); the members'
lift of any of them as an Offer of scope `act`, `cites()` the act, under `moderation_overturn`, naming the
objections. Ask `seat::act_in_force` whether one is in force for a reader.

**A seat from a root grant.** Present it as an Offer of `Conf::Root`, `bundle()` the grant's id, `scope()` the
grant's duty, `obj()` the room the grant names, `to()` and `signer()` the key the grant names; and give the seat rule
the trust root this node reads (`CutSpec::trust_root`, a `root::RootReading`). Onward hops under it are ordinary
`Conf::Seat` offers; whether they pass is the charter's (`RootView::sub_delegation`), never the row's `sub` mark.

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

## Re-asking

Every answer persist asks tells a row that waits from one that concludes nothing, and a wait names the row it
waits on. Hold the row, index it under that id, and ask again when a row of that id is held; ask nothing again on
any other arrival.

- **A row offered whose names are not all held** waits in `held::Held` (`Held::waits`); `Held::lacks(id)` gives
  the ids it still lacks, ascending. It is kept and concluded on the admission that keeps the last of them, and
  `Admitted::kept` lists it then. A row kept on another row's arrival (released by it) is held by that arrival,
  so index a wait under every id it lacks and re-ask on each id in `kept`, not only on the row offered.
- **The seat and window rules** over a kept row: `seat::seat_rule_why` and `window::rule_why` give `Ok(true)`,
  `Ok(false)`, or `Err(Wait(x))`. A kept row reads only its concluded ancestors, which no arrival changes (a
  later row is no row's ancestor), so `Ok(false)` is final: do not re-ask it. The one read outside the fold is
  the trust root's, for a stalled infrastructure room's recovery widening: with no trust root read it waits on
  the grant it names (`seat::stalled_recovery_waits`); with one, on the row the `RootReading` does not hold
  (`RootView::waits_on`, `Root::grant_waits`): the grant, the reader's anchor, or a bundle the grant names.
  `seat::seat_rule` and `window::rule` are those answers with a wait read as `false`.
- **The conferral answers** (`conferral::answers`, `standing::answers`, `content::answers`) already give
  `Answer::Undecided(x)`, the same notion.
- **A recovery widening's conclusion is not final while it waits.** A `Held` concludes a row once, when it is
  kept; a recovery widening concluded before its grant arrived concluded nothing there. When the row a
  `seat_rule_why` wait names arrives, conclude that row and its descendants again (a `Held` built afresh over
  the kept rows, or `seat::conclude`), not only the row.
- **A late voice re-presents the row.** A counted row's later voices arrive as further statements on the SAME
  row id, and the store presents that one row again with a longer `cosigners()` (WIRE_MAP's id trap). "`Ok(false)`
  is final" holds for a row as presented: on a new voice, drop the row's cached answer, present it again, and
  conclude it and its descendants again, as for a recovery wait (`check_acts.py`: "a late voice", a count short by
  one of M that concludes once the last voice is presented).
- **A group referenced by id alone** (an acceptance edge to a community, a licence's authority, `overseen_by`, a
  root grant's room token, a listing's group) never picks between two founding rows held under that id (the
  Constitution's ruling). Present a founding record's declared id as `SeatRow::group_id`, and resolve every such
  reference with `seat::group_of(rows, id)` before reading through it: one founding row, its `Obj::Row`; two or
  more, `Rivals` naming them, and the reference concludes nothing (it is no `Wait`: every rival is held, and no
  arrival settles it). A reference that names a row of one chain resolves to that chain (`seat::group_at`). The
  crate resolves no reference by id itself (`trust` walks keys; a root grant's scope is compared as a row
  digest), so this is the caller's duty wherever its wire carries an id instead of a digest.
- **Liveness.** `seat::infra_live(c, law, spec, obj, at)` gives an infrastructure room's `Liveness` at held row
  `at`: `Live`, or `Stalled { active, m }` (fewer than M + 1 active founders, the count the seat rule reads).

`root.json`'s `waits` replays the model's cases (`check_root.py`, WAITS) in several arrival orders each: a row
that waits on X, X arrives and it concludes; and rows that conclude nothing with every row held.
## A window's table from its policy row

`window::spec_from_policy(row, table, active)` builds a `WindowSpec` from one row of the Constitution's
`manifests/governance_policy.json` (`families`), so a store never writes a window's table itself. The caller
decodes the row into `window::PolicyRow` unchanged (the crate reads no JSON; `tests/policy_spec.rs` shows the
decoding), and the table's `min_count` and `window_classes` into `PolicyTable`. `active` is the base `active`:
`Active::WithinK` (at most `base_law.k` members) or `Active::Census(n)`; `None` on a `standing` row. Where a cell
stops the row, the answer is every `PolicyRefusal { cell, why }`; nothing is defaulted but what the text states.
Only a `two_path` row gives a table. `window.py`'s `spec_from_policy` is the same reading;
`models/causal_kernel/check_policy_spec.py` compares it with the reference's own tables.

| Cell | What it gives |
|---|---|
| `kind` | `two_path`: a table. `mirror`: refused, `NoCell` (no cell states its answer or outcome words). `cosigned`, `ranked`, `tally`: refused, `NotAWindow` |
| `counted.count_set` | `counted` and `concluder` (CC 4.5.13: every window of the table closes by one voice of its count); the proposer's scope (CC 3.1.9.2). One token only. An exclusion (`-target`) must match a `less` in `standing_set`, and the reverse |
| `standing_set` | read only for that `less` |
| `enact_rule` | a fraction: `approve`, `MoreAtLeast(num, den, min_count)` over the base, `landed` (the decider: strictly more, never fewer than `min_count`); in `at_once`, or `at_close` where `irreversible` |
| `cancel_rule`, `cancel_over` | a fraction over `base`: `object`, `AtLeast(num, den, min_count)`, at the close. `strict_majority_of_others` over `others`: `object`, `Strict` over `Base::Others`, at once (CC 3.3.6.4). Any other pairing is refused |
| `floor_rule`, `reverse_path` | with `reverse_path`: a fraction gives `approve`, `AtLeast(num, den, min_count)`; `one_of_n` gives `approve`, `One`; both at the close, `landed` |
| `enact`, `cancel`, `floor` | checked against their `_rule`: `null` only with `none`, a fraction only with the same fraction |
| `at_window` | `cancelled` or `refused`: the cancel's outcome, the default, a silent target's and a withdrawal's |
| `irreversible` | no enact at once |
| `counted.target_silent` | `yes` (with `changes_set` `removes`): `silent` is `at_window` |
| `counted.target_voice` | `yes` (with `changes_set` `adds`): `target_votes` |
| `counted.voice` | `person`, or `key` on a `self` corridor |
| `counted.counted_at` | `named` or `act`: the head the opener names |
| `counted.voices` | `objection`: the answers say `approve` and `object` (`objection:assent`, `objection:raised`) |
| any `counted` cell `unstated` | refused, `Unstated` |
| `base` | `standing`: `Base::All`. `active`: `Base::All` under `WithinK`, `Base::Stated(n)` under `Census(n)` |
| `corridor` | the `min_count` key; `self` adds `withdraw`, `One` over `Base::Opener`, `at_window`, at once (CC 3.3.6.4) |
| `window_secs`, `window_class` | `secs`; the class must give the same length; `0` is refused, `NoWindow` |
| `family`, `cc_ref`, `model`, `status`, `note` | carried; no window cell |
| (no cell) | `opener` `None`; `opener_says` `approve` (CC 3.1.9.2); `landed` (CC 3.1.3, `window:{state}`) |

Six rows give a table today: `default_content`, `default_standing`, `default_irreversible`, `community_invite`,
`self_roster_add`, `self_roster_evict`. The three mirror windows the reference runs (`moderation_action`,
`moderation_overturn`, `accord_halt`) are refused, so a store keeps writing those until the table states them.

The crate embeds no table and parses none; the caller decodes. `tables::law_from_tables(acts, families, protocols)`
gives the `SeatLaw` cells the tables state, from the acts table's rows (`ActsRow`, its six columns), the policy rows
and the policy table's `protocols.kinds` (`ProtocolRow`): `policy` (each family's count from its `enact_rule`, the
text's count for `duty_confer`, `duty_withdraw`, `moderation_overturn` and `moderator_recall`, and `P:{kind}` per
protocol), `acts` (every word read by its `from_word`; an unknown word, a second row for one act, scope and kind, or
a policy with no row is refused) and `removal_floor` (`community_remove`'s floor voices). The rest of `SeatLaw`
(duties, holds, confers, ends, final scopes, roster seats, depth, kinds) is the text's and stays the caller's. The
acts table names the window acts (`moderation_fallback`, `halt_confirm`, `poll`), but in this tag nothing reads that
binding for a window unless the caller asks: `window::rule` and `window::outcome` take the opener's `window()` name
through the caller's lookup, as before. `window::rule_bound` and `window::outcome_bound` take the table through the
binding where the law carries one (`law.acts`): the act the opener proposes (`WindowRow::proposes`, an act and its
scope class) over its object's kind gives the policy row (`window::bound_family`; a `fixed` row its one family, and
an opener stating another concludes nothing; a `row` row the policy the opener states), and the caller's
`Families` closure gives that family's table (built with `spec_from_policy`, `active` per room). An opener bound to
no family, or to one that gives no table, concludes nothing. The window name is then not read.

## Points to settle before adoption

- **Persons and voices.** The crate maps keys to persons itself (CIRISConstitution#224: "one voice however many
  live keys sign"). Present each row with its signing key as signer (`kid`, [WIRE_MAP.md](WIRE_MAP.md) G1) and the
  self-roster rows (a person's `identity:occurrence` rows and their evictions; a voice's room keys) among the rows a
  count reads: `seat::Persons` and `seat::persons_of` give one voice and one member per person, and `seat::person_at`
  the person a key is at a row. `seat::person_keys` (key-person lane) gives a person's live keys. An agent's key is
  itself, never its owner's voice. Do not collapse keys in the adapter.
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
ciris-kernel = { git = "https://github.com/CIRISAI/CIRISKernel", tag = "kernel-v0.5.0", version = "0.5" }
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
  A resignation composed after another member's own end names the newest counted change (naming both is the
  safe form): the other end is no head, so naming it alone leaves the newest counted change unnamed, and the
  resignation concludes nothing.
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
  seat is, and only by its own statement and its owner's signature: the agent's key cosigns the conferral (or
  accepts it by its own row), and the one live owner of the agent's key cosigns the conferral or that acceptance,
  the row it signs naming that owner-binding (the owner's `owner` seat over
  the agent's own roster: an Offer of scope `owner` over the key, the key's and the owner's signatures). The seat
  stops when that binding ends (the owner's revocation), and with two owners there is none. It acts alone within that duty. It is still no voice in any count, the duty holders' own included.
- A moderator's lone removal of an agent's key is an Unseat of its `agent` seat, `Conf::Group`, signed by the
  moderator alone, at the head it names. There is no mark to set: the seat's scope says whose key it is. An
  Unseat of a `member` seat so signed is counted as any removal is, and fails where it failed. The re-seating
  row of the lift is an Offer of scope `agent`, citing the removal (`content`) and naming the newest counted
  changes in its own past as its heads (H4, no exemption). It is counted over the persons seated at both the
  removal's head and its own heads, the removal's author apart: a member admitted after the removal is no voice
  of it, one removed or gone since is out of it.
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

**A key's person**, for `seat::person_at`. Present each person's own key roster as a group whose founding row is
signed by its first key in its own scope (`self` for a person, `key` for a voice), its further keys as counted
admissions and evictions of that scope over it (`self_roster_add`, `self_roster_evict`), and a key's own
revocation as an unseat of its `registered` seat by the key. `SeatLaw::kinds` must map those founding scopes to
`self`, or no person is found. Counts read persons: seat a room's member as its person's genesis key (the key that
signed its self roster's founding record), and a device key of that person signs for it. A person is its
identity key: `person_at` answers `Obj::Key` of the genesis key, never one roster row or one key record, so a
genesis key with several key records, or several rosters, is one person. Only key-life rules read a key itself
(its own revocation, its records); who-signed rules read its person. A genesis key its roster evicted is no voice of the person
the room seats under that identity: only the roster's live keys speak for it. An adopter must never treat kid == the identity's
thumbprint as proof that the key speaks for the person; only a live key of the person's self roster does. The key a
self roster evicts is no voice of its eviction, so a roster whose only live key is its genesis key cannot evict it. One
self roster per identity (ruled): a second founding of a self roster by an identity whose roster the row's past holds
concludes nothing. Of an identity's foundings a reader holds, the reader's roster is the founding its LINE takes up, in
the line's order (`seat::takes_up`): of every row the reader signed or cosigned (concluded for everyone or not, each
counting only where the reader's key stands) that is a founding of the identity or has one in its past, the earliest
(none of the others in its past) fix the roster, and a later row over a rival takes up nothing (acknowledging never
un-voids); first rows reaching two foundings are a wait; a rival founding concludes nothing for that reader, and neither does everything built
on it; neither or both taken up is a wait (a fresh reader holding two waits). A thief cannot put its rival on an
honest reader's line. The genesis key keeps its voice on the roster the reader takes up, as any key of that roster
does, until that roster evicts it: no special rule for the first key either way. The restore case (a one-key identity
restores its genesis key onto a fresh install and founds before fetching its roster): the re-founding concludes
nothing for readers on the first roster; the genesis key's voice there is unchanged; a fresh reader holding both
waits. ADOPTER DUTY: a client holding a genesis key and no roster rows FETCHES the identity's roster before it signs
anything, and never founds where one may exist. A reader's line reads the reader's voices exactly as the counts do: the rows it
signed itself (its cosign rows among them) and the seat rows it is a cosigner of that concluded; a claimed cosigner
on a note or any other row the counts do not read, or on a seat row that concluded nothing, is never read. A reader's
client names its own previous row in every row it signs, or two concurrent rows of its own can make it wait (P2).
CALLER DUTY (for every count): `SeatRow::cosigners` lists only verified voices, keys whose own statement over the
row's payload the store has verified (each voice is a further signed statement, the wire map's rule). Read for a reader through `seat::for_reader`. No key re-founds itself, or adds a device, by founding. The only way onto a self
roster is that roster's own add (its count, or its lone path); an evicted genesis key is restored only by the
roster's counted re-admission. A lone addition is weaker than a lone eviction, as the text has it (CC 3.3.6.4: "One
objection of two others does not stop a lone addition... only a strict majority of the others refuses it"): a live
genesis key in a three-key roster adds a key over one objection, a stated cost. The residual, in the
Constitution's words (0.5.0; to the steward after the tag): "a holder of one key of three that adds a key while one other is silent holds half the roster, and no count or lone path removes it". A self roster's lone-path window that lands (its `landed` landing concluded) is the
counted change it proposes, read through the same ends reading: a landed eviction ends the target's seat, a landed
addition seats each proposed key that signed its opener, and the landing is a head a later count over the roster
names. Present a landing's opener and outcome as `SeatRow::landing`, an eviction opener's target as
`SeatRow::evicts`, an addition opener's keys as `SeatRow::adds` (its `to`, one shape: a `target` alone seats nothing). (The community lone paths change seats by their
own rows: a lone removal is the act, and the overturn's re-seating is a counted offer.) In a two-key roster the count cannot evict (the key evicted is no voice of
it), but the lone path can (CC 4.5.13, the `self_roster_evict` window): one key proposes the other's eviction, and after the
window it lands unless the other key, the whole of the other members and a voice there, objects within it; so a
lost or dead device is put out. The residual: an active stolen key that objects blocks its own eviction, and two
live keys can stalemate each other; with three or more keys the majority path breaks it. Where the owner still holds
a copy of the stolen key, that key can also end by its own revocation (an unseat of its `registered` seat signed by
it), at the key-end rule's cost. Ask at a row of the concluded set: the answer reads that row's own past, an eviction
concurrent with the row by rule 4, and no instant.

**A private room.** The signer of every row is the room key that signed; the voice is the person the persons map
gives for the signing key. `to`, cosigners,
members and voices are in one key space; the crate maps keys to persons by the self rosters it is given. Before presenting a row as its
**The keys a row reaches** (persist). Over the concluded set, with no instant: `seat::person_keys(c, law, spec,
person)` gives a person's live keys (named by its genesis key; the inverse of `persons_of`: a key of two persons,
an agent's key and a key that revoked itself are none of its keys, and a person whose genesis key revoked itself
has none), and `seat::nodes_of(c, law, spec, owner)` gives the node keys whose owner is `owner`, the inverse of
the one owner reading `Seats::owner` (the `owner` seat over the node's key, held by the owner's own signature or
acceptance; a withdrawn or revoked binding, two live owners, or the node's own revocation, and it is none; a
re-binding ends the binding before it). Which keys are nodes is the key
records': filter by `identity_type` `node`. The node set = audiences ∘ person_keys ∘ nodes_of: for each key of a
row's audience (`audience::audiences`), its person's live keys, and for each of those the nodes it owns.

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
- The kernel counts voices by person: a voice's room keys are one person through its key roster (the voice's self
  roster, `seat::Persons`), so two admissions of one person under two room keys are one member. The binding's
  checks (that a room key is the voice's, CC 3.1.3.2) stay the door's.

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
- Each owner's acceptance of the grant: `Kind::Acceptance`, signed by that owner, `on()` the owner binding it is
  made under, from its `refs.also.cites` (N7, CC Part 3 "The owner's acceptance"); present every cited row as
  `cites()` where there may be several, and a binding's node as `node()`, filled from the owner binding's CWT
  `sub` (the key owned). A cited binding MUST carry `node()`: one without it is refused (`acceptance_other_binding`),
  never passed. `owner_of`
  checks it: exactly one cited row (two is refused), an owner binding its signer owns, of the grantee's key, live at
  the acceptance (no re-binding of it in its past). A cited binding not held waits, naming it. A re-binding of the
  cited binding later ends the acceptance's standing: it does not follow the owner's newer binding; the owner
  accepts again citing a live one. `owner_of` reads the bindings among the rows it is given: pass the rows of the
  grant's own subject node only (or present each binding's `node()`).
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

**The consent peer set**, for `consent::may_send`, `peer_set` and `replication_set` (Edge's attestation-plane
replication; CC 3.3.7). Edge's replication set is the operator-addressed peers that are in `consent::peer_set` of a
principal of the local node (`consent::replication_set`), and `consent::may_send` gates each row: it moves only under
a `consent:replication:v1` grant in force from the node or its one owner to that peer whose classes cover the row's
class. Present each grant as `Kind::Grant` (`attesting_key_id` the signer, `peer()` the one `subject_key_ids` entry,
`classes()` the `attestation_prefixes` as signed, `at()` its `asserted_at`, `until()` its `valid_until`), each
`withdraws` or `recants` of one as `Kind::Withdrawal` naming it, and
each node's announcement as `Kind::Announcement`, and every other row (the node's own rows the reading is at
among them) as `Kind::Other`; conclude them with `consent::conclude_rule` beside the families' own rules, giving it
the owner of a key over a withdrawal's past (`Seats::owner(key)`, the one owner reading, over that past). A withdrawal by the grant's
signer, its peer, or the signer's owner there ends the grant; any other key's concludes nothing. Pass the key view
(`Some(&key_end::KeyReading { .. })` over the key lane and these rows in one causal order, for the reading node, its
final counts and its self roster): a grant counts only where its signer's signature does by the end rule, so a
thief's grant concurrent with the key's revocation or rotation moves nothing whatever instant it states. `None`
counts every voice, only for a caller with no key lane. `now` is the caller's instant for the term only: nodes agree
on a term's answer only at the same `now`. Pass the owner from `seat::Seats::owner(node)` (the one owner reading: `Seats::one` of scope `owner` with
the re-binding rule of `standing::answers`) read
over the past of the row the answer is at (`None` with none or two). Read at the row being sent, or the node's own
latest row, never at a clock; `now` is the caller's instant for the term only. Not read here: the `cohorts` allow list
of an owner's grant for its own node (CC 6.1.5.3), and whether the class itself is a grammar the namespace admits
(persist's `consent_grammar::covers` also asks the matcher).

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

**Charters, acceptance edges and licences**, for `charter::declared` and `trust_rows::read_licence`. Present rows
only: the crate reads the edges, the charter and the issuer's standing from them, and takes no edge list.
- A community's charter is its record's `licence_classes` (`SeatRow::licence_classes`: (class, legal_weight)
  pairs), on the founding record and on each change of the record (scope `record`). A version is the whole
  record: a change that states none declares none. An affiliation is a community record whose `declared_cohort`
  is `affiliations` (`SeatRow::declared_cohort`).
- An acceptance edge: a `delegates_to` row (`TrustRow::is_delegates_to`) bearing `trust:accepts:v1`, its
  authority `accepts_dst`, `trust_classes` (`None` where absent; a present list is passed as stated, the crate
  refuses an empty, unsorted or repeating one), `trust_depth` (`None` where absent; the crate refuses one outside
  0 to 5), and `on_behalf` where it speaks for a community. A community's edge carries its duty holders'
  signatures as cosigners and names the community's newest counted changes.
- A licence: `licence_authority` and `licence_class`, naming the rows its standing rests on (the license seat's
  offer and acceptance, or the community's record). Its `asserted_at` (`Dated`) is the instant its seat's term is
  read at.
- A license seat: an Offer of scope `license` over the authority; over a key, by that key (`Conf::Own`), and onward
  under it (`Conf::Seat`, `sub` for a chain); over a community, `Conf::Group` counted by its duty holders
  (`counted` `duty`); over an affiliation, by its body under its protocol. Its term is its own `asserted_at` and
  `valid_until` (`Dated`, persist: `expires_at`).
- **The door's checks, a single row's own fields, which the crate does not make:** refuse a license-seat offer
  that states no term (`valid_until`), or a term longer than 365 days from its `asserted_at` (or than the charter's
  `role_term` where it states a shorter one). The crate reads a seat with no term as unbounded, and the cap needs
  instant arithmetic the crate's `Dated::Instant` does not have.
- An acceptance edge's term is its own `asserted_at` and `valid_until`, read at the caller's `now` only. **Caller
  duty: pass `now`** to `read_licence`; with none, no edge is walked. Every edge carries a term (CC 4.4.3.12): the
  door should refuse an edge stating none, and the crate does not walk one. A licence under a term-bearing seat must
  state its `asserted_at`, or it meets no term.
- Body growth: an authority act concurrent with a change of its body the reader holds is counted over the grown
  body, and one behind the reader's own acknowledged line concludes nothing for it. Present every row the reader
  holds: a reader holding none of the body's newer changes is the residual (it cannot know).
- **Named residual (the term).** Within its term a licence's instant is its holder's word, bounded below by the latest
  instant in its own past (`licensure_instant_before_its_past`). So a holder whose term has run can sign a licence
  dated inside the term, as long as nothing later-dated is in its past; the crate cannot tell it from one signed in
  time.
- **Caller duty (the term).** A node honours a licence under a term that has ended by its own clock only where the
  licence is in the past of a row the node already held when the term ended, or of a row by a key in its trust set
  that it held then. A licence first seen after the term's end with no such anchor is not honoured. The node's own
  receipt record decides this; the crate holds no clock and no receipts, so the caller checks it before presenting the
  licence as honoured.
- Every reason `read_licence` gives is a reading: the licence row stays admitted, and its reason
  (`licence_class_not_trusted`, `licensure_delegator_not_authority`, `licensure_authority_locked`,
  `licensure_link_withdrawn`, `licensure_instant_before_its_past`, `lapsed`, `authority_not_reached`) is no refusal at
  the door.
- Cases: `models/causal_kernel/check_charter.py` and `check_trust_rows.py`, in the `charter` and `trust_rows`
  fixtures.
