#!/usr/bin/env python3
"""
check_delegation.py: a delegation chain from a counted grant (CC 4.1.1, CC 3.4.7), as the seat walk reads it.

"Does key K hold scope S through a chain from a counted grant" is seat.Seats.stands: no new rule. This file
states the cases and holds the walk to them.

    the grant      a counted offer over the bundle's holders to A, of scope `infra`, carrying sub-delegation
    an onward hop  an offer by the delegator, under the offer that seats it, to the delegate, over the same
                   object, with the delegate's own acceptance (two consents)

Cases (each a hand-written answer, read in every arrival order of its rows):
    depth          the reader's cap: a seat more than DEPTH links below the grant does not stand
    attenuation    each hop bears a scope the hop above covers: equal, or narrower by a `:` segment
    the gate       an onward hop stands only where the delegator's own incoming grant carries sub-delegation
    two consents   a hop the delegate has not accepted seats nobody
    an end         a withdrawn hop ends itself and every seat under it, by causal past
    a cycle        A grants B and B grants A: each is visited once, nothing is refused, nobody gains a scope
    a self-edge    a key granting itself gains nothing and is no cycle

Planted breaks, each of which must change a case's answer:
    no_cap         the walk has no depth cap
    no_gate        an onward hop needs no sub-delegation above it
    no_attenuation a hop may bear any scope
    one_consent    the delegate's acceptance is not asked

Root chains (ROOT_CASES, cross-object rest 5): the grantee's seat from a root grant (conf `root`, `bundle` the grant)
stands while the grant resolves at the reader of the root view; the onward gate reads the charter in force there
(Root.sub_delegation), and closes with no root read. Plants root_gate_unread, root_seat_unchecked, root_seat_any_duty, root_through_lone_gate (the root seat read by the
lone-holder gate, not as the one gate's other path).

Not here: the term of an edge that carries sub-delegation (a shape rule of one row, and the caller's); an act
done under the chain after an edge ends (conferral_end.py, one call per edge); the aggregate-weight cap that
CC 2.4.1.3 names, which this walk does not have; a chain across two objects.

    python3 -I check_delegation.py      exit 1 on any difference
"""
import itertools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import seat as ST  # noqa: E402

CK = ST.CK
T, F = True, False
OBJ = "b"
B0 = ST.offer("b", "h1", ("h1", "h2", "h3"), "holder", "@", "self", cosigners=("h2", "h3"))
GRANT = ST.offer("gr", "h1", "A", "infra", OBJ, "group", ("b",), head=("b",), policy="accord_majority", counted="holder",
                 cosigners=("h2", "A"), sub=True)


def hop(i, by, to, scope, under, sub=False, accepted=True, names=()):
    return ST.offer(i, by, to, scope, OBJ, "seat", (under,) + tuple(names), under=under, sub=sub,
                    cosigners=(to,) if accepted else ())


def chain(n, sub_all=True):
    """A -> k1 -> ... -> kn, each hop the same scope, each carrying sub-delegation."""
    rows, by, under = [], "A", "gr"
    for i in range(1, n + 1):
        rows.append(hop("d%d" % i, by, "k%d" % i, "infra:detect", under, sub=sub_all))
        by, under = "k%d" % i, "d%d" % i
    return rows


