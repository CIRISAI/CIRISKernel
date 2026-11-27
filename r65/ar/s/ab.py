exec(open(__file__.replace("ab.py","lib.py")).read())
# (b) the fold's start, with a cheap minority tip AX0 (A,B admit X from {g}) shrinking the common set to ABC(+?)
AX0 = admit("ax","X",("A","B"),("g",))
G = ROOM[0]
def grow(signers_of):
    rows = [G]; mem = ["A","B","C"]; prev = "g"
    for k in "DEFG":
        rows.append(admit("a"+k, k, signers_of(mem, k), (prev,))); mem.append(k); prev = "a"+k
    return rows
U = grow(lambda m, k: tuple(m))                                  # unanimous
T = grow(lambda m, k: tuple(m[:-(len(m)//3)] if len(m) > 3 else m[:2]))   # bare two thirds, earliest members
L = grow(lambda m, k: tuple(m[-((2*len(m)+2)//3):]))             # bare two thirds, the LATEST members
for nm, rs in (("unanimous", U), ("bare 2/3 by earliest", T), ("bare 2/3 by latest", L)):
    print("   growth", nm, [(r["id"], "".join(sorted(ST.signers(r)))) for r in rs[1:]])
    run("Ab %s: cheap tip ax" % nm, rs+[AX0], ids=("aD","aE","aF","aG","ax"))
    run("Ab %s: no tip" % nm, rs, ids=("aD","aE","aF","aG"))
# open room: self-admitted members, then a cheap tip
GO = dict(ST.found("g","A",("A","B","C"),{"moderate":("A",)},cosigners=("B","C")), open=True)
SA = [ST.offer("s"+k,k,k,"member",OBJ,"group",(p,),head=(p,),policy="open:self_admit") for k, p in (("D","g"),)]
SA += [ST.offer("sE","E","E","member",OBJ,"group",("sD",),head=("sD",),policy="open:self_admit")]
run("Ab open room: D,E self-admit (chained)", [GO]+SA, ids=("sD","sE"))
run("Ab open room: D,E self-admit, cheap tip ax by A,B from {g}", [GO]+SA+[AX0], ids=("sD","sE","ax"))
HO = admit("ah","H",("A","B","C","D"),("sE","ax"))
run("Ab ... + A,B,C,D admit H heads (sE,ax)", [GO]+SA+[AX0,HO], ids=("sD","sE","ax","ah"))
