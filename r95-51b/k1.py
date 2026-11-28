import sys, os
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import check_key_view as KV
ST, KE, CK, CH = KV.ST, KV.KE, KV.CK, KV.CH
def run(name, rule, sr, kr, view=True, who="Z"):
    KS = KE.state(list(sr) + list(kr))
    ST.KEY_VIEW.append((lambda rid, k: KE.counts_by(KS, rid, k)) if view else None)
    try:
        ST._READER_MEMO.clear(); ST._VOID_MEMO.clear(); ST._EMEMO.clear(); ST._SEATS_OF.clear()
        S = CK.concluded(CK.kept(list(sr)), KV.WRULE if rule == "window" else KV.RULE)
        P = [q for q in S.Cs if q["id"] in S.anc.get("x", ())] if "x" in S.by else []
        v = set(ST.voices(S.by["x"], P)) if "x" in S.by else None
        Q = ST.Seats(S)
        print(name); print("   x concluded:", bool(S.C.get("x")), "| voices:", sorted(v) if v is not None else None,
                           "| %s member: %s" % (who, Q.stands(who, "member", KV.OBJ)))
    finally:
        ST.KEY_VIEW.pop()
ROOM = CH.ROOM
rotD = KE.rec("qD", "D2", 1, None, names=("kD",), succ_of="D", at_old=1, typ="pseudonym")
# 1. an IN-TIME vote: x signed at 0, before D's rotation (at_old 1); the rotation names D's record only
run("K1a D's in-time cosign of x (at 0), no rotation", "seat", ROOM + [KV.x_row("ABCDE", at=0)], KV.recs())
run("K1b ... then D rotates to D2 (at 1), naming its record only", "seat", ROOM + [KV.x_row("ABCDE", at=0)], KV.recs() + [rotD])
# 2. C revokes, stating revoked_after 9 (x at 3 is before it), from a device that does not hold x
run("K1c C revokes after 9 naming nothing: x (at 3) is before revoked_after", "seat", ROOM + [KV.x_row("ABCDE", at=3)],
    KV.recs() + [KE.revoke("vC", "C", 9)])
# 3. ra is inert for a row that states no instant: a cosign row without `at`, held by the revocation (ra 0)
cC = CK.row("cC", "cosign", "C", ("aG",), of="x")
run("K1d C's cosign row with no instant, C revoked after 0 but its revocation holds the row", "seat",
    ROOM + [cC, KV.x_row("ABDEF", cites=("cC",))], KV.recs() + [KE.revoke("vC", "C", 0, names=("cC",))])
cC3 = CK.row("cC", "cosign", "C", ("aG",), of="x", at=3)
run("K1e control: the same cosign stating at 3, revoked after 0, held: drops", "seat",
    ROOM + [cC3, KV.x_row("ABDEF", cites=("cC",))], KV.recs() + [KE.revoke("vC", "C", 0, names=("cC",))])
# 4. an honest rotation that HOLDS x keeps D's vote; then the retired key D (stolen) revokes itself, naming nothing
rotDx = KE.rec("qD", "D2", 1, None, names=("kD", "x"), succ_of="D", at_old=1, typ="pseudonym")
run("K1f D rotates to D2 holding x: D's vote kept", "seat", ROOM + [KV.x_row("ABCDE", at=0)], KV.recs() + [rotDx])
run("K1g ... then whoever holds the retired key D signs a revocation of D after 0, naming nothing", "seat",
    ROOM + [KV.x_row("ABCDE", at=0)], KV.recs() + [rotDx, KE.revoke("vD", "D", 0)])
# 5. a chain D -> D2 -> D3, and a revocation of D2 by D2 (naming nothing): D's own vote x?
rotD2 = KE.rec("qD2", "D3", 2, None, names=("qD",), succ_of="D2", at_old=2, typ="pseudonym")
run("K1h D -> D2 (holding x) -> D3, then D2 revoked naming nothing: D's vote x", "seat",
    ROOM + [KV.x_row("ABCDE", at=0)], KV.recs() + [rotDx, rotD2, KE.revoke("v2", "D2", 0)])
