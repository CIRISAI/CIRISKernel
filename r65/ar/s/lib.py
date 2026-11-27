import sys, os, random, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tree", "models", "causal_kernel"))
sys.dont_write_bytecode = True
import seat as ST, check_count_heads as CH
CK = ST.CK; RULE = CH.RULE; OBJ = "g"
admit, remove, ack, ROOM, FIVE = CH.admit, CH.remove, CH.ack, CH.ROOM, CH.FIVE
VARS = (None, "asym", "sym", "sym2")
def setv(v):
    ST.RULE_R = {"sym2": "sym", "sym3": "sym"}.get(v, v); ST.SYM_BASE = {"sym2": "fold", "sym3": "all"}.get(v, "past")
    ST.CUT.SYM = v in ("sym", "sym2", "sym3", "join"); ST._SEATS_OF.clear()
def ans(S, own, ids, scopes, obj):
    Q = ST.Seats(S, own=own)
    return ("".join(i for i in ids if S.C.get(i)) or "-", " ".join("%s=%s" % (sc, "".join(sorted(Q.holders(sc, obj)))) for sc in scopes),
            getattr(Q, "sym_cycle", None) and "CYCLE")
def run(name, rs, own=None, ids=(), scopes=("member",), n=60, obj=OBJ, vars=VARS):
    print(name)
    for v in vars:
        setv(v)
        t0 = time.time()
        S = CK.concluded(CK.kept(list(rs)), RULE); a = ans(S, own, ids, scopes, obj)
        rnd = random.Random(7); d = 0
        for _ in range(n):
            t = list(rs[1:]); rnd.shuffle(t)
            if ans(CK.arrive([rs[0]] + t, RULE), own, ids, scopes, obj) != a: d += 1
        print("   %-5s concluded:%-12s %s%s | orders differing %d/%d  (%.1fs)" % (v or "today", a[0], a[1], " "+a[2] if a[2] else "", d, n, time.time()-t0))
