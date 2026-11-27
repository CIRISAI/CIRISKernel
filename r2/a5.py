import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G5, LM = E.G5, E.LM
K5 = "ABCDE"
# two seatings of the founding election over the same set: both stand (B)
base = [ballot("ba","A","B"), ballot("bb","B","B"), elect("e1","B",("ba","bb"),K5),
        elect("e2","B",("ba","bb"),K5)]
show("A5a two seatings over one set", [G5, LM] + base, K5)
# B lays down each seat on its own branch
w1 = ST.withdraw("w1","B","e1",("e1",)); w2 = ST.withdraw("w2","B","e2",("e2",))
x = [ballot("bc1","C","C",("w1",),of="e1"), ballot("bd1","D","C",("w1",),of="e1"), elect("x","C",("bc1","bd1"),K5,heads=("w1",),of="e1")]
y = [ballot("bd2","D","D",("w2",),of="e2"), ballot("be2","E","D",("w2",),of="e2"), elect("y","D",("bd2","be2"),K5,heads=("w2",),of="e2")]
show("A5b two next elections, one per id row", [G5, LM] + base + [w1, w2] + x + y, K5)
ax = admit("ax","X",("A","B","C","D"),("x","y"))
show("A5c then an admission citing both", [G5, LM] + base + [w1, w2] + x + y + [ax], K5+"X")
