import sys, os
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import check_agent_removal as AR
import key_end as KE
ST, WN, CK = AR.ST, AR.WN, AR.CK
recs = [KE.rec("k" + k, k, 0, None, typ="pseudonym") for k in ("m1", "m2", "MOD", "AG")]
def run(name, rows, keyrows, view=True):
    KS = KE.state(list(rows) + list(keyrows))
    ST.KEY_VIEW.append((lambda rid, k: KE.counts_by(KS, rid, k)) if view else None)
    try:
        for m in ("_READER_MEMO", "_VOID_MEMO", "_EMEMO", "_SEATS_OF"): getattr(ST, m).clear()
        S = CK.concluded(CK.kept(list(rows)), AR.RULE)
        Q = ST.Seats(S)
        print(name); print("   rs concluded:", bool(S.C.get("rs")), "| AG agent seated:", Q.stands("AG", "agent", "g"))
    finally:
        ST.KEY_VIEW.pop()
rows = AR.A + [AR.XA, AR.O1, AR.O2, AR.RSA]
run("K2a the lift: m1, m2 object, the re-seating concludes", rows, recs)
run("K2b m2 revoked itself after 0, naming nothing (its objection o2 is not in the revocation's past)", rows, recs + [KE.revoke("v2", "m2", 0)])
run("K2c control: no key view", rows, recs + [KE.revoke("v2", "m2", 0)], view=False)
for plant in ("window_key_view_unread", "key_view_unread"):
    ST.MUT.add(plant)
    run("K2d plant %s on: m2 revoked naming nothing" % plant, rows, recs + [KE.revoke("v2", "m2", 0)])
    ST.MUT.discard(plant)
v2 = KE.revoke("v2", "m2", 0, names=("lm",))          # m2's revocation holds the room up to m1's lay-down (not x, not o2)
run("K2e m2 revoked after 0 holding the room before x: its objection o2 is late", rows, recs + [v2])
run("K2f control: m2 revoked holding o2", rows, recs + [KE.revoke("v2", "m2", 0, names=("o2",))])
