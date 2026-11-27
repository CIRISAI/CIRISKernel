import sys, os, random
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import seat as ST, window as WN, check_lone_acts as L
CK = ST.CK; T, F = True, False
def admit(i, k, signers, heads):
    return ST.offer(i, signers[0], k, "member", "g", "group", tuple(heads), head=tuple(heads), policy="community_invite",
                    cosigners=tuple(signers[1:]) + (k,))
A5 = admit("a5", "p5", ("p1", "p2", "p3"), ("g",))
A6 = admit("a6", "p6", ("p1", "p2", "p3", "p5"), ("a5",))
TD = L.TD     # p1's takedown at head g
LF = ST.offer("lf", "p2", (), "act", "g", "group", ("td", "o2", "o5", "o6", "a6"), head=("a6",), content="td",
              policy="moderation_overturn")
rows = L.W + [TD, A5, A6, L.OB("o2", "p2"), L.OB("o5", "p5"), L.OB("o6", "p6"), LF]
print(L.answer(rows, {"a5": T, "a6": T, "lf": T}, {"td": T}))
# same, objections by p2 and the two new members only; members at td's head g: p1..p4 (p1 author) -> base {p2,p3,p4}
