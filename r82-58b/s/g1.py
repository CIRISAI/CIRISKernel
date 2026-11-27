exec(open(__file__.replace("g1.py","lib.py")).read())
H5 = ("h1","h2","h3","h4","h5")
b1 = nxt("b1","b0",H5,("h1","h2"))                          # h1,h2 of 3 add h4,h5
b2 = nxt("b2","b1",("h3","h4","h5"),("h3","h4","h5"),version=2)   # h3,h4,h5 of 5 remove h1,h2
L = [B0, b1, b2]
rd = RD(anchor="b0", acks=("b2",))
run("G0 control: the reader acked b2; holders", L, rd=rd)
g = GR("g1","b0","uX","room",("h1","h2"))                   # removed h1,h2 grant naming the genesis bundle
run("G1 removed holders h1,h2 issue a grant naming b0", L, gs=(g,), rd=rd, gids=("g1",))
g2 = GR("g2","b2","uX","room",("h1","h2"))
run("G1 control: the same grant naming b2", L, gs=(g2,), rd=rd, gids=("g2",))
# the grant's signers' own statements on b1 are not read: they signed b1, and the grant names b0 only
# G2: a grant naming (b2, b0): b0 is in b2's past; charters differ
L2 = [B0, dict(b1, charter=C1), dict(b2, charter=C1)]
g3 = GR("g3",("b2","b0"),"uX","room",("h3","h4"))
run("G2 h3,h4 grant naming (b2,b0), charters differ: counted over the common", L2, gs=(g3,), rd=rd, gids=("g3",))
g4 = GR("g4","b2","uX","room",("h3","h4"))
run("G2 control: h3,h4 naming b2 alone (2 of 3 there)", L2, gs=(g4,), rd=rd, gids=("g4",))
g5 = GR("g5",("b1","b0"),"uX","room",("h1","h2"))
run("G3 removed h1,h2 grant naming (b1,b0) under the charter change: common = h1h2h3", L2, gs=(g5,), rd=rd, gids=("g5",))
