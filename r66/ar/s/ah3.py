exec(open(__file__.replace("ah3.py","lib.py")).read())
G1 = ST.found("g","A",("A",),{})
rows = [G1]; mem = ["A"]; prev = "g"
for k in "BCDEFG":
    rows.append(admit("a"+k,k,tuple(mem),(prev,))); mem.append(k); prev = "a"+k
P = []; m = ["A"]; pv = "g"
for i in range(1, 13):
    k = "X%d" % i; P.append(admit("p%d" % i, k, tuple(m), (pv,))); m.append(k); pv = "p%d" % i
XB = remove("xb","B",tuple(m),("aG",pv))
run("Hh3 Hh2 for reader R acked aG", rows+[ack("ak","R","aG")]+P+[XB], own="R", ids=("p12","xb"), n=20)
H = admit("ah","H",tuple("ABCDEFG"),("aG",pv))
run("Hh4 A packs X1..X12; all seven admit H heads (aG,p12)", rows+P+[H], ids=("ah",), n=20)
