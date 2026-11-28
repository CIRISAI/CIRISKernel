"""r103-49: a minority at a stale head, end to end, against the ruled close (election-close 63ab34a).
Founders A, B, C; D..G admitted after g; A holds moderate. B and C (two of seven) write at g only:
rcg (recall A), opg (open, citing rcg), xag (remove A; at g, or at rcg in variant 2), ballots for B, B's seating eb, C's receipt of it.
Asked: does the close of eb hold for a fresh reader, for a reader that acknowledged aG, and does the roster seat B?
Run: python3 -I attack_stale.py <tree root> [orders]"""
import sys
sys.path.insert(0, sys.argv[1] + "/models/causal_kernel")
import check_election_close as CC  # noqa: E402
import check_election as EL  # noqa: E402
ST, R, OBJ, CK = CC.ST, CC.R, CC.OBJ, CC.CK
N = int(sys.argv[2]) if len(sys.argv) > 2 else 0

RCG = ST.unseat("rcg", "B", "A", "moderate", OBJ, "group", ("g",), head=("g",), policy="moderator_recall", cosigners=("C",))
OPG = CC.OPEN("opg", "rcg", ("B", "C"), ("rcg",))
XAG = ST.unseat("xag", "B", "A", "member", OBJ, "group", ("rcg",), head=("rcg",), policy="community_remove", cosigners=("C",))
BAL = [CC.B("yb", "B", "B", "opg"), CC.B("yc", "C", "B", "opg")]
EB = CC.SEAT("eb", "B", ("yb", "yc"), op="opg", heads=("rcg",))
XAG0 = ST.unseat("xag", "B", "A", "member", OBJ, "group", ("g",), head=("g",), policy="community_remove", cosigners=("C",))
ACKR = R("akR", "ack", "R", ("aG",), room=OBJ, head=("aG",))

def ask(rows, reader, arrive=False):
    for m in ("_READER_MEMO", "_VOID_MEMO", "_EMEMO", "_SEATS_OF"): getattr(ST, m).clear()
    ST.KEY_VIEW.append(None)
    try:
        S = CK.arrive(list(rows), RULE) if arrive else CK.concluded(CK.kept(list(rows)), RULE)
        Q = ST.Seats(S, own=reader)
        conc = {i: bool(S.C.get(i)) for i in ("rcg", "opg", "xag", "eb")}
        return conc, Q.stands("B", "moderate", OBJ), Q.stands("A", "moderate", OBJ), ST.election_closed(S, "eb", reader)
    finally:
        ST.KEY_VIEW.pop()

RULE = CC.RULE
for label, extra in (("recall, open, ballots, seating, C's receipt", [RCG, OPG] + BAL + [EB, CC.ACK("jc", "C", "eb")]),
                     ("the same and B, C remove A after the recall (at rcg)", [RCG, XAG, OPG] + BAL + [EB, CC.ACK("jc", "C", "eb")]),
                     ("the same and B, C remove A at g (concurrent: a fork)", [RCG, OPG, XAG0] + BAL + [EB, CC.ACK("jc", "C", "eb")])):
    for reader in (None, "R"):
        rows = EL.N1R + extra + ([ACKR] if reader else [])
        conc, b, a, cl = ask(rows, reader)
        line = "%-48s reader %-4s concluded %s  B mod=%s A mod=%s  election_closed(eb)=%s" % (label, reader, conc, b, a, cl)
        if N:
            got = (conc, b, a, cl)
            diff = [p for p in EL.orders(rows, N) if ask([rows[0]] + list(p), reader, arrive=True) != got]
            line += "  orders: %d of %d differ" % (len(diff), N)
        print(line)
