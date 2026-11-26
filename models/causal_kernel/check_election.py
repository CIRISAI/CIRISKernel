#!/usr/bin/env python3
"""
check_election.py: the moderator election (CC 4.5.13; CC 4.5.4 (v) and rule 2), as the rules C1 to C5 ruled for it
(CIRISConstitution#241) and seat.py builds them.

The rows. An election is named by its id row: the room's founding row, or the closed seating of the election before.
A ballot (kind `ballot`, `ranking` best first) and a decline (kind `decline`) are a member's own rows, each naming its
election by `of`. The seating is a counted offer of `moderate` over the room under the ranked count
(`moderator_election`): signed by the winner (its acceptance), `to` the winner, `of` its election, naming the rows it
is counted over (its set). It names no head. A receipt of a seating is an `ack` whose `of` is that seating.

    C1  the electorate (persons) and the candidates are read at the vacancy the id row defines: every end, in the
        reading row's past, of a seat the id row gave; the founding row itself where it gives none. A member admitted
        after the vacancy neither votes nor stands. A leaver is no voice and no candidate.
    C2  a seating concludes only where no person holds a duty over the room in the seats over its whole past, and no
        row of a later election is in its past.
    C3  an id row's standing is read in the naming row's past.
    C4  CONTAINS: a seating stands only where its set contains every other seating's set of its election (equal sets
        are one seat); sets not nested: nobody, until a seating over the union.
    C5  the causal close: a strict majority of the electorate, the winner and the leavers apart, receipting one
        seating that stood (C4) in each receipt's own past; one say per person, read causally. Once closed, no rival
        seating counts, and the next election is named by the closed seating.
Carried over: a ballot ranking a key outside the electorate, a leaver or more than three is void, the whole ballot; a
ballot its signer withdrew is none; a decline strikes its signer; the floor of two ballots; a tie for weakest seats
nobody (an election declares no order); the seating is the winner's own.

OPEN lists the rows the Constitution has not ruled, with this model's answer and the candidates (the open case: a
seating that stood, never closed, and fell vacant; ELECTION_OPEN_NEXT the alternative).

Every case is a hand-written answer, read in every arrival order of its rows above the founding one (a fixed sample of
200 where there are more than six). Each names the rule it rests on.

Planted breaks (seat.MUT), each of which must change a case's answer:
    vacancy_founding        the electorate read at the id row, not at its vacancy (C1)
    vacancy_first_end       one end of the seat read, the others not (C1, concurrent ends)
    electorate_at_seating   the electorate read over the seating's whole past (a member admitted after the vacancy votes)
    leaver_voice            a member whose leaving is in the seating's past is a voice
    c2_holder_unread        a seating concludes beside a live duty holder (C2)
    c2_later_unread         a seating concludes with a later election's row in its past (C2)
    contains_unread         every concluded seating stands (C4)
    twin_withdrawal_unread  a withdrawal of one of two seatings over equal sets leaves the other seating its holder
    close_unread            no election closes (C5)
    receipt_standing_unread a receipt counts though its seating did not stand in its past (C5)
    say_any_receipt         every receipt by a person counts, concurrent rivals and later ones alike (C5)
    close_leavers_kept      a leaver stays in the closing base (C5, point 2)
    closed_rivals_count     a rival seating of a closed election counts (C5)
    election_id_any         any row a seating names as its election is taken as one (C3, C5)
    set_any_signer          a row signed by a key outside the electorate is in a seating's set
    ballot_nonmember_ranked a ballot ranking a key outside the electorate counts, the key skipped
    ballot_ranks_unbounded  a ballot ranking more than three counts
    seating_any_signer      a seating signed by another key than the winner concludes
    twin_ids_apart          two seatings over equal sets name two elections, not one
    fold_ranked_counted     at tips the fold counts a seating as a plain count (which it never meets)

    python3 -I check_election.py      exit 1 on any difference
"""
import contextlib
import itertools
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import seat as ST  # noqa: E402

CK, R = ST.CK, ST.R
T, F = True, False
OBJ = "g"
RULE = lambda r, P, past: ST.seat_rule(r, P, past)
RV = "CIRISConstitution#241, "


def room(n, holders=("A",)):
    ks = tuple("ABCDEFGHIJ"[:n])
    return ST.found("g", "A", ks, {"moderate": tuple(holders)}, cosigners=ks[1:])


G1, G2, G3, G4, G5 = (room(n) for n in (1, 2, 3, 4, 5))
LM = ST.withdraw("lm", "A", "g", ("g",), scope="moderate")      # the one named holder lays moderate down: the vacancy


