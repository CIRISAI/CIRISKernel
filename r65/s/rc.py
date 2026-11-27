exec(open(__file__.replace("rc.py","lib.py")).read())
G = ST.found("g","A",("A","B","C"),{"moderate":("A",)},cosigners=("B","C"))
aD = admit("aD","D",("A","B","C"),("g",))
aF = admit("aF","F",("A","B","C","D"),("aD",))
aG = admit("aG","G",("A","B","C","D","F"),("aF",))        # members at aG: A B C D F G (6)
aE = admit("aE","E",("A","B","C","D"),("aG",))           # 4 of 6 admit E
post = CK.row("fp","post","F",("aG",),room=OBJ)          # F posts, concurrently with aE (has not seen it)
xE = remove("xE","E",("A","B","C","D"),("aE",))
base = [G, aD, aF, aG, aE]
run("RC0 control: A,B,C,D remove E by count (4 of 7)", base + [xE], ids=("xE",))
c1 = admit("c1","H",("A","B","C","D"),("aG",))
c2 = admit("c2","J",("A","B","C","D","H"),("c1",))
run("RC1 c1,c2 beside aE, no post (tie expected)", base + [c1, c2], ids=("aE","c1","c2"))
c1p = admit("c1","H",("A","B","C","D"),("aG",),("fp",))   # c1 cites F's concurrent post
run("RC2 c1 cites F's post fp; c2 on c1", base + [post, c1p, c2], ids=("aE","c1","c2"))
for own in ("E", "F", "G"):
    run("RC2 reader %s" % own, base + [post, c1p, c2], own=own, ids=("aE",))
run("RC3 same but G signed a content row after aE", base + [post, c1p, c2, CK.row("gp","post","G",("aE",),room=OBJ)], ids=("aE",))
# knock: G's honest post after aE, then the attacker's c3 names gp as well (a merge?) 
c3 = admit("c3","K",("A","B","C","D","H","J"),("c2",),("gp",))
run("RC4 G posted after aE; attacker's c3 cites gp", base + [post, c1p, c2, CK.row("gp","post","G",("aE",),room=OBJ), c3], ids=("aE","c3"))
# a mere ack by colluder F on the other side (no post)
ackF = CK.row("af","ack","F",("c2",),room=OBJ,head=("c2",))
run("RC5 colluder F acks c2 (no post)", base + [c1, c2, ackF], ids=("aE",))
