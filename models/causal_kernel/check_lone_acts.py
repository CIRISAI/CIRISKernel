#!/usr/bin/env python3
"""
check_lone_acts.py: a duty holder's lone acts against a key or content, and their ways back (seat.py: lone_act_rule,
reconsideration_rule, act_in_force; CC 4.5.4 (iii), CC 4.5.5, CC 3.1.9.2, CC 4.4.3.12, as the Constitution ruled 2b).

    the acts        a quarantine marker (`quarantine`, state withhold or release, of a KEY) and a slashing verdict
                    (`slashing`, outcome proven_rogue or not_proven, about a KEY), both under the `slash` duty (there is
                    no quarantine duty); a takedown notice (`takedown_notice`, of a CONTENT row) under `takedown`
    in a community  none is counted: each is one duty holder's signature at the newest counted changes in its past, in
                    force by the end rule (seat.removal_in_force read for the act's duty: the signer's standing live,
                    or another holder's receipt keeping it)
    the way back    one lift for all three: the members' moderation_overturn (an offer of scope `act` naming the act and
                    the objections to it), counted over the members seated at both the act's head and the lift's, the
                    author apart, a strict majority, floor two; and for a takedown a second one, a concluded
                    `reconsideration` with outcome `reversed` naming it, the review duty's act
    the markers     a withhold outranks a release whatever their instants: only a release that names the withhold lifts
                    it; the marker plane never withholds itself (a quarantined key's own markers stand)
    the verdict     a slashing verdict fires only on a proven ground: not_proven fires nothing
    an affiliation  the act is its body's, counted over its officers: with one officer a proposal, decided only by a
                    countersign naming it (rule 4: a concurrent withdrawal by the acting seat leaves nothing decided);
                    with two or more, two voices, the member concerned apart

Each case is a hand-written answer (which rows conclude, and which acts are in force), read in arrival orders.

Planted breaks (seat.MUT), each of which must change a case's answer:
    lone_act_counted        a lone act is counted as the duty holders' count
    lone_act_cosigned       a lone act cosigned by another key concludes
    lone_act_end_unread     the end rule is not read: a lone act stays in force after its signer's standing ends
    lone_act_lift_unread    the members' lift of a lone act is not read
    reconsideration_unread  a reversed reconsideration does not take a takedown down
    release_unread          a release naming a withhold does not lift it
    unproven_fires          a not_proven verdict fires
    countersign_unread      (the countersign) an affiliation's one-officer act is decided without a countersign

    python3 -I check_lone_acts.py      exit 1 on any difference
"""
import itertools
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import seat as ST  # noqa: E402
import window as WN  # noqa: E402

CK = ST.CK
OBJ = "g"
RULE = lambda r, P, past: WN.rule(r, P, past)
T, F = True, False

# a room of four: p1 and p2 hold `takedown`, p1 and p2 hold `slash`, p4 holds `review`; p3 posts c1
G = ST.found("g", "p1", ("p1", "p2", "p3", "p4"), {"takedown": ("p1", "p2"), "slash": ("p1", "p2"), "review": ("p4",)},
             cosigners=("p2", "p3", "p4"))
C1 = CK.row("c1", "post", "p3", ("g",), room=OBJ)
W = [G, C1]


def act(i, kind, signer, heads=("g",), names=(), obj=OBJ, **kw):
    """A lone act; it opens the members' moderation_overturn window (as a moderator's lone removal does)."""
    return ST.R(i, kind, signer, tuple(heads) + tuple(names), obj=obj, head=tuple(heads), window="moderation_overturn",
                **kw)


TD = act("td", "takedown_notice", "p1", names=("c1",), of="c1")
QW = act("qw", "quarantine", "p1", target="p3", state="withhold")
QR = act("qr", "quarantine", "p1", names=("qw",), target="p3", state="release", of="qw")
SP = act("sp", "slashing", "p1", target="p3", outcome="proven_rogue")
SN = act("sn", "slashing", "p1", target="p3", outcome="not_proven")
LAY = ST.withdraw("ld", "p1", "g", ("td",), scope="takedown")          # p1 lays its takedown duty down after td
OB = lambda i, k, a="td": WN.answer(i, k, a, "object")
LIFT = lambda objs, a="td": ST.offer("lf", "p2", (), "act", OBJ, "group", (a,) + tuple(objs) + ("g",), head=("g",),
                                     content=a, policy="moderation_overturn", cosigners=())
