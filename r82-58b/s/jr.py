exec(open(__file__.replace("jr.py","lib.py")).read())
b1 = nxt("b1","b0",("h1","h2","h3","h4"),("h1","h2","h3"))           # all three add h4
s0 = nxt("s0","b0",("h1","h2","X"),("h1","h2"))                       # h1,h2 cut h3
b2 = nxt("b2","b1",("h1","h2","h3","h4","h5"),("h1","h3","h4"),version=2)
L = [B0, b1, s0, b2]
sib = {"b1": b1, "s0": s0}
st = CR.SETTLE("st","b1",("h3",),sib)
run("JR0 h1,h2 double-signed (b1, s0); h3 settles toward b1", L + [st], rd=RD(anchor="b0", acks=("s0","b1","st")))
# r:h3 (h3's recovery commitment at b0, stolen or reused) writes a recovery at b0: h3 -> h3x
rc = nxt("rc","b0",("h1","h2","h3x"),("r:h3",),recovers=("h3","h3x"),recovery={"h1":"r:h1","h2":"r:h2","h3x":"r:h3x"})
run("JR1 + a recovery of h3's seat at b0 (by r:h3): is h3 now a double signer, its settle refused?", L + [rc, st], rd=RD(anchor="b0", acks=("s0","b1","st")))
run("JR1b the reader that acked b2 first", L + [rc, st], rd=RD(anchor="b0", acks=("b2",)))
