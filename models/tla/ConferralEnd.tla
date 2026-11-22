---------------------------- MODULE ConferralEnd ----------------------------
(* The causal end of a conferral (CC 2.4.1.1 as ruled: "A withdraws row retires its target as a cut does
   (CC 2.7.7). An act under the target that the withdrawal has among its ancestors stands. One that has the
   withdrawal in its own past, or is concurrent with it, does not count."), read as the Constitution intends
   it (2026-11-21): an end is FORWARD. A concurrent act counts at its own head and is not in force from the
   end's head on; nothing the end does voids an act at the act's own head when that head is not later than
   the end's. No instant is read anywhere: the only order is what rows name.

   The rows. Fixed and in every row's past: an offer by A to B, B's acceptance `acc`, the roster head H0, and
   (with WithTie) a second, independent grant to B by another grantor D, `accD`, that authorises the same acts.
   Signed in any order, each naming only rows already signed:
     H1        a roster version extending H0.
     b1..bN    B's acts, each on one of two DEVICES, at a roster head it names (H0 or H1, any one signed, so
               an OLD head too), `under` acc or the re-acceptance a2, `prev` the device's previous act under
               the same `under` (absent on the first), optionally citing the end (a name it may carry today).
               One of them may be a deputy edge `sub`: an offer by B to C, itself exercised under acc.
     c1        C's act under the deputy edge (reached by the end transitively).
     E         the END: by A (withdrawal of the offer) or by B (withdrawal of its own acceptance), naming
               the roster head it acts from (h_e) and `ack`, an antichain of B's acts under acc that it holds
               (empty, an old tip, or the tips). Its head is not older than a head in its own past.
     Rc        A's receipt of one of B's acts (rule 6's say), naming the act and optionally the end.
     Rm        a removal of the ender's key, naming the end or not.
     a2        B's re-acceptance of the offer, naming the end or not.
   Two nodes take the rows: node 1 in ANY order the door allows, node 2 in signing order. Each node may
   acknowledge H1 once it holds it (the reader's line, CC 2.7.8, over roster heads).

   Three answers are computed in every state, for every act, at every node, as <<counts at its own head,
   in force from the end's head on>>:
     "full"  the proposal: `under`, `prev`, `ack`. An act in the end's past (ack plus everything behind it
             by prev) stands; one with the end in its past does not count; a concurrent act counts at its
             own head and is not in force from h_e on, and if its head is LATER than h_e it does not count
             (the standing is ended there; rule 4, "from the head the cut names") unless the ender holds a
             clean receipt of it concurrent with the end (rule 6, one say).
     "set"   no prev: the end names every acked act individually (the same past for the end); an act's
             own past has no prev edge.
     "weak"  nothing new on acts (no prev, no `under`); the end names only its head h_e. The standing is
             found by the seat walk (any standing of the signer authorises), the end has no acked past.
   The reading's conclusion, `Ans`, is a function of the held set and the reader's acknowledgement.

   Checked (all three readings where they apply): an act in the end's past stands; an act naming the end does
   not count; nothing concurrent is in force from h_e on; the end never voids an act at or before its own
   head (it is forward) and never changes what counted there; one say keeps a receipted act counting at its
   own later head; the member set at a head is fixed by the head (leaving binds by past); a removal of the
   ender's key concurrent with the end voids the end; acts under a re-acceptance are untouched; two nodes
   holding the same rows give the same answer for every act whatever order they took them in, and each
   node's answer is the set function. And where the three readings agree.

   PLANT selects one planted break (each caught):
     "members"   the end applied to the member set at every head (B dropped from n);
     "say"       the ender's clean receipt ignored;
     "naming"    an act naming the end read as concurrent;
     "arrival"   each act's answer latched when it arrives (an answer read in arrival order);
     "own_head"  the end voids a concurrent act at the end's own head (a cut at the act's own head).
   (`_plant_converge` runs "arrival" against Inv_NodesAgree alone.)
   TIE = "any" reads ANY-STANDING (an act stands while any live standing of its signer authorises it) for the
   full reading too; LINE = "tips" adds the proposal's guard (b), the reader's line over the series' tips.
   Both are run only by the documented failing configurations (CONFERRAL_END.md). *)
EXTENDS Naturals, FiniteSets, Sequences

CONSTANTS PLANT, TIE, LINE, MaxB, WithC, WithRc, WithRm, WithA2, WithTie, WithBEnder

