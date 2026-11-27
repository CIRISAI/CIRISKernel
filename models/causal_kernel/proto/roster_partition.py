#!/usr/bin/env python3
"""The roster partition run (a probe, not a check; pending the Constitution's ruling on a roster merge).

Two halves of a room make counted changes after a fork at P = aG (check_count_heads' ROOM, seven members; C, D and E
sign on both sides): side 1 admits H then K, side 2 admits J then L. Readers R1 and R2 acknowledge their own side's
newest change; then every row is held. Printed per reader: the members, the stale changes, and what concludes, for
the rows as held, a later acknowledgement of the other side, a merge naming both tips (by all, and by one side), and
one side acting again forward. Under the monotone line no row both sides' readers accept brings the room back to one
roster.

Run: python3 -I models/causal_kernel/proto/roster_partition.py .
"""
import sys, os
sys.path.insert(0, os.path.join(sys.argv[1] if len(sys.argv) > 1 else ".", "models/causal_kernel"))
sys.dont_write_bytecode = True
import seat as ST, check_count_heads as CH
CK = ST.CK; admit, ack, ROOM = CH.admit, CH.ack, CH.ROOM
S7 = tuple("ABCDEFG")
# the fork at P = aG (seven members). C, D and E are on both sides (their devices split); side 1 has A and B, side 2 F and G
x1 = admit("x1", "H", ("A", "B", "C", "D", "E"), ("aG",))            # side 1 admits H: 5 of 7
x2 = admit("x2", "J", ("C", "D", "E", "F", "G"), ("aG",))            # side 2 admits J: 5 of 7
y1 = admit("y1", "K", ("A", "B", "C", "D", "E", "H"), ("x1",))       # side 1: 6 of 8
y2 = admit("y2", "L", ("C", "D", "E", "F", "G", "J"), ("x2",))       # side 2: 6 of 8
k1 = ack("k1", "R1", "y1"); k2 = ack("k2", "R2", "y2")
base = ROOM + [x1, x2, y1, y2, k1, k2]
def show(name, rows, own):
    S = CK.concluded(CK.kept(list(rows)), lambda r, P, past: ST.seat_rule(r, P, past))
    Q = ST.Seats(S, own=own)
    print("%-72s reader %-4s members %s | stale %s | concluded %s" % (name, own, "".join(sorted(Q.holders("member", "g"))),
          sorted(Q.stale), {i: bool(S.C.get(i)) for i in ("x1", "x2", "y1", "y2", "m", "z", "m2") if i in S.by}))
for own in (None, "R1", "R2"):
    show("the halves met: both sides held", base, own)
show("R1 then acknowledges y2 too (naming y1 and y2)", base + [CK.row("k1b", "ack", "R1", ("y1", "y2", "k1"), room="g", head=("y1", "y2"))], "R1")
m = admit("m", "M", tuple("ABCDEFGHJKL"), ("y1", "y2"))
for own in (None, "R1", "R2"):
    show("a merge m naming y1 and y2, signed by all eleven", base + [m], own)
m2 = admit("m2", "M", ("A", "B", "C", "D", "E", "H", "K"), ("y1", "y2"))
for own in (None, "R1", "R2"):
    show("a merge m2 by side 1 alone (A B C D E H K)", base + [m2], own)
z = admit("z", "J", ("A", "B", "C", "D", "E", "H", "K"), ("y1",))
for own in (None, "R1", "R2"):
    show("side 1 acts again forward: re-admits J at y1", base + [z], own)
