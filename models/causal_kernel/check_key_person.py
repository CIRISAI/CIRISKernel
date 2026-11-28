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
    fold_lift_by_key      the fold's lift reads its objections by key over the persons: a device's objection lost (KP-A)
    fold_author_by_key    the fold's lift takes the author out by key before the person map: the author's member
                          device brings the author back into the base (KP-B)
    remover_counted_over  the count's receipt keeps the remover's person in its base (KP-C)
    opener_withdrawal_voter  the opener's own withdrawal needs a person: a revoked opener withdraws nothing (r78k)
    apart_by_key          a named key set apart by key only: a device-held duty's person votes on its recall (r78k)
    person_keys_by_offer  a person's keys read as every key ever offered to its rosters: an evicted device kept
    nodes_by_offer        an owner's nodes read from the offers, not the owner seat: an unsigned or ended binding binds
    nodes_two_owners_kept a node bound to two live owners read as each one's
    nodes_revocation_unread  the node key's (or the owner's) own revocation not read
    evicted_genesis_speaks  a genesis key its own roster evicted still speaks as its person (r95 P1b)
    evicted_key_votes     the key a self roster evicts is a voice of its own eviction (the one-key residual evicts)
    rival_roster_kept     a second self roster of one identity is kept (r96 G1: re-founding, a device by founding)
    rebinding_unread      Seats.owner reads no re-binding: a re-bound node has two owners, none (consent-set's plant)
    landed_eviction_unread  a self roster's landed lone-path eviction ends nothing (the window an outcome only)
    landed_add_unread     a self roster's landed lone-path addition seats nothing
    self_founding_family  a family's founding read as a self roster's (a rival of the person's roster)
    mutual_evictions_land two concurrent lone evictions of each other both land (r99 M1: the roster emptied)
    rival_line_unread     no reader's line is read: a reader on the first roster waits with a fresh one (the rival stalls)
    line_order_unread     the line read out of order: a later row over the rival takes it up too, and the reader waits (P1)
    line_key_end_unread   the line reads no key end: a thief's row with the reader's revoked key seeds it (K1)
    person_key_lane_unread  the person map reads no key-lane revocation (key_end.MUT; r106 PG1)
    registered_by_past    with no key view, only a row with the reader's registered self-unseat in its past is cut
    claimed_cosigner_counted  another signer's claimed cosigners on a note seed the reader's line (r101 R2)
    seat_voice_counted    a concluded seat row listing the reader as a cosigner seeds its line (review-48 R2s)
    agent_by_seat_only    an agent recognised by its agent seat only: a registered agent admitted as a member speaks
Every count reads one function, seat.count_persons: the base and the voices by person, a named key (the lift's author,
the receipt's remover, the recall's holder) set apart by person from both (the review r78k).

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
import key_end as KE  # noqa: E402
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
REC2 = ST.offer("rec2", "k1", "k1", "registered", "k1", "self", ("rec",))        # k1's second key record
SX = found("SX", "k1")                                                            # a second roster k1 founds
AX = add("ax", "SX", "kx", ("k1",), ("SX",))
AX2 = add("ax2", "SX", "k2", ("k1",), ("SX",))                                   # k2 seated in k1's second roster too
CASES = [
    ("the first key of a self roster, at a row naming the roster", [S, at(("S",))], "k1", "k1"),
    ("a key added by the roster's count, at a row naming the addition", [S, A2, at(("a2",))], "k2", "k1"),
    ("the same key at a row that does not have the addition in its past: no person yet", [S, A2, at(("S",))], "k2", None),
    ("a third key added by two, at a row naming its addition", [S, A2, A3, at(("a3",))], "k3", "k1"),
    ("the third key evicted by the roster's count, at a row naming the eviction: no person", [S, A2, A3, E3, at(("e3",))],
     "k3", None),
    ("the other keys keep their person after the eviction", [S, A2, A3, E3, at(("e3",))], "k2", "k1"),
    ("the evicted key at the eviction's own head, the eviction concurrent with the row: out (rule 4)",
     [S, A2, A3, E3, at(("a3",))], "k3", None),
    ("the evicted key at that head with no eviction held: its person then", [S, A2, A3, at(("a3",))], "k3", "k1"),
    ("a key seated in two self rosters: two persons is none", [S, A2, T, T2, at(("a2", "b2"))], "k2", None),
    ("the same key with only one of the two in the row's past", [S, A2, T, T2, at(("a2",))], "k2", "k1"),
    ("the key's own revocation in the row's past ends its person (the liveness half)", [S, REC, RV, at(("rv",))], "k1", None),
    ("the key's revocation not in the row's past", [S, REC, RV, at(("S",))], "k1", "k1"),
    ("a room key of a voice: the voice is its person", VA + [at((HA,))], "rk:a1", "rk:a0"),
    ("a member seat of a community is no person", [G, at(("g",))], "m1", None),
    ("a key no roster seats", [S, at(("S",))], "zz", None),
    # rule 4: an eviction concurrent with the row counts at its own head and is out of force from that head on
    ("an eviction concurrent with the row, the row at the eviction's head: the key is out from that head on",
     [S, A2, A3, E2, at(("a3",))], "k2", None),
    ("the same eviction, the row at an earlier head: the key's person then", [S, A2, A3, E2, at(("a2",))], "k2", "k1"),
    ("the other keys at the eviction's head keep their person", [S, A2, A3, E2, at(("a3",))], "k3", "k1"),
    # G5: a self roster's object is the identity key, not one key record: a genesis key with two key records and two
    # rosters is one person, whichever roster seats the key
    ("G5: a genesis key with two key records and two rosters: a key of the second roster is the same one person",
     [S, REC, REC2, SX, AX, at(("ax", "rec2"))], "kx", "k1"),
    ("G1 (the reader's line): a fresh reader holding both of k1's rosters, its line taking up neither, waits: a key of "
     "either is no person", [S, A2, REC, REC2, SX, AX, at(("a2", "ax", "rec2"))], "k2", None),
    ("G1: and a key in both of them", [S, A2, REC, REC2, SX, AX2, at(("a2", "ax2", "rec2"))], "k2", None),
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
# the recall's holder apart by person (r78k: one reading of every count): A's device a2 holds moderate; A, B and C
# recall it; A is the holder, no voice of its own recall, so B and C are two of the three others: no recall
SA, AA2 = found("SA", "A"), add("aa2", "SA", "a2", ("A",), ("SA",))
FHD = ST.found("g", "A", ("A", "B", "C", "D", "a2"), {"moderate": ("a2",)}, cosigners=("B", "C", "D", "a2"), names=("aa2",))
def recall_a2(signers):
    return ST.unseat("r", signers[0], "a2", "moderate", "g", "group", ("g",), head=("g",), policy="moderator_recall",
                     cosigners=tuple(signers[1:]))
COUNT_CASES = [
    ("three persons sign the admission: met", BASE + [admit_z(("p1", "p2", "p3"))], "az", True),
    ("two keys of one person and one other: two voices, not met", BASE + [admit_z(("p1", "p1b", "p2"))], "az", False),
    ("a person's device key speaks for its person: met", BASE + [admit_z(("p1b", "p2", "p3"))], "az", True),
    ("an evicted device key is no voice: not met", BASE + [P1C, EV1B, admit_z(("p1b", "p2", "p3"), ("e1b",))], "az", False),
    ("a key seated in two rosters of two different genesis keys (p1's and p2's) has no person and is no voice: not met", BASE + [X1B, admit_z(("p1b", "p2", "p3"), ("x1b",))],
     "az", False),
    ("a self roster's own count stays a count of keys: two keys of S1 add a third", BASE + [P1C], "a1c", True),
    ("the recall's holder apart by person: A's device a2 holds moderate, and A, B and C recall it; A is no voice, two "
     "of three others", [SA, AA2, FHD, recall_a2(("A", "B", "C"))], "r", False),
    ("and B, C and D recall it: three of three others", [SA, AA2, FHD, recall_a2(("B", "C", "D"))], "r", True),
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
    ("K7, a fresh reader (its line takes up no roster): it waits, z not admitted",
     BASE + [S9, admit_z(("p1b", "p2", "p3"), ("S9",))], "az", False, RULE),
    ("the floor of two (KP4): p1 and its device p1b, both seated, are one voice and never meet it: p2 is not removed",
     [SP[1], SP[2], P1B, GF, XF(("p1", "p1b"))], "xf", False, RULE),
    ("the electorate by person (KP4): D is seated only by its device d2, and D's own ballot counts for that member",
     [SD, D2, EG2, EL.LM] + B5 + [bal("bd", "D", "C"), EL.elect("ec", "C", ("ba", "bb", "bc", "be", "bd"))], "ec", True, RULE),
]


# the review r78k: one reading of a count by person (seat.count_persons) at every count. The world: six founding
# members m1 to m4 (moderators), q and q2; m1's device m1b admitted as a member too; m2's device m2b no member; the
# agent's key AG; m1's lone removal x of AG; the members' lift rs on objections. A counted admission az concurrent
# with rs makes two tips over g, so the roster is the fold's (Seats.tips_fold), and the fold reads the lift.
import check_room_keys as CRK
import check_removal_in_force as CRF
G6 = ST.found("g", "m1", ("m1", "m2", "m3", "m4", "q", "q2"), {"moderate": ("m1", "m2", "m3", "m4")},
              cosigners=("m2", "m3", "m4", "q", "q2"))
SM1, SM2 = found("Sm1", "m1"), found("Sm2", "m2")
AM2B = add("am2b", "Sm2", "m2b", ("m2",), ("Sm2",))
LW = [G6, SM1, AM1B, SM2, AM2B, dict(CRK.admit("ab", "m1b", ("m1", "m2", "m3", "m4"), ("g",)), names=("g", "am1b")),
      CRK.admit("ag", "AG", ("m1", "m2", "m3", "m4"), ("ab",), "agent"), CRK.lone("x", "m1", "AG", ("ag",))]
AZ = CRK.admit("az", "z", ("m1", "m2", "m3", "m4"), ("x",))
def lifted(objectors, tip=True):
    os_ = [WN.answer("o_" + k, k, "x", "object", ("x", "am2b")) for k in objectors]
    return LW + os_ + [CRK.lift("rs", "m2", "AG", "x", ("x",), tuple(o["id"] for o in os_))] + ([AZ] if tip else [])
# the count's receipt (CRF's R5): four persons p1 to p4, p1 the one moderator; p1's device p1b admitted as a member;
# p1 removes AG alone and lays moderate down, so the removal stays in force only by the count's receipt
G4 = ST.found("g", "p1", ("p1", "p2", "p3", "p4"), {"moderate": ("p1",)}, cosigners=("p2", "p3", "p4"))
R5D = [G4, SP[1], P1B, dict(CRF.admit("ab", "p1b", ("p1", "p2", "p3"), ("g",)), names=("g", "a1b")),
       CRF.admit("ag", "AG", ("p1", "p2", "p3", "p4"), ("ab",), "agent"), CRF.lone("x", "p1", "AG", ("ag",))]
def receipted(signers):
    return R5D + [CRF.counted_receipt("qc", signers, "x", ("x",)), ST.withdraw("wm", "p1", "g", ("x",), scope="moderate")]
# (name, rows, whether AG holds its agent seat over g)
R78K_CASES = [
    ("KP-A: the fold's lift maps its objections first: m2's device m2b objects for m2; three of the five others, AG re-seated",
     lifted(("m2b", "m3", "m4")), True),
    ("KP-B: the fold's lift takes the author out by person: m1's device m1b, a member, is m1; three of five, AG re-seated",
     lifted(("m2", "m3", "m4")), True),
    ("the seat rule's lift, one tip: the same three of five", lifted(("m2", "m3", "m4"), False), True),
    ("the author's device is the author: m1b's objection is no voice; two of five, AG stays removed",
     lifted(("m1b", "m3", "m4")), False),
    ("KP-C: the count's receipt takes the remover out by person: p1b, a member, is p1; p2 and p3 are two of three, "
     "the removal stands", receipted(("p2", "p3")), False),
    ("KP-C: the remover's device is no voice of the receipt: p1b and p2 are one of three, AG back",
     receipted(("p1b", "p2")), True),
]


def ag_held(rows):
    return "AG" in ST.Seats(CK.concluded(CK.kept(list(rows)), RULE_W)).holders("agent", "g")


# the opener's own withdrawal (r78k, latent: no window of the table reads it over persons): a table that reads the
# opener's withdrawal over a member count, with its own entry. A key of no person (one that revoked itself) that
# opened the window withdraws it as itself, with no voter needed.
LATENT = "kp:opener_withdraws"
LATENT_SPEC = {"policy": "moderation_action", "counted": "member", "concluder": "member", "opener_says": None,
               "at_once": (("withdraw", "one", "opener", "refused"), ("object", ("more", 1, 2, 2), "others", "refused")),
               "silent": None, "at_close": (), "default": "landed"}
LWB = [r for r in WBASE if r["id"] != "op"] + [WN.opener("op", "p1", LATENT, "gc", ("gc",))]
LREC = ST.offer("rec", "p1", "p1", "registered", "p1", "self", ("op",))
LRV = ST.unseat("rv", "p1", "p1", "registered", "p1", "self", ("rec",))
LATENT_CASES = [
    ("the opener withdraws its own proposal: refused", LWB + [WN.answer("w", "p1", "op", "withdraw", ("op",))], "refused"),
    ("the opener revoked its key, a key of no person, and withdraws: still the opener's own, refused",
     LWB + [LREC, LRV, WN.answer("w", "p1", "op", "withdraw", ("op", "rv"))], "refused"),
    ("another member's withdrawal is none", LWB + [WN.answer("w", "p2", "op", "withdraw", ("op",))], "open"),
]


def latent_outcome(rows):
    WN.WINDOWS[LATENT] = LATENT_SPEC
    try:
        return window_outcome(rows)
    finally:
        WN.WINDOWS.pop(LATENT, None)


# the keys a row reaches, for persist (the node set = audiences o person_keys o nodes_of), over the concluded set
# with no instant. person_keys: a person's live keys, the inverse of persons_of. nodes_of: the node keys an owner
# owns, the inverse of a node's owner-binding.
A1D = add("a1d", "S1", "p1d", ("p1", "p1b"), ("a1c",))
E1D = evict("e1d", "S1", "p1d", ("p1", "p1b", "p1c"), ("a1d",))          # p1d evicted by the roster's count
PKW = [SP[1], P1B, P1C, A1D, E1D]
PREC = ST.offer("prec", "p1", "p1", "registered", "p1", "self")
PRV = ST.unseat("prv", "p1", "p1", "registered", "p1", "self", ("prec", "e1d"))   # p1's genesis key revokes itself
BREC = ST.offer("brec", "p1b", "p1b", "registered", "p1b", "self")
BRV = ST.unseat("brv", "p1b", "p1b", "registered", "p1b", "self", ("brec", "e1d"))  # the device p1b revokes itself
# (name, rows, person, its live keys)
PERSON_KEYS_CASES = [
    ("a person with two live devices and one evicted: its genesis key and the two", PKW, "p1", ["p1", "p1b", "p1c"]),
    ("a device also in another person's roster is a key of two persons: none of p1's", PKW + [SP[2], X1B], "p1",
     ["p1", "p1c"]),
    ("and none of p2's", PKW + [SP[2], X1B], "p2", ["p2"]),
    ("a device that revoked itself is no live key", PKW + [BREC, BRV], "p1", ["p1", "p1c"]),
    ("a person whose genesis key revoked itself has no live key", PKW + [PREC, PRV], "p1", []),
    ("a key of no roster is its own person", PKW, "zz", ["zz"]),
    ("G5: a genesis key with two key records and one roster: one person, its keys", [S, A2, REC, REC2], "k1",
     ["k1", "k2"]),
    ("G1: a fresh reader holding both rosters waits: no live key", [S, A2, REC, REC2, SX, AX], "k1", []),
]
def bind(i, node, owner):
    """An owner-binding: the node's offer of the owner seat over its key, the owner's cosignature its consent."""
    return ST.offer(i, node, owner, "owner", node, "self", (), cosigners=(owner,))
NB1, NB2 = bind("nb1", "n1", "o1"), bind("nb2", "n2", "o1")
NUO = ST.unseat("nuo", "o1", "o1", "owner", "n2", "seat", ("nb2",), under="nb2")     # o1 revokes n2's binding
NBU = ST.offer("nbu", "n3", "o1", "owner", "n3", "self")                             # n3's offer o1 never signed
NB4A, NB4B = bind("nb4a", "n4", "o1"), bind("nb4b", "n4", "o2")                       # n4 bound to two owners
NWB = ST.withdraw("nwb", "o1", "nb1", ("nb1",))                                       # o1 withdraws n1's binding
NREC = ST.offer("nrec", "n1", "n1", "registered", "n1", "self")
NRV = ST.unseat("nrv", "n1", "n1", "registered", "n1", "self", ("nrec", "nb1"))       # the node n1 revokes itself
NOA = ST.offer("noa", "n5", "o1", "owner", "n5", "self")
NAC = ST.accept("nac", "o1", "noa")                                                   # o1 accepts n5's offer
NRB = ST.offer("nrb", "n1", "o2", "owner", "n1", "self", ("nb1",), cosigners=("o2",))      # n1 re-bound to o2
NRBU = ST.offer("nrbu", "n1", "o2", "owner", "n1", "self", ("nb1",))                       # o2 has not accepted
# (name, rows, owner, its nodes)
NODES_CASES = [
    ("an owner with two bound nodes", [NB1, NB2], "o1", ["n1", "n2"]),
    ("an owner with two bound nodes, one whose binding the owner revoked", [NB1, NB2, NUO], "o1", ["n1"]),
    ("a binding the owner withdrew binds nothing", [NB1, NB2, NWB], "o1", ["n2"]),
    ("a node's offer the owner never signed binds nothing", [NB1, NBU], "o1", ["n1"]),
    ("the owner's own acceptance binds", [NOA, NAC], "o1", ["n5"]),
    ("a node bound to two live owners is neither's", [NB1, NB4A, NB4B], "o1", ["n1"]),
    ("and not the other's", [NB1, NB4A, NB4B], "o2", []),
    ("a node key that revoked itself is no node of its owner", [NB1, NB2, NREC, NRV], "o1", ["n2"]),
    # the one owner reading (Seats.owner): a re-binding ends the binding before it, a stint and not a rival
    ("a re-binding of n1 to o2 (its offer has o1's in its past): n1 is o2's", [NB1, NB2, NRB], "o2", ["n1"]),
    ("and no longer o1's", [NB1, NB2, NRB], "o1", ["n2"]),
    ("an unaccepted re-binding ends o1's binding: n1 is nobody's yet", [NB1, NB2, NRBU], "o1", ["n2"]),
]


def concluded_set(rows):
    return CK.concluded(CK.kept(list(rows)), RULE)

# the review r95 (G33: an eviction ends a key AS THE PERSON'S): p1's devices p1b and p1c evict its genesis key p1
# from S1. The person is its identity p1, which the room still seats; only a live key of S1 speaks for it, so the
# evicted p1 is no voice of it (and its own rows are a bare key's), while a live device still is
EVG = evict("evg", "S1", "p1", ("p1b", "p1c"), ("a1c",))
GREC = ST.offer("grec", "p1", "p1", "registered", "p1", "self", ("evg",))     # the evicted p1's own key record
R74_CASES += [
    ("r95 P1b: p1's genesis key evicted from its own roster by its devices: the evicted p1, p2 and p3 are two voices "
     "of four, z is not admitted", BASE + [P1C, EVG, admit_z(("p1", "p2", "p3"), ("evg",))], "az", False, RULE),
    ("r95 P1c (control): an evicted device p1b, p2 and p3 are two voices of four",
     BASE + [P1C, EV1B, admit_z(("p1b", "p2", "p3"), ("e1b",))], "az", False, RULE),
    ("r95: after the genesis key's eviction a live device p1b still votes as the person p1: three of four",
     BASE + [P1C, EVG, admit_z(("p1b", "p2", "p3"), ("evg",))], "az", True, RULE),
    ("r95: the evicted genesis key's own self-signed key record concludes, as a bare key's",
     BASE + [P1C, EVG, GREC], "grec", True, RULE),
    # confirmed by the Constitution: no exemption for the first key; the identity outlives its genesis key
    ("the genesis key is no voice of the count that evicts it: p1 and p1b are one voice of three keys",
     [SP[1], P1B, P1C, evict("evg", "S1", "p1", ("p1", "p1b"), ("a1c",))], "evg", False, RULE),
    ("and p1b and p1c, two of three, evict it", [SP[1], P1B, P1C, evict("evg", "S1", "p1", ("p1b", "p1c"), ("a1c",))],
     "evg", True, RULE),
    ("the one-key residual: a roster whose only live key is the genesis key cannot evict it",
     [SP[1], evict("evg", "S1", "p1", ("p1",), ("S1",))], "evg", False, RULE),
]
CASES += [
    ("r95: the genesis key its devices evicted, at a row naming the eviction: no person (a bare key)",
     [S, A2, A3, ST.unseat("eg1", "k2", "k1", "self", "S", "group", ("a3",), head=("a3",), policy="self_roster_evict",
                           counted="self", cosigners=("k3",)), at(("eg1",))], "k1", None),
]

# the review r96 (G1, ruled): ONE SELF ROSTER PER IDENTITY. p1's devices p1b and p1c evict p1 from S1; a second
# founding by p1 is a rival and concludes nothing, so p1 neither re-founds itself nor adds a device that way; only S1's
# own counted re-admission restores it. Two foundings neither in the other's past: a reader holding both waits.
GA1C = add("a1c", "S1", "p1c", ("p1", "p1b"), ("a1b",))
GW = [SP[1], SP[2], SP[3], SP[4], P1B, dict(GC, names=("a1b", "S2", "S3", "S4")), GA1C]
GEV = evict("evg", "S1", "p1", ("p1b", "p1c"), ("a1c",))
S1N = dict(found("S1n", "p1"), names=("evg",))                  # p1 founds again after its eviction
GAN = add("an", "S1n", "p1n", ("p1",), ("S1n",))                  # and adds a device to it alone
S1P = dict(found("S1n", "p1"), names=("a1c",))                  # p1 founds a second roster before its eviction
S1C = found("S1n", "p1")                                          # a second founding concurrent with S1's line
GRE = add("re", "S1", "p1", ("p1b", "p1c"), ("evg",))            # S1's own count re-admits p1
GS = found("S", "g1")
GD1 = add("d1", "S", "k1", ("g1",), ("S",))                       # a two-key roster: g1 and its device k1
R74_CASES += [
    ("r96 E2: after its eviction p1 founds a second roster S1n: a rival founding, it concludes nothing",
     GW + [GEV, S1N], "S1n", False, RULE),
    ("r96 E2: and p1, p2 and p3 are two voices of four: z is not admitted",
     GW + [GEV, S1N, admit_z(("p1", "p2", "p3"), ("evg", "S1n"))], "az", False, RULE),
    ("r96 E3: a device p1 adds to the rival roster is seated nowhere", GW + [GEV, S1N, GAN], "an", False, RULE),
    ("r96 E3: and p1n, p2 and p3 are two voices of four", GW + [GEV, S1N, GAN, admit_z(("p1n", "p2", "p3"), ("an",))],
     "az", False, RULE),
    ("r96: the pre-emptive device add: p1 founds S1n before its eviction (S1 in its past): refused, and its device too",
     GW + [S1P, GAN, GEV], "an", False, RULE),
    ("r96: a second founding concurrent with S1: a reader holding both waits, so the device p1n speaks for no one",
     GW + [S1C, GAN, admit_z(("p1n", "p2", "p3"), ("an", "a1c"))], "az", False, RULE),
    ("r96: and p1 itself, of two rival rosters, waits too", GW + [S1C, GAN, admit_z(("p1", "p2", "p3"), ("an", "a1c"))],
     "az", False, RULE),
    ("r96 E4: the roster's own counted re-admission restores p1: p1, p2 and p3 admit z",
     GW + [GEV, GRE, admit_z(("p1", "p2", "p3"), ("re",))], "az", True, RULE),
    # a two-key roster by the COUNT: the key evicted is no voice, so neither key evicts the other this way (the lone
    # path, below, does where the other key is silent)
    ("r96 V1: a two-key roster: the device k1 alone cannot evict the genesis key g1",
     [GS, GD1, evict("v", "S", "g1", ("k1",), ("d1",))], "v", False, RULE),
    ("r96 V2: nor g1 alone a stolen device k1", [GS, GD1, evict("v", "S", "k1", ("g1",), ("d1",))], "v", False, RULE),
]
PERSON_KEYS_CASES += [
    ("r96: after p1's eviction and its rival founding, p1's live keys are its two devices", GW + [GEV, S1N], "p1",
     ["p1b", "p1c"]),
]
# the review r99 (D1): rivals are judged in the judged row's own past. A founding names nothing, so a stolen genesis
# key's bare founding S1r is concurrent with S1; the row's past takes up S1 (rows name it or are counted over it) and
# not S1r, so S1 stays the person's roster and the honest devices still speak. A row whose past takes up both waits.
RIV = found("S1r", "p1")
RIVH = ST.cosign("hh", "p1b", "hh", ("S1", "S1r"))                     # a row naming both foundings
R74_CASES += [
    ("r99 D1: the evicted p1's bare founding S1r concludes (nothing in its past)", GW + [GEV, RIV], "S1r", True, RULE),
    ("r99 D2, a fresh reader (its line takes up no roster): it waits, z not admitted", GW + [GEV, RIV,
     admit_z(("p1b", "p2", "p3"), ("evg", "S1r"))], "az", False, RULE),
    ("r99 D4, a fresh reader (its line takes up no roster): it waits, z not admitted", GW + [GEV, RIV, RIVH, admit_z(("p1b", "p2", "p3"), ("evg", "hh"))], "az",
     False, RULE),
    ("r99 D5: the devices are no keys of the rival roster, so their eviction of p1 from it does not conclude",
     GW + [GEV, RIV, evict("evr", "S1r", "p1", ("p1b", "p1c"), ("S1r",))], "evr", False, RULE),
    ("r99 D6, a fresh reader (its line takes up no roster): it waits, z not admitted",
     GW + [RIV, admit_z(("p1b", "p2", "p3"), ("a1c", "S1r"))], "az", False, RULE),
    ("r99 D7, fresh reader: it waits, so p1, p2 and p3 are two of four", GW + [RIV, admit_z(("p1", "p2", "p3"), ("a1c", "S1r"))], "az", False, RULE),
]
R74_CASES += [
    ("r99 drift: a family founding by p1 (scope self, group_kind family) after S1 is no self roster, so no rival: it "
     "concludes", GW + [dict(found("F1", "p1"), names=("a1c",), group_kind="family")], "F1", True, RULE),
]
# the review r99 part 2 (D8 to D10): TAKEN UP means COUNTED by a live voice of the identity, so one thief row naming
# its rival stalls nothing; a thief's counted row on the rival takes it up only while the thief is a live voice
RT = ST.cosign("t", "p1", "t", ("S1r",))                                 # the thief names only its rival
RT2 = ST.cosign("t2", "p1", "t2", ("S1r", "a1c"))                       # names its rival and the honest roster's head
RTA = add("ta", "S1r", "p1x", ("p1",), ("S1r",))
RIVD = ST.offer("S1d", "p1", ("p1", "p1x"), "self", "@", "self", cosigners=("p1x",))   # a rival seating p1x                         # the thief's counted addition on its rival
R74_CASES += [
    ("r99 D8, a fresh reader (its line takes up no roster): it waits, z not admitted",
     GW + [GEV, RIV, RT, admit_z(("p1b", "p2", "p3"), ("evg", "t"))], "az", False, RULE),
    ("r99 D9, a fresh reader (its line takes up no roster): it waits, z not admitted", GW + [GEV, RIV, RT2, admit_z(("p1b", "p2", "p3"), ("evg", "t2"))], "az",
     False, RULE),
    ("r99 D10, a fresh reader (its line takes up no roster): it waits, z not admitted",
     GW + [RIV, RT2, admit_z(("p1b", "p2", "p3"), ("a1c", "t2"))], "az", False, RULE),
    ("r99c T1, a fresh reader (its line takes up no roster): it waits, z not admitted", GW + [RIV, RTA, admit_z(("p1b", "p2", "p3"), ("a1c", "ta"))], "az", False, RULE),
    ("r99c T1, fresh reader: the thief's device p1x speaks for no one", GW + [RIV, RTA, admit_z(("p1x", "p2", "p3"), ("a1c", "ta"))],
     "az", False, RULE),
    ("r100 X-like: a rival founding cosigned by a thief's own device: a fresh reader waits",
     GW + [RIVD, admit_z(("p1b", "p2", "p3"), ("a1c", "S1d"))], "az", False, RULE),
    ("r99 Y3-like, a fresh reader (its line takes up no roster): it waits, z not admitted",
     GW + [GEV, RIV, RTA, admit_z(("p1b", "p2", "p3"), ("evg", "ta"))], "az", False, RULE),
]
# the review r99c (T3, T4): a two-key person g1 (stolen) and k1. The thief founds Sr and adds its own device by its
# count. A fresh reader holding both waits; a reader whose line took up S reads S (LINE_CASES): the two-key stalemate
# stands, with no muting.
TGR = ST.offer("gr", "g1", ("g1", "m2", "m3", "m4"), "member", "@", "self", cosigners=("m2", "m3", "m4"), names=("d1",))
TRV = found("Sr", "g1")
TTX = add("tx2", "Sr", "x9", ("g1",), ("Sr",))
def tadm(signers, names):
    return ST.offer("az", signers[0], "z", "member", "gr", "group", ("gr",) + tuple(names), head=("gr",),
                    policy="community_invite", cosigners=tuple(signers[1:]) + ("z",))
TB = [GS, GD1, TGR, TRV, TTX]
R74_CASES += [
    ("r99c T3, a fresh reader (its line takes up no roster): it waits, z not admitted",
     TB + [tadm(("k1", "m2", "m3"), ("tx2",))], "az", False, RULE),
    ("r99c T3, fresh reader: it waits, so the thief's device x9 is no voice",
     TB + [tadm(("x9", "m2", "m3"), ("tx2",))], "az", False, RULE),
    ("r99c T3, fresh reader: x9 naming its own rival changes nothing: x9 is no voice", TB + [R("xn", "note", "x9", ("tx2",)), tadm(("x9", "m2", "m3"), ("xn",))], "az", False, RULE),
    ("r99c T3, fresh reader: g1 waits with its identity: g1, m2 and m3 are two of four",
     TB + [tadm(("g1", "m2", "m3"), ("tx2",))], "az", False, RULE),
    ("r99c: an honest single founding is unaffected: g1, m2 and m3 admit z", [GS, GD1, TGR, tadm(("g1", "m2", "m3"), ("d1",))],
     "az", True, RULE),
    ("the residual: a fresh reader holding only the rival (S not held) holds one founding, and reads it: g1, m2, m3 "
     "admit z",
     [TRV, TTX, ST.offer("gr", "g1", ("g1", "m2", "m3", "m4"), "member", "@", "self", cosigners=("m2", "m3", "m4"),
                         names=("tx2",)), tadm(("g1", "m2", "m3"), ("tx2",))], "az", True, RULE),
]
WINDOW_CASES += [
    ("r99c T4: k1 lone-evicts g1 and the thief objects: refused (the target-silence clause), but no eviction is needed",
     TB + [WN.opener("op", "k1", "self_roster_evict", "S", ("d1",), target="g1"), WN.answer("og", "g1", "op", "object", ("op",)),
           WN.receipt("r", "k1", "op", 0), WN.landing("L", "k1", "op", "r", "landed", WN.secs("self_roster_evict"), ("og",))],
     "refused"),
]
PERSON_KEYS_CASES += [
    ("r99 D3, the reader's line: a fresh reader holding the rival waits: no live key", GW + [GEV, RIV], "p1", []),
]
# the lone path in a two-key roster (CC 4.5.13; Eric's correction): one key proposes the other's eviction, and after
# the window it LANDS unless the other key, the whole of "the other members" and a voice here, objects within it.
# That covers a lost or dead device; an active stolen key that objects blocks its own eviction, and two live keys
# proposing against each other, each objecting, stalemate.
EW = WN.secs("self_roster_evict")
def lone_evict(opener, target, objects, pid="op", tag=""):
    rows = [WN.opener(pid, opener, "self_roster_evict", "S", ("d1",), target=target)]
    if objects:
        rows.append(WN.answer("ob" + tag, target, pid, "object", (pid,)))
    rows += [WN.receipt("r" + tag, opener, pid, 0),
             WN.landing("L" + tag, opener, pid, "r" + tag, "landed", EW, ("ob" + tag,) if objects else ())]
    return rows
WINDOW_CASES += [
    ("two keys: k1 proposes evicting g1, and g1 is silent through the window: the eviction lands",
     [GS, GD1] + lone_evict("k1", "g1", False), "landed"),
    ("two keys: the same with g1 objecting within the window: refused", [GS, GD1] + lone_evict("k1", "g1", True),
     "refused"),
    ("two keys proposing against each other, each objecting: neither lands (k1's proposal)",
     [GS, GD1] + lone_evict("k1", "g1", True) + lone_evict("g1", "k1", True, "op2", "2"), "refused"),
    ("and g1's proposal", [GS, GD1] + lone_evict("g1", "k1", True) + lone_evict("k1", "g1", True, "op2", "2"), "refused"),
]

# a landed lone-path eviction TAKES EFFECT (one ends reading): after k1's proposal lands with g1 silent, g1 is out of
# the roster, no voice of the person, no live key of it, and its later rows read as a bare key's; k1 alone is the
# person
LANDED = [GS, GD1] + lone_evict("k1", "g1", False)
LNOTE = R("ln", "note", "g1", ("L",))                                     # g1's own row after the landing
LNOTE_K = R("lk", "note", "k1", ("L",))
AW = WN.secs("self_roster_add")
AOP = dict(WN.opener("opa", "k1", "self_roster_add", "S", ("d1",)), to=("k2",), cosigners=("k2",))   # k2 signs it
AOP_NC = dict(WN.opener("opa", "k1", "self_roster_add", "S", ("d1",)), to=("k2",))                   # k2 does not
ADDED = [GS, GD1, AOP, WN.receipt("ra", "k1", "opa", 0), WN.landing("La", "k1", "opa", "ra", "landed", AW)]
ADDED_T = [GS, GD1, dict(WN.opener("opa", "k1", "self_roster_add", "S", ("d1",), target="k2"), cosigners=("k2",)),
           WN.receipt("ra", "k1", "opa", 0), WN.landing("La", "k1", "opa", "ra", "landed", AW)]
ADDED_NC = [GS, GD1, AOP_NC, WN.receipt("ra", "k1", "opa", 0), WN.landing("La", "k1", "opa", "ra", "landed", AW)]
def R3ADD(objectors):
    rows = [dict(WN.opener("op", "p1", "self_roster_add", "S1", ("a1c",), target="k9"), to=("k9",), cosigners=("k9",))]
    rows += [WN.answer("o" + o, o, "op", "object", ("op",)) for o in objectors]
    return rows + [WN.receipt("r", "p1", "op", 0),
                   WN.landing("L", "p1", "op", "r", "landed", AW, tuple("o" + o for o in objectors))]


def landed_state(rows):
    return CK.concluded(CK.kept(list(rows)), RULE_W)
# (name, rows, what is read, want)
LANDED_CASES = [
    # r106 PG1: the person map reads a key's own revocation in EITHER lane (key_end.revocations over key_end.key_ends)
    ("r106 PG1: the genesis key revoked in the key lane: its device speaks for no one",
     [S, A2, CK.row("rvk", "revoke", "k1", ("S",), key="k1", ra=5)], lambda S_: ST.rep_of(list(S_.Cs), "k2"), None),
    ("and with no revocation the device speaks for its person", [S, A2], lambda S_: ST.rep_of(list(S_.Cs), "k2"), "k1"),
    ("the landed eviction ends g1's seat: the roster's live keys", LANDED,
     lambda S: sorted(ST.Seats(S).holders("self", "S")), ["k1"]),
    ("the evicted g1 is no voice of the person", LANDED, lambda S: ST.rep_of(list(S.Cs), "g1"), None),
    ("person_keys excludes it: k1 alone is the person's", LANDED, lambda S: sorted(ST.person_keys(S, "g1")), ["k1"]),
    ("g1's own later row reads as a bare key's: no person", LANDED + [LNOTE], lambda S: ST.person_of(S, "ln", "g1"), None),
    ("and k1's later row is the person's", LANDED + [LNOTE_K], lambda S: ST.person_of(S, "lk", "k1"), "g1"),
    ("an eviction the target objected to is refused and ends nothing", [GS, GD1] + lone_evict("k1", "g1", True),
     lambda S: sorted(ST.Seats(S).holders("self", "S")), ["g1", "k1"]),
    # rule 4: g1's row concurrent with the landing, at its head (it names what the landing names, not the landing)
    ("a row of g1 concurrent with the landed eviction, at its head: g1 is out from that head on (rule 4)",
     LANDED + [R("lc", "note", "g1", ("r",))], lambda S: ST.person_of(S, "lc", "g1"), None),
    # the add twin: a landed self_roster_add seats its key, which consented (its own approving answer)
    ("the add twin: k1's proposal to add k2 (k2 signing it) lands: k2 is a live key of the person",
     ADDED, lambda S: sorted(ST.person_keys(S, "g1")), ["g1", "k1", "k2"]),
    ("and k2's later row is the person's", ADDED + [R("k2n", "note", "k2", ("La",))],
     lambda S: ST.person_of(S, "k2n", "k2"), "g1"),
    ("after the landed eviction k1 alone is the roster: its addition of k3 at the landing, its head, concludes",
     LANDED + [add("d3", "S", "k3", ("k1",), ("L",))], lambda S: bool(S.C.get("d3")), True),
    ("and g1, evicted, adds nothing", LANDED + [add("d3", "S", "k3", ("g1",), ("L",))], lambda S: bool(S.C.get("d3")),
     False),
    ("r99 M1: two concurrent lone-path evictions of each other, both silent, are contested: neither lands",
     [GS, GD1] + lone_evict("k1", "g1", False) + lone_evict("g1", "k1", False, "op2", "2"),
     lambda S: sorted(ST.Seats(S).holders("self", "S")), ["g1", "k1"]),
    # R3, the text (CC 3.3.6.4, a stated cost: "One objection of two others does not stop a lone addition... only a
    # strict majority of the others refuses it. That is weaker than the eviction"): a live thief genesis key lone-adds
    # its own key k9 to the honest roster S1. The residual, stated (the Constitution, for 0.5.0; to the steward after
    # the tag): "a holder of one key of three that adds a key while one other is silent holds half the roster, and no count or lone path removes it"
    ("R3 (CC 3.3.6.4, a stated cost): the live thief p1 lone-adds k9 to S1, no objection: k9 is a key of p1",
     GW + R3ADD(()), lambda S: sorted(ST.person_keys(S, "p1")), ["k9", "p1", "p1b", "p1c"]),
    ("R3: one objection of the two others does not stop it", GW + R3ADD(("p1b",)),
     lambda S: sorted(ST.person_keys(S, "p1")), ["k9", "p1", "p1b", "p1c"]),
    ("R3: a strict majority of the others (both) refuses it", GW + R3ADD(("p1b", "p1c")),
     lambda S: sorted(ST.person_keys(S, "p1")), ["p1", "p1b", "p1c"]),
    ("one shape: an addition opener naming its key by `target` alone, with no `to`, seats nothing",
     ADDED_T, lambda S: sorted(ST.Seats(S).holders("self", "S")), ["g1", "k1"]),
    ("a landed addition without the new key's own consent seats nothing", ADDED_NC,
     lambda S: sorted(ST.Seats(S).holders("self", "S")), ["g1", "k1"]),
]

# THE READER'S LINE (ruled): a reader's roster for an identity is the founding its line takes up (checkpoint.takes_up);
# a rival founding concludes nothing for that reader, and neither does everything built on it; neither or both taken up
# is a wait. The genesis key keeps its voice on the taken-up roster, as any key does, until that roster evicts it.
# Readers: p4, whose line took up S1 (the room's founding it cosigned names a1b); None, a fresh reader; x, whose line
# took up only the cosigned rival S1r; m4 in the two-key world (the room's founding names d1).
LEVT = evict("evt", "S1", "p1", ("p1b", "p1c"), ("a1c",))
LRX = ST.offer("S1r", "p1", ("p1", "x"), "self", "@", "self", cosigners=("x",))     # a rival cosigned by a thief key x
LT = ST.cosign("t", "x", "t", ("S1r", "a1c"))
LTX = add("tx", "S1r", "y", ("p1", "x"), ("S1r",))
LTXa = add("txa", "S1r", "y", ("p1", "x"), ("S1r", "evt"))
LTXx = add("txx", "S1r", "y", ("x",), ("S1r", "evt"))
LH = ("p1b", "p2", "p3")
LWORLD = {
    "X1": GW + [LRX, admit_z(LH, ("a1c",))], "X2": GW + [LRX, admit_z(LH, ("a1c", "S1r"))],
    "X3": GW + [LRX, LT, admit_z(LH, ("t",))], "X4": GW + [LRX, LEVT, admit_z(LH, ("evt", "S1r"))],
    "X5": GW + [LRX, admit_z(("x", "p2", "p3"), ("S1r", "a1c"))],
    "Y3": GW + [LRX, LTX, LEVT, admit_z(LH, ("evt", "tx"))], "Y5": GW + [LRX, LEVT, LTXa, admit_z(LH, ("txa",))],
    "Y6": GW + [LRX, LEVT, LTXx, admit_z(LH, ("txx",))], "Y6 (y signs)": GW + [LRX, LEVT, LTXx, admit_z(("y", "p2", "p3"), ("txx",))],
    "D2": GW + [GEV, RIV, admit_z(LH, ("evg", "S1r"))], "D4": GW + [GEV, RIV, RIVH, admit_z(LH, ("evg", "hh"))],
    "D6": GW + [RIV, admit_z(LH, ("a1c", "S1r"))], "D7": GW + [RIV, admit_z(("p1", "p2", "p3"), ("a1c", "S1r"))],
    "D8": GW + [GEV, RIV, RT, admit_z(LH, ("evg", "t"))], "D9": GW + [GEV, RIV, RT2, admit_z(LH, ("evg", "t2"))],
    "D10": GW + [RIV, RT2, admit_z(LH, ("a1c", "t2"))],
    "T1": GW + [RIV, RTA, admit_z(LH, ("a1c", "ta"))], "T1 (p1x signs)": GW + [RIV, RTA, admit_z(("p1x", "p2", "p3"), ("a1c", "ta"))],
    "T2": GW + [RIV, RTA, GEV, admit_z(LH, ("evg", "ta"))],
    "T3": TB + [tadm(("k1", "m2", "m3"), ("tx2",))], "T3 (g1 signs)": TB + [tadm(("g1", "m2", "m3"), ("tx2",))],
    "T3 (x9 signs)": TB + [tadm(("x9", "m2", "m3"), ("tx2",))],
}
# (case, reader, whether z is admitted for it)
LWANT = [("X1", "p4", True), ("X1", None, True), ("X1", "x", False), ("X2", "p4", True), ("X2", None, False),
         ("X3", "p4", True), ("X3", None, False), ("X4", "p4", True), ("X4", None, False), ("X5", "p4", False),
         ("X5", None, False), ("X5", "x", True), ("Y3", "p4", True), ("Y3", None, False), ("Y5", "p4", True),
         ("Y5", None, False), ("Y6", "p4", True), ("Y6", None, False), ("Y6 (y signs)", "p4", False),
         ("D2", "p4", True), ("D2", None, False), ("D4", "p4", True), ("D6", "p4", True), ("D7", "p4", True),
         ("D7", None, False), ("D8", "p4", True), ("D9", "p4", True), ("D10", "p4", True), ("D10", None, False),
         ("T1", "p4", True), ("T1", None, False), ("T1 (p1x signs)", "p4", False), ("T2", "p4", True),
         ("T3", "m4", True), ("T3", None, False), ("T3 (g1 signs)", "m4", True), ("T3 (x9 signs)", "m4", False),
         ("T3 (x9 signs)", "x9", True)]
# the restore case (the Constitution's cost case): a one-key identity g restores its genesis key onto a fresh install
# and founds Sg2 before fetching its roster Sg. "The re-founding concludes nothing for readers on the first roster; the
# genesis key's voice there is unchanged; a fresh reader holding both waits."
RSg, RSg2 = found("Sg", "g"), found("Sg2", "g")
RRM = ST.offer("rm", "g", ("g", "m2", "m3", "m4"), "member", "@", "self", cosigners=("m2", "m3", "m4"), names=("Sg",))
RADM = ST.offer("az", "g", "z", "member", "rm", "group", ("rm", "Sg2"), head=("rm",), policy="community_invite",
                cosigners=("m2", "m3", "z"))
LWORLD["restore"] = [RSg, RRM, RSg2, RADM]
# the line in its ORDER (r100r): the earliest taking-up rows fix the roster; a later row over the rival takes up
# nothing. p4's first taking-up row is the room's founding gc (S1 in its past)
LN4 = R("n4", "note", "p4", ("S1r", "gc", "p4n"))          # a tip-following note, naming p4's own previous row
LV4 = R("v4", "note", "p4", ("S1r",))                      # a row naming only the rival, concurrent with gc
LZ4 = admit_z(("p1b", "p2", "p4"), ("a1c", "S1r"))          # p4 cosigns the admission itself (P3)
LM4N = R("m4n", "note", "m4", ("tx2", "gr", "m4r"))
LQ1, LQ2 = R("q1", "note", "q", ("a1c",)), R("q2", "note", "q", ("S1r",))   # q's two concurrent first rows
LWORLD.update({
    "P1": GW + [LRX, LN4, admit_z(LH, ("a1c", "S1r", "n4"))], "P1'": GW + [LRX, LN4, admit_z(LH, ("a1c", "S1r"))],
    "P2": GW + [LRX, LV4, admit_z(LH, ("a1c", "S1r"))], "P3": GW + [LRX, LZ4],
    "T6": TB + [LM4N, tadm(("k1", "m2", "m3"), ("tx2",))],
    "Q": GW + [LRX, LQ1, LQ2, admit_z(LH, ("a1c", "S1r"))],
})
# P2: v4 names only the rival, not p4's own earlier row gc: an honest client's rows always have its own last row in
# their past, so a reader row omitting it is the reader's own self-fork, and waiting is the honest answer (ruled)
LSD = R("sd", "note", "p1", ("S1r",), cosigners=("p4",))     # the thief's row CLAIMING p4 as a cosigner (R2)
LWORLD["R2"] = GW + [LRX, LSD, admit_z(LH, ("a1c", "S1r"))]
LWANT += [("P1", "p4", True), ("P1'", "p4", True), ("P2", "p4", False), ("P3", "p4", True), ("P3", None, False),
          ("T6", "m4", True), ("Q", "q", False), ("Q", "p4", True),
          # R2 (r101, the safer form): the line reads the reader's own signed rows and the seat rows whose voice it is,
          # never another signer's claimed cosigners on any other row: the thief's note claiming p4 seeds nothing
          ("R2", "p4", True),
          # S5, S6: a thief's seat row that concludes nothing, listing p4 as a cosigner, seeds nothing
          ("S5", "p4", True), ("S6", "p4", True)]
# a seat row's voice through a cosign row (seat.voices): q4, a member of a second room G2 only, cosigns its counted
# admission ra2 by a cosign row naming G2's head; the cosign row reaches no founding of p1, the seat row (naming a1c)
# reaches S1: q4's line takes up S1 through its voice on the concluded seat row
LG2 = ST.offer("G2", "p2", ("p2", "p3", "q4"), "member", "@", "self", cosigners=("p3", "q4"))
LCQ = ST.cosign("cq4", "q4", "ra2", ("G2",))
LRA2 = ST.offer("ra2", "p2", "w", "member", "G2", "group", ("G2", "cq4", "a1c"), head=("G2",), policy="community_invite",
                cosigners=("p3", "w"))
LWORLD["V"] = GW + [LRX, LG2, LCQ, LRA2, admit_z(LH, ("a1c", "S1r"))]
# STRICT own_row (review-48 R2s): q4's only rows are its cosign row, which reaches no founding; the seat row it is a
# voice of is not its own row, so q4 has no line and waits
LWANT += [("V", "q4", False)]
# review-48 R2s: X's self-conferred offer over its own object (it concludes on X's word alone) lists p4 as a cosigner
# and names the rival: no row of p4's line, so p4's line takes up S1 and p4 admits
LWORLD["R2s"] = GW + [LRX, ST.offer("ox", "X", "X2", "member", "X", "self", ("S1r",), cosigners=("p4",)),
                      admit_z(LH, ("a1c", "S1r"))]
LWANT += [("R2s", "p4", True)]
LWORLD["S5"] = GW + [LRX, ST.offer("sdo", "p1", "zz", "member", "gc", "group", ("S1r",), head=("S1r",),
                                   policy="community_invite", cosigners=("p4", "zz")), admit_z(LH, ("a1c", "S1r"))]
LWORLD["S6"] = GW + [LRX, ST.unseat("sdu", "p1", "p2", "member", "gc", "group", ("S1r",), head=("S1r",),
                                    policy="community_remove", cosigners=("p4",)), admit_z(LH, ("a1c", "S1r"))]
LWANT += [("restore", "m4", True), ("restore", None, False)]
# a reader that signs the count itself names its own previous row in it (an honest client, ADOPTING): x and x9
LWORLD["X5 (x names its own row)"] = GW + [LRX, R("xn", "note", "x", ("S1r",)),
                                         admit_z(("x", "p2", "p3"), ("S1r", "a1c", "xn"))]
LWORLD["T3 (x9 signs, naming its own row)"] = TB + [R("x9n", "note", "x9", ("tx2",)), tadm(("x9", "m2", "m3"), ("tx2", "x9n"))]
LWORLD["restore (m4's row)"] = [RSg, RRM, RSg2, R("m4r", "note", "m4", ("rm",)), RADM]
LWANT = [(k, rd, w) for k, rd, w in LWANT if (k, rd) not in (("X5", "x"), ("T3 (x9 signs)", "x9"), ("restore", "m4"))]
LWANT += [("X5 (x names its own row)", "x", True), ("T3 (x9 signs, naming its own row)", "x9", True),
          ("restore (m4's row)", "m4", True),
          # STRICT own_row: x's cosignature on the rival founding is no row of its own; its own rows are xn and the
          # count it signs, which names a1c and omits xn: two first rows reaching both foundings, a wait (P2's rule)
          ("X5", "x", False)]
# each reader's own first row (a reader's line is only the rows it signed itself, r101 R2): p4 and m4 acknowledge
# their rooms, x and x9 the rivals they hold; q's own rows are in its world
READER_ROW = {"p4": R("p4n", "note", "p4", ("gc",)), "m4": R("m4r", "note", "m4", ("gr",)),
              "x": R("xn", "note", "x", ("S1r",)), "x9": R("x9n", "note", "x9", ("tx2",))}
def with_reader(rows, rd):
    extra = READER_ROW.get(rd)
    return list(rows) + ([extra] if extra is not None and all(r["id"] != extra["id"] for r in rows) else [])
LINE_CASES = [("r100 %s, %s" % (k, "a fresh reader" if rd is None else "reader " + rd), with_reader(LWORLD[k], rd), rd,
               "az", w) for k, rd, w in LWANT]


def line_concludes(rows, reader, rid, kv=None):
    if kv is not None: ST.KEY_VIEW.append(kv)
    try:
        S = CK.concluded(CK.kept(list(rows)), RULE)
        R = ST.reader_state(S, reader) if reader is not None else S
        return bool(R.C.get(rid))
    finally:
        if kv is not None: ST.KEY_VIEW.pop()


# K1 on the person lane (the ruling, at the line fold): the reader's own rows seed its roster line only where its key
# stands, by the key view the reader passes. A thief holding p4's stolen key writes a row naming the rival S1r,
# concurrent with p4's revocation of that key: the key view does not count p4's signature there, so the row takes up
# no founding and p4's line still takes up S1; with no key view passed, the thief's row seeds the line and p4 waits.
# (The key view here stands in for key_end's reading of the revocation: it counts p4's signature on every row but tn.)
_TN = ST.R("tn", "note", "p4", ("S1r",))
_KV_UNCOUNTED = (("tn", "p4"),)                 # the key view's table: the (row, key) signatures it does not count
_KV_THIEF = lambda rid, k: (rid, k) not in _KV_UNCOUNTED
KV_LINE_CASES = [
    ("K1 on the line: the thief's row with p4's revoked key, the key view passed: p4's line takes up S1, z admitted",
     with_reader(LWORLD["P1"], "p4") + [_TN], "p4", "az", True, _KV_THIEF),
    ("K1 on the line: the same rows with no key view: the thief's row seeds the line, p4 waits",
     with_reader(LWORLD["P1"], "p4") + [_TN], "p4", "az", False, None),
    # the seat lane alone (no key view: seat_lane_ends_ok): the thief's row is concurrent with p4's own registered
    # self-unseat, which names only p4's honest row: the row is no row of p4's line, and p4's line takes up S1
    ("K1 on the line with no key view: p4's registered self-unseat names p4n; the thief's concurrent row is cut",
     with_reader(LWORLD["P1"], "p4") + [_TN, ST.unseat("up4", "p4", "p4", "registered", "p4", "self", ("p4n",))],
     "p4", "az", True, None),
]

# THE ONE agent recognition (seat.agent_keys / registered_agents): an agent is recognised by its agent seat over any
# room or by its agent registration, whatever scope it was admitted under. AG registers as an agent and is admitted as
# a member: it is still no voice (not even as a device of m1's roster) and in no count's base
AGG = ST.found("g", "m1", ("m1", "m2", "m3", "m4"), {"moderate": ("m1", "m2", "m3", "m4")}, cosigners=("m2", "m3", "m4"))
AGRAG = ST.offer("rag", "AG", "AG", "registered", "AG", "self", identity=("agent",))
AGAM = dict(CRK.admit("am", "AG", ("m1", "m2", "m3"), ("g",)), names=("g", "rag"))
def agadm(signers, extra=()):
    return ST.offer("ay", signers[0], "y", "member", "g", "group", ("am",) + tuple(extra), head=("am",),
                    policy="community_invite", cosigners=tuple(signers[1:]) + ("y",))
AGS1, AGA1 = found("Sm1", "m1"), add("aAG", "Sm1", "AG", ("m1",), ("Sm1",))
R74_CASES += [
    ("an agent registered but admitted as member is still no voice: AG (also m1's device), m2 and m3 do not admit y",
     [AGG, AGRAG, AGS1, AGA1, AGAM, agadm(("AG", "m2", "m3"), ("aAG",))], "ay", False, RULE),
    ("and it is in no count's base: m1, m2 and m3 are three of the four persons, and admit y",
     [AGG, AGRAG, AGAM, agadm(("m1", "m2", "m3"))], "ay", True, RULE),
]


PLANTS = ("person_evict_unread", "person_first", "person_any_kind", "person_end_unread", "concurrent_eviction_unread",
          "persons_unread", "base_by_key", "revoked_voice_kept", "agent_speaks", "lift_author_device", "genesis_unread",
          "fold_lift_by_key", "fold_author_by_key", "remover_counted_over", "opener_withdrawal_voter",
          "apart_by_key", "person_keys_by_offer", "nodes_by_offer", "nodes_two_owners_kept", "nodes_revocation_unread",
          "evicted_genesis_speaks", "evicted_key_votes", "rival_roster_kept",
          "rebinding_unread", "landed_eviction_unread", "landed_add_unread",
          "self_founding_family", "mutual_evictions_land", "rival_line_unread", "line_order_unread",
          "claimed_cosigner_counted", "seat_voice_counted", "line_key_end_unread", "agent_by_seat_only", "person_key_lane_unread",
          "registered_by_past")
KE_PLANTS = ("person_key_lane_unread",)   # planted in key_end: a key's one set of ends


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
    for name, rows, want in R78K_CASES:
        got = ag_held(rows)
        if got != want:
            problems.append("%s: got %r, expected %r" % (name, got, want))
        for o in orders(rows)[:21]:
            n += 1
            if ("AG" in ST.Seats(CK.arrive(o, RULE_W)).holders("agent", "g")) != got:
                problems.append("%s: order %s differs" % (name, [r["id"] for r in o]))
                break
    for name, rows, want in LATENT_CASES:
        got = latent_outcome(rows)
        if got != want:
            problems.append("%s: got %r, expected %r" % (name, got, want))
    for name, rows, k, want in PERSON_KEYS_CASES:
        got = sorted(ST.person_keys(concluded_set(rows), k))
        if got != want:
            problems.append("%s: got %r, expected %r" % (name, got, want))
        for o in orders(rows)[:21]:
            n += 1
            if sorted(ST.person_keys(CK.arrive(o, RULE), k)) != got:
                problems.append("%s: order %s differs" % (name, [r["id"] for r in o]))
                break
    for name, rows, k, want in NODES_CASES:
        got = sorted(ST.nodes_of(concluded_set(rows), k))
        if got != want:
            problems.append("%s: got %r, expected %r" % (name, got, want))
        for o in orders(rows)[:21]:
            n += 1
            if sorted(ST.nodes_of(CK.arrive(o, RULE), k)) != got:
                problems.append("%s: order %s differs" % (name, [r["id"] for r in o]))
                break
    for name, rows, f, want in LANDED_CASES:
        got = f(landed_state(rows))
        if got != want:
            problems.append("%s: got %r, expected %r" % (name, got, want))
        for o in orders(rows)[:21]:
            n += 1
            if f(CK.arrive(o, RULE_W)) != got:
                problems.append("%s: order %s differs" % (name, [r["id"] for r in o]))
                break
    for name, rows, rd, rid, want in LINE_CASES:
        got = line_concludes(rows, rd, rid)
        if got != want:
            problems.append("%s: got %r, expected %r" % (name, got, want))
    for name, rows, rd, rid, want, kv in KV_LINE_CASES:
        got = line_concludes(rows, rd, rid, kv)
        if got != want:
            problems.append("%s: got %r, expected %r" % (name, got, want))
    caught = 0
    for plant in PLANTS:
        (KE.MUT if plant in KE_PLANTS else ST.MUT).add(plant)
        try:
            hit = [c[0] for c in CASES if answer(c[1], c[2]) != c[3]] + \
                  [c[0] for c in COUNT_CASES if concludes(c[1], c[2]) != c[3]] + \
                  [c[0] for c in WINDOW_CASES if window_outcome(c[1]) != c[2]] + \
                  [c[0] for c in BALLOT_CASES if concludes(c[1], c[2]) != c[3]] + \
                  [c[0] for c in R74_CASES if bool(CK.concluded(CK.kept(list(c[1])), c[4]).C.get(c[2])) != c[3]] + \
                  [c[0] for c in R78K_CASES if ag_held(c[1]) != c[2]] + \
                  [c[0] for c in LATENT_CASES if latent_outcome(c[1]) != c[2]] + \
                  [c[0] for c in PERSON_KEYS_CASES if sorted(ST.person_keys(concluded_set(c[1]), c[2])) != c[3]] + \
                  [c[0] for c in NODES_CASES if sorted(ST.nodes_of(concluded_set(c[1]), c[2])) != c[3]] + \
                  [c[0] for c in LANDED_CASES if c[2](landed_state(c[1])) != c[3]] + \
                  [c[0] for c in LINE_CASES if line_concludes(c[1], c[2], c[3]) != c[4]] + \
                  [c[0] for c in KV_LINE_CASES if line_concludes(c[1], c[2], c[3], c[5]) != c[4]]
        finally:
            ST.MUT.discard(plant)
            KE.MUT.discard(plant)
        caught += bool(hit)
        print("  plant %-20s %s" % (plant, "caught by %d cases, first: %s" % (len(hit), hit[0]) if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % plant)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases (%d of a key's person, %d of a count over persons, %d of a window's answers, %d of "
          "ballots, %d of the review r74, %d of the review r78k, %d of the opener's withdrawal, %d of a person's keys, "
          "%d of an owner's nodes), %d arrival orders, "
          "%d of %d planted breaks caught"
          % ("ok" if not problems else "%d problems" % len(problems),
             len(CASES) + len(COUNT_CASES) + len(WINDOW_CASES) + len(BALLOT_CASES) + len(R74_CASES) + len(R78K_CASES)
             + len(LATENT_CASES) + len(PERSON_KEYS_CASES) + len(NODES_CASES), len(CASES), len(COUNT_CASES),
             len(WINDOW_CASES), len(BALLOT_CASES), len(R74_CASES), len(R78K_CASES), len(LATENT_CASES),
             len(PERSON_KEYS_CASES), len(NODES_CASES), n, caught, len(PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
