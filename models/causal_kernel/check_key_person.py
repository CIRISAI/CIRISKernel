#!/usr/bin/env python3
"""
check_key_person.py: a key's person at a row, as a function of rows, with no instant (seat.person_of).

Ruled on CIRISConstitution#224: a key is live for its person at a row when, in the row's own past, the key is the
person's genesis key or was seated by an `identity:occurrence` that landed (self_roster_add); no eviction of it has
landed (self_roster_evict), an eviction concurrent with the row following rule 4 (it counts at its own head and is
out of force from that head on); and the key's own revocation is not in the row's past (seat.key_record_ended). The
key record's stated end is the key's own instant against the key's own row (key_end.covers), read there and not
here: no foreign clock. The person is the self roster (an object of kind `self`: a person's own key roster, CC
3.3.6.4, or a voice's room keys, CC 3.1.3.2); two persons are none.

Part 1. Cases: (name, rows, the row asked at, the key, the person expected), each in arrival orders.
Part 2. Planted breaks (seat.MUT), each of which must change a case's answer:
    person_evict_unread   an admission in the past is enough: an evicted key keeps its person
    person_first          two persons read as the first: a key in two self rosters gets one
    person_any_kind       any group is a person: a community's member seat makes the community a key's person
    person_end_unread     the key's own end is not read: a revoked key keeps its person
    concurrent_eviction_unread  rule 4 not read: a key evicted concurrently keeps its person at the eviction's head
    persons_unread        a count of keys, not persons: two keys of one person are two voices, a device no voice
    base_by_key           the base read by key: a person seated by two keys is two members (KP4)
    revoked_voice_kept    a key's own revocation leaves its voice, and its devices speak for it (KP6)
    agent_speaks          an agent's key that is also a key of a person's roster speaks for that person (KP5)
    lift_author_device    the lift leaves out only the remover's own key, not its devices (KP1)
    genesis_unread        each roster a person: two rosters of one genesis key make a key of two persons (K7)

    python3 -I check_key_person.py      exit 1 on any difference
"""
import itertools
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import seat as ST  # noqa: E402
import roomkey as RK  # noqa: E402
import window as WN  # noqa: E402
import check_election as EL  # noqa: E402
import check_room_keys as CR  # noqa: E402

CK, R = ST.CK, ST.R
RULE = lambda r, P, past: ST.seat_rule(r, P, past)
LEDGER = "a key to its person at a row, with no instant (0.5.0)"


def found(i, k, scope="self"):
    """A self roster founded by its first key."""
    return ST.offer(i, k, (k,), scope, "@", "self")


def add(i, roster, k, signers, heads, scope="self"):
    """A key added by the roster's own count (self_roster_add), the key signing its own seat."""
    return ST.offer(i, signers[0], k, scope, roster, "group", tuple(heads), head=tuple(heads), policy="self_roster_add",
                    counted=scope, cosigners=tuple(signers[1:]) + (k,))


def evict(i, roster, k, signers, heads, scope="self"):
    """A key evicted by the roster's own count (self_roster_evict)."""
    return ST.unseat(i, signers[0], k, scope, roster, "group", tuple(heads), head=tuple(heads), policy="self_roster_evict",
                     counted=scope, cosigners=tuple(signers[1:]))


def at(names):
    """The row asked at: a row naming `names`."""
    return R("at", "note", "x", tuple(names))


S = found("S", "k1")
A2 = add("a2", "S", "k2", ("k1",), ("S",))
A3 = add("a3", "S", "k3", ("k1", "k2"), ("a2",))
E3 = evict("e3", "S", "k3", ("k1", "k2"), ("a3",))
T = found("T", "t1")
T2 = add("b2", "T", "k2", ("t1",), ("T",))
REC = ST.offer("rec", "k1", "k1", "registered", "k1", "self")                  # k1's key record
RV = ST.unseat("rv", "k1", "k1", "registered", "k1", "self", ("rec", "S"))      # k1's own revocation
VA, HA = RK.voice_rows("vA", ["rk:a0", "rk:a1"])
G = ST.offer("g", "m1", ("m1", "m2"), "member", "@", "self", cosigners=("m2",))   # a community, no self roster
E2 = evict("e2", "S", "k2", ("k1", "k3"), ("a3",))                             # k2 evicted at the head a3

