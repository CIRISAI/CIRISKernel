import sys, os, random, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tree", "models", "causal_kernel"))
sys.dont_write_bytecode = True
import seat as ST, check_count_heads as CH
CK = ST.CK; RULE = CH.RULE; OBJ = "g"
admit, remove, ack, ROOM, FIVE = CH.admit, CH.remove, CH.ack, CH.ROOM, CH.FIVE
ST.RULE_R = None; ST.CUT.SYM = False
VARS = ("today", "L'", "L")
def setv(v):
    ST.ONE_SAY = v in ("L'", "L'+c", "L's", "L'o"); ST.ACK_CONTENT = v == "L'+c"; ST.L_RULE = v == "L"
    ST.OS_CONTESTED = "stand" if v == "L's" else "void"; ST.ACK_NEEDS_CLOSED = v != "L'o"
    ST._SEATS_OF.clear(); ST.OS_STATS.clear()
def ans(S, own, ids, scopes, obj):
    Q = ST.Seats(S, own=own)
    st = "".join(sorted(i for i in ids if i in Q.stale or i in Q.onesay))
    return ("".join(i for i in ids if S.C.get(i)) or "-", " ".join("%s=%s" % (sc, "".join(sorted(Q.holders(sc, obj)))) for sc in scopes), st)
def run(name, rs, own=None, ids=(), scopes=("member",), n=60, obj=OBJ, vars=VARS):
    print(name)
    for v in vars:
        setv(v); t0 = time.time()
        S = CK.concluded(CK.kept(list(rs)), RULE); a = ans(S, own, ids, scopes, obj)
        cont = sorted(ST.OS_STATS.get("contested", ()))
        rnd = random.Random(7); d = 0
        for _ in range(n):
            t = list(rs[1:]); rnd.shuffle(t)
            if ans(CK.arrive([rs[0]] + t, RULE), own, ids, scopes, obj) != a: d += 1
        print("   %-5s concl:%-10s %s | void:%s%s | orders %d/%d (%.1fs)" % (v, a[0], a[1], a[2] or "-", (" contested:" + ",".join(cont)) if cont else "", d, n, time.time()-t0))
