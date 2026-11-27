import sys
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
G = ST.offer("g", "A", tuple("ABCDEF"), "member", "@", "self", cosigners=tuple("BCDEF"), consensus_protocol="open:self_admit")
for cos in ((), ("B",), ("B", "C"), ("B", "C", "D")):
    r = grp("r", "offer", "X", "member", "community_invite", signer="A", cosigners=tuple(cos) + ("X",))
    S = CK.concluded(CK.kept([G, r]), RULE)
    print("vouch by A +", cos, "of 6 members:", S.C.get("r"))
r = grp("r", "offer", "X", "member", "community_invite", signer="A", cosigners=("X",), window="community_invite")
S = CK.concluded(CK.kept([G, r]), RULE); print("A alone, naming a community_invite window:", S.C.get("r"))
