exec(open(__file__.replace("t1.py","lib.py")).read()); FIVE=CH.FIVE
# a tip made cheaply at the founding head, concurrent with aD..aG
DC0 = ST.offer("dc", "A", "B", "moderate", OBJ, "group", ("g",), head=("g",), policy="duty_confer", counted="duty", cosigners=("B",))
AX0 = admit("ax", "X", ("A","B"), ("g",))
run("T1a tip dc (A's lone conferral at g); A,B remove G heads (dc,aG)", ROOM + [DC0, remove("xg","G",("A","B"),("dc","aG"))], ids=("dc","xg"))
run("T1b tip ax (A,B admit X at g); A,B remove G heads (ax,aG)", ROOM + [AX0, remove("xg","G",("A","B"),("ax","aG"))], ids=("ax","xg"))
run("T1c same as T1a, reader R acked aG", ROOM + [ack("ak","R","aG"), DC0, remove("xg","G",("A","B"),("dc","aG"))], own="R", ids=("dc","xg"))
run("T1d tip dc; A,B admit W heads (dc,aG)", ROOM + [DC0, admit("aw","W",("A","B"),("dc","aG"))], ids=("dc","aw"))
run("T1e tip dc; A,B,C remove D,E? remove E heads (dc,aG)", ROOM + [DC0, remove("xe","E",("A","B"),("dc","aG"))], ids=("dc","xe"))
run("T1f control: only dc tip, no r", ROOM + [DC0], ids=("dc",), scopes=("member","moderate"))
run("T1g honest: five of seven remove G heads (aG) while dc tip exists, naming dc too", ROOM + [DC0, remove("xg","G",FIVE,("aG",),("dc",))], ids=("dc","xg"))
