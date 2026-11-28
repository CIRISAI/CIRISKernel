# Persist's items 4 to 18 and Q8: verdicts for the 0.5.0 release (review-54)

Read on release-0.5.0-wip 3453c7d / 11804e1 plus the lanes, 2026-11-28. Verdicts: **crate** (the crate answers it in
0.5.0), **crate (lane)** (on a lane branch, not yet merged into wip), **caller/Verify**, **not in this tag**.
[plan] marks an addition the tag plan put into 0.5.0; the lead reports all three built (2026-11-28), not re-read by me.

| # | Ask (one line) | Verdict | Crate names / why |
|---|---|---|---|
| 4a | growth needs the member's own reply | crate | two consents: Seats pairing (offer plus the key's acceptance, or its signature on the offer); Seats::holders / roster |
| 4b | an offer's or acceptance's withdrawal | crate | Seats (ends by ancestry); left_in_past, stay_ended_in_past |
| 4c | proposal expiry | crate, at a stated instant | Dated::valid_until, covers_at; Seats::holders_at / stands_at |
| 4d | invitation decline | not in this tag | decline exists only for the election (SeatKind::Decline); 0.5.1 candidate |
| 4e | live invitees (pending offers) | not in this tag | Seats exposes live seats only; 0.5.1 candidate (a query) |
| 4f | the community_invite window path (one proposer, 72 h) | not in this tag | post-tag (Eric) |
| 5-6a | objections, the window, the reverse-quorum fold | crate, given the caller's WindowSpec | window::outcome (at-once / at-close counts, cancel fractions); landings by window:held / window:landed rows. [plan] spec_from_policy / law_from_tables (lane policy-spec) |
| 5-6b | dismissals | not in this tag | nothing in any branch |
| 5-6c | a steward tier | not in this tag | only HOLDS owner -> steward |
| 5-6d | the two-path lone act after a silent window | crate (shape) | window::outcome with `silent` and at_close (self_roster_add / evict, proposal@others) |
| 5-6e | its governance-policy and node-state instances | caller (spec) / not in this tag | per-family specs are the caller's WindowSpec; node state has no spec |
| 5-6f | cosign holds | crate | seat::voices (a cosign row naming every head is a voice of the counted row that names it); root grants' `cosign` (root-fold) |
| 5-6g | cosign-hold expiry | not in this tag | no instant read; nothing lapses it |
| 10a | rotation chain, rival rotations | crate | key_end::successor (rivals give none), live / ended / live_at / ended_at, retained; key_end::counts / counts_by (key-end-retained lane) |
| 10b | who may revoke | crate | key_end: only the key's own revocation; standing.rs: the owner's revocation ends the owner binding only |
| 10c | when a key's statements become suspect | crate | the end rule: key_end::counts / counts_by, revoked_after; a row lapses when its key ends (retained) |
| 10d | occurrence withdrawal | not in this tag | no rule |
| 11a | delegation walk and terms | crate | Seats::stands (depth 5, attenuation, sub-delegation gate, two consents); edge terms: trust_rows (charter lane); chain from a root grant (persist-gaps) |
| 11b | steward bindings | crate | Seats::one, ender, standing::answers |
| 11c | moderators (named, appointed, reach) | crate | moderate seats, duty_confer, seat::election, lone removals, out_of_force, the lift |
| 11d | duty holders | crate | Seats::holders("duty"), duty_gate, the duty count |
| 11e | slash decider; quarantine, slash, takedown | crate (lane) | seat::act_in_force, quarantine / slashing / takedown_notice rows, reconsideration_rule (persist-gaps / charter) |
| 11f | licensure reach and issuance | crate (lane) | trust_rows (issuer standing at issuance, by ancestry), charter::declared, trust::Charters, honours (charter) |
| 11g | admission:unit (count, lease, walk) | not in this tag | only a family name in the audience table |
| 11h | the receipts' trusted-service rule | not in this tag | nothing in any branch; validating a service's signed receipt would be Verify's |
| 11i | location proofs for a geographic charter | caller/Verify (proof); not in this tag (charter class) | |
| 14 | who is served, as one function | crate (lane) for keys; nodes the store's | audience::place / audiences / carried (audience lane). [plan] seat::person_keys, seat::nodes_of (key-person lane) |
| 15a | ownership: the binding in force | crate | standing::answers (re-binding ends the one before), Seats::one, ender |
| 15b | reclaim by abandonment window; rebinding after reclaim | not in this tag | no rule |
| 15c | grant issuer chains | crate (lanes) | root grants over the bundle in force (root.rs, merged at 11804e1); issuer standing (trust_rows, charter); chain from a root grant (persist-gaps) |
| 16a | steward purge as a counted act (holder check, majority, notice window, selection closure, tombstone void) | not in this tag | needs an acts row plus an act_of arm; its void for a reader who acknowledged a successor not holding it is already the reader's line |
| 16b | under it: stubs, settled, finality | crate | head::View::settled / closed_for_me / missing, head::purge (finality only through head::purge over head::Entry rows) |
| 17a | the quarantine fold; takedown and reconsideration standing | crate (lane) | act_in_force, reconsideration_rule, needs_countersign / countersign_ok (persist-gaps / charter) |
| 17b | duty edges void for a minor; the age-band fold | not in this tag | only an `assure:age` seat (CONFERS root); 0.5.1 candidate |
| 18a | the mesh_config fold and its root quorum | not in this tag | the root count beneath it is crate (root.rs RootReading) |
| 18b | "strictly wider" crossing checks | not in this tag | a single-row check against the one row it names; not built |
| 18c | the consent peer set | [plan] crate (lane consent-set) | in_force, peer_set, may_send (consent-set 6a5c8c0) |

## Q8: whose each is

| Item | Verdict |
|---|---|
| accord m-of-n and the halt count | crate: accord_majority / accord_halt via the acts table and the seat count; window halt_fuse; root::RootReading::halt_in_force |
| rotation chain and who may revoke | crate: key_end |
| the receipts' trusted-service rule | not in this tag (verification part: Verify) |
| admission:unit | not in this tag |
| location proofs | caller/Verify (proof); charter class not in this tag |
| age band | not in this tag |
| quarantine fold | crate (lane: persist-gaps / charter) |
| ownership reclaim | not in this tag |
| mesh_config quorum | not in this tag (root-quorum basis is crate, root-fold) |

## Fixtures with rows and expected answers

- wip: seat.json, acts.json, key_end.json, tables.json, purge.json, root.json, root_reader.json.
- lanes: audience.json, resignation.json, charter.json, trust_rows.json, root_chains.json, key_person.json, room_keys.json, roster_merge.json, key_end_counts.json.

Release-note wording (tag plan): "not in this tag: the adopter holds these shut, or keeps only a causal fold; no fold
decides a verdict from a stated instant or the host clock".
