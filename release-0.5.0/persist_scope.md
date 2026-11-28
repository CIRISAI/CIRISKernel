# What 0.5.0 does for persist's asks

Each row of persist's asks, items 4 to 18 and Q8, is marked one of three ways:
- **IN 0.5.0**: the crate function that answers it, and its file in `crates/ciris-kernel/src/`.
- **CALLER** or **VERIFY**: persist's or Verify's duty, with the `ADOPTING.md` section.
- **NOT IN THIS TAG**: the adopter holds these shut, or keeps only a causal fold; no fold decides a verdict from a
  stated instant or the host clock.

The verdicts are review-54's audit, read on release-0.5.0-wip, with the lead's corrections. Names were checked on
release-0.5.0-wip be4c494 and later.

**Finality.** Only `head::purge` over `head::Entry` rows (`head.rs`) says what may become a stub. No seat, content or
window answer returns a "final" bit, so persist prunes nothing on its own judgement.

**The re-ask contract.** Where an answer is `Undecided`, or a refusal names a row that is not held, re-ask once that
row is held. That covers `seat::seat_rule_why`, `window::rule_why` and `window::rule_bound_why`, and `Held::lacks`
(`held.rs`). Present real rows only. Nothing is synthesised, no head is made up by the store, and no stored verdict
comes back in as a row field (`ADOPTING.md`, "The wire map, and how to call").

## Items 4 to 18

| # | Ask | Verdict | Where |
|---|---|---|---|
| 4a | growth needs the member's own reply | IN 0.5.0 | the two consents in the seat walk: `seat::Seats::holders`, `Seats::roster` (`seat.rs`) |
| 4b | the withdrawal of an offer or an acceptance | IN 0.5.0 | ends by ancestry in `seat::Seats` (`seat.rs`) |
| 4c | proposal expiry | IN 0.5.0, at a stated instant the caller gives | `Dated::valid_until`, `covers_at` (`lib.rs`); `Seats::holders_at`, `Seats::stands_at` (`seat.rs`) |
| 4d | the decline of an invitation | NOT IN THIS TAG | the family exists (TEXT, N1: `membership:decline:v1`); the crate reads it for election seatings only (`SeatKind::Decline`); invitations are a 0.5.1 candidate |
| 4e | live invitees (pending offers) | NOT IN THIS TAG | the seat walk gives live seats only; a 0.5.1 candidate (a query) |
| 4f | the `community_invite` window path (one proposer, 72 h) | NOT IN THIS TAG | after the tag, by Eric's ruling |
| 5-6a | objections, the window, the reverse-quorum fold | IN 0.5.0 | `window::outcome` (`window.rs`); the spec from the pinned table: `window::spec_from_policy` (`window.rs`) and `tables::law_from_tables` (`tables.rs`), pin 85750784, so persist maps no table |
| 5-6b | dismissals | NOT IN THIS TAG | no rule in any branch |
| 5-6c | a steward tier | NOT IN THIS TAG | only HOLDS owner → steward |
| 5-6d | the two-path lone act after a silent window | IN 0.5.0 | `window::outcome` with `silent` and `at_close` (`window.rs`): the self roster's lone add and evict |
| 5-6e | its governance-policy and node-state instances | IN 0.5.0 for the policy rows (`spec_from_policy`); NOT IN THIS TAG for node state | node state has no spec |
| 5-6f | cosign holds | IN 0.5.0 | `seat::voices` (`seat.rs`: a cosign row is a voice of the counted row that names it); root grants' `cosign` (`root.rs`) |
| 5-6g | the expiry of a cosign hold | NOT IN THIS TAG | no instant is read and nothing lapses it |
| 10a | the rotation chain, rival rotations | IN 0.5.0 | `key_end::successor` (rivals give none), `live`, `ended`, `retained`, `counts`, `counts_by` (`key_end.rs`) |
| 10b | who may revoke | IN 0.5.0 | `key_end` (`key_end.rs`): only the key's own revocation; the owner's revocation ends the owner binding only (`standing.rs`) |
| 10c | when a key's statements become suspect | IN 0.5.0 | the end rule: `key_end::counts`, `counts_by` (`key_end.rs`); a row lapses when its key ends |
| 10d | the withdrawal of an occurrence | NOT IN THIS TAG | no rule |
| 11a | the delegation walk and its terms | IN 0.5.0 | `seat::Seats::stands` (`seat.rs`: depth 5, attenuation, the sub-delegation gate, two consents); edge terms in `trust_rows::edges_of` (`trust_rows.rs`); a chain from a root grant (`seat.rs`, `root.rs`) |
| 11b | steward bindings | IN 0.5.0 | `seat::Seats::one` (`seat.rs`), `standing::answers` (`standing.rs`) |
| 11c | moderators (named, appointed, their reach) | IN 0.5.0 | moderate seats, `duty_confer`, the election (`seat/election.rs`), lone removals, the lift (`seat.rs`) |
| 11d | duty holders | IN 0.5.0 | `seat::Seats::holders` over the duty scopes, the duty gate, the duty count (`seat.rs`) |
| 11e | the slash decider; quarantine, slash, takedown | IN 0.5.0 | `seat::act_in_force` (`seat.rs`), the `quarantine`, `slashing` and `takedown_notice` rows, `reconsideration_rule` |
| 11f | licence reach and issuance | IN 0.5.0 | `trust_rows::read_licence` (`trust_rows.rs`: issuer standing at issuance, by ancestry); `charter::declared` (`charter.rs`) |
| 11g | `admission:unit` (count, lease, walk) | NOT IN THIS TAG | only a family name in the audience table |
| 11h | the trusted-service rule for receipts | NOT IN THIS TAG | no rule; validating a service's signed receipt would be Verify's |
| 11i | location proofs for a geographic charter | VERIFY for the proof; NOT IN THIS TAG for the charter class | |
| 14 | who is served, as one function | IN 0.5.0 | `audience::place`, `audience::audiences`, `audience::carried` (`audience.rs`); `seat::person_keys`, `seat::nodes_of` (`seat.rs`): the node set = audiences ∘ person_keys ∘ nodes_of |
| 15a | ownership: the binding in force | IN 0.5.0 | `standing::answers` (`standing.rs`: a re-binding ends the one before), `seat::Seats::one` (`seat.rs`) |
| 15b | reclaim by an abandonment window; rebinding after reclaim | NOT IN THIS TAG | no rule |
| 15c | grant issuer chains | IN 0.5.0 | root grants over the bundle in force (`root.rs`); issuer standing (`trust_rows.rs`); a chain from a root grant (`seat.rs`) |
| 16a | a steward purge as a counted act (holder check, majority, notice window, selection closure, tombstone void) | NOT IN THIS TAG | no acts row and no `act_of` arm; its void for a reader who acknowledged a successor not holding it is already the reader's line |
| 16b | under it: stubs, settled | IN 0.5.0 | `head::View::settled`, `closed_for_me`, `missing`, and `head::purge` (`head.rs`): finality only through `head::purge` over `head::Entry` rows |
| 17a | the quarantine fold; takedown and reconsideration standing | IN 0.5.0 | `seat::act_in_force`, `reconsideration_rule`, `seat::countersigned` (`seat.rs`) |
| 17b | duty edges void for a minor; the age-band fold | NOT IN THIS TAG | only an `assure:age` seat; a 0.5.1 candidate |
| 18a | the `mesh_config` fold and its root quorum | NOT IN THIS TAG | the root count beneath it is in the crate (`root.rs`, `RootReading`) |
| 18b | the "strictly wider" crossing checks | NOT IN THIS TAG | a single-row check against the one row it names; not built |
| 18c | the consent peer set | IN 0.5.0 | `consent::in_force`, `peer_set`, `may_send`, `replication_set` (`consent.rs`) [at the tag: add `consent::Reading` once consent-set merges] |

