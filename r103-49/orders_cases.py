"""r103-49: check_election_close.py's 19 cases in arrival orders (the check reads each case once, as listed).
Run: python3 -I orders_cases.py <tree root> [orders]"""
import sys
sys.path.insert(0, sys.argv[1] + "/models/causal_kernel")
import check_election_close as CC  # noqa: E402
import check_election as EL  # noqa: E402
ST, KE, CK = CC.ST, CC.KE, CC.CK
N = int(sys.argv[2]) if len(sys.argv) > 2 else 20

def answer(rows, sid, ask, reader, keys, arrive):
    ST.KEY_VIEW.append((lambda KS: (lambda rid, k: KE.counts_by(KS, rid, k)))(KE.state(list(rows) + list(keys))) if keys is not None else None)
    try:
        for m in ("_READER_MEMO", "_VOID_MEMO", "_EMEMO", "_SEATS_OF"): getattr(ST, m).clear()
        S = CK.arrive(list(rows), CC.RULE) if arrive else CK.concluded(CK.kept(list(rows)), CC.RULE)
        return ST.Seats(S, own=reader).stands(ask[0], ask[1], CC.OBJ), ST.election_closed(S, sid, reader)
    finally:
        ST.KEY_VIEW.pop()

for name, rows, sid, kw, want in CC.CASES:
    if rows is None:
        kw = dict(kw, ask=("A", "moderate") if sid == "open_persons" else ("B", "moderate"))
        rows = CC.person_world(sid == "open_persons"); sid = "eb"
    a = (kw.get("ask", ("C", "moderate")), kw.get("reader"), kw.get("keys"))
    got = answer(rows, sid, *a, arrive=False)
    diff = [p for p in EL.orders(rows, N) if answer([rows[0]] + list(p), sid, *a, arrive=True) != got]
    print("%-70s %s%s  orders: %d of %d differ%s" % (name[:70], got, "" if got == want else " (WANT %s)" % (want,),
          len(diff), min(N, len(EL.orders(rows, N))), "" if not diff else ", first %s" % [r["id"] for r in diff[0]]))
