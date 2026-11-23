"""
conferral_content.py: room content after a member's seat ends, where the END names the rows held good
(the Constitution's proposal of 2026-11-22, second form, for CC 2.4.1.1 and persist v62.0). A reference: from a
set of rows, for every content row of the member, whether it is COUNTED at its own head and whether it is IN
FORCE (in the room's content) now, and the rule that decides it.

The proposal.
1. A content row (a message, a file placement, a reaction) is an act under its signer's membership. It names
   the roster head it is at and, in `prev`, the previous content row of the same KEY in the room: one series per
   key, so a member with two devices has two series.
2. A row that ends the member's seat (a counted removal, or the member's own resignation) names in
   `trusted_through` the newest row of each series its signers hold: the tips.
3. After the end, a content row of the member is in the room's content when it is a named tip or an ancestor of
   one along `prev`. Every other content row of theirs counts at its own head and is not in the room's content.
4. Tips only grow: a later counted row of the same body (`tips`) may name further tips, and the kept set is the
   union. No co-member receipts content.

No instant is read and no arrival order: the answer is a function of the held rows. One member's seat and its
content are modelled (keys B and B2); other members' content is untouched by any of this. Not modelled here:
receipts (conferral_end.py), a re-admission, the reader's line on the end (conferral_end.py: `end_void.line`),
key removals.

Rows (the kernel's row shape: `id`, `kind`, `signer`, the ids it `names`, and the fields a rule reads):
    head   a roster version; `names` the heads it extends
    act    a content row of the member: `signer` the key (B or B2), `head` the roster head it names, `prev` the
           key's previous content row or None
    end    an end of the member's seat: `signer` "count" (a counted removal) or a key of the member (its own
           resignation), `head` (h_e), `trusted_through` the tips it holds good (a list; empty where its signers
           hold none, which on the wire is the member's absence)
    tips   a later row naming further tips: `extends` the end it adds to (which it names), `trusted_through`

Which ends count:
    end_void.stale_head  E1: the end has a head later than h_e in its own past: it concludes nothing
    end_void.seat_ended  the end has a counting end of the seat in its own past: the seat was already ended
Whether an end counts is decided by its own causal past alone, so no row signed later changes it. In
particular the member's own end is NOT voided for naming a head later than another end's: under that rule the
exhaustive check found the member reviving a row that named its first resignation, by signing a second one at
an older head. An extra end of the member's own only ever takes rows out (E3, E4, and the rule below).

Whose tips are read (`merge`). The proposal's third point read literally is `union`, and
check_conferral_content.py shows that under it an ended member adds content for ever, by signing a further
resignation at the head it last sat at. The reference's default closes that:
    count_first             (default) the count's word: the union of the tips of every counted end that is not
                            stale and of every counted `tips` row. The member's own ends are read only where no
                            counted end counts, and then a row stays only where EVERY one of them holds it
                            good, so a second resignation can remove but never add. A `tips` row signed by the
                            member is never read.
    union                   the union of the tips of every end that counts, the member's own included, and of
                            every counted `tips` row
    count_first_self_union  count_first, but where only the member's own ends speak, the union of them

Rules for a content row, in the order they decide (the name a failing test reports):
    no_end           no end counts: counted and in force
    E4.names_end     the row has a counting end in its past: not counted
    E3.later_head    the row names a head that has a counting end's h_e in its past: the seat is ended there
    T.held_good      counted and in force: a tip that is read, or its ancestor along `prev` in the same series
    E2.forward       counted at its own head, not in force: not held good
"""

KEYS, COUNT = ("B", "B2"), "count"
MERGES = ("count_first", "union", "count_first_self_union")


def _past(rows):
    by = {r["id"]: r for r in rows}
    memo = {}

    def anc(i):
        if i not in memo:
            memo[i] = set()
            out = set()
            for n in by[i].get("names", ()):
                out.add(n)
                if n in by:
                    out |= anc(n)
            memo[i] = out
        return memo[i]
    return by, anc


