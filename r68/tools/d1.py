import sys, itertools
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
GI = AC.GI
print("GI:", {k: GI.get(k) for k in ("scope", "to", "consensus_protocol", "cohort_subkind")})
af = lambda i, k, signer, cos, heads=("g",): grp(i, "offer", k, "founder", None, heads=heads, signer=signer, cosigners=tuple(cos) + (k,), counted="founder")
rf = lambda i, k, signer, cos, heads: grp(i, "unseat", k, "founder", None, heads=heads, signer=signer, cosigners=tuple(cos), counted="founder")
rows = [GI, af("a4", "f4", "f1", ("f2",)), af("a5", "f5", "f1", ("f2",), heads=("a4",)),
        rf("x1", "f1", "f4", ("f5",), ("a5",)), rf("x2", "f2", "f4", ("f5",), ("x1",)), rf("x3", "f3", "f4", ("f5",), ("x2",))]
run("P1a f1,f2 admit f4,f5; then f4,f5 (2 of 5) remove f1, f2, f3", rows, [(k, "founder") for k in ("f1", "f2", "f3", "f4", "f5")], orders=False)
rc = grp("am", "offer", (), "record", None, heads=("a5",), signer="f4", cosigners=("f5",), counted="founder", consensus_protocol="quorum:1/1")
run("P1b f4,f5 (2 of 5) change the record (to quorum:1/1, refused as not N/2+1?)", rows[:3] + [rc], [])
rc2 = dict(rc, consensus_protocol="quorum:2/3")
run("P1c f4,f5 (2 of 5) restate quorum:2/3", rows[:3] + [rc2], [])
# one founder's own (uncounted) offer of founder to X, then f1 + X act as 2 founders
own = ST.offer("o", "f1", "X", "founder", OBJ, "self", ("g",), cosigners=("X",))
run("P1d f1's own offer seats X a founder; f1 + X remove f2 and f3", [GI, own, rf("x2", "f2", "f1", ("X",), ("o",)), rf("x3", "f3", "f1", ("X",), ("x2",))],
    [(k, "founder") for k in ("f1", "f2", "f3", "X")], orders=False)
# a founder that left: f3 withdraws; f1 alone?
lv = ST.withdraw("lv", "f3", "g", ("g",))
run("P1e f3 leaves; f1 + f2 still 2: admit f4", [GI, lv, af("a4", "f4", "f1", ("f2",), heads=("lv",))], [("f3", "founder"), ("f4", "founder")])
lv2 = ST.withdraw("lv2", "f2", "g", ("lv",))
run("P1f f2 and f3 leave; f1 alone (quorum 2) admits f4", [GI, lv, lv2, af("a4", "f4", "f1", (), heads=("lv2",))], [("f4", "founder")])
# node as voice
x = rf("xx", "f1", "f4", (), ("am",))
run("P1g after f4,f5's change to quorum:1/1, f4 alone removes f1", rows[:3] + [rc, x], [("f1", "founder")])
