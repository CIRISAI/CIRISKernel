#!/usr/bin/env python3
"""
check_charter.py: charter coverage for licensing authorities (charter.py; CC 3.4.7, CC 4.4.3.12, 4.4.3.34).

DECLARED: the classes an affiliation's record in force declares, over the rows a reader holds. LICENCES: whether a
reader honours a licence, and why not. Every licence row of every case is kept and concluded (admitted as a row,
whatever class it states). Every case is read in every arrival order of its rows up to a cap, and gives one answer.

Planted breaks, each of which must change a case's answer:
    charter_unread        the charter is not read: a licence of any class is honoured where the walk reaches
    at_issuance           the charter is read in the licence's own past, not over the reader's rows
    below_protocol_read   a record change that does not conclude under the affiliation's protocol is read
    fork_union            two version tips that differ declare every class either lists (not the common ones)
    fork_first            of two version tips one is in force (the least id)
    join_unread           a version naming both tips decides nothing: every version is read as a tip
    unstated_clears       a version that states no classes declares none
    any_record_kind       a record that is no affiliation's is read as a charter
    one_seat_countersign  a one-seat affiliation's record change is read as an act against a member (countersign)
    at_founding           the founding record's classes stay in force: no version is read
    absent_means_none     an edge listing no trust_classes admits no class
    edge_classes_unread   an edge's trust_classes are not read: every edge admits every class
    last_hop_only         only the hop arriving at the authority is held to its trust_classes
    affiliation_unread    (seat.py) a group kind `affiliation` is not read: the record is a community's, which
                          declares no charter

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


def aff(i="af", to=("A", "B", "C"), cls=(M, L), **kw):
    """An affiliation's founding record: its members, each seated by its own signature, and its charter."""
    return ST.found(i, to[0], to, cosigners=tuple(to[1:]), group_kind="affiliation", licence_classes=tuple(cls), **kw)


def rec(i, cls, heads=("af",), signer="A", cosigners=("B",), obj="af", **kw):
    """A change of the affiliation's record, counted at `heads` (None: it states no classes)."""
    if cls is not None:
        kw["licence_classes"] = tuple(cls)
    return ST.offer(i, signer, (), "record", obj, "group", tuple(heads), head=tuple(heads), cosigners=tuple(cosigners),
                    **kw)


def lic(i, cls, authority="af", names=None):
    return CH.licensure(i, "D", authority, cls, names=(authority,) if names is None else names)


AF = aff()
V1 = rec("v1", (M,))                                       # A and B: two of three, a strict majority
V1L = rec("v1", (M,), signer="A", cosigners=())            # A alone: below the protocol
V0 = rec("v0", None, consensus_protocol="majority")        # states no classes (a restatement of the protocol)
VA = rec("va", (M, D))                                     # A and B
VB = rec("vb", (M, L), signer="C", cosigners=("B",))       # C and B, beside VA
VJ = rec("vj", (M, L, D), heads=("va", "vb"), signer="A", cosigners=("C",))   # names both
VJ0 = rec("vj", None, heads=("va", "vb"), signer="A", cosigners=("C",), consensus_protocol="majority")
V2 = rec("v2", (M, L), heads=("v1",))                      # restores legal after v1
V3 = rec("v3", None, heads=("v1",), consensus_protocol="majority")
A1 = aff("a1", to=("A",), cls=(M,))                        # a one-seat affiliation
A1V = rec("a1v", (M, L), heads=("a1",), cosigners=(), obj="a1")
CM = ST.found("cm", "A", ("A", "B", "C"), cosigners=("B", "C"), licence_classes=(M, L))   # a community, no affiliation

E0 = [CH.edge("RD", "af")]                                 # trust_classes absent: every class the charter declares
EM = [CH.edge("RD", "af", (M,))]                           # medical only
HOP_ML = [CH.edge("RD", "X", (M, L), 1), CH.edge("X", "af", (M,))]
HOP_ALL = [CH.edge("RD", "X", (), 1), CH.edge("X", "af", (L,))]
HOP_M_THEN_ALL = [CH.edge("RD", "X", (M,), 1), CH.edge("X", "af")]
HOP_SHORT = [CH.edge("RD", "X", (), 0), CH.edge("X", "af")]  # no hop past X

