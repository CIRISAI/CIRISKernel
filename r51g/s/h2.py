import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G = ST.found("g", "A", ("A","B","C"), {"moderate": ("A",)}, cosigners=("B","C"))
rows = [G]; prev = "g"; mem = ["A","B","C"]
for k in "DEFGHI":
    rows.append(admit("a"+k, k, tuple(mem), (prev,))); mem.append(k); prev = "a"+k
K9 = "ABCDEFGHI"
lm2 = ST.withdraw("lm2", "A", "g", ("aI",), scope="moderate")
H = [ballot("b"+k.lower(), k, "D", ("lm2",)) for k in "DEFGHI"]
s1 = elect("s1", "D", tuple(b["id"] for b in H), vac=("lm2",))
cl = [ack("k"+k.lower(), k, "s1", ("b"+k.lower(),)) for k in "EFGHI"]        # 5 of base 8 (A..I less D)
honest = rows + [lm2] + H + [s1] + cl
show("H2a honest: D closed by E..I", honest, K9)
lm1 = ST.withdraw("lm1", "A", "g", ("g",), scope="moderate")                    # A backdates a second end
xb = [ballot("xb","B","B",("lm1","lm2")), ballot("xc","C","B",("lm1","lm2"))]
s2 = elect("s2", "B", ("xb","xc"), vac=("lm1","lm2"))                           # electorate {A,B,C}; A forked
kc = ack("kc", "C", "s2", ("xc",))                                              # base {C}: 1 of 1
show("H2b A, B, C: a rival over the founders' electorate meets its own close", honest + [lm1] + xb + [s2, kc], K9)
