#!/usr/bin/env python3
"""
check_trust_rows.py: the reader's trust walk from rows, and the issuer's standing (trust_rows.py; CC 4.4.3.34).

CASES: whether a reader honours a licence, and why not, with the acceptance edges read from rows (`delegates_to`
bearing trust:accepts:v1) under the rulings this model reads until the Constitution's land (trust_rows.PENDING), or
under a stand-in (MEMBERS: a member of a community speaks for it and issues its licences) that shows where a ruling
plugs in. REFUSALS: the admission of an edge row. Every case is read in every arrival order of its rows up to a cap.

Planted breaks, each of which must change a case's answer:
    edge_any_signer     an edge speaking for another is counted whoever signs it
    bears_unread        a delegates_to row not bearing trust:accepts:v1 is read as an edge
    refusal_unread      an edge's malformed trust_classes are not refused
    depth_unread        an edge's depth outside 0 to 5 is capped, not refused
    withdrawn_unread    a withdrawn edge is walked
    withdraw_by_anyone  a withdrawal held ends the edge whoever signed it, concluded or not
    issuer_unread       any key's licence is the authority's act
    pending_silent      an edge whose owner a pending ruling leaves undecided is walked as decided

    python3 -I check_trust_rows.py      exit 1 on any difference
"""
import contextlib
import itertools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import trust_rows as TR  # noqa: E402

CH, ST, CK = TR.CH, TR.ST, TR.CK
ORDER_CAP = 24
M, L = "medical", "legal"
A = TR.accepts


class Members(TR.Rulings):
    """A stand-in for rulings (a) and (b), to show where they plug in: a member of a community speaks for it, and a
    licence a member signs is its act."""

    def _member(self, S, k, g):
        return k in ST.Seats(S).holders("member", g)

    def speaks_for(self, S, r, src):
        return self._member(S, r["signer"], src) if TR.is_community(S, src) else super().speaks_for(S, r, src)

    def issued_by(self, S, lic, auth):
        return self._member(S, lic["signer"], auth) if TR.is_community(S, auth) else super().issued_by(S, lic, auth)


MEMBERS = Members()
AF = ST.found("af", "A", ("A", "B", "C"), cosigners=("B", "C"), declared_cohort="affiliations",
              licence_classes=((M, True), (L, False)))
KCH = {"K": (M, L)}                                         # a key authority's charter, supplied (the root's, say)


def klic(i, cls=M, signer="K"):
    return CH.licensure(i, signer, "K", cls)


def alic(i, cls=M, signer="A"):
    return CH.licensure(i, signer, "af", cls, names=("af",))


OK, NR = (True, None), (False, "authority_not_reached")
# (name, rows, reader, licence, supplied, rulings, (honoured, reason))
CASES = [
    ("the reader's own edge to a key authority, its licence signed by it", [A("e", "RD", "K"), klic("l")], "RD", "l",
     KCH, None, OK),
    ("an edge a key signs for the reader is not the reader's", [A("e", "X", "K", on_behalf="RD"), klic("l")], "RD",
     "l", KCH, None, NR),
    ("another key's own edge is not the reader's", [A("e", "X", "K"), klic("l")], "RD", "l", KCH, None, NR),
    ("a delegates_to bearing something else is no edge", [A("e", "RD", "K", bears="other"), klic("l")], "RD", "l",
     KCH, None, NR),
    ("trust_classes an empty list: refused, no edge", [A("e", "RD", "K", ()), klic("l")], "RD", "l", KCH, None, NR),
    ("trust_classes not sorted: refused", [A("e", "RD", "K", (M, L)), klic("l")], "RD", "l", KCH, None, NR),
    ("trust_classes listing the class", [A("e", "RD", "K", (L, M)), klic("l")], "RD", "l", KCH, None, OK),
    ("trust_classes not listing it", [A("e", "RD", "K", (L,)), klic("l")], "RD", "l", KCH, None, NR),
    ("a depth outside 0 to 5 is refused (ruling (c), pending)",
     [A("e", "RD", "X", depth=6), A("f", "X", "K"), klic("l")], "RD", "l", KCH, None, NR),
    ("an onward hop from the authority's own edge", [A("e", "RD", "X", depth=1), A("f", "X", "K"), klic("l")], "RD",
     "l", KCH, None, OK),
    ("the classes intersect hop by hop", [A("e", "RD", "X", (L,), 1), A("f", "X", "K"), klic("l")], "RD", "l", KCH,
     None, NR),
    ("depth 0: no hop past the first authority", [A("e", "RD", "X", depth=0), A("f", "X", "K"), klic("l")], "RD", "l",
     KCH, None, NR),
    ("a cycle is visited once and the walk goes on",
     [A("e", "RD", "X", depth=3), A("f", "X", "RD", depth=3), A("g", "X", "K"), klic("l")], "RD", "l", KCH, None, OK),
    ("a cycle that reaches nothing ends", [A("e", "RD", "X", depth=5), A("f", "X", "RD", depth=5), klic("l")], "RD",
     "l", KCH, None, NR),
    ("an edge withdrawn by its signer is no edge (ruling (d), pending)",
     [A("e", "RD", "K"), ST.withdraw("w", "RD", "e"), klic("l")], "RD", "l", KCH, None, NR),
    ("a withdrawal by another key ends nothing", [A("e", "RD", "K"), ST.withdraw("w", "X", "e"), klic("l")], "RD",
     "l", KCH, None, OK),
    ("a licence another key signs is not the key authority's act", [A("e", "RD", "K"), klic("l", signer="X")], "RD",
     "l", KCH, None, (False, "licence_not_the_authoritys_act")),
    ("a class the charter does not declare", [A("e", "RD", "K"), klic("l", "dental")], "RD", "l", KCH, None,
     (False, "licence_class_not_trusted")),
    ("a community authority's licence: the issuer's standing is pending (ruling (b))",
     [AF, A("e", "RD", "af"), alic("l")], "RD", "l", None, None, (False, "issuer_standing_pending")),
    ("under the stand-in, a member's licence is the community's act", [AF, A("e", "RD", "af"), alic("l")], "RD", "l",
     None, MEMBERS, OK),
    ("and a non-member's is not", [AF, A("e", "RD", "af"), alic("l", signer="Z")], "RD", "l", None, MEMBERS,
     (False, "licence_not_the_authoritys_act")),
    ("an onward edge a member signs for the community: its authority set is pending (ruling (a))",
     [AF, A("e", "RD", "af", depth=1), A("f", "B", "K", on_behalf="af"), klic("l")], "RD", "l", KCH, None,
     (False, "authority_set_pending")),
    ("under the stand-in it is the community's own edge",
     [AF, A("e", "RD", "af", depth=1), A("f", "B", "K", on_behalf="af"), klic("l")], "RD", "l", KCH, MEMBERS, OK),
    ("and one a non-member signs for it is not", [AF, A("e", "RD", "af", depth=1), A("f", "Z", "K", on_behalf="af"),
                                                  klic("l")], "RD", "l", KCH, MEMBERS, NR),
]