D1 = hop("d1", "A", "B", "infra:detect", "gr", sub=True)
D2 = hop("d2", "B", "C", "infra:detect:x", "d1")
D3 = hop("d3", "C", "D", "infra:detect:x", "d2")
# (name, rows, [(key, scope, stands)])
CASES = [
    ("the counted grant seats its grantee", [B0, GRANT], [("A", "infra", T)]),
    ("one hop: the delegate holds the narrower scope and not the wider", [B0, GRANT, D1],
     [("B", "infra:detect", T), ("B", "infra", F)]),
    ("two hops down", [B0, GRANT, D1, D2], [("C", "infra:detect:x", T), ("C", "infra:detect", F)]),
    ("the gate: an onward hop by a delegate whose own grant carries no sub-delegation", [B0, GRANT, D1, D2, D3],
     [("D", "infra:detect:x", F), ("C", "infra:detect:x", T)]),
    ("two consents: a hop the delegate has not accepted", [B0, GRANT, hop("d1", "A", "B", "infra:detect", "gr", sub=True, accepted=False)],
     [("B", "infra:detect", F)]),
    ("attenuation: a hop bearing a scope the grant does not cover", [B0, GRANT, hop("dw", "A", "B", "other", "gr")],
     [("B", "other", F)]),
    ("attenuation: a hop widening back to the grant's own scope from a narrower one",
     [B0, GRANT, D1, hop("d2", "B", "C", "infra", "d1")], [("C", "infra", F)]),
    ("depth: %d links below the grant stand" % ST.DEPTH, [B0, GRANT] + chain(ST.DEPTH),
     [("k%d" % ST.DEPTH, "infra:detect", T)]),
    ("depth: the link after the cap does not", [B0, GRANT] + chain(ST.DEPTH + 1),
     [("k%d" % ST.DEPTH, "infra:detect", T), ("k%d" % (ST.DEPTH + 1), "infra:detect", F)]),
    ("an end: the delegator withdraws its hop, and the seat under it falls too",
     [B0, GRANT, D1, D2, ST.withdraw("wd", "A", "d1", ("d1",))],
     [("B", "infra:detect", F), ("C", "infra:detect:x", F), ("A", "infra", T)]),
    ("an end: the grantee withdraws its own acceptance of the grant, and everything below falls",
     [B0, GRANT, D1, D2, ST.withdraw("wg", "A", "gr", ("gr",))],
     [("A", "infra", F), ("B", "infra:detect", F), ("C", "infra:detect:x", F)]),
    ("a cycle: B grants the scope back to A; each is visited once and nobody gains",
     [B0, GRANT, D1, hop("back", "B", "A", "infra:detect", "d1", sub=True)],
     [("A", "infra", T), ("B", "infra:detect", T), ("B", "infra", F)]),
    ("a cycle with no grant under it seats nobody",
     [B0, hop("x1", "A", "B", "infra:detect", "x2", sub=True), hop("x2", "B", "A", "infra:detect", "x1", sub=True)],
     [("A", "infra:detect", F), ("B", "infra:detect", F)]),
    ("a self-edge: A grants itself under its own grant and gains nothing more",
     [B0, GRANT, hop("self", "A", "A", "infra:detect", "gr", sub=True)], [("A", "infra", T), ("A", "other", F)]),
]


# ---- a chain from a ROOT grant (cross-object rest 5): the grantee's seat names the grant (`bundle`) and stands while
# it resolves at the reader of the root view; the onward gate reads the charter in force there (Root.sub_delegation),
# closed with no root read. The room `room`; root grant gA (b0's holders h1 and h2 of three) names uA for it, duty infra
sys.path.insert(0, os.path.join(HERE, "..", "trust_root"))
import root as RT  # noqa: E402

ROOM = ST.found("room", "p1", ("p1", "p2"), cosigners=("p2",))
ROOMD = ST.found("room", "p1", ("p1", "p2", "uA"), {"moderate": ("p1",)}, cosigners=("p2", "uA"),
                 duties=("infra",))                              # infra declared; uA a member (a duty seat stands on one)
RS = ST.offer("rs", "uA", "uA", "infra", "room", "root", ("room",), bundle="gA", sub=True)   # the grantee's root seat
RD1 = ST.offer("rd1", "uA", "B", "infra:detect", "room", "seat", ("rs",), under="rs", cosigners=("B",))
CSUB = {"name": "c0s", "duties": ("infra",), "sub_delegation": ("infra",)}
B0R = RT.bundle("b0", "fam", 0, ("h1", "h2", "h3"), seats=("n1",))
GA = RT.grant("gA", "b0", "uA", "room", ("h1", "h2"))
GROW = RT.bundle("b1", "fam", 1, ("h1", "h2", "h3", "h4", "h5"), prev=("b0",), charter=CSUB, seats=("n1",),
                 stmts=[("h1", 0), ("h2", 0), ("h3", 0)])                     # holders grow to five: gA's two lapse
