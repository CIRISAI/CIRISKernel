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
stands only while its id row stands, for the rows held. b5, H2b, G3c and G3b, once written as waiting for the head
rules, are cases (b5) and line cases (H2b, G3c, G3b). The ruled election close (one election per seat end, the
opening row, the electorate at its heads, the wait) is check_election_close.py; this file's worlds, written before the
opening row, are read with their openings (election_worlds.opened), and the cases the ruling restates say so.

Every case is a hand-written answer, read in every arrival order of its rows above the founding one (a fixed sample of
200 where there are more than six). Each names the rule it rests on.

Planted breaks (seat.MUT), each of which must change a case's answer:
    vacancy_founding        the electorate read at the id row, not at its vacancy (C1)
    vacancy_first_end       one end of the seat read, the others not (C1, concurrent ends)
    electorate_folded       the ends of the vacancy read as one fold of heads, not each alone (C1: since the head rules
                            several heads are folded, so the persons common to the ends are taken per end)
    electorate_at_seating   the electorate read over the seating's whole past (a member admitted after the vacancy votes)
    leaver_voice            a member whose leaving is in the seating's set is a voice
    electorate_reads_past   the electorate read with every withdrawal in the seating's past, named or not (C1, F1, F2:
                            a leaving the seating does not name strikes nobody)
    laydown_off_line        a lay-down behind a reader's line is still a vacancy end for it (H4, the Constitution's
                            ruling: a lay-down is a roster change and sits on the reader's line)
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


def elect(i, k, rows, of="g", cites=(), signer=None, vac=None, head=()):
    """The seating of k (its acceptance, signed by k) over the rows named, of election `of`, naming the end or ends of
    the seat it reads the electorate at (`vac`, F2: `lm` for the founding election of these rooms); `cites` rows it
    names beside its set."""
    vac = ("lm",) if vac is None and of == "g" else tuple(vac or ())
    kw = {"head": tuple(head)} if head else {}
    return ST.offer(i, signer or k, k, "moderate", OBJ, "group", tuple(rows) + vac + tuple(cites) + tuple(head),
                    policy="moderator_election", of=of, **kw)


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

# seven members, C four to three over B (C, D, E, F; A, B, G)
H7C = [ballot("b" + k.lower(), k, r) for k, r in zip("ABCDEFG", "BBCCCCB")]
IDS7C = tuple(b["id"] for b in H7C)
EC7C = elect("ec", "C", IDS7C)

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
    ("C5, (2), the edge: closed by A, B and D (three of four); a concurrent rival over a containing set, made by D's "
     "and E's changed ballots and seated by B: D (its change beside its receipt) and B (its seating beside its "
     "receipt) each said two things, so both are out of the base and no voice: A alone of A and E does not hold the "
     "close, and the rival, containing C's set, stands",
     [G5, LM] + H5 + [EC] + CLOSE + [ST.withdraw("wd", "D", "bd", ("bd",)), ballot("bd2", "D", "B", ("wd",)),
                                      ST.withdraw("we", "E", "be", ("be",)), ballot("be2", "E", "B", ("we",)),
                                      elect("eb", "B", IDS5 + ("wd", "bd2", "we", "be2"))], MOD("B") + NOMOD("C"), "C5, (2)"),
    ("C5: the same rival with no close: it contains C's set and stands",
     [G5, LM] + H5 + [EC, ST.withdraw("wd", "D", "bd", ("bd",)), ballot("bd2", "D", "B", ("wd",)),
                      ST.withdraw("we", "E", "be", ("be",)), ballot("be2", "E", "B", ("we",)),
                      elect("eb", "B", IDS5 + ("wd", "bd2", "we", "be2"))], MOD("B") + NOMOD("C"), "C5"),
    ("C5: a receipt counts only where its seating stood in the receipt's past: receipts of B's subset seating, each "
     "with C's containing seating in its past, close nothing; C stands",
     [G5, LM] + H5 + [EC, elect("eb", "B", ("ba", "bb")), ack("k1", "A", "eb", ("ec",)), ack("k3", "C", "eb", ("ec",)),
                      ack("k4", "D", "eb", ("ec",))], MOD("C") + NOMOD("B"), "C5"),
    ("C5, (2): receipts of B's subset seating by A, C and D, none with C's seating in its past: C's receipt beside its "
     "own seating, and D's beside its own ballot (not in B's set), are each two things, so C and D are out of the base; "
     "A alone of A and E does not close it, and C's containing seating stands",
     [G5, LM] + H5 + [EC, elect("eb", "B", ("ba", "bb")), ack("k1", "A", "eb"), ack("k3", "C", "eb"), ack("k4", "D", "eb")],
     MOD("C") + NOMOD("B"), "C5, (2)"),
    ("C5: receipts of B's subset seating by voters each with its own ballot in its past (A, whose ballot B's set holds, "
     "and E, naming its own): two of the four others is no close, and C's containing seating stands",
     [G5, LM] + H5 + [EC, elect("eb", "B", ("ba", "bb")), ack("k1", "A", "eb"), ack("k5", "E", "eb", ("be",))],
     MOD("C") + NOMOD("B"), "C5"),
    ("C5, (2): D receipts C's seating and, concurrently, B's: D said two things, no voice and out of the base; A and B "
     "of A, B, E hold the close, and C stands",
     [G5, LM] + H5 + [EC, elect("eb", "B", ("ba", "bb")), ack("k1", "A", "ec"), ack("k2", "B", "ec"), ack("k4", "D", "ec"),
                      ack("j4", "D", "eb")], MOD("C") + NOMOD("B"), "C5"),
    ("C5, not monotone: C's election closed by A, B and D is reopened by D's concurrent receipt of a rival over a "
     "containing set, and the rival then stands",
     [G5, LM] + H5 + [EC] + CLOSE + [ST.withdraw("wd", "D", "bd", ("bd",)), ballot("bd2", "D", "B", ("wd",)),
                                      ST.withdraw("we", "E", "be", ("be",)), ballot("be2", "E", "B", ("we",)),
                                      elect("eb", "B", IDS5 + ("wd", "bd2", "we", "be2")), ack("j4", "D", "eb")],
     MOD("B") + NOMOD("C"), "C5, point 4"),
    ("C5: a later receipt by D of a rival, with its first in its past, counts for nothing: the rival seated by E (who "
     "receipted nothing) over a containing set changed by E alone does not unseat C, the close (A, B, D) holding",
     [G5, LM] + H5 + [EC] + CLOSE + [ST.withdraw("we", "E", "be", ("be",)), ballot("be2", "E", "E", ("we",)),
                                      elect("ee", "E", IDS5 + ("we", "be2")), ack("j4", "D", "ee", ("k4",))],
     MOD("C") + NOMOD("E"), "C5"),
    ("C5, (2): a close that still holds a majority of the remaining base stands: of seven, C won four to three; A, D, "
     "E and F receipt it; D then changes its ballot for B beside its receipt (two things: out of the base), and B's "
     "rival over a containing set wins four to three: A, E and F are three of the five left, so the close holds, and "
     "B's rival counts for nothing",
     [room(7), LM] + H7C + [EC7C, ack("r1", "A", "ec"), ack("r4", "D", "ec"), ack("r5", "E", "ec"), ack("r6", "F", "ec"),
                            ST.withdraw("wd", "D", "bd", ("bd",)), ballot("bd2", "D", "B", ("wd",)),
                            elect("eb", "B", IDS7C + ("wd", "bd2"))], MOD("C") + NOMOD("B"), "C5, (2)"),
    ("C5, (2): the same rival with no close: it contains C's set and stands",
     [room(7), LM] + H7C + [EC7C, ST.withdraw("wd", "D", "bd", ("bd",)), ballot("bd2", "D", "B", ("wd",)),
                            elect("eb", "B", IDS7C + ("wd", "bd2"))], MOD("B") + NOMOD("C"), "C5, (2)"),
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
    ("atk 1, (2): B's padded seating over its own concurrent duplicate ballots: B said two things in its own set, so "
     "it is no ballot there, and the padding concludes nothing; C",
     [G5, LM] + H5 + PADB + [EC, elect("eb", "B", ("ba", "bb") + tuple(b["id"] for b in PADB))], MOD("C") + NOMOD("B"), "C4, atk 1"),
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
CE = [G5, LM, leave("le", "E", "g", ("g",)), RC, ballot("ba", "A", "B", ("lm", "rc")),
      ballot("bc", "C", "C", ("lm", "rc")), ballot("bd", "D", "C", ("lm", "rc")), ballot("be", "E", "B", ("lm",))]
