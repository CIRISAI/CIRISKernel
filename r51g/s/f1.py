import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G5 = room(5); K5 = "ABCDE"
xe = ST.unseat("xe", "A", "E", "member", "g", "group", ("g",), head=("g",), policy="community_remove", cosigners=("B","C","D"))
ae = admit("ae", "E", ("A","B","C","D"), ("xe",))                     # E re-admitted
lm = ST.withdraw("lm", "A", "g", ("ae",), scope="moderate")           # then the vacancy
H = [ballot("ba","A","E"), ballot("bb","B","E"), ballot("bc","C","C"), ballot("bd","D","C"), ballot("be","E","E")]
ids = tuple(b["id"] for b in H)
ee = elect("ee", "E", ids)
show("F1a honest: E re-admitted before the vacancy, E wins 3-2", [G5, xe, ae, lm] + H + [ee], K5)
ec = elect("ec", "C", ids + ("xe",))                                    # C names E's OLD removal: E is no voice, no candidate
show("F1b C's seating names E's old (undone) removal: a strict superset", [G5, xe, ae, lm] + H + [ee, ec], K5)
# the same with E's own old leaving, then re-admission
le = ST.withdraw("le", "E", "g", ("g",))
ae2 = admit("ae", "E", ("A","B","C","D"), ("le",))
lm2 = ST.withdraw("lm", "A", "g", ("ae",), scope="moderate")
ec2 = elect("ec", "C", ids + ("le",))
show("F1c the same with E's own old leaving, E re-admitted", [G5, le, ae2, lm2] + H + [ee, ec2], K5)
