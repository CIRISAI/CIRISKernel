exec(open(__file__.replace("ao.py","lib.py")).read())
H5 = ("h1","h2","h3","h4","h5")
b1 = nxt("b1","b0",H5,("h1","h2"))
b2 = nxt("b2","b1",("h3","h4","h5"),("h3","h4","h5"),version=2)      # h1, h2 removed
s0 = nxt("s0","b0",("h1","h2","X"),("h1","h2"))                       # removed h1,h2: an old-majority sibling at b0
L = [B0, b1, b2, s0]
run("AO0 s0 concludes; reader acked b2 then s0", L, rd=RD(anchor="b0", acks=("b2","s0")))
run("AO1 reader acked s0 then b2 (s0 delivered first)", L, rd=RD(anchor="b0", acks=("s0","b2")))
run("AO2 reader acked b1 then s0 then b2", L, rd=RD(anchor="b0", acks=("b1","s0","b2")))
run("AO3 a new reader acked s0 only", L, rd=RD(anchor="b0", acks=("s0",)))
g = GR("gx","s0","uX","room",("h1","h2"))
run("AO3g + h1,h2 grant on s0, reader acked s0 then b2", L, gs=(g,), rd=RD(anchor="b0", acks=("s0","b2")), gids=("gx",))
gh = GR("gh","b2","uY","room",("h3","h4"))
run("AO1h honest grant on b2 by h3,h4; reader acked s0 then b2", L, gs=(gh,), rd=RD(anchor="b0", acks=("s0","b2")), gids=("gh",))
