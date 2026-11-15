-------------------------------- MODULE Cut --------------------------------
(* Removal by causal past (KERNEL.md section 6 rule 4 and "a row of a removed key counts when the removal has
   it among its ancestors"; CC 2.7.7; Causal.only_removals_stop_counting; crates/ciris-kernel
   derived::counts, cut::Cut).
   Two members, m and u, act concurrently on a genesis g; the admin removes m twice, once naming only g (it has
   none of m's rows in its past) and once naming m's first row; m keeps signing, before and after. Rows reach
   the node in ANY order and wait for what they name. The node keeps each row's verdict INCREMENTALLY: when a
   row arrives it is judged against the removals held, and when a removal arrives it revisits the rows it
   stops. Checked: the incremental verdict always equals the set function (a row counts iff it is in the past
   of every held removal of its signer); a row stops counting only when a removal that lacks it arrives; a
   row that stops never counts again; u's rows are never touched by a removal of m.
   MUT = TRUE plants the break: a row is judged once, on arrival, against the removals already held. *)
EXTENDS Naturals, FiniteSets
CONSTANTS MUT
Rows == {"g", "m1", "m2", "u1", "u2", "xa", "xb", "m3"}
Names == [r \in Rows |-> CASE r = "g" -> {} [] r = "m1" -> {"g"} [] r = "m2" -> {"m1"} [] r = "u1" -> {"g"}
                             [] r = "u2" -> {"u1", "m1"} [] r = "xa" -> {"g"} [] r = "xb" -> {"m1"}
                             [] r = "m3" -> {"xb"}]
Signer == [r \in Rows |-> CASE r \in {"m1", "m2", "m3"} -> "m" [] r \in {"u1", "u2"} -> "u" [] OTHER -> "admin"]
Removes == [r \in Rows |-> IF r \in {"xa", "xb"} THEN "m" ELSE "none"]

RECURSIVE Anc(_)
Anc(r) == Names[r] \cup UNION {Anc(n) : n \in Names[r]}

VARIABLES held, waiting, verdict
vars == <<held, waiting, verdict>>

RECURSIVE Grow(_, _)
Grow(H, W) == LET ready == {w \in W : Names[w] \subseteq H} IN IF ready = {} THEN H ELSE Grow(H \cup ready, W \ ready)

\* the set function: a row counts iff it is in the past of every held removal of its signer
Counts(H, r) == \A x \in H : Removes[x] = Signer[r] => r \in Anc(x)

Init == held = {} /\ waiting = {} /\ verdict = [r \in Rows |-> FALSE]

Offer(r) == /\ r \notin held
            /\ LET H2 == Grow(held, waiting \cup {r})
                   new == H2 \ held
               IN /\ held' = H2
                  /\ waiting' = (waiting \cup {r}) \ H2
                  /\ verdict' = [q \in Rows |->
                        IF q \in new THEN (IF MUT THEN \A x \in held : Removes[x] = Signer[q] => q \in Anc(x)
                                           ELSE Counts(H2, q))
                        ELSE IF q \in held THEN verdict[q] /\ (\A x \in new : Removes[x] = Signer[q] => q \in Anc(x))
                        ELSE verdict[q]]

Done == held = Rows /\ UNCHANGED vars   \* every row held: the run ends
Next == (\E r \in Rows : Offer(r)) \/ Done
Spec == Init /\ [][Next]_vars

\* C1 the incremental verdict is the set function, in every order
Inv_Incremental == \A r \in held : verdict[r] = Counts(held, r)
\* C2 a removal of m never touches u's rows
Inv_OthersUntouched == \A r \in held : Signer[r] = "u" => verdict[r]
\* C3 a row of m signed after a removal it names never counts
Inv_SignAfterRemoval == "m3" \in held => ~verdict["m3"]
\* C4 a row that stops counting never counts again, and it stops only when a removal lacking it arrives
Prop_StopsForGood == [][\A r \in held : ~verdict[r] => ~verdict'[r]]_vars
Prop_OnlyRemovalsStop == [][\A r \in held : (verdict[r] /\ ~verdict'[r]) =>
                              \E x \in held' \ held : Removes[x] = Signer[r] /\ r \notin Anc(x)]_vars
==========================================================================
