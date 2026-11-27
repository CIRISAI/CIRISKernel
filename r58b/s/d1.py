import sys, os
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import seat as ST; CK = ST.CK
RULE = lambda r, P, past: ST.seat_rule(r, P, past)
g = ST.offer("g", "f1", ("f1", "f2", "f3"), "duty", "@", "self", cosigners=("f2", "f3"))
mk = ST.offer("mk", "f1", "K", "member", "g", "group", ("g",), head=("g",), policy="community_invite", cosigners=("f2", "f3", "K"))
d = ST.offer("d", "f1", "K", "moderate", "g", "group", ("mk",), head=("mk",), policy="duty_confer", counted="duty", cosigners=("f2",))
ak = ST.accept("ak", "K", "d")
c3 = ST.cosign("c3", "f3", "xf", ("d",))
xf = ST.unseat("xf", "f2", "f1", "duty", "g", "group", ("d", "c3", "ak"), head=("d",), policy="duty_withdraw", content="xf", counted="duty")
S = CK.concluded(CK.kept([g, mk, d, ak, c3, xf]), RULE); Q = ST.Seats(S)
print("t03 rewritten: d", bool(S.C.get("d")), "xf", bool(S.C.get("xf")), "f1 duty", Q.stands("f1","duty","g"), "K moderate", Q.stands("K","moderate","g"))
for tree in (sys.argv[1],): pass
