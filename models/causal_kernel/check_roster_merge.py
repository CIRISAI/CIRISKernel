#!/usr/bin/env python3
"""The roster merge (the Constitution's ruling; the text's `group:roster` version, CC 4.4.3.17, CC 3.1.3.2, CC 2.7.8):
a counted change naming two or more tips of one room, none in another's past, counted on EACH tip by that tip's own
members (its own line, reader-independent), stating its roster outright with fixed content, judged on the reader's
line by its own heads, reviving nothing. Cases, and a planted break for each rule.

Each case: (name, rows, reader, {row: concludes}, members, {duty: holders}, stale or None).
Run: python3 -I models/causal_kernel/check_roster_merge.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
import seat as ST  # noqa: E402
import checkpoint as CP  # noqa: E402
import check_count_heads as CH  # noqa: E402

CK = ST.CK
admit, remove, ack, ROOM = CH.admit, CH.remove, CH.ack, CH.ROOM
OBJ = "g"
T, F = True, False

# the partition (proto/roster_partition.py): the fork at P = aG; C, D and E sign on both sides
X1 = admit("x1", "H", ("A", "B", "C", "D", "E"), ("aG",))
X2 = admit("x2", "J", ("C", "D", "E", "F", "G"), ("aG",))
Y1 = admit("y1", "K", ("A", "B", "C", "D", "E", "H"), ("x1",))
Y2 = admit("y2", "L", ("C", "D", "E", "F", "G", "J"), ("x2",))
PART = ROOM + [X1, X2, Y1, Y2, ack("k1", "R1", "y1"), ack("k2", "R2", "y2")]
ALL = tuple("ABCDEFGHJKL")
MOD = {"moderate": ("A",)}
M = lambda i="m", tips=("y1", "y2"), members=ALL, duty=MOD, signers=ALL: ST.merge(
    i, signers[0], OBJ, tips, members, duty, cosigners=tuple(signers[1:]))
# a cheap tip that removed members: C..G remove A and B at aG; the honest tip x1 admits H
CR = remove("cr", "A", ("C", "D", "E", "F", "G"), ("aG",))
CR2 = remove("cr2", "B", ("C", "D", "E", "F", "G"), ("cr",))
CHEAP = ROOM + [X1, CR, CR2]
# a member's own end on one tip: D leaves (withdraws its admission) on side 2, after x2
WD = ST.withdraw("wd", "D", "aD", ("x2",))
# D leaves on side 2 before y2; y2 (without D) names its end
Y2D = admit("y2", "L", ("C", "E", "F", "G", "J"), ("x2",), ("wd",))
PARTD = ROOM + [X1, X2, Y1, WD, Y2D, ack("k1", "R1", "y1"), ack("k2", "R2", "y2")]
# side 2 removes E (B C D F G) and admits L; for R1 (at y1) that removal is void, and E stays until the merge
X2R = remove("x2", "E", ("B", "C", "D", "F", "G"), ("aG",))
Y2R = admit("y2", "L", ("B", "C", "D", "F", "G"), ("x2",))
PARTR = ROOM + [X1, X2R, Y1, Y2R, ack("k1", "R1", "y1"), ack("k2", "R2", "y2")]
NE = tuple("ABCDFGHKL")
# three tips: side 3 admits N at aG
X3 = admit("x3", "N", ("A", "B", "C", "F", "G"), ("aG",))
THREE = ROOM + [X1, X2, X3]

CASES = [
    ("the halves met: R1 reads its own side (x2 void for it)", PART, "R1", {}, set("ABCDEFGHK"), None, {"x2"}),
    ("the merge naming y1 and y2, signed by all, stating the fixed roster: concludes", PART + [M()], None, {"m": T},
     set(ALL), MOD, None),
    ("after it R1 reads one roster, and x2 stays void for it (nothing revived)", PART + [M()], "R1", {"m": T}, set(ALL),
     MOD, {"x2"}),
    ("and R2 reads the same roster", PART + [M()], "R2", {"m": T}, set(ALL), MOD, {"x1"}),
    ("later changes name it: an admission of Z at m, by nine of the eleven, concludes for R1 and R2 alike",
     PART + [M(), admit("az", "Z", tuple("ABCDEFGHJ"), ("m",))], "R2", {"az": T}, set(ALL) | {"Z"}, None, None),
    ("one side's merge (A B C D E H K) is refused: on y2 it is five of nine", PART + [M("m2", signers=tuple("ABCDEHK"))],
     "R1", {"m2": F}, set("ABCDEFGHK"), None, None),
    ("a side that will not sign: the room stays two rooms for the two reader sets, and each side acts on its own line "
     "(side 1 admits Z at y1)", PART + [M("m2", signers=tuple("ABCDEHK")), admit("z", "Z", tuple("ABCDEHK"), ("y1",))],
     "R1", {"m2": F, "z": T}, set("ABCDEFGHKZ"), None, None),
    ("the same read by R2: Z is not on its line", PART + [M("m2", signers=tuple("ABCDEHK")), admit("z", "Z", tuple("ABCDEHK"), ("y1",))],
     "R2", {"z": T}, set("ABCDEFGJL"), None, None),
    ("the content is fixed: a merge dropping L (never removed) concludes nothing", PART + [M(members=tuple("ABCDEFGHJK"))],
     None, {"m": F}, set(ALL), None, None),
    ("nor one adding Z", PART + [M(members=ALL + ("Z",))], None, {"m": F}, set(ALL), None, None),
    ("nor one stating another duty seat (B as moderator too)", PART + [M(duty={"moderate": ("A", "B")})], None, {"m": F},
     set(ALL), None, None),
    ("a cheap tip that removed A and B (C..G at aG) is not mergeable without the honest tip's count: C..G alone are "
     "five of x1's eight", CHEAP + [M("mc", ("cr2", "x1"), tuple("CDEFGH"), MOD, tuple("CDEFG"))], None, {"mc": F},
     set("CDEFG"), None, None),
    ("with x1's count too (A B C D E F G H sign; A and B, removed on cr2, are voices on x1 only): it concludes, and "
     "the removed stay removed", CHEAP + [M("mc", ("cr2", "x1"), tuple("CDEFGH"), {}, tuple("ABCDEFGH"))], None,
     {"mc": T}, set("CDEFGH"), None, None),
    ("a member's own end on one tip: D left on side 2 (its end in y2's line); the merge's fixed roster drops D (the "
     "room key's end is final)", PARTD + [M(members=tuple("ABCEFGHJKL"), signers=tuple("ABCEFGHJKL"))], "R1", {"m": T},
     set("ABCEFGHJKL"), None, None),
    ("and a merge re-seating D concludes nothing", PARTD + [M(signers=tuple("ABCEFGHJKL"))], None, {"m": F}, None, None, None),
    ("a removal on one tip, void for a reader on the other: side 2 removes E; for R1 (at y1) E stays", PARTR, "R1", {},
     set("ABCDEFGHK"), None, None),
    ("the merge states the roster outright: E, removed on y2, is out for R1 too (the merge ends the seat its line kept)",
     PARTR + [M(members=NE, signers=NE)], "R1", {"m": T}, set(NE), MOD, None),
    ("a member need not sign the merge: L's seat is its own consent on y2 (all but L sign)",
     PART + [M(signers=tuple("ABCDEFGHJK"))], "R1", {"m": T}, set(ALL), MOD, None),
    ("three tips: a merge of x1, x2 and x3, counted on each, states the union", THREE + [
        M("m3", ("x1", "x2", "x3"), tuple("ABCDEFGHJN"), MOD, tuple("ABCDEFGHJN"))], None, {"m3": T}, set("ABCDEFGHJN"), MOD, None),
    ("three tips: short on one (x3's members A..G N: four of eight sign) concludes nothing", THREE + [
        M("m3", ("x1", "x2", "x3"), tuple("ABCDEFGHJN"), MOD, tuple("ABCDHJN"))], None, {"m3": F}, None, None, None),
    ("tips in each other's past are no merge: x1 and y1", PART + [M("mx", ("x1", "y1"), tuple("ABCDEFGHK"))], None,
     {"mx": F}, None, None, None),
    ("a merge that leaves out a newest tip concludes nothing: x1 and y2 (y1 newer than x1)", PART + [M("mx", ("x1", "y2"))],
     None, {"mx": F}, None, None, None),
]

PLANTS = (("merge_over_fold", ST.MUT), ("merge_free_roster", ST.MUT), ("merge_blocked_by_void", "both"),
          ("merge_revives", ST.MUT), ("merge_tip_reader", ST.MUT), ("merge_states_nothing", ST.MUT),
          ("merge_consent_asked", ST.MUT))


def answer(rows, own, concl, members, duties, stale):
    S = CK.concluded(CK.kept(list(rows)), lambda r, P, past: ST.seat_rule(r, P, past))
    Q = ST.Seats(S, own=own)
    got = ({i: bool(S.C.get(i)) for i in concl},
           set(Q.holders("member", OBJ)) if members is not None else None,
           {d: set(Q.holders(d, OBJ)) for d in duties} if duties is not None else None,
           set(Q.stale) if stale is not None else None)
    return got


def want(concl, members, duties, stale):
    return (dict(concl), set(members) if members is not None else None,
            {d: set(v) for d, v in duties.items()} if duties is not None else None, set(stale) if stale is not None else None)


def run():
    import random
    bad = []
    for name, rows, own, concl, members, duties, stale in CASES:
        got = answer(rows, own, concl, members, duties, stale)
        if got != want(concl, members, duties, stale): bad.append("%s: got %s" % (name, got)); continue
        # order-free: the same answer in shuffled arrival orders (CK.arrive)
        rnd = random.Random(len(rows))
        for _ in range(6):
            tail = list(rows[1:]); rnd.shuffle(tail)
            S = CK.arrive([rows[0]] + tail, lambda r, P, past: ST.seat_rule(r, P, past))
            Q = ST.Seats(S, own=own)
            g2 = ({i: bool(S.C.get(i)) for i in concl}, set(Q.holders("member", OBJ)) if members is not None else None)
            if g2 != got[:2]: bad.append("%s: order %s differs" % (name, [r["id"] for r in tail])); break
    return bad


def main():
    bad = run()
    for b in bad: print(b)
    missed = []
    for p, where in PLANTS:
        sets = (ST.MUT, CP.MUT) if where == "both" else (where,)
        for m in sets: m.add(p)
        ST._READER_MEMO.clear(); ST._VOID_MEMO.clear()
        try:
            hit = next((c[0] for c in CASES if not any(c[0] in b for b in bad) and answer(*c[1:]) != want(*c[3:])), None)
        finally:
            for m in sets: m.discard(p)
            ST._READER_MEMO.clear(); ST._VOID_MEMO.clear()
        print("  plant %-24s %s" % (p, ("caught by: " + hit[:90]) if hit else "NOT CAUGHT"))
        if not hit: missed.append(p)
    ok = not bad and not missed
    print("RESULT: %s: %d cases, %d of %d planted breaks caught" % ("ok" if ok else "%d problems" % (len(bad) + len(missed)),
                                                                 len(CASES), len(PLANTS) - len(missed), len(PLANTS)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
