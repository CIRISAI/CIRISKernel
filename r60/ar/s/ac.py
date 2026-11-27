exec(open(__file__.replace("ac.py","lib.py")).read())
# minimal sym-past break: four separate old-past removals, then A,B remove C naming all five tips
XS = [remove("x"+k,k,("A","B"),("g",)) for k in "GFED"]
XC = remove("xc","C",("A","B"),("aG",)+tuple(x["id"] for x in XS))
run("Ac1 A,B remove D..G each from {g} (4 tips), then remove C naming all tips", ROOM+XS+[XC], ids=tuple(x["id"] for x in XS)+("xc",))
# honest concurrent admissions (sym3 non-monotone?)
H = admit("ah","H",FIVE,("aG",)); J = admit("aj","J",("C","D","E","F","G"),("aG",))
run("Ac2 two honest concurrent admissions by five each at aG", ROOM+[H,J], ids=("ah","aj"))
H2 = admit("ah","H",tuple("ABCDEFG"),("aG",)); J2 = admit("aj","J",tuple("ABCDEFG"),("aG",))
run("Ac3 two concurrent unanimous admissions at aG", ROOM+[H2,J2], ids=("ah","aj"))
M = remove("m","G",FIVE,("ah","aj"))
run("Ac4 Ac2 + five remove G heads (ah,aj)", ROOM+[H,J,M], ids=("ah","aj","m"))
