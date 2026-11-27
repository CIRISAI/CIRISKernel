"""roster_fork with a FOLD at tips: with several tips the roster is every member some tip lists, less every
member any tip's line removed (commuting changes fold; an admit and a remove of one member leave it out).
Compared with M0 (the members common to all tips), in and out of the regime where the adversary is below the
count of every valid version."""
import sys, os
sys.path.insert(0, 'models/roster_fork'); sys.dont_write_bytecode = True
import fork as F
m = lambda s: sum(1 << int(c) for c in s)
F.RULES['MF'] = F.RULES['M0']
orig = F.conclude
STRICT = bool(os.environ.get("STRICT")) if 'os' in dir() else False
def conclude(W, S, rule):
    C = orig(W, S, 'M0' if rule == 'MF' else rule)
    if rule == 'MF' and len(C.tips) > 1:
        vs = W.vs; u = 0; d = 0; common = W.ALL
        for t in C.tips: u |= vs[t]['R']; d |= vs[t]['dropped']; common &= vs[t]['R']
        roster = u & ~d
        if STRICT:
            # an add is folded only where the version that adds it still meets its count without the voices
            # that any tip's line removed, over its heads' members less those removed
            lines = set()
            for t in C.tips: lines |= vs[t]['line']
            keep = common
            for zi in range(W.n):
                z = 1 << zi
                if not (roster & z) or (common & z): continue
                adders = [i for i in lines if i and W.valid(i) and vs[i]['R'] & z and not any(vs[e]['R'] & z for e in vs[i]['E'])]
                ok = bool(adders)
                for i in adders:
                    base = W.ALL
                    for e in vs[i]['E']: base &= vs[e]['R']
                    if not W.meets(vs[i]['sig'] & ~d, base & ~d): ok = False
                if ok: keep |= z
            roster = keep & ~d
        C.roster = roster
    return C
F.conclude = conclude
import os
SET = [("majority, one of four", "majority", 5, "0123", "3"), ("majority, a joiner", "majority", 5, "0123", "4"),
       ("three of five, two of them", "quorum3", 5, "01234", "34")] if not os.environ.get("PAST") else [
       ("majority of three; the adversary holds one seated key, one it will lose, and a fresh one", "majority", 4, "012", "123"),
       ("majority of four; the adversary holds two seated keys and a fresh one", "majority", 5, "0123", "234")]
KEYS = ("function", "nsf_resolved", "kept_removed", "adv_alone", "not_final", "stale", "rejoin", "nsf_now", "removed_voice")
for regime in ((True, False) if not os.environ.get('PAST') else (False,)):
    print("== adversary %s the count of every valid version" % ("below" if regime else "may have met an old count: NOT below"))
    for name, proto, n, r0, f in SET:
        res = {}
        for rule in ("M0", "MF"):
            res[rule] = F.check(rule, n, m(r0), m(f), proto, 3, 0, regime=regime)
        print("  %-28s %6d sets" % (name, res["M0"]["sets"]))
        for rule in ("M0", "MF"):
            hit = [k for k in KEYS if res[rule].get(k)]
            print("     %s: %s" % (rule, ", ".join(hit) or "nothing"))
        # where the two rosters differ, who gains
        W = F.world("M0", n, m(r0), m(f), proto, 0)
        lists_adv = adds_honest = diff = alone = 0; ex = None
        vs = W.vs
        def adders(S, z):
            """the valid versions of S that list z where no head they build on does"""
            return [i for i in S if i and W.valid(i) and vs[i]['R'] & z and not any(vs[e]['R'] & z for e in vs[i]['E'])]
        for k, level in F.enumerate_sets(W, 3):
            for S in level:
                if regime and not F.in_regime(W, S): continue
                a = orig(W, S, 'M0'); b = conclude(W, S, 'MF')
                if a.roster != b.roster:
                    diff += 1
                    gain = b.roster & ~a.roster
                    if gain & W.H: adds_honest += 1
                    if gain & W.F:
                        lists_adv += 1
                        for zi in range(W.n):
                            z = 1 << zi
                            if gain & W.F & z and all(not (vs[i]['sig'] & W.H) for i in adders(S, z)):
                                alone += 1
                                if ex is None: ex = (S, z)
                                break
        print("     sets where the fold's roster differs from the common members: %d; it seats an honest key sooner in %d; "
              "it seats an adversary key sooner in %d, and in %d of those no honest key signed the version that adds it" % (diff, adds_honest, lists_adv, alone))
        if ex:
            body, lab = F.show(W, ex[0])
            print("       first: the fold seats %s; the common members do not\n%s" % (F.names(W, ex[1]), "\n".join("         " + l for l in (body if isinstance(body, list) else str(body).split("\n"))[:8])))
