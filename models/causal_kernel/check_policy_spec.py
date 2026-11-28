#!/usr/bin/env python3
"""
check_policy_spec.py: a window's table built from its policy row (window.spec_from_policy) against the tables the
reference writes by hand (window.WINDOWS, and roster.window_from_table's lone paths), over the reference's own
window scenarios.

Part 1. Every family of the policy table: the table spec_from_policy gives, or the cells it refuses on.

Part 2. Every reference table whose policy row gives one: the reference's table is swapped for the row's, and every
scenario that opens that window is concluded again. The scenarios: window.py's adversary worlds (of which
check_window_rows.py reads the #221 rows) under window.rule, and every world check_rosters.py's unmutated
properties conclude under roster.rule and its settle stage (the worlds tables.json carries). Read: every row's
conclusion, the settled conclusions, and every window's outcome under recount. Each difference is listed in
DIFFERS with the side the table supports; a difference not listed, or a listed one that no longer differs, fails.

Part 3. Plants: for every cell spec_from_policy reads, the cell changed in one row must change what that row gives.

    python3 -I check_policy_spec.py      exit 1 on any unlisted difference or an uncaught plant
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import window as WN  # noqa: E402
import roster as RS  # noqa: E402

CK, K = WN.CK, WN.K
POL = WN.policy_table()
TABLE = {f["family"]: f for f in POL["families"]}

# The reference's tables that no policy row is meant to give: tables built to reach a path (window.py says so)
BUILT = {"ballot@once", "proposal@others", "holders@count"}

# Each reference table that differs from its row's (in a clause, or in an outcome over a scenario), with what differs
# and the side the table supports. The rows of policy pin 85750784 (CIRISConstitution 0e80f21), after the rulings of
# 2026-11-27 and 2026-11-28 (policy pin 85750784, CIRISConstitution 0e80f21, carries them).
DIFFERS = {
    "moderation_fallback": "the table before the ruling of 2026-11-28 (a moderator's `answered`, the members' `fallback`, "
                           "the default `lapsed`); the row's table is moderation_action, a moderator's ballot `for` "
                           "landed and `against` refused at once, two that disagree resolving nothing, the members' "
                           "count at the close, the default `refused`. The window adversary table runs both",
    "halt_fuse": "refused: the row's concluder is `local` (each node's own fuse, no landing), RULED 2026-11-28; the "
                 "reference now has the same (no landing of it concludes; the halt fires and is no confirming voice); "
                 "its confirmation, a strict majority of the standing holders, is a separate cosigned row, which the "
                 "reference reads as `confirm` answers met at once",
    "L:community_add:majority": "the enact: the row's is strictly more than 2/3 of the base with min_count voices; the "
                                "reference enacts by the room's declared protocol (CC 3.1.3.2). RULED 2026-11-27: two "
                                "paths. The reference is the cosigned_act path (the declared protocol and the joiner's "
                                "acceptance), 0.5.0's; the community_invite row is the window path (one proposer, the full "
                                "roster, strictly more than 2/3 with its floor), post-tag. The cancel, the default and the "
                                "floor are the row's now (`refused`)",
    "L:community_add:two_thirds": "as L:community_add:majority: the reference enacts at least 2/3 with no floor",
    "L:community_add:quorum:2": "as L:community_add:majority; and the reference's enact, the declared quorum read as "
                                "(`atleast`, 0, 0), is no count a window can read (it divides by zero; no scenario reads "
                                "the table)",
}
# The words: the row's answers say assent and raised (objection:{state}) and its landings state the leaves; the
# reference writes approve and object, and its own reading words for some leaves (landed_means, refused_means). The
# row's table is run in the reference's words, so a scenario reads it as it reads the reference's.
WORDS = {"assent": "approve", "raised": "object"}
READING = {"moderation_overturn": {"landed": "lifted", "refused": "stands"}}


def family_of(name, spec):
    """The policy row, the `active` argument and the seat the reference's table `name` reads."""
    fam = spec["policy"]
    row = TABLE.get(fam, {})
    active = None
    if row.get("base") == "active" and row.get("stated_census") is None:
        rest = name.split("@")
        if len(rest) == 2 and rest[1] == "active":
            active = ("census", WN.ACTIVE)
        elif len(rest) == 3:
            active = ("census", int(rest[2]))
        else:
            active = "within_k"
    seat = spec["counted"] if "+" in row.get("counted", {}).get("count_set", {}).get("value", "") else None
    return fam, active, seat


