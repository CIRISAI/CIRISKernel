exec(open(__file__.replace("gl.py","lib.py")).read())
b1 = nxt("b1","b0",("h1","h2","h3","h4"),("h1","h2","h3"))           # honest: all three add h4
L = [B0, b1]
g0 = GR("g0","b0","uX","room",("h1","h2","h3"))                     # an honest grant made at b0, before b1
run("GL1 honest grant g0 on b0; reader acked b0 then b1; reader rows name nothing", L, gs=(g0,), rd=RD(anchor="b0", acks=("b0","b1")), gids=("g0",))
a1 = AK("a1","b1",names=("g0",))
run("GL2 the same, the reader's acceptance edge of b1 names g0", L, gs=(g0, a1), rd=RD(anchor="b0", acks=("b0","b1"), rows=("a1",)), gids=("g0",))
a2 = AK("a2","b1")
run("GL3 the reader's acceptance edge of b1 written before g0 arrived (names nothing)", L, gs=(g0, a2), rd=RD(anchor="b0", acks=("b0","b1"), rows=("a2",)), gids=("g0",))
run("GL4 a reader that acknowledged b1 only (no earlier ack of b0)", L, gs=(g0,), rd=RD(anchor="b0", acks=("b1",)), gids=("g0",))
