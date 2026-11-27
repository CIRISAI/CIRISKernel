exec(open(__file__.replace("dbg2.py","lib.py")).read())
N=5; V=("L'",)
ACKS = [ack("k"+k, k, "aG") for k in "ABCDEFG"]
Q=[]; mm=["A","B"]; pv="g"
for i in range(1,9): k="X%d"%i; Q.append(admit("p%d"%i,k,tuple(mm),(pv,))); mm.append(k); pv="p%d"%i
run("Q", ROOM+Q, ids=("p1","p7","p8"), n=N, vars=V)
run("Q+ACKS", ROOM+ACKS+Q, ids=("p1","p7","p8"), n=N, vars=V)
run("Q+ah", ROOM+Q+[admit("ah","H",tuple("ABCDEFG"),("aG",),("p8",))], ids=("p1","p7","p8","ah"), n=N, vars=V)
run("Q+kA", ROOM+Q+ACKS[:1], ids=("p1","p7","p8"), n=N, vars=V)