def ballot(i, k, ranking, names=("lm",), of="g"):
    return R(i, "ballot", k, tuple(names), ranking=tuple(ranking), of=of)


def decline(i, k, names=("lm",), of="g"):
    return R(i, "decline", k, tuple(names), of=of)


def elect(i, k, rows, of="g", cites=(), signer=None):
    """The seating of k (its acceptance, signed by k) over the rows named, of election `of`; `cites` rows it names
    beside its set."""
    return ST.offer(i, signer or k, k, "moderate", OBJ, "group", tuple(rows) + tuple(cites),
                    policy="moderator_election", of=of)


def ack(i, k, seating, names=()):
    """A receipt of a seating."""
    return R(i, "ack", k, (seating,) + tuple(names), of=seating)


def admit(i, k, signers, heads):
    return ST.offer(i, signers[0], k, "member", OBJ, "group", tuple(heads), head=tuple(heads), policy="community_invite",
                    cosigners=tuple(signers[1:]) + ((k,) if k not in signers else ()))


def leave(i, k, target, names):
    return ST.withdraw(i, k, target, tuple(names))


MOD = lambda *ks: [(k, "moderate", T) for k in ks]
NOMOD = lambda *ks: [(k, "moderate", F) for k in ks]

# five members A to E; A laid moderate down (lm). Honest ballots: C three first choices, B two
H5 = [ballot("ba", "A", "B"), ballot("bb", "B", "B"), ballot("bc", "C", "C"), ballot("bd", "D", "C"), ballot("be", "E", "C")]
IDS5 = tuple(b["id"] for b in H5)
EC = elect("ec", "C", IDS5)
# the close of EC: three of the other four receipt it
CLOSE = [ack("k1", "A", "ec"), ack("k2", "B", "ec"), ack("k4", "D", "ec")]
WC = ST.withdraw("wc", "C", "ec", ("k1", "k2", "k4"))            # C lays the seat down after the close
# the next election, named by EC: B wins it
N2 = [ballot("na", "A", "B", ("wc",), of="ec"), ballot("nb", "B", "B", ("wc",), of="ec"), ballot("nd", "D", "B", ("wc",), of="ec")]
EN = elect("en", "B", tuple(b["id"] for b in N2), of="ec")

