# Neutral case form

This is the form in which the kernel states a case for a signed test vector: who signs, what each row carries, in
what order the statements are minted and delivered, which crate function is asked and what it answers. It names
no bytes. A minter (CIRISVerify's `mint_cases.py`) reads a case forward, mints each statement under
[`WIRE_MAP.md`](WIRE_MAP.md), and carries the question and the expected answer through untouched. A store reads
the minted statements back through the same map and asks the crate.

The JSON schema is [`tests/vectors/schema.json`](tests/vectors/schema.json) (JSON Schema 2020-12). Every rule
below that the schema cannot state is marked **(prose)**; a minter checks it and refuses the case otherwise.

## A file

```json
{
  "form": "ciris-kernel-cases/1",
  "constitution": "CIRISConstitution rc23-next d5d42bf",
  "cases": [ ... ]
}
```

## A case

| Member | Required | What it is |
|---|---|---|
| `id` | yes | a unique id, dotted lower case (`seat.duty.conferral_on_non_member`) |
| `source` | yes | the model check and case it comes from: `{"check": "models/causal_kernel/check_duty_seats.py", "case": "<the case's own name>"}` |
| `keys` | yes | every key that signs, or that a row names, by local name (below) |
| `placement` | no | the groups the case names, by their founding inputs or a stated id (below) |
| `rows` | no | the rows, by local label (below) |
| `objects` | no | the signed objects that are not rows, by local label (below) |
| `statements` | yes | the statements in mint order (below) |
| `delivery_order` | no | the order the reader receives them, where it differs from mint order (below) |
| `reader` | yes | the identity or key that asks, and its anchor (below) |
| `questions` | yes | one or more questions, each with its expected answer (below) |

## Keys

A key is named once per case and used by name everywhere else.

```json
{"name": "A", "seed": 1, "identity": "A", "identity_type": ["user"], "kind": "genesis", "records": "minter_supplies"}
{"name": "A.phone", "seed": 11, "identity": "A", "identity_type": ["user"], "kind": "occurrence", "records": ["rec.A.phone"]}
{"name": "rk.a0", "seed": 21, "identity": "rk.a0", "identity_type": ["user"], "kind": "room", "room": "g", "records": ["rec.rk.a0"]}
```

| Member | What it is |
|---|---|
| `name` | the local name |
| `seed` | an integer `n` from 1 to 155. Verify's convention: key `n` is the seed pair `[n; 32]` and `[n + 100; 32]`, assigned to the composite key's two halves as Verify's minter assigns them. Two keys of one case never share a seed **(prose)**. |
| `identity` | the name of the key whose identity reference is this key's `iss`: the identity's genesis key; for a room key, the voice's first room key. A genesis key names itself. |
| `identity_type` | a set from `user`, `node`, `agent`, `accord_holder`. `user` or `accord_holder` never with `node` or `agent` (the text refuses the mix; a case testing that refusal is a door case, not a kernel case) |
| `kind` | how the key signs: `genesis` (as itself), `rotated` (a later key of the same identity, by a rotation record), `occurrence` (a device key bound by an `identity:occurrence`), `room` (a room key of a private room) |
| `room` | for `kind: room`, the group (a `placement` name) the key is made for |
| `records` | the labels of the `key:record` rows (in `rows`) that make the key live, or `"minter_supplies"`: the minter mints one self-signed `key:record` for it with `asserted_at` 0 and, where the end rule requires `valid_until` (`node`, `agent`, not a room key), the greatest the bound allows. A case whose answer reads a key's records lists them. |

## Placement

```json
"placement": {
  "groups": {
    "g": {"founding": {"group_kind": "community", "first_members": ["A", "B", "C"], "founded_at": {"$ms": 1000}, "nonce": {"$fill": {"byte": 7, "len": 32}}}},
    "h": {"id": "group-…"}
  }
}
```

A group is given by its founding inputs, from which the minter derives its id (`group-id-input`: `group_kind`,
`first_members` the identity references of the named keys as a set, `founded_at`, `nonce`), or by a stated `id`.
The founding inputs MUST equal the first `group:roster` version's members of the same names **(prose)**. A row
places itself by its own payload members (`cohort_scope`, `community_id`, `family_id`), written with
`{"$group": "g"}`.

## Rows

```json
"rows": {
  "md": {
    "row_type": "scores",
    "family": "membership:.stage",
    "dimension": "membership:widening:v1",
    "sub": {"$identity": "D"},
    "authorship": "counted",
    "payload": {
      "group_kind": "community",
      "group": {"$group": "g"},
      "member": {"$identity": "D"},
      "joined_at": {"$ms": 2000},
      "effective_at": {"$ms": 2000},
      "asserted_at": {"$ms": 2000}
    },
    "refs": {
      "head": {"label": "g", "id": "row"},
      "also": {"cites": [{"label": "acc.D", "id": "row"}]}
    }
  }
}
```

| Member | What it is |
|---|---|
| (the key) | the row's local label |
| `row_type` | `scores`, `delegates_to`, `supersedes`, `withdraws` or `recants` (label -70001) |
| `family` | the family id (label -70002), `.name` segments and all: `membership:.stage`, `key:record` |
| `dimension` | the full dimension string, leaf and version, where the family scores one; absent on a `withdraws`, a `recants`, a `group:roster`, a `key:record`. A segment naming a key or a group is written `{thumb:NAME}` (the bare thumbprint of key `NAME`) or `{group:NAME}`, which the minter fills. It MUST resolve to `family` **(prose)**. |
| `sub` | the CWT subject, one typed value: `{"$identity": "A"}`, `{"$key_ref": "A.phone"}`, `{"$group": "g"}`, or a text string (a lineage name, `canonical:sha256:…`) |
| `authorship` | `authored` or `counted`: which arm of the family's `authorship` cell the row is on |
| `author` | for `authored`, the key name whose identity is the payload's `author` (the minter writes `"author"` into the payload); absent for `counted` |
| `payload` | every payload member except `author`, `dimension` and `refs` (the minter writes those three from the members above and below), as typed values. `asserted_at` is required. A member the producer omits is absent, never null. |
| `refs` | the payload's `refs`, by role (below); absent where the row names nothing |

A row's statements are listed in `statements`; the row itself states no signer. A counted row has one statement
per voice; an authored row has the author's statement first and any second-consent statement after it.

### Typed values

JSON alone cannot tell bytes from text, an integer from a decimal, an instant from a count, or a set from a
sequence. Every payload value is one of:

| JSON | CBOR |
|---|---|
| a string | text |
| `true`, `false` | bool |
| an integer | an integer (a JSON number with a fraction or exponent is refused) |
| `{"$ms": n}` | an `ms-time`: POSIX milliseconds, an unsigned integer. Every instant is written so, and never "now". |
| `{"$bytes": "<hex>"}` | a byte string |
| `{"$fill": {"byte": b, "len": n}}` | `n` bytes each `b` (nonces, salts) |
| `{"$decimal": {"exponent": e, "mantissa": m}}` | tag 4, `[e, m]`, normalised (`e` negative, `m` not divisible by 10) |
| `{"$set": [ ... ]}` | an array the minter sorts by the bytewise order of each element's encoding, with no duplicate |
| `{"$seq": [ ... ]}` | an array in the order given |
| `{"$tuple": [ ... ]}` | an array whose positions the schema names, in the order given |
| a JSON object with no key beginning `$` | a map with text keys |
| `{"$identity": "A"}` | the identity reference (thumbprint URI) of key `A`'s identity |
| `{"$key_ref": "A.phone"}` | the identity reference of key `A.phone` itself |
| `{"$kid": "A.phone"}` | the 32-byte thumbprint of key `A.phone` |
| `{"$cose_key": "A.phone"}` | the composite public key of `A.phone`, as a `ceg-key` |
| `{"$group": "g"}` | the group id of placement group `g` |
| `{"$digest": {"label": "x", "id": "row"}}` | a `hash-digest` naming row or object `x` (`attached_head_digest`) |
| `{"$commitment": ["A.rec"]}` | a recovery commitment over the named keys |

### refs

```json
"refs": {
  "head": {"label": "v2", "id": "row"},
  "further_heads": [{"label": "v2b", "id": "row"}],
  "prev": {"label": "m1", "id": "row"},
  "further_prev": [],
  "answers": {"label": "prop", "id": "row"},
  "target": {"label": "conf", "id": "row"},
  "trusted_through": [{"label": "m3", "id": "row"}],
  "also": {"ack": [], "cites": [], "under": [], "stands_on": [], "voice": []}
}
```

Each entry names a local label and which id is meant: `"row"` (the row id) or `"object"` (an object id).
`refs` never names a statement id. Each array is a set (the minter sorts it); `under`, `stands_on` and `voice`
hold exactly one; `trusted_through` at most 64; `ack` 1 to 256. An empty array or an empty `refs` is omitted,
never written.

## Objects

```json
"objects": {
  "b0": {
    "typ": "ceg-genesis-bundle/2",
    "author": null,
    "iat": 1,
    "payload": {
      "version": 1,
      "asserted_at": {"$ms": 1000},
      "family_key_id": "accord",
      "holders": {"$set": [{"$identity": "h1"}, {"$identity": "h2"}, {"$identity": "h3"}]},
      "serve_nodes": {"$set": [{"$identity": "n1"}]},
      "charter": {"recovery_commitments": {"…": "…"}, "scope": {"$set": ["infra:attest", "infra:serve"]}}
    },
    "refs": {"also": {"cites": [{"label": "rec.h1", "id": "row"}]}}
  }
}
```

| Member | What it is |
|---|---|
| `typ` | `ceg-genesis-bundle/2` or `ceg-revocation-snapshot/2` |
| `author` | `null`, or the key name whose identity is the payload's `author` (a snapshot) |
| `iat` | the seconds every statement's CWT `iat` carries; for a bundle, `floor(asserted_at / 1000)` **(prose)** |
| `payload` | the members of the `typ`'s rule, `refs` apart |
| `refs` | as for a row (`prev` naming an object; `further_prev` on a join) |

An object's signers are its statements in `statements`, one per holder.

## Statements

The ordered list of statements, in mint order:

```json
"statements": [
  {"of": "g", "key": "A", "as": "self"},
  {"of": "g", "key": "B", "as": "self"},
  {"of": "md", "key": "A", "as": "self", "first_held_at": 5000},
  {"of": "md", "key": "B.phone", "as": "occurrence"},
  {"of": "b0", "key": "h1", "as": "self", "fault": {"kind": "bad_signature_half", "half": "ed25519"}}
]
```

| Member | What it is |
|---|---|
| `label` | optional; default `<of>/<key>`. Unique in the case. |
| `of` | the row or object label the statement signs |
| `key` | the signing key's name: its thumbprint is `kid`, its `identity`'s reference is `iss` |
| `as` | `self`, `rotated`, `occurrence` or `room`: the key's `kind` restated (`genesis` signs `as` `self`); a minter refuses a disagreement **(prose)** |
| `first_held_at` | optional, an integer ms: the instant the reader first held this statement. Absent: held from the start of the case. |
| `fault` | optional, one deliberate fault from the closed list below |

**Counted rows.** Each voice of a counted row (or object) is its own entry, all with the same `of`; they share
the payload and so the row id. The voices of a row are exactly its entries.

**Order.** The list is acyclic in list order: a row's or object's first statement comes after the first
statement of every label its `refs` (and its `$digest` values) name **(prose)**. Where a case tests out-of-order
arrival, `statements` is the mint order and `delivery_order` lists every statement label once, in the order the
reader receives them. With no `delivery_order`, delivery is mint order.

### Faults

Only these, each on one statement:

| `kind` | Members | What the minter does |
|---|---|---|
| `wrong_signer` | `key`: another key name | signs with that key's private key while `kid` and `iss` stay the statement's own key's |
| `bad_signature_half` | `half`: `ml_dsa_65` or `ed25519` | signs correctly, then corrupts that half of the composite signature |
| `missing_member` | `path`: a member path (`payload.dimension`, `payload.refs.head`) | mints the statement's payload without that member (the row id is then that of the reduced payload) |
| `unsorted_set` | `path`: a set's path (`payload.refs.also.cites`, `payload.trust_classes`) | writes that set in descending order instead of sorted |
| `second_encoding` | `path`, and `how`: `non_shortest_int`, `indefinite_length` or `unsorted_map_keys` | encodes that member a second way, so the bytes are not the deterministic encoding |

A faulted statement is one the door refuses or does not verify: the store presents no crate row (or no voice)
for it. The expected answer is the crate's over what remains.

## The reader

```json
"reader": {"identity": "A", "key": "A.phone", "anchor": {"bundle": {"label": "b0", "id": "object"}}}
"reader": {"identity": "N", "anchor": {"holders": ["h1", "h2", "h3"]}}
"reader": {"identity": null}
```

| Member | What it is |
|---|---|
| `identity` | the key name of the identity that asks (its own rows are its line), or `null` for a reader with no row of its own |
| `key` | optional: the key it asks under, where that matters |
| `anchor` | optional: a trust root anchor, by a bundle's object id (`bundle`) or by holder thumbprints (`holders`, key names) |

A question may carry its own `reader`, which replaces the case's for that question.

## Questions

```json
"questions": [
  {
    "fn": "seat::Seats::holders",
    "subject": {"scope": "moderate", "obj": {"label": "g", "id": "row"}},
    "args": {"now": {"$ms": 9000}},
    "expected": ["A"]
  },
  {
    "fn": "seat::seat_rule",
    "subject": {"label": "cd", "id": "row"},
    "expected": {"undecided": {"names": {"label": "md", "id": "row"}}}
  }
]
```

| Member | What it is |
|---|---|
| `fn` | a public crate function or method, by its path under `ciris_kernel` (`seat::members_at`, `key_end::live`, `root::Root::in_force`) |
| `subject` | what it is asked of: a row or object (`label` and `id`), a key (`{"key": "D"}`), a statement (`{"statement": "md/A"}`), or the members the function takes (`scope`, `obj`, ...) with references in the same forms |
| `args` | further arguments, typed as payload values are (`now` is an `$ms`) |
| `reader` | optional: replaces the case's reader |
| `expected` | the expected answer, carried through untouched by the minter. Keys are written by key name, rows and objects by label. Where the answer is undecided, `{"undecided": {"names": <the row or object reference it waits on>}}`; where it is a refusal, `{"refused": "<reason token>"}`. |

## The first vector set

The cases the first set carries, one or more for each public function persist calls. Each comes from the named
model check and case; the vector restates its rows in the form above. These are not emitted yet: that lane
follows the merge of the lanes this map reads.

| # | Function | Case | From |
|---|---|---|---|
| 1 | `seat::Seats::holders`, `seat_rule` | three founders, a `duty_holders` map: each signer a member, the map's duties held | `check_duty_seats.py`: "three founders: each listed signer a member; A holds moderate and review, B moderate, C no duty" |
| 2 | `seat::Seats::holders` | one founder, no map: `member`, `moderate` and every declared duty | `check_duty_seats.py`: "one founder" |
| 3 | `seat::seat_rule` | a duty conferral on a key that is not a member seats nobody | `check_duty_seats.py`: "a conferral on a key that is not a member seats nobody" |
| 4 | `seat::seat_rule` (`delivery_order`) | the widening delivered after the conferral and its acceptance: the seat stands | `check_duty_seats.py`: "the widening lands after the conferral and its acceptance: the seat stands with no further row" |
| 5 | `seat::Seats::holders` | a resignation ends the member's duty seats | `check_duty_seats.py`: "a member's resignation ends its duty seats, with no withdrawal of each offer" |
| 6 | `seat::Seats::holders` | a counted removal ends them | `check_duty_seats.py`: "a counted removal from the roster ends them" |
| 7 | `seat::Seats::holders` | no revival after re-admission | `check_duty_seats.py`: "no revival: admitted again after its resignation, the key is a member and the old conferral does not seat it" |
| 8 | `seat::Seats::stands` | the counted grant seats its grantee | `check_delegation.py`: "the counted grant seats its grantee" |
| 9 | `seat::Seats::stands` | two consents: a hop the delegate has not accepted | `check_delegation.py`: "two consents: a hop the delegate has not accepted" |
| 10 | `seat::Seats::stands` | the depth cap | `check_delegation.py`: "depth: the link after the cap does not" |
| 11 | `seat::Seats::roster`, `count_members` | an agent seated: on the roster, no member | `check_agent_seat.py`: "an agent seated: on the roster, no member" |
| 12 | `seat::met` | an agent's signature is no voice | `check_agent_seat.py`: "three persons and an agent: one person and the agent sign an admission, one voice of three, and nothing is admitted" |
| 13 | `seat::seat_rule` | a private room's removed room key is not seated again | `check_room_keys.py`: "private: the room's count removes q, and an admission of the same room key with the removal in its past concludes …" |
| 14 | `seat::Seats::dissolved` | a dissolved group | `tests/fixtures/acts.json`, `dissolved` |
| 15 | `seat::members_at`, `met` | a re-admitted member is a voice | `check_readmit.py`: "a re-admitted member is a voice: of six, X admitted by A, B, C and D (4 of 6) is seated" |
| 16 | `seat::members_at`, `met` | a leaver is out of the base | `check_readmit.py`: "without the re-admission, the leaver is out of the base: of four, X admitted by A and B (2 of the 3 left) is seated" |
| 17 | `seat::seat_rule` (heads ruling) | a version beside the acknowledged one | `check_count_heads.py`: "a version extends the founding version with the acknowledged one in its past: a sibling of it, not behind …" |
| 18 | `seat::Seats::tips`, `tips_fold` | a leaving concurrent with a version: tips wait | `check_rosters.py`: "D's leaving concurrent with v2" |
| 19 | `seat::seat_rule` | a lone holder confers a declared duty alone | `check_rosters.py`: "one of two holders seats a declared duty alone" |
| 20 | `seat::seat_rule` (recall) | the recall's floor | `check_recall.py`: "three members: one other does not" |
| 21 | `seat::merge_concludes` (roster-merge) | a merge read for each side | `check_roster_merge.py`: "the halves met: R1 reads its own side (x2 void for it)" |
| 22 | `seat::merge_concludes` | a merge dropping a member never removed concludes nothing | `check_roster_merge.py`: "the content is fixed: a merge dropping L (never removed) concludes nothing" |
| 23 | `seat::seat_rule`, `seat::election_closed` | an election: three of five rank C first | `check_election.py`: "the count: three of five rank C first, C is seated" |
| 24 | `seat::seat_rule` | a seating with the seated moderator in its past | `check_election.py`: "C2: a seating with the seated moderator in its past concludes nothing …" |
| 25 | `ranked::ranked` | no majority, a tie for weakest | `check_ranked.py`: "A 5, B 3, C 1, D 1 of ten: no majority, and C and D, each holding a ballot, tie for weakest: nobody" |
| 26 | `seat::person_at` (key-person) | the first key of a self roster | `check_key_person.py`: "the first key of a self roster, at a row naming the roster" |
| 27 | `seat::person_at` | an evicted key: no person | `check_key_person.py`: "the third key evicted by the roster's count, at a row naming the eviction: no person" |
| 28 | `seat::person_at` | a key of two self rosters: none | `check_key_person.py`: "a key seated in two self rosters: two persons is none" |
| 29 | `seat::person_at` | a room key's person is its voice | `check_key_person.py`: "a room key of a voice: the voice is its person" |
| 30 | `seat::persons_of`, `met` | a device key speaks for its person | `check_key_person.py`: "a person's device key speaks for its person: met" |
| 31 | `key_end::well_formed`, `conclude_rule` | a rotation at the old record's end | `check_key_end.py`: "a rotation whose old-key instant is the old record's end" |
| 32 | `key_end::conclude_rule` | a rotation without the old key's signature | `check_key_end.py`: "P5b a rotation without the old key's signature is not kept" |
| 33 | `key_end::retained` | a dead key's row a live row names | `check_key_end.py`: "P3b compacting keeps a dead key's row that a live row names" |
| 34 | `key_end::live` (`first_held_at`) | a renewal held before the record's end | `check_key_end.py`: "T2 live when first held: the renewal counts only if this node held it before the record's end" |
| 35 | `key_end::counts_by` (key-end-retained) | an expired key's in-time vote counts | `check_key_view.py`: "an expired key's in-time vote: E's record ends at 4, x signed at 3 under it (no end row): E counts" |
| 36 | `key_end::counts_by`, `seat::met` | a cosigner's self-revocation drops its voice | `check_key_view.py`: "a cosigned row: C, one cosigner, revoked itself after 2 (naming nothing); x signed at 3: C's voice drops, …" |
| 37 | `root::Root::grant` | a grant's count short | `check_root.py`: "the grant's count is short: h1 alone of three" |
| 38 | `root::Root::grant` | a grant by removed holders | `check_root.py`: "G4: a grant by removed holders h1 and h2 naming b0, the reader at b2: no voices in force, refused" |
| 39 | `root::Root::grant` | charters differ, both carrying the duty | `check_root.py`: "charters differ, both carrying the duty: h1, h2 and h4 on s1 resolve" |
| 40 | `root::Root::in_force`, `fold` | two successors with one charter fold | `tests/fixtures/root_reader.json`: "fold: two successors with the same charter fold: …" |
| 41 | `root::Root::in_force` | a forked join | `tests/fixtures/root_reader.json`: "join: a forked join: two joins of s1 and s2 under different charters are contested: …" |
| 42 | `root::Root::halt_in_force` | a halt counts nobody | `tests/fixtures/root.json`: "attack: a halt counts nobody: h1's halt at b0 still halts for that reader …" |
| 43 | `seat::recovery_verdict` | a stalled room's recovery, read over the founders | `check_root.py`: "stalled is read over the founders, whatever scope the widening states: live, counted `member`" |
| 44 | `trust_rows::read_licence` (charter) | the reader's own edge to a key authority | `check_trust_rows.py`: "the reader's own edge to a key authority, its licence signed by it" |
| 45 | `trust_rows::edges_of` | a roster key's seat not in the edge's past | `check_trust_rows.py`: "(a) the roster key's seat not in the edge's past: not the reader's" |
| 46 | `trust_rows::edges_of` (`unsorted_set` fault) | `trust_classes` not sorted | `check_trust_rows.py`: "trust_classes not sorted: refused" |
| 47 | `trust::reaches` | a cycle visited once | `check_trust_rows.py`: "a cycle is visited once and the walk goes on" |
| 48 | `trust_rows::edges_of` | a community with no duty holder signs no edge | `check_trust_rows.py`: "(a) a community with no duty holder: LOCKED, no edge, whatever the members sign" |
| 49 | `charter::declared` | a founding record's licence classes | `check_charter.py`: "the founding record declares its classes, each with its legal weight" |
| 50 | `charter::declared` | a change decided with the official's countersign | `check_charter.py`: "and with its designated official's countersign naming the change, decided: legal is added" |
| 51 | `audience::audiences`, `place` | a room row's audience | `check_audience.py`: `default_room` |
| 52 | `audience::place` | a row pinned to the commons | `check_audience.py`: `pinned_commons` |
| 53 | `audience::history_of` | a row stating `history_on_join` `full` | `check_audience.py`: `history_row_full` |
| 54 | `audience::seats_of` | a duty seat outside the room | `check_audience.py`: `duty_seat_outsider_refused` |
| 55 | `content::answers` | a removal naming the member's tip | `tests/fixtures/conferral_content.json`: `removal_names_tip` |
| 56 | `content::answers` | a removed member keeps posting | `tests/fixtures/conferral_content.json`: `removed_member_keeps_posting` |
| 57 | `content::answers` | a keeps row waits for its end | `tests/fixtures/conferral_content.json`: `adding_row_waits_for_its_end` |
| 58 | `window::outcome`, `unwithdrawn` | a ballot withdrawn beside a second vote | `window_adversary.tsv` (read by `check_window_rows.py`): "a member votes for and against and withdraws the vote against, beside a second vote for: the landing names the four" |
| 59 | `window::outcome` | a false landing that leaves objections unnamed | `window_adversary.tsv`: "false landing: the thief (one device of three) lands an eviction of the owner's device; …" |
| 60 | `seat::act_in_force` (charter) | a lone takedown in force | `check_lone_acts.py`: "a takedown by a takedown holder, alone, at the newest change: concluded and in force" |
| 61 | `seat::act_in_force` | its signer lays the duty down after it | `check_lone_acts.py`: "its signer lays the takedown duty down after it: counted at its own head, out of force from there (E2)" |
| 62 | `seat::seat_rule`, `lone_act_duty` | a release by a key with no slash duty | `check_lone_acts.py`: "a release by a key holding no slash duty concludes nothing" |
| 63 | `seat::act_in_force` | a lone removal with no end held | `check_removal_in_force.py`: "the removal with no end held: in force, the agent out" |
| 64 | `seat::act_in_force` | another holder's receipt keeps it | `check_removal_in_force.py`: "the same with a receipt by another holder: in force" |
| 65 | `conferral::answers` | an act at the end's head | `tests/fixtures/conferral_end.json`: `forward_at_end_head` |
| 66 | `standing::answers` | an act naming its bundle and its acceptance | `tests/fixtures/conferral_two.json`: `names_bundle_and_acceptance` |
| 67 | `standing::answers` | a backdated act after an act under the new owner | `tests/fixtures/conferral_two.json`: `backdated_after_an_act_under_the_new_owner` |

Four of these also carry a deliberate fault, so the minted set exercises each fault kind against a known
answer: case 15 with one voice `bad_signature_half` (the count is then short), case 46 (`unsorted_set`, as the
model states), case 8 with the grant's `missing_member` `payload.refs.head` (the grant then names no head), and
case 31 with the rotation's old-key statement `wrong_signer` (the rotation then carries no old-key signature).
Each faulted variant's expected answer is the crate's over the statements the door admits, and is written when
the vector is.

With the Constitution's rulings (WIRE_MAP.md, the findings and the guessed mappings), cases 43, 58 and 59 can be
minted: the recovery widening names its grant under `refs.also.stands_on` (N3), and a landing's outcome is derived
from its leaf (N6). The election cases (23, 24) mint with the ballots naming their election by `row-ref` and the
seating citing its set (G12, G13). Two rulings meet how the crate reads its rows:
- G9: a `membership:resignation` names no target, while the crate's `Withdraw` reads `target()`. Case 16 is
  unaffected: its founder leaves by a `withdraws` of the founding record, which has a target (N2). Cases 5 and 7
  model the leaver withdrawing the widening that seats it; on the wire that is a `membership:resignation` (no
  target) or a `withdraws` of the leaver's own acceptance, and which form the vector uses waits on the lead.
- G15 is bridged: case 50 mints the countersign as a further statement over the act's own payload, and the store
  presents it as a `Countersign` row view (WIRE_MAP.md G15).
