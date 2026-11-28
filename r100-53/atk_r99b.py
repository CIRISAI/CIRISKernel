"""r99-53 part 2: key-person 517d70e. python3 -I atk_r99b.py <kp models/causal_kernel>"""
import sys, random
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import check_key_person as KP, check_conferral_two as C2
ST, CK, WN = KP.ST, KP.CK, KP.WN
RULE, RULE_W = KP.RULE, KP.RULE_W
found, add, evict, admit_z = KP.found, KP.add, KP.evict, KP.admit_z

def show(name, rows, f, rule=RULE):
    got = f(CK.concluded(CK.kept(list(rows)), rule))
    rnd, bad = random.Random(17), 0
    for _ in range(60):
        t = list(rows); rnd.shuffle(t)
        bad += f(CK.arrive(t, rule)) != got
    print("%-100s %s differ=%d/60" % (name, got, bad))
C = lambda rid: (lambda S: bool(S.C.get(rid)))
GW, GEV, GS, GD1, lone = KP.GW, KP.GEV, KP.GS, KP.GD1, KP.lone_evict
# lone path races
both = [GS, GD1] + lone("k1", "g1", False) + lone("g1", "k1", False, "op2", "2")
show("M1 k1 evicts g1 AND g1 evicts k1, both silent, concurrent: holders of S", both, lambda S: sorted(ST.Seats(S).holders("self", "S")), RULE_W)
show("M1' ... person_keys(g1)", both, lambda S: sorted(ST.person_keys(S, "g1")), RULE_W)
show("M2 after M1, k1 alone adds k3 naming both landings", both + [add("d3", "S", "k3", ("k1",), ("L", "L2"))], C("d3"), RULE_W)
# a landing by a key that is not the opener
LX = [GS, GD1, WN.opener("op", "k1", "self_roster_evict", "S", ("d1",), target="g1"), WN.receipt("r", "zz", "op", 0),
      WN.landing("L", "zz", "op", "r", "landed", WN.secs("self_roster_evict"))]
show("M3 an outsider zz writes the receipt and landing of k1's proposal: holders", LX, lambda S: sorted(ST.Seats(S).holders("self", "S")), RULE_W)
# an opener by an outsider against g1
LO = [GS, GD1, WN.opener("op", "zz", "self_roster_evict", "S", ("d1",), target="g1"), WN.receipt("r", "zz", "op", 0),
      WN.landing("L", "zz", "op", "r", "landed", WN.secs("self_roster_evict"))]
show("M4 an outsider zz opens and lands an eviction of g1: holders", LO, lambda S: sorted(ST.Seats(S).holders("self", "S")), RULE_W)
# 3-key roster: does the lone path let ONE key evict another where the count needs two?
GD2 = add("d2", "S", "k2", ("g1", "k1"), ("d1",))
L3 = [GS, GD1, GD2, WN.opener("op", "k1", "self_roster_evict", "S", ("d2",), target="g1"), WN.receipt("r", "k1", "op", 0),
      WN.landing("L", "k1", "op", "r", "landed", WN.secs("self_roster_evict"))]
show("M5 3-key roster: k1 alone lone-evicts g1, g1 and k2 silent: holders", L3, lambda S: sorted(ST.Seats(S).holders("self", "S")), RULE_W)
# the stalling rival, taken up by a thief's row the honest count builds on
RIV = found("S1r", "p1")
T = ST.cosign("t", "p1", "t", ("S1r",))                                  # the thief names only its rival
show("D8 thief row t names S1r; honest p1b+p2+p3 admit z naming evg and t", GW + [GEV, RIV, T, admit_z(("p1b", "p2", "p3"), ("evg", "t"))], C("az"))
T2 = ST.cosign("t2", "p1", "t2", ("S1r", "a1c"))                          # names its rival and the honest roster's head
show("D9 thief row t2 names S1r and a1c; honest admit names evg and t2", GW + [GEV, RIV, T2, admit_z(("p1b", "p2", "p3"), ("evg", "t2"))], C("az"))
show("D10 no eviction: thief (genesis) t2; honest p1b+p2+p3 admit names a1c and t2", GW + [RIV, T2, admit_z(("p1b", "p2", "p3"), ("a1c", "t2"))], C("az"))
# N7 with node fields
G0 = {"id": "G0", "kind": "bundle", "signer": "count", "names": []}
B0 = {"id": "B0", "kind": "binding", "signer": "N", "names": [], "owner": "O1", "on": None, "node": "N"}
B1 = {"id": "B1", "kind": "binding", "signer": "N", "names": ["B0"], "owner": "O2", "on": "B0", "node": "N"}
B2 = {"id": "B2", "kind": "binding", "signer": "N", "names": ["B1"], "owner": "O1", "on": "B1", "node": "N"}
A = lambda cites, names, i="A", s="O1": {"id": i, "kind": "acceptance", "signer": s, "names": list(names), "on": cites[0], "cites": list(cites)}
X = lambda names, on="A", i="x1": {"id": i, "kind": "act", "signer": "N", "names": list(names), "head": "G0", "on": on}
def full(rows):
    return {k: {kk: v.get(kk) for kk in ("reason", "binding", "counted", "in_force")} for k, v in sorted(C2.chain_answers(rows).items())}
print("A0 control:", full([G0, B0, A(["B0"], ["B0"]), X(["G0", "A"])]))
print("A1 B1 concurrent with A:", full([G0, B0, B1, A(["B0"], ["B0"]), X(["G0", "A"])]))
print("A2 B1 in the act's past:", full([G0, B0, B1, A(["B0"], ["B0"]), X(["G0", "A", "B1"])]))
print("A5 B0->B1->B2 back to O1, old acceptance:", full([G0, B0, A(["B0"], ["B0"]), B1, B2, X(["G0", "A", "B2"])]))
print("A6 new acceptance citing B2:", full([G0, B0, B1, B2, A(["B2"], ["B2"], "A2"), X(["G0", "A2"], "A2")]))
BX = dict(B0, id="BX", node="M")
print("A7 cites O1's binding of node M:", full([G0, BX, A(["BX"], ["BX"]), X(["G0", "A"])]))
print("A8 O2 cites B1 while B1 is concurrent with B0's ... (O2 accepts B1 with B0 rival? no) control:", full([G0, B0, B1, A(["B1"], ["B1"], "A", "O2"), X(["G0", "A"])]))
print("spec self_roster_evict:", WN.WINDOWS["self_roster_evict"])
def L3o(objectors):
    rows = [GS, GD1, GD2, WN.opener("op", "k1", "self_roster_evict", "S", ("d2",), target="g1")]
    rows += [WN.answer("o" + k, k, "op", "object", ("op",)) for k in objectors]
    rows += [WN.receipt("r", "k1", "op", 0), WN.landing("L", "k1", "op", "r", "landed", WN.secs("self_roster_evict"), tuple("o" + k for k in objectors))]
    return rows
for obs in ((), ("g1",), ("k2",), ("g1", "k2")):
    show("M6 3-key: k1 lone-evicts g1, objections %s: outcome, holders" % (obs,), L3o(obs),
         lambda S: (WN.outcome(S, "op", "recount"), sorted(ST.Seats(S).holders("self", "S"))), RULE_W)
