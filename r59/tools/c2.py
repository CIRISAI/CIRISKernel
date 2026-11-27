import sys, itertools
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
GA = AC.GA   # accord: h1, h2, h3, scope holder
solo = ST.offer("so", "h1", "h1", "solo", OBJ, "self", ("g",))
ad = grp("r", "offer", "X", "holder", None, heads=("so",), signer="h1", counted="solo", cosigners=("X",))
rm = grp("x", "unseat", "h2", "holder", None, heads=("so",), signer="h1", counted="solo")
run("M1 accord: h1 holds `solo` by its own offer; counted over solo, h1 alone admits X / removes h2", [GA, solo, ad, rm], [("h1", "solo"), ("X", "holder"), ("h2", "holder")])
ad0 = grp("r", "offer", "X", "holder", None, signer="h1", cosigners=("X",), counted="holder")
run("M1-base h1 alone counted over holders", [GA, ad0], [("X", "holder")])
# community: a counted admission counting a body other than member (protocol body check)
G = AC.GM4
run("M2 community: A alone admits X counted over `detect:x`", [G, grp("r", "offer", "X", "member", "cosigned_act", signer="A", cosigners=("X",), counted="detect:x")], [("X", "member")])
# community_invite (not a protocol row): body free?
so2 = ST.offer("so", "A", "A", "solo", OBJ, "self", ("g",))
run("M3 community: A holds solo; community_invite counted solo, A alone admits X", [G, so2, grp("r", "offer", "X", "member", "community_invite", heads=("so",), signer="A", cosigners=("X",), counted="solo")], [("A", "solo"), ("X", "member")])
run("M3b same, unseat B under community_remove counted solo", [G, so2, grp("x", "unseat", "B", "member", "community_remove", heads=("so",), signer="A", counted="solo")], [("B", "member")])
