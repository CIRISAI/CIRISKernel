"""r90-49: G3 turned around: the backdated lay-down shrinks the close base, and the founders close B's seating."""
import sys
sys.path.insert(0, sys.argv[1] + "/models/causal_kernel")
import check_election as EL  # noqa: E402
ack, MOD, NOMOD, R, OBJ = EL.ack, EL.MOD, EL.NOMOD, EL.ST.R, EL.OBJ
base = EL.N1R + [EL.N1L2] + EL.G3H + [EL.G3ED] + [ack("k" + k.lower(), k, "ed") for k in "EFG"] + [EL.N1L1] + EL.G3X + [EL.G3B]
asks = MOD("B") + MOD("D")
def show(name, rows, own=None, orders=40):
    rows = EL.at_newest(rows)
    got = EL.answers(rows, asks, own=own)
    cl = {s: EL.closed(rows, s) for s in ("eb", "ed")}
    bad = next((p for p in EL.orders(rows, orders) if EL.answers([rows[0]] + list(p), asks, arrive=True, own=own) != got), None)
    print("%-72s B=%s D=%s closed=%s%s" % (name, got[0], got[1], cl, "" if bad is None else " ORDER-DEPENDENT"))
show("G3c as in the case table (control)", base)
show("+ C receipts B's seating (eb only in its past)", base + [ack("jc", "C", "eb")])
show("+ A and C receipt B's seating", base + [ack("ja", "A", "eb"), ack("jc", "C", "eb")])
show("+ C receipts eb, reader acknowledged aG", base + [ack("jc", "C", "eb"), R("akR", "ack", "R", ("aG",), room=OBJ, head=("aG",))], own="R")
show("+ C receipts eb; and B, C later receipt ed too", base + [ack("jc", "C", "eb"), ack("kb2", "B", "ed", ("jc",))])
show("no honest receipts at all, C receipts eb", EL.N1R + [EL.N1L2] + EL.G3H + [EL.G3ED, EL.N1L1] + EL.G3X + [EL.G3B, ack("jc", "C", "eb")])