RC = lambda k, outcome="reversed": act("rc", "reconsideration", k, names=("td",), of="td", outcome=outcome)

# a one-officer affiliation a1: A its officer, B appointed (a member), O its designated official; B posts b1
A1 = ST.found("a1", "A", ("A",), {ST.OFFICER: ("A",)}, declared_cohort="affiliations", official="O")
A1B = ST.offer("a1b", "A", ("B",), "member", "a1", "group", ("a1",), head=("a1",), cosigners=("B",), counted=ST.OFFICER)
B1 = CK.row("b1", "post", "B", ("a1b",), room="a1")
AF = [A1, A1B, B1]
ATD = act("atd", "takedown_notice", "A", heads=("a1b",), names=("b1",), obj="a1", of="b1")
ACS = ST.R("acs", "countersign", "O", ("atd",), of="atd")
AWD = ST.withdraw("awd", "A", "atd", ("atd",))
# two officers: A and C
A2 = ST.found("a1", "A", ("A", "C"), {ST.OFFICER: ("A", "C")}, cosigners=("C",), declared_cohort="affiliations")
A2B = ST.offer("a1b", "A", ("B",), "member", "a1", "group", ("a1",), head=("a1",), cosigners=("C", "B"), counted=ST.OFFICER)

# (name, rows, {row: concludes}, {act: in force})
CASES = [
    ("a takedown by a takedown holder, alone, at the newest change: concluded and in force", W + [TD], {"td": T},
     {"td": T}),
    ("a takedown by a key holding no takedown duty concludes nothing", W + [act("td", "takedown_notice", "p3",
                                                                                names=("c1",), of="c1")],
     {"td": F}, {"td": F}),
    ("a lone act is one signature: a takedown cosigned by another holder is no lone act",
     W + [dict(TD, cosigners=("p2",))], {"td": F}, {"td": F}),
    ("a takedown at an old head (a counted change in its past it does not name) concludes nothing",
     W + [ST.offer("a5", "p1", "p5", "member", OBJ, "group", ("g",), head=("g",), policy="community_invite",
                   cosigners=("p2", "p3", "p5")),
          act("td", "takedown_notice", "p1", names=("c1", "a5"), of="c1")], {"a5": T, "td": F}, {"td": F}),
    ("its signer lays the takedown duty down after it: counted at its own head, out of force from there (E2)",
     W + [TD, LAY], {"td": T, "ld": T}, {"td": F}),
    ("the same, and p2, the other takedown holder, receipts it: in force (E8)",
     W + [TD, CK.row("q2", "ack", "p2", ("td",), of="td"), LAY], {"td": T}, {"td": T}),
    ("the members lift it: p2, p3 and p4 object, three of the three at both heads (p1, the author, apart)",
     W + [TD, OB("o2", "p2"), OB("o3", "p3"), OB("o4", "p4"), LIFT(("o2", "o3", "o4"))], {"lf": T}, {"td": F}),
    ("one objection is no lift (the floor of two): it stays in force", W + [TD, OB("o2", "p2"), LIFT(("o2",))],
     {"lf": F}, {"td": T}),
    ("the author's own objection is no voice", W + [TD, OB("o1", "p1"), OB("o2", "p2"), LIFT(("o1", "o2"))],
     {"lf": F}, {"td": T}),
    ("a reconsideration by the review holder reversing it: the takedown is down", W + [TD, RC("p4")], {"rc": T},
     {"td": F}),
    ("a reconsideration by a key holding no review duty concludes nothing", W + [TD, RC("p2")], {"rc": F}, {"td": T}),
    ("a reconsideration that upholds it leaves it in force", W + [TD, RC("p4", "upheld")], {"rc": T}, {"td": T}),
    ("a quarantine withhold by a slash holder: in force", W + [QW], {"qw": T}, {"qw": T}),
    ("a release naming the withhold lifts it", W + [QW, QR], {"qr": T}, {"qw": F, "qr": T}),
    ("a release naming no withhold concludes nothing, and the withhold holds whatever their order",
     W + [QW, act("qr", "quarantine", "p2", target="p3", state="release")], {"qr": F}, {"qw": T}),
    ("a release by a key holding no slash duty concludes nothing", W + [QW, dict(QR, signer="p3")], {"qr": F},
     {"qw": T}),
    ("there is no quarantine duty: slash authorises the marker, and p4, holding review, concludes nothing", W + [act("qw", "quarantine", "p4", target="p3", state="withhold")], {"qw": F}, {"qw": F}),
    ("the marker plane never withholds itself: p2 quarantines p1, and p1's own withhold of p3 stands",
     W + [QW, act("q1", "quarantine", "p2", target="p1", state="withhold")], {"qw": T, "q1": T}, {"qw": T, "q1": T}),
    ("a slashing verdict on a proven ground fires", W + [SP], {"sp": T}, {"sp": T}),
    ("not proven: the verdict concludes and fires nothing", W + [SN], {"sn": T}, {"sn": F}),
    ("an outcome outside the two concludes nothing", W + [dict(SN, outcome="maybe")], {"sn": F}, {"sn": F}),
    # ---- an affiliation (CC 4.4.3.12): the body's act, over its officers ---------------------------------------------
    ("a one-officer affiliation's takedown of a member's content: a proposal, not in force", AF + [ATD],
     {"atd": T}, {"atd": F}),
    ("countersigned by its designated official: decided, in force", AF + [ATD, ACS], {"acs": T}, {"atd": T}),
    ("the acting officer's withdrawal concurrent with the countersign: nothing decided (rule 4)", AF + [ATD, ACS, AWD],
     {"acs": T}, {"atd": F}),
    ("two officers: one alone takes nothing down", [A2, A2B, B1, ATD], {"atd": F}, {"atd": F}),
    ("and the two together: decided, no countersign asked", [A2, A2B, B1, dict(ATD, cosigners=("C",))], {"atd": T},
     {"atd": T}),
]
PLANTS = ("lone_act_counted", "lone_act_cosigned", "lone_act_end_unread", "lone_act_lift_unread",
          "reconsideration_unread", "release_unread", "unproven_fires", "countersign_unread")


