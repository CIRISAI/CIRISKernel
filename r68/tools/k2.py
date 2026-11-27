import sys, time, cProfile, pstats, io
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
n = int(sys.argv[3])
G = ST.offer("g", "A", ("A", "B", "C"), "member", "@", "self", cosigners=("B", "C"), consensus_protocol="open:self_admit")
sa = lambda i, k, heads: grp(i, "offer", k, "member", "cosigned_act", heads=heads, signer=k)
tips = [sa("s%d" % i, "J%d" % i, ("g",)) for i in range(n)]
cov = sa("cov", "Z", tuple(t["id"] for t in tips))
rows = [G] + tips
t = time.time(); S0 = CK.concluded(CK.kept(rows), RULE); t_tips = time.time() - t
pr = cProfile.Profile(); pr.enable()
t = time.time(); S1 = CK.concluded(CK.kept(rows + [cov]), RULE); t_all = time.time() - t
pr.disable()
print("n=%d: concluding the %d tips %.2fs; with the covering row %.2fs (covering concluded %s)" % (n, n, t_tips, t_all, S1.C.get("cov")))
s = io.StringIO(); pstats.Stats(pr, stream=s).sort_stats("cumulative").print_stats(12); print("\n".join(s.getvalue().splitlines()[:40]))
