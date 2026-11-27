import sys, itertools
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
F4 = lambda proto, **kw: ST.offer("g", "A", ("A", "B", "C", "D"), "member", "@", "self", cosigners=("B", "C", "D"), consensus_protocol=proto, **kw)
rc = lambda i, proto, pol, signer, cos, heads=("g",), **kw: grp(i, "offer", kw.pop("to", ()), "record", pol, heads=heads, signer=signer, cosigners=cos, consensus_protocol=proto, **kw)
rmD = lambda heads, signer="A", cos=(): grp("x", "unseat", "D", "member", None, heads=heads, signer=signer, cosigners=cos)
# F1 unanimous room: 3 of 4 under default_standing install quorum:1/1, then A alone removes D
run("F1 unanimous: A,B,C change to quorum:1/1 under default_standing", [F4("unanimous"), rc("am", "quorum:1/1", "default_standing", "A", ("B", "C")), rmD(("am",))], [("D", "member")])
run("F1-base unanimous: same under cosigned_act", [F4("unanimous"), rc("am", "quorum:1/1", "cosigned_act", "A", ("B", "C")), rmD(("am",))], [("D", "member")])
# F2 open:self_admit: two members change the record
run("F2 open:self_admit: A,B change to quorum:1/1 (cosigned_act)", [F4("open:self_admit"), rc("am", "quorum:1/1", "cosigned_act", "A", ("B",)), rmD(("am",))], [("D", "member")])
# F2b a NON-member X changes the record alone, naming itself in `to`
run("F2b open:self_admit: non-member X alone, record change to=(X,)", [F4("open:self_admit"), rc("am", "quorum:1/1", "cosigned_act", "X", (), to=("X",)), rmD(("am",))], [("D", "member"), ("X", "record")])
# F2c open: removal needs 2 voices (the set says: unstated)
run("F2c open:self_admit: A and B remove D", [F4("open:self_admit"), rmD(("g",), "A", ("B",))], [("D", "member")])
# F3 quorum:2/9 in a room of 4: two lower it to quorum:1/1
run("F3 quorum:2/9: A,B change to quorum:1/1", [F4("quorum:2/9"), rc("am", "quorum:1/1", "cosigned_act", "A", ("B",)), rmD(("am",))], [("D", "member")])
# F5 founder_only, founded with scope founder: one founder changes the record
GF = ST.offer("g", "A", ("A", "B", "C", "D"), "founder", "@", "self", cosigners=("B", "C", "D"), consensus_protocol="founder_only")
run("F5 founder_only (scope founder): A alone changes to quorum:1/1 counted founder", [GF, rc("am", "quorum:1/1", "cosigned_act", "A", (), counted="founder"),
    grp("x", "unseat", "D", "founder", None, heads=("am",), signer="A")], [("D", "founder")])
run("F5b founder_only founded scope member: A,B,C admit E counted founder", [F4("founder_only"), grp("r", "offer", "E", "member", "cosigned_act", signer="A", cosigners=("B", "C", "E"), counted="founder")], [("E", "member")])
# F6 open infra: a key seats itself a founder
GI = ST.offer("g", "f1", ("f1", "f2", "f3"), "member", "@", "self", cosigners=("f2", "f3"), cohort_subkind="infrastructure", consensus_protocol="open:self_admit")
run("F6 open infra: X signs its own founder admission", [GI, grp("r", "offer", "X", "founder", "cosigned_act", signer="X")], [("X", "founder"), ("X", "member")], obj=None) if False else None
