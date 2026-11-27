exec(open(__file__.replace("hc2.py","lib.py")).read())
G = CH.G
aD = admit("aD","D",("A","B","C"),("g",))
aE = admit("aE","E",("A","B","C"),("aD",))               # 3 of 4 admit E (E's yes)
xE = remove("xE","E",("A","B","C"),("aE",))
run("HC4 control: A,B,C remove E by count at aE (3 of 5)", [G, aD, aE, xE], ids=("xE",))
c1 = admit("c1","H",("A","B","C"),("aD",))
c2 = admit("c2","J",("A","B","C","H"),("c1",))
for own in (None, "E", "D"):
    run("HC4 A,B,C write c1 (at aD), c2 (at c1) without aE; reader %s" % own, [G, aD, aE, c1, c2], own=own, ids=("aE","c1","c2"))
# D builds on aE first (D voices a change with aE in past): rescue?
aK = admit("aK","K",("A","D","E"),("aE",))
run("HC5 + D,E,A admit K at aE (fails count?)", [G, aD, aE, aK], ids=("aK",))
