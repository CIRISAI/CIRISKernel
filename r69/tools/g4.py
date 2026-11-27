import sys, itertools
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
GI5, IAM, FRMF, FRMN = AC.GI5, AC.IAM, AC.FRMF, AC.FRMN
W4 = ST.withdraw("w4", "f4", "g", ("g",)); W5 = ST.withdraw("w5", "f5", "g", ("w4",))
st = [GI5, W4, W5]   # 3 founders, M=3, live needs 4: stalled
run("L5' stalled: f1,f2,f3 change the record to quorum:2/3", st + [IAM("quorum:2/3", i="am", heads=("w5",), signer="f1", cosigners=("f2", "f3"))], [])
run("L5'' stalled: f1,f2,f3 restate quorum:3/3? (M kept, N=3)", st + [IAM("quorum:2/3", i="am", heads=("w5",), signer="f1", cosigners=("f2", "f3"))], [])
run("S1' stalled: f1,f2,f3 remove nobody: remove f3", st + [FRMF("f3", ("f1", "f2", "f3"), heads=("w5",))], [("f3", "founder")])
x = FRMF("f5", ("f1", "f2", "f3"))
y = grp("y", "unseat", "f4", "founder", None, heads=("g",), signer="f1", cosigners=("f2", "f5"), counted="founder")
run("S4' live (5): f1,f2,f3 remove f5 and f1,f2,f5 remove f4 concurrently", [GI5, x, y], [("f4", "founder"), ("f5", "founder")])
y2 = grp("y", "unseat", "f4", "founder", None, heads=("g",), signer="f1", cosigners=("f2", "f3"), counted="founder")
run("S4'' f1,f2,f3 remove f5 and f1,f2,f3 remove f4 (no voice removed)", [GI5, x, y2], [("f4", "founder"), ("f5", "founder")])