def counting_ends(rows):
    """{end id: None if it counts, else the rule that voids it}."""
    by, anc = _past(rows)
    ends = [r for r in rows if r["kind"] == "end"]
    later = lambda h, he: he in anc(h) if h in by else False
    memo = {}

    def void(e):
        i = e["id"]
        if i in memo:
            return memo[i]
        if any(later(h, e["head"]) for h in anc(i) if h in by and by[h]["kind"] == "head"):
            memo[i] = "end_void.stale_head"     # decided from the heads alone, before any other end is asked
            return memo[i]
        seated = any(o["id"] in anc(i) and void(o) is None for o in ends if o is not e)   # ends in e's own past
        memo[i] = "end_void.seat_ended" if seated else None
        return memo[i]
    return {e["id"]: void(e) for e in ends}


def held_good(rows, r):
    """The content rows a row's tips hold good: each named tip that is a content row of the member, and its
    ancestors along `prev` while they are rows of the same key (one series)."""
    by = {x["id"]: x for x in rows}
    out, todo = set(), list(r.get("trusted_through", ()))
    while todo:
        t = todo.pop()
        x = by.get(t)
        if x is None or x["kind"] != "act" or x["signer"] not in KEYS or t in out:
            continue
        out.add(t)
        p = by.get(x.get("prev"))
        if p is not None and p["signer"] == x["signer"]:
            todo.append(p["id"])
    return out


def kept(rows, merge="count_first", self_tips=False):
    """The content rows held good by the tips that are read under `merge`. `self_tips` is a plant: a `tips` row
    signed by the member is read."""
    void = counting_ends(rows)
    ends = [r for r in rows if r["kind"] == "end"]
    counts = [e for e in ends if void[e["id"]] is None]
    c_ends = [e for e in ends if e["signer"] == COUNT and void[e["id"]] != "end_void.stale_head"]
    own = [e for e in counts if e["signer"] in KEYS]
    adds = [r for r in rows if r["kind"] == "tips" and (r["signer"] == COUNT or self_tips)]
    union = lambda rs: set().union(*[held_good(rows, r) for r in rs]) if rs else set()
    if merge == "union":
        return union(counts + adds)
    if any(e["signer"] == COUNT for e in counts):
        return union(c_ends + adds)
    if merge == "count_first_self_union":
        return union(own + adds)
    good = [held_good(rows, e) for e in own]
    return (set.intersection(*good) if good else set()) | union(adds)


def answers(rows, merge="count_first", self_tips=False):
    """{content row id: {"counted": bool, "in_force": bool, "rule": str}} over the held `rows`."""
    assert merge in MERGES, merge
    by, anc = _past(rows)
    void = counting_ends(rows)
    ends = [by[i] for i in sorted(void) if void[i] is None]
    later = lambda h, he: he in anc(h) if h in by else False
    good = kept(rows, merge, self_tips)
    out = {}
    for r in rows:
        if r["kind"] != "act":
            continue
        x = r["id"]
        if not ends:
            a = (True, True, "no_end")
        elif any(e["id"] in anc(x) for e in ends):
            a = (False, False, "E4.names_end")
        elif any(later(r["head"], e["head"]) for e in ends):
            a = (False, False, "E3.later_head")
        elif x in good:
            a = (True, True, "T.held_good")
        else:
            a = (True, False, "E2.forward")
        out[x] = dict(zip(("counted", "in_force", "rule"), a))
    return out


def shown_first_held(rows, order, merge="count_first"):
    """The node-local fallback persist floated, NOT part of the proposal: a counted content row this reader held
    before it held any end that counts stays shown to this reader. {content row id: bool}. It reads the arrival
    `order`, so it is not a function of the held rows; check_conferral_content.py shows what follows."""
    final = answers(rows, merge)
    void = counting_ends(rows)
    first_end = min([order.index(i) for i in void if void[i] is None] or [len(order)])
    return {x: a["counted"] and (a["in_force"] or order.index(x) < first_end) for x, a in final.items()}


# ---- the case table: hand-written expectations, which the reference must meet --------------------------------
def head(i, *names):
    return {"id": i, "kind": "head", "signer": COUNT, "names": list(names)}


