exec(open(__file__.replace("wc.py","lib.py")).read())
DC = lambda i, to, heads=("aG",): ST.offer(i, "A", to, "moderate", OBJ, "group", tuple(heads), head=tuple(heads), policy="duty_confer", counted="duty", cosigners=())
acc = lambda i, k, of: ST.accept(i, k, of)
SIB = [DC("z"+k, k) for k in "CDE"] + [acc("k"+k, k, "z"+k) for k in "CDE"]
base = ROOM + [DC("d1","B"), acc("kB","B","d1")]
WB = ST.unseat("wb","A","B","moderate",OBJ,"group",("d1","zC","zD","zE","kB","kC","kD","kE"),head=("d1","zC","zD","zE"),policy="duty_withdraw",counted="duty",cosigners=("C","D","E"))
SC = ("moderate","member")
closers = {
 "none": [],
 "concurrent: five admit H at aG": [admit("c","H",("B","C","D","E","F"),("aG",))],
 "B..F (not A) admit H at head d1": [admit("c","H",("B","C","D","E","F"),("d1",),("kB",))],
 "A and B confer moderate on F at head d1": [ST.offer("c","A","F","moderate",OBJ,"group",("d1","kB"),head=("d1",),policy="duty_confer",counted="duty",cosigners=("B",)), acc("kF","F","c")],
 "A among five admit H at head d1 (member scope)": [admit("c","H",("A","B","C","D","E"),("d1",),("kB",))],
}
for n, cl in closers.items():
    # siblings written after the closer exists (they do not name it): order of writing is causal only
    rows = base + cl + SIB + [WB]
    for own in (None, "B"):
        run("WC [%s] then siblings zC..zE and wb; reader %s" % (n, own), rows, own=own, ids=("zC","wb") + (("c",) if cl else ()), scopes=SC)