CASES = [
    # ---- the count, carried over -------------------------------------------------------------------------------------
    ("the count: three of five rank C first, C is seated", [G5, LM] + H5 + [EC], MOD("C") + NOMOD("A", "B"), "the count"),
    ("the same rows seating B, whom the count does not yield: nothing", [G5, LM] + H5 + [elect("eb", "B", IDS5)],
     NOMOD("B", "C"), "the count"),
    ("the seating signed by another key than the winner, the winner accepting it: nothing",
     [G5, LM] + H5 + [elect("ec", "C", IDS5, signer="A"), ST.accept("ac", "C", "ec")],
     NOMOD("C"), "the seating is the winner's own"),
    ("a row signed outside the electorate adds nothing to a set: X's ballot named beside the honest set leaves the "
     "two seatings one seat, and C's withdrawal of either ends it",
     [G5, LM] + H5 + [ballot("bx", "X", "C"), EC, elect("ec2", "C", IDS5 + ("bx",)), ST.withdraw("wc", "C", "ec", ("ec",))],
     NOMOD("C"), "C4"),
    ("C1: a member admitted before the vacancy votes and stands: X, admitted at g, A laying moderate down after; X wins",
     [G5, admit("ax", "X", tuple("ABCDE"), ("g",)), ST.withdraw("lm", "A", "g", ("ax",), scope="moderate"),
      ballot("bx", "X", "X"), ballot("ba", "A", "X"), ballot("bb", "B", "X"), ballot("bc", "C", "C"), ballot("bd", "D", "C"),
      elect("ex", "X", ("bx", "ba", "bb", "bc", "bd"))], MOD("X"), "C1"),
    ("a ballot ranking four is void whole: without D's four-deep ballot for C, B and C tie and nobody is seated",
     [G5, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), ballot("bc", "C", "C"), ballot("bd", "D", "CABE"),
      ballot("be", "E", "C"), elect("ex", "C", ("ba", "bb", "bc", "bd", "be"))], NOMOD("C", "B"), "ballots"),
    ("a decline strikes its winner: C declines, the count over the rest yields B",
     [G5, LM] + H5 + [decline("dc", "C"), elect("eb", "B", IDS5 + ("dc",))], MOD("B") + NOMOD("C"), "decline"),
    ("a withdrawn ballot is none: D withdraws its ballot for C and ranks B, B wins",
     [G5, LM] + H5 + [ST.withdraw("wd", "D", "bd", ("bd",)), ballot("bd2", "D", "B", ("wd",)),
                      elect("eb", "B", IDS5 + ("wd", "bd2"))], MOD("B") + NOMOD("C"), "ballots"),
    # ---- C1: the electorate at the vacancy -----------------------------------------------------------------------------
    ("C1: a member admitted after the vacancy neither votes nor stands: X, admitted at lm, ranked by A and B and by "
     "itself; those ballots are void, C wins over C's and D's",
     [G5, LM, admit("ax", "X", tuple("ABCDE"), ("lm",)), ballot("ba", "A", "XB", ("ax",)), ballot("bb", "B", "XB", ("ax",)),
      ballot("bx", "X", "X", ("ax",)), ballot("bc", "C", "C"), ballot("bd", "D", "C"),
      elect("ec", "C", ("ba", "bb", "bx", "bc", "bd"))], MOD("C") + NOMOD("X"), "C1"),
    ("C1: and X's seating over those ballots concludes nothing",
     [G5, LM, admit("ax", "X", tuple("ABCDE"), ("lm",)), ballot("ba", "A", "X", ("ax",)), ballot("bb", "B", "X", ("ax",)),
      ballot("bx", "X", "X", ("ax",)), ballot("bc", "C", "C"), elect("ex", "X", ("ba", "bb", "bx", "bc"))],
     NOMOD("X"), "C1"),
    ("C1: a member who left after the vacancy is no voice: E leaves, its ballot for B does not count; C wins two to one "
     "(with E, two to two, nobody)",
     [G5, LM, ballot("ba", "A", "B"), ballot("bc", "C", "C"), ballot("bd", "D", "C"),
      ballot("be", "E", "B"), leave("le", "E", "g", ("be",)), elect("ec", "C", ("ba", "bc", "bd", "be"), cites=("le",))],
     MOD("C"), "C1, point 2"),
    # ---- C2 --------------------------------------------------------------------------------------------------------------
    ("C2: a seating while a person holds a duty concludes nothing (A has not laid moderate down)",
     [G5] + [ballot(b["id"], b["signer"], b["ranking"], ("g",)) for b in H5] + [EC], NOMOD("C") + MOD("A"), "C2"),
    ("C2: a seating with the seated moderator in its past concludes nothing: C holds, D and E rank B, B's seating names EC",
     [G5, LM] + H5 + [EC, ST.withdraw("wd", "D", "bd", ("ec",)), ballot("bd2", "D", "B", ("wd",)),
                      ST.withdraw("we", "E", "be", ("ec",)), ballot("be2", "E", "B", ("we",)),
                      elect("eb", "B", IDS5 + ("wd", "bd2", "we", "be2"))], MOD("C") + NOMOD("B"), "C2"),
    ("C2: a seating of the closed election with a row of the next election in its past concludes nothing",
     [G5, LM] + H5 + [EC] + CLOSE + [WC] + N2 + [elect("eb2", "B", IDS5, cites=("na",))], NOMOD("B"), "C2"),
    # ---- C4 ----------------------------------------------------------------------------------------------------------------
    ("C4: two concurrent seatings, one set within the other: the containing one stands",
     [G5, LM] + H5 + [EC, elect("eb", "B", ("ba", "bb"))], MOD("C") + NOMOD("B"), "C4"),
    ("C4: sets not nested: nobody", [G5, LM] + H5 + [elect("ec", "C", ("bc", "bd", "be")), elect("eb", "B", ("ba", "bb"))],
     NOMOD("B", "C"), "C4"),
    ("C4: and a seating over the union settles it",
     [G5, LM] + H5 + [elect("ec", "C", ("bc", "bd", "be")), elect("eb", "B", ("ba", "bb")), elect("eu", "C", IDS5)],
     MOD("C") + NOMOD("B"), "C4"),
    ("C4: padding by void ballots: a rival over the honest set and A's four-deep ballots for B contains it, and its "
     "count is the honest one: C",
     [G5, LM] + H5 + [EC, ballot("p1", "A", "BCDE"), ballot("p2", "A", "BDCE"), elect("ep", "C", IDS5 + ("p1", "p2"))],
     MOD("C"), "C4"),
    ("C4: a rival omitting a fresh ballot (D withdrew and ranked B) over the rest: not nested with the honest union, nobody",
     [G5, LM] + H5 + [ST.withdraw("wd", "D", "bd", ("bd",)), ballot("bd2", "D", "B", ("wd",)),
                      elect("eb", "B", IDS5 + ("wd", "bd2")), elect("ec2", "C", IDS5 + ("p1",)), ballot("p1", "A", "BCDE")],
     NOMOD("B", "C"), "C4"),
    ("C4: two seatings over one set are one seat; C's withdrawal of either ends it",
     [G5, LM] + H5 + [EC, elect("ec2", "C", IDS5), ST.withdraw("wc", "C", "ec2", ("ec2",))], NOMOD("C"), "C4"),
    ("C4: two seatings over one set: C holds", [G5, LM] + H5 + [EC, elect("ec2", "C", IDS5)], MOD("C"), "C4"),
    # ---- C5 -----------------------------------------------------------------------------------------------------------------
    ("C5: closed by three of the other four; C lays it down; the next election, named by C's seating, seats B",
     [G5, LM] + H5 + [EC] + CLOSE + [WC] + N2 + [EN], MOD("B") + NOMOD("C"), "C5"),
    ("C5: two receipts of four do not close: the next election may not be named by C's seating",
     [G5, LM] + H5 + [EC, ack("k1", "A", "ec"), ack("k2", "B", "ec"), ST.withdraw("wc", "C", "ec", ("k1", "k2"))]
     + [ballot("na", "A", "B", ("wc",), of="ec"), ballot("nb", "B", "B", ("wc",), of="ec"), ballot("nd", "D", "B", ("wc",), of="ec"),
        elect("en", "B", ("na", "nb", "nd"), of="ec")], NOMOD("B", "C"), "C5"),
    ("C5: once closed, a concurrent rival over a containing set counts for nothing: C stands",
     [G5, LM] + H5 + [EC] + CLOSE + [ST.withdraw("wd", "D", "bd", ("bd",)), ballot("bd2", "D", "B", ("wd",)),
                                      ST.withdraw("we", "E", "be", ("be",)), ballot("be2", "E", "B", ("we",)),
                                      elect("eb", "B", IDS5 + ("wd", "bd2", "we", "be2"))], MOD("C") + NOMOD("B"), "C5"),
    ("C5: the same rival with no close: it contains C's set and stands",
     [G5, LM] + H5 + [EC, ST.withdraw("wd", "D", "bd", ("bd",)), ballot("bd2", "D", "B", ("wd",)),
                      ST.withdraw("we", "E", "be", ("be",)), ballot("be2", "E", "B", ("we",)),
                      elect("eb", "B", IDS5 + ("wd", "bd2", "we", "be2"))], MOD("B") + NOMOD("C"), "C5"),
    ("C5: a receipt counts only where its seating stood in the receipt's past: receipts of B's subset seating, each "
     "with C's containing seating in its past, close nothing; C stands",
     [G5, LM] + H5 + [EC, elect("eb", "B", ("ba", "bb")), ack("k1", "A", "eb", ("ec",)), ack("k3", "C", "eb", ("ec",)),
                      ack("k4", "D", "eb", ("ec",))], MOD("C") + NOMOD("B"), "C5"),
    ("C5: receipts of B's subset seating made before C's was seen close the election for B: C's containing seating "
     "is a rival of a closed election",
     [G5, LM] + H5 + [EC, elect("eb", "B", ("ba", "bb")), ack("k1", "A", "eb"), ack("k3", "C", "eb"), ack("k4", "D", "eb")],
     MOD("B") + NOMOD("C"), "C5"),
    ("C5: one say: D receipts C's seating and, concurrently, B's: no say, and A and B alone do not close",
     [G5, LM] + H5 + [EC, elect("eb", "B", ("ba", "bb")), ack("k1", "A", "ec"), ack("k2", "B", "ec"), ack("k4", "D", "ec"),
                      ack("j4", "D", "eb")], MOD("C") + NOMOD("B"), "C5"),
    ("C5, not monotone: C's election closed by A, B and D is reopened by D's concurrent receipt of a rival over a "
     "containing set, and the rival then stands",
     [G5, LM] + H5 + [EC] + CLOSE + [ST.withdraw("wd", "D", "bd", ("bd",)), ballot("bd2", "D", "B", ("wd",)),
                                      ST.withdraw("we", "E", "be", ("be",)), ballot("be2", "E", "B", ("we",)),
                                      elect("eb", "B", IDS5 + ("wd", "bd2", "we", "be2")), ack("j4", "D", "eb")],
     MOD("B") + NOMOD("C"), "C5, point 4"),
    ("C5: a later receipt by D of the rival, with its first in its past, counts for nothing: still closed for C",
     [G5, LM] + H5 + [EC] + CLOSE + [ST.withdraw("wd", "D", "bd", ("bd",)), ballot("bd2", "D", "B", ("wd",)),
                                      ST.withdraw("we", "E", "be", ("be",)), ballot("be2", "E", "B", ("we",)),
                                      elect("eb", "B", IDS5 + ("wd", "bd2", "we", "be2")), ack("j4", "D", "eb", ("k4",))],
     MOD("C") + NOMOD("B"), "C5"),
    ("C5, point 2: a leaver is out of the closing base: E leaves; A and B of A, B, D close",
     [G5, LM] + H5 + [EC, leave("le", "E", "g", ("ec",)), ack("k1", "A", "ec", ("le",)), ack("k2", "B", "ec", ("le",)),
                      ST.withdraw("wc", "C", "ec", ("k1", "k2"))] + N2 + [EN], MOD("B"), "C5, point 2"),
]

