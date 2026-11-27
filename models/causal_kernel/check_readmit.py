#!/usr/bin/env python3
"""
check_readmit.py: a member who left and was re-admitted counts (CIRISConstitution#218, pin list: a re-admitted member
counts), as seat.py's seat rule reads it.

The rule (seat.left_in_past, seat.stay_ended_in_past, one test: seat.seated_after): a key is out of a count by its own
leaving only while no seating of it in that scope stands after the leaving in the counted row's past, that is, while
no offer seating the key that has the leaving in its own past is in the row's past. Before, `left_in_past` read the
leaving and ignored a later admission, so a member who resigned and was re-admitted stood as a member and was in no
count's base and no voice of any count, for ever. A counted removal and re-admission was never affected: the removal
acts through the members at the head (members_at), not through left_in_past. A window's clause is not affected either:
its base is the members at the opener's head, and it reads no leaving.

Every case is a hand-written answer, read in every arrival order of its rows above the founding one (a fixed sample of
300 where there are more than six).

Planted breaks, each of which must change a case's answer:
    readmit_unread      a seating after the leaving is not read (the 0.4.0 reading): the key is out for ever
    end_reseat_unread   rule (2), no second end of a seat, does not read a seating after the first end: a re-admitted
                        key's second leaving is no end

    python3 -I check_readmit.py      exit 1 on any difference
"""
import contextlib
import itertools
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import seat as ST  # noqa: E402

CK = ST.CK
T, F = True, False
OBJ = "g"
RULE = lambda r, P, past: ST.seat_rule(r, P, past)
LEDGER = "CIRISConstitution#218, pin list: a re-admitted member counts: "


def admit(i, k, signers, heads):
    """A widening (community_invite, two thirds), the joiner cosigning."""
    return ST.offer(i, signers[0], k, "member", OBJ, "group", tuple(heads), head=tuple(heads), policy="community_invite",
                    cosigners=tuple(signers[1:]) + ((k,) if k not in signers else ()))


def remove(i, k, signers, heads):
    """A counted removal from the roster (community_remove: the room's protocol, majority, over the other members)."""
    return ST.unseat(i, signers[0], k, "member", OBJ, "group", tuple(heads), head=tuple(heads), policy="community_remove",
                     cosigners=tuple(signers[1:]))


G4 = ST.found("g", "A", tuple("ABCD"), {"moderate": ("A",)}, cosigners=tuple("BCD"))
G6 = ST.found("g", "A", tuple("ABCDEF"), {"moderate": ("A",)}, cosigners=tuple("BCDEF"))
G5 = ST.found("g", "A", tuple("ABCDE"), {"moderate": ("A",)}, cosigners=tuple("BCDE"))
WC = ST.withdraw("wc", "C", "g", ("g",))                       # C resigns (its withdrawal of its founding seat)
AC4 = admit("ac", "C", ("A", "B", "D"), ("wc",))               # the room re-admits C (3 of 3)
AC6 = admit("ac", "C", ("A", "B", "D", "E"), ("wc",))          # (4 of 5)
AC5 = admit("ac", "C", ("A", "B", "D", "E"), ("wc",))          # (4 of 4)
XC4 = remove("xc", "C", ("A", "B", "D"), ("g",))               # or the room removes C
AX4 = admit("ac", "C", ("A", "B", "D"), ("xc",))               # and re-admits it

