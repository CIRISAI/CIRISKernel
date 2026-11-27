exec(open(__file__.replace("ah.py","lib.py")).read())
# (h) packing: A,B admit sybils from the old past {g}, chained (each at the one before), then act with them
P = []; prev = "g"; mem = ["A","B"]
for i in range(1, 9):
    k = "X%d" % i; P.append(admit("p%d" % i, k, tuple(mem), (prev,))); mem.append(k); prev = "p%d" % i
SYB = tuple(mem)                                  # A,B,X1..X8: 10 keys
run("Ah1 A,B admit X1 from {g}", ROOM+P[:1], ids=("p1",))
run("Ah2 A,B admit X1..X8 chained from {g}", ROOM+P, ids=tuple(p["id"] for p in P))
XD = remove("xd","D",SYB,("aG","p8"))
run("Ah3 Ah2 + A,B,X1..X8 remove D heads (aG,p8)", ROOM+P+[XD], ids=("p8","xd"))
XDs = [remove("x"+k,k,SYB,(("aG","p8") if k=="D" else ("x"+prevk,))) for k, prevk in zip("DEFGC", "?DEFG")]
run("Ah4 ... then remove E,F,G,C each chained", ROOM+P+XDs, ids=tuple(x["id"] for x in XDs))
H5 = admit("ah","H",FIVE,("aG","p8"))
run("Ah5 Ah2 + honest five admit H heads (aG,p8)", ROOM+P+[H5], ids=("ah",))
H7 = admit("ah","H",tuple("ABCDEFG"),("aG","p8"))
run("Ah6 Ah2 + all seven admit H heads (aG,p8)", ROOM+P+[H7], ids=("ah",))
run("Ah7 Ah3 for reader R acked aG", ROOM+[ack("ak","R","aG")]+P+[XD], own="R", ids=("p8","xd"))
