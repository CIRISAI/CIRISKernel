------------------------------- MODULE Purge -------------------------------
(* Finality by acknowledgement, checkpoint and purge (KERNEL.md sections 3 and 3a; CC 2.7.5, 2.7.7 rule 6,
   2.7.10; Settled.ack_blocking_quorum, say_settled_final, pruned_view_answers; crates/ciris-kernel head::View,
   head::purge).
   Acts 1..A are each counted at one head whose members are 1..N, and T of them can cut an act. For each act,
   a receipt by every member and a cut by each signer set of CutSets arrive in ANY order, all concurrent with
   one another. One say: a member holding a clean receipt of an act, in a row concurrent with a cut of it, has
   no say on that cut. An act is SETTLED once N - T + 1 members gave receipts. The node may checkpoint an act
   at any point once it is settled: it keeps the act's count at its head and drops the act's receipts and cuts.
   Checked: for every act, the purged node answers whether it counts at its head as the node that keeps every
   row does, in every state, before and after any purge; a settled act counts; the threshold is exact, since
   with fewer receipts some cut voids; and settled is final.
   MUT = TRUE plants the break: the node purges an act whether or not it is settled. *)
EXTENDS Naturals, FiniteSets
CONSTANTS MUT, A, N, T, CutSets
Acts == 1..A
Members == 1..N
Rows == {<<"r", a, k>> : a \in Acts, k \in Members} \cup {<<"x", a, s>> : a \in Acts, s \in CutSets}

Ackers(H, a) == {k \in Members : <<"r", a, k>> \in H}
Voids(H, a, s) == Cardinality((s \cap Members) \ Ackers(H, a)) >= T
CountsAt(H, a) == ~(\E s \in CutSets : <<"x", a, s>> \in H /\ Voids(H, a, s))
Settled(H, a) == Cardinality(Ackers(H, a)) >= N - T + 1

VARIABLES held, purged, kept
vars == <<held, purged, kept>>

Init == held = {} /\ purged = [a \in Acts |-> FALSE] /\ kept = [a \in Acts |-> TRUE]

Arrive(r) == /\ r \notin held /\ held' = held \cup {r} /\ UNCHANGED <<purged, kept>>
Purge(a) == /\ ~purged[a]
            /\ (MUT \/ Settled(held, a))
            /\ purged' = [purged EXCEPT ![a] = TRUE] /\ kept' = [kept EXCEPT ![a] = CountsAt(held, a)]
            /\ UNCHANGED held
Done == held = Rows /\ UNCHANGED vars
Next == (\E r \in Rows : Arrive(r)) \/ (\E a \in Acts : Purge(a)) \/ Done
Spec == Init /\ [][Next]_vars

Answer(a) == IF purged[a] THEN kept[a] ELSE CountsAt(held, a)
\* P1 purging changes no answer
Inv_PurgeChangesNothing == \A a \in Acts : Answer(a) = CountsAt(held, a)
\* P2 a settled act counts at its head, whatever cut arrives (ack_blocking_quorum)
Inv_SettledCounts == \A a \in Acts : Settled(held, a) => CountsAt(held, a)
\* P3 the threshold is exact: N - T receipts, every cut held, and some cut of T non-ackers voids
Inv_ThresholdExact == \A a \in Acts :
    (Cardinality(Ackers(held, a)) = N - T /\ (\A s \in CutSets : <<"x", a, s>> \in held)
      /\ (\E s \in CutSets : Cardinality(s \cap Ackers(held, a)) = 0 /\ Cardinality(s) >= T)) => ~CountsAt(held, a)
\* P4 settled is final
Prop_SettledFinal == [][\A a \in Acts : Settled(held, a) => (Settled(held', a) /\ CountsAt(held', a) = CountsAt(held, a))]_vars
==========================================================================
