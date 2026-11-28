"""r104-49: the holder colludes. A (moderate) lays the seat down at g (lm0, only g in its past): a holder's own
withdrawal, no counted act, so no S'' void reaches it. B and C open at g citing lm0 (2 of the 3 members there); A, B
and C rank B; B's seating at g; A and C receipt it. D..G (admitted after g) never vote. Then the honest side opens
at the newest head citing lm0, with and without the stale opening in its past.
Run: python3 -I attack_holder.py <tree root> [orders]"""
import sys
sys.path.insert(0, sys.argv[1] + "/models/causal_kernel")
import check_election_close as CC  # noqa: E402
import check_election as EL  # noqa: E402
ST, R, OBJ, CK, RULE = CC.ST, CC.R, CC.OBJ, CC.CK, CC.RULE
N = int(sys.argv[2]) if len(sys.argv) > 2 else 0
LM0 = ST.withdraw("lm0", "A", "g", ("g",), scope="moderate")
OPG = CC.OPEN("opg", "lm0", ("B", "C"), ("g",))
BAL = [CC.B("y" + k.lower(), k, "B", "opg") for k in "ABC"]
EB = CC.SEAT("eb", "B", tuple(b["id"] for b in BAL), op="opg", heads=("g",))
ATK = [LM0, OPG] + BAL + [EB, CC.ACK("ja", "A", "eb"), CC.ACK("jc", "C", "eb")]
KBN = ()
def honest(names):
    op = dict(CC.OPEN("op", "lm0", ("D", "E", "F", "G"), ("aG",)), names=("lm0", "aG") + names)
    hb = [CC.B("b" + k.lower(), k, "D", "op") for k in "DEFG"]
    return [op] + hb + [CC.SEAT("ed", "D", tuple(b["id"] for b in hb), op="op", heads=("aG",))] + \
        [CC.ACK("k" + k.lower(), k, "ed") for k in "EFG"] + [CC.ACK("kb", "B", "ed", KBN)]
ACKR = R("akR", "ack", "R", ("aG",), room=OBJ, head=("aG",))

def ask(rows, reader, arrive=False):
    for m in ("_READER_MEMO", "_VOID_MEMO", "_EMEMO", "_SEATS_OF"): getattr(ST, m).clear()
    ST.KEY_VIEW.append(None)
    try:
        S = CK.arrive(list(rows), RULE) if arrive else CK.concluded(CK.kept(list(rows)), RULE)
        Q = ST.Seats(S, own=reader)
        return ({i: bool(S.C.get(i)) for i in ("opg", "eb", "op", "ed") if i in S.by},
                {k: Q.stands(k, "moderate", OBJ) for k in "ABD"},
                {s: ST.election_closed(S, s, reader) for s in ("eb", "ed") if s in S.by})
    finally:
        ST.KEY_VIEW.pop()

for label, extra in (("the founders' stale election", ATK),
                     ("+ the honest one, not holding the stale opening", ATK + honest(())),
                     ("+ the honest one, its opening holding opg", ATK + honest(("opg",)))):
    for reader in (None, "R"):
        rows = EL.N1R + extra + ([ACKR] if reader else [])
        got = ask(rows, reader)
        line = "%-48s reader %-4s concluded %s  moderate %s  closed %s" % (label, reader, *got)
        if N:
            line += "  orders: %d of %d differ" % (sum(ask([rows[0]] + list(p), reader, arrive=True) != got for p in EL.orders(rows, N)), N)
        print(line)
# B's receipt naming its own stale seating (eb), with the honest opening holding opg
KBN = ("eb",)
for reader in (None, "R"):
    rows = EL.N1R + ATK + honest(("opg",)) + ([ACKR] if reader else [])
    print("%-48s reader %-4s concluded %s  moderate %s  closed %s" % ("+ holding opg, B's receipt naming eb", reader, *ask(rows, reader)))
