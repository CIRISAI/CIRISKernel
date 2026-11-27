exec(open(__file__.replace("dbg.py","lib.py")).read())
G1 = ST.found("g","A",("A",),{}); solo=[G1]; m=["A"]; pv="g"
for k in "BCDEFG": solo.append(admit("a"+k,k,tuple(m),(pv,))); m.append(k); pv="a"+k
p1 = admit("p1","X1",("A",),("g",))
setv("L'")
S = CK.concluded(CK.kept(solo+[p1]), RULE)
for r in S.Cs:
    if r.get("head"): print(r["id"], "roster", sorted(ST.change_roster(S, r)), "sig", sorted(ST.signers(r)))
ST.DEBUG_OS=True; X = ST.onesay_void(S); print("void", sorted(X), ST.OS_STATS)
print("conc p1 aB", S.concurrent("p1","aB"))
ST._BOUND["aB"] = frozenset({"A","X1"})
P = [q for q in S.Cs if q["id"] in S.anc["aB"]]
print("aB with A bound:", ST.seat_rule(S.by["aB"], P, lambda a,b: a in S.anc[b]), ST.voices(S.by["aB"], P))
del ST._BOUND["aB"]
