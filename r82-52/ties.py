import sys, itertools
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import audience as AU
ph = lambda s: s.startswith("{") and s.endswith("}")
def names_both(p, q):
    """candidate names matching both p and q: unify segment-wise, lengths up to max+2."""
    P, Q = p.split(":"), q.split(":")
    out = []
    for L in range(1, max(len(P), len(Q)) + 3):
        def seg(X, i):
            if X[-1] == "*" and i >= len(X) - 1: return "*"
            return X[i] if i < len(X) else None
        segs = []
        ok = True
        for i in range(L):
            a, b = seg(P, i), seg(Q, i)
            if a is None or b is None: ok = False; break
            lit = [x for x in (a, b) if x != "*" and not ph(x)]
            if len(set(lit)) > 1: ok = False; break
            segs.append(lit[0] if lit else "zz")
        if ok and AU._match(p, ":".join(segs)) is not None and AU._match(q, ":".join(segs)) is not None:
            out.append(":".join(segs))
    return out
fams = sorted(AU.FAMILIES); bad = 0
for p, q in itertools.combinations(fams, 2):
    for n in names_both(p, q):
        hits = [(AU._match(f, n), f) for f in fams if AU._match(f, n) is not None]
        best = max(k for k, _ in hits); top = [f for k, f in hits if k == best]
        if len(top) > 1:
            bad += 1; print("TIE", n, top, [AU.FAMILIES[f]["allowed"] or AU.FAMILIES[f]["undecided"] for f in top]); break
        # a different-cell resolution worth noting: name an instance of p resolves to q
print("ties:", bad)