# (name, rows, key, person)
CASES = [
    ("the first key of a self roster, at a row naming the roster", [S, at(("S",))], "k1", "S"),
    ("a key added by the roster's count, at a row naming the addition", [S, A2, at(("a2",))], "k2", "S"),
    ("the same key at a row that does not have the addition in its past: no person yet", [S, A2, at(("S",))], "k2", None),
    ("a third key added by two, at a row naming its addition", [S, A2, A3, at(("a3",))], "k3", "S"),
    ("the third key evicted by the roster's count, at a row naming the eviction: no person", [S, A2, A3, E3, at(("e3",))],
     "k3", None),
    ("the other keys keep their person after the eviction", [S, A2, A3, E3, at(("e3",))], "k2", "S"),
    ("the evicted key at the eviction's own head, the eviction concurrent with the row: out (rule 4)",
     [S, A2, A3, E3, at(("a3",))], "k3", None),
    ("the evicted key at that head with no eviction held: its person then", [S, A2, A3, at(("a3",))], "k3", "S"),
    ("a key seated in two self rosters: two persons is none", [S, A2, T, T2, at(("a2", "b2"))], "k2", None),
    ("the same key with only one of the two in the row's past", [S, A2, T, T2, at(("a2",))], "k2", "S"),
    ("the key's own revocation in the row's past ends its person (the liveness half)", [S, REC, RV, at(("rv",))], "k1", None),
    ("the key's revocation not in the row's past", [S, REC, RV, at(("S",))], "k1", "S"),
    ("a room key of a voice: the voice is its person", VA + [at((HA,))], "rk:a1", "vA"),
    ("a member seat of a community is no person", [G, at(("g",))], "m1", None),
    ("a key no roster seats", [S, at(("S",))], "zz", None),
    # rule 4: an eviction concurrent with the row counts at its own head and is out of force from that head on
    ("an eviction concurrent with the row, the row at the eviction's head: the key is out from that head on",
     [S, A2, A3, E2, at(("a3",))], "k2", None),
    ("the same eviction, the row at an earlier head: the key's person then", [S, A2, A3, E2, at(("a2",))], "k2", "S"),
    ("the other keys at the eviction's head keep their person", [S, A2, A3, E2, at(("a3",))], "k3", "S"),
]
# ---- Part 3: counts over persons (ruled on CIRISConstitution#224: one voice however many live keys sign) ------------
# four persons, each a self roster named by its genesis key; p1 has a second device key p1b. They found a room whose
# members are the persons' genesis keys; a counted admission of z (community_invite, two thirds of four: three voices)
SP = {i: found("S%d" % i, "p%d" % i) for i in (1, 2, 3, 4)}
P1B = add("a1b", "S1", "p1b", ("p1",), ("S1",))
GC = ST.offer("gc", "p1", ("p1", "p2", "p3", "p4"), "member", "@", "self", cosigners=("p2", "p3", "p4"),
              names=("a1b", "S2", "S3", "S4"))
P1C = add("a1c", "S1", "p1c", ("p1", "p1b"), ("a1b",))                         # p1's third key
EV1B = evict("e1b", "S1", "p1b", ("p1", "p1c"), ("a1c",))                       # p1b evicted by p1's two other keys
X1B = add("x1b", "S2", "p1b", ("p2",), ("S2",))                                 # p1b seated in a second roster
BASE = [SP[1], SP[2], SP[3], SP[4], P1B, GC]


def admit_z(signers, extra=()):
    return ST.offer("az", signers[0], "z", "member", "gc", "group", ("gc",) + tuple(extra), head=("gc",),
                    policy="community_invite", cosigners=tuple(signers[1:]) + ("z",))


