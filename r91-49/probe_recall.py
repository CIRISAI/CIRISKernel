"""r91-49: without the holder. B and C, two of the three founders, recall A at the founding row (a counted row whose
past is only g, so no newer head is in its past) and remove A as a member there; that recall is a vacancy whose
electorate is the founders. Does it conclude, and what does the proposed close give? Run: python3 -I probe_recall.py <root>"""
import sys
sys.path.insert(0, sys.argv[1] + "/models/causal_kernel")
import check_election as EL  # noqa: E402
import probe_rule1 as P1  # noqa: E402
ST, ack, elect, ballot, OBJ = EL.ST, EL.ack, EL.elect, EL.ballot, EL.OBJ
HON = EL.N1R + [EL.N1L2] + EL.G3H + [EL.G3ED] + [ack("k" + k.lower(), k, "ed") for k in "EFG"]
RCG = ST.unseat("rcg", "B", "A", "moderate", OBJ, "group", ("g",), head=("g",), policy="moderator_recall", cosigners=("C",))
XAG = ST.unseat("xag", "B", "A", "member", OBJ, "group", ("g",), head=("g",), policy="community_remove", cosigners=("C",))
ATK = [ballot("yb", "B", "B", ("rcg", "xag")), ballot("yc", "C", "B", ("rcg", "xag")),
       elect("ey", "B", ("yb", "yc", "xag"), vac=("rcg",)), ack("jc", "C", "ey")]
rows = EL.at_newest(HON + [RCG, XAG] + ATK)
S = ST.CK.concluded(ST.CK.kept(list(rows)), EL.RULE)
print("concluded:", {i: bool(S.C.get(i)) for i in ("rcg", "xag", "ey", "ed")})
for own, label in ((None, "no acknowledgement"), ("R", "acknowledged aG")):
    extra = [ST.R("akR", "ack", "R", ("aG",), room=OBJ, head=("aG",))] if own else []
    print("today's rules, reader %s:" % label, dict(zip("BD", EL.answers(EL.at_newest(HON + [RCG, XAG] + ATK + extra),
                                                                         EL.MOD("B") + EL.MOD("D"), own=own))))
P1.proposed(HON + [RCG, XAG] + ATK, "the proposed close over the same rows")
for own, label in ((None, "no acknowledgement"), ("R", "acknowledged aG")):
    extra = [ST.R("akR", "ack", "R", ("aG",), room=OBJ, head=("aG",))] if own else []
    asks = [("A", "member", None), ("A", "moderate", None)]
    print("A's seats today, reader %s:" % label, EL.answers(EL.at_newest(HON + [RCG, XAG] + extra), asks, own=own))
