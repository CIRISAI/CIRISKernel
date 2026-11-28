import sys, os, random
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import seat as ST, check_agent_seat as A
CK = ST.CK; RULE = A.RULE
def run(name, rows, asks, n=30):
    def ans(S):
        Q = ST.Seats(S); return [(k, sc, Q.stands(k, sc, "g")) for k, sc in asks]
    S = CK.concluded(CK.kept(list(rows)), RULE); a = ans(S)
    rnd = random.Random(3); d = 0
    for _ in range(n):
        t = list(rows[1:]); rnd.shuffle(t)
        if ans(CK.arrive([rows[0]] + t, RULE)) != a: d += 1
    print("%-80s %s  orders differ %d/%d" % (name, a, d, n))
# after the owner's revocation, the agent binds itself to a sock owner SK and re-accepts the old conferral, SK cosigning
OSK = ST.offer("osk", "AG", "SK", "owner", "AG", "self", ("rag", "orv"), cosigners=("SK",))
ACC = ST.accept("acc", "AG", "cr", ("cr", "osk")) | {"cosigners": ("SK",)}
run("control: revoked (W3R + ORV)", A.W3R + [A.ORV], [("AG", "review")])
run("revoked, AG binds sock SK and re-accepts cr with SK cosigning", A.W3R + [A.ORV, OSK, ACC], [("AG", "review")])
# no real owner ever: the agent binds a sock and accepts a conferral (the members' count conferred it)
OSK0 = ST.offer("osk", "AG", "SK", "owner", "AG", "self", ("rag",), cosigners=("SK",))
W = [A.G3, A.admit("ag", "AG", ("p1", "p2", "p3"), ("g",), "agent"), A.RAG, OSK0, A.CRA, ST.accept("acc", "AG", "cr", ("cr", "osk")) | {"cosigners": ("SK",)}]
run("agent with only a self-made sock owner", W, [("AG", "review")])
# a duty conferred on the agent's key over a room where it holds a MEMBER seat (not agent): no owner needed?
WM = [A.G3, A.admit("ag", "AG", ("p1", "p2", "p3"), ("g",), "member"), A.RAG, A.OAG,
      ST.offer("cr", "p1", "AG", "review", "g", "group", ("ag",), head=("ag",), policy="duty_confer", counted="duty", cosigners=("p2", "AG"))]
run("agent key seated as member, review conferred with no owner signature", WM, [("AG", "review"), ("AG", "member")])
