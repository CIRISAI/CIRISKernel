exec(open(__file__.replace("h1.py","lib.py")).read())
glic = C.glic
OK=(True,None); NA=(False,"licensure_delegator_not_authority")
duty = lambda S: sorted(ST.Seats(S).holders("duty","g"))
G3 = ST.found("g","A",("A","B","C","D","E","F","G"),{"moderate":("A","B","C")},cosigners=tuple("BCDEFG"),licence_classes=((M,False),))
GLA = ST.accept("gla","X","glo"); LX = glic("l","g","X")|{"names":("gla",)}
DCC = ST.offer("dcc","A","D","moderate","g","group",("g",),head=("g",),cosigners=("B","C"),counted="duty",policy="duty_confer"); DCA = ST.accept("dca","D","dcc")
WD = ST.withdraw("wd","D","dcc",("dca",))
GLO0 = ST.offer("glo","A",("X",),"license","g","group",("g",),head=("g",),cosigners=("B",),counted="duty")
run("V1' dcc+dca concurrent with glo (A,B from g); D withdraws its seat (concludes)", [G3,DCC,DCA,WD,GLO0,GLA,A("e","RD","g"),LX], "RD","l", want=OK, extra=duty)
run("V1'c without the withdrawal: 2 of 4, refused", [G3,DCC,DCA,GLO0,GLA,A("e","RD","g"),LX], "RD","l", want=NA, extra=duty)
# D and E seated concurrently, then each withdraws: back to ABC
DDE = ST.offer("dde","A",("D","E"),"moderate","g","group",("g",),head=("g",),cosigners=("B","C","D","E"),counted="duty",policy="duty_confer")
WDD = ST.withdraw("wdd","D","dde",("dde",)); WDE = ST.withdraw("wde","E","dde",("dde",))
run("V3 dde (A,B,C seat D,E) concurrent with glo; D and E withdraw: A,B 2 of 3", [G3,DDE,WDD,WDE,GLO0,GLA,A("e","RD","g"),LX], "RD","l", want=OK, extra=duty)
run("V3b only D withdraws: A,B 2 of 4", [G3,DDE,WDD,GLO0,GLA,A("e","RD","g"),LX], "RD","l", want=NA, extra=duty)
# B6: same voices at a LATER head re-counted
DAB = ST.offer("dab","A",("D","E"),"moderate","g","group",("g",),head=("g",),cosigners=("B","D","E"),counted="duty",policy="duty_confer")
FF = ST.offer("ff","A","F","moderate","g","group",("dab",),head=("dab",),cosigners=("B","F"),counted="duty",policy="duty_confer")
run("B6 A,B seat D,E; then A,B seat F at head dab (later head): 2 of 5", [G3,DAB,FF,A("e","RD","g"),glic("l","g","Q")], "RD","l", extra=lambda S:(bool(S.C.get("ff")),duty(S)))
FF2 = ST.offer("ff","A","F","moderate","g","group",("g",),head=("g",),cosigners=("B","F"),counted="duty",policy="duty_confer")
run("B4' A,B seat F at head g (same voices, same head as dab): the ruled batch", [G3,DAB,FF2,A("e","RD","g"),glic("l","g","Q")], "RD","l", extra=lambda S:(bool(S.C.get("ff")),duty(S)))
# batch shared heads but one row also names another change: heads (g) vs heads (g, x)?
