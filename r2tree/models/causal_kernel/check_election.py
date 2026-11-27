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
    runoff_from_eliminations  the runoff order read off one count's eliminations, not the count repeated (reexpress.py)
    runoff_tie_continues      a step of the runoff order that ties strikes an option and goes on (reexpress.py)
    size_any_row              every row a seating names counts toward the size of its set
    election_id_any           any row a seating names as its election is taken as that election
    holders_left_unread       a holder's own leaving or end of its stay is not subtracted from the vacancy test
    decline_unnamed           a decline in the row's past that the row does not name is read
    floor_one                 the floor passed to the count is one ballot, not two
    ballot_any_election       a ballot of another election counts
    seating_any_signer        a seating signed by another key than the winner concludes
    beaten_tip                an outvoted seating is a tip, so the standing one waits on it
    fold_ranked_counted       at tips, the fold counts an election's seating as a plain count (which it never meets)
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


def ballot(i, k, ranking, names=("lm",), of="g"):
    """A member's ballot (`ballot:moderator`): its ranking, best first, naming its election `of` (the last seating of
    moderate that stood, or the founding row)."""
    return CK.row(i, "ballot", k, tuple(names), ranking=tuple(ranking), of=of)


def decline(i, k, names=("lm",), of="g"):
    """A decline (`ballot:moderator_decline`), naming its election."""
    return CK.row(i, "decline", k, tuple(names), of=of)


DA = decline("da", "A")                                       # A's decline (`ballot:moderator_decline`)


def _elect8():
    return [G8, LM, ballot("ba", "A", "AB"), ballot("bd", "D", "AB"), ballot("be", "E", "AB"), ballot("bf", "F", "AB"),
            ballot("bb", "B", "BA"), ballot("bc", "C", "C"), ballot("bg", "G", "C"), ballot("bh", "H", "C")]


def elect(i, k, ballots, members, signer=None, heads=("lm",), cites=(), of="g"):
    """The seating of `k` by the election (its acceptance, signed by the winner), counted over the ballots it names at
    `heads`, naming its election `of`; `members` the options it lists (not read)."""
    return ST.offer(i, signer or k, k, "moderate", OBJ, "group", tuple(ballots) + tuple(heads) + tuple(cites),
                    head=tuple(heads), policy="moderator_election", options=tuple(members), of=of)


def admit(i, k, signers, heads, scope="member"):
    """A widening under the room's protocol, the joiner cosigning."""
    return ST.offer(i, signers[0], k, scope, OBJ, "group", tuple(heads), head=tuple(heads), policy="community_invite",
                    cosigners=tuple(signers[1:]) + ((k,) if k not in signers else ()))


ELECT8 = _elect8()
# the review's rows (#241): five honest ballots and C's seating over them; B's pads
HONEST = [ballot("ba", "A", "B"), ballot("bb", "B", "B"), ballot("bc", "C", "C"), ballot("bd", "D", "C"), ballot("be", "E", "C")]
EC = elect("ec", "C", ("ba", "bb", "bc", "bd", "be"), ("A", "B", "C", "D", "E"))
PAD = [ballot("bb%d" % i, "B", "B") for i in range(4)]
PADIDS = tuple(p["id"] for p in PAD)
PADX = [ballot("bx%d" % i, "X%d" % i, "B") for i in range(4)]          # four keys the room does not seat
PADXIDS = tuple(p["id"] for p in PADX)
PADW = [ST.withdraw("wx%d" % i, "B", "bc", ("bc",)) for i in range(4)]
PADWIDS = tuple(p["id"] for p in PADW)
# a first election seating B over three ballots, and B's resignation of that seat; the second election's ballots
E1ROWS = [ballot("ba", "A", "B"), ballot("bb", "B", "B"), ballot("bc", "C", "B"),
          elect("e1", "B", ("ba", "bb", "bc"), ("A", "B", "C")), ST.withdraw("wb", "B", "e1", ("e1",))]
