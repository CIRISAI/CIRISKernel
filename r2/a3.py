import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G5, LM = E.G5, E.LM
K5 = "ABCDE"
e1rows = [ballot("ba","A","B"), ballot("bb","B","B"), elect("e1","B",("ba","bb"),K5),
          ST.withdraw("wb","B","e1",("e1",))]
e2rows = [ballot("ba2","A","C",("wb",),of="e1"), ballot("bb2","B","C",("wb",),of="e1"), ballot("bc2","C","C",("wb",),of="e1"),
          elect("e2","C",("ba2","bb2","bc2"),K5,heads=("wb",),of="e1")]
show("A3a honest: election 1 seats B, B resigns, election 2 seats C", [G5, LM] + e1rows + e2rows, K5)
# two colluders D, E fork from lm (never citing e1 or anything after), ballots of the founding election
atk = [ballot("bd","D","D"), ballot("be","E","D")]
e1x = elect("e1x","D",("bd","be"),K5)
show("A3b D,E: equal-size different set of the OLD election (tie): e1 and, transitively, e2 die", [G5, LM] + e1rows + e2rows + atk + [e1x], K5)
pad = [ballot("bdv","D","ABCD")]     # void (ranks four) but 'valid' for size
e1y = elect("e1y","D",("bd","be","bdv"),K5)
show("A3c plus one void ballot of D's: (2,3) beats e1 (2,2): D seated, C unseated", [G5, LM] + e1rows + e2rows + atk + pad + [e1y], K5)
# a later admission citing everything (a reader who has all rows)
ax = admit("ax","X",("A","B","C","D"),("e2","e1y"))
show("A3d with a member's admission citing e2 and e1y (the attack's rows heard everywhere)", [G5, LM] + e1rows + e2rows + atk + pad + [e1y, ax], K5+"X")
