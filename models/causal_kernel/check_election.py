#!/usr/bin/env python3
"""
check_election.py: the moderator election (CC 4.5.13, "The moderator election", "One result on every node", "The
floor in a small room", "Ranked choice is one count"; CC 4.5.4 rule 2), as seat.py's seat rule reads it.

The presentation. A ballot is a row of kind `ballot` signed by a member, its `ranking` the keys it ranks, best first
(`ballot:moderator`, CC 3.1.4). The election's seating is one counted offer (conf `group`, policy
`moderator_election`, the ranked count of the policy table): scope `moderate` over the room, `to` the winner, naming
the ballots it is counted over and the head it is counted at (`ballot:moderator_acceptance`, which "binds the ballot
set it was seated on"). It concludes where the ranked count (reexpress.ranked, with no declared order) over exactly
the ballots it names yields its `to`. The seat is two consents: the winner signs the row, or accepts it. The seat
then stands as any duty seat does, only while its holder is a member (check_duty_seats.py).

When it seats: only where no duty holder is left at the heads the row names (CC 4.5.4 (v), rule 2), a holder whose
own leaving is in the row's past not counted as left.

What is counted (seat.count_met, its ranked arm):
    the ballots the row names, each from a key the count is over (the persons at the head the row names, less a
    key whose own leaving is in the row's past): an agent's ballot, a non-member's and an unnamed one count for
    nothing; a ballot whose signer's withdrawal of it is in the row's past is none; a ballot ranking a key that is not
    counted over (no person at the heads, or a key whose own leaving is in the row's past) is not counted, the whole
    ballot; one ballot per key (two different rankings by one key are none, CC 4.5.13 "a person whose ballots
    disagree has none"); the floor is two ballots, or fewer where there are fewer options; a tie for weakest seats
    nobody (an election declares no order).

OPEN lists rows the text does not decide, with the model's answer now and the candidate answers.

Every case is a hand-written answer, read in every arrival order of its rows above the founding one (a fixed sample
of 300 where there are more than six). Each names the ledger row it closes, CIRISConstitution#241: <item> (LEDGER and the
case's item).

Planted breaks, each of which must change a case's answer:
    ballot_any_signer   a ballot counts whoever signed it (an agent's, a non-member's)
    ballot_unnamed      a ballot in the row's past counts though the row does not name it
    election_declared   the election's count breaks a tie for weakest by the order of the row's options
    election_any_winner the row concludes where the count yields any winner, not the key it seats
    ballot_withdrawal_unread  a ballot its signer withdrew in the row's past still counts
    ballot_nonmember_ranked   a ballot ranking a key with no roster seat at the heads counts, the key skipped
    election_beside_holder    the election seats while a duty holder is live at the heads the row names
    election_agent_holder     an AI agent's key holding a duty is read as a holder, and the room does not elect
    candidates_roster         the candidates are the member seats at the heads, a leaver among them
    ballot_ranks_unbounded    a ballot ranking more than three counts
    recall_at_least           the recall read as at least two thirds (the table's cell), not more than
    decline_unread            a decline the seating names is not read: the count yields its winner
    larger_set_unread         every concluded seating stands, whatever the sets of its election's others
    election_id_unread        every ranked seating over the room is of one election
    candidates_options        the candidates are the options the seating lists, not the roster at its head
    floor_unread              the recall's floor of two voices is not read
    runoff_forward            the runoff order read in the order of elimination, not its reverse (reexpress.py)
    zero_strike_off           options holding no ballot are not struck together (reexpress.py)
    recall_holder_in_base     the recall counted over the members with the holder it recalls
    recall_holder_voice       the holder a recall judges is a voice of it
    recall_as_strictfloor     the recall read as the plain StrictFloor count, its holder in the base and a voice

    python3 -I check_election.py      exit 1 on any difference
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
import reexpress as RX  # noqa: E402   (on the path seat.py sets)

CK = ST.CK
T, F = True, False
OBJ = "g"
RULE = lambda r, P, past: ST.seat_rule(r, P, past)
LEDGER = "CIRISConstitution#241: "

# rooms whose founding record names A the one holder of moderate, and A lays it down (LM): no duty holder is left
# (CC 4.5.4 (v): "With no duty holder left the room locks, and the members' count seats one"). A founding with members
# only is refused at the door by the text, so no case is built on one.
G1 = ST.found("g", "A", ("A",), {"moderate": ("A",)})
G3 = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("A",)}, cosigners=("B", "C"))
G4 = ST.found("g", "A", ("A", "B", "C", "D"), {"moderate": ("A",)}, cosigners=("B", "C", "D"))
G5 = ST.found("g", "A", ("A", "B", "C", "D", "E"), {"moderate": ("A",)}, cosigners=("B", "C", "D", "E"))
G10 = ST.found("g", "A", tuple("ABCDEFGHIJ"), {"moderate": ("A",)}, cosigners=tuple("BCDEFGHIJ"))
G8 = ST.found("g", "A", tuple("ABCDEFGH"), {"moderate": ("A",)}, cosigners=tuple("BCDEFGH"))
LM = ST.withdraw("lm", "A", "g", ("g",), scope="moderate")      # the one named holder lays moderate down: no holder left

# the eight ballots of the decline cases: A four first choices, C three, B one (B's next choice A)
B8 = ("ba", "bd", "be", "bf", "bb", "bc", "bg", "bh")
DA = CK.row("da", "decline", "A", ("lm",))                      # A's decline (`ballot:moderator_decline`)

# rooms whose founding record seats duty holders: A alone holds moderate (FH), A and B do (FH2)
FH = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("A",)}, cosigners=("B", "C"))
FH2 = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("A", "B")}, cosigners=("B", "C"))

FH4 = ST.found("g", "A", ("A", "B", "C", "D"), {"moderate": ("A",)}, cosigners=("B", "C", "D"))
FH1 = ST.found("g", "A", ("A",), {"moderate": ("A",)})
ROOM = lambda n: ST.found("g", "A", tuple("ABCDEFG"[:n]), {"moderate": ("A",)}, cosigners=tuple("BCDEFG"[:n - 1]))
# a plain count with the recall's threshold, for the one case that shows the recall's base (a policy name of these cases)
PLAIN_FLOOR = "strict_two_thirds_floor_two"
ST.POLICY.setdefault(PLAIN_FLOOR, ("strictfloor", 2, 3, 2))
FH2M = ST.found("g", "A", ("A", "B"), {"moderate": ("A",)}, cosigners=("B",))


def recall(i, k, signers, heads):
    """The members' recall of `k`'s moderate seat (`moderator_recall`), counted over the members at `heads`."""
    return ST.unseat(i, signers[0], k, "moderate", OBJ, "group", tuple(heads), head=tuple(heads), policy="moderator_recall",
                     cosigners=tuple(signers[1:]))


def ballot(i, k, ranking, names=("lm",)):
    """A member's ballot (`ballot:moderator`): its ranking, best first."""
    return CK.row(i, "ballot", k, tuple(names), ranking=tuple(ranking))