# (name, rows, row asked, concludes)
COUNT_CASES = [
    ("three persons sign the admission: met", BASE + [admit_z(("p1", "p2", "p3"))], "az", True),
    ("two keys of one person and one other: two voices, not met", BASE + [admit_z(("p1", "p1b", "p2"))], "az", False),
    ("a person's device key speaks for its person: met", BASE + [admit_z(("p1b", "p2", "p3"))], "az", True),
    ("an evicted device key is no voice: not met", BASE + [P1C, EV1B, admit_z(("p1b", "p2", "p3"), ("e1b",))], "az", False),
    ("a key seated in two rosters of two different genesis keys (p1's and p2's) has no person and is no voice: not met", BASE + [X1B, admit_z(("p1b", "p2", "p3"), ("x1b",))],
     "az", False),
    ("a self roster's own count stays a count of keys: two keys of S1 add a third", BASE + [P1C], "a1c", True),
]


def concludes(rows, rid):
    return bool(CK.concluded(CK.kept(list(rows)), RULE).C.get(rid))


# ---- the review r74's rows (CIRISConstitution#224, counts over persons) --------------------------------------------
AB = ST.offer("ab", "p1", "p1b", "member", "gc", "group", ("gc",), head=("gc",), policy="community_invite",
              cosigners=("p2", "p3", "p1b"))                     # p1's device also admitted to the room as a member
def admit_y(signers):
    return ST.offer("ay", signers[0], "y", "member", "gc", "group", ("ab",), head=("ab",), policy="community_invite",
                    cosigners=tuple(signers[1:]) + ("y",))
REC1 = ST.offer("rec", "p1", "p1", "registered", "p1", "self")
RV1 = ST.unseat("rv", "p1", "p1", "registered", "p1", "self", ("rec", "a1b"))
SM = found("Sm1", "m1")
AM1B = add("am1b", "Sm1", "m1b", ("m1",), ("Sm1",))
AAG = add("aAG", "Sm1", "AG", ("m1",), ("Sm1",))                   # the room's agent key, also a key of m1's roster
def admit_cr(i, signers, extra):
    return ST.offer(i, signers[0], "y", "member", "g", "group", ("ag",) + tuple(extra), head=("ag",),
                    policy="community_invite", cosigners=tuple(signers[1:]) + ("y",))
def lift_with(objectors):
    objs = [WN.answer("o_" + k, k, "x", "object", ("x", "am1b")) for k in objectors]
    return CR.PV + [SM, AM1B, CR.XL] + objs + [CR.lift("rs", "m2", "AG", "x", ("x",), tuple(o["id"] for o in objs))]
S9 = ST.offer("S9", "p2", ("p2", "p1b"), "self", "@", "self")           # p2 founds a second roster, listing p1b unsigned
GF = ST.offer("gf", "p1", ("p1", "p1b", "p2"), "member", "@", "self", cosigners=("p1b", "p2"), names=("a1b", "S2"))
XF = lambda signers: ST.unseat("xf", signers[0], "p2", "member", "gf", "group", ("gf",), head=("gf",),
                               policy="community_remove", cosigners=tuple(signers[1:]))
EG2 = ST.found("g", "A", ("A", "B", "C", "d2", "E"), {"moderate": ("A",)}, cosigners=("B", "C", "d2", "E"), names=("ad2",))
R74_CASES = [
    ("KP4: a person seated by two keys is one member: three of four persons admit y (five keys seated)",
     BASE + [AB, admit_y(("p1", "p2", "p3"))], "ay", True, RULE),
    ("KP4: and its two keys signing are one voice: p1, p1b and p2 are two of four persons, short",
     BASE + [AB, admit_y(("p1", "p1b", "p2"))], "ay", False, RULE),
    ("KP6: p1 revoked itself: its device p1b speaks for no one, so p1b, p2 and p3 are two voices of four",
     BASE + [REC1, RV1, admit_z(("p1b", "p2", "p3"), ("rv",))], "az", False, RULE),
    ("KP6: and p1's own signature is no voice though p1 is still a member", BASE + [REC1, RV1, admit_z(("p1", "p2", "p3"), ("rv",))],
     "az", False, RULE),
    ("KP5: the room's agent key, also a key of m1's roster, never speaks for m1: AG, m2, m3, m4 are three of five",
     CR.PV + [SM, AAG, admit_cr("ay", ("AG", "m2", "m3", "m4"), ("Sm1", "aAG"))], "ay", False, CR.RULE),
    ("KP5: m1 itself with m2, m3, m4 admits", CR.PV + [admit_cr("ay", ("m1", "m2", "m3", "m4"), ())], "ay", True, CR.RULE),
    ("KP1: the lift's objections: the remover's device is the remover, so m1b, m2, m3 are two of the others, short",
     lift_with(("m1b", "m2", "m3")), "rs", False, CR.RULE),
    ("KP1: m2, m3, m4 lift", lift_with(("m2", "m3", "m4")), "rs", True, CR.RULE),
]
# KP3: a window over a self roster is counted by key: p1's key of another roster withdrawing is not the opener
WS1, WA = found("S1", "p1"), add("a1b", "S1", "p1b", ("p1",), ("S1",))
WS1X, WD = found("S1x", "p1"), add("ad", "S1x", "d", ("p1",), ("S1x",))
WOP = dict(WN.opener("op", "p1", "self_roster_add", "S1", ("a1b",)), to=("k7",))
SELF_WINDOW = [WS1, WA, WS1X, WD, WOP]


