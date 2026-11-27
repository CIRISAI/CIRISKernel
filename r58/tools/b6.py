import sys, itertools
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
GM4 = AC.GM4
am1 = grp("am", "offer", (), "record", "cosigned_act", cosigners=("B", "C"), consensus_protocol="one")
bad = grp("n", "offer", "Q", "member", "community_invite", heads=("am",), signer="A")      # A alone: fails 2/3
am2 = grp("am2", "offer", (), "record", "default_content", heads=("am",), cites=("n",), signer="B", cosigners=("C", "D"), consensus_protocol="majority")
am2 = dict(am2, names=("n",))           # am2 names only the failed row n (which names am)
x = grp("x", "unseat", "D", "member", None, heads=("am2",), signer="A", cosigners=("B", "C"))
rows = [GM4, am1, bad, am2, x]
S = CK.concluded(CK.kept(rows), RULE)
print({r["id"]: S.C.get(r["id"]) for r in rows}, "am in past of am2:", "am" in S.anc["am2"])
P = {q["id"]: q for q in S.Cs if q["id"] in S.anc["x"]}
print("protocol_of at x:", ST.protocol_of(P, "g"))
