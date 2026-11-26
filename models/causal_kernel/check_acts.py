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

PLANTS = ("lift_unread", "election_unread", "recall_by_policy", "kind_unread", "key_kind_unread", "detect_unread")


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


def main():
    problems = []
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
        caught += bool(hit)
        print("  plant %-16s %s" % (plant, "caught by %d cases, first: %s" % (len(hit), hit[0]) if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % plant)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases, %d queries, %d of %d planted breaks caught"
          % ("ok" if not problems else "%d problems" % len(problems), len(CASES), len(QUERIES), caught, len(PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
