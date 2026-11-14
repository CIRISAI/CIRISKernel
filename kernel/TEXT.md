# CC 2.7 The kernel: extract of the normative text

> This file is an extract of the normative text: section 2.7 (2.7.1 to 2.7.10) of Part 2, "The Grammar", of the CIRIS constitution (`constitution/part_2_the_grammar.md`, lines 1066 to 1253), edition 1.0-rc19, commit `60c741e` of [CIRISConstitution](https://github.com/CIRISAI/CIRISConstitution), copied verbatim below the rule. The parent is the normative home; where this extract and the parent differ, the parent governs.
>
> Its citations to other sections ("CC 3.2", "CC 4.5.4" and the like, and the relative links that carry them) are as written: those sections live in the parent repository, and the links resolve there, not here.

---

## 2.7 `kernel` — The kernel

The kernel is what a set of signed rows concludes, given only what the rows name and who has consented. It is one function. A node gives it the rows it holds or has been offered, its own clock and its own key. It returns what every row means to that node, what the node may do, what it owes, and what to copy to whom. Everything else a node does is storage, transport or presentation.

It is a causal kernel. Order comes only from what rows name, and standing comes only from signed consent. No node agrees an order with another; each computes the same answer from the same set of rows. Each rule below has its home in the section it cites. A rule that cites no other section has its home here.

### 2.7.1 `kernel-inputs` — Inputs

| Input | What it is |
|---|---|
| rows | the signed rows the node holds or has been offered, each with the instant this node first held it |
| `now` | the node's own clock |
| own key | the key the node signs under |

The instant a node first held a row is its own receipt, outside the signed row and never replicated ([CC 4.5.13](part_4_composition_governance.md#4.5.13), the processor's state). There is no trust set among the inputs: who a node trusts is a fold over the rows its own key signed ([CC 4.4.3.34](part_4_composition_governance.md#4.4.3.34)). Configuration is not an input. A value that binds others is a row signed by whoever decided it, and a value that binds only the node is a row under the node's own key.

### 2.7.2 `kernel-order` — The only order is what rows name

A row names other rows by digest: the row it answers, the head it extends, the proposal it votes on. That relation is well founded, since a digest cannot name a row that names it back. There is no sequencer. Nothing ranks the rows of different signers by a signed instant, by arrival or by digest ([CC 3.3.4](part_3_the_namespace.md#3.3.4), [CC 4.5.1.3](part_4_composition_governance.md#4.5.1.3)). Two rows where neither names the other, directly or through other rows, are **concurrent**.

Judging each row as it arrives, against what was admitted so far, is not a function of the rows: one set can give two answers in two arrival orders. So the kernel reads what a row names, never what a node happened to admit before it.

One voice may order its own rows. Between two acts of one kind by one signer on one named row, the later signed instant wins and the lower row id breaks a tie ([CC 3.5.1](part_3_the_namespace.md#3.5.1)). A signer who back-dates changes only what that signer says. A session goes to the earliest claimed instant among one person's own devices, which is one voice ordering its own rows ([CC 3.1.3.1](part_3_the_namespace.md#3.1.3.1)). Rows of different signers are decided by a party's own rows, by a count, or by a fixed order on kinds ([CC 2.7.7](#2.7.7)). A listing is not a ranking: the order in which a ballot shows the roster is read by no rule ([CC 4.5.4](part_4_composition_governance.md#4.5.4)).

### 2.7.3 `kernel-layers` — Three layers

| Layer | Reads | Property |
|---|---|---|
| **kept** | the row alone, and whether the rows it names are kept | the least set closed under the door; the same in every arrival order |
| **concluded** | the row against its ancestors | one solution, with negation and counts allowed; final once the row is kept, for a rule that reads no row concurrent with it |
| **derived** | conclusions over a set of rows | a function of the kept set, the node's key and, in one place, `now` |

Admission stops, and ends at one kept set, in every arrival order. A row waits for what it names. It is never refused for what another row says: a check that reads another row concludes nothing, is not counted, is contested, or is kept and not served ([CC 3.1.3.2](part_3_the_namespace.md#3.1.3.2), the refusals; [CC 4.5.13](part_4_composition_governance.md#4.5.13), the state processor).

Every answer about a row is of one of three kinds. **Final by form**: whether the row is kept, its conclusion for a rule that reads no concurrent row, and a row that names a blocking set of receipts. **Final by acknowledgement**: whether an act counts at the head it names, once n − t + 1 of the n members there have given receipts, where t can cut it ([CC 2.7.5](#2.7.5)). **Provisional**: the rest, including whether an act is still in force at a later head ([CC 2.7.7](#2.7.7)). This is finality of authorisation against cuts: a key revoked back to a bound, a row's own end and a reader's own trust are outside it, and it promises nothing about execution.

After a counting cut on a slot, only a key that may cut that slot changes it. A key whose standing has ended can still change what a reader with no acknowledgement of its own concludes ([CC 2.7.9](#2.7.9)).

### 2.7.4 `kernel-operators` — Operators

Every rule cell of the tables is written in these operators.

| Operator | What it does |
|---|---|
| select | the rows matching a pattern on their fields |
| group and reduce | the least, the greatest, the one distinct value, the count of distinct values, or the sum |
| interval | whether a value lies between an opening and a closing |
| table cell | the value a typed table gives for a key |
| bounded repeat | a step applied until nothing changes |
| closure over what rows name | the past of a row; no cell needs more |
| integer arithmetic | an opening plus a duration, or a fraction of a base; no floating point |
| join on a named row | two rows that name the same row |
| result assembly | a verdict for each element, or a set of effects |

A reduce that meets a tie between two different rows concludes nothing for that group, and never breaks the tie by position. A count is over the members at the head its row names, never at the instant of a decision or of the count ([CC 3.3.4](part_3_the_namespace.md#3.3.4)).

### 2.7.5 `kernel-answers` — Named answers

Nine answers, each a composition of the operators. Each role, window, policy and constant they read is data.

| Answer | Question | Layer |
|---|---|---|
| **state** | is this row live: admitted, withdrawn, recanted, superseded | derived, since a later concurrent row on its target can change it |
| **stands** | does this key hold this relation over this object | derived: a bounded walk of live edges |
| **tally** | is this count met, over the head it names | derived |
| **may** | may this key do this act on this target, and if not, which row is missing and who could sign it | derived |
| **audience** | who is this row for | derived, since a row naming it may come later |
| **missing** | which rows that this conclusion depends on are not held, and which receipts an act lacks to be settled | kept |
| **owed** | what this node must emit or do | derived |
| **window** | has this window closed, and with what outcome | derived; the one answer that reads `now` |
| **settled** | does this act count at its head in every later set | concluded for a row that names its receipts; final by acknowledgement once they are held; derived until then |

**stands.** One act underlies it: a voice consents to what binds it. A relation stands when every voice it binds has a concluded consent, one consent names the other, none is withdrawn by its own signer, and no cut removes it. A permission gives something of the signer's own and binds nobody else, so one row carries it. A duty binds the one who places it and the one who carries it, so it takes two consents ([CC 3.1.3.2](part_3_the_namespace.md#3.1.3.2), [CC 4.5.4](part_4_composition_governance.md#4.5.4)).

That pair is the **seat**. It is two consents and no other object, and it stands the same whichever was signed first. Nobody is bound by the rows of others. Any bound voice ends the relation alone, and no third key ends it without a cut ([CC 4.5.4](part_4_composition_governance.md#4.5.4)).

Where a body places a duty, the body is one party, and its consent is a count of its members' signatures on the row. One voice is not a count. A count once met is final: no member's later row lowers it, and only the holder's own withdrawal or a cut ends the duty. The members are those at the head the row names, and no key admits itself ([CC 3.3.4](part_3_the_namespace.md#3.3.4)).

Who may place a duty is one of three: the object's own key, a key holding a seat that may confer, or a group whose count is met. A key stands when a bounded walk of live seats leads to it from a root. For what a row means to a node, the root is that node's own key ([CC 4.4.3.34](part_4_composition_governance.md#4.4.3.34)). An onward hop counts only from the authority's own acceptance edges. At each hop the remaining depth is the lesser of what is left and the edge's own, the classes intersect, and a cycle is visited once. A scope stands at the end of a walk only if every seat on it carries the scope, so nothing amplifies.

A duty seat over a community is one seat with four scopes: `moderate`, `review`, `slash` and `takedown`. The founding record seats the duty holders who sign it, and they are equals. A duty seat is conferred by a strict majority of the duty holders, or by a lone holder with the new holder's acceptance. It is withdrawn by a strict majority of the others, never on fewer than two voices where there are two holders ([CC 4.5.4](part_4_composition_governance.md#4.5.4)). A delegation that carries a scope seats its delegate only with the delegate's own signature ([CC 4.4.3.19](part_4_composition_governance.md#4.4.3.19)). A deputy holds no seat of its own: it acts under its delegator's seat, and what it may do ends when that seat ends. A duty seat validly conferred then stands as an equal. A claim seats no one ([CC 3.4.5.1](part_3_the_namespace.md#3.4.5.1)).

**may.** The door, the control a person is offered and the gate on serving a row are one answer, and a refusal names the missing row ([CC 4.5.13](part_4_composition_governance.md#4.5.13), one function run three ways). A screen is a function of the rows a node holds, the viewer's key and `now`. It offers exactly what the door admits, and never draws as sent a fact the node did not send.

**missing, and what is copied.** A row moves to a peer because that peer must conclude something and lacks it. What is sent is what lies among the ancestors of that conclusion, within the row's audience. A row whose audience is everyone may be served to anyone, and a stranger is routed nothing outside that. A node holds a row only when it is in the row's audience. Being in an audience permits serving a row and does not cause a send; a peer's own request for it is a cause. A row carries its audience to the rows it names when it is concluded, sits in the same room, and its signer is already in the named row's audience. A row leaves its room only by its own signer's act ([CC 5.2](part_5_transport_substrate.md#5.2)).

**settled, and receipts.** A **receipt** of an act is a row by a voice at the head the act names, with the act in its past and no cut of the act by that key in its own past. An act is **settled** once receipts are held from n − t + 1 of the n members at its head, where t can cut it ([CC 2.7.7](#2.7.7) rule 6). **missing** names the voices whose receipts it lacks; a node MAY ask them under the copy rule above, and nobody owes one. An effect that cannot be undone, such as a key wrap or release, a disclosure, an external actuation or a deletion, names a blocking set of receipts of the act it rests on and waits for them. A section that requires such an effect without them says so ([CC 4.5.3](part_4_composition_governance.md#4.5.3)).

**window.** A row opens a clock. An answering row closes it, or time does, and the table states the outcome at the close. Where the outcome binds others, the concluder signs it as a landing row naming the acknowledgement by which it first held the opener, and its own head. Where it binds only the reader, each node reads the close on its own clock and signs nothing ([CC 4.5.13](part_4_composition_governance.md#4.5.13), the clock of a window).

A landing that states an outcome its own past does not give concludes nothing. An answer concurrent with a landing is **recounted**: it is counted with the landing's past, and the landing stands only if the table still gives the outcome it stated. A landing that does not stand says nothing against one that does. A landing with a strict majority behind it is final where no key of that majority answers both ways, in two rows neither of which names the other; such a key has no say there ([CC 2.7.7](#2.7.7) rule 6).

One door runs every policy row and every clock that takes answers, and the policy table states its count, floor and length ([CC 4.5.13](part_4_composition_governance.md#4.5.13)). The door reads five more things, each stated in the text. They are who concludes and with which row, and whether a late answer counts. They are also whether the opening act is in force while its window is open, whether the joiner's own yes is a voice of the floor, and the threshold the room's founding row declares.

**Two notions of time.** There are two: a row's own stated end, read from the row against `now`, and a window with a landing. An invitation's expiry is a window that shuts out a late acceptance ([CC 3.1.3.2](part_3_the_namespace.md#3.1.3.2)). A key is live while one of its own records covers `now` and it has not revoked itself, and no row of another key enters that reading. A row of an ended key that no live row has in its past lapses and counts in no answer. Its own verdict is unchanged, and a revocation never lapses.

### 2.7.6 `kernel-shapes` — Two mechanisms, four shapes

Every row family is one of four shapes: a **consent**, a **door**, a **claim** or **content**. A roster is a consent given by a count, and an acknowledgement is a claim. A family that takes no shape states why.

The four are labels over two mechanisms, consent and the door. Content is carried by consent: its audience is read off roster heads and the rows that name it, and its life is the **state** answer. A claim is carried by consent: what it means to a reader is the reader's own one-voice consents, walked from the reader's key. Nothing else reads `now`, so the door stays. Nothing else makes an offer stand, so consent stays.

### 2.7.7 `kernel-conflict` — Conflict between concurrent rows

Concurrent rows on one target are settled by six rules, and by no ranking of their signers.

1. **Different kinds on one target** are decided by a fixed order on kinds ([CC 3.5.1](part_3_the_namespace.md#3.5.1)).
2. **The same kind on one slot**: both count or neither does. No rule that cannot tell two rows apart can pick one.
3. **A row that names both** may decide between them.
4. **The cut.** A cut is a row on a slot by whoever may conclude it. Once it counts, rows on that slot concurrent with it do not count from the head the cut names, rows in its past stand, and rows that name it are judged at the head they name ([CC 2.4.1.1](#2.4.1.1)).
5. **Equal standing.** Two cuts by keys of equal standing that undo each other stay contested. A voice that the other cannot remove settles them.
6. **One say.** On one slot at one head, a voice that has acknowledged an act and voted to cut it, in two rows neither of which names the other, has no say there. It stays among the members the count is over.

**Answers by head.** Whether an act counts is read at the head it names, and whether it is still in force at a later head. A cut by a voice seated at a later head acts forward from the head it names and never changes what counted earlier; takedown, moderation and the halt act forward too.

A row of a removed key counts when the removal has it among its ancestors: something the removal can see had already named it ([CC 3.3.4](part_3_the_namespace.md#3.3.4)). Among several duty holders, one holder's own conferral concludes only while it is the one duty holder ([CC 4.5.4](part_4_composition_governance.md#4.5.4)).

Three further rules hold. A cosignature is a voice only for a row counted over a head that the cosignature itself names. An offer conferred by a count is ended by its holder or by a count, never by its proposer alone. A counted row counts only if every counted row it is built on counts.

### 2.7.8 `kernel-roster` — The roster is the one ledger

A group's roster is a lineage. Each version names the heads it extends and is counted over their members. Every other row takes its place from the roster head it names, and nothing else is ordered ([CC 3.2](part_3_the_namespace.md#3.2) T6).

Two versions of one head wait as tips. The roster is then the members common to all tips, until a version naming the tips makes one head again. The members at a head are a function of the head, its signatures and its past. A removal is a later counted version and changes the members there, not at the old head. A member's own leaving binds the same way, by causal past ([CC 3.3.4](part_3_the_namespace.md#3.3.4)).

Where the count asks two or more, one key's rows remove nobody, and a removed key counts again only after a version lists it again ([CC 4.5.13](part_4_composition_governance.md#4.5.13), the floor of two voices). A reader that has acknowledged a head holds void every counted act that names an older head and is not in that head's past, however many rows it has. Its signer acts again, forward, at the newer head ([CC 3.3.4](part_3_the_namespace.md#3.3.4)). That voiding is the reader's own and binds nobody else. Anything that binds others rests on receipts, a row that names a blocking set ([CC 2.7.5](#2.7.5)), never on one reader's own closure. Keys that met the count of an old head can sign a valid version alone; a witnessed lineage answers that ([CC 3.2](part_3_the_namespace.md#3.2) T6).

A person's keys, a voice's room keys, a room, the accord and an infrastructure community are this one roster, with parameters read from the policy table and the text. A public room's roster is public, so an audience is the members of a roster, everyone, or one named key ([CC 3.2](part_3_the_namespace.md#3.2)). It is read by asking a member's node, and every other roster is never enumerable outside its cohort.

**A writer's keys are a fold.** Who is entitled to a wrap of which key is a matter of seats and cuts. A rotation is due when a holder of the current key has lost its entitlement ([CC 4.4.3.16](part_4_composition_governance.md#4.4.3.16)). Each write and each mint names the head of the membership rows the writer held. The epoch is the count of the writer's mint rows, and the writer's state is a fold over its own rows.

**A private room seats voices.** In a private room the roster seats a **voice**, never an identity. A voice is a small counted roster of **room keys**, one for each device, made for that room only. That a voice is a given person's is the **binding**, which is never a row and is made for one addressee who cannot prove it to anyone else. No named answer reads a binding, and every named answer is the same over voices as over identity keys. A count of persons waits at a node for the bindings it lacks; a withheld binding is a stall, never a fork ([CC 3.1.3.2](part_3_the_namespace.md#3.1.3.2)).

### 2.7.9 `kernel-limits` — What the kernel does not give

- **No finality without the rows that show it.** Two nodes with the same rows conclude the same, and what is final by form or by receipts is final for every reader that holds them. A reader's own acknowledged head closes older heads for that reader only. Any other slot can be reopened by a key with standing on it.
- **No conclusion from silence without a clock.** A window closing unopposed, and the lapse of an unconfirmed halt, are read on the node's own clock. Nodes may differ while a window is open.
- **No decision that is not a function of rows.** Link and load decisions, retries, rendering and the prose rules given to a model stay outside the kernel.
- **No invariant of the form "at least one".** Two honest keys acting concurrently can leave none. For a community the way back is the lock and the members' count ([CC 4.5.4](part_4_composition_governance.md#4.5.4)).
- **No guard against a slot held on one signature.** A key of equal standing can undo such a slot, and the kernel does not check the tables for one.

An attacker keeps these, each bounded as stated:

- Keys that met a past count can fork on a past head. That unlists members and never lists one, and it moves only a reader with no acknowledgement of its own.
- A relay can choose the order of delivery and withhold a row until it is delivered. An emission made meanwhile cannot be unsent.
- A lone landing is never final against a key that can still sign, and the window's length is the concluder's own word.
- Whoever controls a new reader's first view can make a wrong head stick, until the reader withdraws its own rows.
- Whoever holds an ended key's private half can revive it, and only the key's own revocation makes its end final.
- One row of a seat that may confer can seat any number of keys, until one withdrawal by its conferrer.

A private room does not give deniability against a member who cooperates live with an outsider. A member's word is always possible; what is removed is the proof ([CC 3.1.3.2](part_3_the_namespace.md#3.1.3.2)).

The kernel does not settle these:

- a roster version that names several heads on the wire;
- how a second consent travels, and from when a delegation without one stops seating;
- the reach of a cosignature attached against a node's clock, unless it states its own end;
- a meaning for a clock that times a window from a signed instant and judges it at receipt. The freshness window `W` and `CLOCK_SKEW_VIOLATION` ([CC 2.6.7](#2.6.7)), the bound on a key that has lost standing ([CC 3.3.6.4](part_3_the_namespace.md#3.3.6.4)) and the attach window ([CC 3.2](part_3_the_namespace.md#3.2) T4a) read one. So do a response bounded by `W` ([CC 4.3](part_4_composition_governance.md#4.3)), an objection counted within `W` ([CC 4.5.13](part_4_composition_governance.md#4.5.13)) and the instant of a reserved family's row ([CC 3.4.7](part_3_the_namespace.md#3.4.7)). The kernel gives each no meaning beyond one node's own reading;
- `revoked_after`, which reads a revoked key's rows by their signed instants ([CC 2.4.1.1](#2.4.1.1), [CC 3.2](part_3_the_namespace.md#3.2) T6 to T8, [CC 5.3.2.3](part_5_transport_substrate.md#5.3.2.3)). The kernel gives that reading no meaning beyond one node's own;
- a seat, a licence or an owner read at a row's signed `asserted_at` where the row names no head ([CC 3.1.5](part_3_the_namespace.md#3.1.5), [CC 3.3.1](part_3_the_namespace.md#3.3.1), [CC 3.4.7](part_3_the_namespace.md#3.4.7), [CC 4.3](part_4_composition_governance.md#4.3)). The kernel gives that reading no meaning beyond one node's own;
- the standing verdict of a trust root, which [CC 3.2](part_3_the_namespace.md#3.2) T6 to T8 index by a signed `effective_at`. The kernel gives it no meaning beyond one node's own reading;
- a meaning for a rule cell that keeps a word the operators do not carry, or calls a fold no cell defines;
- what a family confers where no sentence states it;
- the smallest set of rows a node must keep ([CC 2.7.10](#2.7.10));
- whether a withdrawn receipt still blocks a cut. It is treated as blocking, and that is not established.

### 2.7.10 `kernel-checkpoint` — Checkpoint and purge

A node MAY keep its folded state and fold only the rows it has not yet folded. It MAY sign a **checkpoint**: a row under its own key that names the held rows no held row names, and carries the digest of its folded state. It MAY then drop the bytes of rows beneath a checkpoint, as this section allows. None of this is a duty: a node that keeps every row conforms.

A checkpoint binds nobody and is served to nobody unless its signer chooses. It is not an acknowledgement of the heads beneath it, and signing one changes no answer.

**What a checkpoint keeps.** For every row whose bytes it drops, a node keeps the row's digest, the digests it names, the fields a rule reads, and its conclusion. Where an act's count at its own head is final, the node keeps that answer. That is so for a settled act, kept with its receipts' digests, and, for this node only, for an act at a head older than one it has acknowledged ([CC 2.7.8](#2.7.8)). Any other act is kept whole, with its receipts and every cut of it. Whether an act is still in force at a later head is read again. A row that arrives naming a dropped row waits or concludes as it would if the bytes were held.

Nothing that reads `now` is frozen. A node keeps the instant it first held each row that opened a window ([CC 2.7.1](#2.7.1)), and reads again at each `now` every window, row's own end, key's end and `revoked_after` ([CC 2.4.1.1](#2.4.1.1)).

**What a purge never drops.** A purge never drops bytes another section keeps:

- the accountability record ([CC 2.4.1.1](#2.4.1.1));
- identity, consent and config records ([CC 6.1.5.2](part_6_the_coherence_mathematics.md#6.1.5.2) B1);
- records under a `legal_hold` or a class's retention floor ([CC 4.4.3.12](part_4_composition_governance.md#4.4.3.12));
- bytes counted toward an item's target or reported `here`, until `none` is acknowledged ([CC 6.1.5.1](part_6_the_coherence_mathematics.md#6.1.5.1), [CC 3.1.3.3](part_3_the_namespace.md#3.1.3.3));
- a retirement record under an accepted preserve request ([CC 7.5.5](part_7_lifecycle_stewardship.md#7.5.5));
- a tombstone ([CC 4.5.3](part_4_composition_governance.md#4.5.3)).

A deletion duty outranks a kept copy ([CC 4.5.3](part_4_composition_governance.md#4.5.3), [CC 3.3.1](part_3_the_namespace.md#3.3.1)). Only a `legal_hold` or an `erasure_exempt` class suspends consent-driven descent ([CC 4.4.3.29](part_4_composition_governance.md#4.4.3.29)). After a purge a node still serves its audience what it owes. A node holding bytes in custody for others drops only those whose custody has ended.

**Scope.** This section concerns a node's own storage and answers. A new reader taking a group's past on a member's vouch performs a different act ([CC 3.3.4](part_3_the_namespace.md#3.3.4)).
