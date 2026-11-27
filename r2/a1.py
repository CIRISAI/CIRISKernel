import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
# A1: two seatings over the SAME set of rows at different heads: different winners, both stand
G5, LM = E.G5, E.LM
K6 = "ABCDEF"
ax = admit("ax", "F", ("A", "B", "C", "D"), ("lm",))
bal = [ballot("ba","A","F",("ax",)), ballot("bb","B","F",("ax",)), ballot("bc","C","F",("ax",)),
       ballot("bd","D","C",("ax",)), ballot("be","E","C",("ax",))]
ids = tuple(b["id"] for b in bal)
ef = elect("ef", "F", ids, K6, heads=("ax",))
ecl = elect("ec", "C", ids, K6, heads=("lm",))
show("A1a honest F at head ax only", [G5, LM, ax] + bal + [ef], K6)
show("A1b C at old head lm over the same five ballots only", [G5, LM, ax] + bal + [ecl], K6)
show("A1c both", [G5, LM, ax] + bal + [ef, ecl], K6)
