-------------------------------- MODULE Cut --------------------------------
(* Removal by causal past (KERNEL.md section 6 rule 4: "a row of a removed key counts when the removal has it
   among its ancestors"; CC 2.7.7; Causal.only_removals_stop_counting; crates/ciris-kernel derived::counts,
   cut::Cut).
   Each of the keys 1..K signs a chain of C rows on a genesis g. The admin removes each key once, by a removal
   that names that key's J-th row (rows 1..J are in its past, J+1..C concurrent with it), and each key signs
   one more row after its removal, naming it. Every row waits for what it names, and rows arrive in ANY order.
   The node keeps each row's verdict INCREMENTALLY: when a row arrives it is judged against the removals
   held, and when a removal arrives it revisits the rows it stops. Checked: the incremental verdict always
   equals the set function (a row counts iff it is in the past of every held removal of its signer); a row
   stops counting only when a removal that lacks it arrives, and then for good; a row signed after its key's
   removal never counts; another key's rows are never touched.
   MUT = TRUE plants the break: a row is judged once, on arrival, against the removals already held. *)
EXTENDS Naturals, FiniteSets
CONSTANTS MUT, K, C, J
Keys == 1..K
Rows == {<<"g", 0, 0>>} \cup {<<"c", k, i>> : k \in Keys, i \in 1..C} \cup {<<"x", k, 0>> : k \in Keys}
          \cup {<<"p", k, 0>> : k \in Keys}
Names(r) == CASE r[1] = "g" -> {}
              [] r[1] = "c" -> IF r[3] = 1 THEN {<<"g", 0, 0>>} ELSE {<<"c", r[2], r[3] - 1>>}
              [] r[1] = "x" -> {<<"c", r[2], J>>}
              [] r[1] = "p" -> {<<"x", r[2], 0>>}
Signer(r) == IF r[1] \in {"c", "p"} THEN r[2] ELSE 0          \* 0 is the admin
Removes(r) == IF r[1] = "x" THEN r[2] ELSE K + 1          \* K + 1: removes no key

RECURSIVE Anc(_)
Anc(r) == Names(r) \cup UNION {Anc(n) : n \in Names(r)}
AncOf == [r \in Rows |-> Anc(r)]

VARIABLES held, waiting, verdict
vars == <<held, waiting, verdict>>

RECURSIVE Grow(_, _)
Grow(H, W) == LET ready == {w \in W : Names(w) \subseteq H} IN IF ready = {} THEN H ELSE Grow(H \cup ready, W \ ready)

Counts(H, r) == \A x \in H : Removes(x) = Signer(r) => r \in AncOf[x]

Init == held = {} /\ waiting = {} /\ verdict = [r \in Rows |-> FALSE]

Offer(r) == /\ r \notin held /\ r \notin waiting
            /\ LET H2 == Grow(held, waiting \cup {r})
                   new == H2 \ held
               IN /\ held' = H2
                  /\ waiting' = (waiting \cup {r}) \ H2
                  /\ verdict' = [q \in Rows |->
                        IF q \in new THEN (IF MUT THEN \A x \in held : Removes(x) = Signer(q) => q \in AncOf[x]
                                           ELSE Counts(H2, q))
                        ELSE IF q \in held THEN verdict[q] /\ (\A x \in new : Removes(x) = Signer(q) => q \in AncOf[x])
                        ELSE verdict[q]]
Done == held = Rows /\ UNCHANGED vars
Next == (\E r \in Rows : Offer(r)) \/ Done
Spec == Init /\ [][Next]_vars

\* C1 the incremental verdict is the set function, in every order
Inv_Incremental == \A r \in held : verdict[r] = Counts(held, r)
\* C2 a key with no removal held: every row it signed counts
Inv_OthersUntouched == \A r \in held : (~\E x \in held : Removes(x) = Signer(r)) => verdict[r]
\* C3 a row signed after its key's removal never counts
Inv_SignAfterRemoval == \A k \in Keys : <<"p", k, 0>> \in held => ~verdict[<<"p", k, 0>>]
\* C4 a row that stops counting never counts again, and it stops only when a removal lacking it arrives
Prop_StopsForGood == [][\A r \in held : ~verdict[r] => ~verdict'[r]]_vars
Prop_OnlyRemovalsStop == [][\A r \in held : (verdict[r] /\ ~verdict'[r]) =>
                              \E x \in held' \ held : Removes(x) = Signer(r) /\ r \notin AncOf[x]]_vars
==========================================================================
