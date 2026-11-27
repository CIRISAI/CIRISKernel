exec(open(__file__.replace("rr2.py","lib.py")).read())
H = lambda cites, heads=("aG",): admit("ah","H",FIVE,heads,cites)
M = {"P1a": remove("xg","G",("A","B"),("g",),("aG",)), "P1b": admit("ax","X",("A","B"),("g",),("aG",)),
     "A1": remove("xg","G",("A","B"),("g","aG")), "A1b": admit("ax","X",("A","B"),("g","aG"))}
for n, r in M.items():
    run("%s + honest five admit H head aG naming it" % n, ROOM+[r, H((r["id"],))], ids=(r["id"],"ah"))
X = ack("x","Z","g"); Y = ST.offer("y","Z","Z","member",OBJ,"group",("x","aG"),head=("x",),over="x",policy="open:self_admit")
run("I3 + honest five admit H head aG naming y", ROOM+[X,Y,H(("y",))], ids=("y","ah"))
Z0 = ST.offer("z","Z","Z","member",OBJ,"group",("g",),head=("g",),policy="open:self_admit")
run("I2b + honest five admit H heads (z,aG)", ROOM+[Z0,H((),("z","aG"))], ids=("z","ah"))
DC0 = ST.offer("dc","A","B","moderate",OBJ,"group",("g",),head=("g",),policy="duty_confer",counted="duty",cosigners=("B",))
run("T1a dc + honest five admit H heads (dc,aG)", ROOM+[DC0,H((),("dc","aG"))], ids=("dc","ah"))
