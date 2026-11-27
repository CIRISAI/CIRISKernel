exec(open(__file__.replace("lo.py","lib.py")).read())
DC = lambda i, to, heads, cites=(), sc="moderate": ST.offer(i, "A", to, sc, OBJ, "group", tuple(heads)+tuple(cites), head=tuple(heads), policy="duty_confer", counted="duty", cosigners=())
SCOPES = ("moderate","moderate:spam","duty")
acc = lambda i, k, of: ST.accept(i, k, of)
run("LO1 control: A offers moderate to B (o1), then moderate:spam to C naming o1 (sequential)", ROOM + [DC("o1","B",("aG",)), DC("o2","C",("o1",),sc="moderate:spam")], ids=("o1","o2"), scopes=SCOPES)
run("LO2 the same two offers concurrent, both at aG; B and C accept", ROOM + [DC("o1","B",("aG",)), DC("o2","C",("aG",),sc="moderate:spam"), acc("k1","B","o1"), acc("k2","C","o2")], ids=("o1","o2"), scopes=SCOPES)
# own conferrals (conf self) sequentially
S1 = ST.offer("s1","A","B","moderate",OBJ,"self",("aG",)); S2 = ST.offer("s2","A","C","moderate:spam",OBJ,"self",("s1",))
run("LO3 A's own (conf self) offers in sequence, unaccepted", ROOM + [S1, S2], ids=("s1","s2"), scopes=SCOPES)
run("LO3b + B accepts s1 after s2; C accepts s2", ROOM + [S1, S2, acc("k1","B","s1"), acc("k2","C","s2")], ids=("s1","s2"), scopes=SCOPES)
# offer to a key that accepted elsewhere (standing acceptance), then a second offer
SA = ST.accept("sa","B",None,("aG",),scope="moderate",obj=OBJ)
run("LO4 B's standing acceptance; A offers B (o1), then C (o2)", ROOM + [SA, DC("o1","B",("aG",),("sa",)), DC("o2","C",("o1",),sc="moderate:spam")], ids=("o1","o2"), scopes=SCOPES)
# offer withdrawn by A, then second
W1 = ST.withdraw("w1","A","o1",("o1",))
run("LO5 o1 withdrawn, then o2", ROOM + [DC("o1","B",("aG",)), W1, DC("o2","C",("o1",),("w1",),sc="moderate:spam")], ids=("o1","o2","w1"), scopes=SCOPES)
