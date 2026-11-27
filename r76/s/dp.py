exec(open(__file__.replace("dp.py","lib.py")).read())
H5 = ("h1","h2","h3","h4","h5")
b1 = nxt("b1","b0",H5,("h1","h2"))
b2 = nxt("b2","b1",("h3","h4","h5"),("h3","h4","h5"),version=2)      # h1,h2 removed
t1 = nxt("t1","b1",("h1","h2","h3","X"),("h1","h2","h3"),version=2)  # h1,h2 (removed at b2) + h3 (also signed b2) at b1
t  = nxt("t","t1",("h1","h2","h3","X"),("h1","h2","h3"),version=3)
L = [B0, b1, b2, t1, t]
run("DP0 a reader that acked b2 only", L, rd=RD(anchor="b0", acks=("b2",)))
run("DP1 the reader acks b2, then t", L, rd=RD(anchor="b0", acks=("b2","t")))
run("DP2 a new reader that acks t", L, rd=RD(anchor="b0", acks=("t",)))
b3 = nxt("b3","b2",("h3","h4","h5","h6"),("h4","h5","h3"),version=3)
run("DP3 honest b3 on b2; the reader acks b2, b3, then t", L + [b3], rd=RD(anchor="b0", acks=("b2","b3","t")))
j = nxt("j",("t","b3"),("h3","h4","h5","h6"),("h3","h4","h5"),version=4)
run("DP4 honest join (t, b3) by h3,h4,h5", L + [b3, j], rd=RD(anchor="b0", acks=("b2","b3","t","j")))
g = GR("gx","t","uX","room",("h1","h2","h3"))
run("DP1g h1,h2,h3 grant on t; reader as DP1", L, gs=(g,), rd=RD(anchor="b0", acks=("b2","t")), gids=("gx",))
# without h3's double signature: h1,h2 alone at b1 are 2 of 5
t1b = nxt("t1","b1",("h1","h2","X"),("h1","h2"),version=2); tb = nxt("t","t1",("h1","h2","X"),("h1","h2"),version=3)
run("DP5 control: h1,h2 alone at b1", [B0, b1, b2, t1b, tb], rd=RD(anchor="b0", acks=("b2","t")))
