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
BUILT = {"ballot@once", "proposal@others"}

# Each reference table that differs from its row's (in a clause, or in an outcome over a scenario), with what differs
# and the side the table supports
SELF = ("the enact is strictly more than 1/2 with min_count (self, one) voices, as the reference's strict majority; "
        "the lone path is the floor's one voice at the close (floor_rule one_of_n) and the default `refused` "
        "(at_window), where the reference's default is `landed`. They part where the proposer's own answer is not an "
        "approval: the proposer objects to its own proposal and lands it. The decider supports the row: voices 0 is "
        "below floor_votes 1, so `cancelled` (the self roster's word `refused`)")
DIFFERS = {
    "moderation_fallback": "refused: moderation_action's voices cell is `unstated`, and a mirror row has no cell for its "
                           "answer words (`answered`, `for`, `against`) or outcome words (`answered`, `fallback`, `lapsed`; "
                           "at_window reads `tallied`). The reference's words are its own; the table states none",
    "moderation_overturn": "refused: count_set `member` has no `-proposer`, while standing_set reads `less the act's author` "
                           "(the reference counts over `others`, as CC 4.5.13's text and standing_set do); and the outcome "
                           "words `lifted` and `stands` have no cell (at_window reads `lapsed`). The table's count_set "
                           "supports counting the author; its standing_set and the text support the reference",
    "halt_fuse": "refused: accord_halt's counted_at is `unstated`, its voices are `scrubs` (cosignatures of one row, not "
                 "answers), and a mirror row has no cell for `confirm`, `confirmed` or `lapsed` (at_window `lapsed`)",
    "L:community_add:majority": "the row's enact is strictly more than 2/3 of the base with min_count voices (the decider: "
                                "enact_votes = num*base//den + 1, voices >= min_count); the reference enacts by the room's "
                                "declared protocol (CC 3.1.3.2, majority: a strict majority, no floor). The cancel and "
                                "the default are `cancelled` (at_window) where the reference says `refused`. The table "
                                "supports the row's reading: its enact_rule is a fraction, not `protocol`",
    "L:community_add:two_thirds": "as L:community_add:majority: the reference enacts at least 2/3 with no floor (the declared "
                                  "protocol), the row strictly more than 2/3 with two voices; `cancelled` for `refused`",
    "L:community_add:quorum:2": "as L:community_add:majority; and the reference's enact, the declared quorum read as "
                                "(`atleast`, 0, 0), is no count a window can read (it divides by zero; no scenario reads "
                                "the table). The row's is strictly more than 2/3 with two voices",
    "default_content@active": "the enact: the reference reads at least 2/3 of the stated count, the row strictly more than "
                              "2/3 (the decider's enact_votes); they part where 2/3 of the count is whole. The table supports "
                              "the row",
    "default_content@active@5": "as default_content@active",
    "default_content@active@4294967296": "as default_content@active; no scenario parts them, as 2/3 of the count is not whole",
    "default_content@active@4294967309": "as default_content@active; no scenario parts them, as 2/3 of the count is not whole",
    "self_roster_add": SELF,
    "self_roster_evict": SELF,
    "L:self_add": SELF,
    "L:self_evict": SELF,
    "L:voice_add": "the scope: no row is a voice's room keys (CC 3.1.3.2 reads them `as a key of a self roster is`); the row "
                   "self_roster_add counts `self` and the reference `key`. Run under the scope `key`, as self_roster_add: " + SELF,
    "L:voice_evict": "as L:voice_add, for self_roster_evict",
}
# where a difference above is the scope alone, the row's table is run under the caller's scope name
RENAME = {"L:voice_add": "key", "L:voice_evict": "key"}


def family_of(name, spec):
    """The policy row and the `active` argument the reference's table `name` reads."""
    fam = spec["policy"]
    active = None
    if TABLE.get(fam, {}).get("base") == "active":
        rest = name.split("@")
        if len(rest) == 2 and rest[1] == "active":
            active = ("census", WN.ACTIVE)
        elif len(rest) == 3:
            active = ("census", int(rest[2]))
        else:
            active = "within_k"
    return fam, active


