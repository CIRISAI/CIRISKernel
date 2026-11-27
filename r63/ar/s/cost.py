exec(open(__file__.replace("cost.py","lib.py")).read())
v, ntips, N = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
setv(None if v == "today" else v)
names = ["K%02d" % i for i in range(N)]
G = ST.found("g", names[0], tuple(names[:3]), {}, cosigners=tuple(names[1:3]))
rows = [G]; mem = list(names[:3]); prev = "g"
for k in names[3:]:
    rows.append(admit("a"+k, k, tuple(mem), (prev,))); mem.append(k); prev = "a"+k
tips = [admit("t%d" % i, "T%d" % i, tuple(mem), (prev,)) for i in range(ntips)]
fin = admit("fin", "Z", tuple(mem), tuple(t["id"] for t in tips) if ntips else (prev,))
t0 = time.time(); S = CK.concluded(CK.kept(rows + tips + [fin]), RULE); t1 = time.time()
Q = ST.Seats(S); h = Q.holders("member", OBJ); t2 = time.time()
print("%-5s N=%d tips=%d  conclude %.2fs  read %.2fs  fin=%s roster=%d" % (v, N, ntips, t1-t0, t2-t1, S.C.get("fin"), len(h)))
