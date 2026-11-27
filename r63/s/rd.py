exec(open(__file__.replace("rd.py","lib.py")).read())
G = CH.G
aD = admit("aD","D",("A","B","C"),("g",)); aE = admit("aE","E",("A","B","C","D"),("aD",))
aF = admit("aF","F",("A","B","C","E"),("aE",)); aG = admit("aG","G",("A","B","C","E","F"),("aF",))
base = [G, aD, aE, aF, aG]
f = remove("f","E",("A","B","C"),("aD",))
for own in (None, "D", "G", "E", "Q"):
    run("RD fork: A,B,C remove E at head aD (sibling of aE); reader %s" % own, base + [f], own=own, ids=("f",))
# then honest count by the five at aG admitting H, with f in its past?
ah = admit("ah","H",("A","B","C","E","F","G"),("aG",),("f",))
for own in (None, "D", "G"):
    run("RD2 + honest six admit H head aG citing f; reader %s" % own, base + [f, ah], own=own, ids=("f","ah"))
