exec(open(__file__.replace("f3.py","lib.py")).read())
glic = C.glic; G1 = C.G1
OK=(True,None); LW=(False,"licensure_link_withdrawn")
duty = lambda S: sorted(ST.Seats(S).holders("duty","g"))
DCD = ST.offer("dcd","A",("B","C"),"moderate","g","self",("g",)); DAB = ST.accept("dab","B","dcd"); DAC = ST.accept("dac","C","dcd")
GBC = ST.offer("glo","B",("X",),"license","g","group",("dab","dac"),head=("dcd",),cosigners=("C",),counted="duty"); GLA = ST.accept("gla","X","glo")
LX = glic("l","g","X")|{"names":("gla",)}
base = [G1,DCD,DAB,DAC]
run("D1c control: B,C (2 of 3) confer license on X", base+[GBC,GLA,A("e","RD","g"),LX], "RD","l", want=OK, extra=lambda S:bool(S.C.get("glo")))
WD = ST.withdraw("wd","A","dcd",("dab","dac"))
run("D1d conferrer A withdraws the accepted two-key conferral, concurrent with glo", base+[GBC,GLA,WD,A("e","RD","g"),LX], "RD","l", want=OK, extra=lambda S:(bool(S.C.get("wd")),duty(S)))
U2 = dict(ST.unseat("u2","A","B","moderate","g","self",("dab","dac")), to=("B","C"), cuts=ST._slots(("B","C"),"moderate","g"))
run("D1e A's own (conf self) unseat naming B and C, concurrent", base+[GBC,GLA,U2,A("e","RD","g"),LX], "RD","l", extra=lambda S:(bool(S.C.get("u2")),duty(S)))
WB = ST.withdraw("wb","B","dcd",("dab",)); WC = ST.withdraw("wc","C","dcd",("dac",))
run("D1f B and C each lay down (two ends), concurrent", base+[GBC,GLA,WB,WC,A("e","RD","g"),LX], "RD","l", want=LW, extra=duty)
