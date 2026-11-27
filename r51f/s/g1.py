import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G5 = room(5); K5 = "ABCDE"
# A, the holder, lays moderate down (lm). Concurrently B, C and D recall A (a counted unseat of A's moderate seat, B its signer).
rc = ST.unseat("rc", "B", "A", "moderate", "g", "group", ("g",), head=("g",), policy="moderator_recall", cosigners=("C","D"))
# honest ballots name lm (the end they saw). B's ballot is concurrent with B's recall row.
H = [ballot("ba","A","C"), ballot("bb","B","B"), ballot("bc","C","B"), ballot("bd","D","C"), ballot("be","E","C")]
ids = tuple(b["id"] for b in H)
ec = elect("ec","C",ids)                                               # C 3 (A, D, E), B 2
show("G1a honest: C over five ballots naming lm", [G5, LM, rc] + H + [ec], K5)
# E names the recall too: its own second ballot (agreeing) names rc, so rc is an end in E's seating's set
be2 = ballot("be2","E","C",("lm","rc","be"))
ec2 = elect("ec2","C",ids+("be2",), vac=("lm","rc"))
show("G1b a seating whose set holds the recall as an end: does it fork B?", [G5, LM, rc] + H + [ec, be2, ec2], K5)
# weapon: B's two rows (rc, bb) concurrent, both in the set -> B no voter; flip a result where B is decisive
H2 = [ballot("ba","A","B"), ballot("bb","B","B"), ballot("bc","C","B"), ballot("bd","D","C"), ballot("be","E","C")]
eb = elect("eb","B",ids)                                               # B 3, C 2
be3 = ballot("be2","E","C",("lm","rc","be"))
ecx = elect("ecx","C",ids+("be2",), vac=("lm","rc"))                  # with B struck: A:B and C:B ballots rank B -> void; C 2
show("G1c honest B wins 3-2", [G5, LM, rc] + H2 + [eb], K5)
show("G1d E names B's recall row as an end: B forked, struck, C wins by containment", [G5, LM, rc] + H2 + [eb, be3, ecx], K5)
