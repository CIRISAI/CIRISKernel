"""The tips prototype's cases: each (name, rows, reader, the row asked). Printed answer: does it conclude; members."""
import sys, os
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import seat as ST, check_count_heads as CH
CK = ST.CK; OBJ = "g"
admit, remove, ack, ROOM, FIVE = CH.admit, CH.remove, CH.ack, CH.ROOM, CH.FIVE
DCg = ST.offer("dc", "A", "B", "moderate", OBJ, "group", ("g",), head=("g",), policy="duty_confer", counted="duty", cosigners=("B",))
XD = admit("xd", "X", ("A", "B"), ("dc",))
CG = ("C", "D", "E", "F", "G")
C = []
def case(name, rows, ask, own=None): C.append((name, rows, ask, own))
case("H7a C..G remove A at aG citing dc", ROOM + [DCg, remove("xa", "A", CG, ("aG",), ("dc",))], "xa")
case("H7b C..G remove A at aG citing xd", ROOM + [DCg, XD, remove("xa", "A", CG, ("aG",), ("xd",))], "xa")
case("H7c C..G remove A at (xd, aG)", ROOM + [DCg, XD, remove("xa", "A", CG, ("xd", "aG"))], "xa")
case("H7d control: C..G remove A at aG", ROOM + [remove("xa", "A", CG, ("aG",))], "xa")
# t2: strip by repeated tips
d = lambda i, to: ST.offer(i, "A", to, "moderate", OBJ, "group", ("g",), head=("g",), policy="duty_confer", counted="duty", cosigners=(to,))
T2 = ROOM + [d("d1", "B"), remove("x1", "G", ("A", "B"), ("d1", "aG"))]
case("T2 step1: A,B remove G at (d1, aG)", T2, "x1")
T2b = T2 + [d("d2", "C"), remove("x2", "F", ("A", "B"), ("d2", "x1"))]
case("T2 step2: A,B remove F at (d2, x1)", T2b, "x2")
case("T2 step2, reader D", T2b, "x2", "D")
# room of one
G1 = ST.found("g", "A", ("A",), None)
N1 = admit("n1", "N1", ("A",), ("g",))
case("room of one: tip t at g, A removes N1 at (t, n1)", [G1, N1, admit("t", "Z", ("A",), ("g",)), remove("xn", "N1", ("A",), ("t", "n1"))], "xn")
case("room of one: N3 by A at (n1, n2)", [G1, N1, admit("n2", "N2", ("A",), ("g",)), admit("n3", "N3", ("A",), ("n1", "n2"))], "n3")
# lone offer self path
case("LO3 A's own offers s1 then s2", ROOM + [ST.offer("s1", "A", "B", "moderate", OBJ, "self", ("aG",)),
                                         ST.offer("s2", "A", "C", "moderate", OBJ, "self", ("s1",), cosigners=("C",))], "s2")
# (a) a hostile signer among the honest voices
case("(a) A (forked: dc, xd) among the voices removing B at aG, citing xd", ROOM + [DCg, XD, remove("xb", "B", ("A",) + CG, ("aG",), ("xd",))], "xb")
case("(a') the same naming (xd, aG)", ROOM + [DCg, XD, remove("xb", "B", ("A",) + CG, ("xd", "aG"))], "xb")
# (b) honest siblings at one head, C signed only T1, D only T2
S7 = tuple("ABCDEFG")
T1r = admit("t1", "X", tuple(k for k in S7 if k != "D"), ("aG",))
T2r = admit("t2", "Y", tuple(k for k in S7 if k != "C"), ("aG",))
case("(b) siblings t1 (no D), t2 (no C); A..F, X, Y remove G at (t1, t2)", ROOM + [T1r, T2r, remove("xg", "G", tuple("ABCDEFXY"), ("t1", "t2"))], "xg")
case("(b') the same, signed by C, D and four others (6 of 9)", ROOM + [T1r, T2r, remove("xg", "G", tuple("ABCDEF"), ("t1", "t2"))], "xg")
# (c) the attackers' own row: packing from g
def packed(n):
    rows, sg, prev = list(ROOM), ["A", "B"], "g"
    for i in range(1, n + 1):
        rows.append(admit("p%d" % i, "X%d" % i, tuple(sg), (prev,))); sg.append("X%d" % i); prev = "p%d" % i
    return rows + [remove("xd", "D", tuple(sg), ("aG", prev))]
for n in (2, 8):
    case("(c) packing n=%d: A,B,X.. remove D at (aG, p%d)" % (n, n), packed(n), "xd")
    case("(c) packing n=%d, reader D" % n, packed(n), "xd", "D")
