#!/usr/bin/env python3
"""
check_acts.py: which act a counted row is (seat.act_of), and which policy rows an act may take (seat.policy_for), as
the Constitution's acts table (data/governance_policy_acts.tsv) writes them. Steps 1 and 2 of the act-to-policy
binding: no rule reads either yet, so no answer of any other case changes.

The act is decided from the row's kind (offer, unseat), its scope and its object (the object's kind, read from its
founding row's scope: seat.KINDS), never from the policy it states. Each case names one row of a set and the act it
is; each query case names (act, scope class, kind) and the policy rows and choice the table gives.

Planted breaks, each of which must change a case's answer:
    lift_unread         an offer naming a removal of the same seat is read as an admission, not the lift
    election_unread     an offer of a duty under the ranked count is read as the duty holders' conferral
    recall_by_policy    an unseat of a duty is told recall from withdrawal by the policy it states, not by `counted`
    kind_unread         every founding row is a community (an accord's row an admission, and so on)
    key_kind_unread     a key object has no kind
    detect_unread       a detector seat's conferral is no act
    binding_off         the acts table is not read: a counted row is counted under any policy it states
    stated_policy_free  a row's stated policy is not held to its act's rows (a fixed act's, or the row's choice)
    protocol_unread     a protocol row (cosigned_act, community_remove) is counted as a row-declared threshold

    python3 -I check_acts.py      exit 1 on any difference
"""
import contextlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import seat as ST  # noqa: E402

CK = ST.CK
OBJ = "g"

GM = ST.offer("g", "A", ("A", "B", "C"), "member", "@", "self", cosigners=("B", "C"))
FH = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("A",)}, cosigners=("B", "C"), duties=("verify",))
GA = ST.offer("g", "h1", ("h1", "h2", "h3"), "holder", "@", "self", cosigners=("h2", "h3"))       # an accord
GS = ST.offer("g", "d1", ("d1", "d2", "d3"), "self", "@", "self", cosigners=("d2", "d3"))         # a self roster


def grp(i, kind, k, scope, policy, heads=("g",), obj=OBJ, **kw):
    mk = ST.offer if kind == "offer" else ST.unseat
    return mk(i, "A", k, scope, obj, "group", tuple(heads) + tuple(kw.pop("cites", ())), head=tuple(heads), policy=policy, **kw)


