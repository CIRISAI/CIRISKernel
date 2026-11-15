------------------------------ MODULE TrustWalk ------------------------------
(* The reader's trust walk, with cycles (KERNEL.md section 5, stands; CC 2.7.5, CC 4.4.3.34;
   formal/trust_set/TrustSet.lean in the parent; crates/ciris-kernel trust::reaches).
   The walk starts at the reader's own edges with the hop cap as budget. At each hop the remaining budget is
   the lesser of what is left less one and the edge's own depth. A key is expanded again only when reached with
   more budget than before. Keys are taken from the work set in ANY order. The graph has two cycles, and an edge
   that reaches A first with no budget to spare, while a longer path reaches it with budget.
   Checked: the walk always terminates; when it stops, its verdict for every target equals TrustSet.lean's
   `walk`, transcribed below; the budget recorded for a key never falls.
   MUT = TRUE plants the break: each key is expanded once, with the budget it was first reached with (the
   reading of "a cycle is visited once" that differs from the Lean walk). *)
EXTENDS Naturals, FiniteSets
CONSTANTS MUT
Keys == 0..6            \* 0 is the reader
Cap == 5
\* edges: <<src, dst, depth>>; 0 reaches 1 at once with depth 0, and through 2 with budget; 1 -> 3 -> 2 and
\* 3 -> 4 -> 3 are cycles
Edges == {<<0, 1, 0>>, <<0, 2, 5>>, <<2, 1, 5>>, <<1, 3, 5>>, <<3, 2, 5>>, <<3, 4, 1>>, <<4, 3, 5>>,
          <<2, 5, 3>>, <<5, 6, 5>>, <<6, 5, 5>>, <<5, 1, 2>>, <<6, 4, 0>>}
Min(a, b) == IF a < b THEN a ELSE b

\* TrustSet.walk: structural on fuel; from k with budget b, reaches a
RECURSIVE Walk(_, _, _, _)
Walk(f, k, b, a) == IF f = 0 \/ b = 0 THEN FALSE
                    ELSE \E e \in Edges : e[1] = k /\ (e[2] = a \/ Walk(f - 1, e[2], Min(b - 1, e[3]), a))
Lean(a) == Walk(Cap, 0, Cap, a)

None == 99
VARIABLES best, todo, seen
vars == <<best, todo, seen>>

Init == best = [k \in Keys |-> IF k = 0 THEN Cap ELSE None] /\ todo = {0} /\ seen = {0}

Better(nb, old) == old = None \/ nb > old
Expand(k) ==
  /\ k \in todo
  /\ LET out == {e \in Edges : e[1] = k /\ best[k] > 0}
         nb(e) == Min(best[k] - 1, e[3])
         up == IF MUT THEN {e \in out : e[2] \notin seen}
               ELSE {e \in out : Better(nb(e), best[e[2]]) /\ \A f \in out : f[2] = e[2] => nb(f) <= nb(e)}
     IN /\ best' = [j \in Keys |-> IF \E e \in up : e[2] = j THEN nb(CHOOSE e \in up : e[2] = j) ELSE best[j]]
        /\ todo' = (todo \ {k}) \cup {e[2] : e \in up}
        /\ seen' = seen \cup {e[2] : e \in up}
Stop == todo = {} /\ UNCHANGED vars
Next == (\E k \in Keys : Expand(k)) \/ Stop
Spec == Init /\ [][Next]_vars /\ WF_vars(\E k \in Keys : Expand(k))

\* the walk's verdict for a target: an edge into it leaves a key reached with budget
Reached(a) == \E e \in Edges : e[2] = a /\ best[e[1]] # None /\ best[e[1]] > 0
\* W1 it terminates
Prop_Terminates == <>(todo = {})
\* W2 when it stops, it agrees with the Lean walk on every key
Inv_AgreesWithLean == todo = {} => \A a \in Keys \ {0} : Reached(a) = Lean(a)
\* W3 a key's budget never falls
Prop_BudgetRises == [][\A k \in Keys : best[k] # None => (best'[k] # None /\ best'[k] >= best[k])]_vars
==========================================================================
