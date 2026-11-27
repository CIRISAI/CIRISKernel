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
# an infrastructure room: f1..f5 found it under quorum:3/5 (M 3, N 5); two concurrent node seatings at g, each by
# three founders (f3 on both)
F5 = ("f1", "f2", "f3", "f4", "f5")
GI5 = ST.offer("g", "f1", F5, "founder", "@", "self", cosigners=F5[1:], cohort_subkind="infrastructure",
               consensus_protocol="quorum:3/5", consensus_protocol_entrenched=True)
NA = ST.offer("na", "f1", "N1", "node", OBJ, "group", ("g",), head=("g",), counted="founder", cosigners=("f2", "f3"))
NB = ST.offer("nb", "f3", "N2", "node", OBJ, "group", ("g",), head=("g",), counted="founder", cosigners=("f4", "f5"))
INFRA = [GI5, NA, NB]
IM = lambda i="mi", tips=("na", "nb"), founders=F5, nodes=("N1", "N2"), signers=F5, word=None: ST.merge(
    i, signers[0], OBJ, tips, (), {"founder": founders, "node": nodes}, cosigners=tuple(signers[1:]), consensus_protocol=word)
# a stalled tip: on side B, f4 and f5 leave (their own ends) after nb: three founders, at most M
WB4 = ST.withdraw("w4", "f4", "g", ("nb",)); WB5 = ST.withdraw("w5", "f5", "g", ("nb",))
# a new word: side A seats f6 by a founders' amendment, restating quorum:4/6
AM6 = ST.offer("a6", "f1", "f6", "record", OBJ, "group", ("na",), head=("na",), counted="founder", role="founder",
               consensus_protocol="quorum:4/6", consensus_protocol_entrenched=True, policy=None, cosigners=("f2", "f3", "f6"))
F6 = F5 + ("f6",)
# fewer than M + 1 stated: side A removes f5 (f1..f4), side B: f4 leaves after nb; the fixed roster states f1 f2 f3
XA5 = ST.unseat("x5", "f1", "f5", "founder", OBJ, "group", ("na",), head=("na",), counted="founder", cosigners=("f2", "f3"))
WB4b = ST.withdraw("w4", "f4", "g", ("nb",))
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
    ("an infrastructure room: a merge is a founders' amendment on each tip, M (3) of that tip's active founders "
     "(five), stating the founders and the nodes: it concludes, and both nodes are seated",
     INFRA + [IM()], None, {"mi": T}, None, {"founder": F5, "node": ("N1", "N2")}, None),
    ("short on one tip: f1 and f2 with nothing of side B's but f3 (f1 f2 f3 sign) are three on each: the same; f1 "
     "and f2 alone are two: refused", INFRA + [IM(signers=("f1", "f2"))], None, {"mi": F}, None, None, None),
    ("a node never signs or counts: f1, f2 and the nodes are two founders", INFRA + [IM(signers=("f1", "f2", "N1", "N2"))],
     None, {"mi": F}, None, None, None),
    ("a merge from a stalled tip concludes nothing: on side B f4 and f5 left, three founders, at most M (the edge: a "
     "partition leaving one side at M or fewer founders does not heal by merge)",
     INFRA + [WB4, WB5, ST.merge("mi", "f1", OBJ, ("na", "nb"), (), {"founder": ("f1", "f2", "f3"), "node": ("N1", "N2")},
                                  cosigners=("f2", "f3"), names=("w4", "w5"))], None, {"mi": F}, None, None, None),
    ("the word kept: five stated founders, at most N (5): no new word", INFRA + [IM(word="quorum:3/5")], None, {"mi": T},
     None, None, None),
    ("a new word above N: side A seats f6 (quorum:4/6); six stated founders are above side B's N (5), so the merge "
     "states quorum:4/6 (M never lowered)", INFRA + [AM6, IM(tips=("a6", "nb"), founders=F6, signers=F6, word="quorum:4/6")],
     None, {"mi": T}, None, {"founder": F6, "node": ("N1", "N2")}, None),
    ("and keeping the old word with six founders concludes nothing", INFRA + [AM6, IM(tips=("a6", "nb"), founders=F6, signers=F6)],
     None, {"mi": F}, None, None, None),
    ("fewer than M + 1 stated founders is valid (f5 removed on A, f4 left on B: f1 f2 f3), and the merged room is "
     "stalled after: a node seating at the merge by f1 f2 f3 concludes nothing",
     INFRA + [XA5, WB4b, ST.merge("mi", "f1", OBJ, ("x5", "nb"), (), {"founder": ("f1", "f2", "f3"), "node": ("N1", "N2")},
                                       cosigners=("f2", "f3"), names=("w4",)),
              ST.offer("nz", "f1", "NZ", "node", OBJ, "group", ("mi",), head=("mi",), counted="founder", cosigners=("f2", "f3"))],
     None, {"mi": T, "nz": F}, None, {"founder": ("f1", "f2", "f3")}, None),
    ("tips in each other's past are no merge: x1 and y1", PART + [M("mx", ("x1", "y1"), tuple("ABCDEFGHK"))], None,
     {"mx": F}, None, None, None),
    ("a merge that leaves out a newest tip concludes nothing: x1 and y2 (y1 newer than x1)", PART + [M("mx", ("x1", "y2"))],
     None, {"mx": F}, None, None, None),
]

PLANTS = (("merge_over_fold", ST.MUT), ("merge_free_roster", ST.MUT), ("merge_blocked_by_void", "both"),
          ("merge_revives", ST.MUT), ("merge_tip_reader", ST.MUT), ("merge_states_nothing", ST.MUT),
          ("merge_consent_asked", ST.MUT), ("merge_stalled_signs", ST.MUT), ("merge_word_unread", ST.MUT))
# (merge_infra_counted is no plant: counted as an admission there, the founders' binding refuses a member-scope count
# over an infrastructure room anyway, so the explicit refusal is the stated rule and no case can tell them apart)


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


def fixture(with_refs):
    """The cases for the crate (tests/roster_merge.rs), with the answers the model gives."""
    out = []
    for name, rows, own, concl, members, duties, stale in CASES:
        refs = {}
        got = answer(rows, own, concl, members, duties, stale)
        S = CK.concluded(CK.kept(list(rows)), lambda r, P, past: ST.seat_rule(r, P, past))
        Q = ST.Seats(S, own=own)
        out.append({"name": name, "rows": with_refs(rows, refs), "refs": refs, "reader": own,
                    "concluded": got[0], "members": sorted(Q.holders("member", OBJ)),
                    "moderate": sorted(Q.holders("moderate", OBJ))})
    return {"cases": out}


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
