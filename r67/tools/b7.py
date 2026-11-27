import sys, itertools
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
for sc in ("club", "founder", "owner"):
    G = ST.offer("g", "A", ("A", "B", "C"), sc, "@", "self", cosigners=("B", "C"))
    a = grp("r", "offer", "X", "member", "accord_halt", signer="A", cosigners=("X",), counted=sc)
    x = grp("x", "unseat", "B", sc, "accord_halt", signer="A", counted=sc)
    run("K1 founding scope %s (kind %s): A alone admits X / removes B" % (sc, ST.kind_of({"g": G}, "g")), [G, a, x], [("X", "member"), ("B", sc)])