BIds == {"b1", "b2", "b3"}
BId(i) == CASE i = 1 -> "b1" [] i = 2 -> "b2" [] OTHER -> "b3"
ActIds == BIds \cup {"c1"}
Ids == ActIds \cup {"H1", "E", "Rc", "Rm", "a2"}
None == "none"
Null == [k |-> None, s |-> None, dev |-> 0, hd |-> "H0", un |-> None, nm |-> {}, prev |-> None,
         ack |-> {}, of |-> None, sub |-> FALSE]
Variants == {"full", "set", "weak"}

VARIABLES made, f, done, h1, ak, rk, latch
vars == <<made, f, done, h1, ak, rk, latch>>

Made == made

RECURSIVE Anc(_)
Anc(x) == f[x].nm \cup UNION {Anc(y) : y \in f[x].nm}
\* an act's past with no prev edge (the "set" and "weak" readings carry no prev)
RECURSIVE AncS(_)
AncS(x) == LET d == f[x].nm \ {f[x].prev} IN d \cup UNION {AncS(y) : y \in d}

Later(h, he) == h = "H1" /\ he = "H0"
Heads(S) == {"H0"} \cup ({"H1"} \cap S)
EndHd == f["E"].hd
SubOf == IF \E y \in BIds : f[y].sub THEN CHOOSE y \in BIds : f[y].sub ELSE None

\* ---- the answer ------------------------------------------------------------------------------------------
RmV(S) == "Rm" \in S /\ "E" \notin Anc("Rm")
\* the end counts for this reader: held, not voided by a concurrent removal of its signer's key, and not an
\* old fork of a roster head the reader acknowledged (it names H0, and H1 names nothing)
EL0(S, a) == "E" \in S /\ ~RmV(S) /\ ~(a /\ EndHd = "H0")
\* LINE = "tips": the proposal's guard (b), the line transposed onto the series: the reader acknowledged a tip
\* rk of the series; an end whose acked tips all lie behind rk, and which rk does not have in its past, is void
\* for that reader (Reader.olderThan with the acked tips as the heads named)
TipLine(S) == LINE = "tips" /\ rk # None /\ rk \in S /\ f["E"].ack # {} /\ "E" \notin Anc(rk)
                /\ rk \notin Anc("E") /\ \A t \in f["E"].ack : t \in Anc(rk)
EL(S, a) == EL0(S, a) /\ ~TipLine(S)
KeyV(x, S) == "Rm" \in S /\ f[x].s = f["E"].s /\ x \notin Anc("Rm")
LineAct(x, a) == a /\ f[x].hd = "H0" /\ "H1" \notin Anc(x)
Members(S, a) == IF PLANT = "members" /\ EL(S, a) THEN {"A", "C"} ELSE {"A", "B", "C"}
Say(x, S) == PLANT # "say" /\ "Rc" \in S /\ f["Rc"].of = x /\ f["Rc"].s = f["E"].s /\ "E" \notin Anc("Rc")
\* another live standing of the signer authorises the act: under ANY-STANDING (and always under "weak", where
\* nothing binds an act to a standing)
OtherAuth(x, S, v) == x \in BIds /\ (v = "weak" \/ TIE = "any") /\
                      (WithTie \/ ("E" \in S /\ f["E"].s = "B" /\ "a2" \in S))
