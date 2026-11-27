exec(open(__file__.replace("aa.py","lib.py")).read())
# (a) the removal arm: A,B remove G with only g in their past (head g), concurrent with aD..aG
XG = remove("xg","G",("A","B"),("g",))
run("Aa1 A,B remove G, past {g}, head g", ROOM+[XG], ids=("xg",))
H5 = admit("ah","H",FIVE,("xg","aG"))
run("Aa2 + honest five admit H heads (xg,aG)", ROOM+[XG,H5], ids=("xg","ah"))
H5b = admit("ah","H",tuple("ABCDEF"),("xg","aG"))
run("Aa3 + honest six (ABCDEF) admit H heads (xg,aG)", ROOM+[XG,H5b], ids=("xg","ah"))
# chain: remove G,F,E,D each by A,B at head g (each its own tip), or chained on the previous removal
XS = [remove("x"+k,k,("A","B"),("g",)) for k in "GFED"]
run("Aa4 A,B remove G,F,E,D, each past {g}", ROOM+XS, ids=tuple("x"+k for k in "GFED"))
XC = []; prev="g"
for k in "GFED":
    XC.append(remove("x"+k,k,("A","B"),(prev,))); prev="x"+k
run("Aa5 chained: A,B remove G at g, F at xG, E at xF, D at xE", ROOM+XC, ids=tuple("x"+k for k in "GFED"))
AXC = admit("ax","X",("A","B"),("aG","xD"))
run("Aa6 Aa5 + A,B admit X heads (aG,xD)", ROOM+XC+[AXC], ids=tuple("x"+k for k in "GFED")+("ax",))
XCc = remove("xc","C",("A","B"),("aG","xD"))
run("Aa7 Aa5 + A,B remove C heads (aG,xD)", ROOM+XC+[XCc], ids=tuple("x"+k for k in "GFED")+("xc",))
# honest response under sym: D..G and C re-admit? honest 5 at heads (aG,xD)
H5c = remove("xz","Z",FIVE,("aG","xD"))
run("Aa8 Aa5 + honest five remove outsider-less key Z heads (aG,xD) (any honest count)", ROOM+XC+[H5c], ids=("xz",))
