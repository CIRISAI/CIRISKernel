# The steelmanned maximal object

## The purpose the object is judged by

A mechanism has no importance apart from what it is for. This one is for people who want to talk, share files,
keep rooms, decide things together and direct AI agents, with no company in the middle: nobody who can be bought,
blocked or broken, and nobody whose servers hold the group's life.

Whoever runs a platform does four jobs for its users, and a group with no platform has to do them itself:

1. say what order things happened in, so everyone sees the same state;
2. say when a decision is made and will stay made;
3. stop a member from winning by saying two things, by holding an office, or by arriving later;
4. keep the history, which no phone can hold whole.

The object is the claim that all four can be done by a function of the signed statements people's own devices
hold. The moves below are that claim taken apart. Moves 1 and 2 answer the first job, moves 3 and 4 the second,
moves 5 and 7 the third, move 6 the fourth, and move 8 is the wager that the four together are enough. Read
each move's importance against the job it does; judged as distributed-systems results alone, most of the
arithmetic is classical, as the README's lineage says.

That the four jobs are the necessary ones is argued, not proved: each is a function platforms perform today,
and a network that leaves any one undone needs someone to do it. A reviewer who finds a fifth job a group with
no operator cannot do without, and which this function cannot do, has found a kill for move 8.

## The moves

The strongest statement of what this repository is that its record supports, built as eight moves. Each move has
its claim in one sentence, its status, the reasoning, and its **kill**: the observation that would falsify it and
where to push. Statuses:

- **PROVED**: a Lean theorem in [`proofs/`](proofs/), compiled by `./check.sh` with no `sorry` and no axiom
  beyond the three of core Lean. A theorem is about the definitions in its file; whether those definitions are
  the text is a separate question, and each move says where the gap is.
- **RUN**: a model in [`models/`](models/) executed over every case to a stated bound, with plants caught.
  The models and their expected verdicts were written by the authors of the rules.
- **MEASURED**: counted from the parent's rule tables. Not reproducible here unless marked.
- **WAGER**: a claim the record cannot settle, with what would settle it.
- **OPEN**: not established.

Terms. A **row** is signed and names other rows by digest. Two rows are **concurrent** when neither names the
other, directly or through others. An **act** counts at the **head** it names: the roster version whose members
may cut it. A **cut** is a row that voids an act on its slot, signed by voices that may cut it; a body cuts by a
count of t of its n members. A **receipt** (an acknowledgement) is a row by a voice at the act's head with the act
in its past; it is **clean** when no cut of the act by the same key is in its own past.

## Move 1. Order is intrinsic

**Claim.** The only order is what rows name, and admission reaches one kept set and one conclusion for every row
in every arrival order.

**Status.** PROVED: `Causal.kept_is_least`, `door_any_order`, `close_saturated`, `door_spec`, `door_perm`,
`conclOf_unique`, `concl_final` ([`Causal.lean`](proofs/Causal.lean)); judging each row as it arrives is not a
function of the set, `Order.Two.arrival_not_a_function`, and no kernel that treats two rows alike admits exactly
one of them, `Order.no_symmetric_choice` ([`Order.lean`](proofs/Order.lean)). RUN: `check.py` prints `6606 sets,
2182671 arrival orders, 0 orders differ from the set function`, and each of three mutations (the door does not
wait; first held wins; a contested slot goes to the least digest) is caught. Seventeen cases from the parent's
rule tables give two results when judged on arrival ([`data/witnesses.tsv`](data/witnesses.tsv)).

**Reasoning.** A row waits for what it names and is never refused because of another row; a check that reads
another row moves to the concluded or derived layer, where it is a function of the kept set. Naming by digest is
well-founded, so the least closed set exists and every fair arrival order reaches it. The conclusion of a row is
the unique solution of an equation over its ancestors.

**Kill.** Two arrival orders of one finite set of rows that, under these rules, give two kept sets or two
conclusions. Push on: rule cells that read rows concurrent with the row judged (then the conclusion is not final
and `concl_ext` does not apply); a digest scheme in which a row can name a row that names it; any rule cell that
ranks rows of different signers by a signed instant or a digest (the parent measures 0 such cells, MEASURED, not
reproducible here).

