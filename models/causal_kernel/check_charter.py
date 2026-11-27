#!/usr/bin/env python3
"""
check_charter.py: charter coverage for licensing authorities (charter.py; CC 3.4.7, CC 4.4.3.12, 4.4.3.34).

DECLARED: the (class, legal_weight) pairs a community's record in force declares, over the rows a reader holds (at the
caller's instant, where a case gives one). LICENCES: whether a reader honours a licence, and why not; every licence
row of every case is kept and concluded (admitted as a row, whatever class it states). EDGES: the admission of an
acceptance edge's trust_classes. UNDECIDED: a removal from an affiliation is undecided, and concludes nothing. Every
DECLARED and LICENCES case is read in every arrival order of its rows up to a cap, and gives one answer.

Planted breaks, each of which must change a case's answer:
    charter_unread        the charter is not read: a licence of any class is honoured where the walk reaches
    at_issuance           the charter is read in the licence's own past, not over the reader's rows
    below_protocol_read   a record change that does not conclude under the record's protocol is read
    fork_union            two version tips that differ declare every pair either lists (not the common ones)
    fork_first            of two version tips one is in force (the least id)
    join_unread           a version naming both tips decides nothing: every version is read as a tip
    unstated_keeps        a version that states no classes keeps those in force at its head (not: declares none)
    community_unread      only an affiliation's record is a charter, not every community's
    family_read           a family's record is read as a charter
    weight_unread         a class's legal_weight is not read
    one_seat_countersign  a one-seat affiliation's record change is read as an act against a member (countersign)
    at_founding           the founding record's classes stay in force: no version is read
    dissolved_declares    a dissolved group still declares its classes
    dissolves_at_unread   a record's own stated end is not read against the caller's clock
    empty_edge_admits_all an empty trust_classes list is admitted, as every class
    absent_means_none     an edge listing no trust_classes admits no class
    edge_classes_unread   an edge's trust_classes are not read: every edge admits every class
    last_hop_only         only the hop arriving at the authority is held to its trust_classes
    affiliation_unread    (seat.py) a `declared_cohort` of `affiliations` is not read: the record is a plain
                          community's, under the community's acts
    affiliation_admit_unread    (seat.py) an appointment of a member of an affiliation is no act
    affiliation_removal_passes  (seat.py) a removal from an affiliation is counted, not undecided

    python3 -I check_charter.py      exit 1 on any difference
"""
import contextlib
import itertools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import charter as CH  # noqa: E402

ST, CK = CH.ST, CH.CK
ORDER_CAP = 24          # arrival orders read per case

M, L, D = "medical", "legal", "dental"
MW, LW, DW = (M, True), (L, False), (D, False)       # a class with its legal weight


def aff(i="af", to=("A", "B", "C"), cls=(MW, LW), cohort="affiliations", **kw):
    """A community's founding record: its members, each seated by its own signature, and its charter."""
    if cohort is not None:
        kw["declared_cohort"] = cohort
    if cls is not None:
        kw["licence_classes"] = tuple(cls)
    return ST.found(i, to[0], to, cosigners=tuple(to[1:]), **kw)


def rec(i, cls, heads=("af",), signer="A", cosigners=("B",), obj="af", **kw):
    """A version of the record, counted at `heads` (cls None: it states no classes)."""
    if cls is not None:
        kw["licence_classes"] = tuple(cls)
    return ST.offer(i, signer, (), "record", obj, "group", tuple(heads), head=tuple(heads), cosigners=tuple(cosigners),
                    **kw)


def lic(i, cls, authority="af", names=None):
    return CH.licensure(i, "D", authority, cls, names=(authority,) if names is None else names)


