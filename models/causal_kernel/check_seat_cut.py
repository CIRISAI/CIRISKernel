#!/usr/bin/env python3
"""
check_seat_cut.py: an act under a seat follows the cut (CC 2.4.1.1, ruled 2026-11-21; CC 2.7.7), while the members
at a head stay by past (RosterHead.lean leaving_binds_by_past). Runs seat.exercised_stands.

    cases     the named cases, each with its expected answer and the members expected at the act's head
    worlds    every kept set of two pools (a seat over a key; a seat over a group) up to a bound, every act in it:
              the answer is recorded for the crate's differential test (tools/kernel_fixtures.py, seat_cut.json),
              and at every concluded row as a head the members are the same with every ending cut outside that
              head's past taken out of the world, and the cut exercised_stands runs changes no other row's status
    plants    seat_cut_unread ((b) skipped) and seat_cut_retro (the walk reads every held row, the reading
              RosterHead.Retro rejects) must each change a case

    python3 -I check_seat_cut.py     exit 1 on any case that differs, any members that move, or a plant not caught
"""
import itertools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import causal_kernel as CK  # noqa: E402
import seat as ST           # noqa: E402

R = CK.row
SCOPE_K, OBJ_K, KEY = "wa", "O", "k"          # the seat over a key: k holds "wa" over key O, conferred by O itself
SCOPE_G, OBJ_G, KEY_G = "member", "g", "C"     # the seat over a group: C is a member of g


# ---- the pool over a key ------------------------------------------------------------------------------------
def key_pool():
    return [
        ST.offer("o1", "O", KEY, SCOPE_K, OBJ_K, "self"),
        ST.accept("a1", KEY, "o1"),
        R("x1", "act", KEY, ("a1",)),                              # an act under the seat
        ST.withdraw("W", KEY, "a1"),                               # k's own withdrawal, concurrent with x1
        ST.withdraw("Wx", KEY, "a1", ("x1",)),                     # k's withdrawal with x1 in its past
        R("xW", "act", KEY, ("W",)),                               # an act naming the withdrawal
        ST.accept("a2", KEY, "o1"),                                # a re-acceptance on another device, concurrent with W
        R("x2", "act", KEY, ("a2",)),
        R("x3", "act", KEY, ("W", "a2")),                          # names both
        R("rm", "remove", "O", ("x1",), removes=KEY),              # a removal of k's key, concurrent with W
        R("rmO", "remove", KEY, ("x1",), removes="O"),             # k removes O: with rm, equal standing (rule 5)
        ST.withdraw("wc", "O", "o1"),                              # the conferrer's withdrawal of the offer
        ST.unseat("u", "O", KEY, SCOPE_K, OBJ_K, "self"),          # the object's own key unseats k
        R("xu", "act", KEY, ("u",)),
    ]


# ---- the pool over a group ----------------------------------------------------------------------------------
def group_pool():
    g = ST.offer("g", "A", ("A", "B", "C"), SCOPE_G, "@", "self", cosigners=("B", "C"))
    cnt = dict(head=("g",), policy="community_remove", cosigners=("B",))
    return [
        g,
        R("y1", "act", KEY_G, ("g",)),
        ST.unseat("u", "A", KEY_G, SCOPE_G, "g", "group", ("g",), content="u", **cnt),          # a count, concurrent with y1
        ST.unseat("uy", "A", KEY_G, SCOPE_G, "g", "group", ("g", "y1"), content="uy", **cnt),   # a count with y1 in its past
        R("yu", "act", KEY_G, ("u",)),                                                       # names the count
        ST.withdraw("Cw", KEY_G, "g"),                     # C resigns: its own withdrawal of the offer that seats it
        R("yC", "act", KEY_G, ("Cw",)),
        ST.withdraw("Aw", "A", "g"),                       # A resigns: it ends A's seat, not C's
    ]


def pick(pool, ids):
    by = {r["id"]: r for r in pool}
    return [by[i] for i in ids]


