import sys, itertools
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
FH4 = AC.FH4   # A, B, C, D; A the one moderator by the founding map
for pol in ("community_invite",):
    for sc in ("member", "agent"):
        r = grp("r", "offer", "X", sc, pol, signer="A", cosigners=("X",), counted="moderate")
        run("M4 A (lone moderator) alone admits X as %s, %s counted over moderate" % (sc, pol), [FH4, r], [("X", sc)])
r0 = grp("r", "offer", "X", "member", "community_invite", signer="A", cosigners=("X",))
run("M4-base same counted over members", [FH4, r0], [("X", "member")])
# a lone moderator + over another room
H = ST.offer("h", "A", ("A",), "member", "@", "self", consensus_protocol="majority")
for pol in ("community_invite", "cosigned_act"):
    r = grp("r", "offer", "X", "member", pol, heads=("h",), signer="A", cosigners=("X",), over="h")
    run("M5 A alone admits X to g counted over its own room h (%s)" % pol, [AC.GM4, H, r], [("X", "member")])
    u = grp("x", "unseat", "B", "member", "community_remove" if pol == "community_invite" else None, heads=("h",), signer="A", over="h")
    run("M5b A alone removes B from g counted over h", [AC.GM4, H, u], [("B", "member")])
