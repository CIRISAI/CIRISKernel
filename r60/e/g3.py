import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G = ST.found("g", "A", ("A","B","C"), {"moderate": ("A",)}, cosigners=("B","C"))
rows = [G]; prev = "g"; mem = ["A","B","C"]
for k in "DEFG":
    rows.append(admit("a"+k, k, tuple(mem), (prev,))); mem.append(k); prev = "a"+k
K7 = "ABCDEFG"
lm2 = ST.withdraw("lm2", "A", "g", ("aG",), scope="moderate")
H = [ballot("b"+k.lower(), k, r, ("lm2",)) for k, r in zip(K7, "DDDDDDD")]
ids = tuple(b["id"] for b in H)
ed = elect("ed", "D", ids, vac=("lm2",))
show("G3a honest: all seven rank D", rows + [lm2] + H + [ed], K7)
lm1 = ST.withdraw("lm1", "A", "g", ("g",), scope="moderate")             # A backdates a second end
xb = [ballot("xb","B","B",("lm1","lm2","bb")), ballot("xc","C","B",("lm1","lm2","bc"))]   # B, C re-ballot naming both ends
# B and C each have two ballots in the set (bb/xb disagree): use withdrawals so each has one
wb = [ST.withdraw("wbb","B","bb",("xb",)), ST.withdraw("wbc","C","bc",("xc",))]
eb = elect("eb", "B", ids + ("xb","xc","wbb","wbc"), vac=("lm2","lm1"))
show("G3b B, C name A's backdated end in new ballots: electorate {A,B,C}", rows + [lm2] + H + [ed, lm1] + xb + wb + [eb], K7)
ak = [ack("k"+k.lower(), k, "ed") for k in "EFG"]
show("G3c E, F, G receipt ed before holding eb", rows + [lm2] + H + [ed] + ak + [lm1] + xb + wb + [eb], K7)
ak2 = [ack("k"+k.lower(), k, "ed", ("eb",)) for k in "EFG"]
show("G3d the same receipts made after eb", rows + [lm2] + H + [ed, lm1] + xb + wb + [eb] + ak2, K7)
