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

The rulings E1 to E3 on it: E1, a leaver (left or removed) is out of C5's closing base, read in each receipt's past;
everyone but the winner gone, the seating closes itself. E2, an equivocator's two receipts are no say and it stays in
the base; the election is open again for everyone alike; the way back is to remove it. E3, once its holder's seat has
ended, a seating that stood and never closed names the next election, C3 deciding between rival ids by past; the cost:
two lines in two next elections until one id's standing is settled in the other's past. CLOSE_CASES read the close
directly. F1 to F4 (the third read): every input to a count from the set; the vacancy part of the set; a next election
stands only while its id row stands, for the rows held. PENDING: a case the merged tree must pass once the head
rules land.

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


def elect(i, k, rows, of="g", cites=(), signer=None, vac=None):
    """The seating of k (its acceptance, signed by k) over the rows named, of election `of`, naming the end or ends of
    the seat it reads the electorate at (`vac`, F2: `lm` for the founding election of these rooms); `cites` rows it
    names beside its set."""
    vac = ("lm",) if vac is None and of == "g" else tuple(vac or ())
    return ST.offer(i, signer or k, k, "moderate", OBJ, "group", tuple(rows) + vac + tuple(cites),
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
EN = elect("en", "B", tuple(b["id"] for b in N2), of="ec", vac=("wc",))

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
    ("E3: two receipts of four do not close; C's seating stood and C laid it down, so it names the next election, "
     "which seats B",
     [G5, LM] + H5 + [EC, ack("k1", "A", "ec"), ack("k2", "B", "ec"), ST.withdraw("wc", "C", "ec", ("k1", "k2"))]
     + [ballot("na", "A", "B", ("wc",), of="ec"), ballot("nb", "B", "B", ("wc",), of="ec"), ballot("nd", "D", "B", ("wc",), of="ec"),
        elect("en", "B", ("na", "nb", "nd"), of="ec", vac=("wc",))], MOD("B") + NOMOD("C"), "E3"),
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
      elect("e2", "C", ("ba2", "bc2", "bd2"), of="e1", vac=("wb",))]
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
      elect("x", "C", ("bc1", "bd1"), of="e1", vac=("w1",)),
      ballot("bd2", "D", "D", ("w2",), of="e1b"), ballot("be2", "E", "D", ("w2",), of="e1b"),
      elect("y", "D", ("bd2", "be2"), of="e1b", vac=("w2",))], NOMOD("B", "C", "D"), "C4, A5"),
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

# C1, concurrent ends of one seat: A lays moderate down (lm) and, beside it, B and C recall it (rc), E having left in
# the recall's past only. A seating holding only lm reads E a voice; one holding both does not
RC = ST.unseat("rc", "B", "A", "moderate", OBJ, "group", ("le",), head=("le",), policy="moderator_recall",
               cosigners=("C", "D"))
CE = [G5, LM, leave("le", "E", "g", ("g",)), RC, ballot("ba", "A", "B", ("g",)),
      ballot("bc", "C", "C", ("g",)), ballot("bd", "D", "C", ("g",)), ballot("be", "E", "B", ("g",))]
CASES += [
    ("C1, concurrent ends: a seating holding lm and the recall (E's leaving in its past) reads E no voice: C wins two "
     "to one", CE + [elect("ec", "C", ("ba", "bc", "bd", "be"), vac=("lm", "rc"), cites=("le",))], MOD("C"), "C1, point 1"),
    ("C1, concurrent ends: X, admitted in the recall's past only, is no member at lm, so the members at both ends "
     "leave it out: its ballot and A's for it are void, C wins",
     [G5, LM, admit("ax", "X", tuple("ABCDE"), ("g",)),
      ST.unseat("rc", "B", "A", "moderate", OBJ, "group", ("ax",), head=("ax",), policy="moderator_recall",
                cosigners=("C", "D", "E")),
      ballot("bx", "X", "X", ("g",)), ballot("ba", "A", "X", ("g",)), ballot("bc", "C", "C", ("g",)), ballot("bd", "D", "C", ("g",)),
      elect("ec", "C", ("bx", "ba", "bc", "bd"), vac=("lm", "rc"))], MOD("C"), "C1, point 1"),
    ("C1, concurrent ends: a seating holding lm alone reads E a voice: two to two, nobody (the two reads differ)",
     [G5, LM, ballot("ba", "A", "B", ("g",)), ballot("bc", "C", "C", ("g",)), ballot("bd", "D", "C", ("g",)),
      ballot("be", "E", "B", ("g",)), elect("ec", "C", ("ba", "bc", "bd", "be"))], NOMOD("C", "B"), "C1, point 1"),
]