def _elect8():
    return [G8, LM, ballot("ba", "A", "AB"), ballot("bd", "D", "AB"), ballot("be", "E", "AB"), ballot("bf", "F", "AB"),
            ballot("bb", "B", "BA"), ballot("bc", "C", "C"), ballot("bg", "G", "C"), ballot("bh", "H", "C")]


def elect(i, k, ballots, members, signer=None, heads=("lm",), cites=()):
    """The seating of `k` by the election, counted over the ballots it names at `heads`; `members` its options."""
    return ST.offer(i, signer or k, k, "moderate", OBJ, "group", tuple(ballots) + tuple(heads) + tuple(cites),
                    head=tuple(heads), policy="moderator_election", options=tuple(members))


def admit(i, k, signers, heads, scope="member"):
    """A widening under the room's protocol, the joiner cosigning."""
    return ST.offer(i, signers[0], k, scope, OBJ, "group", tuple(heads), head=tuple(heads), policy="community_invite",
                    cosigners=tuple(signers[1:]) + ((k,) if k not in signers else ()))


ELECT8 = _elect8()
# A wins at once and declines; B to E hold no ballot (DEC5)
DEC5 = [G5, LM, ballot("ba", "A", "A"), ballot("bb", "B", "A"), ballot("bc", "C", "A"), CK.row("da", "decline", "A", ("lm",))]
# two seatings of one election over equal sets (EQ4), and over a smaller and a larger (LG5)
EQ4 = [ballot("ba", "A", "B"), ballot("bb", "B", "B"), ballot("bc", "C", "C"), ballot("bd", "D", "C"),
       elect("eb", "B", ("ba", "bb"), ("A", "B", "C", "D")), elect("ec", "C", ("bc", "bd"), ("A", "B", "C", "D"))]
LG5 = [ballot("ba", "A", "B"), ballot("bb", "B", "B"), ballot("bc", "C", "C"), ballot("bd", "D", "C"),
       ballot("be", "E", "C"), elect("eb", "B", ("ba", "bb"), ("A", "B", "C", "D", "E")),
       elect("ec", "C", ("ba", "bb", "bc", "bd", "be"), ("A", "B", "C", "D", "E"))]