REM = grp("xr", "unseat", "X", "agent", "community_remove", window="moderation_overturn")
# (name, rows, the row asked, (act, scope class, kind) or None)
CASES = [
    ("an admission of a member", [GM, grp("r", "offer", "D", "member", "community_invite")], "r", ("admit", "member", "community")),
    ("an admission of an agent", [GM, grp("r", "offer", "X", "agent", "community_invite")], "r", ("admit", "agent", "community")),
    ("a removal of a member, whatever policy it states", [GM, grp("r", "unseat", "B", "member", "accord_halt")], "r",
     ("remove", "member", "community")),
    ("a removal of an agent (a lone removal by its shape)", [GM, REM], "xr", ("remove", "agent", "community")),
    ("the lift: an offer naming a removal of the same seat", [GM, REM, grp("r", "offer", "X", "agent", "moderation_overturn",
                                                                          cites=("xr",), content="xr")],
     "r", ("lift", "agent", "community")),
    ("an offer naming a removal of another key's seat is an admission", [GM, REM, grp("r", "offer", "Y", "agent", "community_invite",
                                                                                        cites=("xr",), content="xr")],
     "r", ("admit", "agent", "community")),
    ("the duty holders' conferral of moderate", [FH, grp("r", "offer", "B", "moderate", "duty_confer", counted="duty")], "r",
     ("duty_confer", "duty", "community")),
    ("a conferral of a duty the record declares", [FH, grp("r", "offer", "B", "verify", "duty_confer", counted="duty")], "r",
     ("duty_confer", "duty", "community")),
    ("a members' count conferring moderate (no election named) is a conferral by its shape, whatever it states",
     [GM, grp("r", "offer", "B", "moderate", "community_invite")], "r", ("duty_confer", "duty", "community")),
    ("the election's seating: an offer of a duty under the ranked count (the one act read from the stated policy, for "
     "this tag: the election is not answered safely by it)",
     [GM, grp("r", "offer", "B", "moderate", "moderator_election")], "r", ("election_seating", "moderate", "community")),
    ("an offer of moderate naming a row, under an admission's policy, is a conferral by its shape (no structural "
     "election in this tag)",
     [GM, grp("r", "offer", "B", "moderate", "community_invite", of="g")], "r", ("duty_confer", "duty", "community")),
    ("the holders' withdrawal: an unseat of a duty counted over the duty holders",
     [FH, grp("r", "unseat", "A", "moderate", "moderator_recall", counted="duty")], "r", ("duty_withdraw", "duty", "community")),
    ("the recall: an unseat of a duty counted over the members, whatever it states",
     [FH, grp("r", "unseat", "A", "moderate", "duty_withdraw")], "r", ("recall", "duty", "community")),
    ("the holders' conferral of a detector seat (CC 4.5.7)",
     [FH, grp("r", "offer", "N", "detect:list1", "duty_confer", counted="duty")], "r", ("seat_confer", "detect", "community")),
    ("the holders' withdrawal of a detector seat (CC 4.5.7: 'withdrawn by the count of (iv)')",
     [FH, grp("r", "unseat", "N", "detect:list1", "duty_withdraw", counted="duty")], "r", ("seat_withdraw", "detect", "community")),
    ("another scope that is no duty and no roster seat is no act",
     [FH, grp("r", "offer", "N", "verify2", "duty_confer", counted="duty")], "r", None),
    ("an accord's counted row is a standing act", [GA, grp("r", "offer", "h4", "holder", "accord_majority", counted="holder")], "r",
     ("standing_act", "any", "accord")),
    ("an accord's grant of another scope too", [GA, grp("r", "offer", "A2", "infra", "accord_majority", counted="holder")], "r",
     ("standing_act", "any", "accord")),
    ("a self roster's admission of a key", [GS, grp("r", "offer", "d4", "self", "self_roster_add", counted="self")], "r",
     ("admit", "key", "self")),
    ("a self roster's removal of a key", [GS, grp("r", "unseat", "d3", "key", "self_roster_evict", counted="self")], "r",
     ("remove", "key", "self")),
    ("a counted row over a key object is the self roster's", [grp("r", "offer", "K2", "key", "self_roster_add", heads=(), obj="KY")], "r",
     ("admit", "key", "self")),
    ("a row that is not counted is no act", [GM, ST.offer("r", "A", "D", "member", OBJ, "seat", ("g",), under="g")], "r", None),
    ("an object that is a row and no founding row has no kind",
     [CK.row("q", "note", "A", ()), grp("r", "offer", "D", "member", "community_invite", heads=(), obj="q", cites=("q",))], "r", None),
]

# (act, scope class, kind) -> (policy rows, choice), or None
QUERIES = [
    (("admit", "member", "community"), (("cosigned_act", "community_invite"), "row")),
    (("remove", "agent", "community"), (("community_remove",), "fixed")),
    (("duty_confer", "duty", "community"), (("duty_confer",), "fixed")),
    (("duty_withdraw", "duty", "community"), (("duty_withdraw",), "fixed")),
    (("recall", "duty", "community"), (("moderator_recall",), "fixed")),
    (("lift", "act", "community"), (("moderation_overturn",), "fixed")),
    (("lift", "agent", "community"), (("moderation_overturn",), "fixed")),
    (("seat_confer", "detect", "community"), (("duty_confer",), "fixed")),
    (("seat_withdraw", "detect", "community"), (("duty_withdraw",), "fixed")),
    (("election_seating", "moderate", "community"), (("moderator_election",), "fixed")),
    (("standing_act", "any", "accord"), (("accord_majority",), "fixed")),
    (("admit", "key", "self"), (("self_roster_add",), "fixed")),
    (("remove", "member", "affiliation"), (("affiliation_member_action", "cosigned_act"), "row")),
    (("admit", "member", "accord"), None),
    (("recall", "duty", "self"), None),
]

