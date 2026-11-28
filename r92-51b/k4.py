import sys, os, random
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import check_key_view as KV
ST, KE, CK = KV.ST, KV.KE, KV.CK
def ans(sr, kr, order):
    KS = KE.arrived(order(list(sr) + list(kr)))
    ST.KEY_VIEW.append(lambda rid, k: KE.counts_by(KS, rid, k))
    try:
        for m in ("_READER_MEMO", "_VOID_MEMO", "_EMEMO", "_SEATS_OF"): getattr(ST, m).clear()
        rows = order(list(sr))
        S = CK.arrive([sr[0]] + [r for r in rows if r is not sr[0]], KV.RULE)
        return bool(S.C.get("x")), ST.Seats(S).stands("Z", "member", KV.OBJ)
    finally:
        ST.KEY_VIEW.pop()
rotDx = KE.rec("qD", "D2", 1, None, names=("kD", "x"), succ_of="D", at_old=1, typ="pseudonym")
cases = [("K1b", KV.CH.ROOM + [KV.x_row("ABCDE", at=0)], KV.recs() + [KE.rec("qD", "D2", 1, None, names=("kD",), succ_of="D", at_old=1, typ="pseudonym")]),
         ("K1g", KV.CH.ROOM + [KV.x_row("ABCDE", at=0)], KV.recs() + [rotDx, KE.revoke("vD", "D", 0)]),
         ("K1f", KV.CH.ROOM + [KV.x_row("ABCDE", at=0)], KV.recs() + [rotDx])]
rnd = random.Random(3)
for name, sr, kr in cases:
    seen = set()
    for _ in range(30):
        def order(rs):
            rs = list(rs); head = rs[0]; t = rs[1:]; rnd.shuffle(t); return [head] + t
        seen.add(ans(sr, kr, order))
    print(name, "answers over 30 orders:", seen)
