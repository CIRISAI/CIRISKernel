import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G5 = room(5); KS = "ABCDEFGHI"
lm2 = ST.withdraw("lm2", "A", "g", ("g",), scope="moderate")             # A resigns: the vacancy (electorate A..E)
adm, prev, mem = [], "g", list("ABCDE")
for k in "FGHI":                                                          # newcomers, admitted on rows not holding lm2
    adm.append(admit("a"+k, k, tuple(mem), (prev,))); mem.append(k); prev = "a"+k
H = [ballot("b"+k.lower(), k, r, ("lm2",)) for k, r in zip("ABCDE", "CCCCC")]
s1 = elect("s1", "C", tuple(b["id"] for b in H), vac=("lm2",))
cl = [ack("k"+k.lower(), k, "s1", ("b"+k.lower(),)) for k in "BDE"]       # 3 of {A,B,D,E}: closed
honest = [G5, lm2] + adm + H + [s1] + cl
show("J1a honest: C closed by B, D, E; F..I admitted after (not voters)", honest, KS)
lm1 = ST.withdraw("lm1", "A", "g", ("aI",), scope="moderate")             # A lays down again on the newest admission
x = [ballot("xf","F","F",("lm1",)), ballot("xg","G","F",("lm1",)), elect("sx","F",("xf","xg"),vac=("lm1",))]
show("J1b A + F + G: a seating whose end is lm1 (electorate A..I): the union base takes in F..I", honest + [lm1] + x, KS)
# the same with re-admitted members: F..I members at the old end, left before lm2, re-admitted after it
G = ST.found("g", "A", tuple("ABCDEFGHI"), {"moderate": ("A",)}, cosigners=tuple("BCDEFGHI"))
lv = [leave("l"+k.lower(), k, "g", ("g",)) for k in "FGHI"]
lm2b = ST.withdraw("lm2", "A", "g", tuple("l"+k.lower() for k in "FGHI"), scope="moderate")
ra, prev = [], "lm2"
for k in "FGHI":
    ra.append(admit("r"+k, k, tuple("ABCDE"), (prev,))); prev = "r"+k
lm1b = ST.withdraw("lm1", "A", "g", ("g",), scope="moderate")              # backdated to the founding row
x2 = [ballot("xf","F","F",("lm1","rF")), ballot("xg","G","F",("lm1","rG")), elect("sx","F",("xf","xg"),vac=("lm1",))]
honest2 = [G] + lv + [lm2b] + ra + H + [s1] + cl
show("J1c re-admitted: honest close", honest2, KS)
show("J1d re-admitted: A backdates to g; F, G vote at lm1", honest2 + [lm1b] + x2, KS)
