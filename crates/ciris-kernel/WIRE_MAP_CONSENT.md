# The wire map: `consent::ConsentRow`

This is the `consent::ConsentRow` entry of [`WIRE_MAP.md`](WIRE_MAP.md) (section 7, after `head::Entry`). It is
kept in its own file because `WIRE_MAP.md` lives on the `wire-map` lane; fold it in there when that lane merges.
Markers are those of `WIRE_MAP.md` (**D** derived by the store, **L** store-local, **NO WIRE FAMILY**).

Source: the Constitution at `origin/rc23-next`, CC 3.3.7 (the grant's shape and its conformance shape), CC 3.5.1
(the fold), CC 2.4.1.1 (withdrawal), CC 3.3.5 (`valid_until`). The grant is a bare `scores` Contribution, the
dimension `consent:replication:v1`, its parameters payload-level under `subject_kind: "consent_replication"`.
`manifests/family_payloads_v2.cddl` at `rc23-next` has no `ceg-row/2` payload for it. The Constitution has stated
the payload (the schema rule comes later):

| Where | Member | Rule |
|---|---|---|
| payload | `subject_kind` | `"consent_replication"` |
| payload | `grants` | `"replication"`, a constant |
| payload | `attestation_prefixes` | a sorted, deduplicated set of text: an entry ending in `:` is a namespace prefix, any other a corpus class name |
| payload | `cohorts` (optional) | a sorted set of `{scope, target}`, `scope` one of `self`, `family`, `community`, `affiliations`; `target` the group's key id, absent on `self`. Empty means explicitly none; absent means the class default. Only on an owner's grant for one of its own nodes, which is placed at `cohort_scope: self` |
| envelope | `subject_key_ids` | exactly one entry, the peer P |
| envelope | `witness_relation` | `self` |
| envelope | `valid_until` (optional) | the term |
| envelope | `cohort_scope` | `federation`; `self` on an owner's `cohorts` grant; held between the two nodes where either is unannounced |

| Accessor | Wire source | Notes |
|---|---|---|
| `id`, `signer` | row id; `attesting_key_id` (G, the granting node or its owner) | `witness_relation` must be `self`; a grant otherwise is not conformant and is not presented |
| `names` | the digests the row names (`references_attestation_id` on a `withdraws`/`recants`/`supersedes`) | |
| `kind` | `Grant`: dimension `consent:replication:v1`. `Withdrawal`: a `withdraws` or `recants` whose `references_attestation_id` is a grant, signed by the grant's signer, its peer or the signer's owner. `Revocation`: the key's own revocation (`key_end::KeyEndRow::revocation`). `Announcement`: a node's own announcement (CC 5.4.6). `Other`: any other row | **D** |
| `federation` | `cohort_scope == "federation"` | a grant at federation scope concludes only where its signer and its peer have announced in its past |
| `peer` | the one entry of `subject_key_ids` | a grant naming none or several is not conformant (CC 3.3.7, "the **single** recipient peer"): present `peer()` as `None` and it concludes nothing |
| `classes` | payload `attestation_prefixes`, as signed | `conclude_rule` refuses a list that is not sorted ascending and deduplicated; an entry ending in `:` is a namespace prefix, any other a corpus `subject_kind` class name |
| `at` | `asserted_at` | the fold's instant, compared only among one signer's grants to one peer |
| `until` | `valid_until` (envelope, optional) | the term, read at the caller's `now` |
| `withdraws` | the withdrawal's `references_attestation_id` | the grant it retracts, whole |
| `revocation` | the key record lane's revocation: the key and its `revoked_after` | only the key's own is read |

Not read: `score` (magnitude is not load-bearing), `topical_relation: bilateral_pair` (pairing is the
consumer's), `grants: "replication"` (a constant), and the `cohorts` allow list of an owner's grant for its own node
(CC 6.1.5.3). The owner the answers take is `seat::Seats::one("owner", node)` over the reading row's past, from the
owner binding's own rows (`WIRE_MAP.md` section 7.2); the owner `conclude_rule` asks for at a withdrawal is the same
reading over the withdrawal's own past.
