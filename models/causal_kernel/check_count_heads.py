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
]
PLANTS = (("count_heads_unread", ST.MUT), ("line_concurrent", CP.MUT), ("cut_before_line", ST.MUT))


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
    # the answer before: the three rules switched off together
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
    for p, m in PLANTS:
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
          % ("ok" if not problems else "%d problems" % len(problems), len(CASES), changed, n, caught, len(PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
