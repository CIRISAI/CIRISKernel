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

CK = ST.CK
T, F = True, False
OBJ = "g"
RULE = lambda r, P, past: ST.seat_rule(r, P, past)
LEDGER = "CIRISConstitution#241: "

# rooms founded with members only: no duty holder (CC 4.5.4 (v): "With no duty holder left the room locks, and the
# members' count seats one")
G1 = ST.offer("g", "A", ("A",), "member", "@", "self")
G3 = ST.offer("g", "A", ("A", "B", "C"), "member", "@", "self", cosigners=("B", "C"))
G4 = ST.offer("g", "A", ("A", "B", "C", "D"), "member", "@", "self", cosigners=("B", "C", "D"))
G5 = ST.offer("g", "A", ("A", "B", "C", "D", "E"), "member", "@", "self", cosigners=("B", "C", "D", "E"))
G8 = ST.offer("g", "A", tuple("ABCDEFGH"), "member", "@", "self", cosigners=tuple("BCDEFGH"))

# rooms whose founding record seats duty holders: A alone holds moderate (FH), A and B do (FH2)
FH = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("A",)}, cosigners=("B", "C"))
FH2 = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("A", "B")}, cosigners=("B", "C"))


def ballot(i, k, ranking, names=("g",)):
    """A member's ballot (`ballot:moderator`): its ranking, best first."""
    return CK.row(i, "ballot", k, tuple(names), ranking=tuple(ranking))


def elect(i, k, ballots, members, signer=None, heads=("g",), cites=()):
    """The seating of `k` by the election, counted over the ballots it names at `heads`; `members` its options."""
    return ST.offer(i, signer or k, k, "moderate", OBJ, "group", tuple(ballots) + tuple(heads) + tuple(cites),
                    head=tuple(heads), policy="moderator_election", options=tuple(members))


def admit(i, k, signers, heads, scope="member"):
    """A widening under the room's protocol, the joiner cosigning."""
    return ST.offer(i, signers[0], k, scope, OBJ, "group", tuple(heads), head=tuple(heads), policy="community_invite",
                    cosigners=tuple(signers[1:]) + ((k,) if k not in signers else ()))


M3, M4, M5 = ("A", "B", "C"), ("A", "B", "C", "D"), ("A", "B", "C", "D", "E")
MOD = lambda *ks: [(k, "moderate", T) for k in ks]
NOMOD = lambda *ks: [(k, "moderate", F) for k in ks]

