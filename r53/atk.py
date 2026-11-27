import sys, random
sys.path.insert(0, sys.argv[1])
sys.dont_write_bytecode = True
import check_room_keys as C
ST, CK, WN = C.ST, C.CK, C.WN
OBJ = "g"
M = ("m1", "m2", "m3", "m4")

def run(name, rows, asks, concl=()):
    S = CK.concluded(CK.kept(list(rows)), C.RULE)
    def rd(S):
        Q = ST.Seats(S)
        return ({i: bool(S.C.get(i)) for i in concl}, sorted(Q.roster(OBJ)),
                [(k, sc, Q.stands(k, sc, OBJ)) for k, sc in asks])
    got = rd(S)
    rnd = random.Random(7); bad = 0
    for _ in range(60):
        t = list(rows[1:]); rnd.shuffle(t)
        if rd(CK.arrive([rows[0]] + t, C.RULE)) != got: bad += 1
    print("%-62s %s  orders-differ=%d/60" % (name, got, bad))

PV = C.PV
XQ = C.XQ
# A1: removed member q re-seated as `agent`, by one founder alone (Conf self) and by the count
own_ag = ST.offer("oa", "m1", "q", "agent", OBJ, "self", ("xq",), cosigners=("q",))
run("A1a removed q, m1 alone offers q `agent` (self)", PV + [XQ, own_ag], [("q", "agent"), ("q", "member")], ("xq", "oa"))
run("A1b removed q, count admits q as `agent`", PV + [XQ, C.rejoin("ra", "q", ("xq",), "agent")], [("q", "agent")], ("ra",))
own_m = ST.offer("om", "m1", "z", "member", OBJ, "self", ("ag",), cosigners=("z",))
run("A1c (no removal) m1 alone admits fresh z as member (self)", PV + [own_m], [("z", "member")], ("om",))
run("A1d resigned q, m1 alone offers q `agent`", PV + [C.WQ, ST.offer("oa", "m1", "q", "agent", OBJ, "self", ("wq",), cosigners=("q",))],
    [("q", "agent")], ("oa",))
# A2: `founder` scope (HOLDS founder -> member) in a private room with no duty holders
g2 = ST.found("g", "m1", M, cosigners=M[1:], membership="private")
aq = C.admit("aq", "q", ("m1", "m2", "m3"), ("g",))
xq = C.remove("xq", "q", M, ("aq",))
fo = ST.offer("of", "m1", "q", "founder", OBJ, "self", ("xq",), cosigners=("q",))
run("A2 no-duty private room: removed q, m1 alone offers `founder`", [g2, aq, xq, fo], [("q", "member"), ("q", "founder")], ("xq", "of"))
# A3: founding row of scope `duty`; a founder with a second (member) seat row
g3 = ST.found("g", "m1", M, cosigners=M[1:], scope="duty", membership="private")
a3 = C.admit("a3", "m3", ("m1", "m2", "m4"), ("g",))
run("A3a duty-scope founding; m3 also admitted as member", [g3, a3], [("m3", "member")], ("a3",))
run("A3b m3 withdraws the founding row (end_scope=duty)", [g3, a3, ST.withdraw("w3", "m3", "g", ("a3",))], [("m3", "member"), ("m3", "duty")], ("w3",))
run("A3c m3 withdraws its member row (end_scope=member)", [g3, a3, ST.withdraw("w3", "m3", "a3", ("a3",))], [("m3", "member"), ("m3", "duty")], ("w3",))
run("A3d ...then a fresh count admission of m3", [g3, a3, ST.withdraw("w3", "m3", "a3", ("a3",)), C.admit("a4", "m3", ("m1", "m2", "m4"), ("w3",))],
    [("m3", "member")], ("a4",))
