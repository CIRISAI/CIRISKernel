import sys, os
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import check_removal_in_force as RF
import key_end as KE
ST, CK = RF.ST, RF.CK
recs = [KE.rec("k" + k, k, 0, None, typ="pseudonym") for k in ("p1", "p2", "p3", "AG")]
def run(name, rows, keyrows, view=True):
    KS = KE.state(list(rows) + list(keyrows))
    ST.KEY_VIEW.append((lambda rid, k: KE.counts_by(KS, rid, k)) if view else None)
    try:
        for m in ("_READER_MEMO", "_VOID_MEMO", "_EMEMO", "_SEATS_OF"): getattr(ST, m).clear()
        S = CK.concluded(CK.kept(list(rows)), RF.RULE)
        Q = ST.Seats(S)
        print(name); print("   AG on the roster:", Q.stands("AG", "agent", "g"))
    finally:
        ST.KEY_VIEW.pop()
base = RF.W + [RF.X, RF.UND]
run("K3a p1's lone removal of AG, then p2, p3 withdraw p1's moderate: no receipt", base, recs)
r2 = RF.receipt("r2", "p2", "x")
run("K3b with p2's receipt of x (a duty holder's): x stays in force", RF.W + [RF.X, r2, RF.UND], recs)
run("K3c ... p2 then revokes itself after 0, naming nothing (the receipt not in its past)", RF.W + [RF.X, r2, RF.UND],
    recs + [KE.revoke("v2", "p2", 0)])
run("K3d p1's lone removal x of AG alone", RF.W + [RF.X], recs)
run("K3e ... p1 revoked itself after 0, naming nothing (x not in its past)", RF.W + [RF.X], recs + [KE.revoke("v1", "p1", 0)])
