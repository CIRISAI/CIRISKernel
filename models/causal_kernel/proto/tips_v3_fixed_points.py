"""V3's fixed points: V = built-on closure of {q : some p of the past, not in V, that q is stale against}. All of them,
by enumeration, for an honest chain of h rows and a fork chain of f rows from the founding head."""
import sys, os, itertools
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import seat as ST, check_count_heads as CH, checkpoint as CP
CK = ST.CK
G = CH.G
def world(h, f):
    rows, mem, prev = [G], ["A", "B", "C"], "g"
    for i in range(h):
        k = "H%d" % i; rows.append(CH.admit("h%d" % i, k, tuple(mem), (prev,))); mem.append(k); prev = "h%d" % i
    sg, fp = ["A", "B"], "g"
    for i in range(f):
        k = "F%d" % i; rows.append(CH.admit("f%d" % i, k, tuple(sg), (fp,))); sg.append(k); fp = "f%d" % i
    return rows
for h, f in ((2, 5), (5, 2), (3, 3), (2, 8), (1, 1), (2, 2)):
    rows = world(h, f)
    S = CK.State(rows, {q["id"]: True for q in rows})
    acts = CP.counted_acts(S, "g")
    pairs = ST._v3_conflicts(S, acts)
    ids = [a["id"] for a in acts]
    fps = []
    for bits in itertools.product((0, 1), repeat=len(ids)):
        V = {i for i, b in zip(ids, bits) if b}
        want = ST._built_closure(acts, {q for q, p in pairs if p not in V})
        if want == V: fps.append(sorted(V))
    naive = sorted(ST._built_closure(acts, {q for q, _ in pairs}))
    print("honest %d, fork %d: %d fixed points: %s | every pair voids: %s" % (h, f, len(fps), fps, naive))