ANCHOR = RT.reader(anchor="b0")
import check_root as CR  # noqa: E402
AOW = CR.AO                                                      # root-fold's AO world: b0, b1, b2, and the sibling s0
GS = RT.grant("gs", "s0", "uA", "room", ("h1", "h2", "X"))
RSS = dict(RS, bundle="gs")
# (name, bundles or None for no root read, reader, rows, [(key, scope, stands)])
ROOT_CASES = [
    ("a root grant in force seats its grantee, and the charter's sub_delegation lets it pass the duty on",
     [dict(B0R, charter=CSUB)], ANCHOR, [ROOM, RS, RD1], [("uA", "infra", T), ("B", "infra:detect", T)]),
    ("the charter in force carries no sub_delegation: the onward hop is refused, the row's own `sub` mark not read",
     [B0R], ANCHOR, [ROOM, RS, RD1], [("uA", "infra", T), ("B", "infra:detect", F)]),
    ("the holders grow to five at the reader (b1 acknowledged): gA's two voices lapse, and the seat ends with it",
     [dict(B0R, charter=CSUB), GROW], RT.reader(anchor="b0", acks=("b1",)), [ROOM, RS, RD1],
     [("uA", "infra", F), ("B", "infra:detect", F)]),
    ("a reader whose anchor is not the genesis: the grant does not resolve for it, and the seat is nothing",
     [dict(B0R, charter=CSUB)], RT.reader(anchor="zz"), [ROOM, RS, RD1], [("uA", "infra", F)]),
    ("no root read: the root seat seats nothing and the gate is closed", None, None, [ROOM, RS, RD1],
     [("uA", "infra", F), ("B", "infra:detect", F)]),
    ("a root seat of another duty than the grant's seats nothing",
     [dict(B0R, charter=CSUB)], ANCHOR, [ROOM, dict(RS, scope="other")], [("uA", "other", F)]),
    ("a root grant's seat of a duty the room's record declares (uA a member): not the lone holder's act, the one gate's other "
     "path (a resolving grant whose scope carries the duty); it stands",
     [dict(B0R, charter=CSUB)], ANCHOR, [ROOMD, RS], [("uA", "infra", T)]),
    # the reader's monotone line (root-fold's AO world): gs is a grant on s0 (h1, h2 and X: h1 and h2's sibling at b0)
    ("the reader's line: a grant on a bundle the reader's line holds void (it acknowledged s0, then b2, which s0 is "
     "behind) seats nothing for that reader", AOW, RT.reader(anchor="b0", acks=("s0", "b2")), [ROOM, RSS],
     [("uA", "infra", F)], (GS,)),
    ("and for a reader whose line holds it (it acknowledged only s0) the same rows seat uA",
     AOW, RT.reader(anchor="b0", acks=("s0",)), [ROOM, RSS], [("uA", "infra", T)], (GS,)),
    ("a root seat signed by a key the grant does not name seats nothing",
     [dict(B0R, charter=CSUB)], ANCHOR, [ROOM, dict(RS, signer="X", to=("X",))], [("X", "infra", F)]),
]
ROOT_PLANTS = ("root_gate_unread", "root_seat_unchecked", "root_seat_any_duty", "root_through_lone_gate")


def root_answers(case, plant=None, order=None):
    _name, bundles, rd, rows, asks = case[:5]
    grants = case[5] if len(case) > 5 else (GA,)
    rows = order or rows
    saved = set(ST.MUT)
    if plant: ST.MUT.add(plant)
    try:
        ctx = ST.root_view(RT.Root(bundles, (), grants), rd) if bundles is not None else None
        if ctx: ctx.__enter__()
        try:
            S = CK.concluded(CK.kept(list(rows)), lambda r, P, past: ST.seat_rule(r, P, past))
            Q = ST.Seats(S)
            return [Q.stands(k, sc, "room") for k, sc, _ in asks]
        finally:
            if ctx: ctx.__exit__()
    finally:
        ST.MUT.clear(); ST.MUT |= saved