def in_words(d, fam):
    """The row's table d in the reference's words: answers by WORDS, leaves by READING."""
    out_w = READING.get(fam, {})
    v = lambda w: WORDS.get(w, w)
    o = lambda w: out_w.get(w, w)
    how = lambda h: tuple(v(x) if isinstance(x, str) else x for x in h) if isinstance(h, tuple) else h
    cl = lambda cs: tuple((v(a), how(h), b, o(x)) for a, h, b, x in cs)
    return dict(d, opener_says=v(d["opener_says"]) if d["opener_says"] else None, at_once=cl(d["at_once"]),
                at_close=cl(d["at_close"]), silent=o(d["silent"]) if d["silent"] else None, default=o(d["default"]))


def derived(name):
    spec = WN.WINDOWS[name]
    fam, active, seat = family_of(name, spec)
    if fam not in TABLE:
        return None, "no policy row %s" % fam
    try:
        d = WN.spec_from_policy(TABLE[fam], POL, active, seat)
    except WN.PolicyRefusal as e:
        return None, e.reasons
    d.pop("secs")
    return in_words(d, fam), None


# ---- the scenarios -------------------------------------------------------------------------------------
def adversary_worlds():
    out = []
    for world in WN.WORLDS:
        title, cases = world()
        for case, rows, _, _ in cases:
            out.append(("window: %s: %s" % (title, case), list(rows), "window"))
    return out


def roster_worlds():
    """Every world check_rosters.py's unmutated properties conclude (as tools/kernel_fixtures.py's tables fixture
    collects them), with the window names each opens."""
    import check_rosters as CR
    import contextlib
    depth = {"n": 0}
    orig_mut, orig_state, orig_run = CR.mutated, RS.state, CR.run

    @contextlib.contextmanager
    def mutated(*a, **kw):
        depth["n"] += 1
        try:
            with orig_mut(*a, **kw):
                yield
        finally:
            depth["n"] -= 1
    worlds, seen = [], set()

    def state(rows):
        if depth["n"] == 0 and not RS.MUT and not RS.PARAMS:
            key = json.dumps([sorted(map(str, r.items())) for r in rows])
            if key not in seen:
                seen.add(key)
                worlds.append(list(rows))
        return orig_state(rows)
    CR.mutated, RS.state = mutated, state
    CR.run = lambda spec, worlds_, pred, orders=True, windows=lambda rows: (): orig_run(spec, worlds_, pred, False, windows)
    try:
        for name in CR.TASKS:
            if name.startswith("fork_"):
                continue
            RS.MUT.clear(); RS.PARAMS.clear()
            CR.TASKS[name](RS.instances())
    finally:
        CR.mutated, RS.state, CR.run = orig_mut, orig_state, orig_run
        RS.MUT.clear(); RS.PARAMS.clear()
    return [("roster world %d" % i, rows, "roster") for i, rows in enumerate(worlds)]


def opens(rows):
    return {r.get("window") for r in rows if WN.is_opener(r)} - {None}


def answers(rows, how):
    if how == "window":
        S = CK.concluded(CK.kept(list(rows)), WN.rule)
        return ({r["id"]: bool(S.C.get(r["id"])) for r in S.rows}, WN.outcome(S, "p", "recount") if "p" in S.by else None)
    S = CK.concluded(CK.kept(list(rows)), RS.rule)
    P = RS.settle(S)
    wins = {p["id"]: WN.outcome(P, p["id"], "recount") for p in P.Cs if WN.is_opener(p) and p.get("window") in WN.WINDOWS}
    return ({r["id"]: bool(S.C.get(r["id"])) for r in S.rows}, {r["id"]: bool(P.C.get(r["id"])) for r in P.rows}, wins)


