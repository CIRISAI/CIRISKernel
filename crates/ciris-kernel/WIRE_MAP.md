# The wire map: `ceg-row/2` to the crate's row views

This note maps each field a crate row view reads to the signed wire statement it comes from. A store builds
exactly this map to present rows, and a minter reads it the other way, to turn a neutral case
([`VECTORS.md`](VECTORS.md)) into signed statements.

Sources read:

- The Constitution at `origin/rc23-next` `d5d42bf`: `manifests/signed_object_v2.cddl` (the row and object CDDL, the
  working schema CC 2.6.1.4 names; `ietf/signed_object.cddl` is the frozen schema of the published
  Internet-Draft -04, rebuilt byte for byte, so it lacks what came after, such as a join's `further_prev`), `manifests/family_payloads_v2.cddl`, `manifests/family_model.json`
  (columns `authorship`, `second_signers`, `count`, `names_head`, `standing_act`, `confers`, `body`), and the text
  of CC 2.4.1.1, CC 2.4.1.2, CC 2.6.1.1 to 2.6.1.11, CC 3.1.3.2, CC 3.1.4, CC 4.4.3.12, CC 4.5.4, CC 4.5.13.
- The crate at `release-0.5.0-wip` `11804e1` (root-fold merged), and the row fields the unmerged lanes add:
  `roster-merge` `23b26c1`, `audience` `3a37cd2`, `charter` `48b44ad` (which contains `persist-gaps` `9e791b3`),
  `key-person` `70af5e8`, `room-key-vectors` `d991aa5` (fixture only), `key-end-retained` `44c697c`. The tables
  below are the union.
- The Constitution's readings at `d5d42bf` (family model sha256 `94a6ac96`) of every N and G below. Each is cited **TEXT** (the text says it, or it follows from the
  text), **RULED** (the Constitution's ruling where the text is silent or contradicts itself; the text change it
  names is to follow), or **PROVISIONAL** (ruled for now, the rule not yet in the text).