def derived(name):
    spec = WN.WINDOWS[name]
    fam, active = family_of(name, spec)
    if fam not in TABLE:
        return None, "no policy row %s" % fam
    try:
        d = WN.spec_from_policy(TABLE[fam], POL, active)
    except WN.PolicyRefusal as e:
        return None, e.reasons
    d.pop("secs")
    if name in RENAME:
        d = dict(d, counted=RENAME[name], concluder=RENAME[name])
    return d, None


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
    # the self roster: the proposer objects to its own proposal, and lands it at the close
    g = ST.offer("g", "d1", ("d1", "d2", "d3"), "self", "@", "self", cosigners=("d2", "d3"))
    for name in ("self_roster_evict", "self_roster_add", "L:self_evict", "L:self_add"):
        W = WN.secs(name)
        out.append((name, "the proposer objects to its own proposal and lands it at the close",
                    [g, WN.opener("p", "d1", name, "g", ("g",), target="d4" if "add" in name else "d2"),
                     WN.answer("o1", "d1", "p", "object"), WN.receipt("r", "d1", "p", 0),
                     WN.landing("L", "d1", "p", "r", "landed", W, ("o1",))], "landed", "open"))
    # a room of three: two approve at once; two object and a member lands `refused` at the close
    m = ST.offer("g", "m1", ("m1", "m2", "m3"), "member", "@", "self", cosigners=("m2", "m3"))
    for name in ("L:community_add:majority",):
        out.append((name, "a room of three: the proposer and one member approve, no landing",
                    [m, WN.opener("p", "m1", name, "g", ("g",)), WN.answer("a2", "m2", "p", "approve")], "landed", "open"))
    for name in ("L:community_add:majority", "L:community_add:two_thirds"):
        W = WN.secs(name)
        out.append((name, "a room of three: two members object and one lands `refused` at the close",
                    [m, WN.opener("p", "m1", name, "g", ("g",)), WN.answer("o2", "m2", "p", "object"),
                     WN.answer("o3", "m3", "p", "object"), WN.receipt("r", "m2", "p", 0),
                     WN.landing("L", "m2", "p", "r", "refused", W, ("o2", "o3"))], "refused", "open"))
    # the base active, where 2/3 of the count is whole: thirteen members over a stated fifteen (a table built here, as
    # window.py builds @5), and twelve members over a stated five (the members, never fewer); ten and eight approve
    ref = WN.WINDOWS["default_content@active"]
    WN.WINDOWS["default_content@active@15"] = dict(
        ref, at_once=tuple((v, h, ("stated", 15), o) for v, h, _, o in ref["at_once"]),
        at_close=tuple((v, h, ("stated", 15), o) for v, h, _, o in ref["at_close"]))
    for name, n, yes in (("default_content@active@15", 13, 10), ("default_content@active@5", 12, 8)):
        ms = tuple("c%02d" % i for i in range(1, n + 1))
        room = ST.offer("g", ms[0], ms, "member", "@", "self", cosigners=ms[1:])
        out.append((name, "%d members, %d approve at once" % (n, yes),
                    [room, WN.opener("p", ms[0], name, "g", ("g",))] +
                    [WN.answer("a%d" % i, ms[i], "p", "approve") for i in range(1, yes)], "landed", "open"))
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
    "counted": "counted.count_set (one token)",
    "concluder": "counted.count_set (CC 4.5.13: one voice of its count closes every window of the table)",
    "opener": "none: counted.count_set proposes (CC 3.1.9.2)",
    "opener_says": "`approve` (CC 3.1.9.2: the proposal is the proposer's approval)",
    "at_once": "enact_rule (strictly more, min_count[corridor]) over base unless irreversible, `landed` (CC 3.1.3); "
               "corridor self: withdraw (CC 3.3.6.4) and cancel_rule over cancel_over, word at_window",
    "silent": "counted.target_silent (changes_set removes), word at_window",
    "at_close": "cancel_rule over cancel_over (not corridor self), word at_window; enact_rule if irreversible; "
                "floor_rule with reverse_path, `landed`",
    "default": "at_window",
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
            src = ROSTER_SOURCE if name.startswith("L:") else {k: HAND for k in DUMP_FIELDS}
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
    # (cell, family, new value): what the row gives must change
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
    ("at_window", "community_invite", "refused"),
    ("window_secs", "default_content", 172800),
    ("window_class", "default_content", "ruled_48h"),
    ("irreversible", "default_content", True),
    ("reverse_path", "default_content", False),
    ("corridor", "self_roster_add", "community"),
    ("family", "default_content", "default_renamed"),
    ("min_count.community", None, 3),
    ("window_classes.content_24h", None, 3600),
)


def give(row, table=POL, active=None):
    if active is None and row.get("base") == "active":
        active = "within_k"
    try:
        return ("spec", WN.spec_from_policy(row, table, active))
    except WN.PolicyRefusal as e:
        return ("refused", e.reasons)


def run_plants():
    caught, out = 0, []
    for cell, fam, v, *act in PLANTS:
        a = act[0] if act else None
        if fam is None:                       # a cell of the table, read for every row
            t = _set(POL, cell, v)
            hit = [f["family"] for f in POL["families"] if give(f, t) != give(f)]
        else:
            hit = [fam] if give(_set(TABLE[fam], cell, v), POL, a) != give(TABLE[fam], POL, a) else []
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
    WN.WINDOWS.pop("default_content@active@15", None)
    for name in sorted(set(differ) | set(DIFFERS)):
        if name in differ and name not in DIFFERS:
            problems.append("an unlisted difference: %s" % name)
        elif name in DIFFERS and name not in differ and name in WN.WINDOWS:
            problems.append("listed as differing and it does not: %s" % name)
    print("\n  the differences, and the side the table supports:")
    for name, why in DIFFERS.items():
        print("    %s: %s" % (name, why))
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
