#!/usr/bin/env python3
"""
check_ranked.py: the ranked count (kernel_lib/reexpress.py `ranked`, crate `ranked::ranked`) and its runoff order
(`runoff`, crate `ranked::runoff`), on hand-written ballots (CC 4.5.13: "Ranked choice is one count, and any choice
among options may use it").

    the count        instant runoff; in each round the options holding no first choice are eliminated together,
                     before the weakest is sought (CIRISConstitution#241 E1: every ranked count); a tie for weakest
                     goes against the option later in a declared order, and with none seats nobody
    the runoff order the one count repeated: the first is the count's winner, the next the winner of the same count
                     over the same ballots with those ahead of it struck, and so on; a step that ties ends the order

The fixture `reexpress.json` holds every small case of three options and 600 of four to six, each with its winner,
rounds and order; tests/lib_ops.rs replays it. Each case names its ledger row: CIRISConstitution#241: ranked choice.

Planted breaks (reexpress.MUT), each of which must change a case's answer:
    zero_strike_off           options holding no ballot are not struck together: a tie at zero seats nobody
    runoff_tie_continues      a step of the runoff order that ties strikes an option and goes on
    runoff_from_eliminations  the runoff order read off one count's eliminations, not the count repeated

    python3 -I check_ranked.py      exit 1 on any difference
"""
import contextlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "..", "kernel_lib"))
import reexpress as RX  # noqa: E402

TEN = list("ABCDEFGHIJ")
b = lambda spec: [("p%d" % i, tuple(r)) for i, r in enumerate(spec)]

# (name, ballots, options, declared, (winner, rounds), runoff order)
CASES = [
    ("of ten options, first choices 4, 3 and 3 among three: the seven others go together, then the two at 3 tie for "
     "weakest, and the count seats nobody", b(["A"] * 4 + ["B"] * 3 + ["CA"] * 3), TEN, False, (None, 1), ()),
    ("first choices 5, 3 and 2: the seven go together, then the 2, whose ballots pass to A, who wins",
     b(["A"] * 5 + ["B"] * 3 + ["CA"] * 2), TEN, False, ("A", 2), ("A", "B", "C")),
    ("every member a candidate: of five options, D and E named by no ballot go out together, then A, and C has a "
     "majority; the order C, B, A", b(["AC", "B", "C", "C", "B"]), list("ABCDE"), False, ("C", 2), ("C", "B", "A")),
    ("A 6, B 3, C 1, A's ballots ranking B next: A wins at once; with A struck B has nine of ten; then C",
     b(["AB"] * 6 + ["B"] * 3 + ["C"]), list("ABCD"), False, ("A", 0), ("A", "B", "C")),
    ("A 5, B 3, C 1, D 1 of ten: no majority, and C and D, each holding a ballot, tie for weakest: nobody",
     b(["AB"] * 5 + ["B"] * 3 + ["C", "D"]), list("ABCD"), False, (None, 0), ()),
    ("the eight of a decline: A 4, C 3, B 1 (B's next A): B goes out and A wins; with A struck, A's four pass to B, "
     "who has five of eight: the order is A, B, C (not A, C, B, the first count's eliminations reversed)",
     b(["AB"] * 4 + ["BA"] + ["C"] * 3), list("ABC"), False, ("A", 1), ("A", "B", "C")),
    ("a step that ties ends the order: A 3, B 1, C 1; with A struck B and C tie, so the order is A alone",
     b(["A"] * 3 + ["B", "C"]), list("ABC"), False, ("A", 0), ("A",)),
    ("with a declared order the zero-ballot strike moves no winner, only the rounds: of four, A 2, B 1, C 1 (C's next A)",
     b(["A", "A", "B", "CA"]), list("ABCD"), True, ("A", 2), ("A", "B", "C")),
]

PLANTS = ("zero_strike_off", "runoff_tie_continues", "runoff_from_eliminations")


@contextlib.contextmanager
def planted(plant):
    saved = set(RX.MUT)
    if plant:
        RX.MUT.add(plant)
    try:
        yield
    finally:
        RX.MUT.clear(); RX.MUT |= saved


def answers(plant=None):
    with planted(plant):
        return [(RX.ranked(bs, o, 2, d), tuple(RX.runoff(bs, o, 2, d))) for _, bs, o, d, _, _ in CASES]


def main():
    problems = []
    for (name, _b, _o, _d, want, order), (got, got_order) in zip(CASES, answers()):
        if got != want or got_order != order:
            problems.append("%s: got %s %s, expected %s %s" % (name, got, got_order, want, order))
        if got_order and got_order[0] != got[0]:
            problems.append("%s: the order's first is not the count's winner" % name)
    caught = 0
    for plant in PLANTS:
        hit = [c[0] for c, g in zip(CASES, answers(plant)) if g != (c[4], c[5])]
        caught += bool(hit)
        print("  plant %-24s %s" % (plant, "caught by %d cases, first: %s" % (len(hit), hit[0]) if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % plant)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases, %d of %d planted breaks caught"
          % ("ok" if not problems else "%d problems" % len(problems), len(CASES), caught, len(PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
