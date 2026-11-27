exec(open(__file__.replace("cost2.py","lib.py")).read())
v, ntips, N, L = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
setv(None if v == "today" else v)
names = ["K%02d" % i for i in range(N)]
G = ST.found("g", names[0], tuple(names[:3]), {}, cosigners=tuple(names[1:3]))
rows = [G]; mem = list(names[:3]); prev = "g"; hist = [("g", list(mem))]
for k in names[3:]:
    rows.append(admit("a"+k, k, tuple(mem), (prev,))); mem.append(k); prev = "a"+k; hist.append((prev, list(mem)))
tips = []; heads = []
for i in range(ntips):                        # chain i forks from an older head, L admissions long
    h, m = hist[len(hist) - 1 - 3*i]; m = list(m)
    for j in range(L):
        k = "T%d_%d" % (i, j); tips.append(admit("t%d_%d" % (i, j), k, tuple(m), (h,))); m.append(k); h = "t%d_%d" % (i, j)
    heads.append(h)
fin = admit("fin", "Z", tuple(mem), tuple(heads) or (prev,))
t0 = time.time(); S = CK.concluded(CK.kept(rows + tips + [fin]), RULE); t1 = time.time()
Q = ST.Seats(S); h = Q.holders("member", OBJ); t2 = time.time()
print("%-5s N=%d tips=%d L=%d rows=%d conclude %.2fs read %.2fs fin=%s roster=%d" % (v, N, ntips, L, len(S.rows), t1-t0, t2-t1, S.C.get("fin"), len(h)))