M3, M4, M5 = ("A", "B", "C"), ("A", "B", "C", "D"), ("A", "B", "C", "D", "E")
M10 = tuple("ABCDEFGHIJ")
MOD = lambda *ks: [(k, "moderate", T) for k in ks]
NOMOD = lambda *ks: [(k, "moderate", F) for k in ks]

# (name, rows, [(key, scope, stands)], ledger item)
CASES = [
    # ---- the count -------------------------------------------------------------------------------------------------
    ("two of three rank B first: B is seated",
     [G3, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), elect("el", "B", ("ba", "bb"), M3)],
     MOD("B") + NOMOD("A", "C") + [("B", "member", T)], "the count"),
    ("the same ballots seating A: the count yields B, so the row concludes nothing",
     [G3, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), elect("el", "A", ("ba", "bb"), M3)],
     NOMOD("A", "B", "C"), "the count"),
    ("a weakest option eliminated passes its ballot on: of five, over the options A, B and C, A's ballot moves to C, who has a majority",
     [G5, LM, ballot("ba", "A", "AC"), ballot("bb", "B", "B"), ballot("bc", "C", "C"), ballot("bd", "D", "C"),
      ballot("be", "E", "B"), elect("el", "C", ("ba", "bb", "bc", "bd", "be"), M3)],
     MOD("C") + NOMOD("A", "B"), "the count"),
    ("the same ballots seating B, the strongest first choice tied with C: nothing",
     [G5, LM, ballot("ba", "A", "AC"), ballot("bb", "B", "B"), ballot("bc", "C", "C"), ballot("bd", "D", "C"),
      ballot("be", "E", "B"), elect("el", "B", ("ba", "bb", "bc", "bd", "be"), M3)],
     NOMOD("A", "B", "C"), "the count"),
    ("every member a candidate: of five, D and E, whom no ballot names, go out together (#241 E1, derived: options "
     "holding no ballot are eliminated together), then A, and C has a majority",
     [G5, LM, ballot("ba", "A", "AC"), ballot("bb", "B", "B"), ballot("bc", "C", "C"), ballot("bd", "D", "C"),
      ballot("be", "E", "B"), elect("el", "C", ("ba", "bb", "bc", "bd", "be"), M5)],
     MOD("C") + NOMOD("A", "B"), "who may stand"),
    ("the candidates are the roster at the head, whatever options the seating lists: the same ballots, the seating "
     "listing A and B only, still seat C",
     [G5, LM, ballot("ba", "A", "AC"), ballot("bb", "B", "B"), ballot("bc", "C", "C"), ballot("bd", "D", "C"),
      ballot("be", "E", "B"), elect("el", "C", ("ba", "bb", "bc", "bd", "be"), ("A", "B"))],
     MOD("C"), "who may stand"),
    ("a room of ten, first choices 4, 3 and 3 among three members: the seven others go together, then the two at 3 "
     "tie for weakest, and the count seats nobody",
     [G10, LM, LM] + [ballot("b" + k, k, r) for k, r in zip("ABCDEFGHIJ", ["A"] * 4 + ["B"] * 3 + ["CA"] * 3)]
     + [elect("el", "A", tuple("b" + k for k in "ABCDEFGHIJ"), M10)],
     NOMOD("A", "B", "C"), "ties"),
    ("first choices 5, 3 and 2: the seven go together, then the 2, whose ballots pass to A, who is seated",
     [G10, LM, LM] + [ballot("b" + k, k, r) for k, r in zip("ABCDEFGHIJ", ["A"] * 5 + ["B"] * 3 + ["CA"] * 2)]
     + [elect("el", "A", tuple("b" + k for k in "ABCDEFGHIJ"), M10)],
     MOD("A") + NOMOD("B", "C"), "ties"),
    # ---- ties --------------------------------------------------------------------------------------------------------
    ("three ballots, three first choices: a tie for weakest seats nobody (an election declares no order)",
     [G3, LM, ballot("ba", "A", "AB"), ballot("bb", "B", "B"), ballot("bc", "C", "C"),
      elect("el", "A", ("ba", "bb", "bc"), M3)],
     NOMOD("A", "B", "C"), "ties"),
    ("the same ballots seating C, the last option listed: nothing (no order of the options decides)",
     [G3, LM, ballot("ba", "A", "AB"), ballot("bb", "B", "B"), ballot("bc", "C", "C"),
      elect("el", "C", ("ba", "bb", "bc"), M3)],
     NOMOD("A", "B", "C"), "ties"),
    ("two against two: a tie seats nobody",
     [G4, LM, ballot("ba", "A", "A"), ballot("bb", "B", "A"), ballot("bc", "C", "C"), ballot("bd", "D", "C"),
      elect("el", "A", ("ba", "bb", "bc", "bd"), M4)],
     NOMOD("A", "C"), "ties"),
    ("the count runs again over the ballots then held: a fifth ballot naming the four breaks the tie",
     [G5, LM, ballot("ba", "A", "A"), ballot("bb", "B", "A"), ballot("bc", "C", "C"), ballot("bd", "D", "C"),
      ballot("be", "E", "C"), elect("el", "C", ("ba", "bb", "bc", "bd", "be"), M5)],
     MOD("C") + NOMOD("A"), "ties"),
    # ---- the floor ---------------------------------------------------------------------------------------------------
    ("one ballot in a room of three is under the floor of two: nobody",
     [G3, LM, ballot("ba", "A", "B"), elect("el", "B", ("ba",), M3)], NOMOD("A", "B"), "the floor"),
    ("a room of one elects itself by its own ballot (the floor is the roster's size)",
     [G1, LM, ballot("ba", "A", "A"), elect("el", "A", ("ba",), ("A",))], MOD("A"), "the floor"),
    ("a seating that names no ballot seats nobody, in a room of one too",
     [G1, LM, elect("el", "A", (), ("A",))], NOMOD("A"), "the floor"),
    # ---- whose ballot ------------------------------------------------------------------------------------------------
    ("a ballot from a key the room does not seat counts for nothing: one member's ballot is under the floor",
     [G3, LM, ballot("ba", "A", "B"), ballot("bx", "X", "B"), elect("el", "B", ("ba", "bx"), M3)],
     NOMOD("A", "B"), "the base"),
    ("an agent's ballot is no voice (an AI agent's key is in no count): one person's ballot is under the floor",
     [G3, LM, admit("ax", "X", ("A", "B"), ("lm",), "agent"), ballot("ba", "A", "B", ("ax",)),
      ballot("bx", "X", "B", ("ax",)), elect("el", "B", ("ba", "bx"), M3, heads=("ax",))],
     NOMOD("A", "B") + [("X", "agent", T)], "the base"),
    ("a ballot the seating does not name is not counted: the seating names B's ballot only, which names A's",
     [G3, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B", ("ba",)), elect("el", "B", ("bb",), M3)],
     NOMOD("B"), "the ballot set"),
    ("a ballot ranking a key the room does not seat is not counted, the whole ballot: one ballot is under the floor",
     [G3, LM, ballot("ba", "A", "XB"), ballot("bb", "B", "B"), elect("el", "B", ("ba", "bb"), M3)],
     NOMOD("A", "B"), "who may stand"),
    ("a ballot ranking an agent's key (which holds `agent`, no member seat) is not counted: one ballot is under the floor",
     [G3, LM, admit("ax", "X", ("A", "B"), ("lm",), "agent"), ballot("ba", "A", "XB", ("ax",)),
      ballot("bb", "B", "B", ("ax",)), elect("el", "B", ("ba", "bb"), M3, heads=("ax",))],
     NOMOD("A", "B") + [("X", "agent", T)], "who may stand"),
    ("a ballot ranking a key admitted after the head the seating names is not counted",
     [G3, LM, ballot("ba", "A", "XB"), ballot("bb", "B", "B"), admit("ax", "X", ("A", "B"), ("lm",)),
      elect("el", "B", ("ba", "bb"), M3, cites=("ax",))],
     NOMOD("A", "B") + [("X", "member", T)], "who may stand"),
    ("and counted at a head after the admission: B has two first choices of three, and is seated",
     [G3, LM, admit("ax", "X", ("A", "B"), ("lm",)), ballot("ba", "A", "XB", ("ax",)), ballot("bb", "B", "B", ("ax",)),
      ballot("bc", "C", "B", ("ax",)), elect("el", "B", ("ba", "bb", "bc"), M3, heads=("ax",))],
     MOD("B"), "who may stand"),
    ("a ballot ranking first a member who left, its leaving in the seating's past, is not counted (#241 O2, derived: "
     "a leaver is out of the base, the voices and the candidates): one ballot is under the floor",
     [G4, LM, ST.withdraw("wc", "C", "g", ("lm",)), ballot("ba", "A", "CB"), ballot("bb", "B", "B"),
      elect("el", "B", ("ba", "bb"), ("B", "D"), cites=("wc",))],
     NOMOD("B") + [("C", "member", F)], "a candidate who leaves"),
    ("the leaver's own ballot is not counted either: B and the leaver C rank B, one ballot is under the floor",
     [G4, LM, ST.withdraw("wc", "C", "g", ("lm",)), ballot("bc", "C", "B"), ballot("bb", "B", "B"),
      elect("el", "B", ("bc", "bb"), ("B", "D"), cites=("wc",))],
     NOMOD("B"), "a candidate who leaves"),
    ("and without the leaving in its past, the seating counts A's ballot: B has two first choices of three, and is "
     "seated (C's leaving beside it)",
     [G4, LM, ST.withdraw("wc", "C", "g", ("lm",)), ballot("ba", "A", "CB"), ballot("bb", "B", "B"), ballot("bd", "D", "B"),
      elect("el", "B", ("ba", "bb", "bd"), ("B", "D"))],
     MOD("B"), "a candidate who leaves"),
    ("a ballot ranking four is void, the whole ballot (CC 4.5.13 'Each person ranks up to three'; #241 O3): one "
     "ballot is under the floor",
     [G5, LM, ballot("ba", "A", "BCDE"), ballot("bb", "B", "B"), elect("el", "B", ("ba", "bb"), M5)],
     NOMOD("B"), "the ballot"),
    ("a ballot ranking three counts: B is seated",
     [G5, LM, ballot("ba", "A", "BCD"), ballot("bb", "B", "B"), elect("el", "B", ("ba", "bb"), M5)],
     MOD("B"), "the ballot"),
    # ---- one ballot a person -----------------------------------------------------------------------------------------
    ("two different ballots by one member are none: B's one ballot is under the floor",
     [G3, LM, ballot("ba", "A", "B"), ballot("ba2", "A", "C"), ballot("bb", "B", "B"),
      elect("el", "B", ("ba", "ba2", "bb"), M3)],
     NOMOD("A", "B", "C"), "the fold"),
    ("two agreeing ballots by one member are one",
     [G3, LM, ballot("ba", "A", "B"), ballot("ba2", "A", "B"), ballot("bb", "B", "B"),
      elect("el", "B", ("ba", "ba2", "bb"), M3)],
     MOD("B"), "the fold"),
    # ---- a withdrawal -------------------------------------------------------------------------------------------------
    ("a ballot its signer withdrew, the withdrawal in the seating's past, is none: one ballot is under the floor",
     [G3, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), ST.withdraw("wa", "A", "ba", ("ba",)),
      elect("el", "B", ("ba", "bb", "wa"), M3)],
     NOMOD("A", "B"), "the fold"),
    ("of two disagreeing ballots, one withdrawn: the other stands, and B is seated",
     [G3, LM, ballot("ba", "A", "C"), ballot("ba2", "A", "B"), ballot("bb", "B", "B"), ST.withdraw("wa", "A", "ba", ("ba",)),
      elect("el", "B", ("ba", "ba2", "bb", "wa"), M3)],
     MOD("B") + NOMOD("A", "C"), "the fold"),
    ("a withdrawal beside the seating (not in its past) is not read by it: B is seated (#241 L6)",
     [G3, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), ST.withdraw("wa", "A", "ba", ("ba",)),
      elect("el", "B", ("ba", "bb"), M3)],
     MOD("B"), "the fold"),
    ("another key's withdrawal of A's ballot withdraws nothing: B is seated",
     [G3, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), ST.withdraw("wa", "B", "ba", ("ba",)),
      elect("el", "B", ("ba", "bb", "wa"), M3)],
     MOD("B"), "the fold"),
    # ---- a vacancy ---------------------------------------------------------------------------------------------------
    ("a room with a duty holder does not elect: A holds moderate by the founding record, and B's seating concludes nothing",
     [FH, ballot("bb", "B", "B", ("g",)), ballot("bc", "C", "B", ("g",)), elect("el", "B", ("bb", "bc"), M3, heads=("g",))],
     NOMOD("B", "C") + MOD("A"), "a vacancy"),
    ("the last holder lays its duty down: at a head after that, the room elects B",
     [FH, ST.withdraw("wm", "A", "g", ("g",), scope="moderate"), ballot("bb", "B", "B", ("wm",)),
      ballot("bc", "C", "B", ("wm",)), elect("el", "B", ("bb", "bc"), M3, heads=("wm",))],
     MOD("B") + NOMOD("A", "C") + [("A", "member", T)], "a vacancy"),
    ("the last holder leaves the room: at a head after that, the room elects B",
     [FH, ST.withdraw("wa", "A", "g", ("g",)), ballot("bb", "B", "B", ("wa",)), ballot("bc", "C", "B", ("wa",)),
      elect("el", "B", ("bb", "bc"), M3, heads=("wa",))],
     MOD("B") + NOMOD("A") + [("A", "member", F)], "a vacancy"),
    ("one of two holders lays its duty down: the other is left, and the room does not elect",
     [FH2, ST.withdraw("wm", "A", "g", ("g",), scope="moderate"), ballot("bb", "B", "C", ("wm",)),
      ballot("bc", "C", "C", ("wm",)), elect("el", "C", ("bb", "bc"), M3, heads=("wm",))],
     NOMOD("A", "C") + MOD("B"), "a vacancy"),
    ("an AI agent's key holding moderate is no holder: A, the lone holder, confers moderate on the agent X and lays "
     "its own down; the room, no person holding a duty, elects B (#241 L5: the vacancy is over every duty, by person)",
     [G3, admit("ax", "X", ("A", "B"), ("g",), "agent"),
      ST.offer("cx", "A", "X", "moderate", OBJ, "group", ("ax",), head=("ax",), policy="duty_confer", counted="duty",
               cosigners=("X",)),
      ST.withdraw("lm", "A", "g", ("cx",), scope="moderate"),
      ballot("bb", "B", "B", ("lm",)), ballot("bc", "C", "B", ("lm",)), elect("el", "B", ("bb", "bc"), M3, heads=("lm",))],
     [("X", "moderate", T)] + MOD("B"), "a vacancy"),
    # ---- a decline ---------------------------------------------------------------------------------------------------
    ("a winner who declines passes the duty to the next in runoff order (CC 4.5.13; #241 O4): of eight, A has four "
     "first choices, C three, B one; B goes out first and its ballot to A, who wins and declines; run on, C goes out "
     "next, so the order is A, C, B, and the seating of C stands",
     ELECT8 + [DA, elect("ec", "C", B8 + ("da",), M3)], MOD("C") + NOMOD("A", "B"), "a decline"),
    ("not a rerun: the seating of B (A's four ballots passing to B in a count without A) concludes nothing",
     ELECT8 + [DA, elect("eb", "B", B8 + ("da",), M3)], NOMOD("A", "B", "C"), "a decline"),
    ("a decline in the seating's past that it does not name is not read: the count yields A, and the seating of C concludes nothing",
     ELECT8 + [DA, CK.row("nx", "note", "B", ("da",)), elect("ec", "C", B8, M3, cites=("nx",))],
     NOMOD("A", "B", "C"), "a decline"),
    ("A and C decline: the next in runoff order is B",
     ELECT8 + [DA, CK.row("dc", "decline", "C", ("lm",)), elect("eb", "B", B8 + ("da", "dc"), M3)],
     MOD("B") + NOMOD("A", "C"), "a decline"),
    ("a decline by a key the count does not yield first passes nothing: C declines, A is seated",
     ELECT8 + [CK.row("dc", "decline", "C", ("lm",)), elect("ea", "A", B8 + ("dc",), M3)],
     MOD("A") + NOMOD("C"), "a decline"),
    ("where a tie after the majority leaves the order below the winner unknown, a decline passes to nobody (#241 L2; "
     "CC 4.5.13 'An election declares no order, so a tie there seats nobody'): of five, "
     "A has three, B and C one each; A declines, and the seating of B concludes nothing",
     [G5, LM, ballot("ba", "A", "A"), ballot("bd", "D", "A"), ballot("be", "E", "A"), ballot("bb", "B", "B"),
      ballot("bc", "C", "C"), CK.row("da", "decline", "A", ("lm",)),
      elect("eb", "B", ("ba", "bd", "be", "bb", "bc", "da"), M3)],
     NOMOD("A", "B", "C"), "a decline"),
    # ---- several acceptances of one election ------------------------------------------------------------------------
    ("two seatings of one election over different sets of equal size are a tie, and neither seats anyone (CC 4.5.13; "
     "#241 N2): B over A's and B's ballots, C over C's and D's, then an admission naming both",
     [G4, LM, LM] + EQ4 + [admit("ax", "X", ("A", "B", "C"), ("eb", "ec"))], NOMOD("B", "C") + [("X", "member", T)],
     "several acceptances"),
    ("the same two, read while they are two tips: neither stands", [G4, LM, LM] + EQ4, NOMOD("B", "C"), "several acceptances"),
    ("the seating over the larger set stands, the set counted in rows (#241 L3; CC 4.5.13 'the one counted over the "
     "larger set stands, a larger set being a count'): B over two ballots, C over all five",
     [G5, LM, LM] + LG5 + [admit("ax", "X", ("A", "B", "C", "D"), ("eb", "ec"))], NOMOD("B") + MOD("C"), "several acceptances"),
    ("and at the two tips, C's seat waits as any seat at two tips does, until a row names both (#241 L4)",
     [G5, LM, LM] + LG5, NOMOD("B", "C"), "several acceptances"),
    ("a tie ended by a seating over a larger set (the union and E's ballot): C stands",
     [G5, LM, LM] + EQ4 + [ballot("be", "E", "C"), elect("eu", "C", ("ba", "bb", "bc", "bd", "be"), M5),
                   admit("ax", "X", ("A", "B", "C", "D"), ("eb", "ec", "eu"))],
     NOMOD("B") + MOD("C"), "several acceptances"),
    ("two seatings over the same set are one answer: both seat B",
     [G3, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), elect("e1", "B", ("ba", "bb"), M3),
      elect("e2", "B", ("ba", "bb"), M3, signer="A"), ST.accept("ab", "B", "e2"), admit("ax", "X", ("A", "B"), ("e1", "ab"))],
     MOD("B"), "several acceptances"),
    ("a seating of the next election (its past holds the last seating) is not outvoted by the last one's larger set: "
     "B seated over three ballots, then B resigns its duty and C is seated over two",
     [G3, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), ballot("bc", "C", "B"), elect("e1", "B", ("ba", "bb", "bc"), M3),
      ST.withdraw("wb", "B", "e1", ("e1",)), ballot("ba2", "A", "C", ("wb",)), ballot("bc2", "C", "C", ("wb",)),
      elect("e2", "C", ("ba2", "bc2"), M3, heads=("wb",))],
     NOMOD("B") + MOD("C"), "the election id"),
    ("a decline does not pass into options struck together (#241 L1; CC 4.5.13 'An election declares no order'): "
     "of five, A has three first choices and the others none, so B to E go out together; A declines, and the "
     "seating of B concludes nothing",
     DEC5 + [elect("eb", "B", ("ba", "bb", "bc", "da"), M5)], NOMOD("A", "B"), "a decline"),
    ("a seating that lists its options in an order gets the same answer: nothing",
     DEC5 + [elect("eb", "B", ("ba", "bb", "bc", "da"), ("B", "C", "D", "E", "A"))], NOMOD("A", "B"), "a decline"),
    # ---- a recall --------------------------------------------------------------------------------------------------------
    ("a recall that leaves no holder: the room elects at a head after it",
     [FH4, recall("rc", "A", ("B", "C", "D"), ("g",)), ballot("bb", "B", "B", ("rc",)), ballot("bc", "C", "B", ("rc",)),
      elect("el", "B", ("bb", "bc"), M4, heads=("rc",))],
     NOMOD("A") + MOD("B"), "a recall"),
    ("the recall against a plain count with the same threshold: of three, B and C remove A's moderate seat under "
     "StrictFloor(2, 3, 2), A in the base and a voice: 2 of 3 is not more than two thirds, and A stays",
     [ROOM(3), ST.unseat("rc", "B", "A", "moderate", OBJ, "group", ("g",), head=("g",), policy=PLAIN_FLOOR,
                         cosigners=("C",))], MOD("A"), "a recall"),
    ("and the same rows under Recall(2, 3, 2): A out of the base and no voice, 2 of 2, and A is recalled",
     [ROOM(3), recall("rc", "A", ("B", "C"), ("g",))], NOMOD("A"), "a recall"),
    ("a room of one: no recall (no other member, and the floor is two voices)",
     [FH1, recall("rc", "A", ("A",), ("g",))], MOD("A"), "a recall"),
    ("two members: no recall possible: the one other is below the floor of two (#241 C1: the recall is counted over "
     "the roster less the holder it recalls, who is no voice of it)",
     [ROOM(2), recall("rc", "A", ("B",), ("g",))], MOD("A"), "a recall"),
    ("two members: the holder's own voice is none, so A and B together do not recall A either",
     [ROOM(2), recall("rc", "A", ("A", "B"), ("g",))], MOD("A"), "a recall"),
    ("three members: both others recall (2 of 2)", [ROOM(3), recall("rc", "A", ("B", "C"), ("g",))], NOMOD("A"), "a recall"),
    ("three members: one other does not", [ROOM(3), recall("rc", "A", ("B",), ("g",))], MOD("A"), "a recall"),
    ("four members: all three others recall", [ROOM(4), recall("rc", "A", ("B", "C", "D"), ("g",))], NOMOD("A"), "a recall"),
    ("four members: two of the three others do not (2 of 3 is not strictly more than two thirds), the holder's own "
     "voice beside them none", [ROOM(4), recall("rc", "A", ("A", "B", "C"), ("g",))], MOD("A"), "a recall"),
    ("five members: three of the four others recall", [ROOM(5), recall("rc", "A", ("B", "C", "D"), ("g",))], NOMOD("A"),
     "a recall"),
    ("five members: two of four do not", [ROOM(5), recall("rc", "A", ("B", "C"), ("g",))], MOD("A"), "a recall"),
    ("six members: four of the five others recall", [ROOM(6), recall("rc", "A", ("B", "C", "D", "E"), ("g",))], NOMOD("A"),
     "a recall"),
    ("six members: three of five do not", [ROOM(6), recall("rc", "A", ("B", "C", "D"), ("g",))], MOD("A"), "a recall"),
    ("seven members: five of the six others recall", [ROOM(7), recall("rc", "A", ("B", "C", "D", "E", "F"), ("g",))],
     NOMOD("A"), "a recall"),
    ("seven members: four of six do not", [ROOM(7), recall("rc", "A", ("B", "C", "D", "E"), ("g",))], MOD("A"), "a recall"),
    # ---- the seat ----------------------------------------------------------------------------------------------------
    ("a seating signed by another key seats the winner only with the winner's acceptance: none here",
     [G3, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), elect("el", "B", ("ba", "bb"), M3, signer="A")],
     NOMOD("B", "A"), "the result"),
    ("and with it, seated",
     [G3, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), elect("el", "B", ("ba", "bb"), M3, signer="A"),
      ST.accept("ab", "B", "el")],
     MOD("B") + NOMOD("A"), "the result"),
    ("the elected seat stands only while its holder is a member: B leaves after it is seated",
     [G3, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), elect("el", "B", ("ba", "bb"), M3),
      ST.withdraw("wb", "B", "g", ("el",))],
     NOMOD("B") + [("B", "member", F)], "the result"),
]

