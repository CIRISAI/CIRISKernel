# The wire map: `consent::ConsentRow`

This is the `consent::ConsentRow` entry of [`WIRE_MAP.md`](WIRE_MAP.md) (section 7, after `head::Entry`). It is
kept in its own file because `WIRE_MAP.md` lives on the `wire-map` lane; fold it in there when that lane merges.
Markers are those of `WIRE_MAP.md` (**D** derived by the store, **L** store-local, **NO WIRE FAMILY**).

Source: the Constitution at `origin/rc23-next`, CC 3.3.7 (the grant's shape and its conformance shape), CC 3.5.1
(the fold), CC 2.4.1.1 (withdrawal), CC 3.3.5 (`valid_until`). The grant is a bare `scores` Contribution, the
dimension `consent:replication:v1`, its parameters payload-level under `subject_kind: "consent_replication"`.
`manifests/family_payloads_v2.cddl` at `rc23-next` has no `ceg-row/2` payload for it, so the fields below are the
Contribution's own; a `ceg-row/2` mapping waits on that payload (a question for the Constitution).

| Accessor | Wire source | Notes |
|---|---|---|
| `id`, `signer` | row id; `attesting_key_id` (G, the granting node or its owner) | `witness_relation` must be `self`; a grant otherwise is not conformant and is not presented |
| `names` | the digests the row names (`references_attestation_id` on a `withdraws`/`recants`/`supersedes`) | |
| `kind` | `Grant`: dimension `consent:replication:v1`. `Withdrawal`: a `withdraws` or `recants` whose `references_attestation_id` is a grant. `Revocation`: the key's own revocation (`key_end::KeyEndRow::revocation`). `Other`: any other row | **D** |
| `peer` | the one entry of `subject_key_ids` | a grant naming none or several is not conformant (CC 3.3.7, "the **single** recipient peer"): present `peer()` as `None` and it concludes nothing |
| `classes` | payload `attestation_prefixes`, as signed | `conclude_rule` refuses a list that is not sorted ascending and deduplicated; an entry ending in `:` is a namespace prefix, any other a corpus `subject_kind` class name |
| `at` | `asserted_at` | the fold's instant, compared only among one signer's grants to one peer |
| `until` | `valid_until` (envelope, optional) | the term, read at the caller's `now` |
| `withdraws` | the withdrawal's `references_attestation_id` | the grant it retracts, whole |
| `revocation` | the key record lane's revocation: the key and its `revoked_after` | only the key's own is read |

Not read: `score` (magnitude is not load-bearing), `cohort_scope`, `topical_relation: bilateral_pair` (pairing is the
consumer's), `grants: "replication"` (a constant), and the `cohorts` allow list of an owner's grant for its own node
(CC 6.1.5.3). The owner the answers take is `seat::Seats::one("owner", node)` over the reading row's past, from the
owner binding's own rows (`WIRE_MAP.md` section 7.2).