# ---- the clauses, and scenarios that part them -----------------------------------------------------------
FIELDS = ("counted", "concluder", "opener", "opener_says", "at_once", "silent", "at_close", "default", "target_votes")


def clause_diff(ref, mine):
    """The fields of two tables that differ (a field a table leaves out reads as window.py reads it)."""
    get = lambda w, k: tuple(w.get(k, ())) if k in ("at_once", "at_close") else w.get(k, False if k == "target_votes" else None)
    return [k for k in FIELDS if get(ref, k) != get(mine, k)]


def separating():
    """Scenarios that part a reference table from its row's where no scenario of the reference does: (name, case,
    rows, what the reference gives, what the row gives). Each runs under window.rule, outcome under recount."""
    ST = WN.ST
    out = []
    # a room of three: two approve at once (the declared protocol's strict majority; the row's strictly more than 2/3)
    m = ST.offer("g", "m1", ("m1", "m2", "m3"), "member", "@", "self", cosigners=("m2", "m3"))
    for name in ("L:community_add:majority",):
        out.append((name, "a room of three: the proposer and one member approve, no landing",
                    [m, WN.opener("p", "m1", name, "g", ("g",)), WN.answer("a2", "m2", "p", "approve")], "landed", "open"))
    return out


# ---- the dump: per policy row, what the reference derives today and from which cell ------------------------------
ROSTER_SOURCE = {        # roster.window_from_table: where each field of a lone path's table comes from
    "counted": "caller: the roster instance's scope (roster.instances), no cell",
    "concluder": "caller: the roster instance's scope, as counted; no cell",
    "opener": "none: the counted scope; no cell",
    "opener_says": "hand-written `approve`; no cell",
    "at_once": "enact_rule (count_kind; community: the room's declared protocol, CC 3.1.3.2), over `all`, word "
               "`landed` hand-written; cancel_rule strict_majority_of_others, over `others`, word `refused` hand-written",
    "silent": "counted.target_silent (with the caller's evict flag), word `refused` hand-written",
    "at_close": "cancel_rule fraction with min_count[corridor], over `all`, `refused`; floor_rule fraction with "
                "reverse_path and min_count[corridor], over `all`, `landed`",
    "default": "floor_rule: one_of_n gives `landed`, otherwise `refused`; at_window unread",
    "target_votes": "counted.target_voice",
    "secs": "window_secs (by the family's row)",
}
HAND = "hand-written in window.py WINDOWS; no cell read"
ROW_SOURCE = {           # window.spec_from_policy: where each field comes from
    "counted": "counted.count_set (the seat, where it names several: self+key)",
    "concluder": "concluder (a scope word of the count set; -proposer: the opener's signer apart, by author_apart)",
    "opener": "opener (none where it is the counted scope)",
    "opener_says": "opener_says (approve: the yes of answer_words; nothing: none)",
    "at_once": "enact_rule with comparison.enact over base (others for -proposer), `landed`; corridor self: the "
               "withdrawal (CC 3.3.6.4) and cancel_rule over cancel_over, `refused`; the words of answer_words",
    "silent": "counted.target_silent (changes_set removes): `refused`",
    "at_close": "two_path: cancel_rule with comparison.cancel over cancel_over (not corridor self), `refused`; enact_rule "
                "if irreversible; floor_rule with comparison.floor and reverse_path, `landed`, unless default_at_close is "
                "`landed`; mirror voted_majority: a ballot's for over those who voted",
    "default": "default_at_close",
    "target_votes": "counted.target_voice (changes_set adds)",
    "secs": "window_secs (window_class must agree)",
}
# the hand-written mirror tables: the cell or text each field matches, though nothing reads it
MIRROR_SOURCE = {
    "moderation_overturn": {
        "counted": "counted.count_set `member` (hand-written; matches)",
        "concluder": "no cell; CC 4.5.13 (door_text): `member but the author`, the author apart by author_apart",
        "opener": "no cell; the act is the opener: `moderate`, the duty holder's act (kind mirror, CC 4.5.13)",
        "opener_says": "no cell; none (the act's author is no voice)",
        "at_once": "enact_rule strict_majority + floor_rule voices 2 -> (more, 1, 2, 2); base `others` from standing_set "
                   "`less the act's author` (count_set has no -proposer); value `object` from voices objection "
                   "(raised); outcome `lifted`: no cell",
        "silent": "counted.target_silent `no`",
        "at_close": "none: cancel_rule none; reverse_path false",
        "default": "no cell: `stands` (at_window reads `lapsed`: the lift lapses, the act stands)",
        "target_votes": "counted.target_voice `no`",
    },
    "moderation_fallback": {
        "counted": "counted.count_set `member`",
        "concluder": "no cell; CC 4.5.13: any member lands the fallback",
        "opener": "no cell; a member raising the action (counted scope)",
        "opener_says": "no cell; none",
        "at_once": "enact_rule role_at moderate 1 -> (answered, one, moderate, answered): the words `answered` have no "
                   "cell (counted.voices `unstated`)",
        "silent": "counted.target_silent `no`",
        "at_close": "floor_rule voted_majority 2 -> (for, (voted, 1, 2, 2, against), all, fallback): ballot "
                    "`ballot:moderation_action` for/against (CIRISConstitution#221); words have no cell",
        "default": "no cell: `lapsed` (at_window reads `tallied`)",
        "target_votes": "counted.target_voice `no`",
    },
    "halt_fuse": {
        "counted": "counted.count_set `holder`",
        "concluder": "no cell; a holder (door.py reads the halted node instead)",
        "opener": "no cell; the halt is the opener (enact_rule one_of_n: one holder fires)",
        "opener_says": "no cell; `confirm` (the halting holder's own confirmation)",
        "at_once": "cancel_rule strict_majority (`more than 1/2 confirms`) over base -> (confirm, strict, all, "
                   "confirmed); voices `scrubs` read as answers; words have no cell",
        "silent": "counted.target_silent `no`",
        "at_close": "none: floor_rule none",
        "default": "at_window `lapsed`",
        "target_votes": "counted.target_voice `no`",
    },
}
DUMP_FIELDS = ("counted", "concluder", "opener", "opener_says", "at_once", "silent", "at_close", "default",
               "target_votes", "secs")


