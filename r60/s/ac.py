exec(open(__file__.replace("ac.py","lib.py")).read())
FIVE = CH.FIVE
run("AC1 five of seven remove G heads (g,aG) (not an antichain)", ROOM + [remove("xg","G",FIVE,("g","aG"))], ids=("xg",))
run("AC2 five of seven remove G heads (aD,aG)", ROOM + [remove("xg","G",FIVE,("aD","aG"))], ids=("xg",))
run("AC3 A,B remove G heads (g,aG)", ROOM + [remove("xg","G",("A","B"),("g","aG"))], ids=("xg",))
run("AC4 A,B remove G head (g) naming aG", ROOM + [remove("xg","G",("A","B"),("g",),("aG",))], ids=("xg",))
run("AC5 five remove G head (aF) naming aG", ROOM + [remove("xg","G",FIVE,("aF",),("aG",))], ids=("xg",))
# community_invite with the newcomer's yes missing, as a tip
ax = ST.offer("ax","A","X","member",OBJ,"group",("g",),head=("g",),policy="community_invite",cosigners=("B",))
run("CC1 A,B invite X at g, X's yes missing", ROOM + [ax], ids=("ax",))
run("CC1b used as a tip: A,B remove G heads (ax,aG)", ROOM + [ax, remove("xg","G",("A","B"),("ax","aG"))], ids=("ax","xg"))
# one key conferral by a non-lone holder (B, not a holder) conf self
sb = ST.offer("sb","B","C","moderate",OBJ,"self",("g",))
run("CC2 B (no holder) self-confers moderate on C at g; then used as tip", ROOM + [sb, remove("xg","G",("A","B"),("sb","aG"))], ids=("sb","xg"))
# self-admission outside open protocol as tip
sa = CH.SA("sz","Z",("g",))
run("CC3 Z self-admits (room not open) as tip", ROOM + [sa, remove("xg","G",("A","B"),("sz","aG"))], ids=("sz","xg"))
# a lone removal / unseat with conf group that does not conclude used as head
