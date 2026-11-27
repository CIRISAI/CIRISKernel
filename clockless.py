"""Two moderation windows with NO landing on the wire, read as CC 4.5.13 states them, against the same windows
read from rows. Three members a, b, c. X is the act (a moderator's act for the overturn; the report the moderator
did not answer, for the fallback). Each member may sign one answer (an objection, or a fallback act) at its own
signed instant. A node first holds each row at an instant of its own.

clock    an answer counts at a node iff the node first held it within FRESH of its signed instant and within
         the window, measured from the node's own first holding of X. The outcome is met iff a strict majority
         of the three counts.
rows     the outcome is met iff answers by a strict majority are held. No instant is read.
"""
import itertools
L, FRESH, T = 2, 1, 5            # the window, the freshness bound, the last instant; one unit stands for 24 h
MEM = "abc"

def clock(signed, held, hx):
    n = sum(1 for k in signed if held[k] - signed[k] <= FRESH and held[k] <= hx + L)
    return 2 * n > len(MEM)

def rows(signed):
    return 2 * len(signed) > len(MEM)

differ = same = 0; first = None; sets = 0
for r in range(0, 4):
    for who in itertools.combinations(MEM, r):
        for sg in itertools.product(range(T + 1), repeat=len(who)):
            signed = dict(zip(who, sg)); sets += 1
            views = set()
            ex = {}
            for hx in range(T + 1):
                for hd in itertools.product(*[range(signed[k], T + 1) for k in who]):
                    v = clock(signed, dict(zip(who, hd)), hx)
                    views.add(v); ex.setdefault(v, (hx, dict(zip(who, hd))))
            if len(views) > 1:
                differ += 1
                if first is None or len(who) < len(first[0]):
                    first = (signed, ex[True], ex[False])
            else:
                same += 1
print("clock reading: %d sets of rows (X and up to three answers with their signed instants); on %d of them two nodes "
      "holding the same rows conclude differently, and nothing either node later holds changes its answer" % (sets, differ))
s, y, n = first
print("  smallest: answers signed at %s; node A first holds X at %d and the answers at %s: met; node B first holds X at %d "
      "and the answers at %s: not met" % (s, y[0], y[1], n[0], n[1]))
print("rows reading: the outcome is a function of the set on all %d sets (it reads no instant); it never closes: a "
      "strict majority's answers meet it whenever they are held" % sets)