# (name, the edge row, the refusal or None)
REFUSALS = [
    ("absent classes", A("e", "RD", "K"), None),
    ("a sorted list", A("e", "RD", "K", (L, M)), None),
    ("an empty list", A("e", "RD", "K", ()), "trust_accepts_classes_malformed"),
    ("an unsorted list", A("e", "RD", "K", (M, L)), "trust_accepts_classes_malformed"),
    ("a class twice", A("e", "RD", "K", (M, M)), "trust_accepts_classes_malformed"),
    ("depth 5", A("e", "RD", "K", depth=5), None),
    ("depth 6", A("e", "RD", "K", depth=6), "trust_accepts_depth_malformed"),
    ("a negative depth", A("e", "RD", "K", depth=-1), "trust_accepts_depth_malformed"),
]

REF_FIELDS = ("dst", "on_behalf", "authority")      # the objects an edge row and a licence name, for the fixture

PLANTS = ("edge_any_signer", "bears_unread", "refusal_unread", "depth_unread", "withdrawn_unread",
          "withdraw_by_anyone", "issuer_unread", "pending_silent")


@contextlib.contextmanager
def planted(plant):
    saved = set(TR.MUT)
    if plant:
        TR.MUT.add(plant)
    try:
        yield
    finally:
        TR.MUT.clear(); TR.MUT |= saved


def arrive(order):
    return CK.arrive(list(order), lambda r, P, past: ST.seat_rule(r, P, past))


def answers(case, every_order=False):
    _name, rows, reader, lid, supplied, rulings, _want = case
    out, kept = set(), True
    for o in (itertools.islice(itertools.permutations(rows), ORDER_CAP) if every_order else [rows]):
        S = arrive(o)
        kept &= bool(S.C.get(lid))
        out.add(TR.read_licence(S, reader, lid, supplied=supplied, rulings=rulings or TR.PENDING))
    return out, kept


def misses(plant=None, every_order=False):
    hit = []
    with planted(plant):
        for c in CASES:
            got, kept = answers(c, every_order)
            if got != {c[6]}:
                hit.append("%s: got %s, expected %s" % (c[0], sorted(got, key=str), c[6]))
            if not kept:
                hit.append("%s: the licence row is not admitted" % c[0])
        for name, r, want in REFUSALS:
            if TR.refusal(r) != want:
                hit.append("refusal %s: got %s, expected %s" % (name, TR.refusal(r), want))
    return hit


def main():
    problems = misses(every_order=True)
    caught = 0
    for plant in PLANTS:
        hit = misses(plant)
        caught += bool(hit)
        print("  plant %-20s %s" % (plant, "caught by %d cases, first: %s" % (len(hit), hit[0]) if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % plant)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases (each in up to %d arrival orders), %d refusal cases, %d of %d planted breaks caught"
          % ("ok" if not problems else "%d problems" % len(problems), len(CASES), ORDER_CAP, len(REFUSALS), caught,
             len(PLANTS)))
    return 1 if problems else 0


def fixture(with_refs):
    """The cases with the model's answers, for the crate (tests/trust_rows.rs, through tools/kernel_fixtures.py). The
    stand-in rulings are named (`rulings`: `pending` or `members`); the crate's test builds its own."""
    out = {"cases": [], "refusals": []}
    for name, rows, reader, lid, supplied, rulings, _want in CASES:
        refs = {}
        S = arrive(rows)
        ok, why = TR.read_licence(S, reader, lid, supplied=supplied, rulings=rulings or TR.PENDING)
        out["cases"].append({"name": name, "rows": with_refs(rows, refs), "refs": refs, "reader": reader,
                             "licence": lid, "supplied": {k: sorted(v) for k, v in sorted((supplied or {}).items())},
                             "rulings": "members" if rulings is MEMBERS else "pending", "honoured": ok, "reason": why})
    for name, r, _want in REFUSALS:
        refs = {}
        out["refusals"].append({"name": name, "rows": with_refs([r], refs), "refs": refs, "refusal": TR.refusal(r)})
    return out


if __name__ == "__main__":
    sys.exit(main())
