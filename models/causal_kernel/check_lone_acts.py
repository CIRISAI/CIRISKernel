#!/usr/bin/env python3
"""
check_lone_acts.py: a duty holder's lone acts against a key or content, and their ways back (seat.py: lone_act_rule,
reconsideration_rule, act_in_force; CC 4.5.4 (iii), CC 4.5.5, CC 3.1.9.2, CC 4.4.3.12, as the Constitution ruled 2b).

    the acts        a quarantine marker (`quarantine:{state}`, withhold or release, of a KEY) and a slashing verdict
                    (`slashing:{outcome}`, proven_rogue or not_proven, about a KEY), both under the `slash` duty (there
                    is no quarantine duty); a takedown notice (`takedown_notice:{basis}`, an opaque basis, of a CONTENT
                    row) under `takedown`. The family parameter is the kind's suffix
    in a community  none is counted: each is one duty holder's signature at the newest counted changes in its past, in
                    force by the end rule (seat.removal_in_force read for the act's duty: the signer's standing live,
                    or another holder's receipt keeping it)
    the way back    one lift for all three: the members' moderation_overturn (an offer of scope `act` naming the act and
                    the objections to it), counted over the members seated at both the act's head and the lift's, the
                    author apart, a strict majority, floor two; and for a takedown a second one, a concluded
                    `reconsideration:{grounds}` (new_evidence, procedural_error, quorum_compromise) with outcome
                    `reversed` naming it, the review duty's act (`partial` and `upheld` fell nothing)
    the markers     a withhold outranks a release whatever their instants: only a release that names the withhold lifts
                    it; the marker plane never withholds itself (a quarantined key's own markers stand)
    the verdict     a slashing verdict fires only on a proven ground: not_proven fires nothing
    an affiliation  the act is its body's, counted over its officers: with one officer a proposal, decided only by a
                    countersign: the designated official's or an overseer's own voice on the act's row (G15);
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
    self_release            a content's author reverses its takedown
    release_by_any_holder   another holder's release of a withhold lifts it (G21: only the holder that withheld)
    first_cite              a row citing several reads its first cite (r98: exactly one cite, or nothing)
    release_end_read        a release is read by the E rules: its author's later lay-down brings the withhold back
    release_concurrent_kept an end concurrent with a release does not cut it (rule 4 unread)
    target_any_room         a takedown's content, or a marker's key, need not be the room's
    lift_base_lift_head     (the lift) counted at the lift's heads alone: members admitted after the act carry it

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


# the registered families: the family parameter is the kind's suffix (a notice's basis is an opaque word)
TDK = "takedown_notice:legal_order"
TD = act("td", TDK, "p1", names=("c1",), of="c1")
QW = act("qw", "quarantine:withhold", "p1", target="p3")
QR = act("qr", "quarantine:release", "p1", names=("qw",), target="qw")        # p1's supersedes of its own withhold
SP = act("sp", "slashing:proven_rogue", "p1", target="p3")
SN = act("sn", "slashing:not_proven", "p1", target="p3")
LAY = ST.withdraw("ld", "p1", "g", ("td",), scope="takedown")          # p1 lays its takedown duty down after td
OB = lambda i, k, a="td": WN.answer(i, k, a, "object")
LIFT = lambda objs, a="td": ST.offer("lf", "p2", (), "act", OBJ, "group", (a,) + tuple(objs) + ("g",), head=("g",),
                                     cites=(a,), policy="moderation_overturn", cosigners=())
RC = lambda k, outcome="reversed", grounds="new_evidence": act("rc", "reconsideration:" + grounds, k, names=("td",), cites=("td",),
                                                              outcome=outcome)

# a one-officer affiliation a1: A its officer, B appointed (a member), O its designated official; B posts b1
A1 = ST.found("a1", "A", ("A",), {ST.OFFICER: ("A",)}, declared_cohort="affiliations", official="O")
A1B = ST.offer("a1b", "A", ("B",), "member", "a1", "group", ("a1",), head=("a1",), cosigners=("B",), counted=ST.OFFICER)
B1 = CK.row("b1", "post", "B", ("a1b",), room="a1")
AF = [A1, A1B, B1]
ATD = act("atd", TDK, "A", heads=("a1b",), names=("b1",), obj="a1", of="b1")
ATDO = dict(ATD, cosigners=("O",))          # the countersign: the official's own voice on the act's row (G15)
AWD = ST.withdraw("awd", "A", "atd", ("atd",))
# two officers: A and C
A2 = ST.found("a1", "A", ("A", "C"), {ST.OFFICER: ("A", "C")}, cosigners=("C",), declared_cohort="affiliations")
A2B = ST.offer("a1b", "A", ("B",), "member", "a1", "group", ("a1",), head=("a1",), cosigners=("C", "B"), counted=ST.OFFICER)

# r75 rows: content c4 by p4 (the review holder); another room g2 and its content c2; p5 and p6 admitted after the act
C4 = CK.row("c4", "post", "p4", ("g",), room=OBJ)
G2 = ST.found("g2", "q1", ("q1", "q2", "q3"), {"takedown": ("q1",), "review": ("q2",)}, cosigners=("q2", "q3"))
C2 = CK.row("c2", "post", "q3", ("g2",), room="g2")
A5 = ST.offer("a5", "p1", "p5", "member", OBJ, "group", ("g",), head=("g",), policy="community_invite",
              cosigners=("p2", "p3", "p5"))
A6 = ST.offer("a6", "p1", "p6", "member", OBJ, "group", ("a5",), head=("a5",), policy="community_invite",
              cosigners=("p2", "p3", "p5", "p6"))
LIFT6 = ST.offer("lf", "p2", (), "act", OBJ, "group", ("td", "o2", "o5", "o6", "a6"), head=("a6",), cites=("td",),
                 policy="moderation_overturn")
# (name, rows, {row: concludes}, {act: in force})
CASES = [
    ("a takedown by a takedown holder, alone, at the newest change: concluded and in force", W + [TD], {"td": T},
     {"td": T}),
    ("a takedown by a key holding no takedown duty concludes nothing", W + [act("td", TDK, "p3", names=("c1",), of="c1")],
     {"td": F}, {"td": F}),
    ("a lone act is one signature: a takedown cosigned by another holder is no lone act",
     W + [dict(TD, cosigners=("p2",))], {"td": F}, {"td": F}),
    ("a takedown at an old head (a counted change in its past it does not name) concludes nothing",
     W + [ST.offer("a5", "p1", "p5", "member", OBJ, "group", ("g",), head=("g",), policy="community_invite",
                   cosigners=("p2", "p3", "p5")),
          act("td", TDK, "p1", names=("c1", "a5"), of="c1")], {"a5": T, "td": F}, {"td": F}),
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
    ("a partial reversal does not fell a notice on one content row", W + [TD, RC("p4", "partial")], {"rc": T},
     {"td": T}),
    ("a reconsideration on other grounds (procedural error) reversing it: down", W + [TD, RC("p4", grounds="procedural_error")],
     {"rc": T}, {"td": F}),
    ("grounds outside the three conclude nothing", W + [TD, RC("p4", grounds="whim")], {"rc": F}, {"td": T}),
    ("an outcome outside the three concludes nothing", W + [TD, RC("p4", "maybe")], {"rc": F}, {"td": T}),
    ("a takedown notice with no basis concludes nothing", W + [act("td", "takedown_notice", "p1", names=("c1",), of="c1")],
     {"td": F}, {"td": F}),
    ("a quarantine withhold by a slash holder: in force", W + [QW], {"qw": T}, {"qw": T}),
    ("a release naming the withhold lifts it", W + [QW, QR], {"qr": T}, {"qw": F, "qr": T}),
    ("a release naming no withhold concludes nothing, and the withhold holds whatever their order",
     W + [QW, act("qr", "quarantine:release", "p2", target="p3")], {"qr": F}, {"qw": T}),
    ("a release by a key holding no slash duty concludes nothing", W + [QW, dict(QR, signer="p3")], {"qr": F},
     {"qw": T}),
    ("there is no quarantine duty: slash authorises the marker, and p4, holding review, concludes nothing", W + [act("qw", "quarantine:withhold", "p4", target="p3")], {"qw": F}, {"qw": F}),
    ("the marker plane never withholds itself: p2 quarantines p1, and p1's own withhold of p3 stands",
     W + [QW, act("q1", "quarantine:withhold", "p2", target="p1")], {"qw": T, "q1": T}, {"qw": T, "q1": T}),
    ("a slashing verdict on a proven ground fires", W + [SP], {"sp": T}, {"sp": T}),
    ("not proven: the verdict concludes and fires nothing", W + [SN], {"sn": T}, {"sn": F}),
    ("an outcome outside the two concludes nothing", W + [dict(SN, kind="slashing:maybe")], {"sn": F}, {"sn": F}),
    # ---- r75 ---------------------------------------------------------------------------------------------------------
    ("r75: the key withheld never releases its own withhold: p2 withholds p1, p1's release concludes nothing",
     W + [act("qw1", "quarantine:withhold", "p2", target="p1"),
          act("qr1", "quarantine:release", "p1", names=("qw1",), target="qw1")], {"qr1": F}, {"qw1": T}),
    # ---- G21 as re-ruled: a release is the withholding holder's supersedes of its own withhold -------------------
    ("G21: another slash holder's release is refused: p1 withholds p3, p2 releases it, and the withhold holds",
     W + [QW, act("qr2", "quarantine:release", "p2", names=("qw",), target="qw")], {"qr2": F}, {"qw": T}),
    ("G21: a double release: p1 releases its withhold twice; both conclude and the withhold is lifted",
     W + [QW, QR, act("qr2", "quarantine:release", "p1", names=("qw",), target="qw")], {"qr": T, "qr2": T},
     {"qw": F}),
    ("G21: a release of a release concludes nothing", W + [QW, QR, act("qr3", "quarantine:release", "p1",
                                                                          names=("qr",), target="qr")],
     {"qr3": F}, {"qw": F}),
    ("r75: the author of the content never reconsiders its own takedown: p4 (review) posts c4, p1 takes it down, p4's "
     "reversal concludes nothing", W + [C4, act("td", TDK, "p1", names=("c4",), of="c4"),
                                       act("rc", "reconsideration:new_evidence", "p4", names=("td",), cites=("td",),
                                           outcome="reversed")], {"rc": F}, {"td": T}),
    ("r75: a takedown's content is the room's: p1 takes down c2, a row of another room, and concludes nothing",
     W + [G2, C2, act("td", TDK, "p1", names=("c2",), of="c2")], {"td": F}, {"td": F}),
    ("r75: a marker's key is seated in the room: p1 withholds X, no key of g, and concludes nothing",
     W + [act("qx", "quarantine:withhold", "p1", target="X")], {"qx": F}, {"qx": F}),
    ("r75: the lift at both heads: p5 and p6, admitted after the takedown, object with p2; the base is the members at "
     "both heads (p2, p3, p4), so one of three lifts nothing", W + [TD, A5, A6, OB("o2", "p2"), OB("o5", "p5"),
                                                                  OB("o6", "p6"), LIFT6], {"a6": T, "lf": F}, {"td": T}),
    # ---- review-58 on da015c0: a release is no standing act -----------------------------------------------------------
    ("n1: a release stays in force after its author lays slash down (the end has it in its past): p2 receipts qw, p1 "
     "releases it, then p1 lays slash down; the withhold does not come back", W + [QW, CK.row("rq", "ack", "p2", ("qw",), of="qw"), QR,
                                                   ST.withdraw("ls", "p1", "g", ("qr",), scope="slash")],
     {"qr": T}, {"qw": F, "qr": T}),
    ("a release is an END of its withhold, read by rule 4: a lay-down concurrent with it cuts it, and the receipted "
     "withhold stays", W + [QW, CK.row("rq", "ack", "p2", ("qw",), of="qw"), QR,
                            ST.withdraw("ls", "p1", "g", ("qw",), scope="slash")],
     {"qr": T}, {"qw": T, "qr": F}),
    ("a withhold made after its signer's lay-down concludes nothing", W + [ST.withdraw("ls", "p1", "g", ("g",),
                                                                                       scope="slash"),
                                                                           act("qw", "quarantine:withhold", "p1",
                                                                               names=("ls",), target="p3")],
     {"qw": F}, {"qw": F}),
    # ---- r98 (review-58): a reconsideration names ITS notice and a lift THE act: exactly one cite ------------------
    ("r98 M1: p1 releases p2's withhold of p1 (target qw1, the second withhold cited too): only the holder that "
     "withheld releases, so nothing", W + [QW, act("qw1", "quarantine:withhold", "p2", target="p1"),
                                           act("qr", "quarantine:release", "p1", names=("qw", "qw1"), target="qw1",
                                               cites=("qw", "qw1"))], {"qr": F}, {"qw": T, "qw1": T}),
    ("r98 M2: a lift citing two acts (td, objected; qw, not) concludes nothing, and both stay in force",
     W + [TD, QW, OB("o2", "p2"), OB("o3", "p3"), OB("o4", "p4"),
          ST.offer("lf", "p2", (), "act", OBJ, "group", ("td", "qw", "o2", "o3", "o4", "g"), head=("g",),
                   cites=("td", "qw"), policy="moderation_overturn")], {"lf": F}, {"td": T, "qw": T}),
    ("r98 M2b: the same with its cites the other way round", W + [TD, QW, OB("o2", "p2"), OB("o3", "p3"), OB("o4", "p4"),
          ST.offer("lf", "p2", (), "act", OBJ, "group", ("td", "qw", "o2", "o3", "o4", "g"), head=("g",),
                   cites=("qw", "td"), policy="moderation_overturn")], {"lf": F}, {"td": T, "qw": T}),
    ("r98 M3: p4 reconsiders citing td and td2 (a takedown of p4's own c4): two cites, nothing reversed",
     W + [TD, C4, act("td2", TDK, "p2", names=("c4",), of="c4"),
          act("rc", "reconsideration:new_evidence", "p4", names=("td", "td2"), cites=("td", "td2"), outcome="reversed")],
     {"rc": F}, {"td": T, "td2": T}),
    ("r98 M3b: p4 (review in g) reconsiders citing td and a takedown in another room: nothing reversed",
     W + [TD, G2, C2, act("tdx", TDK, "q1", heads=("g2",), names=("c2",), obj="g2", of="c2"),
          act("rc", "reconsideration:new_evidence", "p4", names=("td", "tdx"), cites=("td", "tdx"), outcome="reversed")],
     {"rc": F, "tdx": T}, {"td": T, "tdx": T}),
    ("r98 M6: a lift whose one cite is the content row, not the act, lifts nothing",
     W + [TD, OB("o2", "p2"), OB("o3", "p3"), OB("o4", "p4"),
          ST.offer("lf", "p2", (), "act", OBJ, "group", ("td", "o2", "o3", "o4", "g"), head=("g",), cites=("c1",),
                   policy="moderation_overturn")], {"lf": F}, {"td": T}),
    # ---- an affiliation (CC 4.4.3.12): the body's act, over its officers ---------------------------------------------
    ("a one-officer affiliation's takedown of a member's content: a proposal, not in force", AF + [ATD],
     {"atd": T}, {"atd": F}),
    ("with its designated official's voice on the act's row (G15): decided, in force", AF + [ATDO], {"atd": T},
     {"atd": T}),
    ("an ineligible outside voice on the act (X): refused", AF + [dict(ATD, cosigners=("X",))], {"atd": F}, {"atd": F}),
    ("the acting officer's withdrawal of its held takedown decides nothing: not in force", AF + [ATD, AWD], {"atd": T},
     {"atd": F}),
    ("two officers: one alone takes nothing down", [A2, A2B, B1, ATD], {"atd": F}, {"atd": F}),
    ("and the two together: decided, no countersign asked", [A2, A2B, B1, dict(ATD, cosigners=("C",))], {"atd": T},
     {"atd": T}),
]
PLANTS = ("lone_act_counted", "lone_act_cosigned", "lone_act_end_unread", "lone_act_lift_unread",
          "reconsideration_unread", "release_unread", "unproven_fires", "countersign_unread", "self_release", "release_by_any_holder", "first_cite", "release_end_read", "release_concurrent_kept",
          "target_any_room", "lift_base_lift_head")


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
