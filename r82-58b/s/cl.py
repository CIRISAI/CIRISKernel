exec(open(__file__.replace("cl.py","lib.py")).read())
H5 = ("h1","h2","h3","h4","h5")
b1 = nxt("b1","b0",H5,("h1","h2")); b2 = nxt("b2","b1",("h3","h4","h5"),("h3","h4","h5"),version=2)
b3 = nxt("b3","b2",("h3","h4","h5","h6"),("h3","h4","h5"),version=3)
t1 = nxt("t1","b1",("h1","h2","h3","X"),("h1","h2","h3"),version=2); t = nxt("t","t1",("h1","h2","h3","X"),("h1","h2","h3"),version=3)
L = [B0, b1, b2, b3, t1, t]
sib = {"b2": b2, "t1": t1}
sT = CR.SETTLE("sT","t1",("h1","h2","h4"),sib, head="b1")      # toward the attacker's t1, by the removed h1,h2 and h4
run("CL0 sT concludes? reader at b3 (acked b2, b3), then acks sT", L + [sT], rd=RD(anchor="b0", acks=("b2","b3","sT")))
run("CL1 reader acked b2 only, then sT", L + [sT], rd=RD(anchor="b0", acks=("b2","sT")))
run("CL1b reader acked b2 only (sT exists, not acked)", L + [sT], rd=RD(anchor="b0", acks=("b2",)))
run("CL2 a new reader acks sT only", L + [sT], rd=RD(anchor="b0", acks=("sT",)))
# devices: device 1 at b3; device 2 concurrently acks sT
run("CL3 device 1 b2,b3; device 2 concurrently sT", L + [sT], rd=RD(anchor="b0", acks=("b2","b3","sT"), after=((),(0,),())))
run("CL3b device 2 sT first, device 1 b2,b3 concurrently", L + [sT], rd=RD(anchor="b0", acks=("sT","b2","b3"), after=((),(),(1,))))
run("CL4 device 1 b2,b3; device 2 concurrently acks t then sT", L + [sT], rd=RD(anchor="b0", acks=("b2","b3","t","sT"), after=((),(0,),(),(2,))))
# a settler at b0, a head the line voids entirely: s0 at b0 by h1,h2 (cuts h3); h3 the only one with a say; toward s0
s0 = nxt("s0","b0",("h1","h2","X"),("h1","h2"))
s0t = CR.SETTLE("s0t","s0",("h3",),{"b1": b1, "s0": s0})
run("CL5 + s0 and a settler at b0 toward s0 by h3; reader at b3", L + [s0, s0t], rd=RD(anchor="b0", acks=("b2","b3","s0t")))
run("CL5b same, reader acked b2 only", L + [s0, s0t], rd=RD(anchor="b0", acks=("b2","s0t")))
# chained: settler at b0 toward b1 (honest), and settler at b1 toward t1
s0b = CR.SETTLE("s0b","b1",("h3",),{"b1": b1, "s0": s0})
run("CL6 chained: b0 settled toward b1, b1 settled toward t1; reader acked s0,b2,s0b,sT", L + [s0, s0b, sT], rd=RD(anchor="b0", acks=("s0","b2","s0b","sT")))
