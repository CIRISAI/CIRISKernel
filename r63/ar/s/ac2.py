exec(open(__file__.replace("ac2.py","lib.py")).read())
GO = dict(ST.found("g","A",("A","B","C"),{"moderate":("A",)},cosigners=("B","C")), open=True)
SA = [ST.offer("sD","D","D","member",OBJ,"group",("g",),head=("g",),policy="open:self_admit"),
      ST.offer("sE","E","E","member",OBJ,"group",("sD",),head=("sD",),policy="open:self_admit")]
AX0 = admit("ax","X",("A","B"),("g",))
XD = remove("xd","D",("A","B","X"),("sE","ax"))
run("Ab2 open room: D,E self-admit; A,B admit X from {g}; A,B,X remove D heads (sE,ax)", [GO]+SA+[AX0,XD], ids=("sD","sE","ax","xd"))
# (c) policy-differing tips: a counted record change by A,B from {g} carrying regime r2
RC = dict(ST.offer("pc","A","B","review",OBJ,"group",("g",),head=("g",),policy="community_invite",cosigners=("B",)), regime="r2")
run("Cc1 A,B regime change from {g}", ROOM+[RC], ids=("pc",))
XD2 = remove("xd","D",("A","B"),("aG","pc"))
run("Cc2 + A,B remove D heads (aG,pc)", ROOM+[RC,XD2], ids=("pc","xd"))
H5 = admit("ah","H",FIVE,("aG","pc"))
run("Cc3 + honest five admit H heads (aG,pc)", ROOM+[RC,H5], ids=("pc","ah"))
run("Cc4 Cc2 for reader R acked aG", ROOM+[ack("ak","R","aG"),RC,XD2], own="R", ids=("pc","xd"))
# (e) a cosignature that is its own row with a newer head in its past
AH = admit("aH","H",tuple("ABCDEFG"),("aG",))
CS = ST.cosign("cs","C",("xs"),("aG","aH"))
XS = ST.unseat("xs","A","G","member",OBJ,"group",("aG","cs"),head=("aG",),policy="community_remove",cosigners=("B","D","E"))
run("Ee1 removal at aG with a cosign whose past holds aH", ROOM+[AH,CS,XS], ids=("aH","xs"))
XS2 = ST.unseat("xs","A","G","member",OBJ,"group",("aG",),head=("aG",),policy="community_remove",cosigners=("B","D","E"))
CS2 = ST.cosign("cs","C","xs",("xs","aH"))
run("Ee2 four sign at aG; C cosigns afterwards having seen aH (cosign not named)", ROOM+[AH,XS2,CS2], ids=("aH","xs"))
