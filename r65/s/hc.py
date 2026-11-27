exec(open(__file__.replace("hc.py","lib.py")).read())
G = CH.G
aD = admit("aD","D",("A","B","C"),("g",))
aE = admit("aE","E",("A","B","C","D"),("aD",))           # honest admission of E
c1 = admit("c1","H",("A","B","C","D"),("aD",))           # concurrently, the same four admit H (another device)
c2 = admit("c2","J",("A","B","C","D","H"),("c1",))       # and then J, not yet having seen aE
base = [G, aD, aE, c1, c2]
for own in (None, "E", "D", "Q"):
    run("HC1 honest concurrency: aE beside c1->c2 by the same voices; reader %s" % own, base, own=own, ids=("aE","c1","c2"))
m = admit("m","K",("A","B","C","D","E","H","J"),("aE","c2"))
run("HC2 + an honest merge admitting K heads (aE,c2)", base + [m], ids=("aE","c2","m"))
c2b = admit("c2","J",("A","B","C","H"),("c1",))          # D did not sign c2 (4 of 5, 2/3 met)
run("HC3 same but D did not sign c2", [G, aD, aE, c1, c2b], ids=("aE","c1","c2"))
