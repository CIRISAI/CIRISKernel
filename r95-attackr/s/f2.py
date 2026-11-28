exec(open(__file__.replace("f2.py","lib.py")).read())
glic = C.glic; G1 = C.G1
OK=(True,None); NA=(False,"licensure_delegator_not_authority"); LW=(False,"licensure_link_withdrawn")
duty = lambda S: sorted(ST.Seats(S).holders("duty","g"))
GLA = ST.accept("gla","X","glo"); LX = glic("l","g","X")|{"names":("gla",)}
print("== community: a counted act from the old past, concurrent with held counted growth")
DCC = ST.offer("dcc","A","C","moderate","g","group",("g",),head=("g",),cosigners=("C",),counted="duty",policy="duty_confer")   # counted growth (A lone)
G1L = ST.offer("glo","A",("X",),"license","g","group",("g",),head=("g",),counted="duty")
run("Q5c control: A (lone) counted license on X, nothing else", [G1,G1L,GLA,A("e","RD","g"),LX], "RD","l", want=OK)
run("Q5 A alone counted license on X from g, concurrent with counted dcc (A,C holders)", [G1,DCC,G1L,GLA,A("e","RD","g"),LX], "RD","l", want=NA, extra=duty)
DC = ST.offer("dc","A","C","moderate","g","self",("g",)); DCA = ST.accept("dca","C","dc")
run("Q6 A alone counted license on X from g, concurrent with lone dc (A,C holders)", [G1,DC,DCA,G1L,GLA,A("e","RD","g"),LX], "RD","l", want=NA, extra=duty)
print("== D1: one end, several voices")
GS = ST.found("g","A",("A",),{},licence_classes=((M,False),))
DCs = [ST.offer("d"+k,"A",k,"moderate","g","self",("g",)) for k in "CD"]; DAs = [ST.accept("a"+k,k,"d"+k) for k in "CD"]
ADM = [ST.offer("m"+k,"A",(k,),"member","g","group",("g",),head=("g",),cosigners=(k,),policy="community_invite") for k in "CD"]
S = arrive([GS]+ADM); print("solo room members", sorted(ST.Seats(S).holders("member","g")))
DC_ = ST.offer("dcd","A",("C","D"),"moderate","g","self",("mC","mD")); DCAc = ST.accept("dac","C","dcd"); DCAd = ST.accept("dad","D","dcd")
base = [GS]+ADM+[DC_,DCAc,DCAd]
S = arrive(base); print("holders after one lone conferral to C,D:", duty(S))
GCD = ST.offer("glo","C",("X",),"license","g","group",("dac","dad"),head=("dcd",),cosigners=("D",),counted="duty")
run("D1c control: C,D (2 of 3) confer license on X", base+[GCD,GLA,A("e","RD","g"),LX], "RD","l", want=OK, extra=lambda S:bool(S.C.get("glo")))
U2 = ST.unseat("u2","A",("C","D"),"moderate","g","self",("mC","mD"))
run("D1 A (the room's own key) unseats C and D in ONE self row, concurrent with glo", base+[GCD,GLA,U2,A("e","RD","g"),LX], "RD","l", want=LW, extra=lambda S:(bool(S.C.get("u2")),duty(S)))
U1 = ST.unseat("u1","A",("C",),"moderate","g","self",("mC","mD"))
run("D1b one-target self unseat of C only, concurrent", base+[GCD,GLA,U1,A("e","RD","g"),LX], "RD","l", want=LW, extra=lambda S:(bool(S.C.get("u1")),duty(S)))
WD = ST.withdraw("wd","A","dcd",("dac","dad"))
run("D1d the conferrer A withdraws its accepted conferral to C,D, concurrent", base+[GCD,GLA,WD,A("e","RD","g"),LX], "RD","l", extra=lambda S:(bool(S.C.get("wd")),duty(S)))
