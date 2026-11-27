import sys, random
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
G = ST.offer("g", "A", ("A", "B", "C", "D"), "member", "@", "self", cosigners=("B", "C", "D"), consensus_protocol="majority")
am = grp("am", "offer", (), "record", "cosigned_act", signer="A", cosigners=("B", "C"), consensus_protocol="quorum:2/4")
n = grp("n", "offer", "Q", "member", "community_invite", heads=("am",), signer="A")                   # fails
am2 = dict(grp("am2", "offer", (), "record", "default_content", heads=("am",), signer="B", cosigners=("C", "D"), consensus_protocol="unanimous"), names=("n",))
x = grp("x", "unseat", "D", "member", None, heads=("am2",), signer="A", cosigners=("B",))            # 2 voices: quorum:2/4 yes, unanimous no
y = grp("y", "offer", "E", "member", "cosigned_act", heads=("am2",), signer="A", cosigners=("B", "E"))
rows = [G, am, n, am2, x, y]
S = CK.concluded(CK.kept(rows), RULE); Q = ST.Seats(S)
base = ({r["id"]: bool(S.C.get(r["id"])) for r in rows}, sorted(Q.holders("member", "g")))
P = {q["id"]: q for q in S.Cs if q["id"] in S.anc["x"]}
print("concluded", base[0], "members", base[1], "protocol at x:", ST.protocol_of(P, "g"))
rnd = random.Random(7); bad = 0
for _ in range(60):
    t = rows[1:]; rnd.shuffle(t)
    S2 = CK.arrive([rows[0]] + t, RULE); Q2 = ST.Seats(S2)
    if ({r["id"]: bool(S2.C.get(r["id"])) for r in rows}, sorted(Q2.holders("member", "g"))) != base: bad += 1
print("60 arrival orders, differing:", bad)
