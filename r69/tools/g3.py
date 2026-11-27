import sys, itertools, random
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
IAM, GI9_6, FRMF = AC.IAM, AC.GI9_6, AC.FRMF
F = ["f%d" % i for i in range(1, 7)]
a = IAM(None, i="a", heads=("w9",), signer="f1", cosigners=("f2", "f3", "f4", "f5"), seat=("X1", "X2", "X3"))
b = IAM(None, i="b", heads=("w9",), signer="f2", cosigners=("f3", "f4", "f5", "f6"), seat=("Y1", "Y2", "Y3"))
K = F + ["X1", "X2", "X3", "Y1", "Y2", "Y3"]
run("C1 six founders (5/9): two concurrent amendments, each seating three (each 9 <= N)", GI9_6 + [a, b], [(k, "founder") for k in K], orders=False)
xa = FRMF("f3", ("X1", "X2", "X3", "f1", "f2"), heads=("a",)); xa["id"] = "xa"
xb = FRMF("f1", ("Y1", "Y2", "Y3", "f3", "f4"), heads=("b",)); xb["id"] = "xb"
xa = grp("xa", "unseat", "f3", "founder", None, heads=("a",), signer="X1", cosigners=("X2", "X3", "f1", "f2"), counted="founder")
xb = grp("xb", "unseat", "f1", "founder", None, heads=("b",), signer="Y1", cosigners=("Y2", "Y3", "f3", "f4"), counted="founder")
run("C2 then on line a X1-3,f1,f2 remove f3; on line b Y1-3,f3,f4 remove f1 (disjoint quorums of 5)", GI9_6 + [a, b, xa, xb], [(k, "founder") for k in K], orders=False)
# seating amendment combined with a removal-ish: an amendment that seats X and names a word with fewer? (not a removal act)
c = IAM(None, i="c", heads=("w9",), signer="f1", cosigners=("f2", "f3", "f4", "f5"), seat=("X1",))
run("C3 amendment stating no word below N seats one", GI9_6 + [c], [("X1", "founder")], orders=False)
d = IAM("quorum:4/7", i="d", heads=("w9",), signer="f1", cosigners=("f2", "f3", "f4", "f5"), seat=("X1",))
run("C4 amendment naming quorum:4/7 (lower M) seating one", GI9_6 + [d], [("X1", "founder")], orders=False)