AF = aff()
V1 = rec("v1", (MW,))                                      # A and B: two of three, a strict majority
V1L = rec("v1", (MW,), signer="A", cosigners=())           # A alone: below the protocol
V0 = rec("v0", None, consensus_protocol="majority")        # states no classes (a restatement of the protocol)
VA = rec("va", (MW, DW))                                   # A and B
VB = rec("vb", (MW, LW), signer="C", cosigners=("B",))     # C and B, beside VA
VA2 = rec("va", (MW,))
VB2 = rec("vb", ((M, False),), signer="C", cosigners=("B",))   # medical without legal weight, beside VA2
VJ = rec("vj", (MW, LW, DW), heads=("va", "vb"), signer="A", cosigners=("C",))   # names both
VJ0 = rec("vj", None, heads=("va", "vb"), signer="A", cosigners=("C",), consensus_protocol="majority")
V2 = rec("v2", (MW, LW), heads=("v1",))                    # restores legal after v1
V3 = rec("v3", None, heads=("v1",), consensus_protocol="majority")
VE = rec("ve", (MW, LW), dissolves_at=50)                  # a version with its own stated end
DIS = rec("dis", None, dissolved_at=100)                   # a counted dissolution (A and B)
A1 = aff("a1", to=("A",), cls=(MW,))                       # a one-seat affiliation
A1V = rec("a1v", (MW, LW), heads=("a1",), cosigners=(), obj="a1")
A1W = ST.withdraw("a1w", "A", "a1")                         # its one member lays down its seat: no seat is left
A1B = ST.offer("a1b", "A", ("B",), "member", "a1", "group", ("a1",), head=("a1",), cosigners=("B",))  # appoints B
A1VB = rec("a1v", (MW, LW), heads=("a1b",), cosigners=(), obj="a1")          # A alone, of two members
A1VAB = rec("a1v", (MW, LW), heads=("a1b",), cosigners=("B",), obj="a1")     # A and B
CM = aff("cm", cohort=None)                                # a community: no declared cohort
FM = aff("fm", cohort=None, group_kind="family", consensus_protocol="majority")   # a family

# (name, rows, the community, reader's own key or None, the caller's instant or None, the pairs declared or None)
DECLARED = [
    ("the founding record declares its classes, each with its legal weight", [AF], "af", None, None, {MW, LW}),
    ("a counted change that drops legal: medical alone", [AF, V1], "af", None, None, {MW}),
    ("a change below the protocol (one voice of three) concludes nothing: the charter is unchanged",
     [AF, V1L], "af", None, None, {MW, LW}),
    ("a version is the whole record: one stating no classes declares none", [AF, V0], "af", None, None, set()),
    ("and after a drop, a version stating none declares none", [AF, V1, V3], "af", None, None, set()),
    ("a later change restores legal", [AF, V1, V2], "af", None, None, {MW, LW}),
    ("two concurrent versions that differ: the pairs both list", [AF, VA, VB], "af", None, None, {MW}),
    ("two concurrent versions listing medical with different legal weights: neither pair is common",
     [AF, VA2, VB2], "af", None, None, set()),
    ("a version naming both decides", [AF, VA, VB, VJ], "af", None, None, {MW, LW, DW}),
    ("a version naming both that states none declares none", [AF, VA, VB, VJ0], "af", None, None, set()),
    ("a reader holding only one of the two reads it", [AF, VA], "af", None, None, {MW, DW}),
    ("a one-seat affiliation changes its charter alone: a record change is no act against a member",
     [A1, A1V], "a1", None, None, {MW, LW}),
    ("an appointed member is a voice: A alone is one of two, below the protocol", [A1, A1B, A1VB], "a1", None, None, {MW}),
    ("and A with B is two of two", [A1, A1B, A1VAB], "a1", None, None, {MW, LW}),
    ("any community's record is a charter", [CM], "cm", None, None, {MW, LW}),
    ("a family's record is no charter", [FM], "fm", None, None, None),
    ("no founding row held: no charter", [V1], "af", None, None, None),
    ("a dissolved affiliation declares nothing", [AF, DIS], "af", None, None, set()),
    ("an affiliation whose last seat has lapsed is dissolved (no signer): nothing", [A1, A1W], "a1", None, None, set()),
    ("a version's own stated end, not yet reached", [AF, VE], "af", None, 40, {MW, LW}),
    ("and reached: nothing", [AF, VE], "af", None, 60, set()),
    ("with no clock given, the stated end is not read", [AF, VE], "af", None, None, {MW, LW}),
]

