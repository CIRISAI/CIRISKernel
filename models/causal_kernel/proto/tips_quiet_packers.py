import sys, os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cases.py")).read().split('if __name__ == "__main__":')[0].replace('os.path.dirname(os.path.abspath(__file__))', repr(os.path.dirname(os.path.abspath(__file__)))))
out = []
for n in (8, 12):
    rows = quiet(n)[:-1]
    sg = ["A", "B"] + ["X%d" % i for i in range(1, n + 1)]
    r = ST.unseat("xc", "A", "C", "member", OBJ, "group", ("amq", "q%d" % n), head=("amq", "q%d" % n), policy="community_remove", cosigners=tuple(sg[1:]))
    S = CK.concluded(CK.kept(rows + [r]), CH.RULE)
    out.append("n=%d packers remove C: %s; for reader D: %s" % (n, bool(S.C.get("xc")), "void" if "xc" in ST.Seats(S, own="D").stale else "live"))
print(os.environ.get("CK_PROTO") or "now", "|", "; ".join(out))