def act(i, h, prev=None, names=(), signer="B"):
    return {"id": i, "kind": "act", "signer": signer, "head": h, "prev": prev,
            "names": sorted(set(names) | {h} | ({prev} if prev else set()))}


def end(i, h, tips=(), signer=COUNT, names=()):
    return {"id": i, "kind": "end", "signer": signer, "head": h, "trusted_through": sorted(tips),
            "names": sorted(set(names) | {h} | set(tips))}


def tips(i, extends, tps, signer=COUNT):
    return {"id": i, "kind": "tips", "signer": signer, "extends": extends, "trusted_through": sorted(tps),
            "names": sorted({extends} | set(tps))}


H0, H1 = head("H0"), head("H1", "H0")
T, F = True, False
M1, M2, M3 = act("m1", "H0"), act("m2", "H0", "m1"), act("m3", "H0", "m2")
KEPT, OUT = (T, T, "T.held_good"), (T, F, "E2.forward")

# (name, about, rows, params, {act: (counted, in_force, rule)}, arrival orders a node may take them in)
CASES = [
    ("content_no_end", "no end held: a member's content rows count and are in the room's content",
     [H0, M1, M2], {}, {"m1": (T, T, "no_end"), "m2": (T, T, "no_end")}),
    ("removal_names_tip", "a counted removal names the newest row of the member's series: the whole series "
     "behind it stays in the room's content",
     [H0, M1, M2, M3, end("E", "H0", ["m3"])], {}, {"m1": KEPT, "m2": KEPT, "m3": KEPT}),
    ("removal_signers_hold_nothing", "the removal's signers held none of the member's content, so it names no "
     "tip: rows that reach a reader are counted at their head and not in the room's content, until a counted "
     "row names a tip",
     [H0, M1, M2, end("E", "H0")], {}, {"m1": OUT, "m2": OUT}),
    ("removal_in_flight_row", "the removers had not yet held m3 when they signed (it is concurrent with the end): "
     "m3 is out for everyone, honest or not; no rule can tell which",
     [H0, M1, M2, M3, end("E", "H0", ["m2"])], {}, {"m1": KEPT, "m2": KEPT, "m3": OUT}),
    ("in_flight_row_named_later", "the same rows, and then a counted row of the body names m3: tips only grow, "
     "and m3 is in the room's content from then on",
     [H0, M1, M2, M3, end("E", "H0", ["m2"]), tips("A", "E", ["m3"])], {}, {"m1": KEPT, "m2": KEPT, "m3": KEPT}),
    ("adding_row_waits_for_its_end", "a row that adds tips names the end it extends, so no node holds it before "
     "that end: in every arrival order the door allows, the end comes first",
     [H0, M1, M2, end("E", "H0", ["m1"]), tips("A", "E", ["m2"])], {}, {"m1": KEPT, "m2": KEPT},
     [["H0", "m1", "m2", "E", "A"], ["H0", "m1", "E", "m2", "A"]]),
    ("removed_member_keeps_posting", "after the removal the member signs m3 at the last head it sat at, not "
     "naming the end, and it arrives after the end at a node that never saw it: admitted, counted at its head, "
     "never in the room's content; the same answer in every arrival order",
     [H0, H1, M1, M2, end("E", "H0", ["m2"]), act("m3", "H0", "m2")], {}, {"m1": KEPT, "m2": KEPT, "m3": OUT},
     [["H0", "H1", "m1", "m2", "E", "m3"], ["H0", "m1", "m2", "m3", "H1", "E"]]),
    ("row_at_later_head", "a content row naming a roster head later than h_e: the member's seat is ended there, "
     "and the row does not count",
     [H0, H1, M1, end("E", "H0", ["m1"]), act("m2", "H1", "m1")], {},
     {"m1": KEPT, "m2": (F, F, "E3.later_head")}),
    ("row_names_end", "a content row that has the end in its past does not count, whatever head it names",
     [H0, M1, end("E", "H0", ["m1"]), act("m2", "H0", "m1", ["E"])], {},
     {"m1": KEPT, "m2": (F, F, "E4.names_end")}),
    ("resignation_names_tip", "the member's own resignation names its own newest row, which no one else holds "
     "yet: the resignation waits at every node until m2 is held (it names it), and then the history stays",
     [H0, M1, M2, end("R", "H0", ["m2"], "B")], {}, {"m1": KEPT, "m2": KEPT},
     [["H0", "m1", "m2", "R"]]),
    ("fork_of_one_series", "one key forked its own series (m2 and x2 both follow m1): the end names one branch, "
     "and only that branch and what is behind it stay; the other branch is out until a counted row names it",
     [H0, M1, M2, act("x2", "H0", "m1"), end("E", "H0", ["m2"])], {}, {"m1": KEPT, "m2": KEPT, "x2": OUT}),
    ("fork_other_branch_named_later", "the same fork, and a counted row then names the other branch's tip: both "
     "branches stay",
     [H0, M1, M2, act("x2", "H0", "m1"), end("E", "H0", ["m2"]), tips("A", "E", ["x2"])], {},
     {"m1": KEPT, "m2": KEPT, "x2": KEPT}),
    ("second_key_never_seen", "the member's second key signed a series the enders never held: the end names one "
     "tip, of the first key's series, and the whole second series is out",
     [H0, M1, M2, act("n1", "H0", signer="B2"), act("n2", "H0", "n1", signer="B2"), end("E", "H0", ["m2"])], {},
     {"m1": KEPT, "m2": KEPT, "n1": OUT, "n2": OUT}),
    ("second_key_named_later", "the same rows, and a counted row then names the second series' tip: it is in",
     [H0, M1, M2, act("n1", "H0", signer="B2"), act("n2", "H0", "n1", signer="B2"), end("E", "H0", ["m2"]),
      tips("A", "E", ["n2"])], {}, {"m1": KEPT, "m2": KEPT, "n1": KEPT, "n2": KEPT}),
    ("prev_across_keys_not_followed", "a row whose `prev` names a row of another key: the walk from a tip stays "
     "in one key's series, so naming n1 does not keep m1",
     [H0, M1, act("n1", "H0", "m1", signer="B2"), end("E", "H0", ["n1"])], {}, {"m1": OUT, "n1": KEPT}),
    ("two_removals_different_tips", "two counted removals of the member at one head, concurrent, naming "
     "different tips: both are the count's word, and the kept set is the union; nothing waits",
     [H0, M1, M2, M3, end("E", "H0", ["m3"]), end("E2", "H0", ["m2"])], {}, {"m1": KEPT, "m2": KEPT, "m3": KEPT}),
    ("removal_then_backdated_resignation", "after a removal that kept m1 only, the member signs m2 and a "
     "resignation at the old head naming m2, neither naming the removal: where a counted end counts the "
     "member's own end is not read, so m2 is not added",
     [H0, M1, end("E", "H0", ["m1"]), M2, end("R", "H0", ["m2"], "B")], {}, {"m1": KEPT, "m2": OUT}),
    ("removal_then_backdated_resignation_union", "the same rows under the proposal's third point read literally "
     "(`union`): the member's own later resignation adds m2. This is the hole count_first closes",
     [H0, M1, end("E", "H0", ["m1"]), M2, end("R", "H0", ["m2"], "B")], {"merge": "union"},
     {"m1": KEPT, "m2": KEPT}),
    ("two_resignations", "the member signs two resignations at one head naming different tips (a fork of its own "
     "end): a row stays only where both hold it good, so a second resignation never adds a row",
     [H0, M1, M2, end("R", "H0", ["m1"], "B"), end("R2", "H0", ["m2"], "B")], {}, {"m1": KEPT, "m2": OUT}),
    ("member_adds_tips_itself", "a row adding tips signed by the member is never read: only a counted row adds",
     [H0, M1, M2, end("E", "H0", ["m1"]), tips("A", "E", ["m2"], "B")], {}, {"m1": KEPT, "m2": OUT}),
    ("second_end_after_first", "a second removal that has the first in its past ends nothing (the seat was "
     "already ended), but it is a counted row of the body and its tips add",
     [H0, M1, M2, end("E", "H0", ["m1"]), end("E2", "H0", ["m2"], names=["E"])], {}, {"m1": KEPT, "m2": KEPT}),
    ("resignation_at_later_head", "a resignation naming a head later than the removal's h_e, concurrent with "
     "it: where a counted end counts the member's own end's tips are not read, so naming none takes nothing out",
     [H0, H1, M1, M2, end("E", "H0", ["m2"]), end("R", "H1", [], "B")], {}, {"m1": KEPT, "m2": KEPT}),
    ("backdated_resignation_uncounts_own_rows", "the member was removed at H1 with m2 (at H1) kept, and then signs "
     "a resignation at H0: E3 puts its own row at H1 at a head later than an end of its seat, so m2 no longer "
     "counts. An ended member can take its own rows out this way; conferral_end.py's reader's line bounds it",
     [H0, H1, M1, act("m2", "H1", "m1"), end("E", "H1", ["m2"]), end("R", "H0", [], "B")], {},
     {"m1": KEPT, "m2": (F, F, "E3.later_head")}),
    ("end_stale_head", "E1: an end naming H0 with H1 in its own past concludes nothing, and its tips are not read",
     [H0, H1, M1, end("E", "H0", ["m1"], names=["H1"])], {}, {"m1": (T, T, "no_end")}),
    ("tip_not_the_members", "a tip that is not a content row of the member is not read: here the end names a "
     "roster head as a tip, and nothing is held good",
     [H0, M1, end("E", "H0", ["H0"])], {}, {"m1": OUT}),
]