## Move 2. Standing is consent

**Claim.** A relation stands exactly when every voice it binds has signed: a permission is one row, a seat is two
consents and nothing else, a count once met is final against its members, and one signature never removes.

**Status.** PROVED ([`Consent.lean`](proofs/Consent.lean)): `silent_voice_not_bound`,
`unbound_rows_change_nothing`, `only_bound_voices_end`, `one_voice_one_row`, `two_voices_two_rows`,
`seat_is_two_consents`, `holder_first_stands`, `count_needs_holder`, `count_is_final_against_members`,
`only_holder_or_cut_ends`. ([`RosterHead.lean`](proofs/RosterHead.lean)): `membersAt_function`,
`no_self_admission`, `one_signature_never_removes`, `readmission_needed`, `leaving_binds_by_past`.
([`Seat.lean`](proofs/Seat.lean), [`Causal.lean`](proofs/Causal.lean)): `third_key_cannot_end`,
`means_is_seat_walk`, `two_readers`, `no_own_edge_no_reach`. RUN: `check_rosters.py`, 90 properties over five
instances of one roster, each with a break that is caught.

**Reasoning.** Nobody is listed as an authority. What a row means to a reader is a bounded walk of live seats
from the reader's own key, so two readers differ only through rows of their own. A duty binds two parties and
takes two consents, in either order. Where a body places a duty its consent is a count of signatures on one row;
a signature is part of the row and is not withdrawn, so no member's later row lowers a met count.

**Kill.** A relation that stands while a voice it binds has signed nothing; a member removed by one key's rows
where the count asks two or more; a reader whose conclusions change because of rows by keys not on its walk.
Push on the gap between the proofs and the tables: the parent records that what a family confers is stated for
161 of 184 families, and 23 confer nothing a sentence states (MEASURED, [`kernel/KERNEL.md`](kernel/KERNEL.md)
section 5). The model's reading that an acceptance is spent once its key has left is the model's, not the text's.

## Move 3. Finality has three kinds, and the kernel says which

**Claim.** Every answer is final by form, final by acknowledgement, or provisional, and the kernel can tell which
from the rows it holds.

**Status.** PROVED ([`Settled.lean`](proofs/Settled.lean)): `kept_ext`, `concl_ext` (by form, under every
later set of any size); `effect_row_settled` (a row that names a blocking set of receipts); `say_settled_final`,
`countsAt_final`, `ack_finality_future_stable` (by acknowledgement); `Rows.count_not_monotone` (counting is not
monotone, so it needs a rule); `three_ways_final` (the three kinds together).

**Reasoning.** Kept and concluded only grow: a later set adds rows and never changes the past of a row already
held. Counting does not grow: with a grant G, an act E and a cut R concurrent with E, E counts at {G, E} and not
at {G, E, R}. What makes counting final is that every coalition able to cut has a member that has cleanly
acknowledged the act, and under the one say rule (Move 5) such a member's concurrent cut is no voice.

**Kill.** A set of rows where an act at its head has clean receipts from n − t + 1 members and some later set
makes it stop counting at that head. Push on the two rules the proof adds to the cut as stated: the voices and
count of a cut are those at the head the act names, and a signature on a cut is not counted against an act its
signer cleanly acknowledged in a concurrent row. Without the first, a later seat defeats an acknowledged act
(`later_seat_defeats_acknowledged`); without the second, the acknowledging voice does (`fork_voids_acknowledged`,
`overrule_voids_acknowledged`). Read from the cut row's signatures alone, as a count is today, the fork still cuts
(`Rows2.fork_stands_on_row_count`).

## Move 4. Coordination is a local proof obligation, and the obligation is minimal

**Claim.** The coordination an act needs is owed to exactly the voices whose future rows could change its answer,
is discharged by their receipts, and n − t + 1 receipts is both enough and necessary.

**Status.** PROVED: `blocking_set_blocks_all_cuts`, `ack_blocking_quorum` (an iff: acknowledgements meet every
coalition of t of n exactly when there are n − t + 1 of them), `five_three`, `unsettled_defeated`,
`final_iff_settled`, `say_unblocked_can_cut` ([`Settled.lean`](proofs/Settled.lean)). Necessity carries a
named assumption, `havail` in `final_iff_settled`: every voice that may cut and has not acknowledged can still
sign one cut of its own. That is a statement about keys, not rows, and is not proved.

