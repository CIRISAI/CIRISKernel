"""r116-53: root-join-signers 8f1941c. python3 -I atk_r116.py <models/trust_root>"""
import sys, random
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import check_root as C
RT, B, GR, RD, nxt = C.RT, C.B, C.GR, C.RD, C.nxt
B0, H3, REC = C.B0, C.H3, C.REC


def go(name, bs, rd, want, gs=()):
    got = C.answer(bs, (), gs, rd, want)
    R = RT.Root(bs, (), gs)
    why = {i: R.refusal(i) for i in want.get("concluded", {})}
    rnd, bad = random.Random(5), 0
    for _ in range(30):
        t = list(bs); rnd.shuffle(t)
        bad += C.answer(t, (), gs, rd, want) != got
    print("%-92s %s %s differ=%d/30" % (name, got, why, bad))


w = lambda *ks, **x: dict({"concluded": {k: None for k in ks}, "heads": None, "holders": None}, **x)
EVIL = {"h1": "r:h1", "h2": "r:evil", "h3": "r:h3"}
# K1: h1 and h3 re-commit h2's recovery key without h2: refused (limb b)
K1 = nxt("b1", "b0", H3, ("h1", "h3"), recovery=EVIL)
go("K1 h1,h3 re-commit h2's recovery to r:evil without h2", [B0, K1], RD(anchor="b0", acks=("b1",)), w("b1"))
# K2: a junk bundle (concludes nothing) declaring rotates=(h2, h1) merges h2 and h1 into one owner
JK = nxt("jk", "b0", H3, ("x9",), rotates=("h2", "h1"))
go("K2 + a junk bundle by x9 declaring rotates (h2 -> h1): does K1 now conclude?", [B0, JK, K1], RD(anchor="b0", acks=("b1",)), w("jk", "b1"))
RV = nxt("rv", "b1", ("h1", "h2e", "h3"), ("r:evil",), version=2, recovers=("h2", "h2e"), recovery={"h1": "r:h1", "h2e": "r:h2e", "h3": "r:h3"})
go("K2' then the attacker's recovery of h2's seat under r:evil", [B0, JK, K1, RV], RD(anchor="b0", acks=("b1", "rv")), w("jk", "b1", "rv"))
go("K2'' control without the junk bundle", [B0, K1, RV], RD(anchor="b0", acks=("b1", "rv")), w("b1", "rv"))
# K3: junk rotates=(h3, x9): x9 then speaks for h3 in a grant?
JK3 = nxt("jk3", "b0", H3, ("x9",), rotates=("h3", "x9"))
g = (GR("g1", "b0", "uX", "room", ("h1", "x9")),)
go("K3 junk rotates (h3 -> x9); grant by h1 and x9 on b0", [B0, JK3], RD(anchor="b0"), {"heads": None, "grant": {"g1": None}}, g)
go("K3' control: the grant by h1 and x9 without the junk", [B0], RD(anchor="b0"), {"heads": None, "grant": {"g1": None}}, g)
# S: a spent commitment reused after a join. rc spends h3's r:h3 at b0 (h3 -> h3b); s1 keeps h3 with r:h3;
# a join of (rc, s1) re-carries r:h3 for h3b
S1 = nxt("s1", "b0", H3, ("h1", "h2"), recovery={"h1": "r:h1", "h2": "r:h2", "h3": "r:h3"})
J = nxt("j", ("rc", "s1"), ("h1", "h2", "h3b"), ("h1", "h2", "h3b"), version=2, recovery={"h1": "r:h1", "h2": "r:h2", "h3b": "r:h3"})
go("S1 join (rc, s1) carries the spent r:h3 for h3b", [B0, REC, S1, J], RD(anchor="b0", acks=("j",)), w("j"))
J2 = nxt("j", ("rc", "s1"), ("h1", "h2", "h3b"), ("h1", "h2", "h3b"), version=2, recovery={"h1": "r:h1", "h2": "r:h2", "h3b": "r:h3b"})
B3 = nxt("b3", "j", ("h1", "h2", "h3b"), ("h1", "h2", "h3b"), version=3, recovery={"h1": "r:h1", "h2": "r:h3", "h3b": "r:h3b"})
go("S2 after a clean join, a later bundle commits h2 to the spent r:h3", [B0, REC, S1, J2, B3], RD(anchor="b0", acks=("b3",)), w("j", "b3"))
# a second recovery of h3's seat under the spent commitment, on the s1 branch
RC2 = nxt("rc2", "s1", ("h1", "h2", "h3z"), ("r:h3",), version=2, recovers=("h3", "h3z"), recovery={"h1": "r:h1", "h2": "r:h2", "h3z": "r:h3z"})
go("S3 a second recovery of h3 under r:h3 on the other branch (s1)", [B0, REC, S1, RC2], RD(anchor="b0", acks=("rc2",)), w("rc2"))
# L: a left key re-seated through a third branch. b1 rotates h2 -> h2x; branches t1 (from b0, keeps h2) and t2 (from b0)
ROT = nxt("r1", "b0", ("h1", "h2x", "h3"), ("h1", "h2", "h3", "h2x"), rotates=("h2", "h2x"),
          recovery={"h1": "r:h1", "h2x": "r:h2x", "h3": "r:h3"})
T1 = nxt("t1", "b0", H3 + ("h4",), ("h1", "h2", "h3", "h4"))
T2 = nxt("t2", "b0", H3 + ("h5",), ("h1", "h2", "h3", "h5"))
JT = nxt("jt", ("t1", "t2"), H3 + ("h4", "h5"), ("h1", "h2", "h3"), version=2)
go("L1 join of t1,t2 (neither has r1 in its lines) seats h2: legal", [B0, ROT, T1, T2, JT], RD(anchor="b0", acks=("jt",)), w("r1", "t1", "t2", "jt"))
J3 = nxt("j3", ("jt", "r1"), ("h1", "h2", "h3", "h4", "h5"), ("h1", "h3", "h4", "h5", "h2x"), version=3)
go("L2 a join of r1 and jt re-seating the left h2", [B0, ROT, T1, T2, JT, J3], RD(anchor="b0", acks=("j3",)), w("jt", "j3"))
J4 = nxt("j4", ("jt", "r1"), ("h1", "h2x", "h3", "h4", "h5"), ("h1", "h3", "h4", "h5", "h2x"), version=3)
go("L3 the same join seating h2x (control)", [B0, ROT, T1, T2, JT, J4], RD(anchor="b0", acks=("j4",)), w("j4"))
B5 = nxt("b5", "jt", H3 + ("h4", "h5"), ("h1", "h2", "h3", "h4"), version=3)
go("L4 h2 still voices on the jt branch after r1 left it elsewhere", [B0, ROT, T1, T2, JT, B5], RD(anchor="b0", acks=("b5",)), w("b5"))
# K4: the same owner merge through a junk RECOVERY row (recovers=(h2, h1)), which also concludes nothing
JR = nxt("jr", "b0", H3, ("x9",), recovers=("h2", "h1"), recovery={"h1": "r:h1", "h2": "r:h2", "h3": "r:h3"})
go("K4 a junk recovery row by x9, recovers (h2 -> h1); then K1", [B0, JR, K1], RD(anchor="b0", acks=("b1",)), w("jr", "b1"))
