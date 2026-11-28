"""r99-53: key-person da43735. python3 -I atk_r99.py <kp models/causal_kernel>"""
import sys, random
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import check_key_person as KP, check_conferral_two as C2
ST, CK, WN = KP.ST, KP.CK, KP.WN
RULE, RULE_W = KP.RULE, KP.RULE_W
found, add, evict, admit_z = KP.found, KP.add, KP.evict, KP.admit_z


def stable(rows, f, rule=RULE):
    got = f(CK.concluded(CK.kept(list(rows)), rule))
    rnd, bad = random.Random(13), 0
    for _ in range(60):
        t = list(rows); rnd.shuffle(t)
        bad += f(CK.arrive(t, rule)) != got
    return got, bad


def show(name, rows, f, rule=RULE):
    got, bad = stable(rows, f, rule)
    print("%-96s %s differ=%d/60" % (name, got, bad))


C = lambda rid: (lambda S: bool(S.C.get(rid)))
GW, GEV = KP.GW, KP.GEV
# L: the two-key lone path: does a landed eviction take effect?
GS, GD1, lone = KP.GS, KP.GD1, KP.lone_evict
LK = GS_rows = [GS, GD1] + lone("k1", "g1", False)
show("L0 k1 proposes evicting g1, g1 silent: window outcome", LK, lambda S: WN.outcome(S, "op", "recount"), RULE_W)
show("L1 ... then is g1 still a live key of S (Seats holders self)?", LK, lambda S: sorted(ST.Seats(S).holders("self", "S")), RULE_W)
show("L2 ... person_keys(g1)", LK, lambda S: sorted(ST.person_keys(S, "g1")), RULE_W)
show("L3 ... rep_of g1 / k1 over the whole set", LK, lambda S: (ST.rep_of(list(S.Cs), "g1"), ST.rep_of(list(S.Cs), "k1")), RULE_W)
# L4: g1 (evicted by the lone path) still signs an addition with k1? and alone?
show("L4 after the landing, g1 alone adds k3 to S (naming the landing)", LK + [add("d3", "S", "k3", ("g1",), ("L",))], C("d3"), RULE_W)
show("L5 after the landing, k1 alone adds k3 to S (naming the landing)", LK + [add("d3", "S", "k3", ("k1",), ("L",))], C("d3"), RULE_W)
# D: the rival founding as a DoS by a (stolen) genesis key, at any time: a founding row names nothing, so it is
# concurrent with the honest roster's founding whatever came before
RIV = found("S1r", "p1")                                                    # names nothing: no past
show("D0 control: after the devices evict p1, p1b+p2+p3 admit z", GW + [GEV, admit_z(("p1b", "p2", "p3"), ("evg",))], C("az"))
show("D1 the evicted p1 writes a fresh founding naming nothing; does it conclude?", GW + [GEV, RIV], C("S1r"))
show("D2 ... and p1b+p2+p3 admit z naming it (the honest person's devices)", GW + [GEV, RIV, admit_z(("p1b", "p2", "p3"), ("evg", "S1r"))], C("az"))
show("D3 ... person_keys(p1)", GW + [GEV, RIV], lambda S: sorted(ST.person_keys(S, "p1")))
H = ST.cosign("hh", "p1b", "hh", ("S1", "S1r"))
show("D4 ... a row naming both foundings, then p1b+p2+p3 admit z", GW + [GEV, RIV, H, admit_z(("p1b", "p2", "p3"), ("evg", "hh"))], C("az"))
EVR = evict("evr", "S1r", "p1", ("p1b", "p1c"), ("S1r",))
show("D5 ... the devices try to evict p1 from the rival roster", GW + [GEV, RIV, EVR], C("evr"))
show("D6 no eviction at all: the genesis key (stolen) founds a rival; p1b+p2+p3 admit z", GW + [RIV, admit_z(("p1b", "p2", "p3"), ("a1c", "S1r"))], C("az"))
# the rival also silences a person's honest community seat: is the genesis key in the room still a voice?
show("D7 rival only: p1+p2+p3 admit z", GW + [RIV, admit_z(("p1", "p2", "p3"), ("a1c", "S1r"))], C("az"))
show("D7' control without the rival: p1+p2+p3 admit z", GW + [admit_z(("p1", "p2", "p3"), ("a1c",))], C("az"))

# N7: the cited binding (check_conferral_two.chain_answers)
def ca(rows):
    out = C2.chain_answers(rows)
    return {k: (v["reason"], v.get("binding")) for k, v in sorted(out.items())}
G0 = {"id": "G0", "kind": "bundle", "signer": "count", "names": []}
B0 = {"id": "B0", "kind": "binding", "signer": "N", "names": [], "owner": "O1", "on": None}
B1 = {"id": "B1", "kind": "binding", "signer": "N", "names": ["B0"], "owner": "O2", "on": "B0"}
A = lambda cites, names, i="A", s="O1": {"id": i, "kind": "acceptance", "signer": s, "names": list(names), "on": cites[0] if cites else None, "cites": list(cites)}
X = lambda names, on="A", i="x1": {"id": i, "kind": "act", "signer": "N", "names": list(names), "head": "G0", "on": on}
print("A1 acceptance cites B0, B1 concurrent with it; act names A only:", ca([G0, B0, B1, A(["B0"], ["B0"]), X(["G0", "A"])]))
print("A2 the same, the act names A and B1 (the re-binding in the act's past):", ca([G0, B0, B1, A(["B0"], ["B0"]), X(["G0", "A", "B1"])]))
B0b = {"id": "B0b", "kind": "binding", "signer": "N", "names": [], "owner": "O1", "on": None}
print("A3 O1 cites its own OTHER binding B0b (also of N), B0 re-bound to O2 in A's past:",
      ca([G0, B0, B0b, B1, A(["B0b"], ["B0b", "B1"]), X(["G0", "A"])]))
BM = {"id": "BM", "kind": "binding", "signer": "M", "names": [], "owner": "O1", "on": None}
print("A4 O1 cites a binding of another node M with no `node` field:", ca([G0, BM, A(["BM"], ["BM"]), X(["G0", "A"])]))
B2 = {"id": "B2", "kind": "binding", "signer": "N", "names": ["B1"], "owner": "O1", "on": "B1"}
print("A5 back to O1: B0 -> B1 (O2) -> B2 (O1); O1's old acceptance citing B0, act after B2:",
      ca([G0, B0, A(["B0"], ["B0"]), B1, B2, X(["G0", "A", "B2"])]))
print("A6 the same with a new acceptance A2 citing B2:", ca([G0, B0, B1, B2, A(["B2"], ["B2"], "A2"), X(["G0", "A2"], "A2")]))

def full(rows):
    out = C2.chain_answers(rows)
    return {k: {kk: v.get(kk) for kk in ("reason", "binding", "owner", "counted", "in_force")} for k, v in sorted(out.items())}
print("A1 full:", full([G0, B0, B1, A(["B0"], ["B0"]), X(["G0", "A"])]))
print("A2 full:", full([G0, B0, B1, A(["B0"], ["B0"]), X(["G0", "A", "B1"])]))
print("A5 full:", full([G0, B0, A(["B0"], ["B0"]), B1, B2, X(["G0", "A", "B2"])]))
print("A0 control full (no re-binding):", full([G0, B0, A(["B0"], ["B0"]), X(["G0", "A"])]))
