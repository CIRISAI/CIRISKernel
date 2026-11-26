import sys, os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cases.py")).read().split('if __name__ == "__main__":')[0].replace('os.path.dirname(os.path.abspath(__file__))', repr(os.path.dirname(os.path.abspath(__file__)))))
src3 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "round3.py")).read().split("def ans(S, a):")[0]
ns = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "round3.py")}; exec(src3, ns)
for name, rows, a in ns["W"]:
    if not name.startswith("silent"): continue
    S = CK.concluded(CK.kept(list(rows)), CH.RULE)
    out = []
    for own in (None, "D", "C"):
        Q = ST.Seats(S, own=own)
        m = "".join(sorted(Q.holders("member", OBJ)))
        out.append("%s: %s" % (own, m))
    print(name[:60], " | ".join(out))
