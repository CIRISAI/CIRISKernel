import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G6 = room(6); K6 = "ABCDEF"
s2r = [ballot("ba","A","B"), ballot("bb","B","B"), elect("s2","B",("ba","bb"))]
s1r = [ballot("bc","C","C"), ballot("bd","D","C"), ballot("be","E","C"), ballot("bf","F","C"), elect("s1","C",("bc","bd","be","bf"))]
cl = [ack("kd","D","s1",("bd",)), ack("ke","E","s1",("be",)), ack("kf","F","s1",("bf",))]      # 3 of {A,B,D,E,F}: closed
base = [G6, LM] + s2r + s1r + cl
show("H1a s1 closed (D, E, F of base 5); s2 a non-nested rival", base, K6)
lf = leave("lf", "F", "g", ("kf",))                                       # F leaves the room, after its receipt
show("H1b F, a needed receipter, leaves afterwards", base + [lf], K6)
# a next election after C resigns, closed in its own right
nx = [ST.withdraw("wc","C","s1",("kd","ke","kf")), ballot("n1","A","A",("wc",),of="s1"), ballot("n2","D","A",("wc",),of="s1"),
      elect("en","A",("n1","n2"),of="s1",vac=("wc",))]
show("H1c the chain: C resigns, A elected next (named on s1)", base + nx, K6)
show("H1d the same chain, then F leaves", base + nx + [ST.withdraw("lf","F","g",("en",))], K6)