# (name, rows, affiliation, reader's own key or None, the classes declared or None)
DECLARED = [
    ("the founding record declares its classes", [AF], "af", None, {M, L}),
    ("a counted change that drops legal: medical alone", [AF, V1], "af", None, {M}),
    ("a change below the protocol (one voice of three) concludes nothing: the charter is unchanged",
     [AF, V1L], "af", None, {M, L}),
    ("a change that states no classes leaves them as they were", [AF, V0], "af", None, {M, L}),
    ("and after a drop, the dropped classes stay dropped", [AF, V1, V3], "af", None, {M}),
    ("a later change restores legal", [AF, V1, V2], "af", None, {M, L}),
    ("two concurrent versions that differ: the classes both list", [AF, VA, VB], "af", None, {M}),
    ("a version naming both decides", [AF, VA, VB, VJ], "af", None, {M, L, D}),
    ("a version naming both that states none keeps the common classes", [AF, VA, VB, VJ0], "af", None, {M}),
    ("a reader holding only one of the two reads it", [AF, VA], "af", None, {M, D}),
    ("a one-seat affiliation changes its charter alone: a record change is no act against a member",
     [A1, A1V], "a1", None, {M, L}),
    ("a community's record is no charter", [CM], "cm", None, None),
    ("no founding row held: no charter", [V1], "af", None, None),
]

LM, LL, LD = lic("lm", M), lic("ll", L), lic("ld", D)
OK, NT, NR = (True, None), (False, "licence_class_not_trusted"), (False, "authority_not_reached")