KP, GP = key_pool(), group_pool()
# name, pool, row ids, the act, (k, scope, obj), expected, the holders of the pool's seat by the walk over the act's past
CASES = [
    ("x in the withdrawal's past", KP, "o1 a1 x1 Wx", "x1", (KEY, SCOPE_K, OBJ_K), "stands", {KEY}),
    ("x concurrent with the withdrawal", KP, "o1 a1 x1 W", "x1", (KEY, SCOPE_K, OBJ_K), "cut", {KEY}),
    ("x names the withdrawal", KP, "o1 a1 W xW", "xW", (KEY, SCOPE_K, OBJ_K), "not seated", set()),
    ("the withdrawal voided by a concurrent counting removal of k", KP, "o1 a1 x1 W rm", "x1", (KEY, SCOPE_K, OBJ_K), "stands", {KEY}),
    ("the withdrawal contested: removals of equal standing (rule 5)", KP, "o1 a1 x1 W rm rmO", "x1", (KEY, SCOPE_K, OBJ_K), "contested", {KEY}),
    ("re-accepted on a second device, x under it only", KP, "o1 a1 W a2 x2", "x2", (KEY, SCOPE_K, OBJ_K), "cut", {KEY}),
    # the walk seats k (a1 ended, a2 live): an act follows the walk. A count over x3 would still leave k out
    # (left_in_past, RosterHead.readmission_needed): acts re-seat, counts do not re-count
    ("re-accepted on a second device, x names both", KP, "o1 a1 W a2 x3", "x3", (KEY, SCOPE_K, OBJ_K), "stands", {KEY}),
    ("the conferrer's withdrawal concurrent", KP, "o1 a1 x1 wc", "x1", (KEY, SCOPE_K, OBJ_K), "cut", {KEY}),
    ("an unseat by the object's own key concurrent", KP, "o1 a1 x1 u", "x1", (KEY, SCOPE_K, OBJ_K), "cut", {KEY}),
    ("an act naming the unseat", KP, "o1 a1 u xu", "xu", (KEY, SCOPE_K, OBJ_K), "not seated", set()),
    ("an unseat by a count, x concurrent", GP, "g y1 u", "y1", (KEY_G, SCOPE_G, OBJ_G), "cut", {"A", "B", "C"}),
    ("an unseat by a count, x in its past", GP, "g y1 uy", "y1", (KEY_G, SCOPE_G, OBJ_G), "stands", {"A", "B", "C"}),
    ("an act naming the counted unseat", GP, "g u yu", "yu", (KEY_G, SCOPE_G, OBJ_G), "not seated", {"A", "B"}),
    ("a resignation concurrent", GP, "g y1 Cw", "y1", (KEY_G, SCOPE_G, OBJ_G), "cut", {"A", "B", "C"}),
    ("an act naming the resignation", GP, "g Cw yC", "yC", (KEY_G, SCOPE_G, OBJ_G), "not seated", {"A", "B"}),
    ("another member's resignation concurrent", GP, "g y1 Aw", "y1", (KEY_G, SCOPE_G, OBJ_G), "stands", {"A", "B", "C"}),
    ("not k's seat at all", KP, "o1 a1 x1", "x1", ("z", SCOPE_K, OBJ_K), "not seated", {KEY}),
]

POOLS = {"key": (KP, (KEY, SCOPE_K, OBJ_K), ("o1", "a1")), "group": (GP, (KEY_G, SCOPE_G, OBJ_G), ("g",))}
BOUND = 5        # rows beyond the base


def state(rows):
    return CK.concluded(CK.kept(list(rows)), lambda r, P, past: ST.seat_rule(r, P, past))


def head_members(S, h, scope, obj):
    """The members of (scope, obj) at h, by past: members_at over the concluded rows, less h's own leavings."""
    P = [q for q in S.Cs if q["id"] in S.anc[h]] + [S.by[h]] if S.C.get(h) else []
    past = lambda a, b: a in S.anc[b]
    return ST.members_at(P, past, obj, (h,), scope)


def act_head_members(S, x, scope, obj):
    """The holders at the act's head by an independent path: the world cut down to x's own past, kept and
    concluded again, and Seats.holders over it. (a) must equal it."""
    T = state([r for r in S.rows if r["id"] in S.anc[x]])
    return set(ST.Seats(T).holders(scope, obj))


def ending_cuts(S, k, scope, obj):
    w = ST.ending_withdrawals(S, k, scope, obj)
    u = {q["id"] for q in S.Cs if q["kind"] == "unseat" and ("seat", k, scope, obj) in q["cuts"]}
    return w | u


