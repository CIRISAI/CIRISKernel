"""r106-49: the r104 fix (a lay-down behind the reader's line ends no seat for that reader). The lm0 world: A lays
moderate down with only g in its past (lm0); D..G open at aG citing lm0, all rank D, D's seating ed, receipts E, F,
G, B. Readers: None; R (acknowledged aG); R2 (acknowledged aG, then ed).
Probes: (a) A then lays the seat down again at R's line (lm, at aG) and the honest election cites lm instead;
(b) the founders' stale election built on lm0 (opg at g, A B C rank B, eb, receipts A and C), and a reader that
acknowledges eb. Run: python3 -I attack_line.py <tree root> [orders]"""
import sys
sys.path.insert(0, sys.argv[1] + "/models/causal_kernel")
import check_election_close as CC  # noqa: E402
import check_election as EL  # noqa: E402
ST, R, OBJ, CK, RULE = CC.ST, CC.R, CC.OBJ, CC.CK, CC.RULE
N = int(sys.argv[2]) if len(sys.argv) > 2 else 0
LM0 = ST.withdraw("lm0", "A", "g", ("g",), scope="moderate")
LM = ST.withdraw("lm", "A", "g", ("aG",), scope="moderate")
def honest(end, tag=""):
    op = dict(CC.OPEN("op" + tag, end, ("D", "E", "F", "G"), ("aG",)), names=(end, "aG"))
    hb = [CC.B("b" + k.lower() + tag, k, "D", "op" + tag) for k in "DEFG"]
    return [op] + hb + [CC.SEAT("ed" + tag, "D", tuple(b["id"] for b in hb), op="op" + tag, heads=("aG",))] + \
        [CC.ACK("k" + k.lower() + tag, k, "ed" + tag) for k in "EFGB"]
OPG = CC.OPEN("opg", "lm0", ("B", "C"), ("g",))
BAL = [CC.B("y" + k.lower(), k, "B", "opg") for k in "ABC"]
STALE = [OPG] + BAL + [CC.SEAT("eb", "B", tuple(b["id"] for b in BAL), op="opg", heads=("g",)),
                       CC.ACK("ja", "A", "eb"), CC.ACK("jc", "C", "eb")]
RD = {None: [], "R": [R("akR", "ack", "R", ("aG",), room=OBJ, head=("aG",))]}
def acks(after):
    return [R("akR", "ack", "R", ("aG",), room=OBJ, head=("aG",)), R("akR2", "ack", "R", ("akR", after), room=OBJ, head=(after,))]

def ask(rows, reader, sids, arrive=False):
    for m in ("_READER_MEMO", "_VOID_MEMO", "_EMEMO", "_SEATS_OF"): getattr(ST, m).clear()
    ST.KEY_VIEW.append(None)
    try:
        S = CK.arrive(list(rows), RULE) if arrive else CK.concluded(CK.kept(list(rows)), RULE)
        Q = ST.Seats(S, own=reader)
        return ({k: Q.stands(k, "moderate", OBJ) for k in "ABD"},
                {s: ST.election_closed(S, s, reader) for s in sids if s in S.by})
    finally:
        ST.KEY_VIEW.pop()

WORLDS = [
    ("lm0 world", [LM0] + honest("lm0"), ("ed",)),
    ("(a) A lays down again at aG (lm); honest cites lm", [LM0, LM] + honest("lm"), ("ed",)),
    ("(a') the same, honest cites lm0", [LM0, LM] + honest("lm0"), ("ed",)),
    ("(b) the founders' stale election only", [LM0] + STALE, ("eb",)),
    ("(b') stale election and the honest one citing lm0", [LM0] + STALE + honest("lm0"), ("eb", "ed")),
]
for label, extra, sids in WORLDS:
    for reader, rd, tag in ((None, [], "none"), ("R", RD["R"], "R@aG"), ("R", acks(sids[-1]), "R@" + sids[-1]),
                            ("R", acks("eb"), "R@eb") if "eb" in sids else (None, None, None)):
        if rd is None: continue
        rows = EL.N1R + extra + rd
        got = ask(rows, reader, sids)
        line = "%-52s %-7s moderate %s closed %s" % (label, tag, *got)
        if N:
            line += "  orders: %d of %d differ" % (sum(ask([rows[0]] + list(p), reader, sids, arrive=True) != got
                                                       for p in EL.orders(rows, N)), N)
        print(line)
