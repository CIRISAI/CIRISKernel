import sys, os, random
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import seat as ST, check_count_heads as CH
CK = ST.CK; RULE = CH.RULE; OBJ = "g"
admit, remove, ack, ROOM = CH.admit, CH.remove, CH.ack, CH.ROOM
def run(name, rs, own=None, ids=(), scopes=("member",), n=60, obj=OBJ):
    def ans(S):
        Q = ST.Seats(S, own=own)
        return ({i: bool(S.C.get(i)) for i in ids}, {sc: "".join(sorted(Q.holders(sc, obj))) for sc in scopes}, tuple(sorted(Q.stale)))
    S = CK.concluded(CK.kept(list(rs)), RULE); a = ans(S)
    rnd = random.Random(7); d = 0
    for _ in range(n):
        t = list(rs[1:]); rnd.shuffle(t)
        if ans(CK.arrive([rs[0]] + t, RULE)) != a: d += 1
    print(name); print("   ", a, "| orders differing %d/%d" % (d, n))