Reached(x, v) == x = "c1" \/ (x \in BIds /\ (v = "weak" \/ f[x].un = "acc" \/ f["E"].s = "A"))
\* (the offer's withdrawal by A reaches acts under any acceptance of that offer, a2 included)
Seen(x, v) == v # "weak" /\ x \in Anc("E")
NamesEnd(x, v) == IF v = "full" THEN "E" \in Anc(x) ELSE "E" \in AncS(x)

EndRule(x, S, a, v) ==
  IF ~EL(S, a) \/ ~Reached(x, v) \/ OtherAuth(x, S, v) THEN <<TRUE, TRUE>>
  ELSE IF Seen(x, v) THEN <<TRUE, TRUE>>
  ELSE IF NamesEnd(x, v) /\ PLANT # "naming" THEN <<FALSE, FALSE>>
  ELSE IF Later(f[x].hd, EndHd) THEN <<Say(x, S), FALSE>>
  ELSE IF PLANT = "own_head" /\ f[x].hd = EndHd THEN <<FALSE, FALSE>>
  ELSE <<TRUE, FALSE>>

Base(x, S, a) == f[x].s \in Members(S, a) /\ ~LineAct(x, a) /\ ~KeyV(x, S)

RECURSIVE Ans(_, _, _, _)
Ans(x, S, a, v) ==
  LET e == EndRule(x, S, a, v)
      up == IF x = "c1" THEN Ans(SubOf, S, a, v) ELSE <<TRUE, TRUE>>
      b == Base(x, S, a)
  IN <<b /\ e[1] /\ up[1], b /\ e[1] /\ e[2] /\ up[2]>>

\* node 1 takes the rows in any order the door allows (h1, ak); node 2 in one fixed order the door allows
\* (by depth, then name), without an acknowledgement: holding Prefix(k), it answers as Rep2 (under the
\* arrival plant, the answer latched over the prefix that ends with the act)
IdNum(x) == CASE x = "H1" -> 1 [] x = "b1" -> 2 [] x = "b2" -> 3 [] x = "b3" -> 4 [] x = "a2" -> 5
              [] x = "E" -> 6 [] x = "c1" -> 7 [] x = "Rc" -> 8 [] x = "Rm" -> 9 [] OTHER -> 10
Rank(x) == Cardinality(Anc(x)) * 16 + IdNum(x)
Pos(x) == 1 + Cardinality({y \in made : Rank(y) < Rank(x)})
Prefix(k) == {y \in made : Pos(y) <= k}
Rep1(x) == IF PLANT = "arrival" THEN latch[x] ELSE Ans(x, h1, ak, "full")
Rep2(k, x) == IF PLANT = "arrival" THEN Ans(x, Prefix(Pos(x)), FALSE, "full") ELSE Ans(x, Prefix(k), FALSE, "full")
Without(S) == {y \in S : y # "E" /\ "E" \notin Anc(y)}

\* ---- signing ---------------------------------------------------------------------------------------------
Mk(id, r) == /\ ~done /\ id \notin Made
             /\ made' = made \cup {id} /\ f' = [f EXCEPT ![id] = r]
             /\ UNCHANGED <<done, h1, ak, rk, latch>>

MakeH1 == Mk("H1", [Null EXCEPT !.k = "version", !.s = "count"])

TipOn(d, u) == {y \in Made \cap BIds : f[y].dev = d /\ f[y].un = u /\
                  ~\E z \in Made \cap BIds : f[z].dev = d /\ f[z].un = u /\ y \in Anc(z)}
MakeB(d, hd, cite, u, sb) ==
  LET nb == Cardinality(Made \cap BIds)
      p == TipOn(d, u)
      pv == IF p = {} THEN None ELSE CHOOSE y \in p : TRUE
  IN /\ nb < MaxB
     /\ hd \in Heads(Made)
     /\ (cite => "E" \in Made)
     /\ (u = "a2" => "a2" \in Made)
     /\ (sb => WithC /\ u = "acc" /\ ~\E y \in Made \cap BIds : f[y].sub)
     /\ Mk(BId(nb + 1), [Null EXCEPT !.k = "act", !.s = "B", !.dev = d, !.hd = hd, !.un = u, !.prev = pv,
             !.sub = sb, !.nm = (IF pv = None THEN {} ELSE {pv}) \cup (IF hd = "H1" THEN {"H1"} ELSE {})
                                \cup (IF cite THEN {"E"} ELSE {}) \cup (IF u = "a2" THEN {"a2"} ELSE {})])

MakeC(hd, cite) ==
  /\ WithC /\ SubOf # None /\ SubOf \in Made
  /\ hd \in Heads(Made) /\ (cite => "E" \in Made)
  /\ Mk("c1", [Null EXCEPT !.k = "act", !.s = "C", !.hd = hd, !.un = "sub",
               !.nm = {SubOf} \cup (IF hd = "H1" THEN {"H1"} ELSE {}) \cup (IF cite THEN {"E"} ELSE {})])

MakeE(s, ack, hd) ==
  LET past == ack \cup UNION {Anc(y) : y \in ack}
  IN /\ s \in (IF WithBEnder THEN {"A", "B"} ELSE {"A"})
     /\ ack \subseteq {y \in Made \cap BIds : f[y].un = "acc"}
     /\ \A y, z \in ack : y \notin Anc(z)
     /\ hd \in Heads(Made) /\ ("H1" \in past => hd = "H1")
     /\ Mk("E", [Null EXCEPT !.k = "end", !.s = s, !.hd = hd, !.ack = ack,
                 !.nm = ack \cup (IF hd = "H1" THEN {"H1"} ELSE {})])

MakeRc(x, afterE) ==
  /\ WithRc /\ x \in Made \cap BIds /\ (afterE => "E" \in Made)
  /\ Mk("Rc", [Null EXCEPT !.k = "receipt", !.s = "A", !.of = x,
               !.nm = {x} \cup (IF afterE THEN {"E"} ELSE {})])

MakeRm(nE) == WithRm /\ "E" \in Made /\
              Mk("Rm", [Null EXCEPT !.k = "removal", !.s = "count", !.nm = IF nE THEN {"E"} ELSE {}])

MakeA2(nE) == WithA2 /\ (nE => "E" \in Made) /\
              Mk("a2", [Null EXCEPT !.k = "accept", !.s = "B", !.nm = IF nE THEN {"E"} ELSE {}])

\* ---- arrival ---------------------------------------------------------------------------------------------
Latched(S, x) == IF PLANT = "arrival" /\ x \in ActIds
                 THEN [latch EXCEPT ![x] = Ans(x, S, ak, "full")] ELSE latch

Arrive(x) == /\ done /\ x \in Made \ h1 /\ f[x].nm \subseteq h1
             /\ h1' = h1 \cup {x} /\ latch' = Latched(h1 \cup {x}, x)
             /\ UNCHANGED <<made, f, done, ak, rk>>
AckH1 == /\ "H1" \in h1 /\ ~ak
         /\ ak' = TRUE /\ UNCHANGED <<made, f, done, h1, rk, latch>>
AckTip(x) == /\ LINE = "tips" /\ x \in h1 \cap BIds /\ rk = None
             /\ rk' = x /\ UNCHANGED <<made, f, done, h1, ak, latch>>

Init == /\ made = {} /\ f = [i \in Ids |-> Null] /\ done = FALSE /\ h1 = {}
        /\ ak = FALSE /\ rk = None /\ latch = [i \in Ids |-> None]

Close == ~done /\ done' = TRUE /\ UNCHANGED <<made, f, h1, ak, rk, latch>>

Next == \/ Close
        \/ MakeH1
        \/ \E d \in {1, 2}, hd \in {"H0", "H1"}, c \in BOOLEAN, u \in {"acc", "a2"}, sb \in BOOLEAN :
              MakeB(d, hd, c, u, sb)
        \/ \E hd \in {"H0", "H1"}, c \in BOOLEAN : MakeC(hd, c)
        \/ \E s \in {"A", "B"}, ack \in SUBSET BIds, hd \in {"H0", "H1"} : MakeE(s, ack, hd)
        \/ \E x \in BIds, b \in BOOLEAN : MakeRc(x, b)
        \/ \E b \in BOOLEAN : MakeRm(b) \/ MakeA2(b)
        \/ \E x \in Ids : Arrive(x)
        \/ AckH1
        \/ \E x \in BIds : AckTip(x)
        \/ (done /\ UNCHANGED vars)     \* everything signed and delivered: nothing left to do

Spec == Init /\ [][Next]_vars

\* ---- invariants ------------------------------------------------------------------------------------------
\* for every node, every act it holds, under a reading
\* (node 2's held sets are prefixes of the signing order, each a set node 1 also reaches)
ForAll(P(_, _, _, _)) == \A x \in ActIds \cap h1 : P(x, h1, ak, 1)
Static(x, S, a) == ~LineAct(x, a) /\ ~KeyV(x, S)
Upstream(x, S, a, v) == x = "c1" => Ans(SubOf, S, a, v)[1]

PPast(x, S, a, n) == \A v \in {"full", "set"} :
  (EL(S, a) /\ x \in BIds /\ x \in Anc("E") /\ Static(x, S, a)) => Ans(x, S, a, v) = <<TRUE, TRUE>>
Inv_PastStands == ForAll(PPast)

PNaming(x, S, a, n) == \A v \in Variants :
  (EL(S, a) /\ Reached(x, v) /\ ~OtherAuth(x, S, v) /\ NamesEnd(x, v) /\ ~Seen(x, v)) => ~Ans(x, S, a, v)[1]
Inv_NamingEndVoid == ForAll(PNaming)

PForce(x, S, a, n) == \A v \in Variants :
  (EL(S, a) /\ Reached(x, v) /\ ~OtherAuth(x, S, v) /\ ~Seen(x, v)) => ~Ans(x, S, a, v)[2]
Inv_NotInForceFromEnd == ForAll(PForce)

\* forward: an act at or before the end's head, not naming it, counts at its own head
PFwd(x, S, a, n) == \A v \in Variants :
  (EL(S, a) /\ Static(x, S, a) /\ Upstream(x, S, a, v) /\ ~NamesEnd(x, v) /\ ~Later(f[x].hd, EndHd))
    => Ans(x, S, a, v)[1]
Inv_ForwardNeverVoidsAtOwnHead == ForAll(PFwd)

\* the end never changes what counted at an act's own head, unless the act names it or sits at a later head
PUnmake(x, S, a, n) ==
  ("E" \in S /\ "Rm" \notin S /\ x \in Without(S) /\ ~Later(f[x].hd, EndHd)
     /\ (x = "c1" => ~Later(f[SubOf].hd, EndHd))) =>
    Ans(x, S, a, "full")[1] = Ans(x, Without(S), a, "full")[1]
Inv_EndNeverUnmakes == ForAll(PUnmake)

PSay(x, S, a, n) == \A v \in Variants :
  (EL(S, a) /\ x \in BIds /\ Static(x, S, a) /\ Reached(x, v) /\ ~OtherAuth(x, S, v) /\ ~Seen(x, v)
     /\ ~NamesEnd(x, v) /\ Later(f[x].hd, EndHd)
     /\ "Rc" \in S /\ f["Rc"].of = x /\ f["E"].s = "A" /\ "E" \notin Anc("Rc"))
    => Ans(x, S, a, v) = <<TRUE, FALSE>>
Inv_OneSay == ForAll(PSay)

Inv_MembersByPast == Members(h1, ak) = {"A", "B", "C"}

PRm(x, S, a, n) == (RmV(S) /\ x \in BIds /\ Static(x, S, a)) => Ans(x, S, a, "full") = <<TRUE, TRUE>>
Inv_RemovalVoidsEnd == ForAll(PRm)

PReacc(x, S, a, n) == (x \in BIds /\ f[x].un = "a2" /\ "E" \in Made /\ f["E"].s = "B" /\ Static(x, S, a)) => Ans(x, S, a, "full") = <<TRUE, TRUE>>
Inv_ReacceptUntouched == ForAll(PReacc)

Inv_NodesAgree == ~ak => \A k \in 0..Cardinality(made) : h1 = Prefix(k) => \A x \in ActIds \cap h1 : Rep1(x) = Rep2(k, x)
PFold(x, S, a, n) == Rep1(x) = Ans(x, S, a, "full")
Inv_Fold == ForAll(PFold)

\* ---- where the readings agree, and where they differ (the differences are run as documented failing
\* configurations: ConferralEnd_prev.cfg, ConferralEnd_weak_seen.cfg, ConferralEnd_weak_reaccept.cfg,
\* ConferralEnd_tie_any.cfg) ---------------------------------------------------------------------------------
PrevSticky(x) == "E" \in Anc(x) /\ "E" \notin AncS(x)
WeakOther(S) == "E" \in S /\ f["E"].s = "B" /\ "a2" \in S
PSet(x, S, a, n) == ~PrevSticky(x) => Ans(x, S, a, "full") = Ans(x, S, a, "set")
Inv_SetAgrees == ForAll(PSet)
PSetAll(x, S, a, n) == Ans(x, S, a, "full") = Ans(x, S, a, "set")
Inv_SetAgreesAll == ForAll(PSetAll)
PWeak(x, S, a, n) == (~Seen(x, "full") /\ ~PrevSticky(x) /\ ~WeakOther(S) /\ ~WithTie) =>
                       Ans(x, S, a, "full") = Ans(x, S, a, "weak")
Inv_WeakAgreesUnseen == ForAll(PWeak)
\* the same counts at its own head, whatever the ender saw
PWeakCnt(x, S, a, n) == (~PrevSticky(x) /\ ~WeakOther(S) /\ ~WithTie) =>
                          Ans(x, S, a, "full")[1] = Ans(x, S, a, "weak")[1]
Inv_WeakAgreesOnCount == ForAll(PWeakCnt)
PWeakSeen(x, S, a, n) == Ans(x, S, a, "full") = Ans(x, S, a, "weak")
Inv_WeakAgreesSeen == ForAll(PWeakSeen)
PWeakRe(x, S, a, n) == (~Seen(x, "full") /\ ~PrevSticky(x)) => Ans(x, S, a, "full") = Ans(x, S, a, "weak")
Inv_WeakAgreesReaccept == ForAll(PWeakRe)
\* TIE: an act bound to acc that names the end, while accD (another grantor's grant) still authorises it
PTie(x, S, a, n) == (EL(S, a) /\ x \in BIds /\ f[x].un = "acc" /\ "E" \in Anc(x) /\ ~Seen(x, "full"))
                      => ~Ans(x, S, a, "full")[1]
Inv_EndReachesWhatNamesIt == ForAll(PTie)
\* the target cannot void its own end: the end counts for a reader unless removed or an old fork of a roster
\* head that reader acknowledged (ConferralEnd_line_tips.cfg runs LINE = "tips", where it fails)
Inv_TargetCannotVoidEnd == ("E" \in h1) => (EL(h1, ak) = EL0(h1, ak))
=============================================================================
