exec(open(__file__.replace("g2.py","lib.py")).read())
H5 = ("h1","h2","h3","h4","h5")
L = [B0, nxt("b1","b0",H5,("h1","h2")), nxt("b2","b1",("h3","h4","h5"),("h3","h4","h5"),version=2)]
rd = RD(anchor="b0", acks=("b2",))
G = (GR("B1","b0","f4","g",("h1","h2")),)
rows = CR.STALLED + [CR.RCV()]
got = CR.recovery_answer(rows, L, G, rd)
print("G4 stalled infra room: f4 widens itself on a grant by removed holders h1,h2 naming b0; reader at b2 ->", got)
# order-freedom of the seat rows
import random
rnd = random.Random(7); d = 0
for _ in range(60):
    t = rows[1:]; rnd.shuffle(t)
    if CR.recovery_answer([rows[0]] + t, L, G, rd) != got: d += 1
print("   orders differing %d/60" % d)
print("G4 control, grant by h3,h4 naming b2 ->", CR.recovery_answer(rows, L, (GR("B1","b2","f4","g",("h3","h4")),), rd))
print("G4 control, grant by h1,h2 naming b2 ->", CR.recovery_answer(rows, L, (GR("B1","b2","f4","g",("h1","h2")),), rd))