def orders(rows):
    """Every arrival order the door allows: a row arrives only after the rows it names."""
    ids = {r["id"] for r in rows}
    by = {r["id"]: r for r in rows}
    out = []

    def go(done, seq):
        if len(seq) == len(rows):
            out.append(list(seq)); return
        for r in rows:
            if r["id"] not in done and all(n in done or n not in ids for n in by[r["id"]]["names"]):
                done.add(r["id"]); seq.append(r["id"]); go(done, seq); seq.pop(); done.discard(r["id"])
    go(set(), [])
    return out


def check_cases():
    """Every case: the reference gives the hand-written answer, and the same in every arrival order."""
    problems = []
    for c in CASES:
        name, about, rows, params, want = c[:5]
        got = answers(rows, **params)
        for x, (cnt, frc, rule) in want.items():
            g = got.get(x)
            if g != {"counted": cnt, "in_force": frc, "rule": rule}:
                problems.append("%s: %s expected %s, reference %s" % (name, x, (cnt, frc, rule), g))
        if set(got) != set(want):
            problems.append("%s: acts %s, expectations for %s" % (name, sorted(got), sorted(want)))
        by = {r["id"]: r for r in rows}
        for o in orders(rows)[:200]:
            if answers([by[i] for i in o], **params) != got:
                problems.append("%s: order %s differs" % (name, o))
    return len(CASES), problems


