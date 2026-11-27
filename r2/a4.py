import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G5, LM = E.G5, E.LM
K5 = "ABCDE"
e1rows = [ballot("ba","A","B"), ballot("bb","B","B"), elect("e1","B",("ba","bb"),K5), ST.withdraw("wb","B","e1",("e1",))]
e2rows = [ballot("ba2","A","C",("wb",),of="e1"), ballot("bb2","B","C",("wb",),of="e1"), ballot("bc2","C","C",("wb",),of="e1"),
          elect("e2","C",("ba2","bb2","bc2"),K5,heads=("wb",),of="e1")]
atk = [ballot("bd","D","D"), ballot("be","E","D"), ballot("bdv","D","ABCD"), elect("e1y","D",("bd","be","bdv"),K5)]
ak = CK.row("ak", "ack", "R", ("e2",), room="g", head=("e2",))
show("A4a reader R acknowledged e2", [G5, LM] + e1rows + e2rows + atk + [ak], K5, own="R")
show("A4b reader that acknowledged nothing", [G5, LM] + e1rows + e2rows + atk + [ak], K5)
# attacker's fork at the newest head it may use without e2 in its past: wb
atk2 = [ballot("bd","D","D",("wb",)), ballot("be","E","D",("wb",)), ballot("bdv","D","ABCD",("wb",)), elect("e1y","D",("bd","be","bdv"),K5,heads=("wb",))]
show("A4c fork at wb, reader acked e2", [G5, LM] + e1rows + e2rows + atk2 + [ak], K5, own="R")
# A1 with a reader who acknowledged the honest seating
ax = admit("ax", "F", ("A", "B", "C", "D"), ("lm",))
bal = [ballot("ba","A","F",("ax",)), ballot("bb","B","F",("ax",)), ballot("bc","C","F",("ax",)), ballot("bd","D","C",("ax",)), ballot("be","E","C",("ax",))]
ids = tuple(b["id"] for b in bal)
ef = elect("ef", "F", ids, "ABCDEF", heads=("ax",)); ecl = elect("ec", "C", ids, "ABCDEF", heads=("lm",))
ak2 = CK.row("ak2", "ack", "R", ("ef",), room="g", head=("ef",))
show("A1d reader acked ef", [G5, LM, ax] + bal + [ef, ecl, ak2], "ABCDEF", own="R")
# A1e: C's seating at head ax-free but the honest one acked only 'ax' (the head both could see)
ak3 = CK.row("ak3", "ack", "R", ("ax",), room="g", head=("ax",))
show("A1e reader acked ax (the admission)", [G5, LM, ax] + bal + [ef, ecl, ak3], "ABCDEF", own="R")