# Rows the text does not decide: each carries the answer the model gives now and the candidate answers. Read like the
# cases (the answer now, in every arrival order), so a change to it is seen; the answer is no ruling.
# (name, rows, [(key, scope, stands now)], ledger item, the candidate answers)
OPEN = []


@contextlib.contextmanager
def planted(plant):
    saved, pol, rx = set(ST.MUT), dict(ST.POLICY), set(RX.MUT)
    if plant == "recall_at_least":
        ST.POLICY["moderator_recall"] = ("atleast", 2, 3)       # the table's 2/3 read as at least
    elif plant in RX_PLANTS:
        RX.MUT.add(plant)
    elif plant:
        ST.MUT.add(plant)
    try:
        yield
    finally:
        ST.MUT.clear(); ST.MUT |= saved
        ST.POLICY.clear(); ST.POLICY.update(pol)
        RX.MUT.clear(); RX.MUT |= rx


PLANTS = ("ballot_any_signer", "ballot_unnamed", "election_declared", "election_any_winner", "ballot_withdrawal_unread",
          "ballot_nonmember_ranked", "election_beside_holder", "election_agent_holder",
          "candidates_roster", "ballot_ranks_unbounded", "recall_at_least",
          "decline_unread", "larger_set_unread", "election_id_unread",
          "candidates_options", "floor_unread", "runoff_forward", "zero_strike_off",
          "recall_holder_in_base", "recall_holder_voice",
          "recall_as_strictfloor")
