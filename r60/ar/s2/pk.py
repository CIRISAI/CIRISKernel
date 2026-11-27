exec(open(__file__.replace("pk.py","lib.py")).read())
V=("today","L'","L's")
for n in (6,7):
    Q=[]; mm=["A","B"]; pv="g"
    for i in range(1,n+1): k="X%d"%i; Q.append(admit("p%d"%i,k,tuple(mm),(pv,))); mm.append(k); pv="p%d"%i
    run("Pk A,B chain %d admissions from {g}, nothing else" % n, ROOM+Q, ids=("aD","aG","p1","p%d"%n), n=60, vars=V)
    run("Pk' same, reader R acked aG", ROOM+[ack("ak","R","aG")]+Q, own="R", ids=("aD","aG","p1","p%d"%n), n=20, vars=V)
G1 = ST.found("g","A",("A",),{}); solo=[G1]; m=["A"]; pv="g"
for k in "BCDEFG": solo.append(admit("a"+k,k,tuple(m),(pv,))); m.append(k); pv="a"+k
for n in (2,3,4):
    Q=[]; mm=["A"]; pv="g"
    for i in range(1,n+1): k="X%d"%i; Q.append(admit("p%d"%i,k,tuple(mm),(pv,))); mm.append(k); pv="p%d"%i
    run("Ps solo room of seven; A chains %d admissions from {g}" % n, solo+Q, ids=("aB","aG","p1","p%d"%n), n=20, vars=V)
