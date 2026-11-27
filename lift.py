import sys, os
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import check_agent_removal as AR, seat as ST, checkpoint as CP
CK = ST.CK
ack = CK.row("ak", "ack", "m1", ("x",), room="g", head=("x",))
rows = AR.A + [AR.XA, AR.O1, AR.O2, AR.RSA, ack]
for mut in (False, True):
    CP.MUT.clear()
    if mut: CP.MUT.add("line_concurrent")
    S = CK.concluded(CK.kept(rows), AR.RULE)
    for own in (None, "m1"):
        Q = ST.Seats(S, own=own)
        print("old line" if mut else "new line", own, "rs concluded", S.C["rs"], "stale", sorted(Q.stale), "roster", sorted(Q.roster("g")))
