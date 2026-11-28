"""r103-49: the honest election in the seven-room (A lays moderate down at the newest row; D, E, F, G open; all seven
rank D; D's seating closed by A, E, F, G), and two founders' stale rows at g: a recall of A (rcg), and an opening
citing it (opg). Does the honest close hold for a fresh reader, and for one that acknowledged aG?
Run: python3 -I attack_block.py <tree root> [orders]"""
import sys
sys.path.insert(0, sys.argv[1] + "/models/causal_kernel")
import check_election_close as CC  # noqa: E402
import check_election as EL  # noqa: E402
ST, R, OBJ, CK, RULE = CC.ST, CC.R, CC.OBJ, CC.CK, CC.RULE
N = int(sys.argv[2]) if len(sys.argv) > 2 else 0
LM = ST.withdraw("lm", "A", "g", ("aG",), scope="moderate")
OP = CC.OPEN("op", "lm", ("D", "E", "F", "G"), ("aG",))
HB = [CC.B("b" + k.lower(), k, "D", "op") for k in "ABCDEFG"]
ED = CC.SEAT("ed", "D", tuple(b["id"] for b in HB), op="op", heads=("aG",))
HON = EL.N1R + [LM, OP] + HB + [ED] + [CC.ACK("k" + k.lower(), k, "ed") for k in "AEFG"]
RCG = ST.unseat("rcg", "B", "A", "moderate", OBJ, "group", ("g",), head=("g",), policy="moderator_recall", cosigners=("C",))
OPG = CC.OPEN("opg", "rcg", ("B", "C"), ("rcg",))
ACKR = R("akR", "ack", "R", ("aG",), room=OBJ, head=("aG",))

def ask(rows, reader, arrive=False):
    for m in ("_READER_MEMO", "_VOID_MEMO", "_EMEMO", "_SEATS_OF"): getattr(ST, m).clear()
    ST.KEY_VIEW.append(None)
    try:
        S = CK.arrive(list(rows), RULE) if arrive else CK.concluded(CK.kept(list(rows)), RULE)
        return ({i: bool(S.C.get(i)) for i in ("op", "ed", "rcg", "opg") if i in S.by},
                ST.Seats(S, own=reader).stands("D", "moderate", OBJ), ST.election_closed(S, "ed", reader))
    finally:
        ST.KEY_VIEW.pop()

for label, extra in (("honest", []), ("+ B, C recall A at g", [RCG]), ("+ and open citing it at g", [RCG, OPG]),
                     ("+ B, C open citing lm at g (no recall)", [dict(CC.OPEN("opg", "lm", ("B", "C"), ("g",)), names=("lm", "g"))])):
    for reader in (None, "R"):
        rows = HON + extra + ([ACKR] if reader else [])
        got = ask(rows, reader)
        line = "%-40s reader %-4s concluded %s  D mod=%s  election_closed(ed)=%s" % (label, reader, *got)
        if N:
            line += "  orders: %d of %d differ" % (sum(ask([rows[0]] + list(p), reader, arrive=True) != got for p in EL.orders(rows, N)), N)
        print(line)
