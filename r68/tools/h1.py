import sys, itertools
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
G = ST.found("g", "A", ("A", "B", "C", "D"), {"moderate": ("A",)}, cosigners=("B", "C", "D"))
am = grp("am", "offer", "X", "member", "community_invite", signer="A", cosigners=("B", "C", "X"))
aa = grp("aa", "offer", "X", "agent", "community_invite", heads=("am",), signer="A", cosigners=("B", "C", "X"))
cm = grp("cm", "offer", "X", "review", "duty_confer", heads=("aa",), signer="A", counted="duty", cosigners=("X",))
base = [G, am, aa, cm]
S = CK.concluded(CK.kept(base), RULE); Q = ST.Seats(S)
print("P0 X holds member, agent, review:", {s: Q.stands("X", s, "g") for s in ("member", "agent", "review")}, {r["id"]: bool(S.C.get(r["id"])) for r in base})
# P3: is X (member + agent) a voice of a members' count? A, X admit Y (2 of 5 members-or-persons?)
P = [q for q in S.Cs]
past = lambda a, b: a in S.anc[b]
print("P3 counted_keys(member) at cm:", sorted(ST.counted_keys(P, past, "g", ("cm",))[1]))
# P1: X withdraws its agent seat
w = ST.withdraw("wa", "X", "aa", ("cm",))
run("P1 X withdraws its agent seat only", base + [w], [("X", "member"), ("X", "review"), ("X", "agent")], orders=False)
# P2: moderator A lone-removes X's agent seat
x = grp("x", "unseat", "X", "agent", "community_remove", heads=("cm",), signer="A", window="moderation_overturn")
run("P2 A (moderate) lone-removes X's agent seat", base + [x], [("X", "member"), ("X", "review"), ("X", "agent")], orders=False)
