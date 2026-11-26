"""S' order-freeness: each case's answer over 60 arrival orders, and the void set of the asked row in each order;
plus V3-style chain worlds (2,5), (5,2), (3,3), packing against a short honest line, L'."""
import sys, os, random
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cases.py")).read().split('if __name__ == "__main__":')[0].replace('os.path.dirname(os.path.abspath(__file__))', repr(os.path.dirname(os.path.abspath(__file__)))))
import checkpoint as CP
def chain(h, f):
    rows, mem, prev = [CH.G], ["A", "B", "C"], "g"
    for i in range(h):
        k = "H%d" % i; rows.append(admit("h%d" % i, k, tuple(mem), (prev,))); mem.append(k); prev = "h%d" % i
    sg, fp = ["A", "B"], "g"
    for i in range(f):
        k = "F%d" % i; rows.append(admit("f%d" % i, k, tuple(sg), (fp,))); sg.append(k); fp = "f%d" % i
    return rows + [remove("xr", "C", tuple(mem[3:]) + ("C",), (prev, fp))], "xr"
W = [(n, r, a) for n, r, a, _ in C if n.startswith(("H7", "(b)", "(c) packing n=8:", "L'", "tightened", "quiet"))]
for h, f in ((2, 5), (5, 2), (3, 3), (2, 8)):
    rows, a = chain(h, f); W.append(("chains honest %d fork %d" % (h, f), rows, a))
def ans(S, a):
    P = [q for q in S.Cs if q["id"] in S.anc.get(a, ())]
    r = S.by[a]
    return bool(S.C.get(a)), tuple(sorted(ST.signers_void(r, P))) if P else ()
for name, rows, a in W:
    base = ans(CK.concluded(CK.kept(list(rows)), CH.RULE), a)
    rnd = random.Random(7); diff = 0
    for _ in range(60):
        t = list(rows[1:]); rnd.shuffle(t)
        if ans(CK.arrive([rows[0]] + t, CH.RULE), a) != base: diff += 1
    print("%-80s concludes %s, void %s | orders differing %d/60" % (name[:80], base[0], list(base[1]), diff))
