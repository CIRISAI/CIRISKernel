# The causal end of a conferral: is the wire proposal ready for persist v62.0?

Model: `models/tla/ConferralEnd.tla` with its configurations. Run by `tools/tla_check.sh` (small) and
`tools/tla_check.sh --large`. No instant is read anywhere; the only order is what rows name.

The rule under test is CC 2.4.1.1 as ruled ("A withdraws row retires its target as a cut does (CC 2.7.7). An
act under the target that the withdrawal has among its ancestors stands. One that has the withdrawal in its
own past, or is concurrent with it, does not count."), read the way the Constitution intends it (2026-11-21).
An end is FORWARD. A concurrent act counted at its own head and is not in force afterwards. Nothing the end
does voids an act at the act's own head. Voiding there belongs to rule 6, and nobody unmakes what counted.

## Verdict

**Sound with changes.** The proposal as written is not ready: it gives the end no head, so its forward reading
can't be told apart from a cut at the act's own head. Its guard (b), the reader's line moved onto series tips,
lets the grantee void its own end. With the changes below, the cheapest wire change that gives the right
answers is the **weak variant**. It touches the 10 ending sites, not the 47 producer sites. Listed from the
cheapest:

1. **WEAK: the end names its head. Nothing new on acts.** (10 sites.) The rules:
   - **E1.** Every ending row names the roster head it acts from (`h_e`): an explicit head of the ledger the
     ended acts are counted on, the same kind of head an act names today. It is the newest such head its
     signer holds, and it must not be older than any head in the end's own past. If it is, the end concludes
     nothing.
   - **E2. Forward.** An act whose own head is `h_e`, or older than `h_e`, or concurrent with it, counts at
     its own head and is not in force from `h_e` on. The end never voids an act at such a head.
   - **E3. The standing is ended at later heads.** An act whose named head has `h_e` in its past finds the
     standing ended there (the seat walk at its head, "from the head the cut names"), so it does not count.
     There is one exception, rule 6's one say: if the ender holds a clean receipt of that act concurrent with
     the end, the ender has no say on it. The act then counts at its own head, and still is not in force from
     `h_e` on. A forward end is never blocked.
   - **E4. Naming the end.** An act with the end in its causal past, by any name it carries today, does not
     count.
   - **E5. Concluding.** The end concludes as a cut under its signer's own standing at `h_e`:
     - a holder's withdrawal of its own acceptance is signed by the consent-giver alone and needs no count;
     - a conferrer's withdrawal of its own offer is signed by the offer's signer (`self`), or by the count at
       `h_e` (`group`);
     - an unseat follows the seat rules.

     The existing line (CC 2.7.8) applies to the end as to any counted cut over roster heads. A reader that
     has acknowledged a newer head holds void an end naming an older head not in that head's past, and the
     ender acts again, forward, at the newer head.
   - **E6. Reach.** The end reaches only acts exercised under the target, deputies transitively. It never
     reaches the member set or n at any head: a leaving binds by past there.
   - **E7. ANY-STANDING.** Nothing binds an act to one standing. CC 2.4.1.1's "an act under the target" must
     then read "an act that no other live standing of its signer authorises at its head" (see the tie, below).
   - **Exercised acts stay off the seat's slot** (question 6).

   What the weak variant gives up, with traces below:
   - The end can't keep in force the acts it saw. Every act of the ended standing is out of force from
     `h_e` on, and the durable effects of an ended deputy (a moderation, a hold) stop there unless reissued.
   - A second standing of the grantee keeps its acts counting. That can be another grantor's grant, or the
     holder's own re-acceptance concurrent with its withdrawal.
2. **WEAK + ACK SET.** The weak variant, plus `under` on acts (47 sites) and an `ack` naming each acked act
   individually. This restores "what the end saw stays in force" and the BOUND reading. The cost: `ack` grows
   with the history (one digest per act the ender holds), and `under` has no form for a bundle standing.
3. **FULL (the proposal with the changes).** `under` + `prev` + `ack` of the tips (47 sites, plus new
   per-device state). `prev` changes no answer that matters: question 5. It only compresses `ack` to one
   digest per tip (at most one per device).

**Not for v62.0 in any variant:** guard (b) as proposed (the reader's line over acked tips). It is not CC 2.7.8
and must be dropped: see question (b) below.

## The model

Fixed and in every row's past:
- an offer by A to B, and B's acceptance `acc`;
- roster head H0;
- with `WithTie`, a second grant `accD` to B from another grantor D, authorising the same acts.

Signed in any order, each naming only rows already signed:
- **H1**: a roster version extending H0.
- **b1, b2** (b3 in the large run): B's acts. Each is on one of **two devices**, at a roster head it names
  (an old head included), `under` either `acc` or the re-acceptance `a2`, with `prev` the device's previous act
  under the same `under`. An act may cite the end, and one may be a deputy edge to C (`sub`).
- **c1** (large run): C's act under the deputy edge.
- **E**: the end, by A (withdrawing the offer) or by B (withdrawing its own acceptance). It names `h_e` and an
  `ack` antichain of B's acts: empty, an old tip, or the tips.
- **Rc**: the ender's receipt of one of B's acts, which may name the end.
- **Rm**: a removal of the ender's key, which may name the end.
- **a2**: B's re-acceptance, which may name the end.

Node 1 takes the rows in every order the door allows, and may acknowledge H1. Node 2 takes them in one fixed
order. For every act, at every held set, the spec computes three answers side by side: **full** (the proposal),
**set** (no `prev`; `ack` names every act), and **weak** (no `prev`, no `under`, no `ack`). Each answer is
⟨counts at its own head, in force from `h_e` on⟩.

| Run | Constants | Distinct states, diameter, time |
|---|---|---|
| small (CI) | 2 B acts on 2 devices, H0 and H1, E by A or B, Rc, Rm, a2 | 1,919,466, 17, 82 s |
| large (local) | the same plus the deputy edge and C's act | 18,082,792, 19, 23 min |

Invariants checked in the main configuration, over all three readings where they apply:

| Invariant | What it checks |
|---|---|
| `Inv_PastStands` | an act in the end's past stands and stays in force (full, set) |
| `Inv_NamingEndVoid` | an act with the end in its past does not count |
| `Inv_NotInForceFromEnd` | no unseen act under the target is in force from `h_e` on |
| `Inv_ForwardNeverVoidsAtOwnHead` | an act at `h_e` or before, not naming the end, counts at its own head |
| `Inv_EndNeverUnmakes` | such an act's count is the same with or without the end held |
| `Inv_OneSay` | a clean concurrent receipt by the ender keeps a later-head act counting at its own head, and never in force |
| `Inv_MembersByPast` | the member set at a head never changes |
| `Inv_RemovalVoidsEnd` | an end concurrent with the removal of its signer's key changes nothing |
| `Inv_ReacceptUntouched` | acts under a re-acceptance after a holder's withdrawal are untouched |
| `Inv_TargetCannotVoidEnd` | nothing the target signs voids the end for a reader |
| `Inv_NodesAgree`, `Inv_Fold` | convergence |
| `Inv_SetAgrees`, `Inv_WeakAgreesUnseen`, `Inv_WeakAgreesOnCount` | where the readings agree |

Plants, each caught by `tools/tla_check.sh`:

| Plant | Caught as | States at catch |
|---|---|---|
| `members` (`_plant.cfg`): the end applied to the member set at every head | `Inv_MembersByPast` | 329 |
| `say`: the ender's clean receipt ignored | `Inv_OneSay` | 242,341 |
| `naming`: an act naming the end read as concurrent | `Inv_NamingEndVoid` | 2,897 |
| `arrival`: each act's answer latched on arrival | `Inv_Fold` | 902 |
| `converge`: the same latch, checked between the two nodes | `Inv_NodesAgree` | 1,710 |
| `own_head`: the end voids a concurrent act at the end's own head | `Inv_ForwardNeverVoidsAtOwnHead` | 1,108 |

These configurations are meant to fail. Like `MinorVoid_expiry.cfg`, they are outside both runs, and each
records a difference with a trace:

| Configuration | Fails on | What it shows |
|---|---|---|
| `ConferralEnd_prev.cfg` | `Inv_SetAgreesAll` | prev's one effect |
| `ConferralEnd_weak_seen.cfg` | `Inv_WeakAgreesSeen` | weak loses "in force" for acts the end saw |
| `ConferralEnd_weak_reaccept.cfg` | `Inv_WeakAgreesReaccept` | weak is ANY over a re-acceptance |
| `ConferralEnd_tie_any.cfg` | `Inv_EndReachesWhatNamesIt` | the tie under ANY-STANDING |
| `ConferralEnd_line_tips.cfg` | `Inv_TargetCannotVoidEnd` | guard (b) lets the target void its own end |

`ConferralEnd_tie_bound.cfg` passes: it holds the main invariants with the second grant present, under BOUND.

## 1. The five cases

All three readings agree on whether each act counts, except where noted. "In force" is written ⟨count, force⟩.

| Case | Answer | Evidence |
|---|---|---|
| In the end's past | ⟨yes, yes⟩ in full and set. ⟨yes, no⟩ in weak, which has no acked past: everything before the end is out of force from `h_e` on. | `Inv_PastStands`; `_weak_seen` trace: b1 at H0, E at H0 acking b1 |
| Concurrent | At `h_e` or an older or concurrent head: ⟨yes, no⟩, never voided at its own head. At a head later than `h_e`: ⟨no, no⟩, unless the ender holds a clean concurrent receipt, which gives ⟨yes, no⟩. | `Inv_ForwardNeverVoidsAtOwnHead`, `Inv_EndNeverUnmakes`, `Inv_NotInForceFromEnd`, `Inv_OneSay` |
| Naming the end | ⟨no, no⟩ | `Inv_NamingEndVoid`; plant `naming` |
| The end voided by a concurrent removal of the ender's key | The end changes nothing; every act is judged as if it were absent. The removal is a cut on the ender's key slot. If B withdrew its own acceptance and B's key is removed, B's acts concurrent with the removal fall by the key cut itself. | `Inv_RemovalVoidsEnd` |
| Withdraw and re-accept on two devices | B withdraws `acc` on device 1 and re-accepts (`a2`) on device 2. Full: acts under `a2` are untouched; acts under `acc` follow the rows above. Weak: nothing binds an act to `acc`, so while `a2` is held, B's acts under the old acceptance count too, at later heads as well. | `Inv_ReacceptUntouched`; `_weak_reaccept` trace: E by B at H0, a2 concurrent, b1 at H1 |

The last case needs one more statement. A re-acceptance re-seats B under an uncounted conferral. In a
**counted scope** (membership) it is not enough: a version must list the key again (`readmission_needed`). A
version with the withdrawal in its past does not list B (`leaving_binds_by_past`). Keep the two apart. The
re-acceptance restores the standing the acceptance carried, never the member set.

An end by A that withdraws the offer reaches acts under every acceptance of that offer, `a2` included. A
re-acceptance of a withdrawn offer seats nothing.

## 2. Backdating both ways, with no instants

**A grantee who never cites the end** keeps signing acts that name old heads.
- Such an act counts at its own head and is never in force from `h_e` on (`Inv_NotInForceFromEnd`).
- It can't name a head later than `h_e` and count, because the standing is ended there (E3).
- So "counted at its head, not in force after" is enough **only together with E3**. The proposal's literal
  rule ("a concurrent act counted at its own head") lets an act at any later head count, so the end would
  bound nothing until the grantee chose to cite it.

Can a standing effect survive? Only at heads not later than `h_e`:
- **A vote** counted into a version at an old head stays counted (`later_head_changes_nothing`). That version
  is a fork of the newer head. A reader that acknowledged the newer head holds it void (CC 2.7.8,
  `line_voids_old_fork`); other readers hold the two as tips until a version joins them. This is the existing
  exposure of an old count (KERNEL.md section 7, "an adversary holding the count of an old head"), not
  something the end adds.
- **A deputy edge** made concurrently with the end counts at its own head and is not in force from `h_e` on.
  Its deputies' acts:
  - at heads later than `h_e`: do not count, by transitive reach or by the seat walk;
  - at older heads: count there only;
  - naming the end: do not count.

  This was checked in the large run (`c1`).

**An ender who acks nothing.**
- Full and set read every act as concurrent, so they agree with weak.
- No act at `h_e` or before loses its count (forward), and every act loses force from `h_e` on.
- Acts at later heads do not count unless the ender's own receipt is concurrent with the end (one say). An
  ender who acknowledged an act can't erase it by leaving it out of `ack`.

**An ender who acks an old tip** (b1 when b2, behind it by `prev`, exists):
- b1 and everything behind it stand;
- b2 is concurrent and counts at its own head if that head is not later than `h_e`; it is out of force.

**An ender who names an old head** (a head older than one it holds) reaches the acts at the heads in between:
they sit at heads later than `h_e`. Three things bound this:
- E1: the end concludes nothing if a newer head is in its own past.
- One say.
- The line: a reader that acknowledged the newer head holds the end void, and the ender acts again at the
  newer head.

This is the exposure of every cut that names an old head. It is not new.

## 3. Convergence

The same rows in different arrival orders give the same answer for every act (`Inv_NodesAgree`, `Inv_Fold`).
Every answer is a function of the held set and the reader's own acknowledgement.

A reading latched in arrival order is caught twice:
- the `arrival` plant, on `Inv_Fold`. Trace: b1 and E, concurrent at one head; b1 latched while E was not yet
  held;
- the `converge` plant, on `Inv_NodesAgree`.

The answers differ between readers only through a reader's own acknowledgement (the line). That binds nobody
else, as CC 2.7.8 says.

## 4. The members hazard

Caught: plant `members`, as `Inv_MembersByPast`, at 329 states. B's acts in the end's past then stop counting
too (`Inv_PastStands`). The end reaches only acts exercised under the target. The member set and n at a head
are the head's own (`RosterHead.membersAt_function`, `leaving_binds_by_past`; the rejected rules `Rejected` and
`Retro`).

## 5. Is `prev` needed?

**No.** Against the variant with `under` plus an `ack` set naming each acked act, every answer matches
(`Inv_SetAgrees`) except one. If a device cited the end on one act and not on its next, then under `prev` the
next act has the end in its past and does not count. Under the set, that act is concurrent: it counts at its
own head and is out of force (`ConferralEnd_prev.cfg`: b1 cites E, b2 has `prev` b1 and cites nothing).

That difference is not a guarantee. A grantee who wants the concurrent reading forks `prev`: a second device,
or a `prev` that skips the citing act. Nothing can check `prev`. So `prev` gives honest producers stickiness,
and gives readers nothing they can rely on.

The cost, with a 32-byte digest per reference:

| | per act | per end | producer state | door |
|---|---|---|---|---|
| `prev` + `ack` of tips | +32 B (one `prev`) | 32 B per tip held: 1 per device, typically 1 or 2 | last act per (device, `under`) | the end waits for the chain behind its tips, as it would anyway |
| `ack` set, no `prev` | 0 | 32 B × the acts under the standing the ender holds, growing with the history: 10,000 acts make a 320 KB end | the ender lists its whole history of the standing | the end waits for every act it names |
| weak | 0 | 32 B (`h_e`) | none new | unchanged |

## 6. Putting exercised acts on the seat's slot

**It breaks the forward reading, so don't do it.** Today the slot ("seat", k, s, o) holds offers and
acceptances only:
- `models/causal_kernel/seat.py` `offer` and `accept` set `on=_slots(...)`;
- `unseat` cuts the slot;
- `_revoked_before` reads `on`.

The cut over a slot has no heads:
- `Seat.lean` Part B, `rowVoided`: a row on a slot is voided by any concurrent cut that hits it;
- `outsider_row_never_counts`;
- `crates/ciris-kernel/src/cut.rs`: "a row on one of those slots that is concurrent with the cut does not
  count".

With acts on the slot, an unseat would void every concurrent act outright, at its own head. That is the
`own_head` plant, and it contradicts `later_head_changes_nothing` and the ruling.

The slot's holder rule would also read them:
- `cut::Cut::holder`, `Causal.holder_both_or_neither`: two concurrent acts on one slot are "both or neither",
  and with two values the holder is `Conflict`;
- `seat.py`'s FINAL `_revoked_before` would refuse any act with a final unseat in its past.

No proved theorem assumes exercised acts are absent from the slot, because none puts them there. The proofs
stay true, but they would then prove the wrong thing about acts. In `SeatWalk.lean` the walk is over
(offer, key) pairs and reads no acts.

Keep acts off the slot. The end reaches them by a derived rule: E2 to E4, read over `under` in the full
variant, or over the seat walk at the act's head in the weak variant.

## The reader's line (guard b): not the transposition

The line of CC 2.7.8 (`Reader.lean` `behind`, `olderThan`; `line.rs` `settle`; `head.rs` `behind`/`void_set`)
voids, for one reader, a **counted act naming roster heads** that are all strictly in the past of an act on
the reader's acknowledged line, and concurrent with it. Its justification is the count: an act counted over an
old membership may be counted wrongly, and its signer acts again, forward, at the newer head.

Moving it onto series tips makes the grantee's own later act the "newer head". An end's authority does not
come from the series, so nothing about it goes stale when the grantee acts again.

The model finds the harm (`ConferralEnd_line_tips.cfg`, `Inv_TargetCannotVoidEnd`):
1. b1 and then b2 on one device;
2. E acks b1;
3. a reader acknowledges b2;
4. E is void for that reader. The target has voided its own end, by acting once on a device the ender
   hadn't seen.

The ender can't act "forward" past acts it is not shown, so the end is blocked. This is the opposite of
guard (c).

**Drop the transposition.** The end becomes a counted row naming a roster head (E1, E5). The existing line
then applies to it unchanged, as `head.rs` `void_set` already applies it to every `Kind::Cut`.

What an authored end must carry:
- its target (as today);
- `h_e` (the newest roster head its signer holds);
- optionally `ack` (variants 2 and 3).

It concludes as a cut under its signer's own standing at `h_e`. A holder's withdrawal of its own acceptance is
satisfied by that one signer, the consent-giver, with no count.

## The forward end needs an explicit head

A forward end can't be told apart from a cut at the act's own head without an explicitly named head. Without
`h_e`, a reader has to take the end's head from its past: the target and the acked tips. Those are exactly the
heads its concurrent acts name.

`head::View` then reads the end as a cut at the act's own head, and `voids_at` voids the act. That is plant
`own_head`, caught at 1,108 states.

With `ack` empty, the derived head is the target's own. Every concurrent act since the acceptance would then
sit at a "later" head and fall: an ender who acks nothing would reach back to the acceptance.

So the end must name its head explicitly. The head is a roster version of the ledger its acts are counted on,
the kind of head every counted act names today (`head::Entry.head`; KERNEL.md section 7). It is not a series
tip, and not the target.

Where a standing's acts are counted on no roster at all, there is no "own head". The plain cut applies there:
a concurrent act does not count. The forward reading then needs a head on the acts, which is the 47-site change.

## The producer survey

**A tie (one act, two live standings).** Two readings:
- **BOUND:** the act binds itself to one standing and falls with it.
- **ANY-STANDING:** the act stands while any live standing of its signer authorises it.

Under ANY-STANDING the model finds the trace (`ConferralEnd_tie_any.cfg`):
1. A ends grant A;
2. B, having seen the end, signs b1 naming it;
3. b1 counts, on D's grant.

The ruled text protects **the ender's** intent. "One that has the withdrawal in its own past … does not count"
is about an act under the target, and BOUND is that reading.

ANY-STANDING protects **the other grantor's**: D's grant was never A's to end. It is sound as authority. No act
counts that no live standing authorises, and `ConferralEnd_tie_bound.cfg` and the main invariants hold with the
second grant present. What it loses is attribution: the accountability record can't say which standing an
act used.

If the Constitution takes ANY-STANDING, `under` need not exist. Then CC 2.4.1.1 must say "an act that no other
live standing of its signer authorises at its head", and the weak variant is exactly that reading.

**No series exists today (the weak variant).** Under the weak variant acts carry nothing new. Acts already name
a head: `head::Entry.head` for `Kind::Act`, and every counted row takes its place from the roster head it names.

The weak variant agrees with the full proposal:
- on every count at an act's own head (`Inv_WeakAgreesOnCount`);
- on every answer for acts the end did not see (`Inv_WeakAgreesUnseen`);
- on the five cases, backdating both ways, convergence and the members hazard, apart from the two
  differences below.

They differ in two places:
- **Acts the end saw** (`_weak_seen`): full keeps them in force; weak leaves them counted at their head and
  out of force from `h_e` on. This is the forward-cut reading of `head::View::carried`, which also does not
  read whether the act is in the cut's past. Cost: an ended deputy's durable acts (a moderation, a hold)
  stop at the end, unless the ender or another holder reissues them.
- **A second standing** (`_weak_reaccept`, and the tie): weak is ANY-STANDING. Cost: the ender's intent
  yields to the grantee's other live standing.

Weak can't restore the first difference by reading heads instead. "Acts at heads older than `h_e` stay in
force" would keep the backdated acts in force too. Telling seen from unseen needs a past on the end: `ack`.

It touches 10 sites, not 47.

**Bundle standing (an accord holder's standing is a bundle with an object id).** A row-ref `under` can't name
it.
- Under the weak variant nothing names the standing. The seat walk at the act's head finds the bundle, the end
  names its target and `h_e`, and the answers are those above. It is fine.
- Under the full variant `under` would need an object-id form, or a rule naming the bundle's latest seating
  row. That is another reason to prefer weak.

## For the Constitution to vendor

> **CC 2.4.1.1, the end of a conferral.** An ending row (a withdrawal of an acceptance, a holder's or a
> count's withdrawal of an offer, an unseat, a resignation) names the roster head it acts from. That head is
> the newest its signer holds, and the end concludes nothing if a newer head is in its own past. The end
> concludes as a cut under its signer's own standing at that head: one's own acceptance needs only its own
> signature. It reaches only the acts exercised under its target, deputies transitively, and never the
> member set at any head. An act that has the end in its past does not count. Any other act under the
> target counts at its own head if that head is the end's or older, or concurrent with it, and from the
> end's head on it is not in force. An act at a later head finds the standing ended and does not count,
> unless the ender holds a clean receipt of it concurrent with the end; then the ender has no say on it at
> that head (CC 2.7.7 rule 6). The reader's line (CC 2.7.8) applies to the end as to any counted cut. An act
> that another live standing of its signer authorises at its head stands on that standing. [Variants 2 and 3
> only: an end may also name the acts it has seen; those stand and stay in force.]
