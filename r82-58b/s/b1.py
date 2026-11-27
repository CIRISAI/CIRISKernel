exec(open(__file__.replace("b1.py","lib.py")).read())
KCH = C.KCH; klic = C.klic; glic = C.glic; G1, GD = C.G1, C.GD
LW = (False,"licensure_link_withdrawn"); NA=(False,"licensure_delegator_not_authority"); OK=(True,None); NR=(False,"authority_not_reached")
duty = lambda S: sorted(ST.Seats(S).holders("duty","g"))
DC1 = ST.offer("dc1","A","C","moderate","g","self",("g",)); DA1 = ST.accept("da1","C","dc1")
# C has acted as a holder since: a counted act by A,C (license on Y), so the body {A,C} is plainly in force
GY = ST.offer("gy","A",("Y",),"license","g","group",("da1",),head=("dc1",),cosigners=("C",),counted="duty"); GYA = ST.accept("gya","Y","gy")
# later, A alone writes dc2 (A->B) from the OLD past {g}: a "batch" with dc1
DC2 = ST.offer("dc2","A","B","moderate","g","self",("g",)); DA2 = ST.accept("da2","B","dc2")
base = [G1,DC1,DA1,GY,GYA]
run("B0 control: A alone confers moderate on B naming gya (body {A,C}): refused", base+[dict(DC2,names=("gya",)),DA2,A("e","RD","g"),glic("l","g","Q")], "RD","l", extra=duty)
run("B1 A alone confers moderate on B naming only g (batched with dc1)", base+[DC2,DA2,A("e","RD","g"),glic("l","g","Q")], "RD","l", extra=duty)
# then A,B (2 of 3) withdraw C's duty, and A,B confer license on X
WCU = ST.unseat("wcu","A","C","moderate","g","group",("da1","da2","gya"),head=("gy","dc2"),cosigners=("B",),counted="duty",policy="duty_withdraw")
run("B2 + A,B withdraw C's duty (strict majority of the others)", base+[DC2,DA2,WCU,A("e","RD","g"),glic("l","g","Q")], "RD","l", extra=lambda S:(bool(S.C.get("wcu")),duty(S)))
GX = ST.offer("gx","A",("X",),"license","g","group",("da2","gya"),head=("gy","dc2"),cosigners=("B",),counted="duty"); GXA = ST.accept("gxa","X","gx")
run("B3 A,B (2 of 3, via the batched dc2) confer license on X; X licenses", base+[DC2,DA2,GX,GXA,A("e","RD","g"),glic("l","g","X")|{"names":("gxa",)}], "RD","l", want=NA, extra=lambda S:(bool(S.C.get("gx")),duty(S)))
F = A("f","A","K",on_behalf="g",names=("da2","gya"),cosigners=("B",))
run("B4 A,B (2 of 3) sign an edge for g", base+[DC2,DA2,A("e","RD","g",depth=1),F,klic("l")], "RD","l",KCH, want=NR)
# batch spanning a lay-down: A lays down moderate after dc1 (C now lone), then dc2 from {g}
LD = ST.withdraw("ld","A","g",("da1",),scope="moderate")
run("B5 A lays down (C lone), then A alone dc2 from {g}", [G1,DC1,DA1,LD,DC2,DA2,A("e","RD","g"),glic("l","g","Q")], "RD","l", extra=duty)
G5 = ST.offer("g5","B",("X",),"license","g","group",("da2",),head=("dc2",),counted="duty"); G5A = ST.accept("g5a","X","g5")
run("B5b ... then B alone confers license on X from dc2", [G1,DC1,DA1,LD,DC2,DA2,G5,G5A,A("e","RD","g"),glic("l","g","X")|{"names":("g5a",)}], "RD","l", want=NA)
# double end: A lays down moderate twice (two concurrent rows), concurrent with A,B's license conferral
GLO, GLA = C.GLO, C.GLA
L1 = ST.withdraw("l1","A","g",(),scope="moderate"); L2 = ST.withdraw("l2","A","g",(),scope="moderate")
run("E1c control: one lay-down concurrent with A,B's license conferral", [GD,L1,A("e","RD","g"),GLO,GLA,glic("l","g","X")|{"names":("gla",)}], "RD","l", want=LW)
run("E1 two identical lay-downs concurrent with it", [GD,L1,L2,A("e","RD","g"),GLO,GLA,glic("l","g","X")|{"names":("gla",)}], "RD","l", want=LW)
L3 = ST.withdraw("l3","A","g",())
run("E2 a lay-down of moderate and a full resignation, both concurrent", [GD,L1,L3,A("e","RD","g"),GLO,GLA,glic("l","g","X")|{"names":("gla",)}], "RD","l", want=LW)
