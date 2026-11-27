exec(open(__file__.replace("rr.py","lib.py")).read())
N = 20
H5 = lambda heads, cites=(): admit("ah","H",FIVE,heads,cites)
# ---- B1 packing
G1 = ST.found("g","A",("A",),{}); solo=[G1]; m=["A"]; pv="g"
for k in "BCDEFG": solo.append(admit("a"+k,k,tuple(m),(pv,))); m.append(k); pv="a"+k
P=[]; mm=["A"]; pv="g"
for i in range(1,13): k="X%d"%i; P.append(admit("p%d"%i,k,tuple(mm),(pv,))); mm.append(k); pv="p%d"%i
run("B1a solo-founded: A admits X1 from {g}", solo+P[:1], ids=("p1",), n=N)
run("B1b solo-founded: A packs X1..X12; A,X* remove B heads (aG,p12)", solo+P+[remove("xb","B",tuple(mm),("aG","p12"))], ids=("p1","p12","xb"), n=N)
run("B1c solo: all seven admit H heads (aG,p12)", solo+P+[admit("ah","H",tuple("ABCDEFG"),("aG","p12"))], ids=("p1","ah"), n=N)
Q=[]; mm2=["A","B"]; pv="g"
for i in range(1,9): k="X%d"%i; Q.append(admit("p%d"%i,k,tuple(mm2),(pv,))); mm2.append(k); pv="p%d"%i
run("B1d A,B pack X1..X8 from {g}; remove D heads (aG,p8)", ROOM+Q+[remove("xd","D",tuple(mm2),("aG","p8"))], ids=("p1","p8","xd"), n=N)
# ---- B2 policy tip
RC = dict(ST.offer("pc","A","B","review",OBJ,"group",("g",),head=("g",),policy="community_invite",cosigners=("B",)), regime="r2")
run("B2 A,B regime tip from {g}; A,B remove D heads (aG,pc)", ROOM+[RC,remove("xd","D",("A","B"),("aG","pc"))], ids=("pc","xd"), n=N)
# ---- B3 old-past removal
XG = remove("xg","G",("A","B"),("g",))
run("B3a A,B remove G from {g}", ROOM+[XG], ids=("xg",), n=N)
run("B3b + honest line ah (five, aG), aj (six, ah)", ROOM+[XG,H5(("aG",)),admit("aj","J",FIVE+("H",),("ah",))], ids=("xg","ah","aj"), n=N)
XC=[]; pv="g"
for k in "GFED": XC.append(remove("x"+k,k,("A","B"),(pv,))); pv="x"+k
run("B3c chained A,B remove G,F,E,D; then A,B remove C heads (aG,xD)", ROOM+XC+[remove("xc","C",("A","B"),("aG","xD"))], ids=("xG","xD","xc"), n=N)
# ---- B4 four tips then removal
XS=[remove("x"+k,k,("A","B"),("g",)) for k in "GFED"]
run("B4 four old-past removal tips; A,B remove C naming all", ROOM+XS+[remove("xc","C",("A","B"),("aG",)+tuple(x["id"] for x in XS))], ids=("xG","xc"), n=N)
# ---- B5 lone holder
DC1 = ST.offer("d1","A","C","moderate",OBJ,"group",("aG",),head=("aG",),policy="duty_confer",counted="duty",cosigners=("C",))
DC0 = ST.offer("d0","A","B","moderate",OBJ,"group",("g",),head=("g",),policy="duty_confer",counted="duty",cosigners=("B",))
WC = ST.unseat("wc","A","C","moderate",OBJ,"group",("d1","d0"),head=("d1","d0"),policy="duty_withdraw",counted="duty",cosigners=("B",))
run("B5 d1 honest; d0 A alone from {g}; A,B withdraw C heads (d1,d0)", ROOM+[DC1,DC0,WC], ids=("d1","d0","wc"), scopes=("member","moderate"), n=N)
# ---- open room stall
GO = dict(ST.found("g","A",("A","B","C"),{"moderate":("A",)},cosigners=("B","C")), open=True)
SA = [ST.offer("sD","D","D","member",OBJ,"group",("g",),head=("g",),policy="open:self_admit"),
      ST.offer("sE","E","E","member",OBJ,"group",("sD",),head=("sD",),policy="open:self_admit")]
AX0 = admit("ax","X",("A","B"),("g",))
run("B7 open room: D,E self-admit; A,B admit X from {g}", [GO]+SA+[AX0], ids=("sD","sE","ax"), n=N)
run("B7b + A,B,X remove D heads (sE,ax)", [GO]+SA+[AX0,remove("xd","D",("A","B","X"),("sE","ax"))], ids=("ax","xd"), n=N)
