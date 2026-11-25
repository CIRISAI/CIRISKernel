#!/usr/bin/env python3
"""
check_duty_seats.py: a duty seat stands only on a member (CC 4.5.4, "a non-member holds no duty"), as seat.py reads it.

The rule, in two halves (seat.py, `member`):

    stands on a member   a duty seat stands only where its holder holds the roster's seat over the same community at
                         the same reading. A conferral on a key that is not a member seats nobody and is no voice in
                         a duty count; when the key's widening lands, the seat stands with no further row.
    ends with the stay   an end of the holder's stay as a member ends the duty seats whose offers are in that end's
                         past: a counted removal from the roster, or the holder's own withdrawal of a seat that holds
                         `member` (its member seat, or the founding row). Nothing revives: a later admission does not
                         seat an offer so ended. A conferral that is not in the end's past (made after it, or beside
                         it) waits for the next admission like any conferral on a non-member.

At tips the duty seat follows the folded roster (seat.Seats.tips_fold): out where the fold holds its holder out of
`member`.

The founding, as rows. A founding row of scope `duty` seats the keys it names as duty holders, and that seat holds
`member`: a founding holder's membership is its founding duty seat, and its withdrawal of the founding row ends both.
Where a founding holder is to lay down its duty and stay a member, it needs a member seat beside its duty seat, and
what runs depends on how many found the community:
    three or more   the founding row, then one chained counted row of scope `member` per founding holder, signed by
                    the other holders (the crate holds that no key admits itself, CC 2.7.5: a key a counted row
                    seats is no voice of its count, so one row seating every founder on the founders' own voices
                    concludes nothing there; this reference does not have that rule, and the cases here use only
                    rows the two agree on). Each holder then has a member seat beside its duty seat: its withdrawal
                    of the founding row ends its duty seat, and it stays a member.
    one             the founding row, then the founder's own offer of `member` to itself over the founding row
                    (conferrer: the object's own key). Over a founding row that seats one key that offer stands on
                    its own, so it outlives the founder's withdrawal of the founding row.
    two             neither runs: one voice of two meets no count here, and over a founding row that seats several
                    keys an own offer stands only while its signer's founding seat does. Two founders have no
                    presentation in which either lays down its duty and stays a member. This is open.
The withdrawal of the founding row ends the duty seats conferred on that holder in its past as well: it is the
holder's own withdrawal of a seat that holds `member`. Persist's table gives the duty seat `member` and no named duty
(HOLDS.duty = ("member",)), with each named duty a chained counted row; the cases run that table too.

What the rule does not reach, each a case below: a community whose founding row is not of scope `duty`; a seat the
duty holders place that makes its holder no duty holder (a node's detector seat). A deputy's edge is no seat
(conferral_end.py), and its case there answers as it did.

Every case is a hand-written answer, read in every arrival order of its rows (a fixed sample of 300 where there are
more than six rows above the founding one).

Planted breaks, each of which must change a case's answer:
    duty_no_member      the membership condition is off: a conferral seats a key that is not a member
    duty_revives        an end of the stay ends nothing by its past: the next admission seats the old offer
    resign_keeps_duty   a holder's own end of its stay does not end its duty seats
    member_cut_only     a counted removal cuts the member seat only (seat.py's own mutation): the old offer revives
    duty_fold_unread    at tips the duty seat does not follow the folded roster

Not here: the count that confers or withdraws a duty seat (check_rosters.py, the duty instance); a count over a scope
that is no duty; the term of a seat; an act done under a duty seat after it ends (conferral_end.py).

    python3 -I check_duty_seats.py      exit 1 on any difference
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
import conferral_end as CE  # noqa: E402

CK = ST.CK
T, F = True, False
OBJ = "g"
RULE = lambda r, P, past: ST.seat_rule(r, P, past)
PERSIST_HOLDS = ("member",)                   # persist's table: the duty seat holds `member`, each named duty is its own row

G = ST.offer("g", "A", ("A", "B", "C"), "duty", "@", "self", cosigners=("B", "C"))      # three founding duty holders
G2 = ST.offer("g", "A", ("A", "B"), "duty", "@", "self", cosigners=("B",))              # two
GM = ST.offer("g", "A", ("A", "B", "C"), "member", "@", "self", cosigners=("B", "C"))   # a room whose founding row is not of scope duty


def admit(i, k, signers, heads, cites=()):
    """The widening: a counted row of the roster's own seat, the joiner cosigning (its own yes)."""
    ks = (k,) if isinstance(k, str) else tuple(k)
    return ST.offer(i, signers[0], k, "member", OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
                    policy="community_invite", cosigners=tuple(signers[1:]) + tuple(x for x in ks if x not in signers))


