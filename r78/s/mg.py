import sys, os, random
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel")); sys.dont_write_bytecode = True
import seat as ST, check_count_heads as CH, check_roster_merge as RM
CK = ST.CK; RULE = CH.RULE; admit, remove, ack, ROOM = CH.admit, CH.remove, CH.ack, CH.ROOM
def run(name, rs, own=None, ids=(), n=60):
    def ans(S):
        Q = ST.Seats(S, own=own)
        return ({i: bool(S.C.get(i)) for i in ids}, "".join(sorted(Q.holders("member","g"))))
    S = CK.concluded(CK.kept(list(rs)), RULE); a = ans(S); rnd = random.Random(7); d = 0
    for _ in range(n):
        t = list(rs[1:]); rnd.shuffle(t)
        if ans(CK.arrive([rs[0]] + t, RULE)) != a: d += 1
    print(name); print("   ", a, "| orders differing %d/%d" % (d, n))
# a self-forked minority removal tip: A,B,C (who signed aD..aG) remove G at aF (sibling of aG? a fork at aF)
# honest tip: x1 = five admit H at aG
X1 = admit("x1","H",("A","B","C","D","E"),("aG",))
f1 = remove("f1","G",("A","B","C","D"),("aF",))     # A..D (4 of 6 at aF) remove G at aF; they also signed aG
L = ROOM + [X1, f1]
run("MG0 tips x1 and f1 (f1 self-forked?)", L, ids=("x1","f1"))
SEVENH = tuple("ABCDEFGH")
m_keep = ST.merge("m", "A", "g", ("x1","f1"), SEVENH, {"moderate": ("A",)}, cosigners=tuple("BCDEFGH"))
m_drop = ST.merge("m", "A", "g", ("x1","f1"), tuple("ABCDEFH"), {"moderate": ("A",)}, cosigners=tuple("BCDEFGH"))
run("MG1 merge (x1,f1) keeping G, signed by all", L + [m_keep], ids=("m",))
run("MG2 merge (x1,f1) dropping G, signed by all", L + [m_drop], ids=("m",))
m_drop2 = ST.merge("m", "A", "g", ("x1","f1"), tuple("ABCDEFH"), {"moderate": ("A",)}, cosigners=tuple("BCDEH"))
run("MG3 merge dropping G, signed by A..E and H (not F, G)", L + [m_drop2], ids=("m",))
print("---- a self-forked tip (depth 2 at aE) that removes E")
f1 = remove("f1","E",("A","B","C","D"),("aE",))        # A..D, 4 of 5 at aE; they also signed aF, aG (aE is behind aF's head)
f2 = admit("f2","Z",("A","B","C","D","Z"),("f1",))
L2 = ROOM + [X1, f1, f2]
run("MG4 tips x1 and f2", L2, ids=("x1","f1","f2"))
for own in ("F","E"):
    run("MG4 reader %s" % own, L2, own=own, ids=("f2",))
keepE = ST.merge("m", "A", "g", ("x1","f2"), tuple("ABCDEFGHZ"), {"moderate": ("A",)}, cosigners=tuple("BCDEFGHZ"))
dropE = ST.merge("m", "A", "g", ("x1","f2"), tuple("ABCDFGHZ"), {"moderate": ("A",)}, cosigners=tuple("BCDFGHZ"))
run("MG5 merge (x1,f2) keeping E, signed by all", L2 + [keepE], ids=("m",))
run("MG6 merge (x1,f2) dropping E (and keeping Z), signed by all but E", L2 + [dropE], ids=("m",))
