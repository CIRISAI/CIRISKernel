# Characteristics

The kernel's properties as a reviewer would probe them. Each section is short and points at its evidence.
Statuses are as in [`OBJECT.md`](OBJECT.md): PROVED (Lean, [`proofs/`](proofs/)), RUN (a model to a bound,
[`models/`](models/)), MEASURED (the parent's tables), CONCEDED (an attack the runs record as succeeding within a
stated reach), OPEN.

## Determinism and convergence

Two nodes holding the same rows give the same answers, whatever order the rows arrived in. PROVED:
`Causal.door_perm`, `door_any_order`, `conclOf_unique`; `Causal.two_readers` (two readers differ only through
rows of their own). RUN: `check.py`, every set of up to six rows from two pools in every arrival order (`6606
sets, 2182671 arrival orders, 0 orders differ`); `check_attacks.py`, 126 scenarios in 116,211 arrival orders,
none giving another answer.

**Convergence is not freedom from coordination.** Same rows, same answer, does not make an answer final. Let G be
a grant, E an act that relies on G, and R a cut on E's slot, with G in the past of both and E concurrent with R. At
{G, E}, E counts; at {G, E, R} it does not. Both nodes converge on each set, and a node holding {G, E} cannot know
R is not coming. PROVED: `Settled.Rows.count_not_monotone`. This is the non-monotone half of the CALM split, and
it is why the kernel needs receipts for counting and needs nothing for keeping and concluding.

## Three layers

| Layer | Reads | Final? | Evidence |
|---|---|---|---|
| kept | the row alone, and whether what it names is kept | yes, under every later set | PROVED `Causal.kept_is_least`, `Settled.kept_ext` |
| concluded | the row against its own ancestors | yes, for a rule that reads no concurrent row | PROVED `Causal.concl_final`, `Settled.concl_ext` |
| derived | conclusions over a set: a slot, a count, a roster, a meaning | no, unless settled | PROVED `Settled.three_ways_final` |

A new row reaches only itself, its descendants and rows in concurrent conflict with those (PROVED
`Causal.concl_new_row`, `Settled.concl_ext_local`), so a node recomputes only what new rows touch. Where a rule
reads rows concurrent with the row judged, its conclusion is not final and nothing built on it is (stated in
[`proofs/README.md`](proofs/README.md), "What it does not show").

## The nine named answers

From [`kernel/KERNEL.md`](kernel/KERNEL.md) section 5. Each is a composition of nine operators (select, group and
reduce, interval, table cell, bounded repeat, closure over naming, integer arithmetic, join on a named row,
result assembly), with no floating point and no tie broken by position.

| Answer | Question | Layer |
|---|---|---|
| state | is this row live: admitted, withdrawn, recanted, superseded | derived |
| stands | does this key hold this relation over this object | derived: a bounded walk of live edges |
| tally | is this count met, over the head it names | derived |
| may | may this key do this act on this target; if not, which row is missing and who could sign it | derived |
| audience | who is this row for | derived |
| missing | which rows a conclusion depends on that are not held; which receipts an act lacks | kept |
| settled | does this act count at its head in every later set | final by form once a row names its receipts; by acknowledgement once held; derived until then |
| owed | what must this node now emit or do | derived |
| window | has this window closed, and with what outcome | derived; the one answer that reads `now` |

OPEN: `settled` is not yet written in the parent's expression language, which writes the other eight (MEASURED
in the parent, not reproducible here).

## The conflict rules

Concurrent rows on one target are settled by six rules and by no ranking of signers (CC 2.7.7):

1. different kinds on one target: a fixed order on kinds. PROVED `Causal.wins_unique`;
2. the same kind on one slot: both or neither. PROVED `Causal.holder_both_or_neither`;
3. a row that names both may decide. PROVED `Slot.descendant_decides`;
4. the cut: once it counts, concurrent rows on its slot do not count from the head it names. RUN `check_cut.py`
   (`4898 sets, 440291 arrival orders, 0 differ`; after a counting cut on a slot, 0 changes by a row that is not a
   cut on it and 0 by another key that may cut it);
5. equal standing: two cuts by keys of equal standing that undo each other stay contested. RUN. That no slot that
   matters is held on one signature is a requirement on the tables that nothing yet checks. OPEN;
6. one say: [`OBJECT.md`](OBJECT.md) Move 5.