# The reviewers' rows (#241, the two reads of the election: r2/a1-a9, scripts/atk, late, readmit), rebuilt on C1-C5
E1 = [ballot("ba", "A", "B"), ballot("bb", "B", "B"), ballot("bc", "C", "B"), elect("e1", "B", ("ba", "bb", "bc")),
      ack("q1", "A", "e1"), ack("q3", "C", "e1"), ack("q4", "D", "e1"), ST.withdraw("wb", "B", "e1", ("q1", "q3", "q4"))]
E2 = [ballot("ba2", "A", "C", ("wb",), of="e1"), ballot("bc2", "C", "C", ("wb",), of="e1"), ballot("bd2", "D", "C", ("wb",), of="e1"),
      elect("e2", "C", ("ba2", "bc2", "bd2"), of="e1")]
PADB = [ballot("bb%d" % i, "B", "B") for i in range(4)]
CASES += [
    ("A3: election 1 closed for B, B resigned, election 2 seats C; D and E fork election 1 at its founding (never "
     "naming e1), padded by D's void ballot: a rival of a closed election, nothing",
     [G5, LM] + E1 + E2 + [ballot("bd", "D", "D"), ballot("be", "E", "D"), ballot("bdv", "D", "ABCD"),
                           elect("e1y", "D", ("bd", "be", "bdv"))], MOD("C") + NOMOD("D", "B"), "C5, A3"),
    ("A5: two seatings of election 1 over one set are one seat, and one election named by either: B laid down on one "
     "branch each, two next elections over sets not nested seat nobody",
     [G5, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), elect("e1", "B", ("ba", "bb")), elect("e1b", "B", ("ba", "bb")),
      ack("q1", "A", "e1"), ack("q3", "C", "e1b"), ack("q4", "D", "e1"),
      ST.withdraw("w1", "B", "e1", ("q1", "q3", "q4")), ST.withdraw("w2", "B", "e1b", ("q1", "q3", "q4")),
      ballot("bc1", "C", "C", ("w1",), of="e1"), ballot("bd1", "D", "C", ("w1",), of="e1"),
      elect("x", "C", ("bc1", "bd1"), of="e1"),
      ballot("bd2", "D", "D", ("w2",), of="e1b"), ballot("be2", "E", "D", ("w2",), of="e1b"),
      elect("y", "D", ("bd2", "be2"), of="e1b")], NOMOD("B", "C", "D"), "C4, A5"),
    ("A6: a seating of election 1 with election 2's seating in its past: nothing (C2), C holds",
     [G5, LM] + E1 + E2 + [ballot("bd", "D", "D", ("e2",)), ballot("be", "E", "D", ("e2",)),
                           elect("e1y", "D", ("bd", "be"))], MOD("C") + NOMOD("D"), "C2, A6"),
    ("atk 1: B's padded seating over its own duplicate ballots is not nested with the honest set: nobody",
     [G5, LM] + H5 + PADB + [EC, elect("eb", "B", ("ba", "bb") + tuple(b["id"] for b in PADB))], NOMOD("B", "C"), "C4, atk 1"),
    ("atk 1: and a seating over the union, B's duplicates one say, seats C",
     [G5, LM] + H5 + PADB + [EC, elect("eb", "B", ("ba", "bb") + tuple(b["id"] for b in PADB)),
                             elect("eu", "C", IDS5 + tuple(b["id"] for b in PADB))], MOD("C") + NOMOD("B"), "C4, atk 1"),
    ("atk 1b: a padding of a non-member's ballots adds nothing to B's set, which C's contains: C",
     [G5, LM] + H5 + [ballot("bx%d" % i, "X", "QQQQ") for i in range(3)]
     + [EC, elect("eb", "B", ("ba", "bb", "bx0", "bx1", "bx2"))], MOD("C") + NOMOD("B"), "C4, atk 1b"),
    ("atk 1c: B's withdrawals of C's ballot are not C's, and add nothing: C",
     [G5, LM] + H5 + [ST.withdraw("wx%d" % i, "B", "bc", ("bc",)) for i in range(3)]
     + [EC, elect("eb", "B", ("ba", "bb", "wx0", "wx1", "wx2"))], MOD("C") + NOMOD("B"), "C4, atk 1c"),
    ("atk 2: B's quick seating over two ballots, then C's over all five naming no row of it: concurrent, C's contains "
     "B's, C", [G5, LM] + H5 + [elect("eb", "B", ("ba", "bb")), EC], MOD("C") + NOMOD("B"), "C4, atk 2"),
    ("atk 2: the same with C's seating naming B's: B holds there, so C's concludes nothing (C2), and B stands",
     [G5, LM] + H5 + [elect("eb", "B", ("ba", "bb")), elect("ec", "C", IDS5, cites=("eb",))], MOD("B") + NOMOD("C"),
     "C2, atk 2"),
    ("two tips, C's seating at one and X's admission at the other: the fold seats C (a seating is read by C1 to C5, "
     "not counted as a plain count) and X", [G5, LM] + H5 + [EC, admit("ax", "X", tuple("ABCDE"), ("lm",))],
     MOD("C") + [("X", "member", T)], "the fold"),
    ("readmit: C left and was admitted again before the vacancy: it votes and stands",
     [G5, leave("lc", "C", "g", ("g",)), admit("ac", "C", ("A", "B", "D", "E"), ("lc",)),
      ST.withdraw("lm", "A", "g", ("ac",), scope="moderate"),
      ballot("ba", "A", "C"), ballot("bc", "C", "C"), ballot("bd", "D", "B"), elect("ec", "C", ("ba", "bc", "bd"))],
     MOD("C"), "C1, readmit"),
]

