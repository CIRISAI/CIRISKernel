import sys, random; sys.path.insert(0, sys.argv[1])
import seat as ST, check_count_heads as CH
CK=ST.CK; admit, remove, ROOM = CH.admit, CH.remove, CH.ROOM
def chain(n):
    P, m, pv = [], ["A", "B"], "g"
    for i in range(1, n+1):
        k = "X%d" % i; P.append(admit("p%d" % i, k, tuple(m), (pv,))); m.append(k); pv = "p%d" % i
    return P, tuple(m), pv
P, sg, tip = chain(8)
WC = ST.withdraw("wc", "C", "g", ("aG",))
worlds = {
 "T-pack: A,B pack X1..X8 from g; the packers remove C at (aG,p8)": ROOM + P + [remove("xr", "C", sg, ("aG", tip))],
 "T-pack, C also signed p2 (no single-chain member: residual 1)": ROOM + [P[0], dict(P[1], cosigners=P[1]["cosigners"] + ("C",))] + P[2:] + [remove("xr", "D", sg + ("C",), ("aG", tip))],
 "T-left: C resigns at aG; the packers remove D at (aG,p8)": ROOM + [WC] + P + [remove("xr", "D", sg, ("aG", tip))],
 "T-left: C resigns at aG; the packers remove D at (wc,p8)": ROOM + [WC] + P + [remove("xr", "D", sg, ("aG", tip), ("wc",))],
 "T-left control: C resigns, no fork": ROOM + [WC],
}
for nm, W in worlds.items():
    for own in (None, "D"):
        S = CK.concluded(CK.kept(list(W)), CH.RULE); Q = ST.Seats(S, own=own)
        a = ({i: bool(S.C.get(i)) for i in ("p1", "xr", "wc") if i in S.by}, "".join(sorted(Q.holders("member", "g"))), sorted(Q.stale))
        rnd = random.Random(3); d = 0
        for _ in range(8):
            t = list(W[1:]); rnd.shuffle(t); S2 = CK.arrive([W[0]] + t, CH.RULE); Q2 = ST.Seats(S2, own=own)
            d += ({i: bool(S2.C.get(i)) for i in ("p1", "xr", "wc") if i in S2.by}, "".join(sorted(Q2.holders("member", "g"))), sorted(Q2.stale)) != a
        print(nm, "| reader", own, "|", a, "| orders differing", d, "/8")
