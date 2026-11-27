exec(open(__file__.replace("ah2.py","lib.py")).read())
G1 = ST.found("g","A",("A",),{})
rows = [G1]; mem = ["A"]; prev = "g"
for k in "BCDEFG":
    rows.append(admit("a"+k,k,tuple(mem),(prev,))); mem.append(k); prev = "a"+k
run("Hh0 room founded by A alone, grown to seven", rows)
X1 = admit("p1","X1",("A",),("g",))
run("Hh1 A alone admits X1 from {g}", rows+[X1], ids=("p1",))
P = []; m = ["A"]; pv = "g"
for i in range(1, 13):
    k = "X%d" % i; P.append(admit("p%d" % i, k, tuple(m), (pv,))); m.append(k); pv = "p%d" % i
XB = remove("xb","B",tuple(m),("aG",pv))
run("Hh2 A alone admits X1..X12 chained from {g}; A,X1..X12 remove B heads (aG,p12)", rows+P+[XB], ids=("p12","xb"))