# E3 (ruled): once its holder's seat has ended, a seating that stood and never closed names the next election, C3
# deciding between rival ids by past. OC: C's seating stood, never closed; X is admitted; C lays it down
OC = [G5, LM] + H5 + [EC, admit("ax", "X", tuple("ABCDE"), ("ec",)), ST.withdraw("wc", "C", "ec", ("ax",))]
N_OC = [ballot("na", "A", "B", ("wc",), of="ec"), ballot("nb", "B", "B", ("wc",), of="ec"), ballot("nx", "X", "B", ("wc",), of="ec"),
        elect("en", "B", ("na", "nb", "nx"), of="ec", vac=("wc",))]
RERUN = [ST.withdraw("wd", "D", "bd", ("wc",)), ballot("bd2", "D", "B", ("wd",)), ST.withdraw("we", "E", "be", ("wc",)),
         ballot("be2", "E", "B", ("we",)), ballot("bx", "X", "X", ("wc",)), elect("eb", "B", IDS5 + ("wd", "bd2", "we", "be2", "bx"))]
LOCK = [G2, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), elect("eb", "B", ("ba", "bb")),
        admit("ax", "X", ("A", "B"), ("eb",)), admit("ay", "Y", ("A", "B", "X"), ("ax",)),
        ST.withdraw("wb", "B", "eb", ("ay",)), leave("la", "A", "g", ("wb",)), leave("lb", "B", "eb", ("la",))]
# the E3 cost: two seatings of election 1 concurrent, each read alone by a reader that then opens a next election
S2 = elect("eb", "B", ("ba", "bb"))
COST = [G5, LM] + H5 + [EC, S2, ST.withdraw("wc", "C", "ec", ("ec",)), ST.withdraw("wb", "B", "eb", ("eb",)),
                        ballot("pa", "A", "D", ("wc",), of="ec"), ballot("pd", "D", "D", ("wc",), of="ec"),
                        elect("n1", "D", ("pa", "pd"), of="ec", vac=("wc",)),
                        ballot("qb", "B", "E", ("wb",), of="eb"), ballot("qe", "E", "E", ("wb",), of="eb"),
                        elect("n2", "E", ("qb", "qe"), of="eb", vac=("wb",))]
CASES += [
    ("E3: C's unclosed seating, laid down, names the next election; X, admitted before that vacancy, votes in it, and "
     "B is seated", OC + N_OC, MOD("B"), "E3"),
    ("E3, C3: a rerun of election 1 after C's seating stood and ended concludes nothing (the next election is named "
     "by C's seating): X never votes there, and B is not seated by it", OC + RERUN, NOMOD("B", "C", "X"), "E3, C3"),
    ("E3: the room whose first electorate has all left elects again, named by B's laid-down seating",
     LOCK + [ballot("bx", "X", "Y", ("lb",), of="eb"), ballot("by", "Y", "Y", ("lb",), of="eb"),
             elect("ey", "Y", ("bx", "by"), of="eb", vac=("wb",))], MOD("Y"), "E3"),
    ("F3, the stated cost: C's and B's seatings of election 1, concurrent, each laid down on its own line, each line "
     "opening a next election: a reader of either line alone is in that line's next election; where both are held C4 "
     "beats B's seating, and B's next election falls with it (a next election stands only while its id row stands): "
     "D alone", COST, MOD("D") + NOMOD("E"), "F3, the cost"),
    ("F3: and a further seating of B's next election holding C's seating (which contains B's) concludes nothing",
     COST + [elect("n2b", "E", ("qb", "qe"), cites=("wc",), of="eb", vac=("wb",))], MOD("D"), "F3, the cost"),
    ("E2, C3: closed by A, B and D; C lays it down; the next election seats B; then D receipts a rival of C's seating, "
     "concurrently: election 1 is open again, and election 2, named in its own past by a closed seating, does not "
     "fall with it", [G5, LM] + H5 + [EC] + CLOSE + [WC] + N2 + [EN, elect("es", "B", ("ba", "bb")), ack("j4", "D", "es")],
     MOD("B") + NOMOD("C"), "E2, E3, C3"),
    ("E2: a close holds while no receipter it needs has said two things: D's concurrent receipt of B's subset seating "
     "reopens C's election, and C still stands (the rival is contained: nobody is unseated by the reopening itself)",
     [G5, LM] + H5 + [EC, elect("es", "B", ("ba", "bb"))] + CLOSE + [ack("j4", "D", "es")], MOD("C") + NOMOD("B"), "E2"),
]
# C5's close read directly: (name, rows, the seating, closed)
def _small(n, receipts):
    ks = "ABCDE"[:n]
    win = ks[-1]
    bal = [ballot("b" + k.lower(), k, win) for k in ks]
    acks = [ack("k" + k.lower(), k, "es") for k in [x for x in ks if x != win][:receipts]]
    return [room(n), LM] + bal + [elect("es", win, tuple(b["id"] for b in bal))] + acks