NEW2 = [ballot("ba2", "A", "C", ("wb",), of="e1"), ballot("bc2", "C", "C", ("wb",), of="e1")]
# A wins at once and declines; B to E hold no ballot (DEC5)
DEC5 = [G5, LM, ballot("ba", "A", "A"), ballot("bb", "B", "A"), ballot("bc", "C", "A"), decline("da", "A", ("lm",))]
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
     [G10, LM] + [ballot("b" + k, k, r) for k, r in zip("ABCDEFGHIJ", ["A"] * 4 + ["B"] * 3 + ["CA"] * 3)]
     + [elect("el", "A", tuple("b" + k for k in "ABCDEFGHIJ"), M10)],
     NOMOD("A", "B", "C"), "ties"),
    ("first choices 5, 3 and 2: the seven go together, then the 2, whose ballots pass to A, who is seated",
     [G10, LM] + [ballot("b" + k, k, r) for k, r in zip("ABCDEFGHIJ", ["A"] * 5 + ["B"] * 3 + ["CA"] * 2)]
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
      ballot("bb", "B", "B", ("lm",), of="cx"), ballot("bc", "C", "B", ("lm",), of="cx"),
      elect("el", "B", ("bb", "bc"), M3, heads=("lm",), of="cx")],
     [("X", "moderate", T)] + MOD("B"), "a vacancy"),
    # ---- a decline ---------------------------------------------------------------------------------------------------
    ("a winner who declines passes the duty to the next in runoff order, the count repeated with it struck (CC 4.5.13; "
     "#241 O4): of eight, A has four first choices, C three, B one; B goes out and its ballot passes to A, who wins and "
     "declines; the count without A passes A's four ballots to B, who has five of eight, and the seating of B stands",
     ELECT8 + [DA, elect("eb", "B", B8 + ("da",), M3)], MOD("B") + NOMOD("A", "C"), "a decline"),
    ("the order is not read off the first count's eliminations: the seating of C (the last eliminated beside A) "
     "concludes nothing",
     ELECT8 + [DA, elect("ec", "C", B8 + ("da",), M3)], NOMOD("A", "B", "C"), "a decline"),
    ("first choices A 6, B 3, C 1 of ten, A's ballots ranking B next: A wins at once and declines; the count without A "
     "gives B nine of ten, and B is seated",
     [G10, LM] + [ballot("b" + k, k, r) for k, r in zip("ABCDEFGHIJ", ["AB"] * 6 + ["B"] * 3 + ["C"])]
     + [decline("da", "A"), elect("eb", "B", tuple("b" + k for k in "ABCDEFGHIJ") + ("da",), M10)],
     MOD("B") + NOMOD("A", "C"), "a decline"),
    ("first choices A 5, B 3, C 1, D 1 of ten: no first-round majority (5 is not more than half of 10), and C and D, "
     "each holding a ballot, tie for weakest: the count seats nobody, and the seating of A concludes nothing",
     [G10, LM] + [ballot("b" + k, k, r) for k, r in zip("ABCDEFGHIJ", ["AB"] * 5 + ["B"] * 3 + ["C", "D"])]
     + [elect("ea", "A", tuple("b" + k for k in "ABCDEFGHIJ"), M10)],
     NOMOD("A", "B"), "ties"),
    ("a decline in the seating's past that it does not name is not read: the count yields A, and the seating of C concludes nothing",
     ELECT8 + [DA, CK.row("nx", "note", "B", ("da",)), elect("ec", "C", B8, M3, cites=("nx",))],
     NOMOD("A", "B", "C"), "a decline"),
    ("A and C decline: the next in runoff order is B",
     ELECT8 + [DA, decline("dc", "C", ("lm",)), elect("eb", "B", B8 + ("da", "dc"), M3)],
     MOD("B") + NOMOD("A", "C"), "a decline"),
    ("a decline by a key the count does not yield first passes nothing: C declines, A is seated",
     ELECT8 + [decline("dc", "C", ("lm",)), elect("ea", "A", B8 + ("dc",), M3)],
     MOD("A") + NOMOD("C"), "a decline"),
    ("where the count with the decliner struck ties, the duty passes to nobody and the room elects again (#241 L2; "
     "CC 4.5.13 'An election declares no order, so a tie there seats nobody'): of five, "
     "A has three, B and C one each; A declines, and the seating of B concludes nothing",
     [G5, LM, ballot("ba", "A", "A"), ballot("bd", "D", "A"), ballot("be", "E", "A"), ballot("bb", "B", "B"),
      ballot("bc", "C", "C"), decline("da", "A", ("lm",)),
      elect("eb", "B", ("ba", "bd", "be", "bb", "bc", "da"), M3)],
     NOMOD("A", "B", "C"), "a decline"),
    # ---- several acceptances of one election ------------------------------------------------------------------------
    ("two seatings of one election over different sets of equal size are a tie, and neither seats anyone (CC 4.5.13; "
     "#241 N2): B over A's and B's ballots, C over C's and D's, then an admission naming both",
     [G4, LM] + EQ4 + [admit("ax", "X", ("A", "B", "C"), ("eb", "ec"))], NOMOD("B", "C") + [("X", "member", T)],
     "several acceptances"),
    ("the same two, read while they are two tips: neither stands", [G4, LM] + EQ4, NOMOD("B", "C"), "several acceptances"),
    ("the seating over the larger set stands, the set counted in rows (#241 L3; CC 4.5.13 'the one counted over the "
     "larger set stands, a larger set being a count'): B over two ballots, C over all five",
     [G5, LM] + LG5 + [admit("ax", "X", ("A", "B", "C", "D"), ("eb", "ec"))], NOMOD("B") + MOD("C"), "several acceptances"),
    ("and at the two tips: the outvoted seating is no tip, so C's seat does not wait on it (#241 A7)",
     [G5, LM] + LG5, NOMOD("B") + MOD("C"), "several acceptances"),
    ("a tie ended by a seating over a larger set (the union and E's ballot): C stands",
     [G5, LM] + EQ4 + [ballot("be", "E", "C"), elect("eu", "C", ("ba", "bb", "bc", "bd", "be"), M5),
                   admit("ax", "X", ("A", "B", "C", "D"), ("eb", "ec", "eu"))],
     NOMOD("B") + MOD("C"), "several acceptances"),
    ("two seatings over the same set are one answer: both seat B",
     [G3, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), elect("e1", "B", ("ba", "bb"), M3),
      elect("e2", "B", ("ba", "bb"), M3, signer="A"), ST.accept("ab", "B", "e2"), admit("ax", "X", ("A", "B"), ("e1", "ab"))],
     MOD("B"), "several acceptances"),
    ("a seating of the next election (its past holds the last seating) is not outvoted by the last one's larger set: "
     "B seated over three ballots, then B resigns its duty and C is seated over two",
     [G3, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), ballot("bc", "C", "B"), elect("e1", "B", ("ba", "bb", "bc"), M3),
      ST.withdraw("wb", "B", "e1", ("e1",)), ballot("ba2", "A", "C", ("wb",), of="e1"),
      ballot("bc2", "C", "C", ("wb",), of="e1"), elect("e2", "C", ("ba2", "bc2"), M3, heads=("wb",), of="e1")],
     NOMOD("B") + MOD("C"), "the election id"),
    ("a decline whose count has no ballot left seats nobody (#241 L1): of five, A has three first choices and the others "
     "none; A declines, the count without A holds no ballot that ranks anyone else, and the "
     "seating of B concludes nothing",
     DEC5 + [elect("eb", "B", ("ba", "bb", "bc", "da"), M5)], NOMOD("A", "B"), "a decline"),
    ("a seating that lists its options in an order gets the same answer: nothing",
     DEC5 + [elect("eb", "B", ("ba", "bb", "bc", "da"), ("B", "C", "D", "E", "A"))], NOMOD("A", "B"), "a decline"),
    # ---- the review's rows (#241 E-A1 to E-A6) -------------------------------------------------------------------------
    ("the size of a set is the persons of the electorate heard in it (#241 E-A1): B's four agreeing duplicate ballots "
     "beside A's add rows and no person, so the seating of C over five persons stands",
     [G5, LM] + HONEST + PAD + [EC, elect("eb", "B", ("ba", "bb") + PADIDS, M5),
                                admit("ax", "X", ("A", "B", "C", "D"), ("eb", "ec"))],
     NOMOD("B") + MOD("C"), "the size of a set"),
    ("a non-member's void ballots add nothing to the size: C stands",
     [G5, LM] + HONEST + PADX + [EC, elect("eb", "B", ("ba", "bb") + PADXIDS, M5),
                                 admit("ax", "X", ("A", "B", "C", "D"), ("eb", "ec"))],
     NOMOD("B") + MOD("C"), "the size of a set"),
    ("B's withdrawals of C's ballot (no withdrawal of B's own) add nothing to the size: C stands",
     [G5, LM] + HONEST + PADW + [EC, elect("eb", "B", ("ba", "bb") + PADWIDS, M5),
                                 admit("ax", "X", ("A", "B", "C", "D"), ("eb", "ec"))],
     NOMOD("B") + MOD("C"), "the size of a set"),
    ("of two sets hearing the same persons, the one holding more valid rows stands: B's ballot and its own withdrawal "
     "and a fresh ballot, beside the set without the withdrawal (#241 E-A1: a set that omits a withdrawal does not "
     "out-count the set that holds it)",
     [G3, LM, ballot("ba", "A", "C"), ballot("bb", "B", "B"), ST.withdraw("wb", "B", "bb", ("bb",)),
      ballot("bb2", "B", "C", ("wb",)), ballot("bc", "C", "C"),
      elect("eb", "B", ("ba", "bb", "bc"), M3), elect("ec", "C", ("ba", "bb", "wb", "bb2", "bc"), M3),
      admit("ax", "X", ("A", "B", "C"), ("eb", "ec"))],
     NOMOD("B") + MOD("C"), "the size of a set"),
    ("a seating signed by a non-member over a padded set concludes nothing (#241 E-A6), and C stands",
     [G5, LM] + HONEST + PADX + [EC, elect("eb", "B", ("ba", "bb") + PADXIDS, M5, signer="X"), ST.accept("ab", "B", "eb"),
                                 admit("ax", "X", ("A", "B", "C", "D"), ("ab", "ec"))],
     NOMOD("B") + MOD("C"), "the seating"),
    ("a later seating that has seen an earlier one of the same election names the same election, and the larger "
     "replaces it: B over two ballots, then C over all five, citing B's seating; C alone is seated (#241 E-A3)",
     [G5, LM] + HONEST + [elect("eb", "B", ("ba", "bb"), M5), elect("ec", "C", ("ba", "bb", "bc", "bd", "be"), M5, cites=("eb",))],
     NOMOD("B") + MOD("C"), "the election id"),
    ("a seating naming the election another seating of it was counted in is that election's rival, whatever it has "
     "seen: of four, B is seated over three ballots and resigns; a seating of C over four naming the founding row "
     "again is a larger seating of the same election, and C is seated (#241 E-A3)",
     [G4, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), ballot("bc", "C", "B"),
      elect("e1", "B", ("ba", "bb", "bc"), M4), ST.withdraw("wb", "B", "e1", ("e1",)),
      ballot("ba2", "A", "C", ("wb",), of="g"), ballot("bb2", "B", "C", ("wb",), of="g"),
      ballot("bc2", "C", "C", ("wb",), of="g"), ballot("bd2", "D", "C", ("wb",), of="g"),
      elect("e2", "C", ("ba2", "bb2", "bc2", "bd2"), M4, heads=("wb",), of="g")],
     NOMOD("B") + MOD("C"), "the election id"),
    ("a seating naming an election row that a later seating of another election follows concludes nothing: of three, "
     "B is seated in the first election (naming the founding row); B, the lone holder, confers moderate on C; both "
     "lay it down; a seating naming B's "
     "election row e1 then seats nobody, since C's conferral is the last seating that stood",
     [G3, LM] + E1ROWS[:4] + [
         ST.offer("cc", "B", "C", "moderate", OBJ, "group", ("e1",), head=("e1",), policy="duty_confer", counted="duty",
                  cosigners=("C",)),
         ST.withdraw("wb", "B", "e1", ("cc",)), ST.withdraw("wcc", "C", "cc", ("wb",)),
         ballot("ba2", "A", "A", ("wcc",), of="e1"), ballot("bb2", "B", "A", ("wcc",), of="e1"),
         elect("e2", "A", ("ba2", "bb2"), M3, heads=("wcc",), of="e1")],
     NOMOD("A", "B", "C"), "the election id"),
    ("old ballots named alone in the next election seat nobody: B's seating over the first election's ballots and A's "
     "new one counts A's new ballot only, under the floor",
     [G3, LM] + E1ROWS + NEW2 + [elect("e2x", "B", ("ba", "bb", "bc", "ba2"), M3, heads=("wb",), of="e1")],
     NOMOD("B", "C"), "the election id"),
    ("a holder's own end of its stay in the seating's past takes it out of the vacancy test, though it held the duty "
     "at the head the seating names: A leaves, and a seating at the founding head citing that elects B",
     [FH, ST.withdraw("wa", "A", "g", ("g",)), ballot("bb", "B", "B", ("wa",)), ballot("bc", "C", "B", ("wa",)),
      elect("el", "B", ("bb", "bc"), M3, heads=("g",), cites=("wa",))],
     MOD("B") + [("A", "member", F)], "a vacancy"),
    ("a seating naming an outvoted seating as its election concludes nothing: B's seating, beaten by C's, is no "
     "election row",
     [G5, LM] + LG5 + [ballot("bz", "A", "A", ("eb",), of="eb"), ballot("by", "B", "A", ("eb",), of="eb"),
                       elect("ez", "A", ("bz", "by"), M5, heads=("lm",), cites=("eb",), of="eb")],
     NOMOD("A", "B") + MOD("C"), "the election id"),
    ("old ballots named in the next election count for nothing (#241 E-A4): B's seating over the first election's "
     "ballots and A's new one concludes nothing, and C is seated",
     [G3, LM] + E1ROWS + NEW2 + [elect("e2", "C", ("ba2", "bc2"), M3, heads=("wb",), of="e1"),
                                 elect("e2x", "B", ("ba", "bb", "bc", "ba2"), M3, heads=("wb",), of="e1"),
                                 admit("ax", "X", ("A", "C"), ("e2", "e2x"))],
     NOMOD("B") + MOD("C"), "the election id"),
    ("a stale decline moves nothing and adds no size: A's decline in the first election, named by a seating of C in "
     "the second, is not read, and A is seated",
     [G3, LM, ballot("ba", "A", "CA"), ballot("bb", "B", "AC"), ballot("bc", "C", "CA"), decline("dz", "A"),
      elect("e1", "C", ("ba", "bb", "bc", "dz"), M3), ST.withdraw("wc", "C", "e1", ("e1",)),
      ballot("ba2", "A", "AC", ("wc",), of="e1"), ballot("bb2", "B", "AC", ("wc",), of="e1"),
      ballot("bc2", "C", "AC", ("wc",), of="e1"),
      elect("e2", "A", ("ba2", "bb2", "bc2"), M3, heads=("wc",), of="e1"),
      elect("e2x", "C", ("ba2", "bb2", "bc2", "dz"), M3, heads=("wc",), of="e1"),
      admit("ax", "X", ("A", "B"), ("e2", "e2x"))],
     MOD("A") + NOMOD("C"), "the election id"),
    ("a padded seating landing after the room was seated and opened is still beaten: C seated over five, an admission, "
     "then B over two ballots and four duplicates",
     [G5, LM] + HONEST + [EC, admit("ax", "X", ("A", "C", "D", "E"), ("ec",))] + PAD
     + [elect("eb", "B", ("ba", "bb") + PADIDS, M5), admit("ay", "Y", ("A", "C", "D", "E"), ("ax", "eb"))],
     NOMOD("B") + MOD("C"), "the size of a set"),
    ("a seating that names no ballot seats nobody, its count over an empty set",
     [G3, LM, ballot("ba", "A", "A"), elect("el", "A", (), M3)], NOMOD("A"), "the floor"),
    ("a seating naming no election seats nobody",
     [G3, LM, ballot("ba", "A", "B", of=None), ballot("bb", "B", "B", of=None), elect("el", "B", ("ba", "bb"), M3, of=None)],
     NOMOD("B"), "the election id"),
    ("a decline the row does not name is not read even where it is in the row's past and of the election: A is seated",
     [G3, LM, ballot("ba", "A", "AB"), ballot("bb", "B", "AB"), decline("da", "A"), CK.row("nx", "note", "B", ("da",)),
      elect("ea", "A", ("ba", "bb"), M3, cites=("nx",))],
     MOD("A"), "a decline"),
    ("at two tips, an election's seating beside an admission: the fold takes the seating as concluded (its ballots are "
     "read by the seat rule alone, as the crate reads it), so C stands (the case of the first Rust/Python disagreement)",
     [G5, LM] + HONEST + [EC, admit("ax", "X", ("A", "B", "C", "D"), ("lm",))], MOD("C") + [("X", "member", T)],
     "the seating"),
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
    ("the seating is the winner's acceptance: one signed by another key concludes nothing (#241 E-A6)",
     [G3, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), elect("el", "B", ("ba", "bb"), M3, signer="A")],
     NOMOD("B", "A"), "the result"),
    ("and the winner's later acceptance of it seats nobody either",
     [G3, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), elect("el", "B", ("ba", "bb"), M3, signer="A"),
      ST.accept("ab", "B", "el")],
     NOMOD("B", "A"), "the result"),
    ("the elected seat stands only while its holder is a member: B leaves after it is seated",
     [G3, LM, ballot("ba", "A", "B"), ballot("bb", "B", "B"), elect("el", "B", ("ba", "bb"), M3),
      ST.withdraw("wb", "B", "g", ("el",))],
     NOMOD("B") + [("B", "member", F)], "the result"),
]

