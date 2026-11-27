"""Attacks on key-person (seat.persons_of / person_for). python3 -I atk_kp.py <models/causal_kernel>"""
import sys, random
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import check_key_person as KP
ST, CK, WN, EL = KP.ST, KP.CK, KP.WN, KP.EL
RULE, RULE_W = KP.RULE, KP.RULE_W
SP, P1B, GC, BASE, add, evict, found, admit_z = KP.SP, KP.P1B, KP.GC, KP.BASE, KP.add, KP.evict, KP.found, KP.admit_z


def conc(name, rows, rid, rule=RULE):
    got = bool(CK.concluded(CK.kept(list(rows)), rule).C.get(rid))
    rnd, bad = random.Random(5), 0
    for _ in range(60):
        t = list(rows); rnd.shuffle(t)
        if bool(CK.arrive(t, rule).C.get(rid)) != got: bad += 1
    print("%-74s %s=%s differ=%d/60" % (name, rid, got, bad))


def adm(i, who, signers, heads, extra=()):
    return ST.offer(i, signers[0], who, "member", "gc", "group", tuple(heads) + tuple(extra), head=tuple(heads),
                    policy="community_invite", cosigners=tuple(signers[1:]) + (who,))

# K1: a person's device key is ALSO admitted to the room as a member: two voices for one person
AB = adm("ab", "p1b", ("p1", "p2", "p3"), ("gc",))
H = ST.cosign("h", "p1", "h", ("ab",))
def admit_y(signers):
    return ST.offer("ay", signers[0], "y", "member", "gc", "group", ("ab",), head=("ab",), policy="community_invite",
                    cosigners=tuple(signers[1:]) + ("y",))
conc("K1 p1b admitted as member (5 members); p1+p1b+p2+p3 admit y (4 of 5 keys, 3 persons)", BASE + [AB, admit_y(("p1", "p1b", "p2", "p3"))], "ay")
conc("K1' same with p4 instead of p1b (4 persons)", BASE + [AB, admit_y(("p1", "p4", "p2", "p3"))], "ay")
conc("K1'' p1+p2+p3 only (3 of 5)", BASE + [AB, admit_y(("p1", "p2", "p3"))], "ay")
# K2: hostile p2 adds p1's device p1b to its own roster S2 WITHOUT p1b's signature, to silence it
X1 = ST.offer("x1", "p2", "p1b", "self", "S2", "group", ("S2",), head=("S2",), policy="self_roster_add", counted="self")
conc("K2 p2 adds p1b to S2 unsigned; x1 concludes?", BASE + [X1], "x1")
conc("K2 then p1b+p2+p3 admit z (p1b silenced?)", BASE + [X1, admit_z(("p1b", "p2", "p3"), ("x1",))], "az")
X1c = dict(X1, consent="one")
conc("K2b same with consent=one; x1 concludes?", BASE + [X1c], "x1")
conc("K2b then p1b+p2+p3 admit z", BASE + [X1c, admit_z(("p1b", "p2", "p3"), ("x1",))], "az")
# K3: an addition to S1 not by S1's count (p2 adds k9 to S1): k9 speaks for p1?
X9 = add("x9", "S1", "k9", ("p2",), ("S1",))
conc("K3 p2 adds k9 to p1's roster; x9 concludes?", BASE + [X9], "x9")
conc("K3 then k9+p2+p3 admit z", BASE + [X9, admit_z(("k9", "p2", "p3"), ("x9",))], "az")
# K4: device added concurrently with its eviction, count names both
P1C = KP.P1C
A1D = add("a1d", "S1", "p1d", ("p1", "p1b"), ("a1b",))
E1D = evict("e1d", "S1", "p1d", ("p1", "p1c"), ("a1c",))
conc("K4 p1d added || evicted(p1d named in neither?)", BASE + [P1C, A1D, E1D], "e1d")
conc("K4 p1d+p2+p3 admit z naming both", BASE + [P1C, A1D, E1D, admit_z(("p1d", "p2", "p3"), ("a1d", "e1d"))], "az")
conc("K4' p1d+p2+p3 admit z naming addition only", BASE + [P1C, A1D, E1D, admit_z(("p1d", "p2", "p3"), ("a1d",))], "az")
# K5: a key claiming a person whose genesis key is no member (p5's roster)
S5 = found("S5", "p5"); A5 = add("a5", "S5", "p5b", ("p5",), ("S5",))
conc("K5 p5b (person p5, no member) + p2 + p3 admit z", BASE + [S5, A5, admit_z(("p5b", "p2", "p3"), ("a5",))], "az")
# K6: the genesis key revoked itself; its device still speaks for it?
REC = ST.offer("rec", "p1", "p1", "registered", "p1", "self")
RV = ST.unseat("rv", "p1", "p1", "registered", "p1", "self", ("rec", "a1b"))
conc("K6 p1 revoked itself; p1b+p2+p3 admit z", BASE + [REC, RV, admit_z(("p1b", "p2", "p3"), ("rv",))], "az")
conc("K6' p1 revoked itself; p1+p2+p3 admit z (p1 in base: revocation unread)", BASE + [REC, RV, admit_z(("p1", "p2", "p3"), ("rv",))], "az")
# K7: a self roster founded with a member's key listed but unsigned (hostile p2 founds S9 listing p1 as to)
S9 = ST.offer("S9", "p2", ("p2", "p1b"), "self", "@", "self")
conc("K7 p2 founds S9 listing p1b unsigned; p1b+p2+p3 admit z", BASE + [S9, admit_z(("p1b", "p2", "p3"), ("S9",))], "az")

# K8 window: the opener's device key answers `withdraw`
WB = KP.WBASE
def wout(rows):
    return WN.outcome(CK.concluded(CK.kept(list(rows)), RULE_W), "op", "recount")
o = lambda i, k, says: WN.answer(i, k, "op", says, ("op",))
print("K8 window base, p1b (opener p1's device) says withdraw:", wout(WB + [o("w1", "p1b", "withdraw")]))
print("K8' opener p1 says withdraw:", wout(WB + [o("w1", "p1", "withdraw")]))
print("K8'' nobody:", wout(WB))
print("K9 p2 and p2b object, p3 objects:", wout(WB + [o("o1", "p2", "object"), o("o2", "p2b", "object"), o("o3", "p3", "object")]))
print("K9' p2 objects, p2b approves, p3 objects:", wout(WB + [o("o1", "p2", "object"), o("o2", "p2b", "approve"), o("o3", "p3", "object")]))