# (name, rows, [(key, scope, stands)], item)
CASES = [
    ("a re-admitted member is a voice: of six, X admitted by A, B, C and D (4 of 6) is seated",
     [G6, WC, AC6, admit("ax", "X", "ABCD", ("ac",))], [("C", "member", T), ("X", "member", T)], "a voice"),
    ("a re-admitted member is in the base: of four, X admitted by A and B (2 of 4) is not seated",
     [G4, WC, AC4, admit("ax", "X", "AB", ("ac",))], [("C", "member", T), ("X", "member", F)], "the base"),
    ("a removal: of six, F removed by A, B, C and D (4 of 6) is out",
     [G6, WC, AC6, remove("xf", "F", "ABCD", ("ac",))], [("F", "member", F)], "a removal"),
    ("a removal: of five, E removed by A and B (two of the four others: the member removed is not counted) is not out",
     [G5, WC, AC5, remove("xe", "E", "AB", ("ac",))], [("E", "member", T)], "a removal"),
    ("without the re-admission, the leaver is out of the base: of four, X admitted by A and B (2 of the 3 left) is seated",
     [G4, WC, admit("ax", "X", "AB", ("wc",))], [("C", "member", F), ("X", "member", T)], "the base"),
    ("a re-admission beside the count (not in its past) is not read by it: C is out, and X by A and B is seated",
     [G4, WC, AC4, admit("ax", "X", "AB", ("wc",))], [("C", "member", T), ("X", "member", T)], "the base"),
    ("a leaving after the re-admission puts the key out again: C leaves, is re-admitted, leaves; X by A and B is seated",
     [G4, WC, AC4, ST.withdraw("wc2", "C", "ac", ("ac",)), admit("ax", "X", "AB", ("wc2",))],
     [("C", "member", F), ("X", "member", T)], "the base"),
    ("a removal and re-admission was never out of the base: of four, X by A and B is not seated",
     [G4, XC4, AX4, admit("ax", "X", "AB", ("ac",))], [("C", "member", T), ("X", "member", F)], "a removal"),
    ("and a re-admitted removed member is a voice: of four, X by A, B and C (3 of 4) is seated",
     [G4, XC4, AX4, admit("ax", "X", "ABC", ("ac",))], [("X", "member", T)], "a voice"),
    ("a re-admitted resigned member is a voice the same way: of four, X by A, B and C (3 of 4) is seated",
     [G4, WC, AC4, admit("ax", "X", "ABC", ("ac",))], [("X", "member", T)], "a voice"),
]

PLANTS = ("readmit_unread", "end_reseat_unread")


# every counted row and every seat's end names the newest counted changes over the room in its own past (H1, H4, the
# heads ruling of 2026-11-26): a resignation is no head of a count, so a count after one names the change before it
CASES = [(c[0], ST.honest(c[1])) + tuple(c[2:]) for c in CASES]


@contextlib.contextmanager
def planted(plant):
    saved = set(ST.MUT)
    if plant:
        ST.MUT.add(plant)
    try:
        yield
    finally:
        ST.MUT.clear(); ST.MUT |= saved


def answers(rows, asks, plant=None, arrive=False):
    with planted(plant):
        S = CK.arrive(list(rows), RULE) if arrive else CK.concluded(CK.kept(list(rows)), RULE)
        Q = ST.Seats(S)
        return [Q.stands(k, s, OBJ) for k, s, _ in asks]


def orders(rows):
    tail = rows[1:]
    if len(tail) <= 6:
        return itertools.permutations(tail)
    rnd = random.Random(len(tail))
    out = [tail, tail[::-1]]
    for _ in range(298):
        p = list(tail); rnd.shuffle(p); out.append(p)
    return out


def main():
    problems, n_orders = [], 0
    for name, rows, asks, _item in CASES:
        want = [w for _, _, w in asks]
        got = answers(rows, asks)
        if got != want:
            problems.append("%s: got %s, expected %s" % (name, got, want))
        for p in orders(rows):
            n_orders += 1
            if answers([rows[0]] + list(p), asks, arrive=True) != got:
                problems.append("%s: order %s differs" % (name, [r["id"] for r in p]))
                break
    caught = 0
    for plant in PLANTS:
        hit = [name for name, rows, asks, _ in CASES if answers(rows, asks, plant) != [w for _, _, w in asks]]
        caught += bool(hit)
        print("  plant %-16s %s" % (plant, "caught by %d cases, first: %s" % (len(hit), hit[0]) if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % plant)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases, %d answers, %d orders, %d of %d planted breaks caught"
          % ("ok" if not problems else "%d problems" % len(problems), len(CASES), sum(len(a) for _, _, a, _ in CASES),
             n_orders, caught, len(PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
