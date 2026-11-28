# The wire map: `ceg-row/2` to the crate's row views

This note maps each field a crate row view reads to the signed wire statement it comes from. A store builds
exactly this map to present rows, and a minter reads it the other way, to turn a neutral case
([`VECTORS.md`](VECTORS.md)) into signed statements.

Sources read:

- The Constitution at `origin/rc23-next` `d5d42bf`: `manifests/signed_object_v2.cddl` (the row and object CDDL, the
  schema CC 2.6.1.4 names; `ietf/signed_object.cddl` is the Internet-Draft's copy), `manifests/family_payloads_v2.cddl`, `manifests/family_model.json`
  (columns `authorship`, `second_signers`, `count`, `names_head`, `standing_act`, `confers`, `body`), and the text
  of CC 2.4.1.1, CC 2.4.1.2, CC 2.6.1.1 to 2.6.1.11, CC 3.1.3.2, CC 3.1.4, CC 4.4.3.12, CC 4.5.4, CC 4.5.13.
- The crate at `release-0.5.0-wip` `11804e1` (root-fold merged), and the row fields the unmerged lanes add:
  `roster-merge` `23b26c1`, `audience` `3a37cd2`, `charter` `48b44ad` (which contains `persist-gaps` `9e791b3`),
  `key-person` `70af5e8`, `room-key-vectors` `d991aa5` (fixture only), `key-end-retained` `44c697c`. The tables
  below are the union.
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
| **NO WIRE FAMILY** | The crate reads a fact a signed row should carry, and no family, member or role carries it. Listed in [the findings](#no-wire-family-findings). |
| **[Gn]** | The mapping is a reading, not stated by the text. Listed in [the guessed mappings](#guessed-mappings). |

## 1. The statement and its three ids

A row is one `COSE_Sign1` statement, or several over one payload (CC 2.6.1.1, 2.6.1.9).

| Wire element | Where | What the crate takes from it |
|---|---|---|
| `alg` | protected label 1 | Nothing. The constant `-70100`, the composite ML-DSA-65 with Ed25519. This is the only signature suite of a row; there is no other suite member on a row. (`suite` in an `mls:leaf_vouch` payload is the MLS ciphersuite, the constant 77, and no crate view reads it.) |
| `cty` | protected label 3 | Nothing. The constant `application/vnd.ciris.row+cbor`. |
| `kid` | protected label 4 | The signing key: a 32-byte RFC 9679 thumbprint. Presented as the key's identity reference (`urn:ietf:params:oauth:ckt:sha-256:` + base64url of the 32 bytes). This is `Row::signer` on every view except the root lane [G1]. |
| `iss` | CWT label 1 | The signer's stable identity: its genesis key's identity reference; under a room key, the voice (the identity reference of the voice's first room key). Not `Row::signer` [G1]: it MUST name the person the persons map gives for `kid` (`seat::Persons`, from the self roster), and a statement whose `iss` disagrees is refused at the door. The root lane's views (`RootBundle::statements`, `RootGrant::signers`) read `iss`, because a bundle names its holders by identity. |
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
| the cohort scope of a row (placement) | payload `cohort_scope`, with `community_id` or `family_id` (each a group id); a row with no `cohort_scope` that names keys for delivery is `addressed` [G3] |

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
- An election's set: `ballot:moderator_acceptance` binds "the digest of the ballot and withdrawal rows counted"
  (CC 3.1.4), and `ballot:moderator` names "the election id (digest of the community id and the last seating
  row, or of the roster's genesis)". Neither is a `row-ref`. See [G12], [G13].

## 4. Objects: rows, keys and groups

`seat::Obj` is `Row(id)` or `Key(k)`; `Obj::from_reference` types a reference by form: `[-16, digest]` is a row, an
identity reference is a key.

| Wire reference | `Obj` |
|---|---|
| a row id in `refs` | `Obj::Row(row id)` |
| an identity reference (`sub`, `member`, `members[].key`, `holders[]`) | `Obj::Key(identity reference)` |
| a group id `group-…` (payload `group`, `community_id`, `family_id`, `on_behalf_of`; a `sub` of a group's row) | `Obj::Row(row id of the group's first `group:roster` version)` [G4]. `Obj::from_reference` recognises neither form for it: a group id is no thumbprint URI and no digest pair. The store resolves the group id to the founding version, which carries the same `group` member. |
| a lineage name (`family_key_id`, a `sub` naming it) | not an `Obj`: `RootBundle::family` |

**A group's id** is derived, never chosen: `"group-"` + base64url (unpadded) of SHA-256 over
`["CEG-group/2", group_kind, first_members (a set of identity references), founded_at (ms), nonce (32 bytes)]`,
taken from the first version. A case that founds a group gives those inputs; the minter derives the id.

**A self roster** (key-person): its object is the founding record of a person's own key roster (CC 3.3.6.4), whose
first bind names the genesis key's own `key:record` in `refs.head`. Present that `key:record` row's id as the
roster's object, `Obj::Row(record row id)`, with `SeatLaw::kinds` mapping its scope to
`CommunityKind::SelfRoster` [G5].

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
| an election decline | `Decline`: **NO WIRE FAMILY** [N1] | | | |
| `ballot:moderation_action` | `Other` | `Answer` (`says` `for` or `against`) | | `Answer` |
| `objection:{state}` (`assent`, `raised`) | `Other` | `Answer`, `says` the state leaf | | `Answer` |
| `window:held:v1` | `Other` | `Receipt` | | `Other` |
| `window:landed:v1` | `Other` | `Landing` | | `Other` |
| `window:refused:v1` | `Other` | `Landing` stating refused [G14] | | `Other` |
| `quarantine:{state}` | `Quarantine` | | | |
| `slashing:{outcome}` | `Slashing` | | | |
| `takedown_notice:{basis}` | `TakedownNotice` | | | |
| `reconsideration:{grounds}` | `Reconsideration` | | | |
| a countersign of a one-officer affiliation's act | `Countersign` [G15] | | | |
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
| `scope` | widening, removal: `"member"`, or `"agent"` where the member's key record's `identity_type` contains `agent` [G17]. `group:roster` first version: `"member"`, or `"founder"` for an infrastructure community (`cohort_subkind` `infrastructure`). Later `group:roster` version: `"record"`. `self:delegates_to`: a token of payload `scope[]` other than `sub_delegation`; a set of several duty tokens is one crate row per token [G18]. Owner-binding: `"owner"`. `key:record`: `"registered"`. Acceptance: the payload `role`, else `"member"`. Withdraw: **NO WIRE FAMILY** [N2] | |
| `obj` | widening, removal, acceptance, keeps: payload `group`. `self:delegates_to` over a room: payload `community_id` (or `family_id`). Founding version: its own row id. Owner-binding, `key:record`: `Obj::Key(sub)` | a group id resolves to the founding version's row id [G4] |
| `conf` | **D**: `Own` for a founding version and for a row over the signer's own key; `Seat` for an authored `delegates_to` under a seat (`refs.also.under` present, or the signer's own live seat); `Group` for every counted arm | |
| `under` | `refs.also.under`, its one element | row id |
| `cosigners` | the `kid` of every further verified statement over the payload (section 1); on an authored row, the second-consent roles | identity references |
| `subjects` | payload `subject_key_ids` | identity references (or `canonical:{hashalg}:{hex}` text) |
| `sub` | `"sub_delegation"` is a token of the `delegates_to` payload `scope[]` (CC 4.4.3.19) | |
| `head` | `refs.head` then `refs.further_heads` | row ids |
| `consensus_protocol` | `group:roster` payload `consensus_protocol` | |
| `cohort_subkind` | `group:roster` payload `cohort_subkind` | |
| `group_kind` | `group:roster` payload `group_kind` | |
| `official` | an affiliation record's designated official [G19] | the text names the limb ("designated officials", CC 4.4.3.12) and no member |
| `overseen_by` | the affiliation record's `overseen_by` (CC 4.4.3.12 names the member in prose; no CDDL rule) | a group id or row id [G19] |
| `family_param` | the `dimension` segment at the family's `{name}` position | text |
| `outcome` | `reconsideration:{grounds}` payload `outcome` (CC 4.5.5 prose; no CDDL rule); on `slashing:{outcome}`, the `{outcome}` segment | |
| `agent_registration` | `key:record` payload `identity_type` (a set) contains `agent` | |
| `target_key` | `quarantine:{state}`, `slashing:{outcome}`: `sub` | identity reference |
| `protocol_entrenched` | `group:roster` `consensus_protocol_entrenched`; absent reads false on the wire, `None` here only where the version omits it | |
| `admission_quorum_basis` | `group:roster` `cohort_subkind_payload.infrastructure_constraint.admission_quorum_basis` | |
| `dissolves` | `group:roster` carries `dissolved_at` | |
| `bundle` | a recovery widening's bundle: **NO WIRE FAMILY** [N3] | |
| `role` | widening `role`; `group:roster` `members[].role` (`founder`) on a founders' amendment | |
| `regime` | **D**: the protocol in force and the act's policy, as one value the store composes | |
| `lifts` | payload `lifts` (present only as `true`) | |
| `policy` | **T**: the act's policy row (`governance_policy_acts.tsv`, `act_of`, `policy_for`); `moderator_election` for a `ballot:moderator_acceptance` seating | |
| `counted` | **T** | |
| `over` | **T** | |
| `need` | **T** for a count; on a record declaring `weighted:{rubric}`, the threshold in the record's `policy` map [G20] | |
| `of` | `Accept` replying to a grant: `refs.answers`. `Ack`: one element of `refs.also.ack`. `Ballot`, `Decline`, election seating: the election's id row, derived from the election id [G12]. `Quarantine` release: the withhold it lifts [G21]. `TakedownNotice`: the content row, which the notice names by `content_sha256`, not by row id [G22]. `Reconsideration`: the notice [G23]. `Countersign`: the act [G15] | row ids |
| `target` | `withdraws` `refs.target` | row id |
| `content` | a lift's citation of the removal: `refs.also.cites` [G24] | row id |
| `duties` | `group:roster` `policy.duties` | |
| `duty_holders` | `group:roster` `duty_holders` (first version only) | map duty to a set of identity references |
| `weights` | a `weighted:{rubric}` record's weights in its `policy` map [G20] | |
| `options` | **NO WIRE FAMILY** [N4] | no ranked offer with options is a wire row (the election's seating states none) |
| `ranking` | `ballot:moderator` `ranks`, up to three identity references in order (a sequence) | the family model's body cell for `ranks` is `type: unstated` |
| `signing_key` | `kid`, as an identity reference | |
| `room` | `Ack` read from a reader's row: the group of the head it names **D** | |
| `licence_classes` | the community record's `licence_classes`, each with `legal_weight` (CC 4.4.3.12 prose; no CDDL rule) | |
| `declared_cohort` | the community record's `declared_cohort` (CC 4.4.3.12 prose; no CDDL rule) | |
| `private_room` | founding `group:roster` `membership` is `private` | |
| `merge` (roster-merge) | a later `group:roster` version naming two or more tips (`refs.head` and `refs.further_heads`) | |
| `merge_members` (roster-merge) | that version's `members[].key` | |
| `merge_duties` (roster-merge) | **NO WIRE FAMILY** [N5]: `duty_holders` is carried "on the first version of a community only" | |

### 7.3 `window::WindowRow`

| Accessor | Wire source | Notes |
|---|---|---|
| `win_kind` | section 6.1 | **D** |
| `window` | **T**: the window name of the opener's act's table row | |
| `target_key` | the opener's `sub`, where it is a key | identity reference |
| `says` | an answer: the `objection:{state}` leaf (`assent`, `raised`) or the ballot's word (`for`, `against`). A landing's outcome: **NO WIRE FAMILY** [N6] | `window-step` carries `author`, `dimension`, `refs`, `asserted_at` and no outcome |
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
| `family` | the family name matched against `audience_table.rs` patterns: the `dimension` less its `:vN`; for a row with no `dimension`, the family id respelled as its pattern [G27] | |
| `scope` | payload `cohort_scope`, or `addressed` [G3] | |
| `room` | payload `community_id` or `family_id` [G4] | founding row id |
| `named` | `sub` (the attested key), `subject_key_ids`, `for_key_id` | identity references |
| `seat_act`, `obj`, `to` | as `SeatRow` (section 7.2) on a widening (`Offer`) or removal (`Unseat`) | |
| `concluded` | **D** | |
| `history_on_join` | payload `history_on_join` (`full`, `from_join`) | |

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
| `on` | an act: `refs.also.stands_on`. A receipt: its act under `refs.also.ack`. An acceptance: its binding: **NO WIRE FAMILY** [N7] (the reply names the grant under `refs.answers`, never the binding). A re-binding: the binding it ends [G28] | |
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
| `names` | the bundles a settler names beside those it extends: **NO WIRE FAMILY** [N8] | |
| `recovery` | `charter.recovery_commitments`: holder to the commitment `[-16, SHA-256(["CEG-recovery/2", [key]])]`, not the key [G30] | |
| `settles` | **NO WIRE FAMILY** [N9] | |
| `recovers` | a recovery bundle (one statement, `iss` the holder, `kid` the recovery key): (`iss`, the key of the holder's new signing-key record under `refs.also.cites`) [G31] | |
| `iat` | `floor(asserted_at / 1000)` | seconds |
| `statements` | each verified statement: (`iss`, its CWT `iat`) | |

### 7.11 `root::RootGrant`

| Accessor | Wire source | Notes |
|---|---|---|
| `id`, `names`, `signer` | row id (statement id for a `cosigns` row), `refs` plus `attached_head_digest`, `iss` (the root lane counts holders by identity) | |
| `is_grant` | family `trust:.job:.version`, dimension `trust:confers:v1`, row type `delegates_to` | |
| `attached_head` | `trust:accepts` `attached_head_digest` | object id |
| `cosigns` | the grant's row id, on a later statement over its payload | |
| `halts` | family `accord:invoke:constitutional:.halt_id` | |
| `bundles` | `refs.head` and `refs.further_heads` | object ids |
| `to` | `sub` | identity reference |
| `scope` | the room the grant seats in: payload `community_id` [G32] | founding row id |
| `signers` | the `iss` of every verified statement | |
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

## NO WIRE FAMILY findings

Each is a crate field a signed row should carry and that no family, member or `refs` role carries at
`rc23-next` `d5d42bf`. They are findings for the Constitution.

| # | Crate field | What the crate reads | What the wire has |
|---|---|---|---|
| N1 | `SeatKind::Decline` (with `of()` the election) | a member's decline of an election | `ballot:moderator`, `ballot:moderator_acceptance` and the generic `membership:decline` (which answers a proposal or a grant). No election decline. |
| N2 | `SeatRow::scope` on a `Withdraw` | the one seat of the target a withdrawal ends (a founder laying down one duty of a founding record) | a `withdraws` payload carries `refs`, `asserted_at` and `lifts`; no member names the seat |
| N3 | `SeatRow::bundle` | the bundle a stalled infrastructure room's recovery widening is counted over | a widening's `refs.head` is its roster head; no member or role names a bundle |
| N4 | `SeatRow::options` | a ranked offer's options | no family carries options; the moderator election states none |
| N5 | `SeatRow::merge_duties` (roster-merge) | a roster merge's duty seats | `duty_holders` is "on the first version of a community only" |
| N6 | `WindowRow::says` on a landing | the outcome a landing states | `window-step` carries no outcome member; the leaves are `held`, `landed`, `refused` |
| N7 | `StandingRow::on` on an acceptance | the binding an owner's acceptance of a grant is made under | `membership-reply` names only the grant under `refs.answers` |
| N8 | `RootBundle::names` | the sibling bundles a bundle at a head names besides those it extends (rule 3) | `genesis-refs` carries `prev`, `further_prev` (a join) and `also.cites` (rows); no role names a sibling that is not a predecessor |
| N9 | `RootBundle::settles` | which contested sibling a settler names as the one that stands | no member |
| N10 | `SeatRow::head` on a room count's receipt (`SeatKind::Ack`, `Conf::Group`, `of()` a lone removal) | the heads the count is read at (each the removal's head or later) | `act:ack` "names no head" (`family_payloads_v2.cddl`, `act-ack`) |

Wire-side mismatches the map met, for the same list:

- The two CDDL copies differ on `genesis-refs`: `manifests/signed_object_v2.cddl` carries `further_prev` (since
  `12615bd`), and `ietf/signed_object.cddl`, the Internet-Draft's copy, still lists `prev` and `also` only. The map
  reads the manifests copy, the schema CC 2.6.1.4 names.
- `trust:accepts` names its bundle in `attached_head_digest`, outside `refs`; a reader gathering the named set from
  `refs` alone misses it.
- `ballot:moderator` and `ballot:moderator_acceptance` name the election and its counted set by digests (CC 3.1.4),
  not by `row-ref`; neither payload has a CDDL rule.
- `takedown_notice` names its content by `content_sha256`, not by row id.
- `membership:proposal` and `membership:resignation` have no payload rule in `family_payloads_v2.cddl`;
  `ballot:moderator`'s `ranks` is `type: unstated` in the family model.

## Guessed mappings

Each is a mapping the text does not state. Those marked **kernel's choice** are how the crate presents a wire
row, not a reading of the text: they are settled here, and a store and a minter follow them. Those marked
**open** wait on the Constitution's ruling.

| # | Field | The reading taken | Status |
|---|---|---|---|
| G1 | `Row::signer` | `kid`, the key that signed, as an identity reference; `cosigners()` likewise. The person is derived by the persons map (`seat::Persons`, from the self roster: a device key to its genesis key, a room key to its voice). `iss` MUST name the person the persons map gives; a mismatch is a door refusal. Required by the key view (`seat::voices_with` calls `key_end::counts_by(row, signer)`, keyed by `kid`) and by key-person's persons map, which reads the signer as the device key. The root lane is the exception: `RootGrant::signers` and `RootBundle::statements` read `iss`, since a bundle names its holders by identity. ADOPTING.md's private-room sentence ("the signer of every row is the voice, not the room key that signed") is then read through the persons map, which gives the voice. | provisionally confirmed by the Constitution: the signer the rules read is `kid`, and `iss` gives the identity; final with its other rulings |
| G2 | `Row::signer` of a counted row | the `kid` of the verified statement with the least statement id; the other voices' `kid`s are `cosigners()`. Rules that set one signer apart (a window table over `others`, `author_apart`) read whichever voice is chosen. | kernel's choice: the crate reads a counted row's voices as one set (signer with cosigners); one must be named signer, and the least statement id is fixed by the bytes, not by arrival. Consistent with G1: each voice is its signing key. |
| G3 | `AudienceRow::scope` `addressed` | a row with no `cohort_scope` that names keys for delivery | open: a question for the text |
| G4 | a group id | resolved to the row id of the group's first `group:roster` version; `Obj::from_reference` does not type a `group-…` reference | kernel's choice: the crate's object for a group is its founding row (`seat::Obj`); the group id is derived from that version, so the resolution is one-to-one. |
| G5 | the self roster | its object is the genesis key's `key:record` row; an `identity:occurrence` is an offer of scope `key` to the `occurrence_key_id`; its revocation an unseat | kernel's choice: `SeatLaw::kinds` types a self roster by its founding row; the genesis key's record is the row the first bind names in `refs.head`. |
| G6 | `Record::at_old` | the rotation's own `asserted_at`, since the old key's statement is over the same payload | kernel's choice: the rotation and the old key's statement are over one payload, so they state one `asserted_at`; this is the crate's `at_old`. |
| G7 | an acceptance of a proposal | a standing acceptance (`of()` `None`, `scope` the `role` or `member`, `obj` the group), which the widening names under `refs.also.cites`; the crate's `consented` reads it that way | kernel's choice: the crate's `consented` already reads a standing acceptance the offer names; the widening names the acceptance under `also.cites`. |
| G8 | `membership:decline` | a `Withdraw` of the row it answers (the crate's "declining an invitation" is a withdrawal of an offer never consented to) | kernel's choice: the crate models declining an invitation as a withdrawal of an offer never consented to, which ends no stay. |
| G9 | `membership:resignation` | a `Withdraw` whose `target()` the store derives: the offer that seats the member (its widening, or the founding version), or its own acceptance. No `refs.target` is stated for the leaf. | open: a question for the text |
| G10 | a counted `withdraws` | an `Unseat` of the target's seat (the model's holders' withdrawal is `unseat ... duty_withdraw`) | kernel's choice: the crate's cut on a seat slot is `Unseat`; the model presents the holders' withdrawal so (`check_acts.py`, `duty_withdraw`). |
| G11 | the reader's acknowledgement | every row the reader signs naming a roster head is an `Ack` with `room()` that head's group | kernel's choice: CC 2.7.9 makes every row a reader signs an acknowledgement of its past; the crate reads it as `Ack` with `room()`. |
| G12 | an election's id row (`of()` of a ballot, a decline, a seating) | the wire's election id is a digest of the community id and the last seating row (or the roster's genesis); the store recomputes it and maps it to that row | kernel's choice: the text defines the election id from the last seating row (or the genesis); the crate names that row, so the store maps the digest back to it. |
| G13 | the set an election seating names | the wire binds a digest of the counted ballots and withdrawals; the crate reads the seating's `names()`; the store presents the set the digest commits to as names | kernel's choice: the crate reads a seating's set through `names()`; the store presents the rows the digest commits to. |
| G14 | `window:refused:v1` | a landing stating refused | open: a question for the text |
| G15 | `SeatKind::Countersign` | a countersign key's further statement over the act's payload, presented as its own row (`Row::id` its statement id, `of()` the act's row id). The text says "countersigned by a key outside the officers" and names no row form. | kernel's choice: the crate reads a countersign as a row with `of()` the act; a further statement presented as its own row (id its statement id) fits whatever row form the text gives. At `d5d42bf` the one-officer text (CC 4.4.3.12) says which acts are held until countersigned and who countersigns, and still names no row form. |
| G16 | `standing::Kind::Removal` | a `membership:removal` whose `sub` is the key | kernel's choice: the crate's `Removal` is a removal of a key; `membership:removal` is that row. |
| G17 | scope `agent` | read from the seated key's `key:record` `identity_type` (contains `agent`); the widening itself carries no scope | kernel's choice: the crate reads an agent's seat by scope `agent`; the key record's `identity_type` is the one place the wire says a key is an agent's. Consistent with G1: the record read is the seated key's own (an agent's key is itself, never its owner, CC 4.5.13). |
| G18 | a `scope[]` with several tokens | one crate row per token, all under the one row id | kernel's choice: the crate reads one scope per seat row; a set of tokens is presented as one crate row per token under the one row id. |
| G19 | `official`, `overseen_by` | members of the affiliation's record named in prose (CC 4.4.3.12); `official`'s member name is not stated | open: a question for the text |
| G20 | `weights`, `need` of a weighted record | members of the record's `policy` map; the member names are not stated | open: a question for the text |
| G21 | a quarantine release's `of()` | the withhold it lifts, under `refs.target` | open: a question for the text |
| G22 | a takedown's `of()` | the content row whose bytes hash to `content_sha256`; the notice names no row | open: a question for the text |
| G23 | a reconsideration's `of()` | the notice, under `refs.answers` | open: a question for the text |
| G24 | a lift's `content()` | the removal, under `refs.also.cites` | open: a question for the text |
| G25 | the key end views' signer | the `kid` of the statement, as an identity reference: the same as every view under G1 | kernel's choice: a key ends, not an identity; G1 makes this the general rule, so the key view and the seat views see one signer. |
| G26 | `KeyEndRow::statement().1` | the key record of the `kid` whose window covers the statement's `asserted_at`, found by the store | kernel's choice: no row names its cover; the store finds the record of the signing key whose window covers the instant, as `key_end` reads it. |
| G27 | `AudienceRow::family` | the `dimension` less its version, else the family id respelled as its pattern | kernel's choice: the audience table is matched by family name; the dimension less its version is that name. |
| G28 | a re-binding's `on()` | the binding it ends, under `refs.target` | open: a question for the text |
| G29 | `RootBundle::sub_delegation` | every duty of the charter where `charter.scope` holds `sub_delegation` | open: a question for the text |
| G30 | `RootBundle::recovery` | the second element is the commitment digest, compared by equality, not the recovery key | kernel's choice: the crate compares the recovery entry by equality only; the commitment is what the wire carries and compares the same way. |
| G31 | `RootBundle::recovers` | the new key is the key of the holder's new signing-key record cited under `refs.also.cites` | open: a question for the text |
| G32 | `RootGrant::scope` | the grant's placement `community_id`; `trust:confers` carries scope tokens and no room member | open: a question for the text |
