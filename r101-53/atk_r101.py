"""r101-53: key-person 09923a2, the reader's line. python3 -I atk_r101.py <kp models/causal_kernel>"""
import sys, random
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import check_key_person as KP
ST, CK, WN = KP.ST, KP.CK, KP.WN
RULE, RULE_W = KP.RULE, KP.RULE_W
found, add, evict, admit_z = KP.found, KP.add, KP.evict, KP.admit_z

def per(rows, f, rd, rule=RULE, n=20):
    g = lambda S: f(ST.reader_state(S, rd, rule if rule is not RULE else None))
    got = g(CK.concluded(CK.kept(list(rows)), rule))
    rnd, bad = random.Random(31), 0
    for _ in range(n):
        t = list(rows); rnd.shuffle(t)
        bad += g(CK.arrive(t, rule)) != got
    return got, bad
def show(name, rows, f, readers, rule=RULE):
    print("%-84s %s" % (name, "  ".join("%s:%s%s" % (rd, *(lambda gb: (gb[0], "" if not gb[1] else "(differ %d)" % gb[1]))(per(rows, f, rd, rule)))
                                          for rd in readers)))
C = lambda rid: (lambda S: bool(S.C.get(rid)))
# 1. the branch's own LWORLD, every world x four readers, in arrival orders
print("== LWORLD x readers (az concludes)")
for k, rows in KP.LWORLD.items():
    show("W " + k, rows, C("az"), ("p4", None, "x", "m4", "x9"))
GW = KP.GW
RX = ST.offer("S1r", "p1", ("p1", "x"), "self", "@", "self", cosigners=("x",))
Z = lambda names, sig=("p1b", "p2", "p3"): admit_z(sig, names)
R3 = ("p4", None, "x")
print("== seeding the honest reader's line")
show("S0 control: admit naming a1c, S1r", GW + [RX, Z(("a1c", "S1r"))], C("az"), R3)
show("S1 the thief's row claims p4 as cosigner, naming S1r", GW + [RX, ST.R("sd", "note", "p1", ("S1r",), cosigners=("p4",)), Z(("a1c", "S1r"))], C("az"), R3)
show("S2 p4 signs over S1r (P2 again)", GW + [RX, ST.R("v4", "note", "p4", ("S1r",)), Z(("a1c", "S1r"))], C("az"), R3)
REC = ST.offer("rec4", "p4", "p4", "registered", "p4", "self", ("gc",)); RV = ST.unseat("rv4", "p4", "p4", "registered", "p4", "self", ("rec4",))
show("S3 p4 revoked itself, then its (stolen) key signs over S1r", GW + [RX, REC, RV, ST.R("v4", "note", "p4", ("S1r", "rv4")), Z(("a1c", "S1r"))], C("az"), R3)
show("S3' p4 revoked itself, no further rows: its line still takes S1?", GW + [RX, REC, RV, Z(("a1c", "S1r"))], C("az"), R3)
show("S4 p4 signs over S1r and THEN revokes itself", GW + [RX, ST.R("v4", "note", "p4", ("S1r",)), dict(REC, names=("v4",)), RV, Z(("a1c", "S1r"))], C("az"), R3)
print("== descendants of the rival, reader p4")
OY = ST.offer("oy", "p1", "y", "self", "S1r", "group", ("S1r",), head=("S1r",), policy="self_roster_add", counted="self", cosigners=("x",))
AY = ST.accept("ay", "y", "oy"); WY = ST.withdraw("wy", "y", "ay", ("ay",))
show("V1 offer over S1r: oy concludes", GW + [RX, OY], C("oy"), R3)
show("V2 y's acceptance of oy concludes", GW + [RX, OY, AY], C("ay"), R3)
show("V3 y's withdrawal of that acceptance concludes", GW + [RX, OY, AY, WY], C("wy"), R3)
ND = ST.offer("ndb", "nd", "x", "owner", "nd", "self", ("S1r",), cosigners=("x",))
show("V4 x (a rival key) owns node nd: nodes_of(x)", GW + [RX, ND], lambda S: sorted(ST.nodes_of(S, "x")), R3)
show("V5 person_keys(p1)", GW + [RX, ND], lambda S: sorted(ST.person_keys(S, "p1")), R3)
show("V6 x signs into the room: x+p2+p3 admit naming a1c (no S1r in its past)", GW + [RX, Z(("a1c",), ("x", "p2", "p3"))], C("az"), R3)
print("== landed windows")
EW, AW = WN.secs("self_roster_evict"), WN.secs("self_roster_add")
def lone_add(obj, opener, k, head, objectors=(), pid="op"):
    rows = [dict(WN.opener(pid, opener, "self_roster_add", obj, head, target=k), to=(k,), cosigners=(k,))]
    rows += [WN.answer("o" + o, o, pid, "object", (pid,)) for o in objectors]
    rows += [WN.receipt("r", opener, pid, 0), WN.landing("L", opener, pid, "r", "landed", AW, tuple("o" + o for o in objectors))]
    return rows
LR = lone_add("S1r", "p1", "y", ("S1r",))
show("L1 a landed add over the rival S1r: y in S1r holders", GW + [RX] + LR, lambda S: sorted(ST.Seats(S).holders("self", "S1r")), R3, RULE_W)
show("L1' ... person_keys(p1)", GW + [RX] + LR, lambda S: sorted(ST.person_keys(S, "p1")), R3, RULE_W)
# the live thief genesis p1 lone-adds its own key k9 to the HONEST roster S1 (no rival needed)
for obs in ((), ("p1b",), ("p1b", "p1c")):
    LH = lone_add("S1", "p1", "k9", ("a1c",), obs)
    show("L2 thief p1 lone-adds k9 to S1, objections %s: outcome" % (obs,), GW + LH, lambda S: WN.outcome(S, "op", "recount"), ("p4", None), RULE_W)
    show("L2' ... person_keys(p1)", GW + LH, lambda S: sorted(ST.person_keys(S, "p1")), ("p4", None), RULE_W)
