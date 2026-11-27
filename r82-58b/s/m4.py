exec(open(__file__.replace("m4.py","lib.py")).read())
glic = C.glic; G1 = C.G1
LW = (False,"licensure_link_withdrawn"); OK=(True,None)
duty = lambda S: sorted(ST.Seats(S).holders("duty","g"))
DC = ST.offer("dc","A","C","moderate","g","self",("g",)); DCA = ST.accept("dca","C","dc")
GLO2 = ST.offer("glo","A",("X",),"license","g","group",("dca",),head=("dc",),cosigners=("C",),counted="duty")
GLA = ST.accept("gla","X","glo"); L = glic("l","g","X")|{"names":("gla",)}
WC = ST.withdraw("wc","C","g")
WC2 = ST.withdraw("wc","C","g",("dca",))
run("F1 C resigns from g (names g only) concurrent with glo", [G1,DC,DCA,WC,GLO2,GLA,A("e","RD","g"),L], "RD","l", want=LW, extra=lambda S:(bool(S.C.get("wc")),duty(S)))
run("F1' C resigns naming dca (dc in its past)", [G1,DC,DCA,WC2,GLO2,GLA,A("e","RD","g"),L], "RD","l", want=LW, extra=lambda S:(bool(S.C.get("wc")),duty(S)))