def dump():
    """Per policy row: every reference table that reads it, each field's value and where it comes from; the table
    spec_from_policy gives from the row (or the cells it refuses on); and the fields where the two disagree."""
    RS.instances()
    for p in ("two_thirds", "quorum:2"):
        RS.instances(p)
    RS.instances()
    out = {}
    for f in POL["families"]:
        fam = f["family"]
        g = give(f)
        row = {"spec": None, "refused": None}
        if g[0] == "spec":
            row["spec"] = {k: {"value": g[1].get(k), "from": ROW_SOURCE[k]} for k in DUMP_FIELDS}
        else:
            row["refused"] = [list(r) for r in g[1]]
        refs = {}
        for name in sorted(WN.WINDOWS):
            w = WN.WINDOWS[name]
            if w["policy"] != fam:
                continue
            src = (ROW_SOURCE if TABLE[fam]["corridor"] == "self" else ROSTER_SOURCE) if name.startswith("L:") \
                else {k: HAND for k in DUMP_FIELDS}
            if name in MIRROR_SOURCE:
                src = {k: HAND + "; " + MIRROR_SOURCE[name][k] for k in MIRROR_SOURCE[name]}
            if not name.startswith("L:"):
                src = dict(src, secs="window_secs (window.secs, by the family's row)")
            vals = dict(w, secs=WN.secs(name))
            ref = {"built_for_a_path": name in BUILT,
                   "fields": {k: {"value": vals.get(k, False if k == "target_votes" else None), "from": src[k]}
                              for k in DUMP_FIELDS}}
            d, _ = derived(name)
            if d is not None:
                ref["differs_from_row"] = clause_diff(w, d)
            ref["note"] = DIFFERS.get(name)
            refs[name] = ref
        out[fam] = {"cells": f, "row_gives": row, "reference": refs}
    return {"source": "data/governance_policy.json (CIRISConstitution manifests/governance_policy.json)",
            "policy_sha256": POL["_meta"]["policy_sha256"],
            "reading": "per family: `cells` the row as the table carries it; `row_gives` window.spec_from_policy's table "
                       "(each field's value and the cell it comes from) or the cells it refuses on; `reference` every "
                       "table the reference runs under that family today, each field's value and where it comes from, "
                       "and `differs_from_row` the fields that differ from the row's table",
            "families": out}