# Rows the text does not decide: each carries the answer the model gives now and the candidate answers. Read like the
# cases (the answer now, in every arrival order), so a change to it is seen; the answer is no ruling.
# (name, rows, [(key, scope, stands now)], ledger item, the candidate answers)
OPEN = []


# the runoff order is the count repeated (#241): (name, ballots, options, order)
RUNOFF_CASES = [
    ("A 6, B 3, C 1 of ten, A's ranking B next: A, then B (A struck), then C", 
     [("p%d" % i, ("A", "B")) for i in range(6)] + [("q%d" % i, ("B",)) for i in range(3)] + [("r", ("C",))],
     list("ABCD"), ("A", "B", "C")),
    ("the eight of the decline cases: A, then B (not C, the last eliminated beside A)",
     [("a%d" % i, ("A", "B")) for i in range(4)] + [("b", ("B", "A"))] + [("c%d" % i, ("C",)) for i in range(3)],
     list("ABC"), ("A", "B", "C")),
    ("a step that ties ends the order: A 3, B 1, C 1; without A, B and C tie, so the order is A alone",
     [("a%d" % i, ("A",)) for i in range(3)] + [("b", ("B",)), ("c", ("C",))], list("ABC"), ("A",)),
]

# the tips of the room (#241 A7: an outvoted seating is no tip): (name, rows, tips)
TIP_CASES = [
    ("B's seating, outvoted by C's, is no tip: the one tip is C's", [G5, LM] + LG5, ("ec",)),
    ("two seatings of equal size and different sets are both outvoted: the tip is the founding row",
     [G4, LM] + EQ4, ("g",)),
]