def fixture():
    """The fixture, in the format of conferral_end.json: every case with its rows, parameters, arrival orders
    and every content row's answer."""
    _, problems = check_cases()
    assert not problems, problems
    cases = []
    for c in CASES:
        name, about, rows, params, want = c[:5]
        cases.append({"name": name, "about": about, "rows": rows, "merge": params.get("merge", "count_first"),
                      "orders": c[5] if len(c) > 5 else [[r["id"] for r in rows]],
                      "refused": None,
                      "answers": answers(rows, **params)})
    return {"about": "room content after a member's seat ends, where the end names the rows held good "
                     "(`trusted_through`): the Constitution's proposal of 2026-11-22 for CC 2.4.1.1, for persist "
                     "v62.0. Generated from models/causal_kernel/conferral_content.py; checked by "
                     "check_conferral_content.py. A PROPOSAL until the Constitution rules it",
            "roles": {"B": "a key of the member whose seat ends", "B2": "a second key of the same member",
                      "count": "a counted row (a roster version, a removal, a row adding tips)"},
            "merge": "whose tips are read: count_first (the reference's default), union (the proposal's third "
                     "point read literally) or count_first_self_union; see `rules`. The Constitution rules which",
            "refused": "null in every case here: every content row names its head",
            "rules": __doc__.split("Which ends count:")[1].strip(),
            "cases": cases}
