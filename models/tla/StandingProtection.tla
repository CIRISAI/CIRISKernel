-------------------------- MODULE StandingProtection --------------------------
(* The minors floor on announcing (CC 5.4.6 at v1.0-rc21, Constitution commit b016df4, part 5 line 1081:
   "a node that carries the occurrence of a user key a row on record places in a minor band MUST NOT carry a
   federation-scope owner-binding, whoever owns it, and the promotion concludes nothing while that row
   stands", CC 2.7.3; CC 3.4.13 Q5), as the Constitution session ruled it on 2026-11-20 (rc22 is to read
   "while that person's band reads minor"): a STANDING protection reads the person's CURRENT band from the
   rows held NOW, the CC 3.4.11 read-union of MinorSuspend.tla, whose band function this spec reuses
   (BandAt). With no act instant every held row and every held retraction counts; per signer the newest row
   stands and the lowest id at one instant, so a minor row its own signer has superseded no longer stands,
   and one outranked by a higher assurance level no longer decides; a retraction takes its row out; the
   subject's minor lowers, and at an equal level minor wins. Expiry: serving or announcing is the reading
   node's own present act, so an age row's expires_at is judged on that node's own clock (CC 2.7.9 bounds the
   reading to that node). Nodes holding the same rows therefore agree at equal clocks, and at different
   clocks differ only across some held row's expires_at.
   Rows about one person K: the owner-binding B at federation scope (dated 2); witness 1 (provider) minor at 1
   (expiring at 2) and adult at 3; witness 2 (provider) minor at 2 (expiring at 3); witness 3 (government)
   adult at 4; K's own self-declared minor at 5, retracted at 6; and with LARGE, K's self-declared adult at 7
   and the retraction of witness 3's adult at 8. Two nodes each take the rows in ANY order, a retraction
   possibly before its row, with their own clocks ticking 1..3. Each keeps a running summary (the binding, each
   signer's rows, the retractions seen) and re-reads its announcement on every arrival and every tick.
   The same read decides two more standing relations, held from the start: K's owner-binding at self scope,
   which counts for nothing at EVERY scope while the band reads minor and counts again when it reads adult (CC
   3.2 line 961 at b016df4, "A binding whose owner a row on record places in a minor band counts for nothing";
   no carve-out by scope, as ruled), so the federation-scope binding B counts exactly when it does; and a
   guardian's steward-binding over K (CC 3.2, the guardianship rule), a standing relation on the current band
   that ends when the band reads adult, which needs an assured row, since a self-declaration never raises.
   MUT = TRUE plants the break: the announcement is judged once, when the binding arrives, at the binding's
   instant, and never read again. *)
EXTENDS Naturals, FiniteSets
CONSTANTS MUT, LARGE
Nodes == {1, 2}
Clocks == 1..3
MS == INSTANCE MinorSuspend WITH MUT <- FALSE, W <- 3, N <- 1, held <- {}, rows <- <<>>, rets <- {},
                                susp <- <<>>, now <- 0
Signers == MS!Signers
Row(k, b, s, at, exp, id, tgt) == MS!Row(k, b, s, at, exp, id, tgt)
Bind == Row("binding", "-", 9, 2, 0, 500, 0)
AgeRows == {Row("assured", "minor", 1, 1, 2, 11, 0), Row("assured", "adult", 1, 3, 0, 12, 0),
            Row("assured", "minor", 2, 2, 3, 21, 0), Row("assured", "adult", 3, 4, 0, 32, 0),
            Row("self", "minor", 0, 5, 0, 1, 0)}
           \cup (IF LARGE THEN {Row("self", "adult", 0, 7, 0, 2, 0)} ELSE {})
RetractRows == {Row("retract", "-", 9, 6, 0, 101, 1)} \cup (IF LARGE THEN {Row("retract", "-", 9, 8, 0, 132, 32)} ELSE {})
Rows == {Bind} \cup AgeRows \cup RetractRows
IsMinor(r) == r \in AgeRows /\ r.band = "minor"

