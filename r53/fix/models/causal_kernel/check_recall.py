#!/usr/bin/env python3
"""
check_recall.py: the members' recall of a duty holder (CC 4.5.13: "A recall is one row cosigned by more than two thirds
of the standing roster within the 72-hour standing window. The floor is two voices"), as seat.py's seat rule reads it.

The rows: a founding record naming A the holder of `moderate`; the recall is a counted unseat of A's `moderate` seat
under the policy row `moderator_recall`, counted over the members at the head it names. The count (`Policy::Recall`,
seat.count_met): strictly more than two thirds, never fewer than two voices, over the members LESS the holder it
recalls, and that holder no voice of it (CIRISConstitution#241 C1: the recall judges one holder, as the lift does). A
plain count with the same threshold (`Policy::StrictFloor`) counts the member it removes as a voice, as any removal
does (CC 2.7.5); one case shows the two side by side.

Every case is a hand-written answer, read in every arrival order of its rows above the founding one. Each names its
ledger row: CIRISConstitution#241: a recall.

Planted breaks, each of which must change a case's answer:
    recall_at_least         the recall read as at least two thirds (the table's cell), not more than
    floor_unread            the floor of two voices is not read
    recall_holder_in_base   the recall counted over the members with the holder it recalls
    recall_holder_voice     the holder a recall judges is a voice of it
    recall_as_strictfloor   the recall read as the plain StrictFloor count

    python3 -I check_recall.py      exit 1 on any difference
"""
import contextlib
import itertools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import seat as ST  # noqa: E402

CK = ST.CK
T, F = True, False
OBJ = "g"
RULE = lambda r, P, past: ST.seat_rule(r, P, past)
PLAIN_FLOOR = "strict_two_thirds_floor_two"          # a plain count with the recall's threshold, for one case
ST.POLICY.setdefault(PLAIN_FLOOR, ("strictfloor", 2, 3, 2))


def room(n):
    """A founding record of n members (A, B, ...), A the one holder of moderate."""
    ks = tuple("ABCDEFG"[:n])
    return ST.found("g", "A", ks, {"moderate": ("A",)}, cosigners=ks[1:])


def recall(i, k, signers, heads=("g",), policy="moderator_recall"):
    return ST.unseat(i, signers[0], k, "moderate", OBJ, "group", tuple(heads), head=tuple(heads), policy=policy,
                     cosigners=tuple(signers[1:]))


MOD = lambda *ks: [(k, "moderate", T) for k in ks]
NOMOD = lambda *ks: [(k, "moderate", F) for k in ks]

# (name, rows, [(key, scope, stands)])
CASES = [
    ("a room of one: no recall (no other member, and the floor is two voices)", [room(1), recall("rc", "A", "A")], MOD("A")),
    ("two members: no recall possible: the one other is below the floor of two", [room(2), recall("rc", "A", "B")], MOD("A")),
    ("two members: the holder's own voice is none, so A and B together do not recall A either",
     [room(2), recall("rc", "A", "AB")], MOD("A")),
    ("three members: both others recall (2 of 2)", [room(3), recall("rc", "A", "BC")], NOMOD("A")),
    ("three members: one other does not", [room(3), recall("rc", "A", "B")], MOD("A")),
    ("four members: all three others recall", [room(4), recall("rc", "A", "BCD")], NOMOD("A") + [("A", "member", T)]),
    ("four members: two of the three others do not (2 of 3 is not strictly more than two thirds), the holder's own "
     "voice beside them none", [room(4), recall("rc", "A", "ABC")], MOD("A")),
    ("five members: three of the four others recall", [room(5), recall("rc", "A", "BCD")], NOMOD("A")),
    ("five members: two of four do not", [room(5), recall("rc", "A", "BC")], MOD("A")),
    ("six members: four of the five others recall", [room(6), recall("rc", "A", "BCDE")], NOMOD("A")),
    ("six members: three of five do not", [room(6), recall("rc", "A", "BCD")], MOD("A")),
    ("seven members: five of the six others recall", [room(7), recall("rc", "A", "BCDEF")], NOMOD("A")),
    ("seven members: four of six do not", [room(7), recall("rc", "A", "BCDE")], MOD("A")),
    ("a plain count with the recall's threshold (StrictFloor(2, 3, 2)): of three, B and C do not remove A, A in the "
     "base and a voice (2 of 3 is not more than two thirds)", [room(3), recall("rc", "A", "BC", policy=PLAIN_FLOOR)], MOD("A")),
]

PLANTS = ("recall_at_least", "floor_unread", "recall_holder_in_base", "recall_holder_voice", "recall_as_strictfloor")


@contextlib.contextmanager
def planted(plant):
    saved, pol = set(ST.MUT), dict(ST.POLICY)
    if plant == "recall_at_least":
        ST.POLICY["moderator_recall"] = ("atleast", 2, 3)
    elif plant:
        ST.MUT.add(plant)
    try:
        yield
    finally:
        ST.MUT.clear(); ST.MUT |= saved
        ST.POLICY.clear(); ST.POLICY.update(pol)


def answers(rows, asks, plant=None, arrive=False):
    with planted(plant):
        S = CK.arrive(list(rows), RULE) if arrive else CK.concluded(CK.kept(list(rows)), RULE)
        Q = ST.Seats(S)
        return [Q.stands(k, s, OBJ) for k, s, _ in asks]


def main():
    problems, n_orders = [], 0
    for name, rows, asks in CASES:
        want = [w for _, _, w in asks]
        got = answers(rows, asks)
        if got != want:
            problems.append("%s: got %s, expected %s" % (name, got, want))
        for p in itertools.permutations(rows[1:]):
            n_orders += 1
            if answers([rows[0]] + list(p), asks, arrive=True) != got:
                problems.append("%s: order %s differs" % (name, [r["id"] for r in p]))
                break
    caught = 0
    for plant in PLANTS:
        hit = [name for name, rows, asks in CASES if answers(rows, asks, plant) != [w for _, _, w in asks]]
        caught += bool(hit)
        print("  plant %-22s %s" % (plant, "caught by %d cases, first: %s" % (len(hit), hit[0]) if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % plant)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases, %d answers, %d orders, %d of %d planted breaks caught"
          % ("ok" if not problems else "%d problems" % len(problems), len(CASES), sum(len(a) for _, _, a in CASES),
             n_orders, caught, len(PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