def answer(rows, concl, force):
    S = CK.concluded(CK.kept(list(rows)), RULE)
    return ({i: bool(S.C.get(i)) for i in concl}, {a: ST.act_in_force(S, a) for a in force})


def orders(rows):
    tail = rows[1:]
    if len(tail) <= 5:
        return [[rows[0]] + list(p) for p in itertools.permutations(tail)]
    rnd = random.Random(len(tail))
    out = [[rows[0]] + tail[::-1]]
    for _ in range(20):
        p = list(tail)
        rnd.shuffle(p)
        out.append([rows[0]] + p)
    return out


def misses(plant=None, every_order=False):
    hit = []
    saved = set(ST.MUT)
    if plant: ST.MUT.add(plant)
    try:
        for name, rows, concl, force in CASES:
            want = (concl, force)
            for o in (orders(rows) if every_order else [rows]):
                got = answer(o, concl, force)
                if got != want:
                    hit.append("%s: got %s, expected %s" % (name, got, want))
                    break
    finally:
        ST.MUT.clear(); ST.MUT |= saved
    return hit


def main():
    problems = misses(every_order=True)
    caught = 0
    for p in PLANTS:
        h = misses(p)
        caught += bool(h)
        print("  plant %-24s %s" % (p, "caught by %d cases, first: %s" % (len(h), h[0][:150]) if h else "NOT CAUGHT"))
        if not h: problems.append("plant %s not caught" % p)
    for p in problems: print(p)
    print("RESULT: %s: %d cases, %d of %d planted breaks caught" % ("ok" if not problems else "%d problems" % len(problems),
                                                                   len(CASES), caught, len(PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