CASES += [
    ("C1, concurrent ends: a seating holding lm and the recall (E's leaving in its past) reads E no voice: C wins two "
     "to one", CE + [elect("ec", "C", ("ba", "bc", "bd", "be"), vac=("lm", "rc"), cites=("le",))], MOD("C"), "C1, point 1"),
    ("C1, concurrent ends: X, admitted in the recall's past only, is no member at lm, so the members at both ends "
     "leave it out: its ballot and A's for it are void, C wins",
     [G5, LM, admit("ax", "X", tuple("ABCDE"), ("g",)),
      ST.unseat("rc", "B", "A", "moderate", OBJ, "group", ("ax",), head=("ax",), policy="moderator_recall",
                cosigners=("C", "D", "E")),
      ballot("bx", "X", "X", ("rc",)), ballot("ba", "A", "X", ("lm", "rc")), ballot("bc", "C", "C", ("lm", "rc")),
      ballot("bd", "D", "C", ("lm", "rc")),
      elect("ec", "C", ("bx", "ba", "bc", "bd"), vac=("lm", "rc"))], MOD("C"), "C1, point 1"),
    ("C1, concurrent ends: a seating holding lm alone reads E a voice: two to two, nobody (the two reads differ)",
     [G5, LM, ballot("ba", "A", "B"), ballot("bc", "C", "C"), ballot("bd", "D", "C"),
      ballot("be", "E", "B"), elect("ec", "C", ("ba", "bc", "bd", "be"))], NOMOD("C", "B"), "C1, point 1"),
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
     LOCK + [ballot("bx", "X", "Y", ("wb", "lb"), of="eb"), ballot("by", "Y", "Y", ("wb", "lb"), of="eb"),
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
    ("(2) on the E2 rows: D's two receipts, and B's seating beside its receipt of C's, are each two things: both out "
     "of the base, A alone of A and E, not closed", EQV, "ec", F),
    ("the way back: the room removes D by count, its two receipts as evidence, and E receipts C's seating: A and E "
     "of A and E close it",
     EQV + [RMD, ack("k5", "E", "ec", ("rd",))], "ec", T),
    ("the removal alone: A alone of A and E, not closed",
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
    ("F2, (3) (b2 re-checked): the voters named lm2; C's seating names lm1, which no counted ballot names, so lm1 is "
     "part of no set: C's seating reads no vacancy and concludes nothing, and F's stands",
     [G5, LM1, AF, LM2] + HB2 + [elect("ef", "F", IDB2, vac=("lm2",)), elect("ec", "C", IDB2, vac=("lm1",))],
     MOD("F") + NOMOD("C"), "F2, (3)"),
    ("F2 (b2): F's seating alone (the end at lm2): F", [G5, AF, LM2] + HB2 + [elect("ef", "F", IDB2, vac=("lm2",))],
     MOD("F"), "F2"),
    ("F2, (3): a seating naming both ends, lm1 named by no ballot, has the same set as F's: F's count, so C's "
     "concludes nothing: F",
     [G5, LM1, AF, LM2] + HB2 + [elect("ef", "F", IDB2, vac=("lm2",)), elect("eu", "C", IDB2, vac=("lm1", "lm2"))],
     MOD("F") + NOMOD("C"), "F2, (3)"),
    ("F2, (3): honest concurrent ends: D and E saw lm1 and name it beside lm2; the union seating names both and reads "
     "the members at both, F no member at lm1: the ballots for F are void, C",
     [G5, LM1, AF, LM2] + [ballot("ba", "A", "F", ("lm2",)), ballot("bb", "B", "F", ("lm2",)), ballot("bc", "C", "F", ("lm2",)),
                           ballot("bd", "D", "C", ("lm1", "lm2")), ballot("be", "E", "C", ("lm1", "lm2"))]
     + [elect("ef", "F", IDB2, vac=("lm2",)), elect("eu", "C", IDB2, vac=("lm1", "lm2"))], MOD("C") + NOMOD("F"), "F2, (3)"),
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
# F3: two concurrent seatings of election 1 over sets not nested, each laid down on its own line, each line opening
# a next election: neither stands where both are held, so both next elections fall: nobody until a seating over the
# union. (Under the candidate rule E3 replaced, no next election opened on an unclosed seating at all, and a room
# whose first electorate had all left was locked; that rule is gone, kept only as the planted break `wait_close`.)
S2N = elect("eb", "B", ("ba", "bb"))
SCN = elect("ec", "C", ("bc", "bd", "be"))
COSTN = [G5, LM] + H5 + [SCN, S2N, ST.withdraw("wc", "C", "ec", ("ec",)), ST.withdraw("wb", "B", "eb", ("eb",)),
                         ballot("pa", "A", "D", ("wc",), of="ec"), ballot("pd", "D", "D", ("wc",), of="ec"),
                         elect("n1", "D", ("pa", "pd"), of="ec", vac=("wc",)),
                         ballot("qb", "B", "E", ("wb",), of="eb"), ballot("qe", "E", "E", ("wb",), of="eb"),
                         elect("n2", "E", ("qb", "qe"), of="eb", vac=("wb",))]
CASES += [
    ("F3: two concurrent seatings of election 1 not nested, each line opening a next election: where both are held "
     "neither id stands, and both next elections fall: nobody", COSTN, NOMOD("B", "C", "D", "E"), "F3, the cost"),
    ("F3: either line alone seats its next election's winner", [G5, LM] + H5 + [SCN, ST.withdraw("wc", "C", "ec", ("ec",)),
     ballot("pa", "A", "D", ("wc",), of="ec"), ballot("pd", "D", "D", ("wc",), of="ec"),
     elect("n1", "D", ("pa", "pd"), of="ec", vac=("wc",))], MOD("D"), "F3, the cost"),
]
# N2 (the fourth read, f1): a named leaving strikes a key only in the election's window, not in the past of the
# vacancy end the seating reads (which already settled every leaving and re-admission before it)
XE = ST.unseat("xe", "A", "E", "member", OBJ, "group", ("g",), head=("g",), policy="community_remove", cosigners=("B", "C", "D"))
AE = admit("ae", "E", ("A", "B", "C", "D"), ("xe",))
LMN = ST.withdraw("lm", "A", "g", ("ae",), scope="moderate")
HN = [ballot("ba", "A", "E"), ballot("bb", "B", "E"), ballot("bc", "C", "C"), ballot("bd", "D", "C"), ballot("be", "E", "E")]
IDN = tuple(b["id"] for b in HN)
LEN = leave("le", "E", "g", ("g",))
AE2 = admit("ae", "E", ("A", "B", "C", "D"), ("le",))
CASES += [
    ("N2 (F1a): E removed and re-admitted before the vacancy; E wins three to two", [G5, XE, AE, LMN] + HN + [elect("ee", "E", IDN)],
     MOD("E") + NOMOD("C"), "N2"),
    ("N2 (F1b): C's seating names E's old, undone removal: it is before the vacancy and strikes nobody, so the count "
     "is E's and C's seating concludes nothing: E",
     [G5, XE, AE, LMN] + HN + [elect("ee", "E", IDN), elect("ec", "C", IDN + ("xe",))], MOD("E") + NOMOD("C"), "N2"),
    ("N2 (F1c): the same with E's own old leaving and its re-admission: E",
     [G5, LEN, AE2, LMN] + HN + [elect("ee", "E", IDN), elect("ec", "C", IDN + ("le",))], MOD("E") + NOMOD("C"), "N2"),
    ("N2, control: a leaving after the vacancy still strikes: E leaves after lm; C's seating naming that leaving reads "
     "E no voice and no candidate (B's ballot for E void), and C wins; with E counted it is two to two, nobody",
     [G5, LM] + [ballot("ba", "A", "C"), ballot("bb", "B", "E"), ballot("bc", "C", "C"), ballot("be", "E", "E"),
                 leave("le", "E", "g", ("lm",)), elect("ec", "C", ("ba", "bb", "bc", "be", "le"))], MOD("C"), "N2"),
]
# The rulings on N1, N3 and N4 (the fourth read). (1) A self-fork: two rows by one key over ONE election, neither in
# the other's past, are that key saying two things; rows in two rooms are never a fork. (2) Scoped to the election's
# own rows only (ballot, ballot withdrawal, decline, receipt, a lay-down read as its vacancy, seating): for a reader
# holding both rows the key is no voice (and no candidate, as a leaver) and out of that election's close base, the
# honest receipters keeping theirs. It is NOT a general roster rule: outside an election a fork is evidence and the
# reader's line, with no automatic effect (the guard case below). (3) A vacancy end is in a set only where a counted
# ballot of the set names it.
F3E1 = [ballot("ba", "A", "B"), ballot("bb", "B", "B"), ballot("bc", "C", "B"), elect("e1", "B", ("ba", "bb", "bc"))]
F3E2 = [ballot("a2", "A", "C", ("wb",), of="e1"), ballot("c2", "C", "C", ("wb",), of="e1"), ballot("d2", "D", "C", ("wb",), of="e1"),
        elect("e2", "C", ("a2", "c2", "d2"), of="e1", vac=("wb",)),
        ack("q1", "A", "e2", ("a2",)), ack("q2", "B", "e2"), ack("q3", "D", "e2", ("d2",))]
F3E3 = [ST.withdraw("wc", "C", "e2", ("q1", "q2", "q3")), ballot("a3", "A", "D", ("wc",), of="e2"),
        ballot("d3", "D", "D", ("wc",), of="e2"), elect("e3", "D", ("a3", "d3"), of="e2", vac=("wc",))]
CHAIN2 = [G5, LM] + F3E1 + [ack("p1", "A", "e1"), ack("p3", "C", "e1"), ack("p4", "D", "e1"),
                            ST.withdraw("wb", "B", "e1", ("p1", "p3", "p4"))] + F3E2 + F3E3
RIV = [ballot("bd0", "D", "D"), ballot("be0", "E", "D"), elect("r1", "D", ("bd0", "be0")), ack("p4x", "D", "r1")]
G6 = room(6)
CHAIN6 = [G6, LM] + F3E1 + [ack("p1", "A", "e1"), ack("p3", "C", "e1"), ack("p4", "D", "e1"),
                            ST.withdraw("wb", "B", "e1", ("p1", "p3", "p4"))] + F3E2 + F3E3
CHAIN = [G5, LM] + F3E1 + [ST.withdraw("wb", "B", "e1", ("e1",))] + F3E2 + F3E3
# N1: seven members, A resigns at the newest row (lm2) and seven vote, D five to two; A then backdates a second end
# from the founding row (lm1)
GN1 = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("A",)}, cosigners=("B", "C"))
N1R = [GN1]
_prev, _mem = "g", ["A", "B", "C"]
for _k in "DEFG":
    N1R.append(admit("a" + _k, _k, tuple(_mem), (_prev,))); _mem.append(_k); _prev = "a" + _k
N1L2 = ST.withdraw("lm2", "A", "g", ("aG",), scope="moderate")
N1H = [ballot("b" + k.lower(), k, r, ("lm2",)) for k, r in zip("ABCDEFG", "BBDDDDD")]
N1I = tuple(b["id"] for b in N1H)
N1L1 = ST.withdraw("lm1", "A", "g", ("g",), scope="moderate")
# a founding row with two duty seats: A moderates, B reviews; both lay down at the newest row, and B backdates
GN2 = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("A",), "review": ("B",)}, cosigners=("B", "C"))
N2R = [GN2]
_prev, _mem = "g", ["A", "B", "C"]
for _k in "DE":
    N2R.append(admit("a" + _k, _k, tuple(_mem), (_prev,))); _mem.append(_k); _prev = "a" + _k