# small rooms (C5): the closing receipts each needs, the winner apart
def _small(n, receipts):
    G = room(n)
    ks = "ABCDE"[:n]
    win = ks[-1]
    bal = [ballot("b" + k.lower(), k, win) for k in ks]
    s = elect("es", win, tuple(b["id"] for b in bal))
    acks = [ack("k" + k.lower(), k, "es") for k in [x for x in ks if x != win][:receipts]]
    w = ST.withdraw("ws", win, "es", tuple(a["id"] for a in acks) or ("es",))
    nxt = [ballot("n" + k.lower(), k, ks[0], ("ws",), of="es") for k in ks if k != win] or \
        [ballot("na", "A", "A", ("ws",), of="es")]
    if len(nxt) == 1 and n > 1:
        nxt.append(ballot("n" + win.lower(), win, ks[0], ("ws",), of="es"))
    en = elect("en", ks[0], tuple(b["id"] for b in nxt), of="es")
    return [G, LM] + bal + [s] + acks + [w] + nxt + [en]


for n, need in ((1, 0), (2, 1), (3, 2), (4, 2), (5, 3)):
    CASES.append(("C5, a room of %d: %d receipt%s close%s it, and the next election seats A" % (n, need, "" if need == 1 else "s",
                                                                                                 "s" if need == 1 else ""),
                  _small(n, need), MOD("A"), "C5, small rooms"))
    if need:
        CASES.append(("C5, a room of %d: one receipt fewer does not close it" % n, _small(n, need - 1), NOMOD("A"),
                      "C5, small rooms"))

