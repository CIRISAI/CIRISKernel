----------------------------- MODULE ReaderLine -----------------------------
(* The roster head and a reader's own acknowledged line (KERNEL.md sections 7 and 8a; CC 2.7.8; proved as
   Reader.line_voids_old_fork, old_fork_void_for_ever, sibling_waits, merge_accepted; crates/ciris-kernel
   line::settle, line::void).
   A roster lineage: v0 founds it, v1 extends v0, v2 extends v1. A fork u extends the old head v0 (signed by
   keys that once met its count), and u2 extends u. A sibling s extends v1, the head v2 is counted over. m names
   v2 and s, joining the two tips. Two readers receive the versions in ANY order, each on its own. Reader R1 may
   acknowledge v2 at any point after holding it; reader R2 never acknowledges anything.
   The reading is Reader.lean's (checkpoint.py `behind`). A version is left behind by the reader's line when it
   is concurrent with a version of the line, and every head it names is strictly older than every head that
   version names. A version built on a void version is void.
   Checked, per reader:
   - the void set is a function of what the reader holds and what it acknowledged;
   - R1, having acknowledged v2, holds u and u2 void;
   - the sibling s waits as a tip and m is accepted;
   - R2 holds nothing void, since the voiding is the reader's own;
   - void is for ever.
   MUT = TRUE plants the break: one reader's acknowledgement voids for every reader. *)
EXTENDS Naturals, FiniteSets
CONSTANTS MUT
Vs == {"v0", "v1", "v2", "u", "u2", "s", "m"}
Builds == [v \in Vs |-> CASE v = "v0" -> {} [] v = "v1" -> {"v0"} [] v = "v2" -> {"v1"} [] v = "u" -> {"v0"}
                            [] v = "u2" -> {"u"} [] v = "s" -> {"v1"} [] v = "m" -> {"v2", "s"}]
Readers == {"R1", "R2"}

RECURSIVE Anc(_)
Anc(v) == Builds[v] \cup UNION {Anc(b) : b \in Builds[v]}

VARIABLES held, acked, void
vars == <<held, acked, void>>

RECURSIVE Grow(_, _)
Grow(H, W) == LET ready == {x \in W : Builds[x] \subseteq H} IN IF ready = {} THEN H ELSE Grow(H \cup ready, W \ ready)

\* the reader's line: the versions it acknowledged and every version in their past
Line(A) == A \cup UNION {Anc(h) : h \in A}
Conc(x, y) == x # y /\ ~(x \in Anc(y)) /\ ~(y \in Anc(x))
OlderHeads(v, l) == Builds[v] # {} /\ \A b \in Builds[v] : \A c \in Builds[l] : b \in Anc(c)
Behind(v, H, A) == v \notin Line(A) /\ \E l \in Line(A) \cap H : Conc(v, l) /\ OlderHeads(v, l)
\* the reader's void set, by recursion on ancestry (rows of lower depth first)
RECURSIVE VoidSet(_, _, _)
VoidSet(H, A, todo) == IF todo = {} THEN {} ELSE
    LET v == CHOOSE x \in todo : \A y \in todo : ~(x \in Anc(y))   \* a highest row: its past is decided first
        rest == VoidSet(H, A, todo \ {v})
    IN IF Behind(v, H, A) \/ (\E b \in Builds[v] : b \in rest) THEN rest \cup {v} ELSE rest
Void(H, A) == VoidSet(H, A, H)

Init == held = [r \in Readers |-> {}] /\ acked = [r \in Readers |-> {}] /\ void = [r \in Readers |-> {}]

Deliver(r, v) == /\ v \notin held[r]
                 /\ Builds[v] \subseteq held[r]          \* the door: a version waits for what it extends
                 /\ held' = [held EXCEPT ![r] = @ \cup {v}]
                 /\ void' = [q \in Readers |-> Void(held'[q], IF MUT THEN acked["R1"] \cup acked["R2"] ELSE acked[q])]
                 /\ UNCHANGED acked
Ack(r) == /\ r = "R1" /\ "v2" \in held[r] /\ acked[r] = {}
          /\ acked' = [acked EXCEPT ![r] = {"v2"}]
          /\ void' = [q \in Readers |-> Void(held[q], IF MUT THEN acked'["R1"] \cup acked'["R2"] ELSE acked'[q])]
          /\ UNCHANGED held
Done == (\A r \in Readers : held[r] = Vs) /\ UNCHANGED vars

Next == (\E r \in Readers, v \in Vs : Deliver(r, v)) \/ (\E r \in Readers : Ack(r)) \/ Done
Spec == Init /\ [][Next]_vars

\* L1 per reader, the void set is a function of what the reader holds and acknowledged
Inv_Function == \A r \in Readers : void[r] = Void(held[r], acked[r])
\* L2 the line voids the old-head fork for the reader that acknowledged the newer head
Inv_LineVoids == ("v2" \in acked["R1"] /\ "u" \in held["R1"]) => "u" \in void["R1"] /\
                 ("u2" \in held["R1"] => "u2" \in void["R1"])
\* L3 the voiding binds nobody else: a reader with no acknowledgement holds nothing void
Inv_OwnOnly == void["R2"] = {}
\* L4 a version naming both tips, and the acknowledged line itself, are never void
Inv_MergeStands == "s" \notin void["R1"] /\ "m" \notin void["R1"] /\ Line(acked["R1"]) \cap void["R1"] = {}
\* L5 void for ever: once void for a reader, void in every later state
Prop_VoidForEver == [][\A r \in Readers : void[r] \subseteq void'[r]]_vars
==========================================================================