**Reasoning.** This is quorum intersection read as a finality certificate. No node needs to know the full row set
or agree an order: it checks whether the receipts it holds meet every coalition able to cut. Members that have not
acknowledged still cut when there are t of them, so fewer receipts leave the answer open.

**Kill.** An act final against every extension with fewer than n − t + 1 clean receipts while every other voice
can still sign; or an act with n − t + 1 clean receipts that some extension defeats at its head. Push on
`havail`: a voice whose key is lost cannot sign, so for that act fewer receipts may suffice in fact, and the
kernel cannot see it.

## Move 5. The one say rule is forced, not chosen

**Claim.** On one slot at one head, a voice that has acknowledged an act and voted to cut it, in rows neither of
which names the other, has no say there: any reading that treats the voice's two rows alike gives it no say,
and of the readings defined, only the one that keeps "said both" apart from "said nothing" is closed under adding
rows.

**Status.** PROVED ([`Settled.lean`](proofs/Settled.lean)): `symmetric_say_forced`, `say4_symmetric`,
`say4_closed`, `say3_not_closed`, `say4_absorbing`, `sole_cutter_fork_stands`, `say_unblocked_can_cut`; the rival
readings fail, `sayA_not_safe`, `sayC_not_symmetric`. RUN: `check_purge.py` plant `no_say` (the rule switched off)
is caught with 60 answers different.

**Reasoning.** The two rows are concurrent, so no rule that treats rows alike can prefer one. Giving both effect
makes the act at once blocked and cut. Merging "said both" into "said nothing" is not closed under adding rows:
two such voices part when each adds a row. What remains is a voice that said both has no say there, and it stays
among the members counted.

**Kill.** A reading of a voice's two concurrent opposite rows that treats them alike, is closed under adding
rows and keeps an acknowledgement binding, other than no say. Push on what "alike" and "closed" mean in the file:
symmetry is quantified over every reading of the two flags (`symmetric_say_forced`), but closure is shown for the
readings defined there (`say3_not_closed`, `say4_closed`), not over all of them. The rule is added to the cut; it is not derived from the cut as the text
states it (`fork_stands_on_row_count`).

## Move 6. Forgetting can be certified

**Claim.** A node may cache, checkpoint and purge so that every answer under every later set equals the answer it
would give had it kept everything, and dropping the rows of an act not yet settled is shown unsafe by a witness
pair.

**Status.** PROVED for a sufficient set ([`Settled.lean`](proofs/Settled.lean)): `closed_iff_no_witness_pair`,
`full_view_closed`, `pruned_view_closed`, `pruned_view_answers`, `concl_ext_local`, `checkpoint_resume`,
`checkpoint_conclusions`; the unsafe case, `count_view_not_closed`, `Rows2.unsettled_drop_has_witness_pair`.
RUN: `check_purge.py` prints `broad reading: 200 replays over 9 histories; 12 rows kept whole, 36 reduced to a
stub` and `narrow reading: 200 replays over 9 histories; 16 rows kept whole, 32 reduced to a stub`, every answer
equal to keeping everything, no duty breached, eight plants caught. OPEN: the least set that suffices; many acts
purged at once and repeated purges (run part way, not proved); stubs as the store; own end, key end and
`revoked_after` over stubs.

**Reasoning.** A view of the store is safe to keep in place of the rows exactly when its next value is a function
of its value under every added row; the failure of that has a normal form, two states with one view that part
after one step. A settled act's count at its head never changes, so its receipts can go; an unsettled one has a
witness pair, so its rows stay. The closure normal form is a standard factorisation argument restated here.

**Kill.** A history, a purge the rules allow, and a later row under which the purged store answers differently
from the full one. Push on: rows whose bytes a duty keeps (CC 2.7.10's list; plant `drop_duty` shows the check
sees a breach); anything read against `now`, which a purge must never freeze (plant `freeze_now`).

## Move 7. Power acts forward

**Claim.** A later seat, a takedown, a moderation act or a halt changes what is in force from the head it names
onward and never what counted at an earlier head.