# (d) stacking for V3: A's lone conferral at aD makes the honest aE stale within r's past
SD = ST.offer("sd", "A", "B", "moderate", OBJ, "group", ("aD",), head=("aD",), policy="duty_confer", counted="duty", cosigners=("B",))
case("(d) A's lone conferral sd at aD; honest C..G remove A at (sd, aG)", ROOM + [SD, remove("xa", "A", CG, ("sd", "aG"))], "xa")
case("(d') the same; A,B remove G at (sd, aG)", ROOM + [SD, remove("xg", "G", ("A", "B"), ("sd", "aG"))], "xg")
case("(d'') the same; A,B remove G at (sd, aG), reader E", ROOM + [SD, remove("xg", "G", ("A", "B"), ("sd", "aG"))], "xg", "E")
# antichain, window, community_invite missing yes
case("antichain: five remove G at (g, aG)", ROOM + [remove("xg", "G", FIVE, ("g", "aG"))], "xg")
ax = ST.offer("ax", "A", "X", "member", OBJ, "group", ("g",), head=("g",), policy="community_invite", cosigners=("B",))
case("CC1b invitation without X's yes as a tip: A,B remove G at (ax, aG)", ROOM + [ax, remove("xg", "G", ("A", "B"), ("ax", "aG"))], "xg")
# tightened rules: a room founded under `majority`; the honest line admits D..G, then raises the protocol to
# two_thirds (am); A and B pack from g under the old rule. The honest C..G then remove A at (am, pn), having seen pn
GM = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("A",)}, cosigners=("B", "C"), consensus_protocol="majority")
def hadm(i, k, sg, prev): return ST.offer(i, sg[0], k, "member", OBJ, "group", (prev,), head=(prev,), policy="cosigned_act",
                                          cosigners=tuple(sg[1:]) + (k,))
RM, mem, prev = [GM], ["A", "B", "C"], "g"
for k in "DEFG":
    RM.append(hadm("a" + k, k, tuple(mem), prev)); mem.append(k); prev = "a" + k
AM = ST.offer("am", "A", "g", "record", OBJ, "group", ("aG",), head=("aG",), policy="cosigned_act",
              consensus_protocol="two_thirds", cosigners=tuple("BCDEFG"))
def tight(n):
    rows, sg, prev = RM + [AM], ["A", "B"], "g"
    for i in range(1, n + 1):
        rows.append(hadm("p%d" % i, "X%d" % i, tuple(sg), prev)); sg.append("X%d" % i); prev = "p%d" % i
    heads = ("am", prev) if n else ("am",)
    return rows + [ST.unseat("xa", "C", "A", "member", OBJ, "group", heads, head=heads, policy="community_remove",
                             cosigners=("D", "E", "F", "G"))]
for n in (0, 1, 2, 8):
    case("tightened (majority to two_thirds at am); A,B pack n=%d at g under majority; C..G remove A at (am, p%d)" % (n, n), tight(n), "xa")
# L' (the honest chain's first change signed only by the later forkers), from lprime.py
import importlib.util as _u
_sp = _u.spec_from_file_location("lprime", os.path.join(os.path.dirname(os.path.abspath(__file__)), "lprime.py"))
LP = _u.module_from_spec(_sp); _sp.loader.exec_module(LP)
for _n, _rows in LP.W.items():
    case(_n + ": C..G remove A at (xd, aG)", _rows + [LP.rem("xa", "A", ("C", "D", "E", "F", "G"), ("xd", "aG"))], "xa")
# forkers that never acknowledged the honest line, under a tightened rule: a quorum-of-two room founded by A..F; the
# honest C..F admit G and raise the protocol to two_thirds (am); A and B pack from g under the old quorum
GQ = ST.found("g", "A", tuple("ABCDEF"), {"moderate": ("A",)}, cosigners=tuple("BCDEF"), consensus_protocol="quorum")
AG2 = LP.adm("ag2", "G", ("C", "D", "E", "F"), ("g",))
AMQ = ST.offer("amq", "C", "g", "record", OBJ, "group", ("ag2",), head=("ag2",), policy="cosigned_act", need=2,
               consensus_protocol="two_thirds", cosigners=("D", "E", "F", "G"))
def quiet(n):
    rows, sg, prev = [GQ, AG2, AMQ], ["A", "B"], "g"
    for i in range(1, n + 1):
        rows.append(LP.adm("q%d" % i, "X%d" % i, tuple(sg), (prev,))); sg.append("X%d" % i); prev = "q%d" % i
    heads = ("amq", prev) if n else ("amq",)
    return rows + [ST.unseat("xa", "C", "A", "member", OBJ, "group", heads, head=heads, policy="community_remove",
                             cosigners=("D", "E", "F", "G"))]
for n in (0, 2, 8):
    case("quiet forkers (never signed the honest line), quorum to two_thirds; pack n=%d; C..G remove A" % n, quiet(n), "xa")
if __name__ == "__main__":
    for name, rows, ask, own in C:
        S = CK.concluded(CK.kept(list(rows)), CH.RULE)
        Q = ST.Seats(S, own=own)
        st = ("/void" if ask in Q.stale else "/live") if own else ""
        print("%s\t%s%s\t%s" % (name, "T" if S.C.get(ask) else "F", st, "".join(sorted(Q.holders("member", OBJ)))))
