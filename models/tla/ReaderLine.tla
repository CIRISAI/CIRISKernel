----------------------------- MODULE ReaderLine -----------------------------
(* The roster head and a reader's own acknowledged line (KERNEL.md sections 7 and 8a; CC 2.7.8; proved as
   Reader.line_voids_old_fork, old_fork_void_for_ever, sibling_by_acknowledgement; crates/ciris-kernel
   line::settle, line::void, line::versions).
   A roster lineage v0 .. vD, each extending the one before. A fork u extends the founding head v0 and u2
   extends u: keys that once met an old count sign a line of their own. A sibling s extends v(D-1), as vD
   does, and m names vD and s, joining the two tips. Every reader receives the versions in ANY order, each on
   its own, and may acknowledge any one version it holds, at any point.
   The reading is CC 2.7.8's: "Two versions of one head wait as tips", and "a reader that has acknowledged a
   head holds void every counted act that names an older head and is not in that head's past". A version
   concurrent with an act of the reader's line is void for that reader when it names only versions in that
   act's past. A version built on a void version is void.
   Checked, per reader:
   - the void set is a function of what the reader holds and acknowledged (the voiding is the reader's own);
   - with no acknowledgement nothing is void, so siblings wait as tips;
   - with one, every held version concurrent with the acknowledged act that names only heads in its past is
     void (the fork, and a sibling of the acknowledged act);
   - the reader's own line is never void;
   - void is for ever.
   Readers are interchangeable (SYMMETRY in the large configuration).
   MUT = TRUE plants the break: every reader's acknowledgement voids for every reader. *)
EXTENDS Naturals, FiniteSets, TLC
CONSTANTS MUT, D, Readers
Vs == {<<"v", i>> : i \in 0..D} \cup {<<"u", 1>>, <<"u", 2>>, <<"s", 0>>, <<"m", 0>>}
Builds(v) == CASE v[1] = "v" -> (IF v[2] = 0 THEN {} ELSE {<<"v", v[2] - 1>>})
               [] v = <<"u", 1>> -> {<<"v", 0>>}
               [] v = <<"u", 2>> -> {<<"u", 1>>}
               [] v[1] = "s" -> {<<"v", D - 1>>}
               [] v[1] = "m" -> {<<"v", D>>, <<"s", 0>>}

RECURSIVE Anc(_)
Anc(v) == Builds(v) \cup UNION {Anc(b) : b \in Builds(v)}
AncOf == [v \in Vs |-> Anc(v)]

VARIABLES held, acked, void
vars == <<held, acked, void>>

Line(A) == A \cup UNION {AncOf[h] : h \in A}
Conc(x, y) == x # y /\ ~(x \in AncOf[y]) /\ ~(y \in AncOf[x])
OlderThan(v, l) == Builds(v) # {} /\ \A b \in Builds(v) : b \in AncOf[l]
Behind(v, H, A) == v \notin Line(A) /\ \E l \in Line(A) \cap H : Conc(v, l) /\ OlderThan(v, l)
RECURSIVE VoidSet(_, _, _)
VoidSet(H, A, todo) == IF todo = {} THEN {} ELSE
    LET v == CHOOSE x \in todo : \A y \in todo : ~(x \in AncOf[y])   \* a highest version: its past first
        rest == VoidSet(H, A, todo \ {v})
    IN IF Behind(v, H, A) \/ (\E b \in Builds(v) : b \in rest) THEN rest \cup {v} ELSE rest
Void(H, A) == VoidSet(H, A, H)
AllAcks == UNION {acked[q] : q \in Readers}
Recompute(h, a) == [q \in Readers |-> Void(h[q], IF MUT THEN UNION {a[p] : p \in Readers} ELSE a[q])]

Init == held = [r \in Readers |-> {}] /\ acked = [r \in Readers |-> {}] /\ void = [r \in Readers |-> {}]

Deliver(r, v) == /\ v \notin held[r]
                 /\ Builds(v) \subseteq held[r]          \* the door: a version waits for what it extends
                 /\ held' = [held EXCEPT ![r] = @ \cup {v}]
                 /\ void' = Recompute(held', acked)
                 /\ UNCHANGED acked
Ack(r, v) == /\ v \in held[r] /\ acked[r] = {}
             /\ acked' = [acked EXCEPT ![r] = {v}]
             /\ void' = Recompute(held, acked')
             /\ UNCHANGED held
Done == (\A r \in Readers : held[r] = Vs) /\ UNCHANGED vars

Next == (\E r \in Readers, v \in Vs : Deliver(r, v) \/ Ack(r, v)) \/ Done
Spec == Init /\ [][Next]_vars
Sym == Permutations(Readers)

\* L1 per reader, the void set is a function of what that reader holds and acknowledged
Inv_Function == \A r \in Readers : void[r] = Void(held[r], acked[r])
\* L2 CC 2.7.8, no acknowledgement: nothing is void, so two versions of one head wait as tips
Inv_TipsWaitWithoutAck == \A r \in Readers : acked[r] = {} => void[r] = {}
\* L3 CC 2.7.8, an acknowledgement: what names only heads in the acknowledged act's past is void for that
\*    reader, a sibling of the acknowledged act included
Inv_OlderVoidWithAck == \A r \in Readers : \A a \in acked[r] : \A x \in held[r] \ Line(acked[r]) :
                          (Conc(x, a) /\ OlderThan(x, a)) => x \in void[r]
Inv_SiblingVoid == \A r \in Readers : (acked[r] = {<<"v", D>>} /\ <<"s", 0>> \in held[r]) => <<"s", 0>> \in void[r]
\* L4 the reader's own line is never void
Inv_LineStands == \A r \in Readers : Line(acked[r]) \cap void[r] = {}
\* L5 void for ever
Prop_VoidForEver == [][\A r \in Readers : void[r] \subseteq void'[r]]_vars
==========================================================================
