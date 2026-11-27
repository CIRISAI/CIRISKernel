import sys, itertools, random
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
G = ST.offer("g", "A", tuple("ABCDEF"), "member", "@", "self", cosigners=tuple("BCDEF"), consensus_protocol="majority")
rem = lambda i, k, signers, heads=("g",): grp(i, "unseat", k, "member", None, heads=heads, signer=signers[0], cosigners=tuple(signers[1:]))
def orders(name, rows, n=60):
    S = CK.concluded(CK.kept(rows), RULE); Q = ST.Seats(S)
    base = (sorted(Q.dropped), sorted(Q.roster("g")))
    rnd = random.Random(3); bad = 0
    for _ in range(n):
        t = rows[1:]; rnd.shuffle(t)
        Q2 = ST.Seats(CK.arrive([rows[0]] + t, RULE))
        if (sorted(Q2.dropped), sorted(Q2.roster("g"))) != base: bad += 1
    print(name, "out:", base[0], "roster:", base[1], "| 60 orders differing:", bad)
x1 = rem("x1", "E", "ABCD"); x2 = rem("x2", "F", "BCDE"); x3 = rem("x3", "A", "CDEF")
orders("T3 three-way cycle at g", [G, x1, x2, x3])
y1 = rem("y1", "E", "ABCD"); y2 = rem("y2", "A", "BCDE")
orders("T2 pair at g", [G, y1, y2])
orders("T2+1 pair plus an independent removal needing neither (C,D,E,F remove B)", [G, y1, y2, rem("y3", "B", "CDEF")])
# chain: y1 <-> y2 contested; z removes a voice of y1 only (one-sided)
orders("T4 a removal of D by B,C,E,F concurrent (threatens y1 and y2)", [G, y1, y2, rem("z", "D", "BCEF")])
# a pair at different heads: admission row h, then y2 at head h
h = grp("h", "offer", "Q", "member", "cosigned_act", heads=("g",), signer="A", cosigners=("B", "C", "D", "Q"))
orders("T5 pair at different heads (y1 at g, y2' at h)", [G, h, y1, rem("y2", "A", "BCDE", heads=("h",))])
orders("T5b swapped (y1' at h, y2 at g)", [G, h, rem("y1", "E", "ABCD", heads=("h",)), y2])