N2LA = ST.withdraw("la", "A", "g", ("aE",), scope="moderate")
N2LB = ST.withdraw("lb", "B", "g", ("la",), scope="review")
N2H = [ballot("b" + k.lower(), k, r, ("la", "lb")) for k, r in zip("ABCDE", "BBDDD")]
CASES += [
    ("N3 (F3a): the chain e1 (B, unclosed), e2 (C, closed), e3 (D): D", CHAIN, MOD("D") + NOMOD("B", "C"), "N3"),
    ("N3 (F3c): e1 closed by A, C and D, then the chain: D", CHAIN2, MOD("D"), "N3"),
    ("N3 (F3d): D, a needed receipter of e1, later receipts a rival seating it made with E's ballot: D said two things "
     "in election 1, so it is no voice and out of e1's base; A and C are two of the three left, the close holds, and "
     "the chain stands: D", CHAIN2 + RIV, MOD("D"), "N3"),
    ("N3, the edge: the same in a room of six, e1 closed three of five (A, C, D); D's fork leaves two of four, the close "
     "fails, e1 and D's rival are not nested, so neither stands, and every election named on e1 falls (F3): nobody",
     CHAIN6 + RIV, NOMOD("A", "B", "C", "D", "E", "F"), "N3, the edge"),
    ("N4 (F3e): B, the resigned winner, forks from lm (no e1 in its past): its new ballot beside its seating and its "
     "first ballot is two things, so B is no ballot and no candidate in its own superset seating, which concludes "
     "nothing; the closed successor stands: D", CHAIN + [ballot("bb2", "B", "B"), elect("e1x", "B", ("ba", "bb", "bc", "bb2"))],
     MOD("D") + NOMOD("B"), "N4"),
    ("N1, (3): A backdates a second end (lm1); B's seating names both ends, but no counted ballot names lm1, so lm1 is "
     "out of its set: its count is at lm2, D's, and it concludes nothing; D stands",
     N1R + [N1L2] + N1H + [elect("ed", "D", N1I, vac=("lm2",)), N1L1, elect("eb", "B", N1I, vac=("lm2", "lm1"))],
     MOD("D") + NOMOD("B"), "N1, (3)"),
    ("N1, (1): B forks a ballot naming lm1 beside its first: B said two things, no voice; B's seating over the union "
     "reads the members at both ends (A, B, C), B out: one ballot (A's for B), under the floor: nothing; D stands",
     N1R + [N1L2] + N1H + [elect("ed", "D", N1I, vac=("lm2",)), N1L1, ballot("bb2", "B", "B", ("lm1",)),
                           elect("eb", "B", N1I + ("bb2",), vac=("lm2", "lm1"))], MOD("D") + NOMOD("B"), "N1, (1)"),
    ("N1, several duty seats: A moderates and B reviews; both lay down, five vote naming both ends, D; B backdates a "
     "second end of its seat; a seating naming it beside the honest ends, no ballot naming it, is the honest set: D",
     N2R + [N2LA, N2LB] + N2H + [elect("ed", "D", tuple(b["id"] for b in N2H), vac=("la", "lb")),
                                 ST.withdraw("lb2", "B", "g", ("g",), scope="review"),
                                 elect("eb", "B", tuple(b["id"] for b in N2H), vac=("la", "lb", "lb2"))],
     MOD("D") + NOMOD("B"), "N1"),
    ("(2), the guard: D forks two ballots in the election; outside it, D's cosignature on an admission is a voice as "
     "ever (a fork is no general roster rule): X, admitted by A, B, C and D (four of five), is a member",
     [G5, LM, ballot("bd", "D", "C"), ballot("bd2", "D", "B"), admit("ax", "X", ("A", "B", "C", "D"), ("lm",))],
     [("X", "member", T), ("D", "member", T)], "(2), the guard"),
]
# (5) the room of four: winners A (S1, signed by A) and B (S2, signed by B), voters C and D; B and C receipt S1, A and
# D receipt S2. A seating is its signer's say (i): a winner that receipts the rival has said two things. Without (i)
# nobody forks (each winner is outside its own seating's base) and both close two of three. With (i), over the ONE base
# the election has for a reader (the intersection of the members at every end any of its seatings names, less the departed
# whose leaving does not hold their receipt and the forkers, over the rows held: n keys), no
# two seatings of one election both close: a key receipting both forks, and a winner receipting the rival forks, so
# the two receipter sets are disjoint and hold neither winner; each must be more than half of that base less its own
# winner (n - 1), and two such sets do not fit in the n - 2 keys left. (ii) is the rule backstop: where two groups
# meet their close over the rows held anyway, neither is closed
G4F = room(4)
R4 = [G4F, LM, ballot("bx", "C", "A"), ballot("bw2", "B", "A"), elect("s1", "A", ("bx", "bw2")),
      ballot("by", "D", "B"), ballot("bw1", "A", "B"), elect("s2", "B", ("by", "bw1"))]
