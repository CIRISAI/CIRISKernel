import sys, itertools
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
FH4 = AC.FH4   # A,B,C,D; A holds moderate
ag = grp("ag", "offer", ("X", "Y", "Z"), "agent", "cosigned_act", signer="A", cosigners=("B", "C", "X", "Y", "Z"))
rc = grp("rc", "unseat", "A", "moderate", None, heads=("ag",), signer="X", cosigners=("Y", "Z"), counted="agent")
run("R1 three agents recall moderator A (counted agent)", [FH4, ag, rc], [("A", "moderate")])
rcm = grp("rc", "unseat", "A", "moderate", None, heads=("ag",), signer="B", cosigners=("C",), counted="member")
run("R1-base B, C recall A counted over members", [FH4, ag, rcm], [("A", "moderate")])
# a subset of duty holders withdraws a duty: moderate A,B,F; review C,D,E
G = ST.found("g", "A", ("A", "B", "C", "D", "E", "F"), {"moderate": ("A", "B", "F"), "review": ("C", "D", "E")}, cosigners=("B", "C", "D", "E", "F"))
w = grp("w", "unseat", "B", "moderate", None, signer="A", cosigners=("F",), counted="moderate")
run("R2 A, F (2 of the 5 other duty holders) withdraw B's moderate, counted over moderate", [G, w], [("B", "moderate")])
w2 = dict(w, counted="duty")
run("R2-base same counted over duty", [G, w2], [("B", "moderate")])
