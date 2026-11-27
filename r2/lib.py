import sys, os, random
R = sys.argv[1]
sys.path.insert(0, os.path.join(R, "models/causal_kernel"))
import check_election as E
ST, CK = E.ST, E.CK
ballot, elect, admit, decline = E.ballot, E.elect, E.admit, E.decline
def seats(rows, keys, own=None, arrive=False):
    S = CK.arrive(list(rows), E.RULE) if arrive else CK.concluded(CK.kept(list(rows)), E.RULE)
    Q = ST.Seats(S, own=own)
    return {k: Q.stands(k, "moderate", "g") for k in keys}, Q, S
def show(name, rows, keys, n=60, own=None):
    base, Q, S = seats(rows, keys, own)
    conc = sorted(r["id"] for r in S.Cs if r.get("policy") == "moderator_election")
    print(name); print("   moderate:", {k: v for k, v in base.items()}, "| concluded seatings:", conc,
          "| beaten:", sorted(Q.beaten), "| tips:", sorted(x["id"] for x in Q.tips("g")))
    rnd = random.Random(7); tail = rows[1:]; diffs = 0
    for _ in range(n):
        p = list(tail); rnd.shuffle(p)
        if seats([rows[0]] + p, keys, own, arrive=True)[0] != base: diffs += 1
    print("   orders differing: %d of %d" % (diffs, n))
    return Q, S