CLOSE_CASES = []
for n, need in ((1, 0), (2, 1), (3, 2), (4, 2), (5, 3)):
    CLOSE_CASES.append(("C5, a room of %d: %d receipt%s close%s it" % (n, need, "" if need == 1 else "s",
                                                                     "s" if need == 1 else ""), _small(n, need), "es", T))
    if need:
        CLOSE_CASES.append(("C5, a room of %d: one receipt fewer does not" % n, _small(n, need - 1), "es", F))
EQV = [G5, LM] + H5 + [EC, elect("es", "B", ("ba", "bb"))] + CLOSE + [ack("j4", "D", "es")]
RMD = ST.unseat("rd", "A", "D", "member", OBJ, "group", ("k1", "k2", "k4", "j4"), head=("lm",), policy="community_remove",
                cosigners=("B", "C", "E"))
CLOSE_CASES += [
    ("E1, the limit: everyone but the winner has left after C's seating: the base is empty and it closes itself",
     [G3, LM, ballot("bb", "B", "C"), ballot("bc", "C", "C"), elect("ec", "C", ("bb", "bc")),
      leave("la", "A", "g", ("ec",)), leave("lb", "B", "g", ("la",))], "ec", T),
    ("E1: one of the two others still there: no receipt, no close",
     [G3, LM, ballot("bb", "B", "C"), ballot("bc", "C", "C"), elect("ec", "C", ("bb", "bc")), leave("la", "A", "g", ("ec",))],
     "ec", F),
    ("E2: closed by A, B and D", [G5, LM] + H5 + [EC, elect("es", "B", ("ba", "bb"))] + CLOSE, "ec", T),
    ("E2: D's concurrent receipt of a rival: no say, and D stays in the base: A and B are two of four, not closed", EQV, "ec", F),
    ("E2, the way back: the room removes D by count, its two receipts as evidence; E receipts C's seating after: D is "
     "out of the base in E's receipt's past, and A, B and E close it",
     EQV + [RMD, ack("k5", "E", "ec", ("rd",))], "ec", T),
    ("E2: the removal alone, read in A's and B's receipts' past (where D is no leaver), does not close it",
     EQV + [RMD], "ec", F),
]
# The third read (r51c, b1 to b6) and the rulings F1 to F4
H7 = [ballot("b" + k.lower(), k, r) for k, r in zip("ABCDEFG", "BBBCCCC")]
IDS7 = tuple(b["id"] for b in H7)
EC7 = elect("ec", "C", IDS7)
CLOSE7 = [ack("k" + k.lower(), k, "ec") for k in "ABDE"]
WFG = [ST.withdraw("wf", "F", "bf", ("bf",)), ST.withdraw("wg", "G", "bg", ("bg",)), R("nt", "note", "B", ("wf", "wg"))]
# b2: A lays moderate down twice, on two lines, F admitted on one of them before its end
LM1 = ST.withdraw("lm1", "A", "g", ("g",), scope="moderate")
AF = admit("aF", "F", tuple("ABCDE"), ("g",))
LM2 = ST.withdraw("lm2", "A", "g", ("aF",), scope="moderate")
HB2 = [ballot("ba", "A", "F", ("lm2",)), ballot("bb", "B", "F", ("lm2",)), ballot("bc", "C", "F", ("lm2",)),
       ballot("bd", "D", "C", ("lm2",)), ballot("be", "E", "C", ("lm2",))]
