----------------------------- MODULE MinorSuspend -----------------------------
(* The current age band about T at an act's own instant, which decides whether T's duty seat counts for
   the act X or is held suspended ("seated but not counted while the band reads minor"). Companion of
   MinorVoid.tla: the void is a property of the appointment's history; this is the reading at one act.
   Source: CC 3.4.11 at v1.0-rc21 (Constitution commit b016df4), "Read-union - witness outranks subject",
   CC 3.4.13's fail-secure rule, CC 3.5.1 rules 2 and 3 (between one attester's own rows the largest
   asserted_at wins, and at one instant the lowest attestation_id), and CC 2.4.1.1 (a withdrawal reaches
   forward only), as the Constitution session ruled them for this read on 2026-11-20 (the T8 pattern).
   The read at t = X's asserted_at. A retraction counts at t only if its own asserted_at <= t. For each
   signer, its current row at t is its newest age row with asserted_at <= t that no retraction counted at t
   names; at one instant the lowest id stands; it counts only if it covers t (asserted_at <= t <
   expires_at, half-open), and an expired newest row leaves that signer no current row. So a signer's newer
   row replaces its older one: a minor graduates by a newer adult row from the same signer. Across the
   signers' current rows: a witness outranks the subject, except that the subject's lower band (minor)
   lowers the reading; a higher assurance level outranks a lower one; at an equal level, minor wins. A
   person with no current row reads none and is not suspended.
   Rows: T's self-declared minor at 1 and adult at 3; witness 1 (provider) minor at 1 expiring at 3 and
   adult at 2 expiring at 5; witness 2 (provider) adult (id 21) and minor (id 22) both at 1, a tie the
   lower id wins; and with W = 3, witness 3 (government) minor at 4 expiring at 6 and adult at 5.
   Retractions: of T's minor, dated 2; of witness 1's adult, dated 4; with W = 3, of witness 3's minor,
   dated 5. An act X is offered dated at each instant 1..N. Rows arrive in ANY order, a retraction possibly
   BEFORE the row it names, and the node's clock ticks between arrivals.
   The node keeps each signer's rows and the retractions it has seen (target, date) INCREMENTALLY and
   re-reads every held X on each arrival.
   MUT = TRUE plants the break: the read is judged at the reader's clock, now, instead of X's asserted_at
   (both the rows and the retractions it counts). A display read by a node's own clock is outside the
   invariant (CC 2.7.9). *)
EXTENDS Naturals, FiniteSets
CONSTANTS MUT, W, N
TMax == N + 1
Times == 0..TMax
Signers == 0..W                                   \* 0 is T itself (the self rung)
Witnesses == 1..W
Level(s) == IF s = 3 THEN 2 ELSE 1                \* witness 3 is government, the others provider
Row(k, b, s, at, exp, id, tgt) == [k |-> k, band |-> b, s |-> s, at |-> at, exp |-> exp, id |-> id, tgt |-> tgt]
AgeRows == {Row("self", "minor", 0, 1, 0, 1, 0), Row("self", "adult", 0, 3, 0, 2, 0),
            Row("assured", "minor", 1, 1, 3, 11, 0), Row("assured", "adult", 1, 2, 5, 12, 0),
            Row("assured", "adult", 2, 1, 0, 21, 0), Row("assured", "minor", 2, 1, 0, 22, 0)}
           \cup (IF W >= 3 THEN {Row("assured", "minor", 3, 4, 6, 31, 0), Row("assured", "adult", 3, 5, 0, 32, 0)}
                 ELSE {})
RetDate(id) == CASE id = 1 -> 2 [] id = 12 -> 4 [] OTHER -> 5
RetractRows == {Row("retract", "-", 9, RetDate(r.id), 0, 100 + r.id, r.id) : r \in {q \in AgeRows : q.id \in {1, 12, 31}}}
XRows == {Row("X", "-", 9, t, 0, 200 + t, 0) : t \in 1..N}
Rows == AgeRows \cup RetractRows \cup XRows
IsMinor(r) == r \in AgeRows /\ r.band = "minor"