R4A = [ack("r1", "B", "s1", ("bw2",)), ack("r2", "C", "s1", ("bx",))]
R4B = [ack("r3", "A", "s2", ("bw1",)), ack("r4", "D", "s2", ("by",))]
CASES += [
    ("(5), the room of four, a reader of side 1 only: S1 closed by B and C: A", R4[:5] + R4A, MOD("A") + NOMOD("B"), "(5)"),
    ("(5), the room of four, a reader of side 2 only: S2 closed by A and D: B", R4[:2] + R4[5:] + R4B, MOD("B") + NOMOD("A"), "(5)"),
    ("(5), the room of four, both held: each winner signed its seating and receipted the rival (two things, (i)), so "
     "each close falls to one of two; the sets are not nested: nobody. (ii), the guard: no two seatings of one "
     "election both close over the rows held (the receipters are disjoint and both winners are out)",
     R4 + R4A + R4B, NOMOD("A", "B"), "(5), (i), (ii)"),
    ("(5), b3 a reader of side 2 only: C", [G5, LM] + BE, MOD("C") + NOMOD("B"), "(5)"),
    ("(4): two devices of one voice: E's ballots through two verified room keys (`dev`, the models' verified signing "
     "key), concurrent, the same ranking, are two keys' rows, no fork; one say per voice: C three to two",
     [G5, LM] + H5[:4] + [dict(ballot("be1", "E", "C"), dev="e1"), dict(ballot("be2", "E", "C"), dev="e2"),
                          elect("ec", "C", IDS5[:4] + ("be1", "be2"))], MOD("C"), "(4)"),
    ("(4): a label the row body states is no key: E, signing through one verified key, states two device labels on "
     "two concurrent ballots of one ranking: one key said two things, a fork; with both in the set E is no ballot, and "
     "A, B against C, D tie: nobody", [G5, LM] + H5[:4] + [dict(ballot("be1", "E", "C"), dev="e1", device_label="phone"),
                                                          dict(ballot("be2", "E", "C"), dev="e1", device_label="laptop"),
                                           elect("ec", "C", IDS5[:4] + ("be1", "be2"))], NOMOD("C", "B"), "(4)"),
    ("(1): a row the key only cosigns is no part of a fork: D's ballot and its concurrent cosignature on X's admission: "
     "D's voice counts, C", [G5, LM] + H5 + [admit("ax", "X", ("A", "B", "C", "D"), ("lm",)), EC], MOD("C"), "(1)"),
    ("(3), the honest self-fork: E, restored from an old backup, signs a second ballot without its first in its past: "
     "E has said two things and is out of the election: with both in the set E is no ballot, and A, B against C, D "
     "tie: nobody", [G5, LM] + H5 + [ballot("be2", "E", "C"), elect("ec", "C", IDS5 + ("be2",))], NOMOD("B", "C"), "(3)"),
]
# b6: twins over equal sets count alike under F1, so the close's base is read the same from either: (regression)
B6 = [G5, LM1, AF, LM2] + HB2 + [elect("ef", "F", IDB2, vac=("lm2",)), elect("ef2", "F", IDB2, vac=("lm2",)),
                                 ack("ka", "A", "ef"), ack("kb", "B", "ef"), ack("kc", "C", "ef2"), ack("kd", "D", "ef2")]
CLOSE_CASES += [
    ("b6 (regression): twins over one set, receipted two and two: one seat, one base, closed by four of five", B6, "ef", T),
    ("b6: the same asked of the other twin", B6, "ef2", T),
]
# (1): rows in two rooms are never a fork: A receipts C's seating in g and, concurrently, votes in room h's election;
# a minimal close (two of three) holds
G4X = room(4)
H4 = [ballot("ba", "A", "C"), ballot("bb", "B", "C"), ballot("bc", "C", "C"), ballot("bd", "D", "B")]
HR = ST.found("h", "A", ("A",), {})
CLOSE_CASES += [
    ("(1): A's receipt in room g and its concurrent ballot in room h's election are no fork: A and B, two of three, close it",
     [G4X, LM, HR] + H4 + [elect("ec", "C", tuple(b["id"] for b in H4)), ack("k1", "A", "ec"), ack("k2", "B", "ec"),
                           ballot("ha", "A", "A", ("h",), of="h")], "ec", T),
    ("(1): a row the key only cosigns is no part of a fork: A and D receipt C's seating, and D cosigns X's admission "
     "concurrently: two of three close it",
     [G4X, LM] + H4 + [elect("ec", "C", tuple(b["id"] for b in H4)), ack("k1", "A", "ec"), ack("k4", "D", "ec"),
                       admit("ax", "X", ("A", "C", "D"), ("lm",))], "ec", T),
    ("C5: a later receipt, with the first in its past, counts for nothing: D's say is B's subset seating's; C's has B "
     "and E of four, not closed",
     [G5, LM] + H5 + [EC, elect("es", "B", ("ba", "bb")), ack("k4", "D", "es", ("bd",)), ack("j4", "D", "ec", ("k4",)),
                      ack("k2", "B", "ec"), ack("k5", "E", "ec")], "ec", F),
]
# The fifth read. G2: one base per election for a reader (departed read over the rows held, not per group), and (ii)
# as a rule. Eight members: B's seating (A, B) and C's (C, D); D, E, F and G receipt C's and then leave, on rows that
# do not hold it; A and H receipt B's naming those leavings. With one base ({A, B, H} less the winner, D to G gone),
# B's group is A and H of A and H... and C's group is none (its receipters have left): B; never two closes
G8 = room(8)
G2R = [G8, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), elect("s1", "B", ("ba", "bb")),
       ballot("bc", "C", "C"), ballot("bd", "D", "C"), elect("s2", "C", ("bc", "bd"))] \
    + [ack("k" + k.lower(), k, "s2", ("bd",)) for k in "DEFG"] + [leave("l" + k.lower(), k, "g", ("lm",)) for k in "DEFG"] \
    + [ack("ka", "A", "s1", tuple("l" + k.lower() for k in "DEFG")), ack("kh", "H", "s1", tuple("l" + k.lower() for k in "DEFG"))]
