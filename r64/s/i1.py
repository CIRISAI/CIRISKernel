exec(open(__file__.replace("i1.py","lib.py")).read())
# y: A "self-admits" (policy open:self_admit, to=[A]) at the founding head g, with aG in its past. Room is NOT self-admit.
Y = ST.offer("y", "A", "A", "member", OBJ, "group", ("aG",), head=("g",), policy="open:self_admit")
run("I1 control: A,B remove G, head g, names aG", ROOM + [remove("xg","G",("A","B"),("g",),("aG",))], ids=("xg",))
run("I1 A,B remove G, head y (authored, heads g), aG in past", ROOM + [Y, remove("xg","G",("A","B"),("y",))], ids=("y","xg"))
run("I1b A,B admit X, head y", ROOM + [Y, admit("ax","X",("A","B"),("y",))], ids=("y","ax"))
run("I1c reader R acked aG; A,B remove G head y", ROOM + [ack("ak","R","aG"), Y, remove("xg","G",("A","B"),("y",))], own="R", ids=("y","xg"))
run("I1d recall of A by B,C head y", ROOM + [Y, CH.RC(("y",),("B","C"))], ids=("y","rc"), scopes=("moderate",))
# y signed by an outsider Z (not a member at all)
Z = ST.offer("y", "Z", "Z", "member", OBJ, "group", ("aG",), head=("g",), policy="open:self_admit")
run("I1e outsider Z's self-admit as head; A,B remove G", ROOM + [Z, remove("xg","G",("A","B"),("y",))], ids=("y","xg"))
# single founder? A alone with head y where y heads g - A,B needed. Try A alone removing D,E,F,G via y whose head is aD? no: fine.