def confer(i, k, scope, signers, heads, cites=(), accepted=True):
    """A duty seat conferred by the duty holders' count (CC 4.5.4 (iv))."""
    return ST.offer(i, signers[0], k, scope, OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
                    policy="duty_confer", counted="duty", cosigners=tuple(signers[1:]) + ((k,) if accepted and k not in signers else ()))


def remove(i, k, signers, heads, cites=()):
    """A counted removal from the roster."""
    return ST.unseat(i, signers[0], k, "member", OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
                     policy="community_remove", cosigners=tuple(signers[1:]))


# the rows the cases share. D is admitted over the founding row, then seated to moderate over its admission.
MD = admit("md", "D", ("A", "B"), ("g",))
CD = confer("cd", "D", "moderate", ("A", "B"), ("md",))
CR = confer("cr", "D", "review", ("A", "B"), ("cd",))
WD = ST.withdraw("wd", "D", "md", ("cd",))                              # D resigns: its withdrawal of its member seat
XD = remove("xd", "D", ("A", "B", "C"), ("cd",))                             # the room removes D
MD2 = admit("md2", "D", ("A", "B"), ("cd",), ("wd",))                    # D admitted again after resigning
MD2X = admit("md2", "D", ("A", "B"), ("xd",))                            # D admitted again after its removal
CD2 = confer("cd2", "D", "moderate", ("A", "B"), ("md2",))               # a fresh conferral over the re-admission
# the founding with a member seat beside each founding holder's duty seat
# (one chained counted row per founding holder, signed by the others: no key admits itself)
MFA = admit("mfa", "A", ("B", "C"), ("g",))
MFB = admit("mfb", "B", ("A", "C"), ("mfa",))
MFC = admit("mfc", "C", ("A", "B"), ("mfb",))
WA = ST.withdraw("wa", "A", "g", ("mfa",))                              # A lays down its founding duty seat
CM = confer("cm", "A", "moderate", ("B", "C"), ("mfa",))                 # persist's table: a named duty is a chained row
G1 = ST.offer("g", "A", ("A",), "duty", "@", "self")                     # a lone founder
MS1 = ST.offer("ms", "A", "A", "member", OBJ, "self", ("g",))            # and its own offer of `member` to itself