# G1: B signs a counted recall of A (rc) beside lm, and its ballot; E's second ballot names rc as an end
RCB = ST.unseat("rc", "B", "A", "moderate", OBJ, "group", ("g",), head=("g",), policy="moderator_recall", cosigners=("C", "D"))
HG1 = [ballot("ba", "A", "B"), ballot("bb", "B", "B"), ballot("bc", "C", "B"), ballot("bd", "D", "C"), ballot("be", "E", "C")]
IDG1 = tuple(b["id"] for b in HG1)
CLOSE_CASES += [
    ("G2: one base per election: D to G have left over the rows held, so their receipts of C's seating count for "
     "nothing, and B's closes on A and H", G2R, "s1", T),
    ("G2: and C's does not close (one close at most)", G2R, "s2", F),
]
CASES += [
    ("G2 (200 orders): the room of eight: B", G2R, MOD("B") + NOMOD("C"), "G2"),
    ("G2, a reader of C's side only (C's seating, its receipts and the leavings; no row of B's): C's receipters left "
     "in the rows held, so it does not close; C stands by C4 alone", [G8, LM] + G2R[5:12]
     + [leave("l" + k.lower(), k, "g", ("lm",)) for k in "DEFG"], MOD("C"), "G2"),
    ("G2, a reader holding both seatings, C's receipts and the leavings, but not A's and H's receipts: not nested, "
     "neither closed: nobody", G2R[:12] + [leave("l" + k.lower(), k, "g", ("lm",)) for k in "DEFG"], NOMOD("B", "C"), "G2"),
    ("G2, a reader of B's side only (A's and H's receipts, which hold the leavings): B and C's seatings are not nested, "
     "but B's closed: B", G2R[:8] + [leave("l" + k.lower(), k, "g", ("lm",)) for k in "DEFG"] + G2R[-2:],
     MOD("B") + NOMOD("C"), "G2"),
    ("G1 (G1c): honest, B wins three to two", [G5, LM, RCB] + HG1 + [elect("eb", "B", IDG1)], MOD("B"), "G1"),
    ("G1 (G1d): E names B's recall row as an end: a counted unseat is never its signer's election row, so B is no "
     "fork; the containing seating counts B and is B's count, so C's concludes nothing: B",
     [G5, LM, RCB] + HG1 + [elect("eb", "B", IDG1), ballot("be2", "E", "C", ("lm", "rc", "be")),
                           elect("ecx", "C", IDG1 + ("be2",), vac=("lm", "rc"))], MOD("B") + NOMOD("C"), "G1"),
    ("G1, control: a holder's own two concurrent lay-downs of the seat still fork it: A lays moderate down twice, both "
     "ends named, A no ballot; A's ballot for B void, and B and C tie: nobody",
     [G5, LM, ST.withdraw("lm0", "A", "g", ("g",), scope="moderate")]
     + [ballot("ba", "A", "B", ("lm", "lm0")), ballot("bb", "B", "B", ("lm", "lm0")), ballot("bc", "C", "C", ("lm", "lm0")),
        ballot("bd", "D", "C", ("lm", "lm0")), ballot("be", "E", "B", ("lm", "lm0"))]
     + [elect("ec", "C", ("ba", "bb", "bc", "bd", "be"), vac=("lm", "lm0"))], NOMOD("B", "C"), "G1"),
]
# (ii) is a rule and a backstop: with (i) no two groups of one election meet their close over the rows held, so it is
# shown with (i) taken away (the premise `seating_not_a_say`): the room of four, both held, then closes neither
BACKSTOP = [
    ("(ii), the backstop: the room of four, both held, with a seating no say: each seating meets its close (two of "
     "three); neither is closed, and their sets are not nested: nobody", R4 + R4A + R4B, NOMOD("A", "B"), "(ii)"),
]
# G3 (held: the long-range class): N1 as a race the close stops. A resigns at the newest row (lm2) and all seven rank
# D; A then backdates lm1 from the founding row, and B and C re-ballot naming both ends
G3H = [ballot("b" + k.lower(), k, "D", ("lm2",)) for k in "ABCDEFG"]
G3I = tuple(b["id"] for b in G3H)
G3X = [ballot("xb", "B", "B", ("lm1", "lm2", "bb")), ballot("xc", "C", "B", ("lm1", "lm2", "bc")),
       ST.withdraw("wbb", "B", "bb", ("xb",)), ST.withdraw("wbc", "C", "bc", ("xc",))]
G3B = elect("eb", "B", G3I + ("xb", "xc", "wbb", "wbc"), vac=("lm2", "lm1"))
G3ED = elect("ed", "D", G3I, vac=("lm2",))
G3C = N1R + [N1L2] + G3H + [G3ED] + [ack("k" + k.lower(), k, "ed") for k in "EFG"] + [N1L1] + G3X + [G3B]
CASES += [
    ("G3c, the stated residual (a reader with no acknowledgement): E, F and G receipt D's seating before holding B's; "
     "A's backdated lay-down shrinks the close's base to the founders, the newcomers' receipts fall outside it, and the "
     "honest close fails: nobody (a backdated lay-down can shrink the close's base for a reader with no "
     "acknowledgement, and that reaches an honest close made before the attack)", G3C, NOMOD("D", "B"), "G3, the residual"),
    ("G3d (held): the same receipts made after B's seating: not nested, nobody", N1R + [N1L2] + G3H + [G3ED, N1L1] + G3X
     + [G3B] + [ack("k" + k.lower(), k, "ed", ("eb",)) for k in "EFG"], NOMOD("B", "D"), "G3"),
]
# The sixth read. H1: an honest leaving after the close does not reopen it: a receipt counts, and its signer stays in
# the base, where the key's leaving (or a counted removal of it) has that receipt in its past
G6H = room(6)
H1S2 = [ballot("ba", "A", "B"), ballot("bb", "B", "B"), elect("s2", "B", ("ba", "bb"))]
H1S1 = [ballot("bc", "C", "C"), ballot("bd", "D", "C"), ballot("be", "E", "C"), ballot("bf", "F", "C"),
        elect("s1", "C", ("bc", "bd", "be", "bf"))]
H1CL = [ack("kd", "D", "s1", ("bd",)), ack("ke", "E", "s1", ("be",)), ack("kf", "F", "s1", ("bf",))]
H1B = [G6H, LM] + H1S2 + H1S1 + H1CL
H1NX = [ST.withdraw("wc", "C", "s1", ("kd", "ke", "kf")), ballot("n1", "A", "A", ("wc",), of="s1"),
        ballot("n2", "D", "A", ("wc",), of="s1"), elect("en", "A", ("n1", "n2"), of="s1", vac=("wc",))]
# H2 (base since J1: the INTERSECTION of the members at every end any of its seatings names); nine members, A
# resigns at lm2 and six rank D; A then backdates lm1, and B and C re-ballot naming both ends
GH2 = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("A",)}, cosigners=("B", "C"))
H2R = [GH2]
_prev, _mem = "g", ["A", "B", "C"]
for _k in "DEFGHI":
    H2R.append(admit("a" + _k, _k, tuple(_mem), (_prev,))); _mem.append(_k); _prev = "a" + _k
H2L2 = ST.withdraw("lm2", "A", "g", ("aI",), scope="moderate")
H2H = [ballot("b" + k.lower(), k, "D", ("lm2",)) for k in "DEFGHI"]
H2HON = H2R + [H2L2] + H2H + [elect("s1", "D", tuple(b["id"] for b in H2H), vac=("lm2",))] \
    + [ack("k" + k.lower(), k, "s1", ("b" + k.lower(),)) for k in "EFGHI"]