LM, LL, LD = lic("lm", M), lic("ll", L), lic("ld", D)
OK, NT, NR = (True, None), (False, "licence_class_not_trusted"), (False, "authority_not_reached")
E0 = [CH.edge("RD", "af")]                                 # trust_classes absent: every class the charter declares
EM = [CH.edge("RD", "af", (M,))]                           # medical only
E_EMPTY = [CH.edge("RD", "af", ())]                        # an empty list: refused at admission, no edge
E_UNSORTED = [CH.edge("RD", "af", (M, L))]                 # not sorted: refused
HOP_ML = [CH.edge("RD", "X", (L, M), 1), CH.edge("X", "af", (M,))]
HOP_ALL = [CH.edge("RD", "X", None, 1), CH.edge("X", "af", (L,))]
HOP_M_THEN_ALL = [CH.edge("RD", "X", (M,), 1), CH.edge("X", "af")]
HOP_SHORT = [CH.edge("RD", "X", None, 0), CH.edge("X", "af")]  # no hop past X

# (name, rows, edges, reader, licence, supplied charters, the caller's instant, (honoured, reason))
LICENCES = [
    ("a class declared is honoured", [AF, LM], E0, "RD", "lm", None, None, OK),
    ("a class the charter does not declare is read and not honoured", [AF, LD], E0, "RD", "ld", None, None, NT),
    ("a class a later amendment drops stops matching, the licence issued before it included",
     [AF, LL, V1], E0, "RD", "ll", None, None, NT),
    ("a licence issued after the drop names the change, and is not honoured either",
     [AF, V1, lic("ll2", L, names=("af", "v1"))], E0, "RD", "ll2", None, None, NT),
    ("a drop below the protocol changes nothing", [AF, LL, V1L], E0, "RD", "ll", None, None, OK),
    ("a reader holding the older version honours the class", [AF, LL], E0, "RD", "ll", None, None, OK),
    ("a reader holding the newer one does not", [AF, LL, V1], E0, "RD", "ll", None, None, NT),
    ("a version stating no classes: nothing is honoured", [AF, LM, V0], E0, "RD", "lm", None, None, NT),
    ("two versions that differ: a class one lists waits", [AF, VA, VB, LD], E0, "RD", "ld", None, None, NT),
    ("and a class both list is honoured", [AF, VA, VB, LM], E0, "RD", "lm", None, None, OK),
    ("until a version names both", [AF, VA, VB, VJ, LD], E0, "RD", "ld", None, None, OK),
    ("trust_classes absent: every class the charter declares", [AF, LL], E0, "RD", "ll", None, None, OK),
    ("trust_classes present: a class it does not list is not reached", [AF, LL], EM, "RD", "ll", None, None, NR),
    ("trust_classes present: a class it lists", [AF, LM], EM, "RD", "lm", None, None, OK),
    ("trust_classes an empty list: the edge is refused, so nothing is reached", [AF, LM], E_EMPTY, "RD", "lm", None,
     None, NR),
    ("trust_classes not sorted: the edge is refused", [AF, LM], E_UNSORTED, "RD", "lm", None, None, NR),
    ("hop by hop: legal admitted at the first hop and not at the second", [AF, LL], HOP_ML, "RD", "ll", None, None, NR),
    ("hop by hop: medical admitted at both", [AF, LM], HOP_ML, "RD", "lm", None, None, OK),
    ("hop by hop: the first hop admits all, the second legal", [AF, LL], HOP_ALL, "RD", "ll", None, None, OK),
    ("hop by hop: the first hop admits medical only, the second all", [AF, LL], HOP_M_THEN_ALL, "RD", "ll", None, None,
     NR),
    ("an edge with no depth left reaches no licensor past it", [AF, LM], HOP_SHORT, "RD", "lm", None, None, NR),
    ("a reader with no edge reaches nothing", [AF, LM], [], "RD", "lm", None, None, NR),
    ("a one-seat affiliation's change adds legal", [A1, A1V, lic("l1", L, "a1")], [CH.edge("RD", "a1")], "RD", "l1",
     None, None, OK),
    ("a community's record declares its classes", [CM, lic("lc", M, "cm")], [CH.edge("RD", "cm")], "RD", "lc", None,
     None, OK),
    ("and not others", [CM, lic("lc", D, "cm")], [CH.edge("RD", "cm")], "RD", "lc", None, None, NT),
    ("a family's record declares nothing", [FM, lic("lf", M, "fm")], [CH.edge("RD", "fm")], "RD", "lf", None, None, NT),
    ("a dissolved affiliation's licences are not honoured", [AF, LM, DIS], E0, "RD", "lm", None, None, NT),
    ("a record whose stated end has passed, at the caller's instant", [AF, VE, LM], E0, "RD", "lm", None, 60, NT),
    ("a charter supplied for the authority meets the one read from rows", [AF, LL], E0, "RD", "ll", {"af": (M,)}, None,
     NT),
    ("and the classes both declare are honoured", [AF, LM], E0, "RD", "lm", {"af": (M,)}, None, OK),
    ("a charter supplied for an authority that is no community held stands alone",
     [lic("lr", L, "RT", names=())], [CH.edge("RD", "RT")], "RD", "lr", {"RT": (L,)}, None, OK),
]

