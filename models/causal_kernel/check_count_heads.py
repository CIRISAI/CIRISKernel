#!/usr/bin/env python3
"""
check_count_heads.py: the heads of a count, and the reader's line (the heads ruling of 2026-11-26, H1 to H8).

    H1  A count is read at the NEWEST of the heads it names (one in another named head's past is dropped), each a
        counted change over the row's own object or its founding row, and they must be exactly the newest counted
        changes over that object in the row's own past (seat.newer_head_in_past). Concurrent tips are intersected.
    H2  No `over`: a counted row is counted over its own object, and one stating another concludes nothing.
    H3  No read-through of an authored head: a self-admission (one key's row) is no head a count may name, and no
        counted change a count must name.
    H4  No exemption: every row that changes a roster names the newest counted changes over its object in its own
        past or concludes nothing: a moderator's lone removal (whose signer holds `moderate` at those heads, less a
        laying down of it in the removal's past), a self-admission, a resignation (a withdrawal of a seat over a
        room, among the rows it names), a lift (counted at the head its act names).
    H5  The text's reader's line: no test of concurrency (checkpoint.settle, checkpoint.versions); the line is read
        before the cut (seat.Seats).
    H6  A reader's own signed rows are its acknowledgements: every concluded row it signed or cosigned over the object
        (checkpoint.acknowledgements), each acknowledging the counted acts in its own past.
    H7  A counted change in a row's past that is behind an acknowledgement, also in the row's past, by one of the
        row's own signers is no head the row must name (seat.acked_behind). Never extended to a row built on it.
    H8  No caller-synthesised heads: a row of no object, a note, a cosignature naming itself is no head of a count.
    An election's seating (seat.is_election: an offer, conf group, policy ranked) names no head and is exempt from
    H1, H4 and the line; it is a counted change every later row must name. (roster-kinds' election2 replaces the
    predicate with "a seating names its election's id row".)

Each case is read as one batch and in arrival orders of its rows (every order up to six rows above the founding one,
else the batch order, its reverse and forty shuffles). A case marked OPEN states what the rules give and is a hole the
rules leave (for a reader with no row of its own). Each rule has a planted break, which must change a case's answer.

    python3 -I check_count_heads.py      exit 1 on any difference
"""
import itertools
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import seat as ST  # noqa: E402
import checkpoint as CP  # noqa: E402

CK = ST.CK
OBJ = "g"
RULE = lambda r, P, past: ST.seat_rule(r, P, past)
T, F = True, False


def admit(i, k, signers, heads, cites=()):
    """A counted admission of k (k cosigning, its own yes), counted at `heads`, naming `cites` too."""
    return ST.offer(i, signers[0], k, "member", OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
                    policy="community_invite", cosigners=tuple(signers[1:]) + ((k,) if k not in signers else ()))


def remove(i, k, signers, heads, cites=(), scope="member"):
    return ST.unseat(i, signers[0], k, scope, OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
                     policy="community_remove", cosigners=tuple(signers[1:]))


def ack(i, reader, head):
    return CK.row(i, "ack", reader, (head,), room=OBJ, head=(head,))


# a room founded by A, B and C (A holds `moderate`), grown to seven by counted admissions, each at the one before
G = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("A",)}, cosigners=("B", "C"))
ROOM = [G]
_mem, _prev = ["A", "B", "C"], "g"
for _k in "DEFG":
    ROOM.append(admit("a" + _k, _k, tuple(_mem), (_prev,)))
    _mem.append(_k)
    _prev = "a" + _k
SEVEN = frozenset("ABCDEFG")
FIVE = ("A", "B", "C", "D", "E")                         # five of the seven: at least two thirds
DC = lambda i, to, heads, cites=(): ST.offer(i, "A", to, "moderate", OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
                                             policy="duty_confer", counted="duty", cosigners=(to,))
RC = lambda heads, by, cites=(): ST.unseat("rc", by[0], "A", "moderate", OBJ, "group", tuple(heads) + tuple(cites), head=heads,
                                           policy="moderator_recall", cosigners=tuple(by[1:]))
SA = lambda i, k, heads, cites=(): ST.offer(i, k, k, "member", OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
                                            policy="open:self_admit")