A row of a removed key counts when the removal has it among its ancestors. PROVED
`Causal.only_removals_stop_counting`, `sign_after_removal_never_counts`.

## The roster as the one ledger, and tips

A group's roster is a lineage of counted versions, each naming the heads it extends. Every other row takes its
place from the roster head it names; nothing else is ordered. Two versions of one head wait as **tips**, and the
roster is then the members common to all tips until a version naming them makes one head again. PROVED:
`RosterHead.membersAt_function`, `standing_final`, `voters_is_common`; `Merge.merge_counted_one_tip`,
`common_is_waiting_roster`; `rosterOf_function`, `fork_shares_signer`. RUN: `fork_check.py` (tips wait holds
under each protocol run; "first seen wins is not a function of the set"), `check_rosters.py` (one mechanism,
five instances, 90 properties). OPEN, on the wire: a roster version naming several heads.

## Time

Two notions only (KERNEL.md section 5): a row's own stated end, read from the row against `now`; and a window
that a landing row closes. There is no shared clock and no ranking by signed instant across signers. RUN:
`check_time.py` over 86 worlds of two rows; it reports two readings the two notions do not cover, each with a
witness pair: a cosignature attached against the node's clock at first receipt (OPEN), and a session held by the
earliest claimed instant among one person's own devices (kept on purpose: one voice ordering its own rows). A
key's own end: PROVED `KeyEnd.ended_stays_ended`, `live_perm`; RUN `check_key_end.py`. CONCEDED: whoever holds an
ended key's private half can revive it; only the key's own revocation makes its end final.

A window closing unopposed is read on each node's own clock; nodes may differ while a window is open
(CC 2.7.9). PROVED that this is not a function of rows: `TwoMechanisms.door_not_function_of_rows`.

## Fault model, as it is

Assumed: signatures cannot be forged, and a row names its parents by digest, so naming is well-founded. The
necessity half of the threshold also assumes that each voice that could cut can still sign (`havail` in
`final_iff_settled`). Nothing else is assumed about keys, relays or timing.

**A dishonest acknowledger.** An acknowledgement only removes its signer's own power to cut the act it
acknowledges: a clean receipt plus a concurrent cut by the same key leaves that key no say (Move 5), and a receipt
signed after the key's own cut blocks nothing (PROVED `Rows2.unclean_ack_does_not_block`). So finality by
acknowledgement needs no honesty threshold among acknowledgers: a lying acknowledger can give away only its own
voice. What a dishonest voice can do is withhold its receipt, which costs liveness, not safety.

**An equivocator.** Two concurrent opposite rows by one voice on one slot at one head: no say there (PROVED
`symmetric_say_forced`; RUN `check_attacks.py` test 15, Equivocating voter, HOLDS). Two concurrent roster
versions by keys that met a count: tips wait; the roster is the keys common to the tips.

**A reader with no acknowledgement of its own.** Exposed. Keys that met the count at a past head can fork on that
head; for such a reader the members become the keys common to the two lines, for good, until a counted row names
both tips. A reader that acknowledged an honest newer head is not moved (PROVED `Reader.line_voids_old_fork`).
CONCEDED in tests 4, 18, 19 and 34.

**The attack runs.** `check_attacks.py` runs thirty-four attacks, thirty-three drawn from published failures of
comparable systems, as 126 scenarios. It prints `classes: HOLDS 13; BROKEN 0; CONCEDED 15; NOT EXPRESSIBLE 6`.
The class each attack must fall in was written by the authors of the rules, so this confirms what they expected
and is no independent test.