# (name, rows, [(key, scope, stands)], ledger item)
CASES = [
    # ---- the count -------------------------------------------------------------------------------------------------
    ("two of three rank B first: B is seated",
     [G3, ballot("ba", "A", "B"), ballot("bb", "B", "B"), elect("el", "B", ("ba", "bb"), M3)],
     MOD("B") + NOMOD("A", "C") + [("B", "member", T)], "the count"),
    ("the same ballots seating A: the count yields B, so the row concludes nothing",
     [G3, ballot("ba", "A", "B"), ballot("bb", "B", "B"), elect("el", "A", ("ba", "bb"), M3)],
     NOMOD("A", "B", "C"), "the count"),
    ("a weakest option eliminated passes its ballot on: of five, over the options A, B and C, A's ballot moves to C, who has a majority",
     [G5, ballot("ba", "A", "AC"), ballot("bb", "B", "B"), ballot("bc", "C", "C"), ballot("bd", "D", "C"),
      ballot("be", "E", "B"), elect("el", "C", ("ba", "bb", "bc", "bd", "be"), M3)],
     MOD("C") + NOMOD("A", "B"), "the count"),
    ("the same ballots seating B, the strongest first choice tied with C: nothing",
     [G5, ballot("ba", "A", "AC"), ballot("bb", "B", "B"), ballot("bc", "C", "C"), ballot("bd", "D", "C"),
      ballot("be", "E", "B"), elect("el", "B", ("ba", "bb", "bc", "bd", "be"), M3)],
     NOMOD("A", "B", "C"), "the count"),
    # ---- ties --------------------------------------------------------------------------------------------------------
    ("three ballots, three first choices: a tie for weakest seats nobody (an election declares no order)",
     [G3, ballot("ba", "A", "AB"), ballot("bb", "B", "B"), ballot("bc", "C", "C"),
      elect("el", "A", ("ba", "bb", "bc"), M3)],
     NOMOD("A", "B", "C"), "ties"),
    ("the same ballots seating C, the last option listed: nothing (no order of the options decides)",
     [G3, ballot("ba", "A", "AB"), ballot("bb", "B", "B"), ballot("bc", "C", "C"),
      elect("el", "C", ("ba", "bb", "bc"), M3)],
     NOMOD("A", "B", "C"), "ties"),
    ("two against two: a tie seats nobody",
     [G4, ballot("ba", "A", "A"), ballot("bb", "B", "A"), ballot("bc", "C", "C"), ballot("bd", "D", "C"),
      elect("el", "A", ("ba", "bb", "bc", "bd"), M4)],
     NOMOD("A", "C"), "ties"),
    ("the count runs again over the ballots then held: a fifth ballot naming the four breaks the tie",
     [G5, ballot("ba", "A", "A"), ballot("bb", "B", "A"), ballot("bc", "C", "C"), ballot("bd", "D", "C"),
      ballot("be", "E", "C"), elect("el", "C", ("ba", "bb", "bc", "bd", "be"), M5)],
     MOD("C") + NOMOD("A"), "ties"),
    # ---- the floor ---------------------------------------------------------------------------------------------------
    ("one ballot in a room of three is under the floor of two: nobody",
     [G3, ballot("ba", "A", "B"), elect("el", "B", ("ba",), M3)], NOMOD("A", "B"), "the floor"),
    ("a room of one elects itself by its own ballot (the floor is the roster's size)",
     [G1, ballot("ba", "A", "A"), elect("el", "A", ("ba",), ("A",))], MOD("A"), "the floor"),
    ("a seating that names no ballot seats nobody, in a room of one too",
     [G1, elect("el", "A", (), ("A",))], NOMOD("A"), "the floor"),
    # ---- whose ballot ------------------------------------------------------------------------------------------------
    ("a ballot from a key the room does not seat counts for nothing: one member's ballot is under the floor",
     [G3, ballot("ba", "A", "B"), ballot("bx", "X", "B"), elect("el", "B", ("ba", "bx"), M3)],
     NOMOD("A", "B"), "the base"),
    ("an agent's ballot is no voice (an AI agent's key is in no count): one person's ballot is under the floor",
     [G3, admit("ax", "X", ("A", "B"), ("g",), "agent"), ballot("ba", "A", "B", ("ax",)),
      ballot("bx", "X", "B", ("ax",)), elect("el", "B", ("ba", "bx"), M3, heads=("ax",))],
     NOMOD("A", "B") + [("X", "agent", T)], "the base"),
    ("a ballot the seating does not name is not counted: the seating names B's ballot only, which names A's",
     [G3, ballot("ba", "A", "B"), ballot("bb", "B", "B", ("ba",)), elect("el", "B", ("bb",), M3)],
     NOMOD("B"), "the ballot set"),
    ("a ballot ranking a key the room does not seat is not counted, the whole ballot: one ballot is under the floor",
     [G3, ballot("ba", "A", "XB"), ballot("bb", "B", "B"), elect("el", "B", ("ba", "bb"), M3)],
     NOMOD("A", "B"), "who may stand"),
    ("a ballot ranking an agent's key (which holds `agent`, no member seat) is not counted: one ballot is under the floor",
     [G3, admit("ax", "X", ("A", "B"), ("g",), "agent"), ballot("ba", "A", "XB", ("ax",)),
      ballot("bb", "B", "B", ("ax",)), elect("el", "B", ("ba", "bb"), M3, heads=("ax",))],
     NOMOD("A", "B") + [("X", "agent", T)], "who may stand"),
    ("a ballot ranking a key admitted after the head the seating names is not counted",
     [G3, ballot("ba", "A", "XB"), ballot("bb", "B", "B"), admit("ax", "X", ("A", "B"), ("g",)),
      elect("el", "B", ("ba", "bb"), M3, cites=("ax",))],
     NOMOD("A", "B") + [("X", "member", T)], "who may stand"),
    ("and counted at a head after the admission: two ballots, B is seated",
     [G3, admit("ax", "X", ("A", "B"), ("g",)), ballot("ba", "A", "XB", ("ax",)), ballot("bb", "B", "B", ("ax",)),
      elect("el", "B", ("ba", "bb"), M3, heads=("ax",))],
     MOD("B"), "who may stand"),
    ("a ballot ranking first a member who left, its leaving in the seating's past, is not counted (#241 O2, derived: "
     "a leaver is out of the base, the voices and the candidates): one ballot is under the floor",
     [G4, ST.withdraw("wc", "C", "g", ("g",)), ballot("ba", "A", "CB"), ballot("bb", "B", "B"),
      elect("el", "B", ("ba", "bb"), ("B", "D"), cites=("wc",))],
     NOMOD("B") + [("C", "member", F)], "a candidate who leaves"),
    ("the leaver's own ballot is not counted either: B and the leaver C rank B, one ballot is under the floor",
     [G4, ST.withdraw("wc", "C", "g", ("g",)), ballot("bc", "C", "B"), ballot("bb", "B", "B"),
      elect("el", "B", ("bc", "bb"), ("B", "D"), cites=("wc",))],
     NOMOD("B"), "a candidate who leaves"),
    ("and without the leaving in its past, the seating counts both: B is seated (C's leaving beside it)",
     [G4, ST.withdraw("wc", "C", "g", ("g",)), ballot("ba", "A", "CB"), ballot("bb", "B", "B"),
      elect("el", "B", ("ba", "bb"), ("B", "D"))],
     MOD("B"), "a candidate who leaves"),
    # ---- one ballot a person -----------------------------------------------------------------------------------------
    ("two different ballots by one member are none: B's one ballot is under the floor",
     [G3, ballot("ba", "A", "B"), ballot("ba2", "A", "C"), ballot("bb", "B", "B"),
      elect("el", "B", ("ba", "ba2", "bb"), M3)],
     NOMOD("A", "B", "C"), "the fold"),
    ("two agreeing ballots by one member are one",
     [G3, ballot("ba", "A", "B"), ballot("ba2", "A", "B"), ballot("bb", "B", "B"),
      elect("el", "B", ("ba", "ba2", "bb"), M3)],
     MOD("B"), "the fold"),
    # ---- a withdrawal -------------------------------------------------------------------------------------------------
    ("a ballot its signer withdrew, the withdrawal in the seating's past, is none: one ballot is under the floor",
     [G3, ballot("ba", "A", "B"), ballot("bb", "B", "B"), ST.withdraw("wa", "A", "ba", ("ba",)),
      elect("el", "B", ("ba", "bb", "wa"), M3)],
     NOMOD("A", "B"), "the fold"),
    ("of two disagreeing ballots, one withdrawn: the other stands, and B is seated",
     [G3, ballot("ba", "A", "C"), ballot("ba2", "A", "B"), ballot("bb", "B", "B"), ST.withdraw("wa", "A", "ba", ("ba",)),
      elect("el", "B", ("ba", "ba2", "bb", "wa"), M3)],
     MOD("B") + NOMOD("A", "C"), "the fold"),
    ("a withdrawal beside the seating (not in its past) is not read by it: B is seated",
     [G3, ballot("ba", "A", "B"), ballot("bb", "B", "B"), ST.withdraw("wa", "A", "ba", ("ba",)),
      elect("el", "B", ("ba", "bb"), M3)],
     MOD("B"), "the fold"),
    ("another key's withdrawal of A's ballot withdraws nothing: B is seated",
     [G3, ballot("ba", "A", "B"), ballot("bb", "B", "B"), ST.withdraw("wa", "B", "ba", ("ba",)),
      elect("el", "B", ("ba", "bb", "wa"), M3)],
     MOD("B"), "the fold"),
    # ---- a vacancy ---------------------------------------------------------------------------------------------------
    ("a room with a duty holder does not elect: A holds moderate by the founding record, and B's seating concludes nothing",
     [FH, ballot("bb", "B", "B"), ballot("bc", "C", "B"), elect("el", "B", ("bb", "bc"), M3)],
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
    ("an AI agent's key holding moderate is no holder: the room, its persons holding no duty, elects B",
     [G3, admit("ax", "X", ("A", "B"), ("g",), "agent"),
      ST.offer("cx", "A", "X", "moderate", OBJ, "group", ("ax",), head=("ax",), policy="community_invite",
               counted="member", cosigners=("B", "X")),
      ballot("bb", "B", "B", ("cx",)), ballot("bc", "C", "B", ("cx",)), elect("el", "B", ("bb", "bc"), M3, heads=("cx",))],
     [("X", "moderate", T)] + MOD("B"), "a vacancy"),
    # ---- the seat ----------------------------------------------------------------------------------------------------
    ("a seating signed by another key seats the winner only with the winner's acceptance: none here",
     [G3, ballot("ba", "A", "B"), ballot("bb", "B", "B"), elect("el", "B", ("ba", "bb"), M3, signer="A")],
     NOMOD("B", "A"), "the result"),
    ("and with it, seated",
     [G3, ballot("ba", "A", "B"), ballot("bb", "B", "B"), elect("el", "B", ("ba", "bb"), M3, signer="A"),
      ST.accept("ab", "B", "el")],
     MOD("B") + NOMOD("A"), "the result"),
    ("the elected seat stands only while its holder is a member: B leaves after it is seated",
     [G3, ballot("ba", "A", "B"), ballot("bb", "B", "B"), elect("el", "B", ("ba", "bb"), M3),
      ST.withdraw("wb", "B", "g", ("el",))],
     NOMOD("B") + [("B", "member", F)], "the result"),
]

# Rows the text does not decide: each carries the answer the model gives now and the candidate answers. Read like the
# cases (the answer now, in every arrival order), so a change to it is seen; the answer is no ruling.
# (name, rows, [(key, scope, stands now)], ledger item, the candidate answers)
OPEN = [
    ("OPEN: every member a candidate, as the text says the ballot is: of five, over the roster's five, D and E named by "
     "no ballot tie for weakest at no first choice, and the count seats nobody",
     [G5, ballot("ba", "A", "AC"), ballot("bb", "B", "B"), ballot("bc", "C", "C"), ballot("bd", "D", "C"),
      ballot("be", "E", "B"), elect("el", "C", ("ba", "bb", "bc", "bd", "be"), M5)],
     NOMOD("A", "B", "C"), "who may stand",
     "nobody (CC 4.5.13 'a tie seats nobody', read over every member, the crate's answer where the options are the "
     "roster) | C (the members no ballot names are no standing candidates, and the count runs as over A, B and C). "
     "Over a roster of n with every member voting and no first-round majority, two members with no first choice is "
     "the common case, so under the first reading a runoff seldom decides."),
    ("OPEN: a ballot ranking four, where the text says each person ranks up to three: A ranks B, C, D and E; B ranks B",
     [G5, ballot("ba", "A", "BCDE"), ballot("bb", "B", "B"), elect("el", "B", ("ba", "bb"), M5)],
     MOD("B"), "the ballot",
     "B (the whole ranking counted, the model's answer; or its first three, the same here) | nobody (a ballot "
     "ranking more than three is refused or void; one ballot is then under the floor)"),
    ("OPEN: a winner who declines: of eight, A has four first choices, C three, B one, and B's ballot passes to A, "
     "who wins and declines; one seating names B and one C, each over the ballots and the decline",
     [G8, ballot("ba", "A", "AB"), ballot("bd", "D", "AB"), ballot("be", "E", "AB"), ballot("bf", "F", "AB"),
      ballot("bb", "B", "BA"), ballot("bc", "C", "C"), ballot("bg", "G", "C"), ballot("bh", "H", "C"),
      CK.row("da", "decline", "A", ("g",)),
      elect("eb", "B", ("ba", "bd", "be", "bf", "bb", "bc", "bg", "bh", "da"), M3),
      elect("ec", "C", ("ba", "bd", "be", "bf", "bb", "bc", "bg", "bh", "da"), M3)],
     NOMOD("A", "B", "C"), "a decline",
     "C (the next in runoff order read as the order the original count ranks them: A, then C, the last standing "
     "beside it, then B) | B (the count run again with the decliners struck: A's four ballots pass to B, five of "
     "eight). The text: 'passes the duty to the next in runoff order'; 'The count yields the first in the set's "
     "runoff order who has not declined'. The model reads no decline (a row of no seat kind) and seats nobody. "
     "Silence past `election_grace_secs` is a node's clock, no row."),
    ("NOT BUILT (the text decides): two seatings over different ballot sets of equal size, then an admission naming "
     "both: the model seats both (while the two seatings are two tips, each waits, and neither stands)",
     [G4, ballot("ba", "A", "B"), ballot("bb", "B", "B"), ballot("bc", "C", "C"), ballot("bd", "D", "C"),
      elect("eb", "B", ("ba", "bb"), M4), elect("ec", "C", ("bc", "bd"), M4), admit("ax", "X", ("A", "B", "C"), ("eb", "ec"))],
     MOD("B", "C"), "several acceptances",
     "neither (CC 4.5.13: 'Two acceptances over different sets of equal size are a tie, and neither seats anyone. "
     "The tie ends when the node holds an acceptance counted over the union of the two sets.'). Not built: the rows "
     "carry no election id (the digest of the community and the last seating row), so the crate cannot tell which "
     "seatings are one election's."),
    ("NOT BUILT (the text decides): a seating over a larger set beside one over a smaller, then an admission naming "
     "both: the model seats both",
     [G5, ballot("ba", "A", "B"), ballot("bb", "B", "B"), ballot("bc", "C", "C"), ballot("bd", "D", "C"),
      ballot("be", "E", "C"), elect("eb", "B", ("ba", "bb"), M5), elect("ec", "C", ("ba", "bb", "bc", "bd", "be"), M5),
      admit("ax", "X", ("A", "B", "C", "D"), ("eb", "ec"))],
     MOD("B", "C"), "several acceptances",
     "C only (CC 4.5.13: 'Among the valid acceptances a node holds, the one counted over the larger set stands, a "
     "larger set being a count'). Not built, as above. Read so here: 'larger' by the number of rows in the set, "
     "which covers the ballot, withdrawal and decline rows."),
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


PLANTS = ("ballot_any_signer", "ballot_unnamed", "election_declared", "election_any_winner", "ballot_withdrawal_unread",
          "ballot_nonmember_ranked", "election_beside_holder", "election_agent_holder",
          "candidates_roster")


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
