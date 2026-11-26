"""Round 4: S'' and the reader-line exclusion inside the fold; the asked row's answer for readers none, D, C, and its
order-freeness (60 orders)."""
import sys, os, random
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cases.py")).read().split('if __name__ == "__main__":')[0].replace('os.path.dirname(os.path.abspath(__file__))', repr(os.path.dirname(os.path.abspath(__file__)))))
_sp3 = _u.spec_from_file_location("r3", os.path.join(os.path.dirname(os.path.abspath(__file__)), "round3.py"))
src3 = open(_sp3.origin).read().split("def ans(S, a):")[0]
ns = {"__file__": _sp3.origin}; sys_argv = sys.argv
exec(compile(src3, _sp3.origin, "exec"), ns)
W = [(n, r, a) for n, r, a, _ in C if n.startswith(("H7", "T2 step1", "room of one", "(a)", "(b)", "(c) packing n=8:", "(c) packing n=2:", "tightened", "L'", "quiet"))]
W += ns["W"]
def ans(rows, a, own):
    S = CK.concluded(CK.kept(list(rows)), CH.RULE)
    if own is None or not ("fold" in ST.PROTO and "rline" in ST.PROTO):
        ok = bool(S.C.get(a))
        if own is not None and ok: ok = a not in ST.Seats(S, own=own).stale
        return ok
    RV = ST.reader_void(S, own)
    r = next(q for q in rows if q["id"] == a)
    Sx = CK.State(list(rows), dict(S.C))          # the asked row read against the concluded rows of its past
    P = [q for q in S.Cs if q["id"] in Sx.anc.get(a, ())]
    past = lambda x, y: x in Sx.anc.get(y, ())
    ST._RVOID.append(frozenset(RV))
    try:
        return bool(ST.seat_rule(r, P, past)) and a not in RV
    finally:
        ST._RVOID.pop()
for name, rows, a in W:
    row = []
    for own in (None, "D", "C"):
        base = ans(rows, a, own)
        rnd = random.Random(7); diff = 0
        for _ in range(20):
            t = list(rows[1:]); rnd.shuffle(t)
            if ans([rows[0]] + t, a, own) != base: diff += 1
        row.append("%s%s" % ("T" if base else "F", "" if not diff else "!%d" % diff))
    print("%-74s none=%s D=%s C=%s" % (name[:74], *row))
