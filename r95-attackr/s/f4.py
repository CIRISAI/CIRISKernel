exec(open(__file__.replace("f4.py","lib.py")).read())
glic = C.glic; GD = C.GD; KCH = C.KCH; klic = C.klic
OK=(True,None); NA=(False,"licensure_delegator_not_authority"); LW=(False,"licensure_link_withdrawn"); NR=(False,"authority_not_reached")
GLA = ST.accept("gla","X","glo"); LX = glic("l","g","X")|{"names":("gla",)}
print("== issuance over the licence's own past: a licence naming part of a contest")
G4, UC, UA, GCD = C._G4, C._U_C, C._U_A, C._GLO_CD
for nm, names, want in (("both u1,u2 (the check's case)", ("gla","u1","u2"), OK), ("u1 only (C's removal)", ("gla","u1"), None),
                        ("u2 only (A's removal)", ("gla","u2"), None), ("neither", ("gla",), None)):
    run("C%s" % nm, [G4,UC,UA,GCD,GLA,A("e","RD","g"),glic("l","g","X")|{"names":names}], "RD","l", want=want)
print("== a row built on a cut row")
L1 = ST.withdraw("l1","A","g",(),scope="moderate")
DCC = ST.offer("dcc","A","D","moderate","g","group",("g",),head=("g",),cosigners=("B","D"),counted="duty",policy="duty_confer")
GBD = ST.offer("glo","B",("X",),"license","g","group",("dcc",),head=("dcc",),cosigners=("D",),counted="duty")
GDm = ST.found("g","A",("A","B","C","D"),{"moderate":("A","B")},cosigners=("B","C","D"),licence_classes=((M,False),))
run("W0 control: A,B seat D; B,D confer license on X", [GDm,DCC,GBD,GLA,A("e","RD","g"),LX], "RD","l", want=OK)
run("W1 A lays down concurrently with dcc: D's seat is cut; B,D's conferral built on it", [GDm,L1,DCC,GBD,GLA,A("e","RD","g"),LX], "RD","l", want=LW)
F = A("f","B","K",on_behalf="g",names=("dcc",),cosigners=("D",))
run("W2 the same, B,D sign an edge for g naming dcc", [GDm,L1,DCC,A("e","RD","g",depth=1),F,klic("l")], "RD","l",KCH, want=NR)
