exec(open(__file__.replace("m3.py","lib.py")).read())
KCH = C.KCH; klic = C.klic; glic = C.glic; G1 = C.G1
LW = (False,"licensure_link_withdrawn"); OK=(True,None)
duty = lambda S: sorted(ST.Seats(S).holders("duty","g"))
DC1 = ST.offer("dc1","A","C","moderate","g","self",("g",)); DA1 = ST.accept("da1","C","dc1")
DC2 = ST.offer("dc2","A","B","moderate","g","self",("g",)); DA2 = ST.accept("da2","B","dc2")
GLA = ST.accept("gla","X","glo")
G3 = ST.offer("glo","A",("X",),"license","g","group",("da1","da2"),head=("dc1","dc2"),cosigners=("B","C"),counted="duty")
L = glic("l","g","X")|{"names":("gla",)}
run("F4e dc1,dc2 concurrent; A,B,C (3 of 3) license to X, both in its past", [G1,DC1,DA1,DC2,DA2,G3,GLA,A("e","RD","g"),L], "RD","l", want=OK, extra=lambda S:(bool(S.C.get("glo")), duty(S)))
G4 = ST.offer("glo","A",("X",),"license","g","group",("da1",),head=("dc1",),cosigners=("C",),counted="duty")
run("F4f control: dc1 only; A,C license to X", [G1,DC1,DA1,G4,GLA,A("e","RD","g"),L], "RD","l", want=OK)
run("F4g dc1 only, reader also holds dc2 (written later, concurrent)", [G1,DC1,DA1,G4,GLA,DC2,DA2,A("e","RD","g"),L], "RD","l", want=OK)
# officer resigns via its appointment: done in m1 F2. Founding resignation:
for nm, w in (("no names", ST.withdraw("wc","C","g")), ("scope member", ST.withdraw("wc","C","g",(),scope="member"))):
    S = arrive([G1,DC1,DA1,w]); Q = ST.Seats(S)
    print("resign", nm, "concl", S.C.get("wc"), "members", sorted(Q.holders("member","g")), "duty", duty(S))
