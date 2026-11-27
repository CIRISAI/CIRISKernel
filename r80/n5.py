exec(open(__file__.replace("n5.py","lib.py")).read())
KCH = C.KCH; klic = C.klic; glic = C.glic; E0 = A("e","RD","K")
KRO, KRA = C.KRO, C.KRA
LW = (False,"licensure_link_withdrawn"); NA=(False,"licensure_delegator_not_authority")
KX = CK.row("kx","ack","K",("kra",),room="K")                 # any later row of K's, naming kra
KU = ST.unseat("ku","K","d","key","K","self",("kra",))
KU2 = ST.unseat("ku","K","d","key","K","self",("kx",))        # the eviction names K's newer row, not kra itself
run("V1 eviction names kra; d's licence naming kra (r73 fix)", [E0,KRO,KRA,KU,klic("l",signer="d",names=("kra",))], "RD","l",KCH, want=LW)
run("V2 eviction names kx (which names kra); d's licence naming kra", [E0,KRO,KRA,KX,KU2,klic("l",signer="d",names=("kra",))], "RD","l",KCH, want=LW)
GD, GLO, GLA = C.GLO and C.GD, C.GLO, C.GLA
Y = CK.row("y","ack","A",("gla",),room="g")
GLU2 = ST.unseat("glu","A","X","license","g","group",("y",),head=("glo",),cosigners=("B",),counted="duty",policy="duty_withdraw")
run("V3 control: counted unseat glu names glo,gla; X's licence naming gla", [C.GD,A("e","RD","g"),GLO,GLA,C.GLU,glic("l","g","X")|{"names":("gla",)}], "RD","l", want=LW)
run("V4 glu names y (which names gla); X's licence naming gla", [C.GD,A("e","RD","g"),GLO,GLA,Y,GLU2,glic("l","g","X")|{"names":("gla",)}], "RD","l", want=LW,
    extra=lambda S: bool(S.C.get("glu")))
RO, RA = C.RO, C.RA
RX = CK.row("rx","ack","RD",("ra",),room="RD")
RU2 = ST.unseat("ru","RD","d","key","RD","self",("rx",))
run("V5 RD evicts d naming rx; d writes RD's edge to Z naming ra", [RO,RA,RX,RU2,A("e","d","Z",on_behalf="RD",names=("ra",)),CH.licensure("l","Z","Z",M)], "RD","l",{"Z":(M,)}, want=(False,"authority_not_reached"))