# ---- the act binding: an opener's table through the acts table ------------------------------------------------------
def families(fam, obj, seat):
    """A family's table from its row (window.FAMILIES), in the reference's words: the base `active` read within k;
    the seat the object's founding row seats, where the count set names several."""
    row = TABLE.get(fam)
    if row is None: return None
    several = "+" in row["counted"]["count_set"]["value"].split("-")[0]
    try:
        d = WN.spec_from_policy(row, POL, "within_k" if row["base"] == "active" and row["stated_census"] is None else None,
                                seat if several else None)
    except WN.PolicyRefusal:
        return None
    return in_words(d, fam)


def bind(p, act, scope, **kw):
    """Opener p proposing (act, scope), under a window name no table has: the binding alone gives its table."""
    return dict(p, proposes=(act, scope), window="unbound", **kw)


def bound_cases():
    """(name, rows, the by-name rows or None, the outcome the binding must give or None): the self roster's lone
    paths with their openers bound (each must give what the by-name table gives), and a room's openers bound to a
    family that gives a table, to one that does not, and to none."""
    out = []
    for world, act in ((WN.self_world, "remove"), (WN.add_world, "admit")):
        _, cases = world()
        for case, rows, _, _ in cases:
            out.append(("bound, %s: %s" % (act, case), [bind(r, act, "key") if r["id"] == "p" and r["kind"] == "open" else r
                                                         for r in rows], rows, None))
    ST = WN.ST
    m = ST.offer("g", "m1", ("m1", "m2", "m3"), "member", "@", "self", cosigners=("m2", "m3"))
    op = WN.opener("p", "m1", "x", "g", ("g",))
    a = lambda i, who: WN.answer(i, who, "p", "approve")
    W = TABLE["default_content"]["window_secs"]
    out += [
        # default_content's opener: a member (ruled 2026-11-28; pin 85750784)
        ("a room's content change, two of three approve: strictly more than 2/3 needs three",
         [m, bind(op, "change", "content"), a("a2", "m2")], None, "open"),
        ("a room's content change, three of three approve", [m, bind(op, "change", "content"), a("a2", "m2"), a("a3", "m3")],
         None, "landed"),
        ("a room's content change, two of three approve and a member lands the floor at the close",
         [m, bind(op, "change", "content"), a("a2", "m2"), WN.receipt("r", "m2", "p", 0),
          WN.landing("L", "m2", "p", "r", "landed", W, ("a2",))], None, "landed"),
        ("a room's content change, the proposer alone and a member lands at the close: the floor is two voices",
         [m, bind(op, "change", "content"), WN.receipt("r", "m2", "p", 0), WN.landing("L", "m2", "p", "r", "landed", W)],
         None, "open"),
        ("an opener that proposes nothing is bound to no family", [m, dict(op, window="unbound"), a("a2", "m2")], None, "none"),
        ("an opener the name alone would bind: the binding reads no name",
         [m, dict(op, window="default_content@active"), a("a2", "m2"), a("a3", "m3")], None, "none"),
        ("a removal's opener: community_remove is a counted row, no window", [m, bind(op, "remove", "member")], None, "none"),
        ("an admission stating community_invite, two of three approve", [m, bind(op, "admit", "member", policy="community_invite"),
                                                                          a("a2", "m2")], None, "open"),
        ("an admission stating community_invite, three of three approve",
         [m, bind(op, "admit", "member", policy="community_invite"), a("a2", "m2"), a("a3", "m3")], None, "landed"),
        ("an admission stating cosigned_act: a counted row, no window",
         [m, bind(op, "admit", "member", policy="cosigned_act"), a("a2", "m2"), a("a3", "m3")], None, "none"),
        ("an admission stating no policy, where the row chooses", [m, bind(op, "admit", "member"), a("a2", "m2"), a("a3", "m3")],
         None, "none"),
        ("a content change stating another policy than the fixed one",
         [m, bind(op, "change", "content", policy="default_standing"), a("a2", "m2"), a("a3", "m3")], None, "none"),
        ("a record change: two counts at once is no window", [m, bind(op, "record_change", "record"), a("a2", "m2")], None, "none"),
        ("an act the acts table has no row for over a room", [m, bind(op, "halt_confirm", "halt"), a("a2", "m2")], None, "none"),
    ]
    return out


