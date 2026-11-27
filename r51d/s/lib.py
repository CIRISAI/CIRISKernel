import sys, os, random, time
R_ = sys.argv[1]
sys.path.insert(0, os.path.join(R_, "models/causal_kernel"))
import check_election as E
ST, CK, R = E.ST, E.CK, E.R
ballot, decline, elect, ack, admit, leave, room, LM = E.ballot, E.decline, E.elect, E.ack, E.admit, E.leave, E.room, E.LM
def seats(rows, keys, own=None, arrive=False):
    S = CK.arrive(list(rows), E.RULE) if arrive else CK.concluded(CK.kept(list(rows)), E.RULE)
    Q = ST.Seats(S, own=own) if own else ST.Seats(S)
    return {k: Q.stands(k, "moderate", "g") for k in keys}, Q, S
def show(name, rows, keys, n=60, own=None):
    t = time.time()
    base, Q, S = seats(rows, keys, own)
    conc = sorted(r["id"] for r in S.Cs if ST.is_election(r))
    print(name); print("   moderate:", sorted(k for k, v in base.items() if v), "| concluded seatings:", conc,
          "| beaten:", sorted(Q.beaten), "| %.2fs" % (time.time() - t))
    rnd = random.Random(7); tail = rows[1:]; diffs = 0
    for _ in range(n):
        p = list(tail); rnd.shuffle(p)
        if seats([rows[0]] + p, keys, own, arrive=True)[0] != base: diffs += 1
    print("   orders differing: %d of %d" % (diffs, n))
    return Q, S