# C1, concurrent ends of one seat: A lays moderate down (lm) and, beside it, B and C recall it (rc), E having left in
# the recall's past only. A seating holding only lm reads E a voice; one holding both does not
RC = ST.unseat("rc", "B", "A", "moderate", OBJ, "group", ("le",), head=("le",), policy="moderator_recall",
               cosigners=("C", "D"))
CE = [G5, LM, leave("le", "E", "g", ("g",)), RC, ballot("ba", "A", "B", ("g",)),
      ballot("bc", "C", "C", ("g",)), ballot("bd", "D", "C", ("g",)), ballot("be", "E", "B", ("g",))]
CASES += [
    ("C1, concurrent ends: a seating holding lm and the recall (E's leaving in its past) reads E no voice: C wins two "
     "to one", CE + [elect("ec", "C", ("ba", "bc", "bd", "be"), cites=("lm", "rc"))], MOD("C"), "C1, point 1"),
    ("C1, concurrent ends: X, admitted in the recall's past only, is no member at lm, so the members at both ends "
     "leave it out: its ballot and A's for it are void, C wins",
     [G5, LM, admit("ax", "X", tuple("ABCDE"), ("g",)),
      ST.unseat("rc", "B", "A", "moderate", OBJ, "group", ("ax",), head=("ax",), policy="moderator_recall",
                cosigners=("C", "D", "E")),
      ballot("bx", "X", "X", ("g",)), ballot("ba", "A", "X", ("g",)), ballot("bc", "C", "C", ("g",)), ballot("bd", "D", "C", ("g",)),
      elect("ec", "C", ("bx", "ba", "bc", "bd"), cites=("lm", "rc"))], MOD("C"), "C1, point 1"),
    ("C1, concurrent ends: a seating holding lm alone reads E a voice: two to two, nobody (the two reads differ)",
     [G5, LM, ballot("ba", "A", "B", ("g",)), ballot("bc", "C", "C", ("g",)), ballot("bd", "D", "C", ("g",)),
      ballot("be", "E", "B", ("g",)), elect("ec", "C", ("ba", "bc", "bd", "be"), cites=("lm",))], NOMOD("C", "B"), "C1, point 1"),
]

