import sys, os, random
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tree", "models", "causal_kernel")
sys.path.insert(0, T); sys.dont_write_bytecode = True
import check_trust_rows as C
TR, CH, ST, CK = C.TR, C.CH, C.ST, C.CK
A, M, L = TR.accepts, C.M, C.L
def arrive(o): return CK.arrive(list(o), lambda r, P, past: ST.seat_rule(r, P, past))
def run(name, rows, reader, lic, supplied=None, n=40, want=None, extra=None):
    S = arrive(rows); a = TR.read_licence(S, reader, lic, supplied=supplied)
    x = extra(S) if extra else None
    rnd = random.Random(5); d = 0
    for _ in range(n):
        t = list(rows); rnd.shuffle(t)
        S2 = arrive(t)
        if TR.read_licence(S2, reader, lic, supplied=supplied) != a or (extra and extra(S2) != x): d += 1
    flag = "" if want is None else ("  <-- BREAK (claim: %s)" % (want,) if a != want else "  (as claimed)")
    print("%-78s %s%s | orders %d/%d%s" % (name, a, " " + str(x) if extra else "", d, n, flag))
