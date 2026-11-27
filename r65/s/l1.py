exec(open(__file__.replace("l1.py","lib.py")).read())
WM = CH.WM
# the room grows: P,Q,S admitted after N (members m1 m2 MOD N P Q S)
grow = [admit("aP","P",("m1","m2","MOD","N"),("an",)), admit("aQ","Q",("m1","m2","MOD","N","P"),("aP",)), admit("aS","S",("m1","m2","MOD","N","P","Q"),("aQ",))]
XC = ST.unseat("xc","m1","AG","agent",OBJ,"group",("aS",),head=("aS",),policy="community_remove",cosigners=("m2","MOD","N","P","Q","S"))
XL = ST.unseat("xl","MOD","AG","agent",OBJ,"group",("xc",),head=("md",),policy="community_remove")
o1 = CK.row("o1","answer","m1",("xl",),of="xl",says="object"); o2 = CK.row("o2","answer","m2",("xl",),of="xl",says="object")
LF = ST.offer("lf","m1","AG","agent",OBJ,"group",("xl","o1","o2"),head=("md",),content="xl",policy="moderation_overturn",cosigners=("m2",))
base = WM + grow + [XC]
run("L0 control: AG removed by the count of seven", base, ids=("xc",), scopes=("member","agent"))
run("L1 + MOD lone removal at md (xc in its past) + m1,m2 lift at md", base + [XL,o1,o2,LF], ids=("xc","xl","lf"), scopes=("member","agent"))
run("L1r same, reader R acked aS", base + [ack("ak","R","aS"), XL,o1,o2,LF], own="R", ids=("xc","xl","lf"), scopes=("member","agent"))
run("L1x same, reader R acked xc", base + [ack("ak","R","xc"), XL,o1,o2,LF], own="R", ids=("xc","xl","lf"), scopes=("member","agent"))
# a key that never held an agent seat: K was a member; lone removal requires agent seat at head -> expect no
XLK = ST.unseat("xk","MOD","N","agent",OBJ,"group",("aS",),head=("an",),policy="community_remove")
run("L2 lone removal of N (a person) as agent", WM + grow + [XLK], ids=("xk",), scopes=("member","agent"))