# world M: m1 and m2 found the room (m1 its moderator), admit an agent's key AG and MOD; m1, the lone holder, confers
# `moderate` on MOD (md); the three admit N (an)
GM = ST.found("g", "m1", ("m1", "m2"), {"moderate": ("m1",)}, cosigners=("m2",))
AGM = dict(admit("ag", "AG", ("m1", "m2"), ("g",)), scope="agent", on=ST._slots("AG", "agent", OBJ))
AMM = admit("am", "MOD", ("m1", "m2"), ("ag",))
MDM = ST.offer("md", "m1", "MOD", "moderate", OBJ, "group", ("am",), head=("am",), policy="duty_confer", counted="duty",
               cosigners=("MOD",))
ANM = admit("an", "N", ("m1", "m2", "MOD"), ("md",))
WM = [GM, AGM, AMM, MDM, ANM]
LONE = lambda i, heads, cites=(), by="MOD": ST.unseat(i, by, "AG", "agent", OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
                                                      policy="community_remove")
WMD = ST.withdraw("wd", "MOD", "md", ("an",))                 # MOD lays its `moderate` seat down, naming the newest change
O1 = CK.row("o1", "answer", "m1", ("xl",), of="xl", says="object")
O2 = CK.row("o2", "answer", "m2", ("xl",), of="xl", says="object")
LIFT = lambda heads: ST.offer("lf", "m1", "AG", "agent", OBJ, "group", ("xl", "o1", "o2") + tuple(heads), head=tuple(heads),
                              content="xl", policy="moderation_overturn", cosigners=("m2", "AG"))


def elect(i, k, heads):
    """An election's seating of k to `moderate`: ballots of B and C ranking k first, and the offer counting them."""
    bs = [ST.R("b" + v + i, "ballot", v, tuple(heads), ranking=(k, "C")) for v in ("B", "C")]
    return bs + [ST.offer(i, "B", k, "moderate", OBJ, "group", tuple(heads) + tuple(b["id"] for b in bs), head=tuple(heads),
                          policy="moderator_election", options=(k, "C"), cosigners=(k,))]