# r75: standing is re-read at the reader. Rows concluded while the grant resolved are read after it lapsed (the holders
# grew at the reader): the seat is not held. (concluded under, read under, [(key, scope, stands)])
LIVE_VIEW = ([dict(B0R, charter=CSUB)], ANCHOR)
LAPSED_VIEW = ([dict(B0R, charter=CSUB), GROW], RT.reader(anchor="b0", acks=("b1",)))
REREAD = [("concluded while the grant resolved, read after it lapsed: no seat, and no onward hop", LIVE_VIEW, LAPSED_VIEW,
           [("uA", "infra", F), ("B", "infra:detect", F)]),
          ("the control: concluded and read while it resolves", LIVE_VIEW, LIVE_VIEW,
           [("uA", "infra", T), ("B", "infra:detect", T)])]


def reread_answers(case, plant=None):
    _n, at, now, asks = case
    saved = set(ST.MUT)
    if plant: ST.MUT.add(plant)
    try:
        with ST.root_view(RT.Root(at[0], (), (GA,)), at[1]):
            S = CK.concluded(CK.kept([ROOM, RS, RD1]), lambda r, P, past: ST.seat_rule(r, P, past))
        with ST.root_view(RT.Root(now[0], (), (GA,)), now[1]):
            Q = ST.Seats(S)
            return [Q.stands(k, sc, "room") for k, sc, _ in asks]
    finally:
        ST.MUT.clear(); ST.MUT |= saved


def read(rows, plant=None):
    S = CK.State(list(rows), {r["id"]: True for r in rows})
    Q = ST.Seats(S, depth=10 ** 6 if plant == "no_cap" else ST.DEPTH)
    return Q


def answers(rows, asks, plant=None):
    rows = list(rows)
    if plant == "one_consent":
        rows = [dict(r, cosigners=tuple(r["to"])) if r.get("conf") == "seat" else r for r in rows]   # read as accepted
    if plant == "no_gate":
        rows = [dict(r, sub=True) if r["kind"] == "offer" else r for r in rows]
    saved = ST.covers
    if plant == "no_attenuation":
        ST.covers = lambda have, want: True
    try:
        Q = read(rows, plant)
        return [Q.stands(k, s, OBJ) for k, s, _ in asks]
    finally:
        ST.covers = saved


def main():
    problems, orders = [], 0
    for name, rows, asks in CASES:
        want = [w for _, _, w in asks]
        got = answers(rows, asks)
        if got != want:
            problems.append("%s: got %s, expected %s" % (name, got, want))
        # the seats are a function of the set: every order of the rows above the founding one
        tail = rows[1:]
        perms = itertools.permutations(tail) if len(tail) <= 6 else [tail, tail[::-1]]
        for p in perms:
            orders += 1
            if answers([rows[0]] + list(p), asks) != got:
                problems.append("%s: order %s differs" % (name, [r["id"] for r in p]))
                break
    for case in ROOT_CASES:
        want = [w for _, _, w in case[4]]
        for o in itertools.permutations(case[3][1:]):
            o = list(o)
            if root_answers(case, order=[case[3][0]] + list(o)) != want:
                problems.append("root %s: got %s, expected %s" % (case[0], root_answers(case), want))
                break
    for case in REREAD:
        if reread_answers(case) != [w for _, _, w in case[3]]:
            problems.append("reread %s: got %s" % (case[0], reread_answers(case)))
    if all(reread_answers(c, "root_seat_stored") == [w for _, _, w in c[3]] for c in REREAD):
        problems.append("plant root_seat_stored not caught by a reread case")
    root_caught = 0
    for plant in ROOT_PLANTS:
        hit = [c[0] for c in ROOT_CASES if root_answers(c, plant) != [w for _, _, w in c[4]]]
        root_caught += bool(hit)
        if not hit:
            problems.append("plant %s not caught by a root case" % plant)
    caught = 0
    for plant in ("no_cap", "no_gate", "no_attenuation", "one_consent"):
        hit = [name for name, rows, asks in CASES if answers(rows, asks, plant) != [w for _, _, w in asks]]
        caught += bool(hit)
        print("  plant %-15s %s" % (plant, "caught by: %s" % hit[0] if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % plant)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases, %d answers, %d orders, %d of 4 planted breaks caught; %d root-chain cases, %d of %d "
          "planted breaks caught" % ("ok" if not problems else "%d problems" % len(problems), len(CASES),
                                     sum(len(a) for _, _, a in CASES), orders, caught, len(ROOT_CASES), root_caught,
                                     len(ROOT_PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
