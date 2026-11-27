exec(open(__file__.replace("a2.py","lib.py")).read())
KCH = C.KCH; klic = C.klic; glic = C.glic; G1 = C.G1
LD = ST.withdraw("ld","A","g",(),scope="moderate")         # the lone holder lays its duty down: locked
NR = (False, "authority_not_reached"); LK = (False,"licensure_authority_locked")
locked = lambda S: TR.locked(S, "g")
run("K0 control: G1 + ld: locked?", [G1,LD,A("e","RD","g"),glic("l","g",cosigners=("B",))|{"names":("ld",)}], "RD","l", want=LK, extra=locked)
run("K2 locked; members' quorum licence naming only g (backdated)", [G1,LD,A("e","RD","g"),glic("l","g",cosigners=("B",))], "RD","l", want=LK, extra=locked)
run("K3 lone holder's edge f before the lock; then lock; walk through f", [G1,A("e","RD","g",depth=1),A("f","A","K",on_behalf="g",names=("g",)),dict(LD,names=("f",)),klic("l")], "RD","l",KCH, want=NR)
run("K4 lock; A (ex-holder) writes edge f naming only g (backdated)", [G1,LD,A("e","RD","g",depth=1),A("f","A","K",on_behalf="g",names=("g",)),klic("l")], "RD","l",KCH, want=NR)
run("K5 lock; A's edge f naming ld (control)", [G1,LD,A("e","RD","g",depth=1),A("f","A","K",on_behalf="g",names=("ld",)),klic("l")], "RD","l",KCH, want=NR)
# removed duty holder: GD (A,B holders); members remove B's duty? use B laying down: then A lone; B+A old-past edge
GD = C.GD
LDB = ST.withdraw("ldb","B","g",(),scope="moderate")
run("K6 B lays down (A lone holder); A alone edge naming ldb (control: lone holder ok)", [GD,LDB,A("e","RD","g",depth=1),A("f","A","K",on_behalf="g",names=("ldb",)),klic("l")], "RD","l",KCH)
