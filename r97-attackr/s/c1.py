exec(open(__file__.replace("c1.py","lib.py")).read())
glic = C.glic
LW = (False,"licensure_link_withdrawn"); OK=(True,None); NA=(False,"licensure_delegator_not_authority")
duty = lambda S: sorted(ST.Seats(S).holders("duty","g"))
G3 = ST.found("g","A",("A","B","C"),{"moderate":("A","B","C")},cosigners=("B","C"),licence_classes=((M,False),))
GLO = ST.offer("glo","A",("X",),"license","g","group",("g",),head=("g",),cosigners=("B","C"),counted="duty"); GLA = ST.accept("gla","X","glo")
L = glic("l","g","X")|{"names":("gla",)}
RC = ST.withdraw("rc","C","g")                                   # C resigns, naming only g
run("C1c control: A,B,C confer license on X", [G3,GLO,GLA,A("e","RD","g"),L], "RD","l", want=OK)
run("C1 C resigns from {g} afterwards (concurrent): A,B alone still 2 of 3", [G3,GLO,GLA,RC,A("e","RD","g"),L], "RD","l", want=OK, extra=duty)
GLO2 = ST.offer("glo","A",("X",),"license","g","group",("g",),head=("g",),cosigners=("B",),counted="duty")
run("C1d control: A,B only (2 of 3) confer, C resigns concurrently", [G3,GLO2,GLA,RC,A("e","RD","g"),L], "RD","l", want=OK)
# C1b: a later act built on glo (A,B confer license on Y, head glo)
GY = ST.offer("gy","A",("Y",),"license","g","group",("gla",),head=("glo",),cosigners=("B",),counted="duty"); GYA = ST.accept("gya","Y","gy")
LY = glic("ly","g","Y")|{"names":("gya",)}
run("C1b Y's seat by A,B built on glo; C's backdated resignation", [G3,GLO,GLA,GY,GYA,RC,A("e","RD","g"),LY], "RD","ly", want=OK)
run("C1bc control: no resignation", [G3,GLO,GLA,GY,GYA,A("e","RD","g"),LY], "RD","ly", want=OK)
