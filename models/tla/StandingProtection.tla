-------------------------- MODULE StandingProtection --------------------------
(* The minors floor on announcing (CC 5.4.6 at v1.0-rc21, Constitution commit b016df4, part 5 line 1081,
   unchanged on rc22: "a node that carries the occurrence of a user key a row on record places in a minor
   band MUST NOT carry a federation-scope owner-binding, whoever owns it, and the promotion concludes nothing
   while that row stands", CC 2.7.3; CC 3.4.13 Q5). Unlike the seat read of MinorSuspend.tla this is a
   standing protection: it is read on the rows held NOW, never at an act's instant.
   Rows about one person K: the owner-binding B at federation scope (dated 2); a witness's minor row m1
   (dated 1) and K's own self-declared minor row m2 (dated 3), each withdrawn later by its signer (dated 4
   and 5); and with LARGE, a government witness's minor row m3 (dated 6) withdrawn at 7, and the owner's
   withdrawal of B itself (dated 8, un-announcing). Two nodes take the rows in ANY order each, a withdrawal
   possibly before the row it names. Each keeps a running summary (the binding held and not withdrawn, the
   minor rows held and the withdrawals seen) and re-reads its announcement on every arrival.
   MUT = TRUE plants the break: the announcement is judged once, when the binding arrives, against the minor
   rows dated at or before the binding's instant, and never read again. *)
EXTENDS Naturals, FiniteSets
CONSTANTS MUT, LARGE
Nodes == {1, 2}
Row(k, at, id, tgt) == [k |-> k, at |-> at, id |-> id, tgt |-> tgt]
Bind == Row("binding", 2, 1, 0)
Minors == {Row("minor", 1, 11, 0), Row("minor", 3, 12, 0)} \cup (IF LARGE THEN {Row("minor", 6, 13, 0)} ELSE {})
Withdrawals == {Row("withdraw", 4, 111, 11), Row("withdraw", 5, 112, 12)}
               \cup (IF LARGE THEN {Row("withdraw", 7, 113, 13), Row("withdraw", 8, 101, 1)} ELSE {})
Rows == {Bind} \cup Minors \cup Withdrawals

\* the set function over the rows held now
Withdrawn(H, r) == \E x \in H : x.k = "withdraw" /\ x.tgt = r.id
Standing(H) == {m \in H \cap Minors : ~Withdrawn(H, m)}
Announced(H) == Bind \in H /\ ~Withdrawn(H, Bind) /\ Standing(H) = {}

VARIABLES held, minors, gone, ann
vars == <<held, minors, gone, ann>>

Init == held = [n \in Nodes |-> {}] /\ minors = [n \in Nodes |-> {}] /\ gone = [n \in Nodes |-> {}]
        /\ ann = [n \in Nodes |-> FALSE]

Offer(n, r) ==
  /\ r \notin held[n]
  /\ held' = [held EXCEPT ![n] = @ \cup {r}]
  /\ minors' = [minors EXCEPT ![n] = IF r \in Minors THEN @ \cup {r.id} ELSE @]
  /\ gone' = [gone EXCEPT ![n] = IF r.k = "withdraw" THEN @ \cup {r.tgt} ELSE @]
  /\ LET hasBind == Bind \in held'[n] /\ 1 \notin gone'[n]
         standing == minors'[n] \ gone'[n]
     IN ann' = [ann EXCEPT ![n] =
                  IF ~MUT THEN hasBind /\ standing = {}
                  ELSE IF r = Bind THEN hasBind /\ ~\E m \in held[n] \cap Minors : m.id \in standing /\ m.at <= Bind.at
                  ELSE IF r.k = "withdraw" /\ r.tgt = 1 THEN FALSE
                  ELSE @]
Done == (\A n \in Nodes : held[n] = Rows) /\ UNCHANGED vars
Next == (\E n \in Nodes, r \in Rows : Offer(n, r)) \/ Done
Spec == Init /\ [][Next]_vars

\* P1 two nodes holding the same rows agree, whatever order each took them in
Inv_NodesAgree == held[1] = held[2] => ann[1] = ann[2]
\* P2 the announcement kept as rows arrived is the set function over the rows held now
Inv_Fold == \A n \in Nodes : ann[n] = Announced(held[n])
\* P3 no arrival order leaves a minor announced: while a minor row stands, the binding concludes nothing
Inv_NoMinorAnnounced == \A n \in Nodes : ann[n] => Standing(held[n]) = {}
\* P4 a minor row arriving after the binding pulls the announcement back
Prop_MinorPullsBack ==
  [][\A n \in Nodes : (ann[n] /\ \E m \in (held'[n] \ held[n]) \cap Minors : ~Withdrawn(held'[n], m)) => ~ann'[n]]_vars
\* P5 the withdrawal of the last standing minor row restores the announcement
Prop_WithdrawalRestores ==
  [][\A n \in Nodes : (\E x \in held'[n] \ held[n] : x.k = "withdraw" /\ x.tgt # 1)
                        /\ Bind \in held'[n] /\ ~Withdrawn(held'[n], Bind) /\ Standing(held'[n]) = {} => ann'[n]]_vars
==========================================================================
