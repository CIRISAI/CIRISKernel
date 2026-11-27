exec(open(__file__.replace("r1.py","lib.py")).read())
def pack(n, first_signers, rest_signers, base=("g",), pref="p"):
    P = []; pv = base
    for i in range(1, n+1):
        k = "X%d" % i
        sg = first_signers if i == 1 else rest_signers
        P.append(admit("%s%d" % (pref, i), k, tuple(sg) + tuple("X%d" % j for j in range(1, i)), pv)); pv = ("%s%d" % (pref, i),)
    return P, pv[0]
# R1: A,B fork at g; C (who honestly cosigned aD..aG) joins from the second row on: C rescues?
P, last = pack(5, ("A","B"), ("A","B","C"))
XS = lambda vic, heads, extra=(): remove("x"+vic, vic, ("A","B","C") + tuple("X%d" % j for j in range(1, 6)) + tuple(extra), heads)
run("R1a pack X1..X5 (first by A,B; rest by A,B,C), no count", ROOM + P, ids=tuple(p["id"] for p in P))
run("R1b + A,B,C,X1..X5 remove D heads (aG,p5)", ROOM + P + [XS("D", ("aG", last))], ids=("p5","xD"))
run("R1c same, reader D", ROOM + P + [XS("D", ("aG", last))], own="D", ids=("p5","xD"))
run("R1d same, reader Q (no row)", ROOM + P + [XS("D", ("aG", last))], own="Q", ids=("p5","xD"))
# R2: C rescues by a single cosignature on a later fork row only
P2, last2 = pack(5, ("A","B"), ("A","B"))
P2[2] = dict(P2[2], cosigners=tuple(P2[2]["cosigners"]) + ("C",))
run("R2 pack by A,B; C cosigns p3 only; A,B,C,X1..X5 remove D heads (aG,p5)", ROOM + P2 + [XS("D", ("aG", last2))], ids=("p5","xD"))
# R0 control: no C at all
P0, last0 = pack(5, ("A","B"), ("A","B"))
run("R0 control: A,B pack; A,B,X1..X5 remove D", ROOM + P0 + [remove("xD","D",("A","B")+tuple("X%d"%j for j in range(1,6)),("aG",last0))], ids=("p5","xD"))
