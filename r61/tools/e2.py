import sys, itertools, random
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
GI = AC.GI
af = lambda i, k, signer, cos, heads=("g",): grp(i, "offer", k, "founder", None, heads=heads, signer=signer, cosigners=tuple(cos) + (k,), counted="founder")
rf = lambda i, k, signer, cos, heads: grp(i, "unseat", k, "founder", None, heads=heads, signer=signer, cosigners=tuple(cos), counted="founder")
F = ("f1", "f2", "f3", "f4", "f5")
L = [GI, af("a4", "f4", "f1", ("f2",)), af("a5", "f5", "f1", ("f2", "f3"), heads=("a4",))]
run("H0 five founders", L, [(k, "founder") for k in F], orders=False)
run("H1 stale head: f1,f2 remove f3 naming head g (3 founders there)", L + [rf("x", "f3", "f1", ("f2",), ("g",))], [(k, "founder") for k in F], orders=False)
run("H1b same naming head a5 (5 founders)", L + [rf("x", "f3", "f1", ("f2",), ("a5",))], [(k, "founder") for k in F], orders=False)
# two heads: names g and a5 -> founders common to both
run("H2 heads (g, a5): common founders f1-f3; f1,f2 remove f3", L + [rf("x", "f3", "f1", ("f2",), ("g", "a5"))], [(k, "founder") for k in F], orders=False)
# concurrent founder admissions at g
C = [GI, af("a4", "f4", "f1", ("f2",)), af("a5", "f5", "f2", ("f3",))]
run("H3 concurrent admissions of f4 (f1,f2) and f5 (f2,f3) at g", C, [(k, "founder") for k in F])
run("H3b + f4,f5,f1 remove f2 naming both tips", C + [rf("x", "f2", "f4", ("f5", "f1"), ("a4", "a5"))], [(k, "founder") for k in F], orders=False)
# leave and re-admitted
lv = ST.withdraw("lv", "f3", "g", ("g",))
ra = af("ra", "f3", "f1", ("f2",), heads=("lv",))
run("H4 f3 leaves, is re-admitted by f1,f2 (2 of 2)", [GI, lv, ra], [("f3", "founder")])
rows = [GI, lv, ra, rf("x", "f1", "f2", ("f3",), ("ra",))]
run("H4b then f2,f3 remove f1 (2 of 3)", rows, [("f1", "founder")])
# a key in the founding to but unsigned, and a cosigner not in to
GJ = dict(GI, cosigners=("f2", "f3", "Z"), consensus_protocol="quorum:3/4")
run("H5 founding signed by Z (not in to), word quorum:3/4 (N=signers=4): f1,f2 admit f4", [GJ, af("a4", "f4", "f1", ("f2",))], [("f4", "founder"), ("Z", "founder")])
GK = dict(GI, cosigners=("f2", "f3", "Z"))   # word quorum:2/3 but 4 signers
run("H5b same with word quorum:2/3: f1,f2,f3 admit f4", [GK, af("a4", "f4", "f1", ("f2", "f3"))], [("f4", "founder")])
