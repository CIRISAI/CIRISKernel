import sys, os, random
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import seat as ST
CK = ST.CK
print("policies:", ST.POLICY.get("community_invite"), ST.POLICY.get("community_remove"))
RULE = lambda r, P, past: ST.seat_rule(r, P, past)
OBJ = "g"
def admit(i, k, signers, heads, cites=()):
    return ST.offer(i, signers[0], k, "member", OBJ, "group", tuple(heads)+tuple(cites), head=tuple(heads),
                    policy="community_invite", cosigners=tuple(signers[1:]) + ((k,) if k not in signers else ()))
def remove(i, k, signers, heads, cites=()):
    return ST.unseat(i, signers[0], k, "member", OBJ, "group", tuple(heads)+tuple(cites), head=tuple(heads),
                     policy="community_remove", cosigners=tuple(signers[1:]))
G = ST.found("g", "A", ("A","B","C"), {"moderate": ("A",)}, cosigners=("B","C")) if hasattr(ST, "found") else ST.offer("g", "A", ("A","B","C"), "member", "@", "self", cosigners=("B","C"))
print("founding:", "found() with duty map" if hasattr(ST, "found") else "plain offer, scope member, self")
rows = [G]; prev = "g"; mem = ["A","B","C"]
for k in "DEFG":
    rows.append(admit("a"+k, k, tuple(mem), (prev,))); mem.append(k); prev = "a"+k
XG = remove("xg", "G", ("A","B"), ("g",), ("aG",))       # head g (roster 3), past holds aG (roster 7)
AX = admit("ax", "X", ("A","B"), ("g",), ("aG",))
ACK = CK.row("ak", "ack", "R", ("aG",), room=OBJ, head=("aG",))
K = "ABCDEFGX"
def run(name, rs, own=None, n=60):
    def ans(S): Q = ST.Seats(S, own=own); return {k: Q.stands(k, "member", OBJ) for k in K}, Q
    S = CK.concluded(CK.kept(list(rs)), RULE)
    a, Q = ans(S)
    ok = {r["id"]: (r in S.Cs) for r in rs if r["id"] in ("xg","ax")}
    print(name); print("   concluded:", ok, "| stale:", sorted(getattr(Q, "stale", ["(no attr)"])), "| members:", sorted(k for k,v in a.items() if v))
    rnd = random.Random(3); d = 0
    for _ in range(n):
        t = list(rs[1:]); rnd.shuffle(t)
        if ans(CK.arrive([rs[0]]+t, RULE))[0] != a: d += 1
    print("   orders differing: %d of %d" % (d, n))
run("control: roster of seven", rows)
run("P1a removal of G by A,B at head g, past holds aG", rows+[XG])
run("P1b admission of X by A,B at head g, past holds aG", rows+[AX])
run("P2a P1a for reader R that acked aG", rows+[ACK, XG], own="R")
run("P2b P1b for reader R that acked aG", rows+[ACK, AX], own="R")
XG2 = remove("xg", "G", ("A","B"), ("g",))                 # control: concurrent with the admissions
run("P2c control: removal at head g NOT descending from aG, reader acked aG", rows+[ACK, XG2], own="R")
run("P2d same, no reader", rows+[XG2])