# (name, rows, [(key, scope, stands)], table): table "persist" reads the rows under HOLDS.duty = ("member",)
CASES = [
    # ---- a conferral on a non-member -----------------------------------------------------------------------------
    ("a conferral on a key that is not a member seats nobody", [G, confer("cd", "D", "moderate", ("A", "B"), ("g",))],
     [("D", "moderate", F), ("D", "duty", F), ("D", "member", F), ("A", "duty", T)], None),
    ("a key conferred on while no member is no voice in a later duty count: E's seat, signed by A and D of the two holders A and B, is not conferred",
     [G2, admit("me", "E", ("A", "B"), ("g",)), confer("cd", "D", "moderate", ("A", "B"), ("me",)), confer("ce", "E", "review", ("A", "D"), ("cd",))],
     [("D", "moderate", F), ("E", "review", F), ("E", "member", T)], None),
    ("the same rows with D admitted first: D is a duty holder, its voice counts, and E is seated",
     [G2, admit("me", "E", ("A", "B"), ("g",)), admit("md", "D", ("A", "B"), ("me",)), confer("cd", "D", "moderate", ("A", "B"), ("md",)),
      confer("ce", "E", "review", ("A", "D"), ("cd",))],
     [("D", "moderate", T), ("E", "review", T)], None),
    ("the widening lands after the conferral and its acceptance: the seat stands with no further row",
     [G, confer("cd", "D", "moderate", ("A", "B"), ("g",), accepted=False), ST.accept("ad", "D", "cd"), admit("md", "D", ("A", "B"), ("cd",), ("ad",))],
     [("D", "moderate", T), ("D", "duty", T), ("D", "member", T)], None),
    ("the conferral and the widening as two tips of the founding row: the key is a member and its duty seat waits, as tips do",
     [G, confer("cd", "D", "moderate", ("A", "B"), ("g",)), admit("md", "D", ("A", "B"), ("g",))],
     [("D", "member", T), ("D", "moderate", F)], None),
    ("a version naming both tips: the duty seat stands",
     [G, confer("cd", "D", "moderate", ("A", "B"), ("g",)), admit("md", "D", ("A", "B"), ("g",)), admit("me", "E", ("A", "B"), ("cd", "md"))],
     [("D", "member", T), ("D", "moderate", T), ("E", "member", T)], None),
    # ---- an end of the stay ---------------------------------------------------------------------------------------
    ("a member holding two duty seats", [G, MD, CD, CR], [("D", "moderate", T), ("D", "review", T), ("D", "duty", T)], None),
    ("a member's resignation ends its duty seats, with no withdrawal of each offer",
     [G, MD, CD, CR, ST.withdraw("wd", "D", "md", ("cr",))],
     [("D", "moderate", F), ("D", "review", F), ("D", "duty", F), ("D", "member", F), ("A", "duty", T)], None),
    ("a founding holder's resignation (its withdrawal of the founding row, which is its member seat) ends a duty seat conferred on it",
     [G, confer("ca", "A", "moderate:spam", ("B", "C"), ("g",)), ST.withdraw("wa", "A", "g", ("ca",))],
     [("A", "moderate:spam", F), ("A", "duty", F), ("A", "member", F), ("B", "duty", T)], None),
    ("a counted removal from the roster ends them", [G, MD, CD, XD], [("D", "moderate", F), ("D", "duty", F), ("D", "member", F)], None),
    ("a duty count with a holder's resignation in its past is not counted over that holder: E's seat, signed by A and the resigned D, is not conferred",
     [G2, admit("me", "E", ("A", "B"), ("g",)), admit("md", "D", ("A", "B"), ("me",)), CD, WD, confer("ce", "E", "review", ("A", "D"), ("cd",), ("wd",))],
     [("E", "review", F), ("D", "moderate", F)], None),
    ("the same count without the resignation in its past is counted over D, as a count is over any member whose leaving it does not cite",
     [G2, admit("me", "E", ("A", "B"), ("g",)), admit("md", "D", ("A", "B"), ("me",)), CD, WD, confer("ce", "E", "review", ("A", "D"), ("cd",))],
     [("E", "review", T), ("D", "moderate", F)], None),
    # ---- nothing revives ------------------------------------------------------------------------------------------
    ("no revival: admitted again after its resignation, the key is a member and the old conferral does not seat it",
     [G, MD, CD, WD, MD2], [("D", "member", T), ("D", "moderate", F), ("D", "duty", F)], None),
    ("a fresh conferral after that re-admission seats it", [G, MD, CD, WD, MD2, CD2], [("D", "member", T), ("D", "moderate", T)], None),
    ("no revival: admitted again after its removal, the key is a member and the old conferral does not seat it",
     [G, MD, CD, XD, MD2X], [("D", "member", T), ("D", "moderate", F), ("D", "duty", F)], None),
    ("a fresh conferral after that re-admission seats it (removal)", [G, MD, CD, XD, MD2X, CD2], [("D", "member", T), ("D", "moderate", T)], None),
    ("a holder admitted again and conferred on afresh is counted in a duty count that has its old resignation in its past: E's seat, signed by A and D of the three holders, is conferred",
     [G2, admit("me", "E", ("A", "B"), ("g",)), admit("md", "D", ("A", "B"), ("me",)), CD, WD, MD2, CD2, confer("ce", "E", "review", ("A", "D"), ("cd2",))],
     [("E", "review", T), ("D", "moderate", T)], None),
    # ---- a conferral between the end and the re-admission -----------------------------------------------------------
    ("a conferral made after the resignation and before a re-admission waits",
     [G, MD, ST.withdraw("wd", "D", "md", ("md",)), confer("cd", "D", "moderate", ("A", "B"), ("md",), ("wd",))],
     [("D", "moderate", F), ("D", "member", F)], None),
    ("and stands when the re-admission lands",
     [G, MD, ST.withdraw("wd", "D", "md", ("md",)), confer("cd", "D", "moderate", ("A", "B"), ("md",), ("wd",)), admit("md2", "D", ("A", "B"), ("cd",))],
     [("D", "moderate", T), ("D", "member", T)], None),
    ("a conferral made after the removal and before a re-admission waits",
     [G, MD, remove("xd", "D", ("A", "B", "C"), ("md",)), confer("cd", "D", "moderate", ("A", "B"), ("xd",))],
     [("D", "moderate", F), ("D", "member", F)], None),
    ("and stands when the re-admission lands (removal)",
     [G, MD, remove("xd", "D", ("A", "B", "C"), ("md",)), confer("cd", "D", "moderate", ("A", "B"), ("xd",)), admit("md2", "D", ("A", "B"), ("cd",))],
     [("D", "moderate", T), ("D", "member", T)], None),
    ("a conferral beside the resignation (neither row names the other) is not in the end's past: it waits",
     [G, MD, CD, ST.withdraw("wd", "D", "md", ("md",))], [("D", "moderate", F), ("D", "member", F)], None),
    ("and stands when the re-admission lands (beside)",
     [G, MD, CD, ST.withdraw("wd", "D", "md", ("md",)), MD2], [("D", "moderate", T), ("D", "member", T)], None),
    # ---- the founding with a member seat beside the duty seat --------------------------------------------------------
    ("the founding as chained rows: each founding holder has a member seat beside its founding duty seat",
     [G, MFA, MFB, MFC], [("A", "member", T), ("A", "duty", T), ("A", "moderate", T), ("C", "member", T), ("C", "duty", T)], None),
    ("each of the three lays down its duty in turn (it withdraws the founding row) and all stay members; nobody holds a duty",
     [G, MFA, MFB, MFC, ST.withdraw("wa", "A", "g", ("mfc",)), ST.withdraw("wb", "B", "g", ("mfc",)), ST.withdraw("wc", "C", "g", ("mfc",))],
     [("A", "member", T), ("B", "member", T), ("C", "member", T), ("A", "duty", F), ("B", "duty", F), ("C", "duty", F)], None),
    ("a founding holder lays down its duty (it withdraws the founding row) and stays a member",
     [G, MFA, WA], [("A", "member", T), ("A", "duty", F), ("A", "moderate", F), ("B", "duty", T), ("B", "member", T)], None),
    ("a lone founder with its own offer of `member` to itself lays down its duty and stays a member",
     [G1, MS1, ST.withdraw("wa", "A", "g", ("ms",))], [("A", "member", T), ("A", "duty", F)], None),
    ("two founders: an own offer of `member` stands only on its signer's founding seat, so it does not outlive that seat",
     [G2, ST.offer("ms", "A", "A", "member", OBJ, "self", ("g",)), ST.withdraw("wa", "A", "g", ("ms",))],
     [("A", "member", F), ("A", "duty", F), ("B", "member", T)], None),
    ("with the founding row alone, the same withdrawal ends its membership too",
     [G, ST.withdraw("wa", "A", "g", ("g",))], [("A", "member", F), ("A", "duty", F), ("B", "member", T)], None),
    ("persist's table: the founding holders are duty holders and members, and hold no named duty until a chained row confers one",
     [G, MFA, CM], [("A", "duty", T), ("A", "member", T), ("A", "moderate", T), ("B", "duty", T), ("B", "moderate", F)], "persist"),
    ("persist's table: a founding holder lays down a named duty (it withdraws that offer) and stays a member and a founding duty holder",
     [G, MFA, CM, ST.withdraw("wm", "A", "cm", ("cm",))], [("A", "moderate", F), ("A", "duty", T), ("A", "member", T)], "persist"),
    ("persist's table: it lays down its founding duty seat, which ends the named duty conferred before, and stays a member",
     [G, MFA, CM, ST.withdraw("wa", "A", "g", ("cm",))], [("A", "duty", F), ("A", "moderate", F), ("A", "member", T), ("B", "duty", T)], "persist"),
    ("persist's table: a duty conferred on it after that stands, since it is a member",
     [G, MFA, CM, ST.withdraw("wa", "A", "g", ("cm",)), confer("cm2", "A", "moderate", ("B", "C"), ("cm",), ("wa",))],
     [("A", "moderate", T), ("A", "duty", T), ("A", "member", T)], "persist"),
    # ---- two tips -----------------------------------------------------------------------------------------------
    ("two tips: the holder is removed on one and another member is admitted on the other; the duty seat is out under the fold",
     [G, MD, CD, XD, admit("me", "E", ("A", "B", "C"), ("cd",))], [("D", "moderate", F), ("D", "member", F), ("E", "member", T), ("A", "moderate", T)], None),
    ("two tips: a key admitted on one tip by the voice of a member the other tip removed is out of the folded roster, and so is the duty seat conferred on it there",
     [G, remove("xc", "C", ("A", "B"), ("g",)), admit("md", "D", ("B", "C"), ("g",)), confer("cd", "D", "moderate", ("A", "B"), ("md",))],
     [("D", "member", F), ("D", "moderate", F), ("D", "duty", F), ("A", "moderate", T), ("C", "member", F)], None),
    # ---- what the rule does not reach -----------------------------------------------------------------------------
    ("not reached: a room whose founding row is not of scope duty; its members' count seats a key that is no member to moderate",
     [GM, ST.offer("cd", "A", "D", "moderate", OBJ, "group", ("g",), head=("g",), policy="community_invite", counted="member", cosigners=("B", "D"))],
     [("D", "moderate", T), ("D", "member", F)], None),
    ("not reached: a seat the duty holders place that is no duty (a node's detector seat) stands on a key that is no member, and makes it no duty holder",
     [G, confer("cn", "N", "detect:list1", ("A", "B"), ("g",))], [("N", "detect:list1", T), ("N", "member", F), ("N", "duty", F)], None),
]
PLANTS = ("duty_no_member", "duty_revives", "resign_keeps_duty", "member_cut_only", "duty_fold_unread")


