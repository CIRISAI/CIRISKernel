# CC 2.4.1.1 at rc22 850ed50, and `names_head` at 76c4550, read against the model

I read the Constitution's text at `850ed50` and the family model at `76c4550` with `git show`. Nothing in that
repository was changed. They are read against:
- E1 to E8 and section G of `CONFERRAL_END.md`;
- the spec `ConferralEnd.tla`;
- the reference `models/causal_kernel/conferral_end.py` and its case table
  (`crates/ciris-kernel/tests/fixtures/conferral_end.tsv`).

Each finding quotes the sentence and says what the model says. They are listed most consequential first.

## Findings that change an answer

**1. Acts that name no head: the text refuses the rows persist already holds.**

> "A row that exercises a standing and names no head concludes nothing, `act_names_no_head`."

The model counts an act that names no head at its own head and holds it out of force once an end is held,
unless it is receipted. That is the fixture's `uncited_act` (E2.forward) and `uncited_act_receipted`
(E8.receipt). Every act persist signed before this change is such a row. Read literally, the sentence makes
all of them conclude nothing, retroactively. That is against CC 4.5.5 ("Acts already taken under the duty
stand") and against "The end never undoes that count".

Needed: scope the refusal to rows of the new wire version. A row of an earlier version that names no head is
read as the model reads it: concurrent with every end, never at a later head, so counted, and not in force
after an end unless receipted.

**2. A receipt must not keep in force an act at a later head.**

> "*What stays in force.* An act stays in force after the end where a clean receipt of it is held that does
> not have the end in its past"

It is unqualified. The model applies receipts only to acts that count: E3 decides before E8, an act at a head
later than `h_e` does not count, and no receipt revives it (`Inv_ReceiptForwardOnly`). The text's closing "it
revives no act" can be read as covering this, but "revives" is not defined. An implementer may also read the
one-say sentence ("Where the ender holds a clean receipt of such an act concurrent with the end, the act counts
at its own head") together with "What stays in force". The ender's concurrent receipt is the conferrer's
receipt, so that reading would also put the act in force.

Needed:
- "an act that counts at the end's head or an older or concurrent one stays in force …";
- for the one say, "counts at its own head, and is not in force".

**3. The end of a receipter's role is stated by instant, and it has no row.**

> "A receipter's receipt made after the body ended its role keeps nothing."

"Made after" is an instant. The model's rule is causal: a receipt that has the body's end of the role in its
past keeps nothing, and one concurrent with it keeps (`Inv_ReceipterAfterItsEndNothing`,
`Inv_ReceipterBeforeStands`).

The wire also has no row that ends the role. `receipter` is a field on the offer, so ending the role means
withdrawing or superseding the offer, and that ends the grant. The model has a separate row (Rx) that ends the
receipter's seat and leaves the grant.

Needed:
- "a receipt that has the end of the receipter's role in its past keeps nothing";
- either a row that ends the role, or a rule that superseding the offer without `receipter` ends it.

**4. `lifts`: "one's own end" in 2.4.1.1, "one voice" in the wire table.**

> "One's own end lifts nothing, and `lifts` on it is refused, `lifts_on_own_end`." (2.4.1.1)

> "Present only as true. On an end signed by one voice it is refused, lifts_on_own_end." (wire table)

These are different sets. A conferrer that is a single key, ending a grant it made, is not ending its own
standing, but it signs with one voice. Under the wire wording it cannot lift a co-holder's receipts after a
compromise.

The model, section G, lets the conferrer's end carry `lifts` and ignores `lifts` on a self end. Refusing a self
end that carries `lifts` is stricter and safe: the resignation concludes nothing, and the resignee signs it
again without the flag.

Needed:
- one wording;
- a decision on whether a single-key conferrer may lift.

**5. `under` is on the wire, and no rule reads it.**

> "the also role under, a set of exactly one" (commit 850ed50; refs table: "ack, cites or under; each list a
> set, and under a set of exactly one")

The recommended design needs no `under`. Under ANY-STANDING, which the text adopts ("An act that another live
standing of its signer authorises at its head stands on that standing"), no answer depends on it. If a reader
used `under` to bind an act to one standing (BOUND), it would contradict that sentence; that is the trace
`ConferralEnd_tie_any`.

Needed: say `under` is attribution only and no rule reads it, or drop it. Making it required costs the 47
producer sites the design avoided.

## Findings of wording or scope

**6. "does not count", when another standing authorises the act.**

> "An act with the end in its past does not count."

This holds only for the ended standing. Under the text's own "Another standing" paragraph, an act that names
the end stands on a second live standing: the fixture's `tie_any_standing`, rule E7.other_standing, decides
first.

Suggested: "does not count under the ended standing".

**7. The old sentence in 4.5.5 still voids concurrent acts.**

> "A `withdraws` against *any* `delegates_to` in the chain invalidates everything downstream of it, *for every
> act that has the withdrawal in its own past or is concurrent with it*"

The new 2.4.1.1 paragraph rereads "the two sentences above", the ones in 2.4.1.1. This sentence is in Part 4,
and it still says a concurrent act is invalidated. The model never voids an act at or before `h_e` (E2,
`Inv_ForwardNeverVoidsAtOwnHead`).

Suggested: "… is not in force from the withdrawal's head on, read as CC 2.4.1.1 the end of a standing reads it".

**8. `act:ack`: who signs, and its head.**

> "the signer acknowledges the acts it names under `refs.also` `ack`, at the head it names in `refs.head`."

> "**Yes:** a voice at the head the acts name; never the signer of an act it names, and never a node"

> Appendix card: "attest | member | selfAct"

- **The model gives a receipt no head.** A receipt is read by its causal past alone: it must not have the end
  in its past, and it must not be cut by a key removal. A head on it is harmless.
- **"A voice at the head the acts name" is too narrow.** It shuts out two receipters the model needs. The
  offer's receipter is not a member of any roster: a CI worker's owner, for instance. Under a root grant, the
  conferrer is a count of bundle holders.
- **It leaves acts that name no head unreceiptable.** "the head the acts name" does not exist for them, yet
  `uncited_act_receipted` keeps such an act in force.
- **The card's "member" is narrow in the same way.**

Suggested: "the conferrer (a count where the conferrer is one), another holder of the body the acts were done
for, or the receipter the offer names".

**9. Counted receipts and the line.**

> "This line is for counted rows: a version, a vote, a cut and the end of a standing."

An `act:ack` signed by a body's count is a counted row, so the line reaches it. A reader that acknowledged a
newer head would hold void a counted bulk receipt naming an older head, and the acts it covers would drop out
of force for that reader. The model does not apply the line to receipts.

Suggested: name receipts as not reached, or accept it and say so. The end of a standing being listed is right:
the model applies the line to every end (E5).

**10. One's own end is not a counted row.**

> "This line is for counted rows: a version, a vote, a cut and the end of a standing."

A withdrawal of one's own acceptance is authored, signed by one voice, so "counted rows" does not fit it. The
model applies the line to it all the same.

Suggested: "counted rows and every end of a standing".

## What matches the model

| Text (850ed50) | Model |
|---|---|
| "The head is the newest its signer holds of the record that seats the standing … For a grant from a root it is the bundle in force. Where one row between two keys is the whole record, as an owner-binding is, that row is the head." | `persist_root_grant`, `persist_owner_binding`; section D |
| "That head is the newest its signer holds, and an end with a newer head in its own past concludes nothing, `end_names_old_head`." | E1, `end_stale_head` |
| "The end concludes under its signer's own standing at that head, so one's own acceptance is withdrawn by one's own signature." | E5 |
| "It reaches the acts exercised under its target, a deputy's among them. It never reaches the members counted at any head" | E6, `deputy`, `Inv_MembersByPast` |
| "An act at the end's head, at an older head or at a concurrent one counts at its own head, and from the end's head on it is not in force. The end never undoes that count." | E2, `Inv_ForwardNeverVoidsAtOwnHead`, `Inv_EndNeverUnmakes` |
| "An act at a later head finds the standing ended and does not count." | E3 |
| "The receipt is the conferrer's, another holder's of the body …, or that of a receipter the offer names … never the act's own signer's and never a node's. A count that ends a standing MAY state `lifts`, and then only the count's own receipts keep an act in force." | E8, section G; plants `self`, `selflift` |
| "A receipt changes what is in force, never what counted" | `Inv_ReceiptsChangeOnlyForce` |
| "*The limit.* … No reader can tell it from an honest earlier act, and no rule here tries." | `persist_behind_node` |
| 2.7.8: "It does not reach an authored act that names its head, which counts at that head whatever head a reader has acknowledged." | `Inv_AsOfStands`, `ConferralEnd_line_acts` |
| 4.5.5: "What stays in force after a seat ends is what a receipt covers" | E8 |
| refs.head "on a counted row, on a roster version, and on a row that exercises or ends a standing" | the recommendation's wire |
| `receipter`: "A person or an agent, never a node." | section G (c) |

Two model rules the text leaves to the general rules, which do cover them:
- an end concurrent with a removal of its signer's key changes nothing (`end_void.key_removed`);
- a receipt by a removed key keeps nothing (`receipt_by_removed_key`).

Both follow from a removed key's rows counting only in the removal's past (KERNEL.md section 6).

## `names_head` at 76c4550

Of 190 families:

| `names_head` | Families |
|---|---|
| `by_placement` | 150 |
| `none` | 12 |
| `roster` | 9 |
| `standing` | 8 |
| null (open) | 11 |

Against "every act names its head; ends name `h_e`; receipts":

**a. The self branch of `by_placement` misses seated signers.** The builder's note says: "at self it names
none unless its signer signs as someone's node, agent or delegate". `moderation:{allegation_type}` is
`by_placement`, with placement `["self_collective", "targeted_family", "targeted_room", "commons"]` and signer
`seat_role(moderate)`. At commons or self_collective, under this rule it would name no head, though it is
exercised under a duty seat. That makes it `act_names_no_head` or unread.

The same holds for any `by_placement` family whose signer is a `seat_role`, a holder, a grantee of a root grant
or a key grant. The detection rows of a granted CI worker (`detection:{detector}`) need the bundle in force.

Needed: at self or commons, a family signed under a seat or a grant names `standing`.

**b. `act:ack` is null** ("the placement cell is unread"). The registry row says it names `refs.head`. The
model needs no head on a receipt (finding 8), so the column should say `none` or `standing`, not null. As it
stands, a payload builder that reads the column sends no head and refuses nothing, while the text's who-signs
reads "a voice at the head the acts name".

**c. No column marks the ends.** `names_head` is per family, but the 10 ending sites are a `withdraws` row
against an acceptance or an offer, an unseating, and a resignation. `withdraws` is the primitive of 2.4.1.1,
not a family of this model. Nothing in 76c4550 tells the builder that an end carries `refs.head` (`h_e`); only
the 2.4.1.1 sentence does.

Needed: a column or a rule for the ending rows, or a sentence in the build's note that the builder adds
`refs.head` to every end.

**d. `standing` covers the records themselves.** `ownership:{relation}:{target_kind}:{version}` is
`standing`. If it is the owner binding, it is the head; it does not name one. Likewise `key_grant:{axis}` if
it is the grant. A record that seats a standing should name none, or be its own head, not "the record that
seats its signer".

**e. Families marked `none` that may exercise a conferred standing.** `duty:{kind}` is `none` ("a row of its
signer's own"), but its signer is "the attester of the referenced permission", which is a standing. A duty
appointment is exercised under that permission, so it should name the permission's head.

`key:revocation`, `key:record` and `identity:occurrence*` are rightly `none`: a person's own key plane.

**f. 11 families are open:** `act:ack`, `admission:unit`, `archive_release:{basis}`,
`contribution:{subject_kind}`, `lawful_order:release`, `location_proof:{version}`, `preserve_request`,
`preserve_response`, `retirement:{state}`, `stream:head`, `trust:blessing`. If any of these is exercised under
a standing and the builder sends no head, then on the new wire it is `act_names_no_head`.

## Summary

| # | What | Kind |
|---|---|---|
| 1 | scope `act_names_no_head` to the new wire version; held rows are read as the model's uncited act | changes an answer |
| 2 | receipts and one say: say "not in force" and "only acts that count" | changes an answer |
| 3 | the end of a receipter's role: stated by causal past, and given a row | changes an answer |
| 4 | `lifts`: one wording, and decide whether a single-key conferrer may lift | changes an answer |
| 5 | `under`: attribution only, or dropped | changes an answer |
| 6 to 10 | wording: the tie, the old 4.5.5 sentence, `act:ack`'s signer, counted receipts and the line, one's own end | wording or scope |
| `names_head` a to f | the self branch of `by_placement`, `act:ack` null, a marker for ends, record families, `duty`, the 11 open families | column |