\* the set function: the person's current band from the rows held now, at the reading node's clock c
RowsOf(H) == [s \in Signers |-> {r \in H \cap AgeRows : r.s = s}]
RetsOf(H) == {<<x.tgt, x.at>> : x \in H \cap RetractRows}
HeldBand(H, c) == MS!BandAt(RowsOf(H), RetsOf(H), MS!Forever, c)
SB(H, s, c) == MS!SignerBandAt(RowsOf(H)[s], RetsOf(H), MS!Forever, c)
Announced(H, c) == Bind \in H /\ HeldBand(H, c) # "minor"
Retracted(H, r) == \E x \in H \cap RetractRows : x.tgt = r.id
\* the self-scope owner-binding counts while the band does not read minor; the guardianship stands while it
\* does not read adult
OwnerCounts(H, c) == HeldBand(H, c) # "minor"
GuardLive(H, c) == HeldBand(H, c) # "adult"
\* the void (MinorVoid.tla, as ruled) of a duty appointment dated t: any minor row ever held counts,
\* superseded, outranked or retracted, and no un-retracted assured adult proof is dated before t
LiveProofBefore(H, t) == \E r \in H \cap AgeRows : r.k = "assured" /\ r.band = "adult" /\ r.at < t /\ ~Retracted(H, r)
VoidAt(H, t) == (\E r \in H : IsMinor(r)) /\ ~LiveProofBefore(H, t)

VARIABLES held, rows, rets, clk, ann, own, guard
vars == <<held, rows, rets, clk, ann, own, guard>>

Read(rs, rt, n, c) == Bind \in held'[n] /\ MS!BandAt(rs, rt, MS!Forever, c) # "minor"

Init == /\ held = [n \in Nodes |-> {}] /\ rows = [n \in Nodes |-> [s \in Signers |-> {}]]
        /\ rets = [n \in Nodes |-> {}] /\ clk = [n \in Nodes |-> 1] /\ ann = [n \in Nodes |-> FALSE]
        /\ own = [n \in Nodes |-> TRUE] /\ guard = [n \in Nodes |-> TRUE]

Offer(n, r) ==
  /\ r \notin held[n]
  /\ held' = [held EXCEPT ![n] = @ \cup {r}]
  /\ rows' = [rows EXCEPT ![n] = [s \in Signers |-> IF r \in AgeRows /\ r.s = s THEN @[s] \cup {r} ELSE @[s]]]
  /\ rets' = [rets EXCEPT ![n] = IF r \in RetractRows THEN @ \cup {<<r.tgt, r.at>>} ELSE @]
  /\ ann' = [ann EXCEPT ![n] = IF ~MUT THEN Read(rows'[n], rets'[n], n, clk[n])
                               ELSE IF r = Bind THEN Read(rows'[n], rets'[n], n, Bind.at)
                               ELSE @]
  /\ own' = [own EXCEPT ![n] = MS!BandAt(rows'[n], rets'[n], MS!Forever, clk[n]) # "minor"]
  /\ guard' = [guard EXCEPT ![n] = MS!BandAt(rows'[n], rets'[n], MS!Forever, clk[n]) # "adult"]
  /\ UNCHANGED clk
Tick(n) == /\ clk[n] < 3
           /\ clk' = [clk EXCEPT ![n] = @ + 1]
           /\ ann' = [ann EXCEPT ![n] = IF MUT THEN @ ELSE Bind \in held[n] /\ MS!BandAt(rows[n], rets[n], MS!Forever, clk'[n]) # "minor"]
           /\ own' = [own EXCEPT ![n] = MS!BandAt(rows[n], rets[n], MS!Forever, clk'[n]) # "minor"]
           /\ guard' = [guard EXCEPT ![n] = MS!BandAt(rows[n], rets[n], MS!Forever, clk'[n]) # "adult"]
           /\ UNCHANGED <<held, rows, rets>>
Done == (\A n \in Nodes : held[n] = Rows /\ clk[n] = 3) /\ UNCHANGED vars
Next == (\E n \in Nodes, r \in Rows : Offer(n, r)) \/ (\E n \in Nodes : Tick(n)) \/ Done
Spec == Init /\ [][Next]_vars