## Q8

| Item | Verdict | Where |
|---|---|---|
| accord m-of-n and the halt count | IN 0.5.0 | `accord_majority` and `accord_halt` through the acts table and the seat count (`seat.rs`); the window's halt fuse (`window.rs`); `root::RootReading::halt_in_force` (`root.rs`) |
| the rotation chain and who may revoke | IN 0.5.0 | `key_end` (`key_end.rs`) |
| the trusted-service rule for receipts | NOT IN THIS TAG; VERIFY for its verification part | |
| `admission:unit` | NOT IN THIS TAG | |
| location proofs | VERIFY for the proof; NOT IN THIS TAG for the charter class | |
| the age band | NOT IN THIS TAG | |
| the quarantine fold | IN 0.5.0 | `seat::act_in_force` (`seat.rs`) |
| ownership reclaim | NOT IN THIS TAG | |
| the `mesh_config` quorum | NOT IN THIS TAG | the root-quorum basis is in the crate (`root.rs`) |

## Also in 0.5.0

- The wire map, and the 70 neutral vectors Verify mints: `WIRE_MAP.md` and `VECTORS.md`.
- The election close: `seat::election_closed` (`seat/election.rs`).
- The re-ask contract above.

## Fixtures with rows and answers

`tests/fixtures/`: `seat.json`, `acts.json`, `key_end.json`, `tables.json`, `purge.json`, `root.json`, `root_reader.json`,
`audience.json`, `resignation.json`, `charter.json`, `trust_rows.json`, `root_chains.json`, `key_person.json`,
`room_keys.json`, `roster_merge.json`, `key_end_counts.json`.