H2ATK = [ST.withdraw("lm1", "A", "g", ("g",), scope="moderate"), ballot("xb", "B", "B", ("lm1", "lm2")),
         ballot("xc", "C", "B", ("lm1", "lm2")), elect("s2", "B", ("xb", "xc"), vac=("lm1", "lm2")), ack("kc", "C", "s2", ("xc",))]
CASES += [
    ("H1 (H1b): C's seating closed three of five (D, E, F); F leaves after, its leaving holding its receipt: the "
     "receipt counts and F stays in the base: C", H1B + [leave("lf", "F", "g", ("kf",))], MOD("C") + NOMOD("B"), "H1"),
    ("H1 (H1d): the chain (C resigns, A elected next on C's seating), then F leaves: the chain holds: A",
     H1B + H1NX + [leave("lf", "F", "g", ("en",))], MOD("A"), "H1"),
    ("H1: a counted removal of a receipter that holds its receipt leaves the close standing: C",
     H1B + [ST.unseat("xf", "A", "F", "member", OBJ, "group", ("kf",), head=("lm",), policy="community_remove",
                      cosigners=("B", "C", "D", "E"))], MOD("C") + NOMOD("B"), "H1"),
    ("H1, control: a leaving that does not hold the receipt still voids it: F leaves on a row beside its receipt; two "
     "of four, not closed, and the sets are not nested: nobody", H1B + [leave("lf", "F", "g", ("lm",))],
     NOMOD("B", "C"), "H1"),
    ("H2 (H2a): honest, D closed by E to I", H2HON, MOD("D"), "H2"),
    ("H2 (H2b), the stated residual (a reader with no acknowledgement): B's seating over the founders' electorate "
     "(A, B, C at both ends) receipted by C; the close's base is the intersection over the election's ends (A, B, C), "
     "A forked out and B the winner: C alone closes it, and D's five receipters fall outside: B",
     H2HON + H2ATK, MOD("B") + NOMOD("D"), "H2, the residual"),
]
# J1 (the seventh read): A lays moderate down again on the newest admission, F and G ballot at that end. The base is
# the intersection (C1 election-wide), so the newcomers at the second end raise no bar
J1LM2 = ST.withdraw("lm2", "A", "g", ("g",), scope="moderate")
J1ADM, _prev, _mem = [], "g", list("ABCDE")
for _k in "FGHI":
    J1ADM.append(admit("a" + _k, _k, tuple(_mem), (_prev,))); _mem.append(_k); _prev = "a" + _k
J1H = [ballot("b" + k.lower(), k, "C", ("lm2",)) for k in "ABCDE"]
J1S1 = elect("s1", "C", tuple(b["id"] for b in J1H), vac=("lm2",))
J1HON = [G5, J1LM2] + J1ADM + J1H + [J1S1] + [ack("k" + k.lower(), k, "s1", ("b" + k.lower(),)) for k in "BDE"]
J1X = [ballot("xf", "F", "F", ("lm1",)), ballot("xg", "G", "F", ("lm1",)), elect("sx", "F", ("xf", "xg"), vac=("lm1",))]
CASES += [
    ("J1 (J1b): A's second lay-down (lm1) on top of aI, whose chain does not hold lm2: no second end of an ended seat, "
     "but A's two lay-downs, both read as vacancies, are A saying two things; the base, the intersection of the members "
     "at lm2 and lm1 (A to E), less A and the winner C: B, D, E close it three of three: C",
     J1HON + [ST.withdraw("lm1", "A", "g", ("aI",), scope="moderate")] + J1X, MOD("C") + NOMOD("F"), "J1"),
    ("J1, (2): the variant where lm1 has lm2 in its past: an end of a seat with an end of that seat in its own past is "
     "no end; lm1 concludes nothing, F's seating reads no vacancy: C",
     J1HON + [ST.withdraw("lm1", "A", "g", ("aI", "lm2"), scope="moderate")] + J1X, MOD("C") + NOMOD("F"), "J1, (2)"),
]
# (2), read by conclusion: (name, rows, row, concludes). An end of a seat with any end of that seat in its own past
# (a lay-down, a counted unseat, a withdrawal of the offer, whoever signed it) is no end
RC2 = ST.unseat("rc", "B", "A", "moderate", OBJ, "group", ("g",), head=("g",), policy="moderator_recall", cosigners=("C", "D"))
CONCL_CASES = [
    ("J1, (2): lm1, with A's own lay-down of the same seat (lm2) in its past, concludes nothing",
     J1HON + [ST.withdraw("lm1", "A", "g", ("aI", "lm2"), scope="moderate")] + J1X, "lm1", F),
    ("J1: lm1 with no end of the seat in its past concludes",
     J1HON + [ST.withdraw("lm1", "A", "g", ("aI",), scope="moderate")] + J1X, "lm1", T),
    ("(2), any end: A's lay-down with B, C and D's counted recall of A's seat in its past concludes nothing",
     [G5, RC2, ST.withdraw("lm", "A", "g", ("rc",), scope="moderate")], "lm", F),
    ("(2), any end: the counted recall with A's own lay-down of the seat in its past concludes nothing",
     [G5, LM, ST.unseat("rc", "B", "A", "moderate", OBJ, "group", ("lm",), head=("lm",), policy="moderator_recall",
                        cosigners=("C", "D"))], "rc", F),
    ("(2), any end: a second counted recall with the first in its past concludes nothing",
     [G5, RC2, ST.unseat("rc2", "C", "A", "moderate", OBJ, "group", ("rc",), head=("rc",), policy="moderator_recall",
                         cosigners=("B", "D"))], "rc2", F),
    ("(2), the control: the counted recall with no end of the seat in its past concludes", [G5, RC2], "rc", T),
]
# b5: the old-head removal reaching the election (the head rules, H1 to H7), a case; H2b, G3c and G3b, line cases
GB5 = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("C",)}, cosigners=("B", "C"))
B5 = [GB5]
_prev, _mem = "g", ["A", "B", "C"]
for _k in "DEFG":
    B5.append(admit("a" + _k, _k, tuple(_mem), (_prev,))); _mem.append(_k); _prev = "a" + _k
XC5 = ST.unseat("xc", "A", "C", "member", OBJ, "group", ("g", "aG"), head=("g",), policy="community_remove", cosigners=("B",))
# A seating names the newest counted changes over the room as its heads, for its place on a reader's line only (H4,
# the correction to F4): (name, rows, reader, [(key, scope, stands)])
AFX = admit("aF", "F", tuple("ABCDE"), ("lm",))
FORK = [ST.withdraw("wa", "A", "ba", ("ba",)), ballot("ba2", "A", "D", ("wa",)), ST.withdraw("wb", "B", "bb", ("bb",)),
        ballot("bb2", "B", "D", ("wb",)), ST.withdraw("wd", "D", "bd", ("bd",)), ballot("bd2", "D", "D", ("wd",))]
