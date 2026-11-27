import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G = ST.found("g", "A", ("A","B","C"), {"moderate": ("A",)}, cosigners=("B","C"))
rows = [G]; prev = "g"; mem = ["A","B","C"]
for k in "DEFG":
    rows.append(admit("a"+k, k, tuple(mem), (prev,))); mem.append(k); prev = "a"+k
K7 = "ABCDEFG"
lm2 = ST.withdraw("lm2", "A", "g", ("aG",), scope="moderate")           # A resigns at the newest row
H = [ballot("b"+k.lower(), k, r, ("lm2",)) for k, r in zip(K7, "BBDDDDD")]
ids = tuple(b["id"] for b in H)
ed = elect("ed", "D", ids, vac=("lm2",))                                  # D 5 to B 2
show("F2a honest: seven vote, D", rows + [lm2] + H + [ed], K7)
lm1 = ST.withdraw("lm1", "A", "g", ("g",), scope="moderate")             # later, A forks a second end from the founding row
eb = elect("eb", "B", ids + ("lm1",), vac=("lm2","lm1"))                 # electorate A,B,C only: D..G's ballots out; B 2
show("F2b A publishes a backdated end; B's seating names both ends", rows + [lm2] + H + [ed, lm1, eb], K7)
show("F2c the backdated end alone, nobody names it", rows + [lm2] + H + [ed, lm1], K7)
# honest answer: a seating over everything (ballots, both ends) by the count's winner there
eu = elect("eu", "D", ids + ("lm1",), vac=("lm2","lm1"))     # the "union" by D: same electorate A,B,C
show("F2d D tries the union (both ends, all ballots)", rows + [lm2] + H + [ed, lm1, eb, eu], K7)
eu2 = elect("eu", "B", ids + ("lm1",) + ("bd",), vac=("lm2","lm1"))
ak = [ack("k"+k.lower(), k, "eb") for k in "CDEFG"]
show("F2e five of the others receipt B's eb", rows + [lm2] + H + [ed, lm1, eb] + ak, K7)