- The field lists the models and modules already state, checked against the tables below: `models/trust_root/root.py`
  (a bundle's holders, seats, charter, version, family, recovery, and `prev` as `refs.prev` then `refs.further_prev`
  for a join), `models/causal_kernel/key_end.py` (a record; a rotation's `succ_of`, both signatures and `at_old`; a
  revocation's `revoked_after`; a statement), `trust_rows.py` (an edge's `trust:accepts:v1`, destination,
  `trust_classes`, `trust_depth`, `on_behalf`; a licence's authority and class), `audience.rs`'s module doc (family,
  cohort scope, `history_on_join`, named keys), `window.rs` (`window:held`, `window:landed`) and `head::Entry`.
  ADOPTING.md's "Presenting rows" section gives the rules for presenting rows as prose; this note is the map by
  field.

Markers used below:

| Marker | Meaning |
|---|---|
| **D** | Derived by the store from wire members or other held rows; no single member carries it. The rule is stated. |
| **T** | Table data (`governance_policy.tsv`, `governance_policy_acts.tsv`, the window specs), not a row member. |
| **L** | Store-local: the store's own state (first-held instants, purge bookkeeping), never signed. |
| **NO WIRE FAMILY** | The crate reads a fact a signed row should carry, and no family, member or role carries it. Listed, with the Constitution's rulings, in [the findings](#the-no-wire-family-findings-ruled). |
| **[Gn]** | A mapping the text did not state plainly, now cited TEXT, RULED, PROVISIONAL or kernel's choice. Listed in [the guessed mappings](#guessed-mappings). |

## 1. The statement and its three ids

A row is one `COSE_Sign1` statement, or several over one payload (CC 2.6.1.1, 2.6.1.9).

| Wire element | Where | What the crate takes from it |
|---|---|---|
| `alg` | protected label 1 | Nothing. The constant `-70100`, the composite ML-DSA-65 with Ed25519. This is the only signature suite of a row; there is no other suite member on a row. (`suite` in an `mls:leaf_vouch` payload is the MLS ciphersuite, the constant 77, and no crate view reads it.) |
| `cty` | protected label 3 | Nothing. The constant `application/vnd.ciris.row+cbor`. |
| `kid` | protected label 4 | The signing key: a 32-byte RFC 9679 thumbprint. Presented as the key's identity reference (`urn:ietf:params:oauth:ckt:sha-256:` + base64url of the 32 bytes). This is `Row::signer` on every view, the root lane's included [G1]. |
| `iss` | CWT label 1 | The signer's stable identity: its genesis key's identity reference; under a room key, the voice (the identity reference of the voice's first room key). Not `Row::signer` [G1]: it MUST name the person the persons map gives for `kid` (`seat::Persons`, from the self roster), and a statement whose `iss` disagrees is refused at the door. The root lane reads `kid` too (`RootBundle::statements`, `RootGrant::signer`, `RootGrant::signers`): its fold judges the key, and the holder a key speaks for is resolved from the bundle's `holders` and its cited key records [G1]. |
| `sub` | CWT label 2 | What the row is about: an identity reference (a key subject), a group id `group-…`, a lineage name, or other text. Read per family below. |
| `iat` | CWT label 6 | `floor(asserted_at / 1000)`, seconds. A verifier refuses disagreement, so the crate reads the payload's `asserted_at` (ms), never `iat`, except `RootBundle::iat` and `RootBundle::statements`. |
| `nbf`, `exp` | CWT labels 5, 4 | Derived from `valid_from`, `valid_until`. Not read. |
| edition | CWT label -70003 | The constant 2. Not read. |
| `typ` | protected label 16 | `ceg-row/2` for a row; a signed object that is not a row carries `ceg-genesis-bundle/2`, `ceg-revocation-snapshot/2` or `ceg-boot-manifest/2`. |
| row type | protected label -70001 | One of `scores`, `delegates_to`, `supersedes`, `withdraws`, `recants`. Feeds the kind (section 6). |
| family id | protected label -70002 | The family's registry prefix with each `{name}` written `.name` and each `*` written `.`: `membership:.stage`, `key:record`, `trust:.job:.version`. A `withdraws` or `recants` carries its target's family id, no `dimension`, and its target's `sub`. |
| payload | the `bstr .cbor attestation-envelope` | Every member below. |

**The key type.** `Row::Key` (and the `Key` of every view) is a key id. On the wire every party is named by
one spelling, the identity reference: `urn:ietf:params:oauth:ckt:sha-256:` followed by the unpadded base64url
(43 characters) of the key's 32-byte RFC 9679 thumbprint (CC 2.6.1.1). That text is the crate's key id:
`iss`, `author`, a key `sub`, `subject_key_ids`, `member`, `members[].key`, `holders[]`, `serve_nodes[]` and every
role party carry it as written. `kid` (protected label 4) is the same thumbprint as bare bytes: a store turns
it into an identity reference before presenting it. A dimension segment naming a key carries the bare
base64url thumbprint, the reference less its prefix. A store that keeps the 32 bytes as its key id instead does
so for every field alike; the crate compares keys only by equality and order.

**The suite.** The crate holds no suite and verifies nothing: signature verification, the composite algorithm
(`alg` -70100) and its halves are the caller's and Verify's. No view reads `alg`.

**The three ids.** Verify against this before anything else: it is the main trap.

| Id | Input | Names | Where the crate uses it |
|---|---|---|---|
| **row id** | `["CEG-row/2", type, family, sub, author or null, payload bytes]`, SHA-256, `[-16, digest]` | the row: the same for every voice of a counted row, and unchanged when a voice, a receipt or a disclosure is added | `Row::id`, `SeatRow` ids, `ContentRow::id`, `ConferralRow::id`, `StandingRow::id`, `AudienceRow::id`, `head::Entry::id`, every id inside `names()`, every id an accessor returns (`of`, `target`, `head`, `under`, ...) |
| **statement id** | `["CEG-statement-id/2", protected bytes, payload bytes]`, SHA-256 | one voice | Only where the crate takes one crate row per statement: a later cosignature of a root grant presented as its own `RootGrant` row (`RootGrant::cosigns`). Never inside `refs`. |
| **object id** | `["CEG-object/2", typ, author or null, payload bytes]`, SHA-256 | a signed object that is not a row (a genesis bundle, a revocation snapshot): the same for every voice of a counted object | `RootBundle::id`, `RootBundle::prev`, `RootGrant::bundles`, `RootGrant::attached_head`, `StandingRow::head` of an act under a root grant, and any `refs` entry naming a bundle |

A `row-ref` in `refs` is `[2, [-16, digest]]` and names a row id or an object id, never a statement id. A
store keys rows by row id, so the statements of one counted row land on one crate row.

**Counted and authored.** A family is authored or counted by its `authorship` cell in `family_model.json`, arm by
arm on its selector (CC 2.6.1.3). Read the arm from the row, never from a payload member:

- **Authored**: the payload carries `author`, the `iss` of the one who authors it, and the row id reads it. The
  author's statement is the row. A further statement over the same payload is accepted only in a role the
  family's `second_signers` cell names, its `iss` the party that role names: the delegate (`sub`) of a scoped
  `self:delegates_to` or `trust:confers`, the bound node (`sub`) of an owner-binding, the occurrence key
  (`occurrence_key_id`) of an `identity:occurrence`, the predecessor key (the record under `refs.target`) of a key
  rotation, a listed member (`members`) of a `group:roster` version. A voice of a count an authored family counts
  (an owner-binding an affiliation cosigns) is accepted too.
- **Counted**: no `author`; the row id takes null. The row is N statements over one payload, one per voice, all
  with one row id. `refs.head` (and `refs.further_heads`) is inside what every voice signs. The selector `act=group`
  of a family model cell means "several statements over one payload"; `act=own` means one statement by the author.

**What makes a row counted, for the crate.** A crate row is counted (`SeatRow::conf` is `Conf::Group`) when its
wire row is of a counted arm: several statements over one payload, no `author`, counted over the roster or bundle
`refs.head` names. The crate presentation is one crate row per row id:

| Accessor | Counted wire row |
|---|---|
| `Row::id` | the row id |
| `Row::signer` | the `kid` (as an identity reference) of one verified statement, the one with the least statement id bytewise [G2] |
| `SeatRow::cosigners` | the `kid` (as an identity reference) of every other verified statement over the payload, a set |
| `SeatRow::signing_key` | `None`: the signer is already the key that signed |
| `Row::names` | the payload's `refs`, the same for every voice |

When a later voice arrives the store presents the same crate row again with a longer `cosigners()`; its id does
not change. `SeatKind::Cosign` (a separate cosignature row naming its content) has no wire row in this form: a
voice is a further statement, never a row of its own (CC 2.6.1.4, "`cosignatures`, `quorum_signatures`: a further
statement over the same payload, counted; never a payload member"). A store does not present `Cosign` rows.

## 2. Where the scope word, family, sub, signing key and suite come from

| Fact | Wire source |
|---|---|
| family (registry pattern) | label -70002, the family id; respelled as the registry pattern by turning `.name` into `{name}` and `.` into `*` |
| the leaf and version | payload `dimension`: the full scored dimension, leaf and `:vN`, e.g. `membership:widening:v1`. The `{name}` segments of the family pattern take the leaf's segments; the last segment is the version. A row with no `dimension` (`group:roster`, `key:record`, a `withdraws`, a `recants`) has no leaf. |
| family parameter (`quarantine:{state}`, `slashing:{outcome}`, `takedown_notice:{basis}`, `reconsideration:{grounds}`, `licensure:{authority_id}`) | the `dimension` segment at the `{name}` position. A segment naming a key carries the bare thumbprint (the identity reference less its prefix, CC 2.6.1.1). |
| `sub` | CWT label 2 |
| the signer | protected `kid` (label 4), as an identity reference; its person (`iss`, the voice in a private room) is derived by the persons map [G1] |
| the signing key | protected `kid` (label 4) |
| the suite | protected `alg` (label 1), the constant -70100; no row chooses a suite |
| the scope word of a seat | per family (section 7.2, `SeatRow::scope`): `"member"` on a widening or removal, the payload `scope[]` token on a `delegates_to`, `"record"` on a later `group:roster` version, `"registered"` on a `key:record`, `"owner"` on an owner-binding |
| the cohort scope of a row (placement) | payload `cohort_scope`, with `community_id` or `family_id` (each a group id); `addressed` is a row whose signed `for_key_id` names its recipient (TEXT, CC 6.1.9); a row with no `cohort_scope` takes its family's placement rule (placed by another row) [G3] |

## 3. What a row names

`Row::names` is every row id or object id in the payload's `refs`, all roles flattened into one list:

| `refs` member | Shape | Meaning | Crate accessors fed |
|---|---|---|---|
| `head` | one `row-ref` | the roster head a counted row is counted over; the head an act is exercised at; the head an end acts from; a version's predecessor; the bundle a root-lane row is counted over (an object id) | `SeatRow::head`, `ContentRow::head`, `ConferralRow::head`, `StandingRow::head`, `RootGrant::bundles`, `head::Entry::head` |
| `further_heads` | a set | further tips beside `head` | `SeatRow::head` (with `head`), `ContentRow::parents` |
| `prev` | one `row-ref` | the predecessor in a signer's own series; a content row's predecessor; a bundle's predecessor (object id); a landing's held row | `ContentRow::prev`, `RootBundle::prev`, `WindowRow::receipt` |
| `further_prev` | a set | further content predecessors; a bundle join's further predecessors (CC 2.6.1.11 text) | `ContentRow::prev`, `RootBundle::prev` |
| `answers` | one `row-ref` | the proposal or grant a reply answers; the window or proposal an answer answers | `SeatRow::of` (a reply to a grant), window answers |
| `target` | one `row-ref` | the row withdrawn, superseded, recanted, cut or removed; a window step's opener; a rotation's old record | `SeatRow::target`, `ContentRow::retracts`, `Record::succ_of` |
| `trusted_through` | a set of at most 64 | a key revocation's last rows held good; an end's or a keeps row's held-good content tips | `ContentRow::tips` |
| `also.ack` | a set of 1 to 256 | the acts a receipt acknowledges; a snapshot's scope head | `SeatRow::of` on an `Ack`, `ConferralRow::of`, `StandingRow::on` of a receipt |
| `also.cites` | a set | a cited row: a widening's acceptance, a keeps row's end, a landing's counted rows, a bundle's key records and bindings, an eviction's voices' key records | `ContentRow::extends`; the standing acceptance a widening names |
| `also.under` | a set of exactly one | the edge a deputy's edge hangs from; on a node's row in a private room, the in-room owner-binding | `SeatRow::under`, `ConferralRow::via`, `StandingRow::via` |
| `also.stands_on` | a set of exactly one | the acceptance a row under a root grant stands on | `StandingRow::on` of an act |
| `also.voice` | a set of exactly one | the head of the key roster of the voice a room key signs for | the private-room door (`roomkey.py`); a store reads it before presenting the row as its voice's |

Two members name a bundle outside `refs` and still belong in `names()`, because the crate derives a row's causal
past from `names()` alone:

- `trust:accepts` payload `attached_head_digest` (a `hash-digest`, the bundle's object id). `RootGrant::attached_head`.
- None other. An election's id and its counted set are named by `row-ref` (RULED [G12], [G13]): a ballot names its
  election's row (the last seating, or the roster's first version) and a seating cites each ballot, withdrawal and
  decline it counts under `refs.also.cites`. The election id is derived from the row, needing no preimage.

## 4. Objects: rows, keys and groups

`seat::Obj` is `Row(id)` or `Key(k)`; `Obj::from_reference` types a reference by form: `[-16, digest]` is a row, an
identity reference is a key.

| Wire reference | `Obj` |
|---|---|
| a row id in `refs` | `Obj::Row(row id)` |
| an identity reference (`sub`, `member`, `members[].key`, `holders[]`) | `Obj::Key(identity reference)` |
| a group id `group-…` (payload `group`, `community_id`, `family_id`, `on_behalf_of`; a `sub` of a group's row) | the group object is the group id itself, never one chosen first version (TEXT [G4]): two first versions under one id can exist and wait as tips, so a store presents every first version whose `group` is that id, and both are tips. `Obj::from_reference` recognises neither form: a group id is no thumbprint URI and no digest pair. **Crate note:** the crate's community test reads a group as the founding row whose object is itself (`Obj::Row(own id)`); presenting the group id as the object needs that test to read the id. Until it does, a store with one first version presents `Obj::Row(that version's row id)`, which is the same object; with two it presents both and the crate holds them as tips. |
| a lineage name (`family_key_id`, a `sub` naming it) | not an `Obj`: `RootBundle::family` |

**A group's id** is derived, never chosen: `"group-"` + base64url (unpadded) of SHA-256 over
`["CEG-group/2", group_kind, first_members (a set of identity references), founded_at (ms), nonce (32 bytes)]`,
taken from the first version. A case that founds a group gives those inputs; the minter derives the id.

**A self roster** (key-person): its object is the identity, `Obj::Key(identity_key_id)` (TEXT [G5]: the self is its
fedID, CC 3.3.6.4, and a genesis key can hold several `key:record` rows, so no one record is the object). The first
bind names a genesis key's record in `refs.head`; that record is in the roster's past, not its name. **Crate note:**
key-person's `person_at` finds a self roster through `SeatLaw::kinds` over a founding row; reading the roster by its
identity is a change on that lane.

## 5. Instants

Every instant on a row is a POSIX millisecond integer (`ms-time = uint`, no tag, never a float). The crate's
`T` and `Instant` types take them as given (persist's `Micros` is microseconds: multiply by 1000 or keep ms
throughout; never mix).

| Crate | Wire |
|---|---|
| `Dated::asserted_at`, `head::Entry::at`, `WindowRow::at`, `KeyEndRow::statement().0`, `KeyEndRow::instant` | payload `asserted_at` |
| `Dated::valid_until` | payload `valid_until`; where a family states `expires_at` instead (a proposal, a takedown notice), that member |
| `Record::from` | the key record's `asserted_at` |
| `Record::until` | the key record's `valid_until` |
| `Record::at_old` | the old key's statement over the rotation's payload: the same payload, so the same `asserted_at` [G6] |
| `KeyEndRow::revocation().1` | payload `revoked_after`; absent reads as revoke-all (negative infinity) |
| `RootBundle::iat`, `RootBundle::statements[].1` | seconds: the payload's `asserted_at` / 1000 rounded down, and each statement's CWT `iat` |
| `head::Entry::receipt`, a window's first-held instant | **L**: the instant this node first held the row (persist's `first_held_instant`). Not signed and not in any id. |

A first-held instant is the store's, per row and per node. In a vector it is per statement (`first_held_at`);
its absence means held from the start of the case.

## 6. Kinds

The crate's kinds are derived from the row type, the family, the dimension leaf, the arm (authored or counted)
and the shape of `refs`. One wire row can be read by several views; each view's kind is given.

### 6.1 Seat (`SeatKind`), window (`WinKind`), content (`content::Kind`), head (`head::Kind`)

| Wire row | `SeatKind` | `WinKind` | `content::Kind` | `head::Kind` |
|---|---|---|---|---|
| `group:roster`, first version (no `refs`, carries `nonce`) | `Offer`, `Conf::Own`, the founding row | | `Head` | `Seat` |
| `group:roster`, later version (`refs.head` the predecessor) | `Offer`, `Conf::Group`, scope `record` (a change of the record); with two or more heads, `merge()` | | `Head` | `Seat` |
| `membership:proposal:v1` (authored, names the roster head) | `Other` (an invitation; the crate reads none) | | `Other` | `Other` |
| `membership:acceptance:v1` answering a proposal | `Accept`, `of()` `None`: a standing acceptance the widening names [G7] | | `Other` | `Other` |
| `membership:acceptance:v1` answering a grant (`self:delegates_to`, `trust:confers`) | `Accept`, `of()` the grant (`refs.answers`) | | `Other` | `Other` |
| `membership:decline:v1` | `Withdraw` of the row it answers (a decline of an offer the key never consented to) [G8] | | `Other` | `Other` |
| `membership:widening:v1` (counted) | `Offer`, `Conf::Group` | `Open` where its act's table row has a window **T** | `Head` | `Seat` or `Act` |
| `membership:removal:v1` (counted; one statement for a moderator's lone removal) | `Unseat`, `Conf::Group` | `Open` where its table row has a window **T** | `End`, and `Head` | `Seat` or `Act` |
| `membership:resignation:v1` (authored by the member) | `Withdraw` [G9] | | `End` | `Other` |
| `membership:keeps:v1` (counted) | `Other` | | `Tips` | `Act` |
| `self:delegates_to`, `act=own` (one author, the delegate's second statement) | `Offer`, `Conf::Seat` (under a seat) or `Conf::Own` (over the signer's own key) | | `Other` | `Other` |
| `self:delegates_to`, `act=group` (counted): a duty conferral | `Offer`, `Conf::Group` | | `Head` | `Act` |
| `trust:{job}:{version}`, dimension `trust:confers:v1` (counted over a bundle) | the root lane (`RootGrant::is_grant`) | | | |
| `trust:{job}:{version}`, dimension `trust:accepts:v1` (authored) | `TrustRow::is_delegates_to`, `bears()` `trust:accepts:v1`; the root lane's acceptance edge where it carries `attached_head_digest` | | | |
| `ownership:{relation}:{target_kind}:{version}` (an owner-binding) | `Offer`, scope `owner`, over `Obj::Key(sub)`; `standing::Kind::Binding` | | | |
| `withdraws`, one statement by a party to the target (rules 1 to 4 of CC 2.4.1.1) | `Withdraw` | | `Other`; on a content row's target, a retraction (`Content`, `retracts()`) | `Other` |
| `withdraws`, counted (rule 0, or the holders' count) | `Unseat` of the target's seat (`to` the target's `sub`, scope and object the target's) [G10] | | `End` where it ends a member's seat | `Cut` |
| `recants` of a content row | | | `Content`, `retracts()` the target | |
| `supersedes` of a content row (an edit) | | | `Content`, `retracts()` `None` | |
| `act:ack:v1`, one voice | `Ack`, `of()` each act under `refs.also.ack` (one crate row per act named) | | `Other` | `Ack` |
| `act:ack:v1`, counted (a body's receipt, `sub` the body's group id) | `Ack`, `Conf::Group`, `obj()` the body | | `Other` | `Ack` |
| any row the reader signs over a room, naming `refs.head` | `Ack` with `room()` (the reader's acknowledgement) **D** [G11] | | `Ack` | `ReaderAck` |
| `ballot:moderator:v1` | `Ballot` | `Answer` where a ranked window reads it | `Other` | `Answer` |
| `ballot:moderator_acceptance:v1` (the winner's seating) | `Offer`, scope `moderate`, `Conf::Group`, policy `moderator_election` **D** | | `Head` | `Act` |
| an election decline (the winner's own signed row) | `Decline`, `of()` the offer it answers under `refs.answers` (PROVISIONAL [N1]; its family is not yet registered) | | | |
| `ballot:moderation_action` | `Other` | `Answer` (`says` `for` or `against`) | | `Answer` |
| `objection:{state}` (`assent`, `raised`) | `Other` | `Answer`, `says` the state leaf | | `Answer` |
| `window:held:v1` | `Other` | `Receipt` | | `Other` |
| `window:landed:v1` | `Other` | `Landing` | | `Other` |
| `window:refused:v1` | `Other` | `Landing` stating refused [G14] | | `Other` |
| `quarantine:{state}` | `Quarantine` | | | |
| `slashing:{outcome}` | `Slashing` | | | |
| `takedown_notice:{basis}` | `TakedownNotice` | | | |
| `reconsideration:{grounds}` | `Reconsideration` | | | |
| a countersign: an eligible outside key's further statement over the act's own payload (same row id) | `Countersign`, presented as its own row view (the 0.5.0 bridge, [G15]) | | | |
| `key:record` | `Offer`, scope `registered`, over `Obj::Key(the key)`; `agent_registration()` where `identity_type` contains `agent` | | | |
| `key:revocation:v1` by the key itself | `Unseat` of its `registered` seat by the key itself (key-person `key_record_ended`) | | `KeyEnd` where it is one key of the member | |
| `identity:occurrence` | `Offer` of the self roster's key seat (scope `key`, `to` the `occurrence_key_id`) [G5] | | | |
| `identity:occurrence_revocation` (counted for a user self) | `Unseat` of that seat | `Open` (the eviction's window) **T** | `KeyEnd`, `removes()` the `occurrence_key_id` | |
| a content family (`room_content` true: `chat:*` message, reaction, ...) | `Other` | | `Content` | `Other` |
| anything else | `Other` | `None` | `Other` | `Other` |

### 6.2 Conferral (`conferral::Kind`) and standing (`standing::Kind`)

| Wire row | `conferral::Kind` | `standing::Kind` |
|---|---|---|
| a roster version (`group:roster`, a counted widening or removal), a bundle, an owner-binding | `Head` | `Bundle` (a genesis bundle, by object id); `Binding` (an owner-binding) |
| a row signed in exercise of a standing, naming `refs.head` | `Act` | `Act` |
| a `withdraws` of the offer or the acceptance; a `membership:removal` of the holder; a `membership:resignation` | `End` | `GrantEnd`: the counted `withdraws` of a `trust:confers` grant (`refs.target` the grant, `refs.head` the bundle) |
| `act:ack:v1` | `Receipt` | `Receipt` |
| a removal of a key (`membership:removal`, `sub` the key) | `Removal` | `Removal` [G16] |
| the grantee's own `membership:acceptance` again after its own withdrawal | `Accept` | |
| a `membership:acceptance` replying to a grant (its author the owner of the key the grant names) | | `Acceptance` |
| the body's end of the seat of the receipter an offer names (a removal of the `receipter` key) | `ReceipterEnd` **D** | |
| anything else | `Other` | `Other` |

### 6.3 The root lane

| Wire | Crate |
|---|---|
| `ceg-genesis-bundle/2` object | `RootBundle` |
| `trust:confers:v1` (`delegates_to`, counted over the holders of the bundle `refs.head` names) | `RootGrant`, `is_grant()` true |
| `trust:accepts:v1` carrying `attached_head_digest` | `RootGrant`, `is_grant()` false, `attached_head()` |
| a later statement over a grant's payload, presented as its own row | `RootGrant`, `cosigns()` the grant's row id; `Row::id` the statement id |
| `accord:invoke:constitutional:{halt_id}` (one holder's statement) | `RootGrant`, `halts()` true |
| a counted `withdraws` of a grant | `standing::Kind::GrantEnd` |

## 7. Each view, field by field

### 7.1 `Row` and `Dated` (lib.rs)

| Accessor | Wire source | Id |
|---|---|---|
| `Row::id` | computed | row id (statement id for a statement-level root-lane row) |
| `Row::names` | every `row-ref` in payload `refs`, flattened (section 3), plus `attached_head_digest` | row ids and object ids |
| `Row::signer` | `kid`, as an identity reference [G1] | |
| `Dated::asserted_at` | payload `asserted_at` (ms) | |
| `Dated::valid_until` | payload `valid_until`, or `expires_at` where the family states that | |

### 7.2 `seat::SeatRow`

| Accessor | Wire source | Notes |
|---|---|---|
| `seat_kind` | section 6.1 | **D** |
| `word` | none | the crate's own constructor for a scope word |
| `to` | widening, removal: payload `member` (equal to `sub`). `group:roster` first version: `members[].key`. `delegates_to` (`self:delegates_to`, `trust:confers`, owner-binding): `sub`. Election seating: the signer. `key:record`: the key. `identity:occurrence`: `occurrence_key_id`. A counted `withdraws` read as `Unseat`: the target's `to` | identity references |
| `scope` | widening, removal: `"member"`, or `"agent"` where the member's key record's `identity_type` contains `agent` [G17]. `group:roster` first version: `"member"`, or `"founder"` for an infrastructure community (`cohort_subkind` `infrastructure`). Later `group:roster` version: `"record"`. `self:delegates_to`: a token of payload `scope[]` other than `sub_delegation`; a set of several duty tokens is one crate row per token, and those rows share ONE fate: the same row id, so one withdrawal or unseat ends all of them, and they stand together as one seat in a duty count [G18]. Owner-binding: `"owner"`. `key:record`: `"registered"`. Acceptance: the payload `role`, else `"member"`. Withdraw: a lay-down is a `withdraws` targeting the seating conferral (the founding record for a founder's duty), carrying the duty it ends as its scope; absent, the whole stay (RULED [N2]; the payload member's name follows in the text) | |
| `obj` | widening, removal, acceptance, keeps: payload `group`. `self:delegates_to` over a room: payload `community_id` (or `family_id`). Founding version: its own row id. Owner-binding, `key:record`: `Obj::Key(sub)` | a group id resolves to the founding version's row id [G4] |
| `conf` | **D**: `Own` for a founding version and for a row over the signer's own key; `Seat` for an authored `delegates_to` under a seat (`refs.also.under` present, or the signer's own live seat); `Group` for every counted arm | |
| `under` | `refs.also.under`, its one element | row id |
| `cosigners` | the `kid` of every further verified statement over the payload (section 1); on an authored row, the second-consent roles | identity references |
| `subjects` | payload `subject_key_ids` | identity references (or `canonical:{hashalg}:{hex}` text) |
| `sub` | `"sub_delegation"` is a token of the `delegates_to` payload `scope[]` (CC 4.4.3.19) | |
| `head` | `refs.head` then `refs.further_heads`. On a body's counted receipt (`act:ack`, which names no head): **D**, each named act's own head (TEXT [N10]) | row ids |
| `consensus_protocol` | `group:roster` payload `consensus_protocol` | |
| `cohort_subkind` | `group:roster` payload `cohort_subkind` | |
| `group_kind` | `group:roster` payload `group_kind` | |
| `official` | the record's `designated_officials` (role to key), a payload member of the community record beside `consensus_protocol` (RULED [G19]) | a key |
| `overseen_by` | the record's payload member `overseen_by`, one group id, beside `consensus_protocol` (TEXT for the name, RULED for the place [G19]) | group id, resolved to its founding row [G4] |
| `family_param` | the `dimension` segment at the family's `{name}` position | text |
| `outcome` | `reconsideration:{grounds}` payload `outcome` (CC 4.5.5 prose; no CDDL rule); on `slashing:{outcome}`, the `{outcome}` segment | |
| `agent_registration` | `key:record` payload `identity_type` (a set) contains `agent` | |
| `target_key` | `quarantine:{state}`, `slashing:{outcome}`: `sub` | identity reference |
| `protocol_entrenched` | `group:roster` `consensus_protocol_entrenched`; absent reads false on the wire, `None` here only where the version omits it | |
| `admission_quorum_basis` | `group:roster` `cohort_subkind_payload.infrastructure_constraint.admission_quorum_basis` | |
| `dissolves` | `group:roster` carries `dissolved_at` | |
| `bundle` | **D**: the widening carries `refs.also.stands_on` naming the counted grant (RULED [N3]); the bundle is the grant's `refs.head` | the grant's row id, then the bundle's object id |
| `role` | widening `role`; `group:roster` `members[].role` (`founder`) on a founders' amendment | |
| `regime` | **D**: the protocol in force and the act's policy, as one value the store composes | |
| `lifts` | payload `lifts` (present only as `true`) | |
| `policy` | **T**: the act's policy row (`governance_policy_acts.tsv`, `act_of`, `policy_for`); `moderator_election` for a `ballot:moderator_acceptance` seating | |
| `counted` | **T** | |
| `over` | **T** | |
| `need` | **T** for a count; on a record declaring `weighted:{rubric}`, the record's payload member `need` beside `consensus_protocol` (RULED [G20]) | a whole number |
| `of` | `Accept` replying to a grant: `refs.answers`. `Ack`: one element of `refs.also.ack`. `Ballot`: its election's row, by `row-ref` (RULED [G12]). `Decline`: the offer it answers, `refs.answers` (PROVISIONAL [N1]). `Quarantine` release: the withhold it lifts, `refs.also.cites` (RULED [G21]). `TakedownNotice`: the establishing attestation whose content `content_sha256` binds, the copy at the scope the notice's duty is over (TEXT [G22]). `Reconsideration`: the notice it contests, `refs.also.cites`, its ruling in `outcome` (RULED [G23]). `Countersign`: the act's row id (the bridge, [G15]) | row ids |
| `target` | `withdraws` `refs.target` | row id |
| `content` | a lift's citation of the act it lifts (the removal): `refs.also.cites` (TEXT [G24]) | row id |
| `duties` | `group:roster` `policy.duties` | |
| `duty_holders` | `group:roster` `duty_holders` (first version only) | map duty to a set of identity references |
| `weights` | a `weighted:{rubric}` record's payload member `weights` (key to a whole number) beside `consensus_protocol` (RULED [G20]) | |
| `options` | **D**: an election's options are the members of the roster it names (RULED [N4]); a poll's options have no family yet | identity references |
| `ranking` | `ballot:moderator` `ranks`, up to three identity references in order (a sequence) | the family model's body cell for `ranks` is `type: unstated` |
| `signing_key` | `kid`, as an identity reference | |
| `room` | `Ack` read from a reader's row: the group of the head it names **D** | |
| `licence_classes` | the community record's payload member `licence_classes`, each with `legal_weight`, beside `consensus_protocol` (TEXT for the name, RULED for the place [G19]) | |
| `declared_cohort` | the community record's payload member `declared_cohort` beside `consensus_protocol` (TEXT for the name, RULED for the place [G19]) | |
| `private_room` | founding `group:roster` `membership` is `private` | |
| `merge` (roster-merge) | a later `group:roster` version naming two or more tips (`refs.head` and `refs.further_heads`) | |
| `merge_members` (roster-merge) | that version's `members[].key` | |
| `merge_duties` (roster-merge) | none: a merge carries no duty seats; they are the fold of the conferral, withdrawal, resignation and election rows over the folded roster (RULED [N5]). The accessor is to be removed | |

### 7.3 `window::WindowRow`

| Accessor | Wire source | Notes |
|---|---|---|
| `win_kind` | section 6.1 | **D** |
| `window` | **T**: the window name of the opener's act's table row | |
| `target_key` | the opener's `sub`, where it is a key | identity reference |
| `says` | an answer: the `objection:{state}` leaf (`assent`, `raised`) or the ballot's word (`for`, `against`). A landing's outcome: **D** from the leaf: `window:landed` states the change lands, `window:refused` every other outcome the table gives at the window; a tally's direction is recomputed from the rows the landing cites (RULED [N6]) | |
| `receipt` | a landing's `refs.prev` (its signer's `window:held` row) | row id |
| `at` | payload `asserted_at` | ms |

A window row's opener is `refs.target` on `window:held` and `window:landed`; a landing's counted rows are
`refs.also.cites`. Both are in `names()`.

### 7.4 `trust_rows::TrustRow` (charter)

| Accessor | Wire source | Notes |
|---|---|---|
| `is_delegates_to` | row type `delegates_to` | |
| `bears` | payload `dimension` (`trust:accepts:v1` for an acceptance edge) | |
| `accepts_dst` | `trust:accepts` `sub`: an identity reference (`Obj::Key`) or a group id (`Obj::Row` of its founding version) | |
| `on_behalf` | payload `on_behalf_of` (a group id) | |
| `trust_classes` | payload `trust_classes` (a set; absent is `None`) | |
| `trust_depth` | payload `trust_depth` (0 to 5; absent is `None`) | |
| `licence_authority` | the `{authority_id}` segment of `licensure:{authority_id}` (a bare thumbprint, or a group id) | |
| `licence_class` | payload `class` (CC 2.4.1.1, "The row carries `class`") | |

### 7.5 `key_end::KeyEndRow`, `key_end::Record`, `key_end::KeyView` (key-end-retained)

Every row this view reads has `Row::signer` the signing key (`kid`), as every view does [G1]: a key ends, not a
person [G25].

| Accessor | Wire source | Notes |
|---|---|---|
| `record().key` | `key:record` `sub` (the key's identity reference; the `key` member is the composite key whose thumbprint it is) | |
| `record().from` | `asserted_at` | ms |
| `record().until` | `valid_until` | ms |
| `record().succ_of` | a rotation: the key of the record under `refs.target` (the predecessor key, `second_signers` `predecessor_key`) | |
| `record().at_old` | the old key's statement over the rotation's payload [G6] | ms |
| `record().sigs` | the `kid` of every verified statement over the record's payload | |
| `record().end` | **D** from `identity_type` (a set): contains `user` or `accord_holder`: must not state an end; contains `node` or `agent`: must, unless the record carries `room`; otherwise: may | |
| `statement()` | `(asserted_at, the record that covers it)`; the cover is **D**: the key record of the statement's `kid` whose `asserted_at`..`valid_until` covers its `asserted_at`. No row names its cover [G26] | |
| `revocation()` | `key:revocation:v1`: (`sub`, `revoked_after`) | |
| `instant()` | payload `asserted_at` of any row, seat rows included | |
| `roster_end()` (key-end-retained) | a concluded eviction of the key by the person's self roster, under that roster's own count rule (`identity:occurrence_revocation`); never a row the successor signs. It ends the key AS A KEY OF THAT PERSON: no voice or standing of the person, and persons(`kid`) no longer gives that person, so a statement with `iss` that person and `kid` the evicted key is a door refusal. It does not end the key's liveness (only its own revocation does). `effective_at` and `revoked_at` are documentary, read by no rule (RULED [G33]) | |
| `cosigned_by()` (key-end-retained) | the `kid` of every further verified statement over the row's payload (as `SeatRow::cosigners`) | |
| `KeyView::counts` | **D** | |

### 7.6 `content::ContentRow` (audience adds `parents`, `room`, `removes`, `concludes`)

| Accessor | Wire source | Notes |
|---|---|---|
| `id`, `signer` | row id, `kid` [G1] | |
| `kind` | section 6.1 | **D** |
| `head` | `refs.head` | row id |
| `prev` | `refs.prev` then `refs.further_prev` | row ids of the author's own content rows in the same room |
| `tips` | `refs.trusted_through` (at most 64) | row ids |
| `retracts` | the `refs.target` of a `withdraws` or `recants` of a content row | row id |
| `extends` | a `membership:keeps` row's one end under `refs.also.cites` | row id |
| `seat` | **D**: what the roster version is to the member (`SeatAt`), from the version's `members` or the change's `member` | |
| `parents` | a roster version's `refs.head` and `refs.further_heads` | row ids |
| `room` | payload `community_id` or `family_id`, or a change's `group` [G4] | founding row id |
| `removes` | `identity:occurrence_revocation` `occurrence_key_id` (equal to `sub`) | |
| `concludes` | **D**: whether the eviction met the self roster's count | |

### 7.7 `audience::AudienceRow` (audience)

| Accessor | Wire source | Notes |
|---|---|---|
| `id`, `signer`, `names` | row id, `kid` [G1], `refs` | |
| `family` | label -70002, the family id, respelled as its registry pattern, for every row (TEXT [G27]) | |
| `scope` | payload `cohort_scope`; `addressed` where the row carries a signed `for_key_id` (TEXT [G3]); a row of a family placed by another row takes that row's placement | |
| `room` | payload `community_id` or `family_id` [G4] | founding row id |
| `named` | `sub` (the attested key), `subject_key_ids`, `for_key_id` | identity references |
| `seat_act`, `obj`, `to` | as `SeatRow` (section 7.2) on a widening (`Offer`) or removal (`Unseat`) | |
| `concluded` | **D** | |
| `history_on_join` | payload `history_on_join` (`full`, `from_join`) | |
| `follows` (audience) | the row a following family names, by that family's existing role: `custody:{kind}` its content, `stream:head` its stream; else under `refs.also.cites`: `ownership` the owner-binding it mirrors, `duty:{kind}` the permission it attaches to. A row with no such reference is `follows_not_named` (RULED [G34]) | row id |

### 7.8 `conferral::ConferralRow`

| Accessor | Wire source | Notes |
|---|---|---|
| `id`, `signer` | row id, `kid` [G1] | one crate row per act an `act:ack` names, each under the wire row's own id (ADOPTING, Receipts) |
| `kind` | section 6.2 | **D** |
| `head` | `refs.head` | row id |
| `of` | one element of `refs.also.ack` | row id |
| `target` | the removal's `sub` (`member`) | identity reference |
| `via` | `refs.also.under` | row id of the edge |
| `sub_delegation` | `"sub_delegation"` among the edge's `scope[]` tokens | |
| `lifts` | payload `lifts` | |

The offer's `receipter` (payload, an identity reference) names who receipts under it; it feeds `Standing::role`
and the `ReceipterEnd` kind, not a row accessor.

### 7.9 `standing::StandingRow`

| Accessor | Wire source | Notes |
|---|---|---|
| `id`, `signer` | row id (object id for a bundle), `kid` [G1] | |
| `kind` | section 6.2 | **D** |
| `head` | an act's `refs.head` (the bundle in force, an object id); a grant end's `refs.head` | object id |
| `on` | an act: `refs.also.stands_on`. A receipt: its act under `refs.also.ack`. An acceptance: none on the wire: it stands while its author is `owner_of` the key the grant names (RULED [N7]); **D**: the owner-binding of that owner the store holds (where an owner re-signed at several scopes, any of them: they are one binding to `owner_of`). A re-binding: the binding it ends, `refs.target` (TEXT [G28]) | |
| `owner` | an owner-binding's `author` | identity reference |
| `target` | the removal's `sub` | |
| `lifts` | payload `lifts` | |
| `via` | `refs.also.under` | |
| `sub_delegation` | `"sub_delegation"` among the edge's `scope[]` tokens | |

### 7.10 `root::RootBundle`

| Accessor | Wire source | Notes |
|---|---|---|
| `id` | object id | |
| `family` | payload `family_key_id` (text) | |
| `version` | payload `version` | |
| `prev` | `refs.prev`, then `refs.further_prev` on a join | object ids. `genesis-refs` carries `further_prev` beside `prev` (`manifests/signed_object_v2.cddl`; CC 2.6.1.11) |
| `holders` | payload `holders` (a set) | identity references |
| `seats` | payload `serve_nodes` (a set) | identity references |
| `charter` | payload `charter`, compared whole (its deterministic encoding) | |
| `duties` | `charter.scope` (a set of tokens) | |
| `sub_delegation` | `"sub_delegation"` in `charter.scope` (CC 3.2: "the charter of the bundle the grant names carries `sub_delegation`"); the wire states it once for the charter, never per duty [G29] | |
| `names` | a settler's other contested siblings, under `refs.also.cites` (PROVISIONAL [N8]) | object ids |
| `recovery` | `charter.recovery_commitments`: holder to the commitment `[-16, SHA-256(["CEG-recovery/2", [key]])]`, not the key [G30] | |
| `settles` | the sibling that stands, under `refs.target` (PROVISIONAL [N9]) | object id |
| `recovers` | a recovery bundle (one statement, `iss` the holder, `kid` the recovery key): (the holder, by its identity reference `iss`; the key of the holder's new signing-key record under `refs.also.cites`) [G31] | |
| `iat` | `floor(asserted_at / 1000)` | seconds |
| `statements` | each verified statement: (`kid` as an identity reference, its CWT `iat`). The holder it speaks for is resolved from `holders` and the key records under `refs.also.cites`: a holder's current key in the bundle in force, its first key being its identity's genesis key, a later one named by a recovery (`recovers`). A voice under a key a recovery retired is no voice; a holder is one voice across its keys [G1] | |

### 7.11 `root::RootGrant`

| Accessor | Wire source | Notes |
|---|---|---|
| `id`, `names`, `signer` | row id (statement id for a `cosigns` row), `refs` plus `attached_head_digest`, `kid` [G1] | |
| `is_grant` | family `trust:.job:.version`, dimension `trust:confers:v1`, row type `delegates_to` | |
| `attached_head` | `trust:accepts` `attached_head_digest` | object id |
| `cosigns` | the grant's row id, on a later statement over its payload | |
| `halts` | family `accord:invoke:constitutional:.halt_id` | |
| `bundles` | `refs.head` and `refs.further_heads` | object ids |
| `to` | `sub` | identity reference |
| `scope` | the room the grant seats in: a token of the grant's payload `scope` naming the room's group id (TEXT, CC 3.2 T7 [G32]; the token's spelling is not yet stated) | founding row id |
| `signers` | the `kid` of every verified statement, each resolved to its holder as for `RootBundle::statements` [G1] | |
| `duty` | a token of payload `scope[]`; several tokens are one crate grant per token [G18] | |

### 7.12 `head::Entry`

| Field | Wire source |
|---|---|
| `id`, `names`, `signer` | row id, `refs`, `kid` [G1] |
| `kind` | section 6.1 (**D**) |
| `head` | `refs.head` |
| `of` | a receipt's act (`refs.also.ack`); a cut's `refs.target` |
| `members` | a roster version's `members[].key` |
| `q` | **T** / **D**: the count the version's `consensus_protocol` asks |
| `sigs` | a cut's statements' `kid` |
| `length` | **T** (the window spec) |
| `receipt` | **L**: first-held instant |
| `duty`, `delete`, `stub`, `concl`, `final_counts`, `settled_stub`, `ackers`, `acks`, `dropped` | **L**: purge state |
| `at` | payload `asserted_at` |

### 7.13 Specs and views the store supplies

`cut::CutSpec`, `held::HeldSpec`, `line::LineSpec`, `key_end::KeyView` (key-end-retained), `root::RootView`, the
`seat::SeatLaw` and `window::WindowSpec` tables: **D** and **T**. They carry no row member and are not mapped.

## 8. Rows to present, per function

A function's answer is correct only over the right rows. The smallest correct set is **not** the judged row's causal
past. It is, in general:

1. every held row over the object the answer is about: concurrent cuts, contests, the tips and their fold, and held
   growth (a row concluded after the judged row that completes an offer at a tip);
2. the person and key rows of every signer and cosigner those rows carry: each key's `key:record` rows (renewals and
   rotations), its `key:revocation` rows, and its self roster (`identity:occurrence`, `identity:occurrence_revocation`,
   the genesis key's record; a voice's room keys);
3. the reader's own rows over the object: every row it signed or cosigned there (each is an acknowledgement: the kernel's ruling label H6, not yet a sentence of the text);
4. for a root answer, the lineage's bundles (every tip), the holder key revocations, and the root lane's rows
   (grants, their later statements, acceptance edges, halts);
5. for a licence, the acceptance edges the walk can reach and their ends, and the authority's record.

Below, **beyond** marks what a function reads outside that set: a table, a closure, an instant, a view the store
builds. A row left out of the set is not an error the crate can see: the answer is then the answer over fewer rows.

| Function | Rows to present | Beyond |
|---|---|---|
| `layers::kept`, `layers::conclude` (and so every `Concluded` below) | every held row the answer's set needs; a row naming a row not given waits | the family's rule |
| `seat::seat_rule` | the set above (1 to 3) for the row's object: it reads through `Past::graph`, not only the row's ancestors (rule 5 over concurrent removals, the S'' void of self-forked changes, a countersign's withdrawals) | `SeatLaw` (pinned tables); `CutSpec::key_view` at every voices step; `CutSpec::trust_root` for a recovery widening (`bundle()`) and a `Conf::Root` seat, which then needs (4) |
| `seat::Seats::new`, `Seats::for_reader`, `seat::for_reader` | (1) to (3) for every object asked of the roster; `for_reader` with the reader's own key, `Seats::new` with `own` `None` for a reader with no row | as `seat_rule`; `Seats::for_reader` takes the void set `seat::for_reader` returned |
| `Seats::holders`, `holders_at`, `roster`, `one`, `stands`, `tips`, `tips_fold`, `tips_common`, `dissolved` | the rows the `Seats` was built over | `holders_at`: the instant the row `at` states; `stands` with a delegation chain: every link's offer and acceptance; with a `Root`, (4) |
| `seat::members_at` | the rows in the past of the heads named, with the acceptances in the counted row's own past that complete offers at those heads | `SeatLaw`; the scope asked. The one seat answer read from a past alone |
| `seat::met` | none: numbers (`yes`, `n`, the policy, a declared threshold). The count itself (`count_met`) is internal to `seat_rule` | |
| `seat::Persons`, `persons_of`, `person_at`; `person_keys` (key-person, being built) | (2) for every key a count reads, over the counted row's concluded past: the self roster's founding record, its counted additions and evictions (with their windows' rows), and each key's own revocation | `SeatLaw::kinds` (a law with no kinds names no person) |
| the key view: `key_end::KeyReading`, `counts_by`, `counts_for`, `counts`, `live`, `ended`, `retained`, `bytes_retained` | each voice key's `key:record` rows (every renewal and rotation), its `key:revocation` rows, its roster ends, the seat rows whose signatures are judged, in one causal order with the key lane; for `counts_for`, the reader's own rows | the final counts (`final_`, from `seat::final_by_ack`: their receipts must be held); `live`, `ended`, `retained`, `bytes_retained` read `now` (a node-local reading, never a verdict) |
| `root::Root::new`, `RootReading`, `Root::in_force`, `grant`, `grant_in_force`, `halt_in_force`, `reader_line`, `fold` | (4): every held bundle of the lineage (every tip and every join), the revocations of holder keys, every root lane row (grants, later statements over them, acceptance edges, halts) | the reader (`Reader`: its anchor, a bundle's object id or the holders' thumbprints, and its own acknowledgement rows in causal order) |
| `trust_rows::edges_of`, `standing`, `read_licence` | (5) and (1) to (3) as the `Seats` is built: the licence row; the authority's record (a community's record versions and its duty holders' seats, or a key authority's self roster); the license-seat chain (offers, acceptances, withdrawals); every acceptance edge on the walk (the reader's own, then each authority's onward edges, to depth 5) with their withdrawals and ends | `now` (an edge's and a licence's term); the charters `supplied` from elsewhere (the trust root's scope) |
| `audience::place`, `audiences` | the row (and, for `audiences`, every row of the room: the copy rule reads every concluded placed row naming a row, and a `follows` row reads the row it follows) | the `roster` closure (`Seats::roster` over the room's held rows, built as above); the `person` closure (the signer's person's keys); `Joins` (the members at each row's own head, and `history_on_join`) |
| `content::answers` | the rows that bear on one member in one room: the roster heads (with their parents), the member's content rows, the ends of its seats, rows adding tips (`membership:keeps`), its key ends, the reader's acknowledgements | `Seat` (the member, what each version is to it); the `Past` oracle, asked only of these ids. An `Undecided` names the row to fetch |
| `window::rule`, `window::outcome`, `unwithdrawn` | the opener; every answer naming it and every withdrawal of an answer; every receipt and landing and the rows each landing cites; the rows at the opener's head the counted bases read (roster heads, duty seats); any row of the target (a receipt with one in its past is no receipt) | `Tables` (the window specs); `SeatLaw`; for `outcome`, `cut_counts` (from `cut::Cut` over the same rows); the key view at the answers |
| `seat::act_in_force` | (1) to (3) for the act's room: the act, the actor's standing rows (its seat, ends of it, the receipts of the act), lifts and their counts, reconsiderations, releases, countersigns and their withdrawals | `SeatLaw` (the affiliation acts) |
| `seat::election_closed` | every concluded row of the election over the room: ballots, their withdrawals, declines, receipts, every seating, the ends of the last holder's seat it reads, the roster at those heads | `SeatLaw` |
| `conferral::answers` | the rows that bear on one standing: its heads, the acts under it, its end if held, receipts, key removals, the grantee's re-acceptance, the receipter's end | `conferral::Standing` (who each key is to the standing, the reader's acknowledged heads, `deputy_depth`); the `Past` oracle over those ids |
| `standing::answers` | the rows that bear on one node's duty under one root grant: the bundle versions, the node's bindings and re-bindings, the owners' acceptances of the grant, the node's acts and deputy edges, the grant's end if held, receipts, key removals | `conferral::Standing`; the `Past` oracle |
| `head::purge`, `head::View` | the whole store as `head::Entry` rows (stubs included) | this node's own key, `now`, the `Reading` |

**Caching.** Every answer is a pure function of what it is given, so a store may cache it. The key is the exact set
of presented row ids (and, for the root and the walk, object ids), the reader, the key view's inputs (the key-lane
rows and the final counts), `now` where the function reads one, and the table pins (`SeatLaw`, `Tables`, the family
model's sha256). The entry is dropped when any new row is held that would enter that set (by the rules above: a row
over the object, a signer's key or person row, a reader's row, a bundle or root-lane row, an edge on the walk). A
cached answer is never written back as a row field or a stored verdict, and never read as one: it is the answer
over that set, and only that set.

## The NO WIRE FAMILY findings, ruled

Each was a crate field with no wire source at `d5d42bf`. The Constitution ruled each; the tables above apply the
rulings.

| # | Crate field | Ruling | Status |
|---|---|---|---|
| N1 | `SeatKind::Decline` | a decline is the winner's own signed row and answers the offer, `refs.answers`; its family is not yet registered | PROVISIONAL |
| N2 | `SeatRow::scope` on a `Withdraw` | a lay-down is a `withdraws` targeting the seating conferral, carrying the duty it ends as its scope | RULED (the payload member's name, and rule 0's admission of a signer's own withdrawal on a counted record, follow in the text) |
| N3 | `SeatRow::bundle` | the recovery widening carries `refs.also.stands_on` naming the counted grant; the bundle is the grant's `refs.head`, so the field is **D** | RULED |
| N4 | `SeatRow::options` | an election's options are the roster it names; a poll's opening row and options have no family yet | RULED (election); open for polls |
| N5 | `SeatRow::merge_duties` | a merge carries no duty seats: they fold; the accessor is removed | RULED |
| N6 | `WindowRow::says` on a landing | derived from the leaf: `landed` lands the change, `refused` is every other outcome; a tally's direction is recomputed from the cited rows | RULED |
| N7 | `StandingRow::on` on an acceptance | none: the acceptance stands while its author is `owner_of` the key the grant names; the store derives the binding | RULED |
| N8 | `RootBundle::names` | a settler names its other contested siblings under `refs.also.cites` | PROVISIONAL |
| N9 | `RootBundle::settles` | a settler names the sibling that stands under `refs.target` | PROVISIONAL |
| N10 | `SeatRow::head` on a room count's receipt | the count is read at each named act's own head; the receipt names no head | TEXT (CC 2.7.5) |

Wire-side notes, as the Constitution read them:

- `trust:accepts` names its bundle in `attached_head_digest`, outside `refs`, by design (CC 3.2 T4a); a holder adds
  it to the named set. CC 2.1 calls it a byte string of the roster record where T6 and the CDDL give the bundle's
  object id: the Constitution's to reconcile.
- `takedown_notice` names its content by `content_sha256`, by design: the notice reaches the establishing
  attestation, at the scope whose duty it was issued under; a steward purge names a selection, not a row.
- `membership:proposal`, `membership:resignation` and the two ballot rows have members in prose and no payload rule
  yet; `ranks` is a sequence of up to three identity references.

## Guessed mappings

Each was a mapping the text did not state plainly. The Constitution read each against the text at `d5d42bf`: the
status column cites it as TEXT, RULED or PROVISIONAL, or as the **kernel's choice** where it is how the crate
presents a wire row and the text leaves it to the reader.

| # | Field | The reading taken | Status |
|---|---|---|---|
| G1 | `Row::signer` | `kid`, the key that signed, as an identity reference; `cosigners()` likewise. The person is derived by the persons map (`seat::Persons`, from the self roster: a device key to its genesis key, a room key to its voice). `iss` MUST name the person the persons map gives; a mismatch is a door refusal. Required by the key view (`seat::voices_with` calls `key_end::counts_by(row, signer)`, keyed by `kid`) and by key-person's persons map, which reads the signer as the device key. The root lane reads `kid` too (`RootGrant::signer`, `RootGrant::signers`, `RootBundle::statements`): the root fold judges the key (a voice under a key a recovery retired is no voice, a holder is one voice across its keys, retired and spent keys are tracked by key), and the holder is resolved from the bundle's `holders` and cited key records, a holder's current key in the bundle in force. One signer everywhere. ADOPTING.md's private-room sentence reads: the voice is the person the persons map gives for the signing key. | TEXT: `iss` is the signer's identity, `kid` the signing key, and step 8 (CC 2.6.1.7) ties them: persons(`kid`) MUST equal `iss`, a mismatch a door refusal. Only key-life rules read `kid` itself; who-signed rules (standing, counts by person, `author`, "any key of that member") read persons(`kid`). The edges: in a private room persons(`kid`) is the voice, not the person; a node's row there has `iss` = `kid` (the node's room key); a recovery statement has `kid` the recovery key and `iss` the holder |
| G2 | `Row::signer` of a counted row | the `kid` of the verified statement with the least statement id; the other voices' `kid`s are `cosigners()`. Rules that set one signer apart (a window table over `others`, `author_apart`) read whichever voice is chosen. | kernel's choice: a counted row has voices and no signer in the text (TEXT-silent); the least statement id is presentation, and no rule may read `signer()` apart from `cosigners()` on a counted row |
| G3 | `AudienceRow::scope` `addressed` | `addressed` is a row carrying a signed `for_key_id`; a row with no `cohort_scope` takes its family's placement rule | TEXT, and the guess was wrong: `addressed` is a row carrying a signed `for_key_id` (CC 6.1.9); a row with no `cohort_scope` takes its family's placement |
| G4 | a group id | the group object is the group id; every first version under it is presented, and two are tips | TEXT: the id is a function of the first version, and two first versions under one id wait as tips (CC 3.3.4), so resolving the id never picks one. Crate note in section 4 |
| G5 | the self roster | its object is the identity, `Obj::Key(identity_key_id)`; an `identity:occurrence` is an offer of scope `key` to the `occurrence_key_id`, its revocation an unseat | TEXT: the self is its fedID, and a genesis key can hold several records. Crate note in section 4 |
| G6 | `Record::at_old` | the rotation's own `asserted_at`, since the old key's statement is over the same payload | TEXT (derivable): one payload, one `asserted_at` |
| G7 | an acceptance of a proposal | a standing acceptance (`of()` `None`, `scope` the `role` or `member`, `obj` the group), which the widening names under `refs.also.cites`; the crate's `consented` reads it that way | TEXT: the acceptance answers the proposal (`refs.answers`), the widening cites the acceptance (`also.cites`) |
| G8 | `membership:decline` | a `Withdraw` of the row it answers (the crate's "declining an invitation" is a withdrawal of an offer never consented to) | kernel's choice, outcome-equal to the text: a decline ends the proposal for seating; in the text it is the key's answer, and an acceptance concurrent with it is contested, not retired |
| G9 | `membership:resignation` | a `Withdraw` whose `target()` the store derives: the offer that seats the member (its widening, or the founding version), or its own acceptance. No `refs.target` is stated for the leaf. | HELD: the Constitution RULED a resignation names no target (the member's stay at the head named). The crate's `Withdraw` reads `target()`, so this reading stays until the lead settles cases 5 and 7 of VECTORS.md |
| G10 | a counted `withdraws` | an `Unseat` of the target's seat (the model's holders' withdrawal is `unseat ... duty_withdraw`) | TEXT (derivable): a counted `withdraws` ends what its target is; `Unseat` only where the target is a seat's conferral (a grant's end is `GrantEnd`; a roster version or a licence is retired, unseating nobody) |
| G11 | the reader's acknowledgement | every row the reader signs naming a roster head is an `Ack` with `room()` that head's group | RULED (the heads ruling, H6), not yet in the text: the text states no row form for a reader's acknowledgement |
| G12 | an election's id row (`of()` of a ballot, a decline, a seating) | the ballot names its election's row by `row-ref` | RULED: the ballot names its election's row (the last seating, or the roster's first version) by `row-ref`; the id is derived |
| G13 | the set an election seating names | the seating cites the rows it counts under `refs.also.cites` | RULED: the seating cites each ballot, withdrawal and decline it counts under `refs.also.cites`; the store presents those rows |
| G14 | `window:refused:v1` | a landing stating refused | TEXT: a `window:refused` row is a landing |
| G15 | `SeatKind::Countersign` | each eligible outside voice (a further statement by the designated official or an overseer over the act's own payload: same payload, same row id) is PRESENTED as a `Countersign` row view: `of()` the act's row id, `signer()` the outside voice's `kid`, `Row::id` its statement id | RULED: a countersign is a voice on the act's own row. The row view is a presentation bridge for 0.5.0; the native shape (the crate reading the voice among the act's own statements) follows after the tag |
| G16 | `standing::Kind::Removal` | a `membership:removal` whose `sub` is the key | TEXT: `member` equals `sub` |
| G17 | scope `agent` | read from the seated key's `key:record` `identity_type` (contains `agent`); the widening itself carries no scope | TEXT (derivable): the record read is the one covering the admission's instant |
| G18 | a `scope[]` with several tokens | one crate row per token, sharing ONE fate: the same row id, so one withdrawal or unseat ends all of them, and they stand together as one seat | TEXT: one conferral row is one seat with several scopes. A founding record's seats are per duty (one per `duty_holders` entry) |
| G19 | `official`, `overseen_by` | members of the affiliation's record named in prose (CC 4.4.3.12); `official`'s member name is not stated | TEXT for the names (`overseen_by`, one group id; `declared_cohort`; `licence_classes`; `designated_officials`), RULED for the place: payload members of the community record beside `consensus_protocol` |
| G20 | `weights`, `need` of a weighted record | `weights` and `need` are payload members of the record | RULED: `weights` and `need`, whole numbers, payload members of the record beside `consensus_protocol` |
| G21 | a quarantine release's `of()` | the withhold it lifts, under `refs.also.cites` | RULED: the release names the withhold under `refs.also.cites` |
| G22 | a takedown's `of()` | the content row whose bytes hash to `content_sha256`; the notice names no row | TEXT: the notice reaches the establishing attestation the hash binds, at the scope its duty is over; a steward purge names a selection |
| G23 | a reconsideration's `of()` | the notice, under `refs.also.cites`; the ruling in `outcome` | RULED: the reconsideration names the notice under `refs.also.cites` and carries its ruling in `outcome` |
| G24 | a lift's `content()` | the removal, under `refs.also.cites` | TEXT: the lift cites the act it lifts under `refs.also.cites` |
| G25 | the key end views' signer | the `kid` of the statement, as an identity reference: the same as every view under G1 | TEXT (derivable): liveness, cover and lapse are of the key that signed |
| G26 | `KeyEndRow::statement().1` | the key record of the `kid` whose window covers the statement's `asserted_at`, found by the store | TEXT (derivable): any held record of the key covering the instant covers it |
| G27 | `AudienceRow::family` | label -70002 respelled as its registry pattern, on every row; the `dimension` less its version is a leaf, not a pattern to match | TEXT |
| G28 | a re-binding's `on()` | the binding it ends, under `refs.target` | TEXT (derivable): supersede-then-rebind names the old binding under `refs.target`; a re-signing at another scope ends nothing |
| G29 | `RootBundle::sub_delegation` | every duty of the charter where `charter.scope` holds `sub_delegation` | TEXT (derivable): `sub_delegation` in `charter.scope`, per charter; whether the grant must also carry it is not yet stated |
| G30 | `RootBundle::recovery` | the second element is the commitment digest, compared by equality, not the recovery key | TEXT: compared by equality, in constant time |
| G31 | `RootBundle::recovers` | the new key is the key of the holder's new signing-key record cited under `refs.also.cites` | TEXT: the new key is the cited record that is not the `kid`'s |
| G32 | `RootGrant::scope` | a token of the grant's `scope` naming the room | TEXT, and the guess was wrong: the room is a token of the grant's `scope` (CC 3.2 T7), not `community_id`; the token's spelling is not yet stated |
| G33 | `KeyEndRow::roster_end` | a concluded eviction by the person's self roster, under its own count rule; never signed by the successor | RULED: it ends the key as a key of that person (no voice or standing; persons(`kid`) no longer gives that person, so `iss` = that person with that `kid` is a door refusal), not its liveness; `effective_at` and `revoked_at` are documentary |
| G34 | `AudienceRow::follows` | the family's existing role (`custody` its content, `stream:head` its stream), else `refs.also.cites` (`ownership` the binding, `duty` the permission) | RULED; no such reference is `follows_not_named` |
