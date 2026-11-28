"""r91-49: today's close (release-0.5.0-wip) reads a counted removal as a departure from the rows held, though the
roster does not take it: B and C remove A at the founding row (past only g); A is a member for every reader, yet the
close base drops A. Run: python3 -I probe_departed.py <tree root>"""
import sys
sys.path.insert(0, sys.argv[1] + "/models/causal_kernel")
import check_election as EL  # noqa: E402
ST, ack, OBJ = EL.ST, EL.ack, EL.OBJ
HON = EL.N1R + [EL.N1L2] + EL.G3H + [EL.G3ED] + [ack("k" + k.lower(), k, "ed") for k in "EFG"]
XAG = ST.unseat("xag", "B", "A", "member", OBJ, "group", ("g",), head=("g",), policy="community_remove", cosigners=("C",))
XEG = ST.unseat("xeg", "B", "E", "member", OBJ, "group", ("aE",), head=("aE",), policy="community_remove", cosigners=("C",))
for label, rows in (("honest, E F G receipt D's", HON), ("+ B and C remove A at g", HON + [XAG]),
                    ("+ B and C remove E at aE (2 of 5 there)", HON + [XEG])):
    rows = EL.at_newest(rows)
    for own in (None, "R"):
        ex = [ST.R("akR", "ack", "R", ("aG",), room=OBJ, head=("aG",))] if own else []
        r2 = EL.at_newest(rows + ex)
        print("%-42s reader %-4s member A=%s E=%s; D moderate=%s; closed(ed)=%s" % (
            label, own, *EL.answers(r2, [("A", "member", None), ("E", "member", None), ("D", "moderate", None)], own=own),
            EL.closed(r2, "ed")))