LINE_CASES = [
    ("the line: the room admits F by count while the election is open, a reader acknowledges that admission, and "
     "C's seating written after it (its heads the admission) concludes and is not behind: C",
     [G5, LM, AFX] + H5 + [R("ak", "ack", "R", ("aF",), room=OBJ, head=("aF",)), elect("ec", "C", IDS5, head=("aF",))],
     "R", MOD("C")),
    ("the line: D's late seating forked from the old head (a set containing C's) is behind a reader that acknowledged "
     "C's seating: void for it, and C stands for it",
     [G5, LM] + H5 + [elect("ec", "C", IDS5, head=("g",)), R("ak", "ack", "R", ("ec",), room=OBJ, head=("ec",))] + FORK
     + [elect("ed", "D", IDS5 + ("wa", "ba2", "wb", "bb2", "wd", "bd2"), head=("g",))], "R", MOD("C") + NOMOD("D")),
    ("the line: the same set of rows for a reader with no acknowledgement: D's seating contains C's, D",
     [G5, LM] + H5 + [elect("ec", "C", IDS5, head=("g",)), R("ak", "ack", "R", ("ec",), room=OBJ, head=("ec",))] + FORK
     + [elect("ed", "D", IDS5 + ("wa", "ba2", "wb", "bb2", "wd", "bd2"), head=("g",))], None, MOD("D") + NOMOD("C")),
]
_LATER = [
    ("H2b, for a reader that acknowledged aI: lm1, a lay-down, is a roster change held to the "
     "newest heads (H4) and is behind that reader's line, so it is no vacancy end for it: D",
     H2HON + H2ATK + [R("akR", "ack", "R", ("aI",), room=OBJ, head=("aI",))], MOD("D") + NOMOD("B"), "H2b", "R"),
    ("G3c, for a reader that acknowledged aG: lm1 behind its line: the honest close holds: D",
     G3C + [R("akR", "ack", "R", ("aG",), room=OBJ, head=("aG",))], MOD("D") + NOMOD("B"), "G3c", "R"),
    ("G3b: B and C name A's backdated end in new ballots (electorate A, B, C); lm1, a "
     "resignation, is held to the newest heads (H4) and falls behind a reader's line that acknowledged aG",
     N1R + [N1L2] + G3H + [G3ED, N1L1] + G3X + [G3B, R("akR", "ack", "R", ("aG",), room=OBJ, head=("aG",))],
     MOD("D") + NOMOD("B"), "G3b", "R"),
    ("b5: A and B remove C at the founding head (two of three there) and elect A: the removal "
     "names an old head, so it concludes nothing and C keeps the seat",
     B5 + [XC5, ballot("ba", "A", "A", ("xc",)), ballot("bb", "B", "A", ("xc",)), elect("ea", "A", ("ba", "bb"), vac=("xc",))],
     MOD("C") + NOMOD("A"), "b5"),
]



def at_newest(rows, keep=()):
    """The head rules (H1, H4), merged after these cases were written: each counted row over the room, an election's
    seating included, written at the newest counted changes in its own past and naming them as its heads (the
    founding row where there are none; a seating then names none, unless the case places it there); a withdrawal it named as a head (a lay-down, a
    leaving) is cited in its names, never a head (H1); and a seat's end over the room names those changes too (H4).
    What a signer that holds its own past writes; `keep`: rows a case writes at an old head on purpose."""
    by, anc, out = {}, {}, []
    def up(n):
        return {n} | anc.get(n, set())
    for r in rows:
        past = set().union(*[up(n) for n in r["names"]]) if r["names"] else set()
        def newest_in(obj):
            ch = [by[i] for i in past if i in by and ST.change(by[i], obj, by)]
            return tuple(sorted(q["id"] for q in ch if not any(q["id"] in anc.get(o["id"], ()) for o in ch)))
        if r["id"] not in keep and r["id"] != r.get("obj") and r["kind"] in ("offer", "unseat") and r.get("conf") == "group" \
                and r.get("obj") == OBJ:
            hs = newest_in(OBJ) or (() if ST.is_election(r) and not r.get("head") else (OBJ,))
            r = dict(r, head=hs, names=tuple(dict.fromkeys(tuple(r["names"]) + hs)))
            if not hs: r.pop("head")
        elif r["id"] not in keep and r["kind"] == "withdraw" and by.get(r["target"], {}).get("kind") in ("offer", "accept") \
                and ST.CP.object_of(by[r["target"]], by) == OBJ:
            r = dict(r, names=tuple(dict.fromkeys(tuple(r["names"]) + newest_in(OBJ))))
        by[r["id"]] = r
        anc[r["id"]] = past
        out.append(r)
    return out


CASES = [(n, at_newest(rows), a, i) for n, rows, a, i in CASES]
BACKSTOP = [(n, at_newest(rows), a, i) for n, rows, a, i in BACKSTOP]
CLOSE_CASES = [(n, at_newest(rows), q, w) for n, rows, q, w in CLOSE_CASES]
CONCL_CASES = [(n, at_newest(rows), q, w) for n, rows, q, w in CONCL_CASES]
LINE_CASES = [(n, at_newest(rows), o, a) for n, rows, o, a in LINE_CASES]
# b5 writes A's and B's removal of C at the founding head on purpose: that is the attack
_LATER = [(c[0], at_newest(c[1], keep=("xc",) if c[3] == "b5" else ()), *c[2:]) for c in _LATER]
# b5 is a case; H2b, G3c and G3b are line cases (a lay-down is a roster change under H4, on the reader's line, and one
# behind it is no vacancy end for that reader: seat.reader_ends), each with its reader
CASES += [(c[0], c[1], c[2], c[3]) for c in _LATER if c[3] == "b5"]
LINE_CASES += [(c[0], c[1], c[4], c[2]) for c in _LATER if c[3] in ("H2b", "G3c", "G3b")]
# The line case of a seating forked at the old head, restated (the ruling of 2026-11-27): C's and D's seatings both name
# g, so under the sibling-safe line they are siblings and neither is behind the other for a reader that acknowledged
# C's; C4 decides (D's set contains C's), and D stands for that reader too. Its old expectation (D void for the
# reader) assumed the line before it was sibling-safe; the cases on _SAFE show a seating behind a reader's line
LINE_CASES = [(n.replace("is behind a reader that acknowledged C's seating: void for it, and C stands for it",
                         "and a reader that acknowledged C's seating: siblings at g, neither behind (the sibling-safe "
                         "line); C4 decides, D's set containing C's: D"), rows, own,
               MOD("D") + NOMOD("C") if n.startswith("the line: D's late seating forked from the old head") else asks)
              for n, rows, own, asks in LINE_CASES]
# C1, F1, F2: the electorate and the leavings are read from the seating's named set only: E's leaving, in the past of
# D's ballot and so of C's seating, which does not name it, strikes nobody (members_at's read of every withdrawal in a
# counting row's past is the roster's, not the election's)
_UNL = [G5, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), ballot("bc", "C", "C"), ballot("be", "E", "C"),
        leave("le", "E", "g", ("be",)), ballot("bd", "D", "C", ("lm", "le")), elect("ec", "C", ("ba", "bb", "bc", "bd", "be"))]
CASES += [("F1: a leaving the seating does not name strikes nobody: E left in the past of D's ballot, and C's seating, "
           "naming the ballots and not the leaving, reads E a voice: C three to two", at_newest(_UNL),
           MOD("C") + [("E", "member", F)], "F1")]
# the same line where the reader's acknowledged seating is placed at a later head than the fork's (C's seating at F's
# admission, D's at the founding row): D's seating names a head strictly in the past of C's own heads, so it is
# behind C's for that reader under the sibling-safe line
_AFS = dict(admit("aF", "F", tuple("ABCDE"), ("g",)), names=("g", "lm"))
_SAFE = [G5, LM, _AFS] + H5 + [elect("ec", "C", IDS5, head=("aF",)), R("ak", "ack", "R", ("ec",), room=OBJ, head=("ec",))] \
    + FORK + [elect("ed", "D", IDS5 + ("wa", "ba2", "wb", "bb2", "wd", "bd2"), head=("g",))]
