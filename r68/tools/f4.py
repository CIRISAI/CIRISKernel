import sys, itertools
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
GI35, W3, FRMF, FRMN = AC.GI35, AC.W3, AC.FRMF, AC.FRMN
run("S1 stalled (3 of M+1=4): f1,f2,f4 remove f2? no: remove f4", [GI35, W3, FRMF("f4", ("f1", "f2", "f4"), heads=("w3",))], [("f4", "founder")])
run("S2 stalled: f1,f2,f4 remove node n1 (seated before)", [GI35, AC.INODE(("f1", "f2", "f3")), W3, FRMN(("f1", "f2", "f4"), heads=("w3", "r"))], [("n1", "node")], orders=False)
run("S3 live (4): f1,f2,f3 remove f4 -> 3 left, stalled", [GI35, FRMF("f4", ("f1", "f2", "f3"))], [("f4", "founder")])
x2 = AC.grp("x2", "unseat", "f3", "founder", None, heads=("g",), signer="f1", cosigners=("f2", "f4"), counted="founder")
run("S4 two concurrent removals at g (live): f1,f2,f3 remove f4 and f1,f2,f4 remove f3", [GI35, FRMF("f4", ("f1", "f2", "f3")), x2], [("f3", "founder"), ("f4", "founder")])
own_lv = ST.withdraw("w1", "f1", "g", ("g",))
run("S5 stalled by f3 leaving; f3 (left) + f1,f2 remove f4 naming g, w3 in past", [GI35, W3, dict(FRMF("f4", ("f1", "f2", "f3")), names=("g", "w3"))], [("f4", "founder")])