# (name, rows, edges, reader, licence, supplied charters, (honoured, reason))
LICENCES = [
    ("a class declared is honoured", [AF, LM], E0, "RD", "lm", None, OK),
    ("a class the charter does not declare is read and not honoured", [AF, LD], E0, "RD", "ld", None, NT),
    ("a class a later amendment drops stops matching, the licence issued before it included",
     [AF, LL, V1], E0, "RD", "ll", None, NT),
    ("a licence issued after the drop names the change, and is not honoured either",
     [AF, V1, lic("ll2", L, names=("af", "v1"))], E0, "RD", "ll2", None, NT),
    ("a drop below the protocol changes nothing", [AF, LL, V1L], E0, "RD", "ll", None, OK),
    ("a reader holding the older version honours the class", [AF, LL], E0, "RD", "ll", None, OK),
    ("a reader holding the newer one does not", [AF, LL, V1], E0, "RD", "ll", None, NT),
    ("two versions that differ: a class one lists waits", [AF, VA, VB, LD], E0, "RD", "ld", None, NT),
    ("and a class both list is honoured", [AF, VA, VB, LM], E0, "RD", "lm", None, OK),
    ("until a version names both", [AF, VA, VB, VJ, LD], E0, "RD", "ld", None, OK),
    ("trust_classes absent: every class the charter declares", [AF, LL], E0, "RD", "ll", None, OK),
    ("trust_classes present: a class it does not list is not reached", [AF, LL], EM, "RD", "ll", None, NR),
    ("trust_classes present: a class it lists", [AF, LM], EM, "RD", "lm", None, OK),
    ("hop by hop: legal admitted at the first hop and not at the second", [AF, LL], HOP_ML, "RD", "ll", None, NR),
    ("hop by hop: medical admitted at both", [AF, LM], HOP_ML, "RD", "lm", None, OK),
    ("hop by hop: the first hop admits all, the second legal", [AF, LL], HOP_ALL, "RD", "ll", None, OK),
    ("hop by hop: the first hop admits medical only, the second all", [AF, LL], HOP_M_THEN_ALL, "RD", "ll", None, NR),
    ("an edge with no depth left reaches no licensor past it", [AF, LM], HOP_SHORT, "RD", "lm", None, NR),
    ("a reader with no edge reaches nothing", [AF, LM], [], "RD", "lm", None, NR),
    ("a one-seat affiliation's change adds legal", [A1, A1V, lic("l1", L, "a1")], [CH.edge("RD", "a1")], "RD", "l1",
     None, OK),
    ("a community's record declares nothing", [CM, lic("lc", M, "cm")], [CH.edge("RD", "cm")], "RD", "lc", None, NT),
    ("a charter supplied for the authority meets the one read from rows", [AF, LL], E0, "RD", "ll", {"af": (M,)}, NT),
    ("and the classes both declare are honoured", [AF, LM], E0, "RD", "lm", {"af": (M,)}, OK),
    ("a charter supplied for an authority that is no affiliation held stands alone",
     [lic("lr", L, "RT", names=())], [CH.edge("RD", "RT")], "RD", "lr", {"RT": (L,)}, OK),
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
    _name, rows, a, own, _want = case
    out = set()
    for o in (orders(rows) if every_order else [rows]):
        d = CH.declared(arrive(o), a, own)
        out.add(None if d is None else frozenset(d))
    return out


def licence_answers(case, every_order=False):
    _name, rows, edges, reader, lid, supplied, _want = case
    out, kept = set(), True
    for o in (orders(rows) if every_order else [rows]):
        S = arrive(o)
        kept &= bool(S.C.get(lid))
        out.add(CH.read_licence(S, edges, reader, lid, supplied=supplied))
    return out, kept


PLANTS = ("charter_unread", "at_issuance", "below_protocol_read", "fork_union", "fork_first", "join_unread",
          "unstated_clears", "any_record_kind", "one_seat_countersign", "at_founding", "absent_means_none",
          "edge_classes_unread", "last_hop_only", "affiliation_unread")


def misses(plant=None, every_order=False):
    hit = []
    with planted(plant):
        for c in DECLARED:
            want = None if c[4] is None else frozenset(c[4])
            got = declared_answers(c, every_order)
            if got != {want}:
                hit.append("declared %s: got %s, expected %s" % (c[0], sorted(map(lambda x: x and sorted(x), got),
                                                                              key=str), want and sorted(want)))
        for c in LICENCES:
            got, kept = licence_answers(c, every_order)
            if got != {c[6]}:
                hit.append("licence %s: got %s, expected %s" % (c[0], sorted(got, key=str), c[6]))
            if not kept:
                hit.append("licence %s: the licence row is not admitted" % c[0])
    return hit


def fixture(with_refs):
    """The cases with the model's answers, for the crate (tests/charter.rs, through tools/kernel_fixtures.py): rows as
    the models build them, each object a reference (`refs` names them); an edge's ends and an authority are names, a
    row where a row of the case has that id and a key otherwise. `with_refs`: kernel_fixtures.py's."""
    out = {"declared": [], "licences": []}
    for name, rows, a, own, _want in DECLARED:
        refs = {}
        d = CH.declared(arrive(rows), a, own)
        out["declared"].append({"name": name, "rows": with_refs(rows, refs), "refs": refs, "aff": a, "own": own,
                                "declared": None if d is None else sorted(d)})
    for name, rows, edges, reader, lid, supplied, _want in LICENCES:
        refs = {}
        S = arrive(rows)
        ok, why = CH.read_licence(S, edges, reader, lid, supplied=supplied)
        r = S.by[lid]
        out["licences"].append({
            "name": name, "rows": with_refs(rows, refs), "refs": refs, "reader": reader,
            "edges": [[e["src"], e["dst"], list(e["classes"]), e["depth"]] for e in edges],
            "licence": lid, "authority": r["authority"], "class": r["licence_class"],
            "supplied": {k: sorted(v) for k, v in sorted((supplied or {}).items())},
            "admitted": bool(S.C.get(lid)), "honoured": ok, "reason": why})
    return out


def main():
    problems = misses(every_order=True)
    caught = 0
    for plant in PLANTS:
        hit = misses(plant)
        caught += bool(hit)
        print("  plant %-22s %s" % (plant, "caught by %d cases, first: %s" % (len(hit), hit[0]) if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % plant)
    for p in problems:
        print(p)
    print("RESULT: %s: %d declared cases, %d licence cases (each in up to %d arrival orders), %d of %d planted breaks "
          "caught" % ("ok" if not problems else "%d problems" % len(problems), len(DECLARED), len(LICENCES), ORDER_CAP,
                      caught, len(PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