# The refusal (step 3): (name, rows, the row asked, concludes with the acts table, concludes with none)
GM4 = ST.offer("g", "A", ("A", "B", "C", "D"), "member", "@", "self", cosigners=("B", "C", "D"))      # two thirds
GMJ = ST.offer("g", "A", ("A", "B", "C", "D"), "member", "@", "self", cosigners=("B", "C", "D"), protocol="majority")
GN = ST.offer("g", "A", ("A", "B", "C", "D"), "member", "@", "self", cosigners=("B", "C", "D"), protocol=None)
CONCLUDE = [
    ("an admission stating accord_halt (one voice) is no admission's policy: with the table it concludes nothing",
     [GM4, grp("r", "offer", "E", "member", "accord_halt", cosigners=("E",))], "r", False, True),
    ("a removal stating cosigned_act: the removal's policy is fixed (community_remove), so nothing with the table; "
     "without it the room's protocol counts it (three of four)",
     [GM4, grp("r", "unseat", "D", "member", "cosigned_act", cosigners=("B", "C"))], "r", False, True),
    ("a removal stating none is counted under community_remove, the room's protocol: two thirds, three of four",
     [GM4, grp("r", "unseat", "D", "member", None, cosigners=("B", "C"))], "r", True, False),
    ("a removal under community_remove in a room of majority: A and B, two of four, are not more than half",
     [GMJ, grp("r", "unseat", "D", "member", "community_remove", cosigners=("B",))], "r", False, False),
    ("and A, B and C are: the room's protocol, not two thirds or one the row states",
     [GMJ, grp("r", "unseat", "D", "member", "community_remove", cosigners=("B", "C"))], "r", True, True),
    ("a removal in a room whose record declares no protocol concludes nothing, with the table or without",
     [GN, grp("r", "unseat", "D", "member", "community_remove", cosigners=("B", "C", "D"))], "r", False, False),
    ("an admission under cosigned_act is counted under the room's protocol (majority: three of four)",
     [GMJ, grp("r", "offer", "E", "member", "cosigned_act", cosigners=("B", "C", "E"))], "r", True, True),
    ("an admission under cosigned_act where the record declares no protocol concludes nothing",
     [GN, grp("r", "offer", "E", "member", "cosigned_act", cosigners=("B", "C", "D", "E"))], "r", False, False),
    ("an admission under community_invite (the two-path) is its own count: two thirds",
     [GMJ, grp("r", "offer", "E", "member", "community_invite", cosigners=("B", "C", "E"))], "r", True, True),
    ("a counted row of a scope that is no act over a community concludes nothing with the table",
     [FH, grp("r", "offer", "N", "verify2", "accord_halt")], "r", False, True),
    ("a detector seat's conferral stating accord_halt is refused (its policy is fixed: duty_confer)",
     [FH, grp("r", "offer", "N", "detect:list1", "accord_halt", counted="duty")], "r", False, True),
    ("an accord's counted row stating none is a standing act, counted under accord_majority",
     [GA, grp("r", "offer", "h4", "holder", None, counted="holder", cosigners=("h1", "h2", "h4"))], "r", True, False),
]

PLANTS = ("lift_unread", "election_unread", "recall_by_policy", "kind_unread", "key_kind_unread", "detect_unread",
          "binding_off", "stated_policy_free", "protocol_unread")


@contextlib.contextmanager
def planted(plant):
    saved = set(ST.MUT)
    if plant:
        ST.MUT.add(plant)
    try:
        yield
    finally:
        ST.MUT.clear(); ST.MUT |= saved


def answer(rows, rid, plant=None):
    by = {q["id"]: q for q in rows}
    r = by[rid]
    with planted(plant):
        return ST.act_of(r, by, is_key=r.get("obj") is not None and r.get("obj") not in by)


def concludes(rows, rid, bound, plant=None):
    saved = ST.BOUND
    ST.BOUND = bound
    try:
        with planted(plant):
            S = CK.concluded(CK.kept(list(rows)), lambda r, P, past: ST.seat_rule(r, P, past))
            return bool(S.C.get(rid))
    finally:
        ST.BOUND = saved


def main():
    problems = []
    for name, rows, rid, wb, wu in CONCLUDE:
        got = (concludes(rows, rid, True), concludes(rows, rid, False))
        if got != (wb, wu):
            problems.append("%s: got %s, expected %s" % (name, got, (wb, wu)))
    for name, rows, rid, want in CASES:
        got = answer(rows, rid)
        if got != want:
            problems.append("%s: got %s, expected %s" % (name, got, want))
    for q, want in QUERIES:
        got = ST.policy_for(*q)
        if got != want:
            problems.append("query %s: got %s, expected %s" % (q, got, want))
    caught = 0
    for plant in PLANTS:
        hit = [name for name, rows, rid, want in CASES if answer(rows, rid, plant) != want]
        hit += [c[0] for c in CONCLUDE if concludes(c[1], c[2], True, plant) != c[3]]
        caught += bool(hit)
        print("  plant %-16s %s" % (plant, "caught by %d cases, first: %s" % (len(hit), hit[0]) if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % plant)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases, %d queries, %d refusal cases, %d of %d planted breaks caught"
          % ("ok" if not problems else "%d problems" % len(problems), len(CASES), len(QUERIES), len(CONCLUDE), caught,
             len(PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