IDB2 = tuple(b["id"] for b in HB2)
# b3: a partition {A, C} and {B, D}; E votes and receipts on both
AL = [ballot("a1", "A", "B"), ballot("c1", "C", "B"), ballot("e1", "E", "B"), elect("s1", "B", ("a1", "c1", "e1")),
      ack("ka", "A", "s1"), ack("kc", "C", "s1"), ack("ke1", "E", "s1")]
BE = [ballot("b2", "B", "C"), ballot("d2", "D", "C"), ballot("e2", "E", "C"), elect("s2", "C", ("b2", "d2", "e2")),
      ack("kb", "B", "s2"), ack("kd", "D", "s2"), ack("ke2", "E", "s2")]
NA = [ST.withdraw("wB", "B", "s1", ("ka", "kc", "ke1")), ballot("n1", "A", "A", ("wB",), of="s1"),
      ballot("n2", "C", "A", ("wB",), of="s1"), elect("x1", "A", ("n1", "n2"), of="s1", vac=("wB",))]
NB = [ST.withdraw("wC", "C", "s2", ("kb", "kd", "ke2")), ballot("m1", "B", "D", ("wC",), of="s2"),
      ballot("m2", "D", "D", ("wC",), of="s2"), elect("x2", "D", ("m1", "m2"), of="s2", vac=("wC",))]
# b4: election 1 unclosed, B resigns, election 2 seats C; three fork election 1 from lm with a superset of its set
E1R = [ballot("ba", "A", "B"), ballot("bb", "B", "B"), elect("e1", "B", ("ba", "bb")), ST.withdraw("wb", "B", "e1", ("e1",))]
E2R = [ballot("ba2", "A", "C", ("wb",), of="e1"), ballot("bc2", "C", "C", ("wb",), of="e1"), ballot("bd2", "D", "C", ("wb",), of="e1"),
       elect("e2", "C", ("ba2", "bc2", "bd2"), of="e1", vac=("wb",))]