# A4: consent-one re-admission concurrent with q's resignation
c1 = ST.offer("c1", "m1", "q", "member", OBJ, "group", ("ag",), head=("ag",), policy="community_invite", cosigners=("m2", "m3", "m4"), consent="one")
run("A4 consent-one admission concurrent with q's resignation", PV + [C.WQ, c1], [("q", "member")], ("wq", "c1"))
# A5: q's standing acceptance written before its resignation; a re-admission concurrent with the resignation names it
sa = ST.accept("sa", "q", None, ("ag",), scope="member", obj=OBJ)
wq = ST.withdraw("wq", "q", "aq", ("sa",))
ra = ST.offer("ra", "m1", "q", "member", OBJ, "group", ("sa",), head=("sa",), policy="community_invite", cosigners=("m2", "m3", "m4"))
run("A5 private: standing accept before resign, readmission || resign", PV + [sa, wq, ra], [("q", "member")], ("sa", "wq", "ra"))
run("A5' public: same", C.PB + [sa, wq, ra], [("q", "member")], ("sa", "wq", "ra"))
run("A5'' private: readmission AFTER resign (names wq)", PV + [sa, wq, ST.offer("ra", "m1", "q", "member", OBJ, "group", ("wq",), head=("wq",),
    policy="community_invite", cosigners=("m2", "m3", "m4"))], [("q", "member")], ("ra",))
# A6: decline is final: z offered (no cosign), z withdraws the pending offer, a later admission
oz = C.admit("oz", "z", M, ("ag",), joiner=False)
wz = ST.withdraw("wz", "z", "oz", ("oz",))
run("A6 private: z declines (withdraws unaccepted offer); readmit", PV + [oz, wz, C.admit("oz2", "z", M, ("wz",))], [("z", "member")], ("wz", "oz2"))
# A7: single-founder private room: founder's lone Conf-self unseat is final
g7 = ST.found("g", "f", ("f",), membership="private")
a7 = ST.offer("a7", "f", "q", "member", OBJ, "self", ("g",), cosigners=("q",))
x7 = ST.unseat("x7", "f", "q", "member", OBJ, "self", ("a7",))
run("A7 single founder: f admits q, f alone unseats, f re-admits", [g7, a7, x7, ST.offer("a8", "f", "q", "member", OBJ, "self", ("x7",), cosigners=("q",))],
    [("q", "member")], ("a7", "x7", "a8"))
# A8: unsigned listed founding member withdraws the founding row: barred forever
g8 = ST.found("g", "m1", M + ("u",), cosigners=M[1:], membership="private")
run("A8 unsigned listed u withdraws founding row; count admits u", [g8, ST.withdraw("wu", "u", "g", ("g",)), C.admit("au", "u", M, ("wu",))],
    [("u", "member")], ("wu", "au"))
# A9: withdrawal by another key of q's acceptance / of q's offer (cosigner)
acc = [PV[0], C.admit("aq", "q", ("m1", "m2", "m3"), ("g",), joiner=False), ST.accept("acq", "q", "aq")]
run("A9a m2 withdraws q's acceptance", acc + [ST.withdraw("w9", "m2", "acq", ("acq",))], [("q", "member")], ("w9",))
run("A9b m2 (cosigner) withdraws q's admission offer", acc + [ST.withdraw("w9", "m2", "aq", ("acq",))], [("q", "member")], ("w9",))
run("A9c ...then count re-admits q", acc + [ST.withdraw("w9", "m2", "aq", ("acq",)), C.admit("aq2", "q", M, ("w9",))], [("q", "member")], ("aq2",))
# A10: agent resigns its agent seat; member admission of the same key (resign branch scope-blind)
run("A10 AG resigns agent seat; count admits AG as member", PV + [ST.withdraw("wg", "AG", "ag", ("ag",)), C.rejoin("am", "AG", ("wg",))],
    [("AG", "member")], ("am",))
run("A10' count removes AG agent; count admits AG as member", PV + [C.XA, C.rejoin("am", "AG", ("xa",))], [("AG", "member")], ("am",))
