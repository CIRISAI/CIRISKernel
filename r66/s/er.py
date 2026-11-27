exec(open(__file__.replace("er.py","lib.py")).read())
G = CH.G
aD = admit("aD","D",("A","B","C"),("g",))
aE = admit("aE","E",("A","B","C","D"),("aD",))
aF = admit("aF","F",("A","B","C","D","E"),("aE",))
aG = admit("aG","G",("A","B","C","D","E","F"),("aF",))
xs = admit("xs","S",("A","B","C","D","E","F","G"),("aG",))
base = [G, aD, aE, aF, aG, xs]
c1 = admit("c1","X",("A","B","C","D"),("aD",))
c2 = admit("c2","Y",("A","B","C","D","X"),("c1",))
run("ER0 control", base, ids=("aE","aF","aG","xs"))
for own in (None, "G", "E", "S", "Q"):
    run("ER1 A,B,C,D backdate c1 (at aD), c2 (at c1); reader %s" % own, base + [c1, c2], own=own, ids=("aE","aF","aG","xs","c1","c2"))
# can the erased side still count? E,F,G,S + A..D ... honest seven remove X heads (xs, c2)
rx = remove("rx","X",("A","B","C","D","E","F","G","S"),("xs","c2"))
run("ER2 + everyone remove X heads (xs,c2)", base + [c1, c2, rx], ids=("rx",))
# E,F,G,S alone (the later members) remove A
ra = remove("ra","A",("E","F","G","S","B"),("xs",),("c2",))
run("ER3 + E,F,G,S,B remove A head xs citing c2", base + [c1, c2, ra], ids=("ra",))