def worlds(name):
    pool, (k, scope, obj), base = POOLS[name]
    rest = [r for r in pool if r["id"] not in base]
    seen = set()
    for n in range(0, BOUND + 1):
        for extra in itertools.combinations(rest, n):
            rows = [r for r in pool if r["id"] in base] + list(extra)
            ids = tuple(r["id"] for r in CK.kept(rows))
            if ids in seen: continue
            seen.add(ids)
            yield [r for r in rows if r["id"] in ids]


def world_answers(rows, k, scope, obj):
    """Every act's answer, and the members at every concluded row as a head."""
    S = state(rows)
    acts = {r["id"]: ST.exercised_stands(S, r["id"], k, scope, obj) for r in S.rows if r["kind"] == "act"}
    heads = {r["id"]: sorted(head_members(S, r["id"], scope, obj)) for r in S.Cs}
    return S, acts, heads


def statuses_hold(S, k, scope, obj):
    """The cut exercised_stands runs changes the status of no row but the ending withdrawals it adds."""
    import cut as CUT
    ending = ST.ending_withdrawals(S, k, scope, obj)
    tagged = [dict(q, cuts=tuple(q.get("cuts", ())) + (ST.TARGET,), says=ST.OUT) if q["id"] in ending else q for q in S.rows]
    S2 = CK.State(tagged, S.C)
    C, C2 = CUT.Cut(S), CUT.Cut(S2)
    return [q["id"] for q in S.rows if q["id"] not in ending and C.status(q) != C2.status(S2.by[q["id"]])]


def members_hold(rows, S, k, scope, obj):
    """At every concluded head, the members are the same with every ending cut outside its past taken out."""
    bad = []
    cuts = ending_cuts(S, k, scope, obj)
    for h in [r["id"] for r in S.Cs]:
        outside = {c for c in cuts if c != h and c not in S.anc[h]}
        if not outside: continue
        T = state([r for r in rows if r["id"] not in outside])
        if head_members(S, h, scope, obj) != head_members(T, h, scope, obj):
            bad.append(h)
    return bad


def run_cases():
    out = []
    for name, pool, ids, x, (k, scope, obj), want, mem in CASES:
        S = state(pick(pool, ids.split()))
        got = ST.exercised_stands(S, x, k, scope, obj)
        sc, ob = (SCOPE_K, OBJ_K) if pool is KP else (SCOPE_G, OBJ_G)
        m = act_head_members(S, x, sc, ob)
        P = [q for q in S.Cs if q["id"] in S.anc[x]]
        a_ok = set(ST.walk_holders(P, scope, obj)) == act_head_members(S, x, scope, obj)
        out.append((name, x, want, got if a_ok else got + " ((a) differs from Seats.holders)", mem, m))
    return out


def main():
    ok = True
    print("CASES")
    rows = run_cases()
    for name, x, want, got, mem, m in rows:
        good = got == want and m == mem
        ok = ok and good
        print("  %-4s %-64s %-4s %-11s seated at its past %s" % ("ok" if good else "NOT", name, x, got, sorted(m)))
        if not good:
            print("       expected %s, members %s" % (want, sorted(mem)))
    print("WORLDS")
    for name in POOLS:
        pool, (k, scope, obj), _ = POOLS[name]
        n, acts, moved, changed, tally = 0, 0, 0, 0, {}
        for w in worlds(name):
            S, a, _ = world_answers(w, k, scope, obj)
            n += 1
            acts += len(a)
            for v in a.values():
                tally[v] = tally.get(v, 0) + 1
            moved += len(members_hold(w, S, k, scope, obj))
            changed += len(statuses_hold(S, k, scope, obj))
        ok = ok and moved == 0 and changed == 0
        print("  %s: %d worlds, %d acts (%s); heads whose members move with ending cuts outside their past: %d; other rows whose cut status changes: %d"
              % (name, n, acts, ", ".join("%s %d" % kv for kv in sorted(tally.items())), moved, changed))
    print("PLANTS")
    for mut in ("seat_cut_unread", "seat_cut_retro"):
        ST.MUT.add(mut)
        try:
            changed = [r[0] for r in run_cases() if r[2] != r[3]]
        finally:
            ST.MUT.discard(mut)
        ok = ok and bool(changed)
        print("  %-16s %s (%d cases differ)" % (mut, "caught" if changed else "NOT CAUGHT", len(changed)))
    print("check_seat_cut: %d cases, %s" % (len(CASES), "ok" if ok else "NOT OK"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