ATK4 = [ballot("be", "E", "D"), ballot("bf", "F", "D"), ballot("bg", "G", "D"), elect("e1x", "D", ("ba", "bb", "be", "bf", "bg"))]
CASES += [
    ("F1 (b1): B's seating over the same set as C's closed one, F's and G's withdrawals in its past but not in its set: "
     "the same count, so it is no twin with another winner: one moderator, C",
     [room(7), LM] + H7 + [EC7] + CLOSE7 + WFG + [elect("eb", "B", IDS7, cites=("nt",))], MOD("C") + NOMOD("B"), "F1"),
    ("F1 (b1): the same before any receipt: one moderator, C", [room(7), LM] + H7 + [EC7] + WFG
     + [elect("eb", "B", IDS7, cites=("nt",))], MOD("C") + NOMOD("B"), "F1"),
    ("F1: a seating that names the withdrawals counts them, and contains C's: before the close it stands, B",
     [room(7), LM] + H7 + [EC7] + WFG + [elect("eb", "B", IDS7 + ("wf", "wg"))], MOD("B") + NOMOD("C"), "F1"),
    ("F2 (b2): F's seating names lm2 (F a member there), C's names lm1 (F no member there): different vacancies are "
     "different sets, not nested: nobody",
     [G5, LM1, AF, LM2] + HB2 + [elect("ef", "F", IDB2, vac=("lm2",)), elect("ec", "C", IDB2, vac=("lm1",))],
     NOMOD("F", "C"), "F2"),
    ("F2 (b2): F's seating alone (the end at lm2): F", [G5, AF, LM2] + HB2 + [elect("ef", "F", IDB2, vac=("lm2",))],
     MOD("F"), "F2"),
    ("F2: and a seating over the union, naming both ends: the members at both leave F out, the ballots for F are void: C",
     [G5, LM1, AF, LM2] + HB2 + [elect("ef", "F", IDB2, vac=("lm2",)), elect("ec", "C", IDB2, vac=("lm1",)),
                                  elect("eu", "C", IDB2, vac=("lm1", "lm2"))], NOMOD("F") + MOD("C"), "F2"),
    ("F3 (b3), one side: B's seating closed by A, C and E: B", [G5, LM] + AL, MOD("B"), "F3"),
    ("F3 (b3), both sides held: E said two things, neither closes; the sets are not nested, so nobody is seated "
     "until a seating over their union (a close holds while no receipter it needs has said two things; when it fails "
     "over non-nested sets nobody is seated until a seating over their union)", [G5, LM] + AL + BE, NOMOD("B", "C"), "F3"),
    ("F3 (b3): with each side's next election held too, each falls with its id row: nobody",
     [G5, LM] + AL + BE + NA + NB, NOMOD("A", "B", "C", "D"), "F3"),
    ("F3 (b3): one side with its next election: A", [G5, LM] + AL + NA, MOD("A"), "F3"),
    ("F4 (b4): honest: election 1 unclosed, B resigns, election 2 seats C", [room(7), LM] + E1R + E2R, MOD("C"), "F4"),
    ("F4 (b4): three fork election 1 from lm with a superset: election 1's seating is beaten, election 2 falls with it, "
     "and D, seated by the fork, stands for a reader with no acknowledgement (the head rules judge a reader's line)",
     [room(7), LM] + E1R + E2R + ATK4, MOD("D") + NOMOD("C", "B"), "F4"),
]
CASES += [
    ("F2: a seating that names no end of the seat reads no electorate: nothing", [G5, LM] + H5 + [elect("ec", "C", IDS5, vac=())],
     NOMOD("C"), "F2"),
    ("C3: a seating naming as its election a row that is no election (A's laying down) concludes nothing",
     [G5, LM] + [ballot(b["id"], b["signer"], b["ranking"], of="lm") for b in H5] + [elect("ec", "C", IDS5, of="lm", vac=())],
     NOMOD("C"), "C3"),
    ("C2: a rerun of election 1 with a row of the next election in its past concludes nothing, where no seating of "
     "election 1 stands in its past (C's and B's are not nested) to supersede it",
     [G5, LM] + H5 + [EC, ST.withdraw("wd", "D", "bd", ("bd",)), ballot("bd2", "D", "B", ("wd",)),
                      elect("e3", "B", ("ba", "bb", "wd", "bd2")), ST.withdraw("wb3", "B", "e3", ("e3",)),
                      ST.withdraw("wc", "C", "ec", ("ec",)), ballot("na", "A", "A", ("wc",), of="ec"),
                      elect("er", "B", IDS5 + ("wd", "bd2"), cites=("na", "wb3"))], NOMOD("B", "C"), "C2"),
]
# b6: twins over equal sets count alike under F1, so the close's base is read the same from either: (regression)
B6 = [G5, LM1, AF, LM2] + HB2 + [elect("ef", "F", IDB2, vac=("lm2",)), elect("ef2", "F", IDB2, vac=("lm2",)),
                                 ack("ka", "A", "ef"), ack("kb", "B", "ef"), ack("kc", "C", "ef2"), ack("kd", "D", "ef2")]
CLOSE_CASES += [
    ("b6 (regression): twins over one set, receipted two and two: one seat, one base, closed by four of five", B6, "ef", T),
    ("b6: the same asked of the other twin", B6, "ef2", T),
]
# b5: the old-head removal reaching the election is the head rules' (H1 to H7); this tree does not read it. Kept as a
# case the merged tree must pass once `heads` lands: PENDING until then
GB5 = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("C",)}, cosigners=("B", "C"))
B5 = [GB5]
_prev, _mem = "g", ["A", "B", "C"]
for _k in "DEFG":
    B5.append(admit("a" + _k, _k, tuple(_mem), (_prev,))); _mem.append(_k); _prev = "a" + _k
