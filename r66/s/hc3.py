exec(open(__file__.replace("hc3.py","lib.py")).read())
G = CH.G
aD = admit("aD","D",("A","B","C"),("g",)); aE = admit("aE","E",("A","B","C"),("aD",))
aK = admit("aK","K",("A","B","C","E"),("aE",))           # 4 of 5 at aE: E's voice counted
xD = remove("xD","D",("A","B","C","E","K"),("aK",))      # 5 of 6: D removed, counting E and K
c1 = admit("c1","H",("A","B","C"),("aD",)); c2 = admit("c2","J",("A","B","C","H"),("c1",))
run("HC6 control: aK, xD, no backdating", [G, aD, aE, aK, xD], ids=("aE","aK","xD"))
for own in (None, "E", "K", "D"):
    run("HC6 + A,B,C backdate c1, c2 later; reader %s" % own, [G, aD, aE, aK, xD, c1, c2], own=own, ids=("aE","aK","xD","c1","c2"))
