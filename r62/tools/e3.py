import sys, itertools
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
F4 = lambda proto, **kw: ST.offer("g", "A", ("A", "B", "C", "D"), "member", "@", "self", cosigners=("B", "C", "D"), consensus_protocol=proto, **kw)
chg = grp("am", "offer", (), "record", None, signer="A", cosigners=("B", "C", "D"), consensus_protocol="weighted:r", need=5, weights=(("A", 3), ("A", 3), ("B", 1)))
x = grp("x", "unseat", "D", "member", None, heads=("am",), signer="A", cosigners=("B", "C"))
run("W1 all four change to a weighted record weighing A twice; then A,B,C remove D", [F4("majority"), chg, x], [("D", "member")])
ad = grp("r", "offer", "E", "member", "cosigned_act", signer="A", cosigners=("B", "C", "D", "E"), counted="duty")
run("B1 admission counted over duty", [F4("majority"), ad], [("E", "member")])
