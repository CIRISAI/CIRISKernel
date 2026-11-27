import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G5 = room(5); K6 = "ABCDEF"
lm1 = ST.withdraw("lm1", "A", "g", ("g",), scope="moderate")             # A lays moderate down at once
aF = admit("aF", "F", tuple("ABCDE"), ("g",))                            # on another branch F is admitted first
lm2 = ST.withdraw("lm2", "A", "g", ("aF",), scope="moderate")            # and A lays it down there too
H = [ballot("ba","A","F",("lm2",)), ballot("bb","B","F",("lm2",)), ballot("bc","C","F",("lm2",)),
     ballot("bd","D","C",("lm2",)), ballot("be","E","C",("lm2",))]
ids = tuple(b["id"] for b in H)
ef = elect("ef", "F", ids)                                   # past: lm2 only -> electorate A..F, F a candidate
ec = elect("ec", "C", ids, cites=("lm1",))                   # past: lm1 and lm2 -> electorate common to both: A..E
show("B2a F's seating alone", [G5, aF, lm2] + H + [ef], K6)
show("B2b both ends, both seatings over the same set", [G5, lm1, aF, lm2] + H + [ef, ec], K6)
# the same with an honest pair of ends: A resigns on one branch, and the room removes A (member) on the other
