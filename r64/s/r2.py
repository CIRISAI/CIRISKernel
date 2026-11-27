exec(open(__file__.replace("r2.py","lib.py")).read())
P0 = []; pv = ("g",)
for i in range(1, 4):
    P0.append(admit("p%d" % i, "X%d" % i, ("A","B") + tuple("X%d" % j for j in range(1, i)), pv)); pv = ("p%d" % i,)
XD = remove("xD","D",("A","B","X1","X2","X3"),("aG","p3"))
rows = ROOM + P0 + [XD]
for own in (None, "X1", "K", "F"):
    extra = [ack("k","K","p2")] if own == "K" else []
    run("Q2 A,B pack X1..X3 (void, no rescuer); A,B,X1..X3 remove D at (aG,p3); reader %s" % own, rows + extra, own=own, ids=("p3","xD"))
# honest reader F acks aG; later the honest line is tied void? reader F after Hh2-like tie (room of one)
G1 = ST.found("g","A",("A",),{})
rs = [G1]; mem = ["A"]; prev = "g"
for k in "BCDEFG":
    rs.append(admit("a"+k,k,tuple(mem),(prev,))); mem.append(k); prev = "a"+k
P = []; m = ["A"]; pvv = "g"
for i in range(1, 13):
    k = "X%d" % i; P.append(admit("q%d" % i, k, tuple(m), (pvv,))); m.append(k); pvv = "q%d" % i
XB = remove("xb","B",tuple(m),("aG",pvv))
for own in (None, "B", "F", "X5"):
    run("Q3 room of one grown to seven; A packs X1..X12 (tie kept); remove B; reader %s" % own, rs + P + [XB], own=own, ids=("xb",), n=20)
