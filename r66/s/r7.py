exec(open(__file__.replace("r7.py","lib.py")).read())
RC7, RC7G, RCB = CH.RC7, CH.RC7G, CH.RCB
print("RCB rows:", [(r["id"], r["signer"], r.get("cosigners"), r.get("head")) for r in RCB[1:]])
run("RC7 (stated EDGE)", RC7, ids=("aE","cq","c1","c2"))
run("RC7 reader E", RC7, own="E", ids=("aE",))
run("RC7G (guard)", RC7G, ids=("aE","c1"))
# RC7 without the honest cq being dragged: c1 at aG directly (tie expected)
alt = RCB + [CH.RCQ, admit("c1","H",("A","B","C","D"),("aG",)), admit("c2","J",("A","B","C","D","H"),("c1",))]
run("RC7x c1 at aG, cq left alone (cited? no)", alt, ids=("aE","c1","c2"))
alt2 = RCB + [CH.RCQ, admit("c1","H",("A","B","C","D"),("aG",),("cq",)), admit("c2","J",("A","B","C","D","H"),("c1",))]
run("RC7y c1 at aG citing cq (not as head)", alt2, ids=("aE","c1","c2"))
# removal of E by A..D at aE (RC0 shape on this room)
run("RC7 control: A,B,C,D remove E", RCB + [remove("xE","E",("A","B","C","D"),("aE",))], ids=("xE",))
