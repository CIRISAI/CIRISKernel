exec(open(__file__.replace("ad.py","lib.py")).read())

XG = remove("xg","G",FIVE,("aG",))
AX = admit("ax","X",("A","B"),("g",))
run("Ad1 rescue: five remove G at aG; A,B admit X from {g} concurrently", ROOM+[XG,AX], ids=("xg","ax"))
AH = admit("ah","H",("A","B","C","D","E","F","G"),("aG",))
run("Ad2 five remove G at aG; seven admit H at aG concurrently", ROOM+[XG,AH], ids=("xg","ah"))
# flip: removal of G written from aF (G not yet seated there), concurrent with aG
XGF = remove("xg","G",FIVE,("aF",))
run("Ad3 five remove G at aF (concurrent with aG)", ROOM+[XGF], ids=("xg",))
M = admit("ah","H",FIVE,("aG","xg"))
run("Ad4 Ad3 + five admit H heads (aG,xg): one tip", ROOM+[XGF,M], ids=("xg","ah"))