def run_bound(rows):
    saved = WN.FAMILIES
    WN.FAMILIES = families
    try:
        with WN.ST.binding(True):
            S = CK.concluded(CK.kept(list(rows)), WN.rule)
            return {r["id"]: bool(S.C.get(r["id"])) for r in S.rows}, WN.outcome(S, "p", "recount")
    finally:
        WN.FAMILIES = saved


# ---- plants: one cell changed, read in one row ---------------------------------------------------------
def _set(row, path, v):
    row = copy.deepcopy(row)
    *head, last = path.split(".")
    d = row
    for h in head:
        d = d[h]
    d[last] = v
    return row


PLANTS = (
    # (cell, family, new value): what the row gives must change. default_* rows are read with their opener (`unstated`
    # in the table) filled as `member`, so that a cell changed in them changes a table
    ("concluder", "self_roster_add", "member"),
    ("concluder", "moderation_overturn", "member"),
    ("concluder", "community_invite", "local"),
    ("opener", "moderation_overturn", "member"),
    ("opener", "community_invite", "unstated"),
    ("opener_says", "community_invite", "nothing"),
    ("outcome_words", "community_invite", ["landed"]),
    ("answer_words", "moderation_overturn", ["assent", "raised"]),
    ("answer_words", "community_invite", ["for", "against"]),
    ("default_at_close", "community_invite", "landed"),
    ("comparison.enact", "community_invite", "at_least"),
    ("comparison.cancel", "community_invite", "more_than"),
    ("comparison.floor", "community_invite", "more_than"),
    ("stated_census", "community_invite", 9),
    ("counted.count_set.value", "self_roster_add", "member+key"),
    ("kind", "self_roster_add", "cosigned"),
    ("standing_set", "self_roster_add", "the live roster keys of one fedID, less the proposer"),
    ("base", "default_content", "standing", ("census", 20)),
    ("enact", "default_content", {"num": 1, "den": 2}),
    ("cancel", "default_content", None),
    ("floor", "default_content", {"num": 1, "den": 4}),
    ("enact_rule.num", "default_content", 3),
    ("cancel_rule.den", "default_content", 4),
    ("floor_rule.kind", "self_roster_add", "none"),
    ("counted.count_set.value", "default_content", "holder"),
    ("counted.voice.value", "default_content", "key"),
    ("counted.counted_at.value", "default_content", "signed"),
    ("counted.voices.value", "default_content", "ballot"),
    ("counted.target_silent.value", "self_roster_evict", "no"),
    ("counted.changes_set.value", "self_roster_evict", "adds"),
    ("counted.target_voice.value", "community_invite", "no"),
    ("cancel_over", "self_roster_add", "base"),
    ("window_secs", "default_content", 172800),
    ("window_class", "default_content", "ruled_48h"),
    ("irreversible", "default_content", True),
    ("reverse_path", "default_content", False),
    ("corridor", "self_roster_add", "community"),
    ("family", "default_content", "default_renamed"),
    ("min_count.community", None, 3),
    ("window_classes.content_24h", None, 3600),
)