\* P1 two nodes holding the same rows at the same clock agree, whatever order each took them in
Inv_NodesAgree == (held[1] = held[2] /\ clk[1] = clk[2]) => (ann[1] = ann[2] /\ own[1] = own[2] /\ guard[1] = guard[2])
\* P2 at different clocks they differ only across some held age row's expires_at
Inv_ClockOnlyAtExpiry ==
  (held[1] = held[2] /\ (ann[1] # ann[2] \/ own[1] # own[2] \/ guard[1] # guard[2])) =>
    \E r \in held[1] \cap AgeRows : r.exp # 0 /\ ((clk[1] < r.exp /\ r.exp <= clk[2]) \/ (clk[2] < r.exp /\ r.exp <= clk[1]))
\* P3 the announcement kept as rows arrived and clocks ticked is the set function of the rows held now, at
\* the node's clock
Inv_Fold == \A n \in Nodes : ann[n] = Announced(held[n], clk[n]) /\ own[n] = OwnerCounts(held[n], clk[n])
                                /\ guard[n] = GuardLive(held[n], clk[n])
\* P4 no order leaves a person announced whose current band reads minor
Inv_NoMinorAnnounced == \A n \in Nodes : ann[n] => HeldBand(held[n], clk[n]) # "minor"
\* P5 supersession lifts: a minor row whose signer holds a newer, unretracted row is no longer standing, so
\* dropping it changes nothing
Inv_SupersededLifts ==
  \A n \in Nodes : \A m \in held[n] : (IsMinor(m) /\ \E a \in held[n] \cap AgeRows : a.s = m.s /\ a.at > m.at /\ ~Retracted(held[n], a))
    => ann[n] = Announced(held[n] \ {m}, clk[n])
\* P6 outranking lifts: with the subject's current row not minor, the rows of a witness below a witness with
\* a current row decide nothing
Inv_OutrankedLifts ==
  \A n \in Nodes : \A w, v \in MS!Witnesses :
    (MS!Level(w) < MS!Level(v) /\ SB(held[n], v, clk[n]) # "none" /\ SB(held[n], 0, clk[n]) # "minor")
      => ann[n] = Announced({r \in held[n] : ~(r \in AgeRows /\ r.s = w)}, clk[n])
\* P7 the subject's lower self-declaration still blocks
Inv_SelfLowerBlocks == \A n \in Nodes : SB(held[n], 0, clk[n]) = "minor" => ~ann[n]
\* P8 an equal-level disagreement blocks: a witness at the top level with a current minor row
Inv_EqualLevelBlocks ==
  \A n \in Nodes : \A w \in MS!Witnesses :
    (SB(held[n], w, clk[n]) = "minor" /\ \A v \in MS!Witnesses : SB(held[n], v, clk[n]) # "none" => MS!Level(v) <= MS!Level(w))
      => ~ann[n]
\* P9 the void reads what the standing protection lets go: while the person is announced, any held minor row
\* (superseded, outranked or retracted) with no assured adult proof before it still voids a duty appointment
\* dated at its instant. MinorVoid's clause 1 counts the row; the current band does not.
Inv_VoidKeepsWhatStandingLifts ==
  \A n \in Nodes : \A m \in held[n] :
    (ann[n] /\ IsMinor(m) /\ ~LiveProofBefore(held[n], m.at)) => VoidAt(held[n], m.at)
\* Witness for P9 (MinorVoid's difference made visible): StandingProtection_void_witness.cfg checks this and
\* TLC reports a state where a node is announced while a minor row is held
NoMinorRowWhileAnnounced == \A n \in Nodes : ann[n] => ~\E m \in held[n] : IsMinor(m)
\* P10 a minor row arriving that makes the band read minor pulls the announcement back
Prop_MinorPullsBack ==
  [][\A n \in Nodes : ((held'[n] \ held[n]) \cap AgeRows # {} /\ HeldBand(held'[n], clk'[n]) = "minor") => ~ann'[n]]_vars
\* P11 a withdrawal after which the band no longer reads minor restores the announcement
Prop_WithdrawalRestores ==
  [][\A n \in Nodes : ((held'[n] \ held[n]) \cap RetractRows # {} /\ Bind \in held'[n]
                         /\ HeldBand(held'[n], clk'[n]) # "minor") => ann'[n]]_vars
\* P12 no carve-out by scope (CC 3.2 l.961): the federation-scope binding counts exactly when the self-scope
\* binding does, and the self-scope binding counts for nothing while the band reads minor
Inv_NoScopeCarveOut == \A n \in Nodes : (Bind \in held[n] => ann[n] = own[n]) /\ (HeldBand(held[n], clk[n]) = "minor" => ~own[n])
\* P13 the guardianship ends only when the band reads adult, which needs an assured (witness) current row
Inv_GuardEndsOnlyByAssurance == \A n \in Nodes : ~guard[n] => \E w \in MS!Witnesses : SB(held[n], w, clk[n]) = "adult"
\* P14 a self-declaration never ends the guardianship: the subject's own rows alone keep it standing
Inv_SelfDeclarationKeepsGuardian ==
  \A n \in Nodes : GuardLive({r \in held[n] : r \in RetractRows \/ (r \in AgeRows /\ r.s = 0)}, clk[n])
\* P15 the person is always under a guardian or counted as an owner, never neither; both while no band is read
Inv_GuardOrOwner == \A n \in Nodes : guard[n] \/ own[n]
==========================================================================