@contextlib.contextmanager
def table(name):
    """Read under persist's table (HOLDS.duty = ("member",)); the default table otherwise."""
    saved = ST.HOLDS["duty"]
    if name == "persist":
        ST.HOLDS["duty"] = PERSIST_HOLDS
    try:
        yield
    finally:
        ST.HOLDS["duty"] = saved


@contextlib.contextmanager
def planted(plant):
    saved = set(ST.MUT)
    if plant:
        ST.MUT.add(plant)
    try:
        yield
    finally:
        ST.MUT.clear(); ST.MUT |= saved


def answers(rows, asks, tab=None, plant=None, arrive=False):
    with table(tab), planted(plant):
        S = CK.arrive(list(rows), RULE) if arrive else CK.concluded(CK.kept(list(rows)), RULE)
        Q = ST.Seats(S)
        return [Q.stands(k, s, OBJ) for k, s, _ in asks]


def orders(rows):
    """Every order of the rows above the founding one; a fixed sample of 300 where there are more than six."""
    tail = rows[1:]
    if len(tail) <= 6:
        return itertools.permutations(tail)
    rnd = random.Random(len(tail))
    out = [tail, tail[::-1]]
    for _ in range(298):
        p = list(tail); rnd.shuffle(p); out.append(p)
    return out