RX_PLANTS = ("runoff_forward", "zero_strike_off")        # planted in reexpress.py, the ranked count's reference


def answers(rows, asks, plant=None, arrive=False):
    with planted(plant):
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
    for name, rows, asks, _item, _cands in OPEN:
        got = answers(rows, asks)
        if got != [w for _, _, w in asks]:
            problems.append("%s: the answer now is %s, recorded %s" % (name, got, [w for _, _, w in asks]))
        for p in orders(rows):
            n_orders += 1
            if answers([rows[0]] + list(p), asks, arrive=True) != got:
                problems.append("%s: order %s differs" % (name, [r["id"] for r in p]))
                break
        print("  %s\n    candidates: %s" % (name, _cands))
    caught = 0
    for plant in PLANTS:
        hit = [name for name, rows, asks, _ in CASES if answers(rows, asks, plant) != [w for _, _, w in asks]]
        caught += bool(hit)
        print("  plant %-20s %s" % (plant, "caught by %d cases, first: %s" % (len(hit), hit[0]) if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % plant)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases, %d answers, %d open, %d orders, %d of %d planted breaks caught"
          % ("ok" if not problems else "%d problems" % len(problems), len(CASES), sum(len(a) for _, _, a, _ in CASES),
             len(OPEN), n_orders, caught, len(PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
