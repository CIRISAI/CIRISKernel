exec(open(__file__.replace("rj.py","lib.py")).read())
H5 = ("h1","h2","h3","h4","h5")
b1 = nxt("b1","b0",H5,("h1","h2"))
b2 = nxt("b2","b1",("h3","h4","h5"),("h3","h4","h5"),version=2)      # h1, h2 removed
L = [B0, b1, b2]
# removed h1's own genesis recovery commitment r:h1, used at b0
ra = nxt("ra","b0",("h1x","h2","h3"),("r:h1",),recovers=("h1","h1x"),recovery={"h1x":"r:h1x","h2":"r:h2","h3":"r:h3"})
run("RJ0 the removed holder's recovery at b0 concludes?", L + [ra], rd=RD(anchor="b0", acks=("b2",)))
jx = nxt("jx",("b2","ra"),("h3",),("h3",),version=3, recovery={"h3":"r:h3"})
run("RJ1 h3 alone joins b2 and ra, seating only itself (common holders: h3)", L + [ra, jx], rd=RD(anchor="b0", acks=("jx",)))
g = GR("gx","jx","uX","room",("h3",))
run("RJ1g + h3 alone grants on jx", L + [ra, jx], gs=(g,), rd=RD(anchor="b0", acks=("jx",)), gids=("gx",))
run("RJ1r read by a reader that acked b2", L + [ra, jx], gs=(g,), rd=RD(anchor="b0", acks=("b2",)), gids=("gx",))
