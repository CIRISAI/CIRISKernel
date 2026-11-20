----------------------------- MODULE MinorSuspend -----------------------------
(* The current age band about T, which decides whether T's duty seat counts for an act X or is held
   suspended ("seated but not counted while the band reads minor"). Companion of MinorVoid.tla: the void is a
   property of the appointment's history; this is the reading at one act.
   Source: CC 3.4.11 at v1.0-rc21 (Constitution commit b016df4), "Read-union - witness outranks subject": a
   consumer unions both prefixes and takes the highest level on record; a subject's declaration of a lower
   band lowers the reading and never raises it; and CC 3.4.13's fail-secure rule. The per-signer series and
   the instant are as the Constitution session ruled on 2026-11-20 (the T8 pattern; not yet in the text at
   rc21 or at rc22 e24b150): the seat is judged at X's OWN asserted_at t. For each signer, its current row at
   t is its newest non-retracted age row about T with asserted_at <= t, if that row covers t (asserted_at <= t
   < expires_at, half-open); an expired newest row leaves that signer no current row, and a retracted row is
   out of its signer's series, so the previous one stands. Across signers' current rows: a self-declared
   minor lowers and never raises; among witnesses the highest assurance level wins; at that level a
   disagreement goes to minor. A person with no current row reads none and is not suspended.
   Rows: T's self-declared minor at 1 and adult at 3; witness 1 (provider) minor at 1 expiring at 3 and adult
   at 2 expiring at 5; witness 2 (provider) adult at 1; and with W = 3, witness 3 (government) minor at 4
   expiring at 6 and adult at 5. Retractions of T's minor, of witness 1's adult and, with W = 3, of witness
   3's minor. An act X is offered dated at each instant 1..N. Rows arrive in ANY order, a retraction possibly
   BEFORE the row it retracts, and the node's clock ticks between arrivals.
   The node keeps each signer's series INCREMENTALLY (a row arriving after its retraction never enters it)
   and re-reads every held X on each arrival. Checked: the kept reading is the set function of (held rows,
   X's asserted_at); a node reading the same rows at any reader clock agrees; a row dated after t, or one
   whose retraction is held, changes nothing at t; the self rung never raises the witnesses' reading; a
   suspension needs a minor row held, so the void's clause 1 (MinorVoid.tla) holds wherever the seat is
   suspended.
   MUT = TRUE plants the break: the read is judged at the reader's clock, now, instead of X's asserted_at. A
   display read by a node's own clock is outside the invariant (CC 2.7.9). *)
EXTENDS Naturals, FiniteSets
CONSTANTS MUT, W, N
TMax == N + 1
Times == 0..TMax
Signers == 0..W                                   \* 0 is T itself (the self rung)
Level(s) == IF s = 3 THEN 2 ELSE 1                \* witness 3 is government, the others provider
Row(k, b, s, at, exp, id, tgt) == [k |-> k, band |-> b, s |-> s, at |-> at, exp |-> exp, id |-> id, tgt |-> tgt]
AgeRows == {Row("self", "minor", 0, 1, 0, 1, 0), Row("self", "adult", 0, 3, 0, 2, 0),
            Row("assured", "minor", 1, 1, 3, 11, 0), Row("assured", "adult", 1, 2, 5, 12, 0),
            Row("assured", "adult", 2, 1, 0, 21, 0)}
           \cup (IF W >= 3 THEN {Row("assured", "minor", 3, 4, 6, 31, 0), Row("assured", "adult", 3, 5, 0, 32, 0)}
                 ELSE {})
RetractRows == {Row("retract", "-", 9, 0, 0, 100 + r.id, r.id) : r \in {q \in AgeRows : q.id \in {1, 12, 31}}}
XRows == {Row("X", "-", 9, t, 0, 200 + t, 0) : t \in 1..N}
Rows == AgeRows \cup RetractRows \cup XRows

\* One signer's current band at t over its series S (its non-retracted age rows)
Covers(r, t) == r.at <= t /\ (r.exp = 0 \/ t < r.exp)
SignerBand(S, t) ==
  LET C == {r \in S : r.at <= t}
  IN IF C = {} THEN "none"
     ELSE LET m == CHOOSE a \in {r.at : r \in C} : \A r \in C : r.at <= a
              cur == {r \in C : r.at = m /\ Covers(r, t)}
          IN IF cur = {} THEN "none" ELSE IF \E r \in cur : r.band = "minor" THEN "minor" ELSE "adult"
\* Across signers, given each signer's series
Witnesses == 1..W
Band(series, t) ==
  LET sb == [s \in Signers |-> SignerBand(series[s], t)]
      present == {w \in Witnesses : sb[w] # "none"}
      top == IF present = {} THEN 0 ELSE CHOOSE l \in {Level(w) : w \in present} : \A w \in present : Level(w) <= l
      wit == IF present = {} THEN "none"
             ELSE IF \E w \in present : Level(w) = top /\ sb[w] = "minor" THEN "minor" ELSE "adult"
  IN IF sb[0] = "minor" THEN "minor" ELSE wit
WitnessBand(series, t) == Band([s \in Signers |-> IF s = 0 THEN {} ELSE series[s]], t)

\* The set function: the series read straight from the held set H
Retracted(H, r) == \E x \in H : x.k = "retract" /\ x.tgt = r.id
SeriesOf(H) == [s \in Signers |-> {r \in H \cap AgeRows : r.s = s /\ ~Retracted(H, r)}]
Suspended(H, t) == Band(SeriesOf(H), t) = "minor"

VARIABLES held, series, retired, susp, now
vars == <<held, series, retired, susp, now>>

\* the node's reading of X over its kept series, at its clock c
Judge(ser, x, c) == Band(ser, IF MUT THEN c ELSE x.at) = "minor"

Init == /\ held = {} /\ series = [s \in Signers |-> {}] /\ retired = {}
        /\ susp = [x \in XRows |-> FALSE] /\ now = 0

Offer(r) == /\ r \notin held
            /\ held' = held \cup {r}
            /\ retired' = IF r.k = "retract" THEN retired \cup {r.tgt} ELSE retired
            /\ series' = [s \in Signers |->
                            IF r \in AgeRows /\ r.s = s /\ r.id \notin retired THEN series[s] \cup {r}
                            ELSE IF r.k = "retract" THEN {q \in series[s] : q.id # r.tgt}
                            ELSE series[s]]
            /\ susp' = [x \in XRows |-> x \in held' /\ Judge(series', x, now)]
            /\ UNCHANGED now
Tick == now < TMax /\ now' = now + 1 /\ UNCHANGED <<held, series, retired, susp>>
Done == held = Rows /\ now = TMax /\ UNCHANGED vars
Next == (\E r \in Rows : Offer(r)) \/ Tick \/ Done
Spec == Init /\ [][Next]_vars

HeldX == held \cap XRows
\* S1 node agreement: a node holding the same rows and reading at any reader clock c concludes the same
Inv_NodesAgree == \A x \in HeldX, c \in Times : susp[x] = Judge(SeriesOf(held), x, c)
\* S2 order-independence: the series kept as rows arrived, in every order, a retraction before its row
\* included, is the series of the held set, and the kept reading is the set function at X's asserted_at
Inv_SeriesFold == series = SeriesOf(held)
Inv_Fold == \A x \in HeldX : susp[x] = Suspended(held, x.at)
\* S3 a row dated after t is not yet its signer's word at t
Inv_LaterRowsNotYet == \A x \in HeldX : susp[x] = Suspended({r \in held : r.at <= x.at \/ r \notin AgeRows}, x.at)
\* S4 a retracted row is out of its signer's series: dropping it and its retraction changes nothing
Inv_RetractedOut == \A x \in HeldX : \A q \in held :
                      q.k = "retract" => susp[x] = Suspended({r \in held : r.id # q.tgt /\ r # q}, x.at)
\* S5 the self rung lowers and never raises: whenever the witnesses alone read minor, T reads minor
Inv_SelfNeverRaises == \A x \in HeldX : WitnessBand(SeriesOf(held), x.at) = "minor" => susp[x]
\* S6 T's self-declared adult alone reads no band (the subject cannot self-graduate)
Inv_SelfAdultAloneIsNone == \A t \in 1..N :
                              Band([s \in Signers |-> IF s = 0 THEN SeriesOf(held)[0] ELSE {}], t) # "adult"
\* S7 a suspension needs a minor row held, which is the void's clause 1 (MinorVoid.tla); a person with
\* no age row is never suspended
Inv_SuspendedNeedsMinorRow == \A x \in HeldX : susp[x] => \E r \in held : r \in AgeRows /\ r.band = "minor"
==========================================================================
