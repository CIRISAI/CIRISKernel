import sys, time
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
n = int(sys.argv[3])
G = ST.offer("g", "A", ("A", "B", "C"), "member", "@", "self", cosigners=("B", "C"), consensus_protocol="open:self_admit")
sa = lambda i, k, heads: grp(i, "offer", k, "member", "cosigned_act", heads=heads, signer=k)
tips = [sa("s%d" % i, "J%d" % i, ("g",)) for i in range(n)]
ids = tuple(t["id"] for t in tips)
cov_sa = sa("cov", "Z", ids)                                       # an outsider's own seating naming every tip
mem_row = grp("m", "offer", "K", "member", "community_invite", heads=("cov",), signer="A", cosigners=("B", "C", "K"))
stale = grp("m2", "offer", "K2", "member", "community_invite", heads=("s0",), signer="A", cosigners=("B", "C", "K2"))
t = time.time()
S = CK.concluded(CK.kept([G] + tips + [cov_sa, mem_row, stale]), RULE)
t1 = time.time()
past = lambda a, b: a in S.anc.get(b, ())
P = lambda rid: [q for q in S.Cs if q["id"] in S.anc[rid]]
t2 = time.time(); h_cov = ST.newer_head_in_past(cov_sa["head"], None, P("cov"), past, "g", ST.signers(cov_sa)); t3 = time.time()
h_m = ST.newer_head_in_past(("cov",), None, P("m"), past, "g", ST.signers(mem_row)); t4 = time.time()
h_st = ST.newer_head_in_past(("s0",), None, P("m2"), past, "g", ST.signers(stale))
print("n=%d conclude-all %.2fs | covering self-seating concluded=%s, H1 refuses it=%s (%.2fs) | member count naming only cov: H1 refuses=%s (%.3fs), concluded=%s | naming one tip: H1 refuses=%s concluded=%s"
      % (n, t1 - t, S.C.get("cov"), h_cov, t3 - t2, h_m, t4 - t3, S.C.get("m"), h_st, S.C.get("m2")))
