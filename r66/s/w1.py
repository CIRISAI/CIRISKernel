import sys, os, random
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import seat as ST, check_count_heads as CH, window as W
CK = ST.CK
RULE = lambda r, P, past: W.rule(r, P, past)
def go(name, rows, n=60):
    def ans(S): return W.outcome(S, "p", "recount")
    S = CK.concluded(CK.kept(list(rows)), RULE); a = ans(S)
    rnd = random.Random(7); d = 0
    for _ in range(n):
        t = list(rows[1:]); rnd.shuffle(t)
        if ans(CK.arrive([rows[0]] + t, RULE)) != a: d += 1
    print(name, "->", a, "| orders differing %d/%d" % (d, n))
for hd, nm in ((("aG",), "head aG"), (("g",), "head g naming aG")):
    p = W.opener("p", "A", "ballot@once", "g", hd, names=("aG",))
    ans = [W.answer("v"+k, k, "p", "for") for k in "AB"] + [W.answer("v"+k, k, "p", "against") for k in "DEFG"]
    go("W1 ballot@once opened by A, %s; A,B for, D..G against" % nm, CH.ROOM + [p] + ans)
