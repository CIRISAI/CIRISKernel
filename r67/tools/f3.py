import sys, itertools
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
IAD, INODE, GI35, W3 = AC.IAD, AC.INODE, AC.GI35, AC.W3
FS = ("f1", "f2", "f3", "f4", "f5", "f6", "f7")
# GI35: four founders, quorum:3/5 (live needs 4). Two concurrent widenings each to 5 -> 6 > N
a5 = IAD("a5", "f5", ("f1", "f2", "f3")); a6 = IAD("a6", "f6", ("f2", "f3", "f4"))
run("L1 concurrent widenings f5 and f6 at g (each to 5 of N=5)", [GI35, a5, a6], [(k, "founder") for k in FS[:6]])
a7 = IAD("a7", "f7", ("f1", "f5", "f6"), heads=("a5", "a6"))
run("L1b then f1,f5,f6 admit f7 naming both tips", [GI35, a5, a6, a7], [(k, "founder") for k in FS], orders=False)
m = AC.grp("mg", "offer", "Q", "node", None, heads=("a5", "a6"), signer="f1", cosigners=("f2", "f3"), counted="founder")
run("L1c a row naming both tips: founders counted there", [GI35, a5, a6, m], [("Q", "node")], orders=False)
# L2 stalled: f3 leaves -> 3 founders < M+1=4; node seating
run("L2 stalled: f1,f2,f4 seat node n1", [GI35, W3, INODE(("f1", "f2", "f4"), heads=("w3",))], [("n1", "node")])
# L3 a founder leaves and re-admits itself: f3 leaves then signs its own widening with f1,f2,f4 (stalled now)
run("L3 f3 leaves; f1,f2,f4 + f3 re-admit f3", [GI35, W3, IAD("ra", "f3", ("f1", "f2", "f4"), heads=("w3",))], [("f3", "founder")])
# L4 recovery-shaped row with no bundle while stalled
rv = AC.grp("rv", "offer", "f3", "founder", None, heads=("w3",), signer="f3", counted="founder")
run("L4 stalled: f3 signs its own one-seat widening, no bundle", [GI35, W3, rv], [("f3", "founder")])
# L5 the record change while stalled: 3 founders change to quorum:2/3
rc = AC.grp("am", "offer", (), "record", None, heads=("w3",), signer="f1", cosigners=("f2", "f4"), counted="founder", consensus_protocol="quorum:2/3")
run("L5 stalled: f1,f2,f4 change the record to quorum:2/3 (N=3 < 3 founders? live needs 3)", [GI35, W3, rc], [])
run("L5b then f1,f2 remove f4", [GI35, W3, rc, AC.FRMF("f4", ("f1", "f2"), heads=("am",))], [("f4", "founder")])
FRMF = AC.FRMF
x1 = AC.grp("x1", "unseat", "f1", "founder", None, heads=("mg",), signer="f4", cosigners=("f5", "f6"), counted="founder")
x2 = AC.grp("x2", "unseat", "f4", "founder", None, heads=("mg",), signer="f1", cosigners=("f2", "f3"), counted="founder")
run("L1d six founders over N=5: f4,f5,f6 remove f1 and f1,f2,f3 remove f4, both at head mg", [GI35, a5, a6, m, x1, x2], [(k, "founder") for k in FS[:6]], orders=False)
own = ST.offer("o", "f1", "X", "founder", OBJ, "self", ("g",), cosigners=("X",))
run("L6 GI35 (N=5, 4 founders): f1's own offer seats X, then f1's own offer seats Y (6 > N)", [GI35, own, ST.offer("o2", "f1", "Y", "founder", OBJ, "self", ("o",), cosigners=("Y",))], [("X", "founder"), ("Y", "founder")], orders=False)