\* rows: [Signers -> set of that signer's age rows]; rets: set of <<target id, retraction's asserted_at>>
Counted(rets, r, t) == r.at <= t /\ ~\E p \in rets : p[1] = r.id /\ p[2] <= t
Max(S) == CHOOSE a \in S : \A b \in S : b <= a
Min(S) == CHOOSE a \in S : \A b \in S : a <= b
\* The band function, shared with StandingProtection.tla. A signer's current row: its newest row among
\* those counted at t (dated <= t, no retraction dated <= t naming it), the lowest id at one instant, if it
\* is unexpired at the clock c. An act's reading takes c = t; a standing protection reads the held set
\* (t = Forever) at the reading node's own clock c.
Forever == 1000
CurrentAt(S, rets, t, c) ==
  LET C == {r \in S : Counted(rets, r, t)}
  IN IF C = {} THEN {}
     ELSE LET m == Max({r.at : r \in C})
              win == CHOOSE r \in C : r.at = m /\ r.id = Min({q.id : q \in {q2 \in C : q2.at = m}})
          IN IF win.exp = 0 \/ c < win.exp THEN {win} ELSE {}
SignerBandAt(S, rets, t, c) == LET cur == CurrentAt(S, rets, t, c) IN
                                 IF cur = {} THEN "none" ELSE (CHOOSE r \in cur : TRUE).band
\* across signers: the subject's minor lowers; else the highest witness level, and at it minor wins
BandAt(rows, rets, t, c) ==
  LET sb == [s \in Signers |-> SignerBandAt(rows[s], rets, t, c)]
      present == {w \in Witnesses : sb[w] # "none"}
      top == IF present = {} THEN 0 ELSE Max({Level(w) : w \in present})
      wit == IF present = {} THEN "none"
             ELSE IF \E w \in present : Level(w) = top /\ sb[w] = "minor" THEN "minor" ELSE "adult"
  IN IF sb[0] = "minor" THEN "minor" ELSE wit
SignerBand(S, rets, t) == SignerBandAt(S, rets, t, t)
Band(rows, rets, t) == BandAt(rows, rets, t, t)

\* The set function, read straight from the held set H
RowsOf(H) == [s \in Signers |-> {r \in H \cap AgeRows : r.s = s}]
RetsOf(H) == {<<x.tgt, x.at>> : x \in H \cap RetractRows}
Suspended(H, t) == Band(RowsOf(H), RetsOf(H), t) = "minor"
SB(H, s, t) == SignerBand(RowsOf(H)[s], RetsOf(H), t)
\* The void of a duty appointment dated t (MinorVoid.tla, today's reading): any minor row ever held, and no
\* assured adult proof dated before t
VoidAt(H, t) == (\E r \in H : IsMinor(r)) /\ ~\E r \in H \cap AgeRows : r.k = "assured" /\ r.band = "adult" /\ r.at < t

VARIABLES held, rows, rets, susp, now
vars == <<held, rows, rets, susp, now>>

\* the node's reading of X over what it kept, at its clock c
Judge(rs, rt, x, c) == Band(rs, rt, IF MUT THEN c ELSE x.at) = "minor"

Init == /\ held = {} /\ rows = [s \in Signers |-> {}] /\ rets = {}
        /\ susp = [x \in XRows |-> FALSE] /\ now = 0

Offer(r) == /\ r \notin held
            /\ held' = held \cup {r}
            /\ rows' = [s \in Signers |-> IF r \in AgeRows /\ r.s = s THEN rows[s] \cup {r} ELSE rows[s]]
            /\ rets' = IF r.k = "retract" THEN rets \cup {<<r.tgt, r.at>>} ELSE rets
            /\ susp' = [x \in XRows |-> x \in held' /\ Judge(rows', rets', x, now)]
            /\ UNCHANGED now
Tick == now < TMax /\ now' = now + 1 /\ UNCHANGED <<held, rows, rets, susp>>
Done == held = Rows /\ now = TMax /\ UNCHANGED vars
Next == (\E r \in Rows : Offer(r)) \/ Tick \/ Done
Spec == Init /\ [][Next]_vars

HeldX == held \cap XRows
\* S1 node agreement: a node holding the same rows and reading at any reader clock c concludes the same
Inv_NodesAgree == \A x \in HeldX, c \in Times : susp[x] = Judge(RowsOf(held), RetsOf(held), x, c)
\* S2 order-independence: what the node kept as rows arrived, in every order, a retraction before its row
\* included, is what the held set says, and the kept reading is the set function at X's asserted_at
Inv_StoreFold == rows = RowsOf(held) /\ rets = RetsOf(held)
Inv_Fold == \A x \in HeldX : susp[x] = Suspended(held, x.at)
\* S3 a row or a retraction dated after t is not yet anyone's word at t (a withdrawal reaches forward only)
Inv_LaterRowsNotYet == \A x \in HeldX : susp[x] = Suspended({r \in held : r.at <= x.at}, x.at)
\* S4 a retraction counted at t takes its row out: dropping both changes nothing at t
Inv_RetractedOut == \A x \in HeldX : \A q \in held \cap RetractRows :
                      q.at <= x.at => susp[x] = Suspended({r \in held : r.id # q.tgt /\ r # q}, x.at)
\* S5 per signer the newest row stands: dropping a signer's older row changes nothing when a newer row of the
\* same signer is counted at t (a minor graduates by a newer adult row from the same signer)
Inv_NewestStands == \A x \in HeldX : \A r1, r2 \in held \cap AgeRows :
                      (r1.s = r2.s /\ r1.at < r2.at /\ Counted(RetsOf(held), r2, x.at))
                        => susp[x] = Suspended(held \ {r1}, x.at)
\* S6 at one instant the lowest id stands (CC 3.5.1 rule 3): dropping the higher id changes nothing
Inv_TieLowestIdWins == \A x \in HeldX : \A r1, r2 \in held \cap AgeRows :
                         (r1.s = r2.s /\ r1.at = r2.at /\ r1.id < r2.id /\ Counted(RetsOf(held), r1, x.at))
                           => susp[x] = Suspended(held \ {r2}, x.at)
\* S7 graduation does not touch the void: a minor row whose signer's current row at t is a newer adult row
\* still voids a duty appointment dated t that no assured adult proof precedes
Inv_GraduationLeavesVoid ==
  \A x \in HeldX : \A m \in held :
    (IsMinor(m) /\ SB(held, m.s, x.at) = "adult"
       /\ ~\E r \in held \cap AgeRows : r.k = "assured" /\ r.band = "adult" /\ r.at < x.at) => VoidAt(held, x.at)
\* S8 a witness outranks the subject except that the subject's minor lowers: whenever the witnesses alone
\* read minor, or the subject's current row is minor, T reads minor; a self-declared adult alone reads no band
Inv_SelfNeverRaises == \A x \in HeldX : (Band([s \in Signers |-> IF s = 0 THEN {} ELSE RowsOf(held)[s]],
                                              RetsOf(held), x.at) = "minor" \/ SB(held, 0, x.at) = "minor") => susp[x]
Inv_SelfAdultAloneIsNone == \A t \in 1..N :
                              Band([s \in Signers |-> IF s = 0 THEN RowsOf(held)[0] ELSE {}], RetsOf(held), t) # "adult"
\* S9 a higher level outranks a lower one: with the subject not minor, dropping every row of a witness whose
\* level is below a witness with a current row changes nothing
Inv_HigherLevelOutranks ==
  \A x \in HeldX : \A w, v \in Witnesses :
    (Level(w) < Level(v) /\ SB(held, v, x.at) # "none" /\ SB(held, 0, x.at) # "minor")
      => susp[x] = Suspended({r \in held : ~(r \in AgeRows /\ r.s = w)}, x.at)
\* S10 at an equal level minor wins: a witness at the top level with a current minor row suspends
Inv_EqualLevelMinorWins ==
  \A x \in HeldX : \A w \in Witnesses :
    (SB(held, w, x.at) = "minor" /\ \A v \in Witnesses : SB(held, v, x.at) # "none" => Level(v) <= Level(w))
      => susp[x]
\* S11 a suspension needs a minor row held (the void's clause 1); a person with no age row is never suspended
Inv_SuspendedNeedsMinorRow == \A x \in HeldX : susp[x] => \E r \in held : IsMinor(r)
==========================================================================
