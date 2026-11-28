"""r93-49: can a minority END the seat at an old head, for the reader's roster (ruled (1): the end as the reader's
roster takes it)? A holds moderate and never lays it down; D..G are admitted after the founding row; B and C (two of
the three founders, two of seven members) recall A at g, with only g in the recall's past.
Run: python3 -I probe_oldhead_end.py <tree root>"""
import sys
sys.path.insert(0, sys.argv[1] + "/models/causal_kernel")
import check_election as EL  # noqa: E402
ST, OBJ = EL.ST, EL.OBJ
RCG = ST.unseat("rcg", "B", "A", "moderate", OBJ, "group", ("g",), head=("g",), policy="moderator_recall", cosigners=("C",))
RCN = ST.unseat("rcn", "B", "A", "moderate", OBJ, "group", ("aG",), head=("aG",), policy="moderator_recall", cosigners=("C",))
ACK = ST.R("akR", "ack", "R", ("aG",), room=OBJ, head=("aG",))
asks = [("A", "moderate", None), ("A", "member", None)]
for label, extra in (("no recall (control)", []), ("B, C recall A at g (old head)", [RCG]),
                     ("B, C recall A at aG (newest head, 2 of 7)", [RCN])):
    rows = EL.at_newest(EL.N1R + extra, keep=("rcg",))
    for own in (None, "R"):
        r2 = rows + ([ACK] if own else [])
        S = ST.CK.concluded(ST.CK.kept(list(r2)), EL.RULE)
        print("%-44s reader %-4s concluded=%s  A moderate, member = %s" % (
            label, own, {r["id"]: bool(S.C.get(r["id"])) for r in extra}, EL.answers(r2, asks, own=own)))
