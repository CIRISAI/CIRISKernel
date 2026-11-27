exec(open(__file__.replace("ca.py","lib.py")).read())
STL = CR.STL
# acks: 0 = s0 (device 1); 1 = b2 (device 2, nothing before); 2 = b3 (device 2, after 1)
run("CA1 device 1 acks s0; device 2 acks b2 then b3 (concurrent with device 1)", STL, rd=RD(anchor="b0", acks=("s0","b2","b3"), after=((),(),(1,))))
run("CA2 + device 2 later acks b3 again with device 1's row in its past", STL, rd=RD(anchor="b0", acks=("s0","b2","b3","b3"), after=((),(),(1,),(0,1,2))))
run("CA3 the reverse: device 1 acks b2, b3; device 2 then acks s0 (concurrent)", STL, rd=RD(anchor="b0", acks=("b2","b3","s0"), after=((),(0,),())))
g = GR("gx","s0","uX","room",("h1","h2"))
run("CA1g h1,h2 grant on s0, reader CA1", STL, gs=(g,), rd=RD(anchor="b0", acks=("s0","b2","b3"), after=((),(),(1,))), gids=("gx",))