OPEN = [
    ("the open case, the candidate rule: C's seating stood and never closed; C lays it down. The next election is "
     "election 1 again; X, admitted since, is no voice: A, B and D's rerun seats B over a set containing C's",
     [G5, LM] + H5 + [EC, admit("ax", "X", tuple("ABCDE"), ("ec",)), ST.withdraw("wc", "C", "ec", ("ax",)),
                      ST.withdraw("wd", "D", "bd", ("wc",)), ballot("bd2", "D", "B", ("wd",)),
                      ST.withdraw("we", "E", "be", ("wc",)), ballot("be2", "E", "B", ("we",)),
                      ballot("bx", "X", "X", ("wc",)),
                      elect("eb", "B", IDS5 + ("wd", "bd2", "we", "be2", "bx"))],
     MOD("B") + NOMOD("C", "X"), "candidates: (i) the candidate rule, as built; (ii) ELECTION_OPEN_NEXT"),
    ("the open case: the whole first electorate has left; the room's new members can never seat anyone",
     [G2, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), elect("eb", "B", ("ba", "bb")),
      admit("ax", "X", ("A", "B"), ("eb",)), admit("ay", "Y", ("A", "B", "X"), ("ax",)),
      ST.withdraw("wb", "B", "eb", ("ay",)), leave("la", "A", "g", ("wb",)), leave("lb", "B", "eb", ("la",)),
      ballot("bx", "X", "Y", ("lb",)), ballot("by", "Y", "Y", ("lb",)), elect("ey", "Y", ("bx", "by"))],
     NOMOD("Y", "B"), "candidates: (i) locked, as built; (ii) ELECTION_OPEN_NEXT names B's seating, whose vacancy holds X and Y"),
]


# the open case's alternative, behind ELECTION_OPEN_NEXT: an unclosed seating whose holder has ended names the next
# election, read at its own vacancy (C1)
OC = [G5, LM] + H5 + [EC, admit("ax", "X", tuple("ABCDE"), ("ec",)), ST.withdraw("wc", "C", "ec", ("ax",))]
NEXT_CASES = [
    ("ELECTION_OPEN_NEXT: C's unclosed seating, laid down, names the next election; X, admitted before that vacancy, "
     "votes in it, and B is seated",
     OC + [ballot("na", "A", "B", ("wc",), of="ec"), ballot("nb", "B", "B", ("wc",), of="ec"), ballot("nx", "X", "B", ("wc",), of="ec"),
           elect("en", "B", ("na", "nb", "nx"), of="ec")], MOD("B"), "the open case (ii)"),
    ("ELECTION_OPEN_NEXT, C2: a rerun of election 1 with a row of that next election in its past concludes nothing",
     OC + [ballot("na", "A", "B", ("wc",), of="ec"), ballot("nb", "B", "B", ("wc",), of="ec"), ballot("nx", "X", "B", ("wc",), of="ec"),
           elect("en", "B", ("na", "nb", "nx"), of="ec"),
           ST.withdraw("wa", "A", "ba", ("wc",)), ballot("ba2", "A", "D", ("wa",)), ST.withdraw("wd", "D", "bd", ("wc",)),
           ballot("bd2", "D", "D", ("wd",)), ST.withdraw("we", "E", "be", ("wc",)), ballot("be2", "E", "D", ("we",)),
           elect("ed", "D", IDS5 + ("wa", "ba2", "wd", "bd2", "we", "be2"), cites=("na",))], MOD("B") + NOMOD("D"),
     "C2, the open case (ii)"),
    ("ELECTION_OPEN_NEXT: the room whose first electorate has all left elects again, named by B's laid-down seating",
     [G2, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), elect("eb", "B", ("ba", "bb")),
      admit("ax", "X", ("A", "B"), ("eb",)), admit("ay", "Y", ("A", "B", "X"), ("ax",)),
      ST.withdraw("wb", "B", "eb", ("ay",)), leave("la", "A", "g", ("wb",)), leave("lb", "B", "eb", ("la",)),
      ballot("bx", "X", "Y", ("lb",), of="eb"), ballot("by", "Y", "Y", ("lb",), of="eb"), elect("ey", "Y", ("bx", "by"), of="eb")],
     MOD("Y"), "the open case (ii)"),
]


