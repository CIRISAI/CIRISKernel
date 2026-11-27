import sys, itertools, time
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
G = ST.offer("g", "A", ("A", "B", "C"), "member", "@", "self", cosigners=("B", "C"), consensus_protocol="open:self_admit")
sa = lambda i, k, heads=("g",): grp(i, "offer", k, "member", "cosigned_act", heads=heads, signer=k)
for n in (1, 3, 8, 16):
    rows = [G] + [sa("s%d" % i, "J%d" % i) for i in range(n)]
    t = time.time(); S = CK.concluded(CK.kept(rows), RULE); Q = ST.Seats(S)
    seated = sorted(k for k in Q.roster("g") if k.startswith("J"))
    P = list(S.Cs); past = lambda a, b: a in S.anc[b]
    # a members' count naming one tip: A,B remove nobody... use an admission by community_invite of K naming s0
    ci = grp("ci", "offer", "K", "member", "community_invite", heads=("s0",), signer="A", cosigners=("B", "C", "K"))
    S2 = CK.concluded(CK.kept(rows + [ci]), RULE); Q2 = ST.Seats(S2)
    print("F%d concurrent self-admissions: %d seated of %d; count base at s0 %s; K admitted naming one tip: concl %s, seated %s; %.2fs"
          % (n, len(seated), n, sorted(ST.counted_keys(P, past, "g", ("s0",))[0]), S2.C.get("ci"), Q2.stands("K", "member", "g"), time.time() - t))
