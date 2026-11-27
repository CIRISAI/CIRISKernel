exec(open(__file__.replace("b2.py","lib.py")).read())
glic = C.glic; GD = C.GD
LW = (False,"licensure_link_withdrawn"); OK=(True,None)
duty = lambda S: sorted(ST.Seats(S).holders("duty","g"))
G3 = ST.found("g","A",("A","B","C"),{"moderate":("A","B","C")},cosigners=("B","C"),licence_classes=((M,False),))
GLO = ST.offer("glo","A",("X",),"license","g","group",("g",),head=("g",),cosigners=("B",),counted="duty"); GLA = ST.accept("gla","X","glo")
L = glic("l","g","X")|{"names":("gla",)}
U1 = ST.unseat("u1","B","A","moderate","g","group",("g",),head=("g",),cosigners=("C",),counted="duty",policy="duty_withdraw")
U2 = dict(U1, id="u2")
RS = ST.withdraw("rs","A","g")
run("E3c control: B,C withdraw A's duty, concurrent with A,B's license conferral", [G3,U1,GLO,GLA,A("e","RD","g"),L], "RD","l", want=LW, extra=lambda S:(bool(S.C.get("u1")),duty(S)))
run("E3 the same removal written twice (u1, u2)", [G3,U1,U2,GLO,GLA,A("e","RD","g"),L], "RD","l", want=LW, extra=duty)
run("E3b the removal and A's own resignation, both concurrent", [G3,U1,RS,GLO,GLA,A("e","RD","g"),L], "RD","l", want=LW, extra=duty)
# E4: an ex-holder keeps voting: GD, A lays down twice, later A,B confer license naming only g
L1 = ST.withdraw("l1","A","g",(),scope="moderate"); L2 = ST.withdraw("l2","A","g",(),scope="moderate")
GLO_GD = C.GLO
run("E4c control: A lays down once; then A,B confer naming only g", [GD,L1,A("e","RD","g"),GLO_GD,GLA,L], "RD","l", want=LW)
run("E4 A lays down twice; then A,B confer naming only g", [GD,L1,L2,A("e","RD","g"),GLO_GD,GLA,L], "RD","l", want=LW)
