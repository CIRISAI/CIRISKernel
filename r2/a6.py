import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G5, LM = E.G5, E.LM
K5 = "ABCDE"
e1rows = [ballot("ba","A","B"), ballot("bb","B","B"), elect("e1","B",("ba","bb"),K5), ST.withdraw("wb","B","e1",("e1",))]
e2rows = [ballot("ba2","A","C",("wb",),of="e1"), ballot("bc2","C","C",("wb",),of="e1"),
          elect("e2","C",("ba2","bc2"),K5,heads=("wb",),of="e1")]
ak = CK.row("ak", "ack", "R", ("e2",), room="g", head=("e2",))
# D, E: a tying rival in election 2 (concurrent with e2), then a seating of the FOUNDING election that has e2 in its past
x = [ballot("bd2","D","D",("wb",),of="e1"), ballot("be2","E","D",("wb",),of="e1"),
     elect("e2x","D",("bd2","be2"),K5,heads=("wb",),of="e1")]
y = [ballot("bd","D","D",("e2","e2x")), ballot("be","E","D",("e2","e2x")), ballot("bdv","D","ABCD",("e2","e2x")),
     elect("e1y","D",("bd","be","bdv"),K5,heads=("wb",))]
rows = [G5, LM] + e1rows + e2rows + [ak] + x + y
show("A6a reader R acked e2; e1y descends from e2", rows, K5, own="R")
show("A6b no reader line", rows, K5)
