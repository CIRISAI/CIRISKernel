#!/usr/bin/env python3
"""
check_count_heads.py: a count is read at the newest counted heads in its own past; one reader's line; the line
before the cut.

    W1  A counted row over a roster (an offer or an unseat conferred by a count, naming a head) concludes only at
        the newest counted heads of that roster in its own past: a counted row whose own past holds a counted change
        of the roster that is neither one of the heads it names nor in the past of one concludes nothing
        (seat.newer_head_in_past). A counted change is what the reader's line reads as a counted act
        (checkpoint.is_counted_act): an offer or unseat conferred by a count on the same object that names a head,
        of any scope: an admission, a removal, a duty conferral or withdrawal, a recall. A row that has not seen the
        newer head (concurrent with it) still concludes and is left to the line and the fold. A lift (the members'
        re-seating after a moderator's lone removal) is counted at the head its act names, and is read as before. A
        moderator's lone removal is an act of one key and is read as before. A cosignature is a voice only where the
        counted row names it, so the row's own past holds the cosignature's: no separate reading is needed.
    W2  One reader's line, the text's (CC 2.7.8: "holds void every counted act that names an older head and is not in
        that head's past, however many rows it has"): no test of concurrency (checkpoint.settle, line.rs settle). It
        is the rule head.rs and purge.py read.
    W3  A counted act void for a reader cuts nothing for that reader: the line is read before the cut (seat.Seats).
        For a reader with no acknowledgement a removal at a tip is read as before (the fold), and a case states it.

Each case is read as one batch and in arrival orders of its rows (every order up to six rows above the founding one,
else the batch order, its reverse and forty shuffles). Each case states the answer before this change too, read with
the three planted breaks below switched on together.

Planted breaks, each of which must change a case's answer:
    count_heads_unread   a counted row's count read at the heads it names, whatever is in its past (W1)
    line_concurrent      the line voids only acts concurrent with an act of it (W2)
    cut_before_line      the cut is read before the reader's line (W3)
    all_heads_read       a count read at every head it names, not the newest of them
    head_any_row         a named head may be any row, not only a counted change or the founding row
    heads_of_obj         the newest heads tested on the row's own object, not the object it is counted over
    lift_exemption_off   the new line reads the members' lift too (the exemption pending the lift follow-up)

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


def remove(i, k, signers, heads, cites=()):
    return ST.unseat(i, signers[0], k, "member", OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
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

DC = lambda heads: ST.offer("dc", "A", "B", "moderate", OBJ, "group", ("aG",), head=heads, policy="duty_confer",
                            counted="duty", cosigners=("B",))
RC = lambda heads, by: ST.unseat("rc", by[0], "A", "moderate", OBJ, "group", ("aG",), head=heads,
                                 policy="moderator_recall", cosigners=tuple(by[1:]))
AH = admit("aH", "H", tuple(SEVEN), ("aG",))             # an eighth member, at the newest head
CS = ST.cosign("cs", "C", "xs", ("aG", "aH"))            # a cosignature of xs that has aH in its own past
XS = ST.unseat("xs", "A", "G", "member", OBJ, "group", ("aG", "cs"), head=("aG",), policy="community_remove",
               cosigners=("B", "D", "E"))

# world M (check_agent_removal's world A): m1, m2, an agent's key AG, MOD a member conferred `moderate`
GM = ST.offer("g", "m1", ("m1", "m2"), "member", "@", "self", cosigners=("m2",))
AGM = admit("ag", "AG", ("m1", "m2"), ("g",))
AGM = dict(AGM, scope="agent", on=ST._slots("AG", "agent", OBJ))
AMM = admit("am", "MOD", ("m1", "m2"), ("ag",))
MDM = ST.offer("md", "m1", "MOD", "moderate", OBJ, "group", ("am",), head=("am",), policy="community_invite",
               cosigners=("m2", "MOD"))
ANM = admit("an", "N", ("m1", "m2", "MOD"), ("md",))      # a counted admission after the moderator's seat
XLM = ST.unseat("xl", "MOD", "AG", "agent", OBJ, "group", ("an",), head=("md",), policy="community_remove")
WM = [GM, AGM, AMM, MDM, ANM]
# MOD lays its `moderate` seat down (its own withdrawal of the conferral), and then removes AG alone at the head md
WDM = ST.withdraw("wd", "MOD", "md", ("md",))
XLW = lambda names: ST.unseat("xl", "MOD", "AG", "agent", OBJ, "group", names, head=("md",), policy="community_remove")
import check_agent_removal as AR  # noqa: E402   world A: the lift

# (name, rows, reader, {row: concludes}, {scope: holders}, stale, the answer before: (concludes, holders, stale))
CASES = [
    ("a counted admission names the founding head and has the newest admission in its own past",
     ROOM + [admit("ax", "X", ("A", "B"), ("g",), ("aG",))], None,
     {"ax": F}, {"member": SEVEN}, set(), ({"ax": T}, {"member": SEVEN | {"X"}}, set())),
    ("the same admission at the newest head, by five of the seven",
     ROOM + [admit("ax", "X", FIVE, ("aG",))], None, {"ax": T}, {"member": SEVEN | {"X"}}, set(), None),
    ("a counted removal names the founding head and has the newest admission in its own past",
     ROOM + [remove("xg", "G", ("A", "B"), ("g",), ("aG",))], None,
     {"xg": F}, {"member": SEVEN}, set(), ({"xg": T}, {"member": SEVEN - {"G"}}, set())),
    ("the same removal at the newest head, by five of the seven",
     ROOM + [remove("xg", "G", FIVE, ("aG",))], None, {"xg": T}, {"member": SEVEN - {"G"}}, set(), None),
    ("a duty conferral by the lone holder names the founding head and has the newest admission in its own past",
     ROOM + [DC(("g",))], None, {"dc": F}, {"moderate": {"A"}}, set(), ({"dc": T}, {"moderate": {"A", "B"}}, set())),
    ("the same duty conferral at the newest head",
     ROOM + [DC(("aG",))], None, {"dc": T}, {"moderate": {"A", "B"}}, set(), None),
    ("a recall of the moderator names the founding head and has the newest admission in its own past",
     ROOM + [RC(("g",), ("B", "C"))], None, {"rc": F}, {"moderate": {"A"}}, set(), ({"rc": T}, {"moderate": set()}, set())),
    ("the same recall at the newest head, by five of the seven",
     ROOM + [RC(("aG",), ("B", "C", "D", "E", "F"))], None, {"rc": T}, {"moderate": set()}, set(), None),
    ("a counted removal at the newest head whose cosignature has a later admission in its own past",
     ROOM + [AH, CS, XS], None, {"xs": F}, {"member": SEVEN | {"H"}}, set(),
     ({"xs": T}, {"member": (SEVEN | {"H"}) - {"G"}}, set())),
    ("a removal at the founding head that has not seen the admissions (concurrent with them) concludes; no reader",
     ROOM + [remove("xg", "G", ("A", "B"), ("g",))], None, {"xg": T}, {"member": SEVEN - {"G"}}, set(), None),
    ("the same, for a reader that acknowledged the newest head: the removal is behind its line and cuts nothing for it",
     ROOM + [ack("ak", "R", "aG"), remove("xg", "G", ("A", "B"), ("g",))], "R", {"xg": T}, {"member": SEVEN}, {"xg"},
     ({"xg": T}, {"member": SEVEN - {"G"}}, {"xg"})),
    ("a moderator's lone removal of an agent's key at its seat's head, with a later admission in its own past; no reader",
     WM + [XLM], None, {"xl": T}, {"member": {"m1", "m2", "MOD", "N"}, "agent": set()}, set(), None),
    ("the same, for a reader that acknowledged the later admission: the removal names an older head and is not in the "
     "admission's past, so it is behind the line, and cuts nothing for that reader",
     WM + [ack("ak", "m1", "an"), XLM], "m1", {"xl": T}, {"member": {"m1", "m2", "MOD", "N"}, "agent": {"AG"}}, {"xl"},
     ({"xl": T}, {"member": {"m1", "m2", "MOD", "N"}, "agent": set()}, set())),
    # a count is read at the newest of the heads it names, and those must be the newest counted heads of the roster in
    # its own past, each a counted change or the founding row
    ("a counted removal names the founding head and the newest admission together",
     ROOM + [remove("xg", "G", ("A", "B"), ("g", "aG"))], None, {"xg": F}, {"member": SEVEN}, set(),
     ({"xg": T}, {"member": SEVEN - {"G"}}, set())),
    ("a counted admission names the founding head and the newest admission together",
     ROOM + [admit("ax", "X", ("A", "B"), ("g", "aG"))], None, {"ax": F}, {"member": SEVEN}, set(),
     ({"ax": T}, {"member": SEVEN | {"X"}}, set())),
    ("the same removal, for a reader that acknowledged the newest admission",
     ROOM + [ack("ak", "R", "aG"), remove("xg", "G", ("A", "B"), ("g", "aG"))], "R", {"xg": F}, {"member": SEVEN}, set(),
     ({"xg": T}, {"member": SEVEN - {"G"}}, set())),
    ("a counted removal by three names the fourth member's admission and the newest admission together",
     ROOM + [remove("xg", "G", ("A", "B", "C"), ("aD", "aG"))], None, {"xg": F}, {"member": SEVEN}, set(),
     ({"xg": T}, {"member": SEVEN - {"G"}}, set())),
    ("a recall of the moderator names the founding head and the newest admission together",
     ROOM + [RC(("g", "aG"), ("B", "C"))], None, {"rc": F}, {"moderate": {"A"}}, set(), ({"rc": T}, {"moderate": set()}, set())),
    ("a counted removal by five of the seven names a row that is no counted change as its head",
     ROOM + [CK.row("k", "note", "D", ("aG",)), remove("xg", "G", FIVE, ("k",))], None, {"xg": F}, {"member": SEVEN}, set(),
     ({"xg": T}, {"member": SEVEN - {"G"}}, set())),
    ("two admissions at the newest head, concurrent, and a removal by five naming both tips",
     ROOM + [admit("aX", "X", FIVE, ("aG",)), admit("aY", "Y", FIVE, ("aG",)), remove("xg", "G", FIVE, ("aX", "aY"))], None,
     {"aX": T, "aY": T, "xg": T}, {"member": (SEVEN | {"X", "Y"}) - {"G"}}, set(), None),
    # the count is read over the object it is taken over (`over`), and so are its newest heads
    ("an admission in a second room counted over the first room's roster names the first room's founding head, with its "
     "newest admission in its own past",
     ROOM + [ST.found("h", "A", ("A",), {}), ST.offer("ox", "A", "X", "member", "h", "group", ("g", "aG", "h"), head=("g",),
                                                    over="g", policy="community_invite", cosigners=("B", "X"))], None,
     {"ox": F}, {}, set(), ({"ox": T}, {}, set())),
    ("an admission in a second room counted over the first room's roster names a counted change of the second room as its head",
     ROOM + [ST.found("h", "A", ("A",), {}),
             ST.offer("ah", "A", "B", "member", "h", "group", ("h", "aG"), head=("h",), policy="community_invite", cosigners=("B",)),
             ST.offer("ox", "A", "X", "member", "h", "group", ("ah",), head=("ah",), over="g", policy="community_invite",
                      cosigners=FIVE[1:] + ("X",))], None, {"ah": T, "ox": F}, {}, set(), ({"ah": T, "ox": T}, {}, set())),
    # the reader's line is read with every row counting (W3). The rows of a review: a reader acknowledged an admission
    # that a removal cuts on main, and a sibling admission at the same head. The removal names a row that is no counted
    # change among its heads, so it now concludes nothing, the acknowledged admission stands, and the sibling is behind
    # the line. (Asked of the Constitution: whether a cut act of the line leaves its siblings behind. With every head a
    # counted change, a removal that cuts the acknowledged act is concurrent with it and built on an act behind it.)
    ("a reader acknowledged an admission; a removal of the admitted key names a note among its heads; a sibling admission",
     ROOM + [admit("ax", "X", FIVE, ("aG",)), CK.row("k", "note", "D", ("aG",)), remove("xx", "X", FIVE, ("aG", "k")),
             admit("ay", "Y", FIVE, ("aG",)), ack("ak", "R", "ax")], "R",
     {"ax": T, "xx": F, "ay": T}, {"member": SEVEN | {"X"}}, {"ay"},
     ({"ax": T, "xx": T, "ay": T}, {"member": SEVEN | {"Y"}}, set())),
    ("the same removal named at the newest head alone, concurrent with the acknowledged admission",
     ROOM + [admit("ax", "X", FIVE, ("aG",)), CK.row("k", "note", "D", ("aG",)), remove("xx", "X", FIVE, ("aG",), ("k",)),
             admit("ay", "Y", FIVE, ("aG",)), ack("ak", "R", "ax")], "R",
     {"ax": T, "xx": T, "ay": T}, {"member": SEVEN | {"X"}}, {"xx", "ay"},
     ({"ax": T, "xx": T, "ay": T}, {"member": SEVEN | {"Y"}}, set())),
    # what the code gives (the end rule: a lone removal is in force only while its author holds the standing it acts
    # under; seat.out_of_force), with the author's withdrawal of its seat in the removal's past, and concurrent with it
    ("a moderator lays down its seat and then removes an agent's key alone, naming the head where it held the seat",
     [GM, AGM, AMM, MDM, WDM, XLW(("md", "wd"))], None, {"xl": T, "wd": T}, {"moderate": set(), "agent": {"AG"}}, set(), None),
    ("the same removal concurrent with the moderator's withdrawal of its seat",
     [GM, AGM, AMM, MDM, WDM, XLW(("md",))], None, {"xl": T, "wd": T}, {"moderate": set(), "agent": {"AG"}}, set(), None),
    # the lift, read as before, pending the lift follow-up (it is to name the newest counted heads in its own past and
    # be counted over the members seated both at the act's head and at its own, the author apart): today, for a
    # reader that acknowledged the removal, the re-seating counts and the agent's key is back. The new line without the
    # exemption (plant lift_exemption_off) gave: the re-seating stale for that reader, and the agent's key off its roster
    ("the members' lift of a lone removal, for a reader that acknowledged the removal (pending the lift follow-up)",
     AR.A + [AR.XA, AR.O1, AR.O2, AR.RSA, ack("ak", "m1", "x")], "m1", {"rs": T}, {"agent": {"AG"}}, set(), None),
]
PLANTS = (("count_heads_unread", ST.MUT), ("line_concurrent", CP.MUT), ("cut_before_line", ST.MUT), ("all_heads_read", ST.MUT),
          ("head_any_row", ST.MUT), ("heads_of_obj", ST.MUT))
GUARDS = (("lift_exemption_off", ST.MUT),)      # a break of the lift's exemption, pending the lift follow-up


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
    return [answer(CK.concluded(CK.kept(list(rows)), RULE), own, concl, holds) for _, rows, own, concl, holds, _, _ in CASES]


def main():
    problems, n = [], 0
    for name, rows, own, concl, holds, stale, before in CASES:
        got = answer(CK.concluded(CK.kept(list(rows)), RULE), own, concl, holds)
        if got != want(concl, holds, stale):
            problems.append("%s: got %s" % (name, got))
        for p in orders(rows):
            n += 1
            if answer(CK.arrive([rows[0]] + p, RULE), own, concl, holds) != got:
                problems.append("%s: order %s differs" % (name, [r["id"] for r in p]))
                break
    # the answer before: the rules switched off together
    for _, m in PLANTS: m.add(_)
    try:
        old = run_all()
    finally:
        for p, m in PLANTS: m.discard(p)
    changed = 0
    for (name, rows, own, concl, holds, stale, before), o in zip(CASES, old):
        b = want(*before) if before else want(concl, holds, stale)
        if o != b:
            problems.append("%s: before the change got %s, the case states %s" % (name, o, b))
        changed += before is not None
    caught = 0
    now = run_all()
    for p, m in PLANTS + GUARDS:
        m.add(p)
        try:
            hit = [c[0] for c, a, b in zip(CASES, now, run_all()) if a != b]
        finally:
            m.discard(p)
        caught += bool(hit)
        print("  plant %-20s %s" % (p, "caught by: %s" % hit[0] if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % p)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases (%d whose answer this change makes), %d arrival orders, %d of %d planted breaks caught"
          % ("ok" if not problems else "%d problems" % len(problems), len(CASES), changed, n, caught, len(PLANTS + GUARDS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
