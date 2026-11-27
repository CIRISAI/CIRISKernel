import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G5 = room(5); K5 = "ABCDE"
# a chain: e1 (B, unclosed) -> e2 (C, closed) -> e3 (D)
e1r = [ballot("ba","A","B"), ballot("bb","B","B"), ballot("bc","C","B"), elect("e1","B",("ba","bb","bc")),
       ST.withdraw("wb","B","e1",("e1",))]
e2r = [ballot("a2","A","C",("wb",),of="e1"), ballot("c2","C","C",("wb",),of="e1"), ballot("d2","D","C",("wb",),of="e1"),
       elect("e2","C",("a2","c2","d2"),of="e1",vac=("wb",)),
       ack("q1","A","e2"), ack("q2","B","e2"), ack("q3","D","e2")]            # 3 of {A,B,D,E}: e2 closed
e3r = [ST.withdraw("wc","C","e2",("q1","q2","q3")),
       ballot("a3","A","D",("wc",),of="e2"), ballot("d3","D","D",("wc",),of="e2"), elect("e3","D",("a3","d3"),of="e2",vac=("wc",))]
chain = [G5, LM] + e1r + e2r + e3r
show("F3a the chain e1 -> e2 (closed) -> e3", chain, K5)
# (1) B alone, long after: a fork from before its resignation, one more agreeing ballot of its own, and a superset seating
f = [ballot("bb2","B","B",("e1",)), elect("e1x","B",("ba","bb","bc","bb2"),cites=("e1",))]
show("F3b B forks: e1 plus its own duplicate ballot", chain + f, K5)
# (2) e1 closed first; then a backdated equivocation by one needed receipter kills it and the chain
c1 = [ack("p1","A","e1"), ack("p3","C","e1")]                        # A and C: 2 of {A,C,D,E}: not a majority; add D
c1 += [ack("p4","D","e1")]
wb2 = ST.withdraw("wb","B","e1",("p1","p3","p4"))
chain2 = [G5, LM] + e1r[:4] + c1 + [wb2] + e2r + e3r
show("F3c e1 closed (A, C, D), then the chain", chain2, K5)
riv = [ballot("bd0","D","D"), ballot("be0","E","D"), elect("r1","D",("bd0","be0")), ack("p4x","D","r1")]   # D's concurrent receipt of a rival
show("F3d D (a needed receipter) later forks a receipt of a rival seating it and E made", chain2 + riv, K5)
f2_ = [ballot("bb2","B","B"), elect("e1x","B",("ba","bb","bc","bb2"))]
show("F3e B forks from lm (no e1 in its past): e1's ballots plus its own duplicate", chain + f2_, K5)
un = [elect("e1u","B",("ba","bb","bc","bd0","be0"))]
show("F3f after F3d: the honest union of election g by B", chain2 + riv + un, K5)