@contextlib.contextmanager
def planted(plant, open_next=False):
    saved, on = set(ST.MUT), ST.ELECTION_OPEN_NEXT
    if plant:
        ST.MUT.add(plant)
    ST.ELECTION_OPEN_NEXT = open_next
    try:
        yield
    finally:
        ST.MUT.clear(); ST.MUT |= saved
        ST.ELECTION_OPEN_NEXT = on


PLANTS = ("vacancy_founding", "vacancy_first_end", "electorate_at_seating", "leaver_voice", "c2_holder_unread",
          "c2_later_unread", "contains_unread", "twin_withdrawal_unread", "close_unread", "receipt_standing_unread",
          "say_any_receipt", "close_leavers_kept", "closed_rivals_count", "election_id_any", "set_any_signer",
          "ballot_nonmember_ranked", "ballot_ranks_unbounded", "seating_any_signer", "twin_ids_apart",
          "fold_ranked_counted")


def answers(rows, asks, plant=None, arrive=False, open_next=False):
    with planted(plant, open_next):
        S = CK.arrive(list(rows), RULE) if arrive else CK.concluded(CK.kept(list(rows)), RULE)
        Q = ST.Seats(S)
        return [Q.stands(k, s, OBJ) for k, s, _ in asks]


def orders(rows, n=200):
    tail = rows[1:]
    if len(tail) <= 6:
        return list(itertools.permutations(tail))
    rnd = random.Random(len(tail))
    out = [tail, tail[::-1]]
    for _ in range(n - 2):
        p = list(tail); rnd.shuffle(p); out.append(p)
    return out


def main():
    t0 = time.time()
    problems, n_orders = [], 0
    for name, rows, asks, _item in CASES + [o[:3] + (o[3],) for o in OPEN]:
        want = [w for _, _, w in asks]
        got = answers(rows, asks)
        if got != want:
            problems.append("%s: got %s, expected %s" % (name, got, want))
        for p in orders(rows, 40):
            n_orders += 1
            if answers([rows[0]] + list(p), asks, arrive=True) != got:
                problems.append("%s: order %s differs" % (name, [r["id"] for r in p]))
                break
    for name, rows, asks, _item in NEXT_CASES:
        got = answers(rows, asks, open_next=True)
        if got != [w for _, _, w in asks]:
            problems.append("%s: got %s, expected %s" % (name, got, [w for _, _, w in asks]))
        for p in orders(rows, 40):
            n_orders += 1
            if answers([rows[0]] + list(p), asks, arrive=True, open_next=True) != got:
                problems.append("%s: order %s differs" % (name, [r["id"] for r in p]))
                break
    for name, rows, asks, cands in OPEN:
        print("  OPEN %s\n    %s; with ELECTION_OPEN_NEXT: %s" % (name, cands, answers(rows, asks, open_next=True)))
    caught = 0
    for plant in PLANTS:
        hit = [name for name, rows, asks, _ in CASES if answers(rows, asks, plant) != [w for _, _, w in asks]]
        hit += [name for name, rows, asks, _ in NEXT_CASES if answers(rows, asks, plant, open_next=True) != [w for _, _, w in asks]]
        caught += bool(hit)
        print("  plant %-24s %s" % (plant, "caught by %d cases, first: %s" % (len(hit), hit[0][:90]) if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % plant)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases, %d behind ELECTION_OPEN_NEXT, %d open, %d orders, %d of %d planted breaks caught (%.0fs)"
          % ("ok" if not problems else "%d problems" % len(problems), len(CASES), len(NEXT_CASES), len(OPEN), n_orders, caught,
             len(PLANTS), time.time() - t0))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