# a reader's acknowledged line (#241 E-A2): (name, rows, reader, [(key, scope, stands)])
READER_CASES = [
    ("a reader that acknowledged B's seating holds C's rival at the same older head void (behind its line): B "
     "stands for it",
     [G4, LM] + EQ4 + [CK.row("ak", "ack", "R", ("eb",), room=OBJ, head=("eb",))], "R", MOD("B") + NOMOD("C")),
    ("a reader that acknowledged neither sees the tie: neither stands",
     [G4, LM] + EQ4 + [CK.row("ak", "ack", "R", ("eb",), room=OBJ, head=("eb",))], None, NOMOD("B", "C")),
]


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
          "candidates_options", "floor_unread", "runoff_from_eliminations", "runoff_tie_continues", "zero_strike_off",
          "recall_holder_in_base", "recall_holder_voice",
          "recall_as_strictfloor", "size_any_row", "election_id_any", "holders_left_unread", "decline_unnamed", "floor_one", "ballot_any_election", "seating_any_signer", "beaten_tip",
          "fold_ranked_counted")
RX_PLANTS = ("runoff_from_eliminations", "runoff_tie_continues", "zero_strike_off")        # planted in reexpress.py, the ranked count's reference


def answers(rows, asks, plant=None, arrive=False, own=None):
    with planted(plant):
        S = CK.arrive(list(rows), RULE) if arrive else CK.concluded(CK.kept(list(rows)), RULE)
        Q = ST.Seats(S, own=own)
        return [Q.stands(k, s, OBJ) for k, s, _ in asks]


