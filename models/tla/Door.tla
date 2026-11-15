------------------------------- MODULE Door -------------------------------
(* The monotone door (KERNEL.md section 3, kept; CC 2.7.3; crates/ciris-kernel layers::kept, arrive).
   Rows are offered one at a time, in ANY order, a row may be offered twice, and a row may name a row that is
   never offered. A row is kept iff it is well formed alone and every row it names is kept; a row whose
   named rows are not all held waits, and is never refused for another row. The node runs the door to its
   fixed point after each offer.
   Checked: in every reachable state the held set is the least set closed under the door over what was
   offered (a function of the offered set, whatever the order); held only grows; nothing is held that was
   not offered; and every offered row whose past is offered and well formed is eventually held.
   MUT = TRUE plants the break: the door drops a row whose named rows are not held on arrival. *)
EXTENDS Naturals, FiniteSets
CONSTANTS MUT
Rows == 1..7
\* what each row names: a diamond (2,3 on 1; 4 on 2,3), a chain (5 on 4), a row naming 8, which is never
\* offered (6), and a malformed row (7 on 1)
Names == [r \in Rows |-> CASE r = 1 -> {} [] r = 2 -> {1} [] r = 3 -> {1} [] r = 4 -> {2, 3}
                              [] r = 5 -> {4} [] r = 6 -> {8} [] r = 7 -> {1}]
WF(r) == r # 7

VARIABLES offered, held, waiting
vars == <<offered, held, waiting>>

RECURSIVE Grow(_, _)
Grow(H, W) == LET ready == {w \in W : WF(w) /\ Names[w] \subseteq H}
              IN IF ready = {} THEN H ELSE Grow(H \cup ready, W \ ready)
\* the least set closed under the door, over a set of offered rows
Kept(S) == Grow({}, S)

Init == offered = {} /\ held = {} /\ waiting = {}

Offer(r) == /\ offered' = offered \cup {r}
            /\ IF MUT
               THEN /\ held' = IF WF(r) /\ Names[r] \subseteq held THEN held \cup {r} ELSE held
                    /\ waiting' = {}
               ELSE /\ held' = Grow(held, waiting \cup {r})
                    /\ waiting' = (waiting \cup {r}) \ held'

Next == \E r \in Rows : Offer(r)
Spec == Init /\ [][Next]_vars /\ WF_vars(\E r \in Rows \ offered : Offer(r))

TypeOK == offered \subseteq Rows /\ held \subseteq offered /\ waiting \subseteq offered
\* D1 the held set is a function of the offered set: the least closed set, in every order
Inv_HeldIsKept == held = Kept(offered)
\* D2 a row waits for what it names and is never refused for another row
Inv_WaitsNotRefused == held \cup waiting = offered
\* D3 held only grows
Prop_Monotone == [][held \subseteq held']_vars
\* D4 everything whose past is offered and well formed is eventually held
Prop_AllKept == <>[](held = Kept(Rows))
==========================================================================
