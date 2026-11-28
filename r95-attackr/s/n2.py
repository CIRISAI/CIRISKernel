exec(open(__file__.replace("n2.py","lib.py")).read())
KCH = C.KCH; klic = C.klic; glic = C.glic; AFD1 = dict(C.AFD1, official="O"); GD = C.GD
NA = (False,"licensure_delegator_not_authority"); NR = (False,"authority_not_reached")
off = lambda S: sorted(ST.Seats(S).holders(ST.OFFICER,"af"))
AOB = ST.offer("aob","A",("B",),"member","af","group",("af",),head=("af",),cosigners=("B",),counted=ST.OFFICER,role=ST.OFFICER)
CSB = ST.R("csb","countersign","O",("aob",),of="aob")
CSC = ST.R("csc","countersign","O",("aoc",),of="aoc")
AOC = ST.offer("aoc","A",("C",),"member","af","group",("aob",),head=("aob",),cosigners=("C",),counted=ST.OFFICER,role=ST.OFFICER)
run("N4 AFD1 + A appoints B then C officers", [AFD1,AOB,CSB,AOC,CSC,A("e","RD","af"),glic("l","af","Q")], "RD","l", extra=off)
LSO = ST.offer("lso","A","X","license","af","self",("af",)); LSOA = ST.accept("lsoa","X","lso")
run("N4b officers ABC; A alone confers license on X naming only af", [AFD1,AOB,CSB,AOC,CSC,LSO,LSOA,A("e","RD","af"),glic("l","af","X")|{"names":("lsoa","aoc")}], "RD","l", want=NA, extra=off)
run("N4c officers ABC; A alone licence for af naming only af", [AFD1,AOB,CSB,AOC,CSC,A("e","RD","af"),glic("l","af","A")], "RD","l", want=NA, extra=off)
run("N4d officers ABC; A alone licence naming aoc (control)", [AFD1,AOB,CSB,AOC,CSC,A("e","RD","af"),glic("l","af","A")|{"names":("aoc",)}], "RD","l", want=NA, extra=off)
run("N4e officers ABC; A alone edge for af naming only af", [AFD1,AOB,CSB,AOC,CSC,A("e","RD","af",depth=1),A("f","A","K",on_behalf="af",names=("af",)),klic("l")], "RD","l",KCH, want=NR, extra=off)
# community grown: GD (A,B duty holders; members A,B,C); admit D,E,F,G by counted member admissions; then A,B quorum licence naming only g
G = dict(GD, consensus_protocol="majority")
rows=[G]; mem=["A","B","C"]; pv="g"
for k in "DEFG":
    rows.append(ST.offer("a"+k,mem[0],(k,),"member","g","group",(pv,),head=(pv,),cosigners=tuple(mem[1:])+(k,),policy="community_invite")); mem.append(k); pv="a"+k
memb = lambda S: sorted(ST.Seats(S).holders("member","g"))
run("N5 control: grown community, A,B quorum licence naming aG", rows+[A("e","RD","g"),glic("l","g",cosigners=("B",))|{"names":("aG",)}], "RD","l", want=NA, extra=memb)
run("N5b grown community; A,B quorum licence naming only g (2 of 3 then)", rows+[A("e","RD","g"),glic("l","g",cosigners=("B",))], "RD","l", want=NA, extra=memb)