def runoff_answers(plant=None):
    with planted(plant):
        return [RX.runoff(b, o, 2, False) for _, b, o, _ in RUNOFF_CASES]


def tip_answers(plant=None):
    out = []
    with planted(plant):
        for _, rows, _ in TIP_CASES:
            S = CK.concluded(CK.kept(list(rows)), RULE)
            out.append(tuple(sorted(x["id"] for x in ST.Seats(S).tips(OBJ))))
    return out


def reader_answers(plant=None, arrive_order=None):
    out = []
    for _, rows, own, asks in READER_CASES:
        rr = rows if arrive_order is None else arrive_order(rows)
        out.append(answers(rr, asks, plant, arrive=arrive_order is not None, own=own))
    return out


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
    for (name, _b, _o, want), got in zip(RUNOFF_CASES, runoff_answers()):
        if tuple(got) != want:
            problems.append("runoff %s: got %s, expected %s" % (name, got, want))
    for (name, _rows, want), got in zip(TIP_CASES, tip_answers()):
        if got != tuple(sorted(want)):
            problems.append("tips %s: got %s, expected %s" % (name, got, want))
    want_r = [[w for _, _, w in asks] for _, _, _, asks in READER_CASES]
    if reader_answers() != want_r:
        problems.append("reader cases: got %s, expected %s" % (reader_answers(), want_r))
    for name, rows, own, asks in READER_CASES:
        for p in orders(rows):
            n_orders += 1
            if answers([rows[0]] + list(p), asks, arrive=True, own=own) != [w for _, _, w in asks]:
                problems.append("%s: order %s differs" % (name, [r["id"] for r in p]))
                break
    caught = 0
    for plant in PLANTS:
        hit = [name for name, rows, asks, _ in CASES if answers(rows, asks, plant) != [w for _, _, w in asks]]
        hit += ["runoff: " + c[0] for c, got in zip(RUNOFF_CASES, runoff_answers(plant)) if tuple(got) != c[3]]
        hit += ["reader: " + c[0] for c, got, w in zip(READER_CASES, reader_answers(plant), want_r) if got != w]
        hit += ["tips: " + c[0] for c, got in zip(TIP_CASES, tip_answers(plant)) if got != tuple(sorted(c[2]))]
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