**Status.** PROVED for the head index ([`Settled.lean`](proofs/Settled.lean)): `countsAt_local`,
`later_head_changes_nothing`, `carried_to_head`, `Rows.later_seat_is_forward`, `seat_at_head_restores`; for a
reader's own line, `Reader.line_voids_old_fork`, `old_fork_void_for_ever` ([`Reader.lean`](proofs/Reader.lean)).
RUN: `check_purge.py` prints, for the reader's line, that a moderator seat's counted withdrawal on a head below
the one a reader acknowledged is void for that reader and not for a reader with none. No run targets the head
index on its own. That takedown, moderation and the halt act this way is the text's rule (CC 2.7.7, "Answers by head") and
is argued, not proved act by act.

**Reasoning.** Whether an act counts is read at the head it names and reads only rows naming that head. A voice
seated at a later head has no voice at the earlier one, so its cut changes what the act carries forward, not
whether it counted. Read without the head index, the same rows let a later seat void an act everyone at its head
acknowledged (`later_seat_defeats_acknowledged`); the index is what prevents that.

**Kill.** A voice seated at a later head that changes whether an act counted at its own head. Push on the
reader-relative part: a reader that has acknowledged a newer head voids an older fork for itself only; a reader
with no acknowledgement of its own is exposed to a fork signed by keys that met a past count (CONCEDED in the
attack runs, [`CHARACTERISTICS.md`](CHARACTERISTICS.md), fault model).

## Move 8. The ceiling (WAGER)

**Claim.** This is enough for real governance of a mesh of people and AI agents: the answers the model gives are
the answers a deployment needs, and nothing a deployment needs is outside them.

**Status.** WAGER, NOT DONE. What would count, in order:

1. An independent implementation, written from [`kernel/TEXT.md`](kernel/TEXT.md) by people who did not write
   the models, that gives the verdicts of every carried check's expected file and the `expect_kernel` verdict of
   every runnable entry of [`data/divergences.json`](data/divergences.json) (72 at this commit), in every arrival
   order.
2. A deployment under partition, delay, equivocation and crash, logging for each answer the rows the node held,
   in which no logged answer differs from the model's answer over those rows.
3. Governance decisions taken under it in which no party needed an answer the kernel cannot give.

**Kill.** A disagreement in (1) or (2) that is not an implementation bug: a case where the rows do not decide what
the text says they decide. Or a governance need the kernel cannot express: liveness when a quorum withholds,
collusion among the voices that could cut, an "at least one" invariant, a conclusion from silence without a clock.
Several of these are already conceded (REVIEW.md); the wager is that what remains is enough.

## The join

A node holding any set of signed rows can say, for every answer it gives, whether a later row could change it,
and if so whose rows could: order comes only from naming, standing only from consent, and a count becomes final
when receipts from n − t + 1 of the members at its head meet every coalition that could cut it, which is the
classical quorum bound read as a certificate any holder can check. The rules this forces (one say for a voice
that said both, head-indexed counting so that power acts forward, and certified forgetting) are proved over
stated definitions; the tables that instantiate them are measured, not proved; and nothing has yet been checked
against an implementation its authors did not write or a network that misbehaves.

## What the record does not license

- That the kernel achieves consensus, total order, or agreement on any provisional answer.
- That any act is wise, aligned, lawful or beneficial. It is authorisation against cuts, nothing else.
- That an act authorised was executed, or executed once, or executed as named.
- That the parent's rule tables implement the proved definitions. Coverage is measured and incomplete.
- That a withdrawn receipt still blocks a cut, or that the retained set is minimal.
- That a reader with no acknowledgement of its own is protected from a fork by keys that met a past count.
- That liveness holds when voices withhold receipts. A node lacking receipts waits or declines.
- That the attack runs are an independent test. The class each attack must fall in was written by the authors
  of the rules.
- That the counts in [`kernel/KERNEL.md`](kernel/KERNEL.md) not printed by a command here are reproducible here.
- That anything in this repository is novel arithmetic. The quorum results are classical (README.md, Lineage).
- That an AI agent under these rules is or is not a moral patient. The kernel is silent on it.
