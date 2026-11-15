------------------------------- MODULE Purge -------------------------------
(* Finality by acknowledgement, checkpoint and purge (KERNEL.md sections 3 and 3a; CC 2.7.5, 2.7.7 rule 6,
   2.7.10; Settled.ack_blocking_quorum, say_settled_final, pruned_view_answers; crates/ciris-kernel head::View,
   head::purge).
   An act E is counted at head v0, whose members are A, B and C, and t = 2 of them can cut it. Receipts of E by
   A, B and C, and two cuts of E (one signed by B and C, one by A and C), arrive in ANY order; every receipt
   and cut is concurrent with every other. One say: a member holding a clean receipt of E in a row concurrent
   with a cut has no say on that cut. E is SETTLED once n - t + 1 = 2 members gave receipts. The node may
   checkpoint at any point: it keeps E's count at its head if it is final there and drops the receipts and
   cuts, keeping their signers; later rows are read against what it kept.
   Checked: the purged node's answer for whether E counts at its head equals the answer over every row held
   whole, in every state, before and after the purge; once settled the answer never changes again; a settled
   act counts.
   MUT = TRUE plants the break: the node purges whether or not E is settled. *)
EXTENDS Naturals, FiniteSets
CONSTANTS MUT
Members == {"A", "B", "C"}
T == 2
Receipts == {"rA", "rB", "rC"}
Cuts == {"xBC", "xAC"}
Rows == Receipts \cup Cuts
Of == [r \in Receipts |-> CASE r = "rA" -> "A" [] r = "rB" -> "B" [] r = "rC" -> "C"]
Sigs == [x \in Cuts |-> IF x = "xBC" THEN {"B", "C"} ELSE {"A", "C"}]

\* the members with a clean receipt among the held rows (receipts name E only, so every one is clean)
Ackers(H) == {Of[r] : r \in H \cap Receipts}
\* a cut voids E when the members with a say on it reach t; a member holding a receipt has no say
Voids(H, x) == Cardinality((Sigs[x] \cap Members) \ Ackers(H)) >= T
CountsAt(H) == ~(\E x \in H \cap Cuts : Voids(H, x))
Settled(H) == Cardinality(Ackers(H)) >= Cardinality(Members) - T + 1

VARIABLES held, purged, kept, keptAckers
vars == <<held, purged, kept, keptAckers>>

Init == held = {} /\ purged = FALSE /\ kept = TRUE /\ keptAckers = {}

Arrive(r) == /\ r \notin held /\ held' = held \cup {r} /\ UNCHANGED <<purged, kept, keptAckers>>
Purge == /\ ~purged
         /\ (MUT \/ Settled(held))
         /\ purged' = TRUE /\ kept' = CountsAt(held) /\ keptAckers' = Ackers(held)
         /\ UNCHANGED held
Done == held = Rows /\ purged /\ UNCHANGED vars
Next == (\E r \in Rows : Arrive(r)) \/ Purge \/ Done \/ (held = Rows /\ UNCHANGED vars)
Spec == Init /\ [][Next]_vars

\* what the purged node answers: the kept answer once purged, else the answer over what it holds
Answer == IF purged THEN kept ELSE CountsAt(held)
\* P1 purging changes no answer: the purged node agrees with the node that keeps every row
Inv_PurgeChangesNothing == Answer = CountsAt(held)
\* P2 a settled act counts at its head, whatever cut arrives (ack_blocking_quorum)
Inv_SettledCounts == Settled(held) => CountsAt(held)
\* P3 the threshold is exact: one receipt fewer and some cut voids
Inv_ThresholdExact == (Cardinality(Ackers(held)) = 1 /\ Cuts \subseteq held) =>
                        (Ackers(held) = {"C"} \/ ~CountsAt(held))
\* P4 settled is final: once settled, the answer never changes again
Prop_SettledFinal == [][Settled(held) => (Settled(held') /\ CountsAt(held') = CountsAt(held))]_vars
==========================================================================