def deputy():
    """A deputy's edge is no seat: conferral_end.py's own case answers as it is written there."""
    c = next(c for c in CE.CASES if c[0] == "deputy")
    got = CE.answers(c[2], **dict(c[3]))
    return [] if all(got.get(x) == {"counted": cnt, "in_force": frc, "rule": rule} for x, (cnt, frc, rule) in c[4].items()) \
        else ["conferral_end deputy: %s" % got]


def main():
    problems, n_orders = [], 0
    for name, rows, asks, tab in CASES:
        want = [w for _, _, w in asks]
        got = answers(rows, asks, tab)
        if got != want:
            problems.append("%s: got %s, expected %s" % (name, got, want))
        for p in orders(rows):
            n_orders += 1
            if answers([rows[0]] + list(p), asks, tab, arrive=True) != got:
                problems.append("%s: order %s differs" % (name, [r["id"] for r in p]))
                break
    problems += deputy()
    caught = 0
    for plant in PLANTS:
        hit = [name for name, rows, asks, tab in CASES if answers(rows, asks, tab, plant) != [w for _, _, w in asks]]
        caught += bool(hit)
        print("  plant %-18s %s" % (plant, "caught by %d cases, first: %s" % (len(hit), hit[0]) if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % plant)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases, %d answers, %d orders, %d of %d planted breaks caught"
          % ("ok" if not problems else "%d problems" % len(problems), len(CASES), sum(len(a) for _, _, a, _ in CASES), n_orders, caught, len(PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
