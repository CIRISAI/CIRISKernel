import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G = ST.found("g", "A", ("A","B","C"), {"moderate": ("C",)}, cosigners=("B","C"))
rows = [G]; prev = "g"; mem = ["A","B","C"]
for k in "DEFG":
    rows.append(admit("a"+k, k, tuple(mem), (prev,))); mem.append(k); prev = "a"+k
K7 = "ABCDEFG"
show("B5a C moderates a room of seven", rows, K7)
xc = ST.unseat("xc", "A", "C", "member", "g", "group", ("g", "aG"), head=("g",), policy="community_remove", cosigners=("B",))
el = [ballot("ba","A","A",("xc",)), ballot("bb","B","A",("xc",)), elect("ea","A",("ba","bb"),vac=("xc",))]
show("B5b A,B remove C at the founding head (2 of 3 there), then elect A with their two ballots", rows + [xc] + el, K7)
ak = R("ak", "ack", "R", ("aG",), room="g", head=("aG",))
show("B5c same, reader acknowledged aG", rows + [ak, xc] + el, K7, own="R")