# (trust_classes, the admission's refusal or None)
EDGES = [
    (None, None),
    ((L, M), None),
    ((M,), None),
    ((), "trust_accepts_classes_malformed"),
    ((M, L), "trust_accepts_classes_malformed"),
    ((M, M), "trust_accepts_classes_malformed"),
]

REM = ST.unseat("rm", "A", "C", "member", "af", "group", ("af",), head=("af",), cosigners=("B",), policy="cosigned_act")
# (name, rows, the row asked, the reason it is undecided or None, whether it concludes)
UNDECIDED = [
    ("a counted removal of a member of an affiliation is undecided, naming its row", [AF, REM], "rm",
     "affiliation_remove_member_undecided", False),
    ("a change of the record is not", [AF, V1], "v1", None, True),
]


@contextlib.contextmanager
def planted(plant):
    saved = (set(CH.MUT), set(ST.MUT))
    if plant:
        CH.MUT.add(plant)
        ST.MUT.add(plant)
    try:
        yield
    finally:
        CH.MUT.clear(); CH.MUT |= saved[0]
        ST.MUT.clear(); ST.MUT |= saved[1]


def orders(rows):
    """The rows as given, then other arrival orders up to the cap."""
    return itertools.islice(itertools.permutations(rows), ORDER_CAP)


def arrive(order):
    return CK.arrive(list(order), lambda r, P, past: ST.seat_rule(r, P, past))


def declared_answers(case, every_order=False):
    _name, rows, a, own, now, _want = case
    out = set()
    for o in (orders(rows) if every_order else [rows]):
        d = CH.declared(arrive(o), a, own, now)
        out.add(None if d is None else frozenset(d))
    return out


def licence_answers(case, every_order=False):
    _name, rows, edges, reader, lid, supplied, now, _want = case
    out, kept = set(), True
    for o in (orders(rows) if every_order else [rows]):
        S = arrive(o)
        kept &= bool(S.C.get(lid))
        out.add(CH.read_licence(S, edges, reader, lid, supplied=supplied, now=now))
    return out, kept


def undecided_answer(case):
    _name, rows, rid, _r, _c = case
    S = arrive(rows)
    return ST.affiliation_removal(S.by[rid], S.by), bool(S.C.get(rid))


PLANTS = ("charter_unread", "at_issuance", "below_protocol_read", "fork_union", "fork_first", "join_unread",
          "unstated_keeps", "community_unread", "family_read", "weight_unread", "one_seat_countersign", "at_founding",
          "dissolved_declares", "dissolves_at_unread", "empty_edge_admits_all", "absent_means_none",
          "edge_classes_unread", "last_hop_only", "affiliation_unread", "affiliation_admit_unread",
          "affiliation_removal_passes")