# a window's answers by person: p2 has a second key p2b; p1 opens a proposal the others refuse by more than half of
# them and never fewer than two (proposal@others over p2, p3, p4)
P2B = add("a2b", "S2", "p2b", ("p2",), ("S2",))
GW = dict(GC, names=("a1b", "a2b", "S3", "S4"))
WBASE = [SP[1], SP[2], SP[3], SP[4], P1B, P2B, GW, WN.opener("op", "p1", "proposal@others", "gc", ("gc",))]
obj_ = lambda i, k: WN.answer(i, k, "op", "object", ("op",))
# (name, rows, opener, outcome)
WINDOW_CASES = [
    ("a device key's objection counts for its person: p2b and p3, two of three, refuse", WBASE + [obj_("o1", "p2b"),
                                                                                              obj_("o2", "p3")], "refused"),
    ("two keys of one person object: one voice, short of two", WBASE + [obj_("o1", "p2"), obj_("o2", "p2b")], "open"),
]
RULE_W = lambda r, P, past: WN.rule(r, P, past)
WINDOW_CASES += [
    ("KP3: over a self roster the opener's own withdrawal refuses", SELF_WINDOW + [WN.answer("w", "p1", "op", "withdraw",
                                                                                            ("op", "ad"))], "refused"),
    ("KP3: another roster's key of p1 is no opener of this one (a self roster is counted by key)",
     SELF_WINDOW + [WN.answer("w", "d", "op", "withdraw", ("op", "ad"))], "open"),
]


def window_outcome(rows):
    return WN.outcome(CK.concluded(CK.kept(list(rows)), RULE_W), "op", "recount")


# an election's ballots by person (check_election.py's five members A to E, A laying moderate down): D has a second
# key d2, admitted to D's own roster (its genesis key D)
SD = found("SD", "D")
D2 = add("ad2", "SD", "d2", ("D",), ("SD",))
EG = dict(EL.G5, names=("ad2",))
def bal(i, k, r):
    return EL.ballot(i, k, r, ("lm", "ad2"))
B5 = [bal("ba", "A", "B"), bal("bb", "B", "B"), bal("bc", "C", "C"), bal("be", "E", "C")]
BALLOT_CASES = [
    ("a device key's ballot counts for its person: d2 ranks C for D, and C is seated (three of five)",
     [SD, D2, EG, EL.LM] + B5 + [bal("bd", "d2", "C"), EL.elect("ec", "C", ("ba", "bb", "bc", "be", "bd"))], "ec", True),
    ("two keys of one person rank the same: one ballot, C seated",
     [SD, D2, EG, EL.LM] + B5 + [bal("bd", "D", "C"), bal("bd2", "d2", "C"),
                                 EL.elect("ec", "C", ("ba", "bb", "bc", "be", "bd", "bd2"))], "ec", True),
    ("two keys of one person rank differently: the person says two things and casts nothing; B and C tie, nobody",
     [SD, D2, EG, EL.LM] + B5 + [bal("bd", "D", "C"), bal("bd2", "d2", "B"),
                                 EL.elect("ec", "C", ("ba", "bb", "bc", "be", "bd", "bd2"))], "ec", False),
]
R74_CASES += [
    ("K7: two rosters founded by one genesis key p2 are one person p2: p2 is a voice, p1b, p2 and p3 admit z",
     BASE + [S9, admit_z(("p1b", "p2", "p3"), ("S9",))], "az", True, RULE),
    ("the floor of two (KP4): p1 and its device p1b, both seated, are one voice and never meet it: p2 is not removed",
     [SP[1], SP[2], P1B, GF, XF(("p1", "p1b"))], "xf", False, RULE),
    ("the electorate by person (KP4): D is seated only by its device d2, and D's own ballot counts for that member",
     [SD, D2, EG2, EL.LM] + B5 + [bal("bd", "D", "C"), EL.elect("ec", "C", ("ba", "bb", "bc", "be", "bd"))], "ec", True, RULE),
]