LINE_CASES += [
    ("the line, sibling-safe: C's seating at F's admission, acknowledged by a reader; D's late seating at the founding "
     "row (a set containing C's) is behind it for that reader: void for it, and C stands for it", _SAFE, "R",
     MOD("C") + NOMOD("D")),
    ("the line, sibling-safe: the same rows for a reader with no acknowledgement: D's seating contains C's, D", _SAFE,
     None, MOD("D") + NOMOD("C")),
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


# (retired with the readings the ruling of 2026-11-28 withdrew: vacancy_founding, vacancy_first_end, electorate_folded,
# electorate_reads_past, vacancy_unnamed, base_per_seating_electorate, close_base_union; leaver_voice and
# counted_end_forks_signer have no case left under the opening; electorate_at_seating moved to check_election_close.py)
PLANTS = ("laydown_off_line", "c2_holder_unread",
          "c2_later_unread", "contains_unread", "twin_withdrawal_unread", "close_unread", "receipt_standing_unread",
          "say_any_receipt", "close_leavers_kept", "closed_rivals_count", "election_id_any", "set_any_signer",
          "ballot_nonmember_ranked", "ballot_ranks_unbounded", "seating_any_signer", "twin_ids_apart",
          "fold_ranked_counted", "fork_reopens_close", "fork_base_kept", "fork_across_objects", "superseded_unread", "wait_close", "id_cascade_unread",
          "set_inputs_unread", "void_seating_read", "seating_not_a_say", "fork_per_voice",
          "fork_cosigned", "fork_by_stated_device", "two_closes_both_stand",
          "base_per_group",
          "leaving_after_receipt_voids", "end_of_ended_seat",
          "leaving_before_vacancy_read")


from election_worlds import opened  # noqa: E402,F401  (the legacy worlds' openings)


def answers(rows, asks, plant=None, arrive=False, own=None):
    with planted(plant):
        rows = opened(rows)
        S = CK.arrive(list(rows), RULE) if arrive else CK.concluded(CK.kept(list(rows)), RULE)
        Q = ST.Seats(S, own=own)
        return [Q.stands(k, s, OBJ) for k, s, _ in asks]


def concludes(rows, rid, plant=None, arrive=False):
    with planted(plant):
        rows = opened(rows)
        S = CK.arrive(list(rows), RULE) if arrive else CK.concluded(CK.kept(list(rows)), RULE)
        return bool(S.C.get(rid))


def closed(rows, seating, plant=None, arrive=False):
    with planted(plant):
        rows = opened(rows)
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


# ---- restated by the ruling of 2026-11-28 (the election close: one election per seat end, an opening row, the
# electorate at the opening's heads, departures as the reader's roster takes them) --------------------------------------
# These cases were written for the withdrawn readings: the vacancy read from the ends a seating names (F2), the base
# as the intersection of the members at every end (C1, G3), a second lay-down read as a vacancy (N1, J1), a leaving
# struck only where the set names it (F1). Their worlds are kept; their answers are the ruled ones:
#   two concurrent lay-downs of one seat are a FORK and open nothing (rule 1), so no seating stands where both are
#   taken (F2 (3), N1, H2b for a reader with no acknowledgement: the stated residual, it waits);
#   a lay-down with an end of the seat in its past is no end, so the election is at the first (J1, b6: F, admitted
#   after it, neither votes nor stands);
#   the electorate is the roster at the opening's heads, so a key admitted before a counted end the opening cites
#   votes (C1, X);
#   a seating names its opening and cites its ballots: no end is named, and a leaving the reader's roster takes
#   strikes the leaver whatever the set names (F2, F1).
RESTATED = {
    "C1, concurrent ends: X, admitted in the recall's past": [F],
    "F2, (3) (b2 re-checked)": [F, F], "F2, (3): a seating naming both ends": [F, F],
    "F2, (3): honest concurrent ends": [F, F], "F2: a seating that names no end": [T],
    "N1, (3): A backdates a second end": [F, F], "N1, (1): B forks a ballot naming lm1": [F, F],
    "H2 (H2b), the stated residual": [F, F], "J1 (J1b): A's second lay-down": [F, F],
    "F1: a leaving the seating does not name": [F, F],
}
RESTATED_CLOSE = {"b6 (regression)": F, "b6: the same asked of the other twin": F}
for i, (name, rows, asks, item) in enumerate(CASES):
    for pre, want in RESTATED.items():
        if name.startswith(pre):
            CASES[i] = ("(restated, 2026-11-28) " + name, rows, [(k, sc, w) for (k, sc, _), w in zip(asks, want)], item)
for i, (name, rows, seating, want) in enumerate(CLOSE_CASES):
    for pre, w in RESTATED_CLOSE.items():
        if name.startswith(pre):
            CLOSE_CASES[i] = ("(restated, 2026-11-28: the election is at lm1, the first end) " + name, rows, seating, w)


def main():
    t0 = time.time()
    problems, n_orders = [], 0
    for name, rows, asks, _item in CASES:
        want = [w for _, _, w in asks]
        got = answers(rows, asks)
        if got != want:
            problems.append("%s: got %s, expected %s" % (name, got, want))
        for p in orders(rows, 200 if name.startswith("G2 (200") else 40):
            n_orders += 1
            if answers([rows[0]] + list(p), asks, arrive=True) != got:
                problems.append("%s: order %s differs" % (name, [r["id"] for r in p]))
                break
    for name, rows, asks, _item in BACKSTOP:
        ST.MUT.add("seating_not_a_say")
        try:
            want = [w for _, _, w in asks]
            got = answers(rows, asks)
            if got != want:
                problems.append("%s: got %s, expected %s" % (name, got, want))
            for p in orders(rows, 40):
                n_orders += 1
                if answers([rows[0]] + list(p), asks, arrive=True) != got:
                    problems.append("%s: order %s differs" % (name, [r["id"] for r in p]))
                    break
        finally:
            ST.MUT.discard("seating_not_a_say")
    for name, rows, rid, want in CONCL_CASES:
        got = concludes(rows, rid)
        if got != want:
            problems.append("%s: concludes %s, expected %s" % (name, got, want))
        for p in orders(rows, 40):
            n_orders += 1
            if concludes([rows[0]] + list(p), rid, arrive=True) != got:
                problems.append("%s: order %s differs" % (name, [r["id"] for r in p]))
                break
    for name, rows, own, asks in LINE_CASES:
        want = [w for _, _, w in asks]
        got = answers(rows, asks, own=own)
        if got != want:
            problems.append("%s: got %s, expected %s" % (name, got, want))
        for p in orders(rows, 40):
            n_orders += 1
            if answers([rows[0]] + list(p), asks, arrive=True, own=own) != got:
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
    caught = 0
    for plant in PLANTS:
        hit = [name for name, rows, asks, _ in CASES if answers(rows, asks, plant) != [w for _, _, w in asks]]
        hit += [name for name, rows, sq, want in CLOSE_CASES if closed(rows, sq, plant) != want]
        hit += [name for name, rows, rid, want in CONCL_CASES if concludes(rows, rid, plant) != want]
        hit += [name for name, rows, own, asks in LINE_CASES if answers(rows, asks, plant, own=own) != [w for _, _, w in asks]]
        ST.MUT.add("seating_not_a_say")
        try:
            if plant != "seating_not_a_say":
                hit += [name for name, rows, asks, _ in BACKSTOP if answers(rows, asks, plant) != [w for _, _, w in asks]]
        finally:
            ST.MUT.discard("seating_not_a_say")
        caught += bool(hit)
        print("  plant %-24s %s" % (plant, "caught by %d cases, first: %s" % (len(hit), hit[0][:90]) if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % plant)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases, %d of the close, %d of the line, %d orders, %d of %d planted breaks caught (%.0fs)"
          % ("ok" if not problems else "%d problems" % len(problems), len(CASES), len(CLOSE_CASES), len(LINE_CASES),
             n_orders, caught, len(PLANTS), time.time() - t0))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