def show(x):
    return x if x is None else sorted(x)


def misses(plant=None, every_order=False):
    hit = []
    with planted(plant):
        for c in DECLARED:
            want = None if c[5] is None else frozenset(c[5])
            got = declared_answers(c, every_order)
            if got != {want}:
                hit.append("declared %s: got %s, expected %s" % (c[0], sorted(map(show, got), key=str), show(want)))
        for c in LICENCES:
            got, kept = licence_answers(c, every_order)
            if got != {c[7]}:
                hit.append("licence %s: got %s, expected %s" % (c[0], sorted(got, key=str), c[7]))
            if not kept:
                hit.append("licence %s: the licence row is not admitted" % c[0])
        for cs, want in EDGES:
            got = CH.edge_refusal(CH.edge("RD", "af", cs))
            if got != want:
                hit.append("edge %s: got %s, expected %s" % (cs, got, want))
        for c in UNDECIDED:
            got = undecided_answer(c)
            if got != (c[3], c[4]):
                hit.append("undecided %s: got %s, expected %s" % (c[0], got, (c[3], c[4])))
    return hit


def main():
    problems = misses(every_order=True)
    caught = 0
    for plant in PLANTS:
        hit = misses(plant)
        caught += bool(hit)
        print("  plant %-27s %s" % (plant, "caught by %d cases, first: %s" % (len(hit), hit[0]) if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % plant)
    for p in problems:
        print(p)
    print("RESULT: %s: %d declared cases, %d licence cases (each in up to %d arrival orders), %d edge cases, %d undecided "
          "cases, %d of %d planted breaks caught" % ("ok" if not problems else "%d problems" % len(problems),
                                                    len(DECLARED), len(LICENCES), ORDER_CAP, len(EDGES), len(UNDECIDED),
                                                    caught, len(PLANTS)))
    return 1 if problems else 0


def fixture(with_refs):
    """The cases with the model's answers, for the crate (tests/charter.rs, through tools/kernel_fixtures.py): rows as
    the models build them, each object a reference (`refs` names them); an edge's ends and an authority are names, a
    row where a row of the case has that id and a key otherwise. `with_refs`: kernel_fixtures.py's. An edge's classes
    are null where trust_classes is absent."""
    out = {"declared": [], "licences": [], "edges": [], "undecided": []}
    for name, rows, a, own, now, _want in DECLARED:
        refs = {}
        d = CH.declared(arrive(rows), a, own, now)
        out["declared"].append({"name": name, "rows": with_refs(rows, refs), "refs": refs, "aff": a, "own": own,
                                "now": now, "declared": None if d is None else [list(p) for p in sorted(d)]})
    for name, rows, edges, reader, lid, supplied, now, _want in LICENCES:
        refs = {}
        S = arrive(rows)
        ok, why = CH.read_licence(S, edges, reader, lid, supplied=supplied, now=now)
        r = S.by[lid]
        out["licences"].append({
            "name": name, "rows": with_refs(rows, refs), "refs": refs, "reader": reader, "now": now,
            "edges": [[e["src"], e["dst"], None if e["classes"] is None else list(e["classes"]), e["depth"]]
                      for e in edges],
            "licence": lid, "authority": r["authority"], "class": r["licence_class"],
            "supplied": {k: sorted(v) for k, v in sorted((supplied or {}).items())},
            "admitted": bool(S.C.get(lid)), "honoured": ok, "reason": why})
    for cs, _want in EDGES:
        out["edges"].append({"classes": None if cs is None else list(cs),
                             "refusal": CH.edge_refusal(CH.edge("RD", "af", cs))})
    for name, rows, rid, _r, _c in UNDECIDED:
        refs = {}
        reason, concludes = undecided_answer((name, rows, rid, None, None))
        out["undecided"].append({"name": name, "rows": with_refs(rows, refs), "refs": refs, "row": rid,
                                 "reason": reason, "concludes": concludes})
    return out


if __name__ == "__main__":
    sys.exit(main())