PLANTS = ("person_evict_unread", "person_first", "person_any_kind", "person_end_unread", "concurrent_eviction_unread",
          "persons_unread", "base_by_key", "revoked_voice_kept", "agent_speaks", "lift_author_device", "genesis_unread")


def answer(rows, k):
    return ST.person_of(CK.concluded(CK.kept(list(rows)), RULE), "at", k)


def orders(rows):
    if len(rows) <= 6:
        return [list(p) for p in itertools.permutations(rows)]
    rnd = random.Random(len(rows))
    out = [rows[::-1]]
    for _ in range(40):
        p = list(rows)
        rnd.shuffle(p)
        out.append(p)
    return out


def answer_in(order, k):
    return ST.person_of(CK.arrive(order, RULE), "at", k)


def main():
    problems, n = [], 0
    for name, rows, k, want in CASES:
        got = answer(rows, k)
        if got != want:
            problems.append("%s: got %r, expected %r" % (name, got, want))
        for o in orders(rows):
            n += 1
            if answer_in(o, k) != got:
                problems.append("%s: order %s differs" % (name, [r["id"] for r in o]))
                break
    for name, rows, rid, want in COUNT_CASES:
        got = concludes(rows, rid)
        if got != want:
            problems.append("%s: got %r, expected %r" % (name, got, want))
        for o in orders(rows)[:41]:
            n += 1
            if bool(CK.arrive(o, RULE).C.get(rid)) != got:
                problems.append("%s: order %s differs" % (name, [r["id"] for r in o]))
                break
    for name, rows, rid, want, rule in R74_CASES:
        got = bool(CK.concluded(CK.kept(list(rows)), rule).C.get(rid))
        if got != want:
            problems.append("%s: got %r, expected %r" % (name, got, want))
    for name, rows, want in WINDOW_CASES:
        got = window_outcome(rows)
        if got != want:
            problems.append("%s: got %r, expected %r" % (name, got, want))
    for name, rows, rid, want in BALLOT_CASES:
        got = concludes(rows, rid)
        if got != want:
            problems.append("%s: got %r, expected %r" % (name, got, want))
    caught = 0
    for plant in PLANTS:
        ST.MUT.add(plant)
        try:
            hit = [c[0] for c in CASES if answer(c[1], c[2]) != c[3]] + \
                  [c[0] for c in COUNT_CASES if concludes(c[1], c[2]) != c[3]] + \
                  [c[0] for c in WINDOW_CASES if window_outcome(c[1]) != c[2]] + \
                  [c[0] for c in BALLOT_CASES if concludes(c[1], c[2]) != c[3]] + \
                  [c[0] for c in R74_CASES if bool(CK.concluded(CK.kept(list(c[1])), c[4]).C.get(c[2])) != c[3]]
        finally:
            ST.MUT.discard(plant)
        caught += bool(hit)
        print("  plant %-20s %s" % (plant, "caught by %d cases, first: %s" % (len(hit), hit[0]) if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % plant)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases (%d of a key's person, %d of a count over persons, %d of a window's answers, %d of "
          "ballots, %d of the review r74), %d arrival orders, %d of %d planted breaks caught"
          % ("ok" if not problems else "%d problems" % len(problems),
             len(CASES) + len(COUNT_CASES) + len(WINDOW_CASES) + len(BALLOT_CASES) + len(R74_CASES), len(CASES),
             len(COUNT_CASES), len(WINDOW_CASES), len(BALLOT_CASES), len(R74_CASES), n, caught, len(PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