H1, H2, H3, H4, H5, H6, H7, H8, EL, OPEN = ("H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "election", "OPEN")
# (rule, name, rows, reader, {row: concludes}, {scope: holders}, stale)
CASES = [
    # ---- H1 ---------------------------------------------------------------------------------------------------------
    (H1, "a counted admission names the founding head and has the newest admission in its own past",
     ROOM + [admit("ax", "X", ("A", "B"), ("g",), ("aG",))], None, {"ax": F}, {"member": SEVEN}, set()),
    (H1, "the same admission at the newest head, by five of the seven",
     ROOM + [admit("ax", "X", FIVE, ("aG",))], None, {"ax": T}, {"member": SEVEN | {"X"}}, set()),
    (H1, "a counted removal names the founding head and has the newest admission in its own past",
     ROOM + [remove("xg", "G", ("A", "B"), ("g",), ("aG",))], None, {"xg": F}, {"member": SEVEN}, set()),
    (H1, "the same removal at the newest head, by five of the seven",
     ROOM + [remove("xg", "G", FIVE, ("aG",))], None, {"xg": T}, {"member": SEVEN - {"G"}}, set()),
    (H1, "a counted removal names the founding head and the newest admission together",
     ROOM + [remove("xg", "G", ("A", "B"), ("g", "aG"))], None, {"xg": F}, {"member": SEVEN}, set()),
    (H1, "a counted admission names the founding head and the newest admission together",
     ROOM + [admit("ax", "X", ("A", "B"), ("g", "aG"))], None, {"ax": F}, {"member": SEVEN}, set()),
    (H1, "the same removal, for a reader that acknowledged the newest admission",
     ROOM + [ack("ak", "R", "aG"), remove("xg", "G", ("A", "B"), ("g", "aG"))], "R", {"xg": F}, {"member": SEVEN}, set()),
    (H1, "a counted removal by three names the fourth member's admission and the newest admission together",
     ROOM + [remove("xg", "G", ("A", "B", "C"), ("aD", "aG"))], None, {"xg": F}, {"member": SEVEN}, set()),
    (H1, "a recall of the moderator names the founding head and the newest admission together",
     ROOM + [RC(("g", "aG"), ("B", "C"))], None, {"rc": F}, {"moderate": {"A"}}, set()),
    (H1, "a recall of the moderator names the founding head and has the newest admission in its own past",
     ROOM + [RC(("g",), ("B", "C"), ("aG",))], None, {"rc": F}, {"moderate": {"A"}}, set()),
    (H1, "the same recall at the newest head, by five of the seven",
     ROOM + [RC(("aG",), ("B", "C", "D", "E", "F"))], None, {"rc": T}, {"moderate": set()}, set()),
    (H1, "a duty conferral by the lone holder names the founding head and has the newest admission in its own past",
     ROOM + [DC("dc", "B", ("g",), ("aG",))], None, {"dc": F}, {"moderate": {"A"}}, set()),
    (H1, "the same duty conferral at the newest head",
     ROOM + [DC("dc", "B", ("aG",))], None, {"dc": T}, {"moderate": {"A", "B"}}, set()),
    (H1, "two admissions at the newest head, concurrent, and a removal by five naming both tips (intersected)",
     ROOM + [admit("aX", "X", FIVE, ("aG",)), admit("aY", "Y", FIVE, ("aG",)), remove("xg", "G", FIVE, ("aX", "aY"))], None,
     {"aX": T, "aY": T, "xg": T}, {"member": (SEVEN | {"X", "Y"}) - {"G"}}, set()),
    (H1, "a removal at the founding head that has not seen the admissions (concurrent with them) concludes; no reader",
     ROOM + [remove("xg", "G", ("A", "B"), ("g",))], None, {"xg": T}, {"member": SEVEN - {"G"}}, set()),
    (H1, "a counted change of another room in a row's past moves no head of this one",
     ROOM + [ST.found("h", "A", ("A",), {}),
             ST.offer("ah", "A", "B", "member", "h", "group", ("h",), head=("h",), policy="community_invite", cosigners=("B",)),
             remove("xg", "G", FIVE, ("aG",), ("ah",))], None, {"ah": T, "xg": T}, {"member": SEVEN - {"G"}}, set()),
    # ---- H2 ---------------------------------------------------------------------------------------------------------
    (H2, "an admission in a second room stating that it is counted over the first room's roster",
     ROOM + [ST.found("h", "A", ("A",), {}),
             ST.offer("ox", "A", "X", "member", "h", "group", ("h", "aG"), head=("h",), over="g", policy="community_invite",
                      cosigners=("X",))], None, {"ox": F}, {}, set()),
    (H2, "a row counted over another object it writes itself (i3): an outsider's self-admission over its own note",
     ROOM + [ack("x", "Z", "g"), dict(SA("y", "Z", ("x",), ("aG",)), over="x")], None, {"y": F}, {"member": SEVEN}, set()),
    # ---- H3 ---------------------------------------------------------------------------------------------------------
    (H3, "an outsider admits itself at the newest head; a removal by five names that self-admission as its head",
     ROOM + [SA("sa", "Z", ("aG",)), remove("xg", "G", FIVE, ("sa",))], None, {"sa": T, "xg": F}, {"member": SEVEN | {"Z"}}, set()),
    (H3, "the same removal names the fourth member's admission and the self-admission together",
     ROOM + [SA("sa", "Z", ("aG",)), remove("xg", "G", FIVE, ("aD", "sa"))], None, {"sa": T, "xg": F}, {"member": SEVEN | {"Z"}}, set()),
    (H3, "the same removal at the newest admission, the self-admission in its past: the self-admitted key is no voice of it",
     ROOM + [SA("sa", "Z", ("aG",)), remove("xg", "G", FIVE, ("aG",), ("sa",))], None, {"sa": T, "xg": T},
     {"member": (SEVEN | {"Z"}) - {"G"}}, set()),
    (H3, "a founder's own 'self-admission' at the founding head (i1) is no head for a removal by two",
     ROOM + [SA("y", "A", ("g",), ("aG",)), remove("xg", "G", ("A", "B"), ("y",))], None, {"y": F, "xg": F}, {"member": SEVEN}, set()),
    # ---- H4 ---------------------------------------------------------------------------------------------------------
    (H4, "a moderator's lone removal of an agent's key at its seat's head, with a later admission in its own past",
     WM + [LONE("xl", ("md",), ("an",))], None, {"xl": F}, {"member": {"m1", "m2", "MOD", "N"}, "agent": {"AG"}}, set()),
    (H4, "the same lone removal at the newest head",
     WM + [LONE("xl", ("an",))], None, {"xl": T}, {"member": {"m1", "m2", "MOD", "N"}, "agent": set()}, set()),
    (H4, "a moderator lays its seat down and then removes an agent's key alone at the newest head",
     WM + [WMD, LONE("xl", ("an",), ("wd",))], None, {"wd": T, "xl": F}, {"moderate": {"m1"}, "agent": {"AG"}}, set()),
    (H4, "the same removal concurrent with the moderator's laying down: it concludes",
     WM + [WMD, LONE("xl", ("an",))], None, {"wd": T, "xl": T}, {"moderate": {"m1"}}, set()),
    (H4, "an outsider's self-admission at the founding head, with the newest admission in its own past",
     ROOM + [SA("sa", "Z", ("g",), ("aG",))], None, {"sa": F}, {"member": SEVEN}, set()),
    (H4, "a member resigns, its withdrawal naming its admission and a note with a later admission in its past",
     ROOM + [admit("aH", "H", tuple(sorted(SEVEN)), ("aG",)), CK.row("k", "note", "D", ("aH",)),
             ST.withdraw("wg", "G", "aG", ("aG", "k"))], None, {"wg": F}, {"member": SEVEN | {"H"}}, set()),
    (H4, "the same resignation naming the later admission: it concludes",
     ROOM + [admit("aH", "H", tuple(sorted(SEVEN)), ("aG",)), ST.withdraw("wg", "G", "aG", ("aG", "aH"))], None,
     {"wg": T}, {"member": (SEVEN | {"H"}) - {"G"}}, set()),
    (H4, "the members' lift at the head the removal names, older than the removal itself",
     WM + [LONE("xl", ("an",)), O1, O2, LIFT(("an",))], None, {"xl": T, "lf": F}, {"agent": set()}, set()),
    (H4, "the members' lift at the removal, the newest counted change in its past: the key is seated again",
     WM + [LONE("xl", ("an",)), O1, O2, LIFT(("xl",))], None, {"xl": T, "lf": T}, {"agent": {"AG"}}, set()),
    # ---- H5: the line before the cut --------------------------------------------------------------------------------
    (H5, "a removal at the founding head concurrent with the admissions, for a reader that acknowledged the newest: it is "
         "behind the line and cuts nothing for that reader",
     ROOM + [ack("ak", "R", "aG"), remove("xg", "G", ("A", "B"), ("g",))], "R", {"xg": T}, {"member": SEVEN}, {"xg"}),
    (H5, "a reader acknowledged an admission; a removal of the admitted key at the same head, concurrent with it, and a "
         "sibling admission: the line, read with every row counting, holds the removal and the sibling behind it",
     ROOM + [admit("ax", "X", FIVE, ("aG",)), remove("xx", "X", FIVE, ("aG",)), admit("ay", "Y", FIVE, ("aG",)),
             ack("ak", "R", "ax")], "R", {"ax": T, "xx": T, "ay": T}, {"member": SEVEN | {"X"}}, {"xx", "ay"}),
    # ---- H6 ---------------------------------------------------------------------------------------------------------
    (H6, "the same removal, for a founder that signed every admission and wrote no acknowledgement row",
     ROOM + [remove("xg", "G", ("A", "B"), ("g",))], "C", {"xg": T}, {"member": SEVEN}, {"xg"}),
    (H6, "a cheap concurrent tip (A's lone duty conferral at the founding head) and a removal by two naming it and the "
         "newest admission, for the newest member G (its own admission is its acknowledgement)",
     ROOM + [DC("dc", "B", ("g",)), remove("xg", "G", ("A", "B"), ("dc", "aG"))], "G", {"dc": T, "xg": T}, {"member": SEVEN}, {"dc", "xg"}),
    (H6, "a minority packs the room from the founding past (two admissions chained) and removes D with them, for D",
     ROOM + [admit("p1", "X1", ("A", "B"), ("g",)), admit("p2", "X2", ("A", "B", "X1"), ("p1",)),
             remove("xd", "D", ("A", "B", "X1", "X2"), ("aG", "p2"))], "D", {"p1": T, "p2": T, "xd": T}, {"member": SEVEN},
     {"p1", "p2", "xd"}),
    # ---- H7 ---------------------------------------------------------------------------------------------------------
    (H7, "the cheap tip in the past of an honest removal by five at the newest admission: behind its signers' "
         "acknowledgements, it need not be named",
     ROOM + [DC("dc", "B", ("g",)), remove("xg", "G", FIVE, ("aG",), ("dc",))], None, {"dc": T, "xg": T},
     {"member": SEVEN - {"G"}}, set()),
    (H7, "a row built on the cheap tip is no change behind an acknowledgement: the honest removal must name it",
     ROOM + [DC("dc", "B", ("g",)), ST.offer("dc2", "A", "C", "moderate", OBJ, "group", ("dc",), head=("dc",), policy="duty_confer",
                                             counted="duty", cosigners=("B", "C")), remove("xg", "G", FIVE, ("aG",), ("dc2",))], None,
     {"dc": T, "dc2": T, "xg": F}, {"member": SEVEN}, set()),
    # ---- H8 ---------------------------------------------------------------------------------------------------------
    (H8, "a removal by five names a note naming the newest admission as its head",
     ROOM + [CK.row("v", "note", "D", ("aG",)), remove("xg", "G", FIVE, ("v",))], None, {"xg": F}, {"member": SEVEN}, set()),
    (H8, "a removal by five names a cosignature whose `of` is itself",
     ROOM + [ST.R("v", "cosign", "D", ("aG",), of="v"), remove("xg", "G", FIVE, ("v",))], None, {"xg": F}, {"member": SEVEN}, set()),
    # ---- an election's seating --------------------------------------------------------------------------------------
    (EL, "an election's seating at the founding head, with the newest admission in its past: exempt, it seats D",
     ROOM + [ST.withdraw("lm", "A", "g", ("g", "aG"), scope="moderate")] + elect("se", "D", ("aG",)), None,
     {"se": T}, {"moderate": {"D"}}, set()),
    (EL, "the same seating, concurrent with a later admission a reader acknowledged: the line never holds a seating behind",
     ROOM + [admit("aH", "H", tuple(sorted(SEVEN)), ("aG",)), ack("ak", "R", "aH"),
             ST.withdraw("lm", "A", "g", ("g", "aG"), scope="moderate")] + elect("se", "D", ("aG",)), "R",
     {"se": T}, {"moderate": set()}, set()),        # not stale; at two tips the fold seats no election (election2's)
    (EL, "a later admission at the newest admission, leaving the seating unnamed in its past (it names the ballots)",
     ROOM + [ST.withdraw("lm", "A", "g", ("g", "aG"), scope="moderate")] + elect("se", "D", ("aG",)) +
     [admit("ax", "X", FIVE, ("aG",), ("se",))], None, {"se": T, "ax": F}, {"moderate": {"D"}, "member": SEVEN}, set()),
    # ---- holes the rules leave: OPEN, for a reader with no row of its own ---------------------------------------------
    (OPEN, "the cheap tip and the removal by two at (tip, newest), for a reader with no row: concurrent tips intersect "
           "to the founders' roster, and G is out",
     ROOM + [DC("dc", "B", ("g",)), remove("xg", "G", ("A", "B"), ("dc", "aG"))], None, {"dc": T, "xg": T},
     {"member": SEVEN - {"G"}}, set()),
    (OPEN, "the packed removal of D, for a reader with no row",
     ROOM + [admit("p1", "X1", ("A", "B"), ("g",)), admit("p2", "X2", ("A", "B", "X1"), ("p1",)),
             remove("xd", "D", ("A", "B", "X1", "X2"), ("aG", "p2"))], None, {"p1": T, "p2": T, "xd": T},
     {"member": (SEVEN | {"X1", "X2"}) - {"D"}}, set()),
]

# the reader's line over roster versions (checkpoint.versions, line::versions), on worlds of roster_fork's rule M
# (set-aside: a version may have in its past a version it does not extend). Each: (name, extends, past, roster of each
# version, the reader's acknowledged version, the versions that count, the roster of the tips).
VERSIONS = (
    ("a version extends the founding version with the acknowledged one in its past", ((), (0,), (0,)), ((), (0,), (0, 1)),
     ("0123", "012", "012"), 1, {0, 1}, "012"),
    ("the same, and a version over it admits a member", ((), (0,), (0,), (2,)), ((), (0,), (0, 1), (0, 1, 2)),
     ("0123", "012", "012", "0124"), 1, {0, 1}, "012"),
    ("the same, and a version over it removes a member", ((), (0,), (0,), (2,)), ((), (0,), (0, 1), (0, 1, 2)),
     ("0123", "01234", "01234", "0124"), 1, {0, 1}, "01234"),
)
# the seat's line read directly (checkpoint.settle over concluded acts): an act with the acknowledged act in its past
# that names a head older than it. The rules above refuse such a row before the line reads it, so the line is read here
LINE = [G, admit("a1", "D", ("A", "B", "C"), ("g",)), dict(admit("a2", "E", ("A", "B"), ("g",), ("a1",)))]


def version_answer(E, past, ack):
    Tv, _ = CP.versions(list(range(len(E))), {i: E[i] for i in range(len(E))}, {i: set(past[i]) for i in range(len(E))},
                        lambda i: True, ack, False)
    return set(Tv)


def version_roster(past, R, Tv):
    covered = set().union(*[set(past[i]) for i in Tv]) if Tv else set()
    tips = [i for i in Tv if i not in covered]
    return "".join(sorted(set.intersection(*[set(R[i]) for i in tips]))) if tips else ""


def line_answer():
    S = CK.concluded(CK.kept(list(LINE) + [CK.row("ak", "ack", "R", ("a1",), room=OBJ, head=("a1",))]), lambda r, P, past: True)
    return frozenset(CP.void(S, CP.EVERY, "R"))


PLANTS = (("count_heads_unread", ST.MUT), ("all_heads_read", ST.MUT), ("head_any_row", ST.MUT), ("past_disjunct_off", ST.MUT),
          ("changes_any_object", ST.MUT), ("over_allowed", ST.MUT), ("authored_heads", ST.MUT), ("lone_exempt", ST.MUT),
          ("lone_leaving_unread", ST.MUT), ("resign_exempt", ST.MUT), ("line_concurrent", CP.MUT), ("versions_concurrent", CP.MUT),
          ("cut_before_line", ST.MUT), ("line_void_unlisted", ST.MUT), ("line_after_cut", ST.MUT), ("acks_only", CP.MUT),
          ("ack_excuses_none", ST.MUT), ("election_by_line", ST.MUT))


def answer(S, own, concl, holds):
    Q = ST.Seats(S, own=own)
    return ({i: bool(S.C.get(i)) for i in concl}, {sc: frozenset(Q.holders(sc, OBJ)) for sc in holds}, frozenset(Q.stale))


def orders(rows):
    tail = rows[1:]
    if len(tail) <= 6:
        return [list(p) for p in itertools.permutations(tail)]
    rnd = random.Random(len(tail))
    out = [tail[::-1]]
    for _ in range(40):
        p = list(tail)
        rnd.shuffle(p)
        out.append(p)
    return out


def want(concl, holds, stale):
    return (dict(concl), {sc: frozenset(v) for sc, v in holds.items()}, frozenset(stale))


def run_all():
    return [answer(CK.concluded(CK.kept(list(rows)), RULE), own, concl, holds) for _, _, rows, own, concl, holds, _ in CASES] + \
        [(version_answer(E, past, a), version_roster(past, R, version_answer(E, past, a))) for _, E, past, R, a, *_ in VERSIONS] + \
        [line_answer()]


def main():
    problems, n = [], 0
    for rule, name, rows, own, concl, holds, stale in CASES:
        got = answer(CK.concluded(CK.kept(list(rows)), RULE), own, concl, holds)
        if got != want(concl, holds, stale):
            problems.append("%s %s: got %s" % (rule, name, got))
        for p in orders(rows):
            n += 1
            if answer(CK.arrive([rows[0]] + p, RULE), own, concl, holds) != got:
                problems.append("%s: order %s differs" % (name, [r["id"] for r in p]))
                break
    for name, E, past, R, a, want_t, want_r in VERSIONS:
        t = version_answer(E, past, a)
        if (t, version_roster(past, R, t)) != (want_t, want_r):
            problems.append("H5 %s: got %s, roster %s" % (name, t, version_roster(past, R, t)))
    if line_answer() != frozenset({"a2"}):
        problems.append("H5 the seat's line read directly: void %s" % sorted(line_answer()))
    labels = ["%s %s" % (c[0], c[1]) for c in CASES] + ["H5 " + v[0] for v in VERSIONS] + ["H5 the seat's line read directly"]
    now, caught = run_all(), 0
    for p, m in PLANTS:
        m.add(p)
        try:
            hit = [lab for lab, a, b in zip(labels, now, run_all()) if a != b]
        finally:
            m.discard(p)
        caught += bool(hit)
        print("  plant %-22s %s" % (p, "caught by: %s" % hit[0][:120] if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % p)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases (%d OPEN), %d of roster versions, the line read directly, %d arrival orders, %d of %d planted "
          "breaks caught" % ("ok" if not problems else "%d problems" % len(problems), len(CASES),
                             sum(c[0] == OPEN for c in CASES), len(VERSIONS), n, caught, len(PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