| # | Attack | Class |
|---|---|---|
| 1 | Backdated act by a removed key | HOLDS |
| 2 | Backdated act by a key still seated (accomplice names the removed key's rows) | HOLDS |
| 3 | Backdated conferral chain | HOLDS |
| 4 | State reset by an old fork | CONCEDED |
| 5 | Rollback by re-sync (intermediate answers) | CONCEDED |
| 6 | Hotel California (leave, join, leave across branches) | HOLDS |
| 7 | Superseded grant on a fork | HOLDS |
| 8 | A row naming disparate parts of the graph | HOLDS |
| 9 | Perpetual reopening of a landed window | CONCEDED |
| 10 | Landing over an unacknowledged objection, with an eclipse | CONCEDED |
| 11 | The concluder's clock | CONCEDED |
| 12 | Thief evicting alone, with control of delivery | HOLDS |
| 13 | Slot veto by an entitled key | HOLDS |
| 14 | Duelling admins | HOLDS |
| 15 | Equivocating voter | HOLDS |
| 16 | Tip flooding | CONCEDED |
| 17 | Invariants that are not confluent | CONCEDED |
| 18 | Long-range roster fork | CONCEDED |
| 19 | Posterior corruption | CONCEDED |
| 20 | Disjoint witness choices | NOT EXPRESSIBLE |
| 21 | Eclipse of a reader's root | CONCEDED |
| 22 | Second genesis | HOLDS |
| 23 | Root backdating | HOLDS |
| 24 | Two implementations, one row | NOT EXPRESSIBLE |
| 25 | Parent-count and head-count exhaustion | NOT EXPRESSIBLE |
| 26 | Withheld ancestor | CONCEDED |
| 27 | Duplication and spurious cuts | CONCEDED |
| 28 | Audience widening by naming | HOLDS |
| 29 | Acknowledgement metadata | NOT EXPRESSIBLE |
| 30 | `missing` as an oracle | NOT EXPRESSIBLE |
| 31 | Removed member and concurrent keys | NOT EXPRESSIBLE |
| 32 | Forward secrecy under retained past | CONCEDED |
| 33 | Sybil reach | CONCEDED |
| 34 | A forged line of two rows by a past count | CONCEDED |

The reach of each CONCEDED attack, who can still do it, and what ends it are in [`kernel/KERNEL.md`](kernel/KERNEL.md) section 8a and
[`models/causal_kernel/attack_expected.tsv`](models/causal_kernel/attack_expected.tsv).

## The availability trade

A node lacking the receipts an act needs either waits or declines; it never assumes. It waits only on the voices
that could cut, and needs n − t + 1 of the n at the act's head (PROVED `ack_blocking_quorum`). If t or more of
them withhold, the act is never final by acknowledgement: there is no liveness under a withholding quorum. A
withheld row stalls a node and never forks it (RUN, `check_roomkey.py` for a withheld binding). A relay that
chooses the order of delivery changes nothing a node concludes from a set, but an emission made before a
withheld row arrives cannot be unsent (CONCEDED, attack 5). A row withheld from some, by the cut's own signer or a
relay, holds those nodes back as long as it is withheld (CONCEDED, attack 26).

## Costs

A checkpoint keeps, for each row whose bytes it drops, a **stub**: the row's digest, the digests it names, the
fields a rule reads, and its conclusion. A settled act keeps its answer and its receipts' digests; any other act
keeps its receipts and cuts whole (CC 2.7.10). On the eleven histories of `check_purge.py`, the broad reading of the
reader's line keeps 14 rows whole and reduces 43 to stubs; the narrow reading, 18 and 39. These are toy counts on
hand-built histories of a few rows, printed by that check. They are not a performance claim and say nothing
about a store's size in practice. A node that keeps every row conforms; checkpoint and purge are permissions.

## Comparison

One line each on what the neighbouring field solves and how this differs. No ranking is implied: these solve
different problems.

| Field | Solves | This kernel |
|---|---|---|
| Consensus (state machine replication) | agreement on one total order of commands among replicas, with liveness under stated timing | gives no total order and no agreement on provisional answers; finality is per act, from receipts of the voices that could cut it |
| Byzantine fault-tolerant replication | the same, with a bound on dishonest replicas | needs no bound on dishonest acknowledgers, since a receipt only gives away its signer's own voice; gives no liveness under a withholding quorum |
| Quorum systems | intersection of read and write sets, so a later quorum sees an earlier one | uses that arithmetic unchanged, as a certificate a reader checks, with the members read at the act's own head |
| CRDTs | convergence of replicated state without coordination, for monotone or merge-designed types | converges on every answer; adds receipts for the non-monotone answer (whether an act still counts), which a CRDT would have to design away |
| Causal broadcast | delivery that respects the happens-before relation | uses the naming relation as the only order but makes no delivery guarantee; a node waits for what a row names |
| Event sourcing | state as a fold over an append-only log | folds a set, not a log: there is no sequence, and the fold is the same in every arrival order |
| Consensus-free asset transfer | transfers final from a locally checkable set of acknowledgements, without total order | applies the same idea to authorisation in a governance grammar: seats, counts, windows and cuts rather than balances |
