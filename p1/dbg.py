import sys, os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "p1.py")).read().split("run(\"control")[0])
XG2 = remove("xg", "G", ("A","B"), ("g",))
for rs, own in ((rows+[ACK, XG2], "R"), (rows+[ACK], "R"), (rows+[XG2], None)):
    S = CK.concluded(CK.kept(list(rs)), RULE); Q = ST.Seats(S, own=own)
    print([ (r["k"], r["offer"]) for r in Q.recs if r["k"]=="G"], "tips", [t["id"] for t in Q.tips(OBJ)], "fold", Q.tips_fold("member", OBJ), "dropped", getattr(Q,"dropped",None))
