import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G8 = room(8); K8 = "ABCDEFGH"
s1r = [ballot("ba","A","B"), ballot("bb","B","B"), elect("s1","B",("ba","bb"))]
s2r = [ballot("bc","C","C"), ballot("bd","D","C"), elect("s2","C",("bc","bd"))]
y2 = [ack("k"+k.lower(), k, "s2", ("bd",)) for k in "DEFG"]            # D, E, F, G receipt s2: 4 of {A,B,D..H} (7)
lv = [leave("l"+k.lower(), k, "g", ("lm",)) for k in "DEFG"]           # and leave, on rows that do not hold s2
y1 = [ack("ka","A","s1",tuple("l"+k.lower() for k in "DEFG")), ack("kh","H","s1",tuple("l"+k.lower() for k in "DEFG"))]
rows = [G8, LM] + s1r + s2r + y2 + lv + y1
Q, S_ = show("G2 two closes? A,H close s1 over {A,C,H}; D..G close s2 over 7", rows, K8, n=200)
by = {q["id"]: q for q in S_.Cs}
past = lambda a, b: a in S_.anc[b]
Ek = ST._view(S_.Cs, past, by["s1"])[0]
print("   closure over all rows:", sorted(ST.closure(Ek, S_.Cs, past, "g") or []))
A1 = [q for q in S_.Cs if q["id"] in S_.anc["ka"] or q["id"] == "ka"] + [by["kh"]]
A1 = [q for q in S_.Cs if q["id"] in ("ka","kh") or any(q["id"] in S_.anc[x] for x in ("ka","kh"))]
A2 = [q for q in S_.Cs if q["id"] in [y["id"] for y in y2] or any(q["id"] in S_.anc[y["id"]] for y in y2)]
print("   closure over s1's receipts' rows:", sorted(ST.closure(Ek, A1, past, "g") or []))
print("   closure over s2's receipts' rows:", sorted(ST.closure(Ek, A2, past, "g") or []))
