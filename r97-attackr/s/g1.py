exec(open(__file__.replace("g1.py","lib.py")).read())
glic = C.glic
OK=(True,None); NA=(False,"licensure_delegator_not_authority"); LW=(False,"licensure_link_withdrawn")
duty = lambda S: sorted(ST.Seats(S).holders("duty","g"))
G3 = ST.found("g","A",("A","B","C","D","E","F"),{"moderate":("A","B","C")},cosigners=("B","C","D","E","F"),licence_classes=((M,False),))
GLA = ST.accept("gla","X","glo"); LX = glic("l","g","X")|{"names":("gla",)}
print("== growth that is only an acceptance")
DCC = ST.offer("dcc","A","D","moderate","g","group",("g",),head=("g",),cosigners=("B","C"),counted="duty",policy="duty_confer")   # D not yet accepted
DCA = ST.accept("dca","D","dcc")
GLO = ST.offer("glo","A",("X",),"license","g","group",("dcc",),head=("dcc",),cosigners=("B",),counted="duty")   # A,B: 2 of the 3 seated at dcc
run("A0 control: dcc offered, D never accepts; A,B (2 of 3) confer license", [G3,DCC,GLO,GLA,A("e","RD","g"),LX], "RD","l", want=OK, extra=duty)
run("A1 D accepts later, naming only dcc (concurrent with glo)", [G3,DCC,GLO,GLA,DCA,A("e","RD","g"),LX], "RD","l", want=OK, extra=duty)
run("A1b D accepts naming glo (after it)", [G3,DCC,GLO,GLA,dict(DCA,names=("dcc","glo")),A("e","RD","g"),LX], "RD","l", want=OK, extra=duty)
print("== batch: same voices against overlapping")
DDE = ST.offer("dde","A",("D","E"),"moderate","g","group",("g",),head=("g",),cosigners=("B","D","E"),counted="duty",policy="duty_confer")   # A,B seat D,E: holders 5
DFF = ST.offer("dff","A","F","moderate","g","group",("g",),head=("g",),cosigners=("B","F"),counted="duty",policy="duty_confer")             # A,B from g again
run("B1 A,B seat D,E (5 holders); later A,B seat F from g (same voices: batch)", [G3,DDE,DFF,A("e","RD","g"),glic("l","g","Q")], "RD","l", extra=duty)
DDE3 = dict(DDE, cosigners=("B","C","D","E"))
run("B2 same with dde by A,B,C (overlapping): F re-counted 2 of 5", [G3,DDE3,DFF,A("e","RD","g"),glic("l","g","Q")], "RD","l", extra=duty)
GAB = ST.offer("glo","A",("X",),"license","g","group",("dde","dff"),head=("dde","dff"),cosigners=("B",),counted="duty")
run("B3 after B1: A,B (2 of 6) confer license naming dde,dff", [G3,DDE,DFF,GAB,GLA,A("e","RD","g"),LX], "RD","l", want=NA, extra=duty)
print("== growth on a void or ended seat")
DCA2 = ST.accept("dca","D","dcc"); WD = ST.withdraw("wd","D","dca",("dca",))
GLO0 = ST.offer("glo","A",("X",),"license","g","group",("g",),head=("g",),cosigners=("B",),counted="duty")
run("V0 control: A,B confer from g, nothing concurrent", [G3,GLO0,GLA,A("e","RD","g"),LX], "RD","l", want=OK)
run("V1 dcc+dca concurrent with glo, D then withdraws its acceptance", [G3,DCC,DCA2,WD,GLO0,GLA,A("e","RD","g"),LX], "RD","l", want=OK, extra=duty)
L1 = ST.withdraw("l1","C","g",(),scope="moderate")
DCCc = dict(DCC, cosigners=("C",))     # A,C seat D (2 of 3)...
run("V2 a growth whose count a concurrent lay-down (C) breaks: A,C seat D, C lays down; A,B confer from g", [G3,dict(DCC,cosigners=("C","D")),L1,GLO0,GLA,A("e","RD","g"),LX], "RD","l", want=OK, extra=duty)