XC5 = ST.unseat("xc", "A", "C", "member", OBJ, "group", ("g", "aG"), head=("g",), policy="community_remove", cosigners=("B",))
PENDING = [
    ("b5, PENDING the head rules: A and B remove C at the founding head (two of three there) and elect A: the removal "
     "names an old head, so it concludes nothing and C keeps the seat",
     B5 + [XC5, ballot("ba", "A", "A", ("xc",)), ballot("bb", "B", "A", ("xc",)), elect("ea", "A", ("ba", "bb"), vac=("xc",))],
     MOD("C") + NOMOD("A"), "b5"),
]


@contextlib.contextmanager
def planted(plant):
    saved = set(ST.MUT)
    if plant:
        ST.MUT.add(plant)
    try:
        yield
    finally:
        ST.MUT.clear(); ST.MUT |= saved


PLANTS = ("vacancy_founding", "vacancy_first_end", "electorate_at_seating", "leaver_voice", "c2_holder_unread",
          "c2_later_unread", "contains_unread", "twin_withdrawal_unread", "close_unread", "receipt_standing_unread",
          "say_any_receipt", "close_leavers_kept", "closed_rivals_count", "election_id_any", "set_any_signer",
          "ballot_nonmember_ranked", "ballot_ranks_unbounded", "seating_any_signer", "twin_ids_apart",
          "fold_ranked_counted", "equivocator_out", "superseded_unread", "wait_close", "id_cascade_unread",
          "vacancy_unnamed", "set_inputs_unread")


def answers(rows, asks, plant=None, arrive=False):
    with planted(plant):
        S = CK.arrive(list(rows), RULE) if arrive else CK.concluded(CK.kept(list(rows)), RULE)
        Q = ST.Seats(S)
        return [Q.stands(k, s, OBJ) for k, s, _ in asks]


def closed(rows, seating, plant=None, arrive=False):
    with planted(plant):
        S = CK.arrive(list(rows), RULE) if arrive else CK.concluded(CK.kept(list(rows)), RULE)
        past = lambda a, b: a in S.anc[b]
        q = S.by[seating]
        if not S.C.get(seating): return False
        v = ST.seating_view(q, [x for x in S.Cs if past(x["id"], seating)], past)
        return ST.closure(v[0], S.Cs, past, OBJ) == v[2]


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
    for name, rows, asks, _item in CASES:
        want = [w for _, _, w in asks]
        got = answers(rows, asks)
        if got != want:
            problems.append("%s: got %s, expected %s" % (name, got, want))
        for p in orders(rows, 40):
            n_orders += 1
            if answers([rows[0]] + list(p), asks, arrive=True) != got:
                problems.append("%s: order %s differs" % (name, [r["id"] for r in p]))
                break
    for name, rows, seating, want in CLOSE_CASES:
        got = closed(rows, seating)
        if got != want:
            problems.append("%s: closed %s, expected %s" % (name, got, want))
        for p in orders(rows, 200 if name.startswith("b6") else 40):
            n_orders += 1
            if closed([rows[0]] + list(p), seating, arrive=True) != got:
                problems.append("%s: order %s differs" % (name, [r["id"] for r in p]))
                break
    for name, rows, asks, _item in PENDING:
        got = answers(rows, asks)
        print("  PENDING %s: %s (expected once the head rules land: %s)" % (name, got, [w for _, _, w in asks]))
    caught = 0
    for plant in PLANTS:
        hit = [name for name, rows, asks, _ in CASES if answers(rows, asks, plant) != [w for _, _, w in asks]]
        hit += [name for name, rows, sq, want in CLOSE_CASES if closed(rows, sq, plant) != want]
        caught += bool(hit)
        print("  plant %-24s %s" % (plant, "caught by %d cases, first: %s" % (len(hit), hit[0][:90]) if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % plant)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases, %d of the close, %d pending the head rules, %d orders, %d of %d planted breaks caught (%.0fs)"
          % ("ok" if not problems else "%d problems" % len(problems), len(CASES), len(CLOSE_CASES), len(PENDING),
             n_orders, caught, len(PLANTS), time.time() - t0))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
