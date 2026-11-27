import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G5, LM = E.G5, E.LM
K5 = "ABCDE"
e1rows = [ballot("ba","A","B"), ballot("bb","B","B"), elect("e1","B",("ba","bb"),K5), ST.withdraw("wb","B","e1",("e1",))]
e2rows = [ballot("ba2","A","C",("wb",),of="e1"), ballot("bc2","C","C",("wb",),of="e1"),
          elect("e2","C",("ba2","bc2"),K5,heads=("wb",),of="e1")]
# C sits. D and E start "the next election" (of e2) while C still holds, the seating naming an old head (wb)
y = [ballot("bd","D","D",("e2",),of="e2"), ballot("be","E","D",("e2",),of="e2"), elect("y","D",("bd","be"),K5,heads=("wb",),of="e2")]
show("A7a election beside a sitting moderator, seating at an old head", [G5, LM] + e1rows + e2rows + y, K5)
y2 = [ballot("bd","D","D",("e2",),of="e2"), ballot("be","E","D",("e2",),of="e2"), elect("y","D",("bd","be"),K5,heads=("e2",),of="e2")]
show("A7b same at head e2 (control)", [G5, LM] + e1rows + e2rows + y2, K5)
ak = CK.row("ak", "ack", "R", ("e2",), room="g", head=("e2",))
show("A7c A7a for a reader who acked e2", [G5, LM] + e1rows + e2rows + [ak] + y, K5, own="R")
# and in the founding election directly: G5 founded with A moderator, never laid down; seating at head g? (A's duty live)