def seat_of(row):
    """The seat a row of several (`self+key`) is read for here: the self roster's."""
    return "self" if "+" in row["counted"]["count_set"]["value"].split("-")[0] else None


def give(row, table=POL, active=None):
    if active is None and row.get("base") == "active" and row.get("stated_census") is None:
        active = "within_k"
    try:
        return ("spec", WN.spec_from_policy(row, table, active, seat_of(row)))
    except WN.PolicyRefusal as e:
        return ("refused", e.reasons)


def plant_base(fam):
    row = TABLE[fam]
    return dict(row, opener="member") if row["opener"] == "unstated" else row


def run_plants():
    caught, out = 0, []
    for cell, fam, v, *act in PLANTS:
        a = act[0] if act else None
        if fam is None:                       # a cell of the table, read for every row
            t = _set(POL, cell, v)
            hit = [f["family"] for f in POL["families"] if give(f, t) != give(f)]
        else:
            base = plant_base(fam)
            hit = [fam] if give(_set(base, cell, v), POL, a) != give(base, POL, a) else []
        caught += bool(hit)
        out.append((cell, fam, v, hit))
    return caught, out


def main():
    problems = []
    # seat.py's table readers, called after import with no path, read the repository's data/ (ROOT is the path)
    ST = WN.ST
    try:
        if ST.policy_table() != ST.policy_table(os.path.join(ST.ROOT, "data", "governance_policy.json")) \
                or ST.removal_floor() != ST.REMOVAL_FLOOR or ST.acts_table() != ST.ACTS:
            problems.append("seat.py's table readers read another table with no path")
    except TypeError as e:
        problems.append("seat.py's table readers fail with no path: %s" % e)
    print("Part 1. the families of the policy table")
    for f in POL["families"]:
        g = give(f)
        print("  %-26s %s" % (f["family"], "a table" if g[0] == "spec" else "refused: " + "; ".join(
            "%s %s%s" % (c, w, " (%s)" % o if o else "") for c, w, o in g[1])))
    worlds = adversary_worlds() + roster_worlds()
    RS.instances()
    for p in ("two_thirds", "quorum:2"):
        RS.instances(p)
    RS.instances()
    names = sorted(WN.WINDOWS)
    print("\nPart 2. the reference's tables against their rows' (%d scenarios)" % len(worlds))
    differ = {}
    for name in names:
        if name in BUILT:
            print("  %-34s built for a path, no row's table" % name)
            continue
        d, why = derived(name)
        mine = [(t, rows, how) for t, rows, how in worlds if name in opens(rows)]
        if d is None:
            print("  %-34s refused (%d scenarios read it): %s" % (name, len(mine), why))
            differ[name] = ["refused"]
            continue
        before = [answers(rows, how) for _, rows, how in mine]
        saved = WN.WINDOWS[name]
        WN.WINDOWS[name] = d
        try:
            after = [answers(rows, how) for _, rows, how in mine]
        finally:
            WN.WINDOWS[name] = saved
        bad = [t for (t, _, _), a, b in zip(mine, before, after) if a != b]
        cd = clause_diff(saved, d)
        print("  %-34s %d scenarios, %d differ%s%s" % (name, len(mine), len(bad), (": first " + bad[0][:110]) if bad else "",
                                                     "; clauses differ: " + ", ".join(cd) if cd else ""))
        if bad or cd:
            differ[name] = bad or cd
    print("\n  scenarios that part a reference table from its row's:")
    for name, case, rows, want_ref, want_row in separating():
        got = []
        for table in ("reference", "row"):
            saved = WN.WINDOWS[name]
            if table == "row":
                WN.WINDOWS[name] = derived(name)[0]
            try:
                S = CK.concluded(CK.kept(list(rows)), WN.rule)
                got.append(WN.outcome(S, "p", "recount"))
            finally:
                WN.WINDOWS[name] = saved
        ok = got == [want_ref, want_row]
        print("    %-34s %s: reference %s, row %s%s" % (name, case, got[0], got[1], "" if ok else "  (WANT %s, %s)" % (want_ref, want_row)))
        if not ok:
            problems.append("a separating scenario gives another answer: %s: %s" % (name, case))
    for name in sorted(set(differ) | set(DIFFERS)):
        if name in differ and name not in DIFFERS:
            problems.append("an unlisted difference: %s" % name)
        elif name in DIFFERS and name not in differ and name in WN.WINDOWS:
            problems.append("listed as differing and it does not: %s" % name)
    print("\n  the differences, and the side the table supports:")
    for name, why in DIFFERS.items():
        print("    %s: %s" % (name, why))
    print("\nPart 4. the act binding (window.FAMILIES, the acts table)")
    nb = 0
    for name, rows, ref, want in bound_cases():
        got = run_bound(rows)
        if ref is not None:
            S = CK.concluded(CK.kept(list(ref)), WN.rule)
            exp = WN.outcome(S, "p", "recount")
            ok = got[1] == exp
        else:
            exp, ok = want, got[1] == want
        nb += 1
        if not ok:
            problems.append("bound: %s: %s, want %s" % (name, got[1], exp))
            print("  %s: %s, WANT %s" % (name, got[1], exp))
    print("  %d bound cases" % nb)
    print("\nPart 5. at_window is the text's description: no value of it changes what any row gives (ruled 2026-11-28)")
    words = sorted({f["at_window"] for f in POL["families"]} | {"dropped", "open", "cancelled"})
    moved = [(f["family"], w) for f in POL["families"] for w in words if give(dict(f, at_window=w)) != give(f)]
    print("  %d rows x %d words: %s" % (len(POL["families"]), len(words), "none moves" if not moved else moved[:3]))
    if moved:
        problems.append("at_window read: %s" % moved[:3])
    counted = [f["family"] for f in POL["families"] if f["kind"] == "cosigned" and give(f)[0] == "spec"]
    if counted:
        problems.append("a counted row gives a window: %s" % counted)
    print("  every counted row (kind cosigned) is refused, not_a_window: no window, it stays open")
    # the plant: a holder lands a local close (MUTATION local_lands) must break a row of the ruled halt
    WN.MUT.add("local_lands")
    try:
        hit = [t["case"] for t in WN.adversary_table() if t["window"].startswith("the accord") and t["needs"] is not None
               and not t["holds"]["recount"]]
    finally:
        WN.MUT.discard("local_lands")
    print("  plant local_lands: %s" % ("caught by %d rows" % len(hit) if hit else "NOT CAUGHT"))
    # the ruling on moderation_action: two moderators' ballots that disagree resolve nothing
    WN.MUT.add("holders_disagree_unread")
    try:
        hit = [t["case"] for t in WN.adversary_table() if t["needs"] is not None and not t["holds"]["recount"]]
    finally:
        WN.MUT.discard("holders_disagree_unread")
    print("  plant holders_disagree_unread: %s" % ("caught by %d rows" % len(hit) if hit else "NOT CAUGHT"))
    if not hit:
        problems.append("plant holders_disagree_unread not caught")
    if not hit:
        problems.append("plant local_lands not caught")
    print("\nPart 3. plants")
    caught, out = run_plants()
    for cell, fam, v, hit in out:
        print("  plant %-28s %-18s %s" % (cell, fam or "(table)", "caught" if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % cell)
    for p in problems:
        print(p)
    print("RESULT: %s: %d families, %d give a table; %d reference tables, %d differ (all listed); %d scenarios; "
          "%d of %d plants caught" % ("ok" if not problems else "%d problems" % len(problems), len(POL["families"]),
                                      sum(give(f)[0] == "spec" for f in POL["families"]), len(names) - len(BUILT),
                                      len(differ), len(worlds), caught, len(PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
