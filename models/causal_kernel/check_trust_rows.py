#!/usr/bin/env python3
"""
check_trust_rows.py: the reader's trust walk from rows, and the issuer's standing (trust_rows.py; CC 4.4.3.34, CC
4.5.4), under the Constitution's rulings (a) to (d) of 2026-11-27.

CASES: whether a reader honours a licence, and why not, with the acceptance edges read from rows (`delegates_to`
bearing trust:accepts:v1). REFUSALS: the admission of an edge row. Every case is read in every arrival order of its
rows up to a cap, and gives one answer.

Planted breaks, each of which must change a case's answer:
    edge_any_signer          an edge is its owner's whoever signs it
    roster_unread            (a) a person's roster keys do not speak for it
    duty_unread              (a) a community's edge is counted over its members, not its duty holders
    lock_unread              (a), (b) a community with no duty holder is not locked: its members' count stands in
    quorum_fixed_majority    (b) a community's own licence is counted as a strict majority, not its declared protocol
    roster_issuer_unread     (b) a live key of a person's roster is not the person
    license_seat_unread      (seat.py) a license seat over a community is no act: its duty holders confer none
    term_unread              (b) a license seat's term is not read: its holder issues after the term ends
    affiliation_edge_duty_count  (a) an affiliation's edge is counted as a duty conferral, not under its declared protocol
    dissolved_edges_kept     (d) a dissolved authority's own edges are walked
    lapsed_unread            (d) a dissolved authority's licences are read as live, not lapsed
    lapsed_class_unread      (d) a dissolved authority's licence reads lapsed whatever class it states
    pending_unread           (a) the acts row accept / trust_edge / community is not read
    judged_at_read           (a), (b) authority is judged over the reader's rows, not the row's own past
    bears_unread             a delegates_to row not bearing trust:accepts:v1 is read as an edge
    refusal_unread           an edge's malformed trust_classes are not refused
    depth_unread             (c) an edge's depth above 5 is capped, not refused
    depth_absent_refused     (c) an absent trust_depth is refused, not read as 0
    withdrawn_unread         (d) a withdrawn edge is walked
    withdraw_by_anyone       (d) a withdrawal of an edge by any signer of it ends it
    issuer_unread            (b) any key's licence is the authority's act
    chain_unread             (b) a license seat is not read: only the authority's own key issues
    quorum_unread            (b) a community's licence cosigned by its quorum is not its act
    ends_unread              (d) the ends the reader holds are not read over its rows: only the licence's own past
    cut_unread               (d) an end cuts nothing concurrent with it (the lay-downs leave a concurrent conferral)
    self_seat_ungated        (seat.py) a single key's offer of an officer or license seat over a group is not gated by
                             its authority body: a founding signer's own offer revives a locked or dissolved group
    untimed_term_met         (b) a licence stating no instant meets a term-bearing seat's term
    instant_unread           (b) a licence may state an instant earlier than a row it cites
    edge_term_unread         (d) an edge's own term is not read

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

AF = ST.found("af", "A", ("A", "B", "C"), cosigners=("B", "C"), declared_cohort="affiliations",
              licence_classes=((M, True), (L, False)))           # no officer: an affiliation DISSOLVED (CC 4.4.3.12)
AFD = ST.found("af", "A", ("A", "B", "C"), {ST.OFFICER: ("A", "B", "C")}, cosigners=("B", "C"),
               declared_cohort="affiliations", licence_classes=((M, True), (L, False)))   # three officers: majority declared
AFD1 = ST.found("af", "A", ("A", "B", "C"), {ST.OFFICER: ("A",)}, cosigners=("B", "C"), declared_cohort="affiliations",
                licence_classes=((M, True), (L, False)))         # one officer: its authority (the body is its officers)
AFU = dict(AFD, consensus_protocol="unanimous")                  # unanimous declared
GN = ST.found("g", "A", ("A", "B", "C"), cosigners=("B", "C"), licence_classes=((M, False),))   # no duty holder
# the community confers a license seat on X by its duty holders' count (A and B of two), X accepts
GLO = ST.offer("glo", "A", ("X",), "license", "g", "group", ("g",), head=("g",), cosigners=("B",), counted="duty")
GLO1 = ST.offer("glo", "A", ("X",), "license", "g", "group", ("g",), head=("g",), counted="duty")      # A alone
GLA = ST.accept("gla", "X", "glo")
GLU = ST.unseat("glu", "A", "X", "license", "g", "group", ("glo", "gla"), head=("glo",), cosigners=("B",),
                counted="duty", policy="duty_withdraw")          # the duty holders withdraw it
# a lone duty holder A confers a license seat on X, then lays down its duty: no duty holder is left
G1LO = ST.offer("glo", "A", ("X",), "license", "g", "group", ("g",), head=("g",), counted="duty")
G1LD = ST.withdraw("ld", "A", "g", ("glo", "gla"), scope="moderate")
G1LT = dict(G1LO, asserted_at=10, expires_at=100)                # the same seat, with its term
# an affiliation's license seat: its body's count under its declared protocol (majority: two of three)
ALO = ST.offer("alo", "A", ("X",), "license", "af", "group", ("af",), head=("af",), cosigners=("B",), counted=ST.OFFICER)
ALO1 = ST.offer("alo", "A", ("X",), "license", "af", "group", ("af",), head=("af",), counted=ST.OFFICER)
ALA = ST.accept("ala", "X", "alo")
# the affiliation's dissolution, by two of its three officers under its protocol, naming `names`
ADIS = lambda i, names: ST.offer(i, "A", (), "record", "af", "group", tuple(names) + ("af",), head=("af",),
                                 cosigners=("B",), counted=ST.OFFICER, dissolved_at=100)
# the person K's roster seats its key d
KRO, KRA = ST.offer("kro", "K", ("d",), "key", "K", "self"), ST.accept("kra", "d", "kro")
GD = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("A", "B")}, cosigners=("B", "C"),
              licence_classes=((M, False),))                     # duty holders A and B
G1 = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("A",)}, cosigners=("B", "C"),
              licence_classes=((M, False),))                     # a lone duty holder
KCH = {"K": (M, L)}                                              # a key authority's charter, supplied (the root's, say)
# the reader's roster: RD seats its key d
RO, RA = ST.offer("ro", "RD", ("d",), "key", "RD", "self"), ST.accept("ra", "d", "ro")
RU = ST.unseat("ru", "RD", "d", "key", "RD", "self", ("e",))     # RD removes d, after d's edge
# a license seat over K: K confers it on X (sub-delegation), X on Y
LO, LA = ST.offer("lo", "K", ("X",), "license", "K", "self", sub=True), ST.accept("la", "X", "lo")
LO2, LA2 = ST.offer("lo2", "X", ("Y",), "license", "K", "seat", ("lo", "la"), under="lo"), ST.accept("la2", "Y", "lo2")


def klic(i, cls=M, signer="K", names=()):
    return CH.licensure(i, signer, "K", cls, names=names)


def glic(i, auth="af", signer="A", cosigners=(), cls=M):
    r = CH.licensure(i, signer, auth, cls, names=(auth,))
    return dict(r, cosigners=tuple(cosigners)) if cosigners else r


OK, NR = (True, None), (False, "authority_not_reached")
NA, LW = (False, "licensure_delegator_not_authority"), (False, "licensure_link_withdrawn")
E0 = A("e", "RD", "K")
# (name, rows, reader, licence, supplied, (honoured, reason))
CASES = [
    ("the reader's own edge to a key authority, its licence signed by it", [E0, klic("l")], "RD", "l", KCH, OK),
    ("an edge another key signs for the reader is not the reader's", [A("e", "X", "K", on_behalf="RD"), klic("l")],
     "RD", "l", KCH, NR),
    ("another key's own edge is not the reader's", [A("e", "X", "K"), klic("l")], "RD", "l", KCH, NR),
    ("(a) a live key of the reader's roster signs the reader's edge",
     [RO, RA, A("e", "d", "K", on_behalf="RD", names=("ra",)), klic("l")], "RD", "l", KCH, OK),
    ("(a) the roster key's seat not in the edge's past: not the reader's",
     [RO, RA, A("e", "d", "K", on_behalf="RD"), klic("l")], "RD", "l", KCH, NR),
    ("(d) the key removed after the edge: the edge stands (judged over its own past)",
     [RO, RA, A("e", "d", "K", on_behalf="RD", names=("ra",)), RU, klic("l")], "RD", "l", KCH, OK),
    ("a delegates_to bearing something else is no edge", [A("e", "RD", "K", bears="other"), klic("l")], "RD", "l",
     KCH, NR),
    ("trust_classes an empty list: refused, no edge", [A("e", "RD", "K", ()), klic("l")], "RD", "l", KCH, NR),
    ("trust_classes not sorted: refused", [A("e", "RD", "K", (M, L)), klic("l")], "RD", "l", KCH, NR),
    ("trust_classes listing the class", [A("e", "RD", "K", (L, M)), klic("l")], "RD", "l", KCH, OK),
    ("trust_classes not listing it", [A("e", "RD", "K", (L,)), klic("l")], "RD", "l", KCH, NR),
    ("(c) a depth below 0 is refused", [A("e", "RD", "K", depth=-1), klic("l")], "RD", "l", KCH, NR),
    ("(c) a depth above 5 is refused", [A("e", "RD", "X", depth=6), A("f", "X", "K"), klic("l")], "RD", "l", KCH, NR),
    ("(c) an onward hop at depth 1", [A("e", "RD", "X", depth=1), A("f", "X", "K"), klic("l")], "RD", "l", KCH, OK),
    ("(c) depth absent reads as 0: no hop past the first authority", [A("e", "RD", "X"), A("f", "X", "K"), klic("l")],
     "RD", "l", KCH, NR),
    ("the classes intersect hop by hop", [A("e", "RD", "X", (L,), 1), A("f", "X", "K"), klic("l")], "RD", "l", KCH,
     NR),
    ("a cycle is visited once and the walk goes on",
     [A("e", "RD", "X", depth=3), A("f", "X", "RD", depth=3), A("g", "X", "K"), klic("l")], "RD", "l", KCH, OK),
    ("a cycle that reaches nothing ends", [A("e", "RD", "X", depth=5), A("f", "X", "RD", depth=5), klic("l")], "RD",
     "l", KCH, NR),
    ("(d) the reader's own removal of its edge revokes at once", [E0, ST.withdraw("w", "RD", "e"), klic("l")], "RD",
     "l", KCH, NR),
    ("(d) a withdrawal by another key ends nothing", [E0, ST.withdraw("w", "X", "e"), klic("l")], "RD", "l", KCH, OK),
    ("(a) a community's onward edge, two of its two duty holders",
     [GD, A("e", "RD", "g", depth=1), A("f", "A", "K", on_behalf="g", names=("g",), cosigners=("B",)), klic("l")],
     "RD", "l", KCH, OK),
    ("(a) one of two duty holders is not its authority set",
     [GD, A("e", "RD", "g", depth=1), A("f", "A", "K", on_behalf="g", names=("g",)), klic("l")], "RD", "l", KCH, NR),
    ("(a) a member who holds no duty is not either",
     [GD, A("e", "RD", "g", depth=1), A("f", "C", "K", on_behalf="g", names=("g",), cosigners=("A",)), klic("l")],
     "RD", "l", KCH, NR),
    ("(a) a lone duty holder alone",
     [G1, A("e", "RD", "g", depth=1), A("f", "A", "K", on_behalf="g", names=("g",)), klic("l")], "RD", "l", KCH, OK),
    ("(a) a community with no duty holder: LOCKED, no edge, whatever the members sign",
     [GN, A("e", "RD", "g", depth=1), A("f", "A", "K", on_behalf="g", names=("g",), cosigners=("B", "C")),
      klic("l")], "RD", "l", KCH, NR),
    ("(a) an affiliation with no officer: DISSOLVED (CC 4.4.3.12), no edge, whatever the members sign",
     [AF, A("e", "RD", "af", depth=1), A("f", "A", "K", on_behalf="af", names=("af",), cosigners=("B", "C")),
      klic("l")], "RD", "l", KCH, NR),
    ("(a) an affiliation with one officer: its officer alone signs the edge (its authority is its officers)",
     [AFD1, A("e", "RD", "af", depth=1), A("f", "A", "K", on_behalf="af", names=("af",)), klic("l")], "RD", "l", KCH,
     OK),
    ("(a) an affiliation's edge is its officers' act under its declared protocol: two of three officers",
     [AFD, A("e", "RD", "af", depth=1), A("f", "A", "K", on_behalf="af", names=("af",), cosigners=("B",)), klic("l")],
     "RD", "l", KCH, OK),
    ("(a) under a declared unanimous protocol two of three officers sign no edge",
     [AFU, A("e", "RD", "af", depth=1), A("f", "A", "K", on_behalf="af", names=("af",), cosigners=("B",)), klic("l")],
     "RD", "l", KCH, NR),
    ("(a) its lone duty holder signs the edge, before it lays its duty down",
     [G1, G1LO, GLA, A("e", "RD", "g", depth=1), A("f", "A", "K", on_behalf="g", names=("gla",)), klic("l")],
     "RD", "l", KCH, OK),
    ("(a) after: locked, and the license seat's holder keeps it from locking: no edge",
     [G1, G1LO, GLA, G1LD, A("e", "RD", "g", depth=1), A("f", "A", "K", on_behalf="g", names=("ld",)), klic("l")],
     "RD", "l", KCH, NR),
    ("(b) and its members' quorum issues no licence of its own",
     [G1, G1LO, GLA, G1LD, A("e", "RD", "g"), glic("l", "g", cosigners=("B",)) | {"names": ("ld",)}], "RD", "l",
     None, (False, "licensure_authority_locked")),
    ("(d) a community's edge withdrawn by one duty holder alone stands",
     [GD, A("e", "RD", "g", depth=1), A("f", "A", "K", on_behalf="g", names=("g",), cosigners=("B",)),
      ST.withdraw("w", "A", "f"), klic("l")], "RD", "l", KCH, OK),
    ("(d) and by its authority set it ends",
     [GD, A("e", "RD", "g", depth=1), A("f", "A", "K", on_behalf="g", names=("g",), cosigners=("B",)),
      dict(ST.withdraw("w", "A", "f"), cosigners=("B",)), klic("l")], "RD", "l", KCH, NR),
    ("(b) a licence another key signs is testimony", [E0, klic("l", signer="Z")], "RD", "l", KCH, NA),
    ("(b) a license seat holder's licence, naming its seat", [E0, LO, LA, klic("l", signer="X", names=("la",))], "RD",
     "l", KCH, OK),
    ("(b) the seat not in the licence's past: testimony", [E0, LO, LA, klic("l", signer="X")], "RD", "l", KCH, NA),
    ("(b) a delegation chain that resolves to the authority",
     [E0, LO, LA, LO2, LA2, klic("l", signer="Y", names=("la2",))], "RD", "l", KCH, OK),
    ("(d) the link withdrawn in the licence's own past: testimony",
     [E0, LO, LA, ST.withdraw("w", "K", "lo", ("la",)), klic("l", signer="X", names=("w",))], "RD", "l", KCH, NA),
    ("(d) a withdrawal concurrent with the issuance holds it out of force",
     [E0, LO, LA, ST.withdraw("w", "K", "lo", ("la",)), klic("l", signer="X", names=("la",))], "RD", "l", KCH, LW),
    ("(d) a withdrawal after the issuance reaches nothing back",
     [E0, LO, LA, klic("l", signer="X", names=("la",)), ST.withdraw("w", "K", "lo", ("l",))], "RD", "l", KCH, OK),
    ("(b) a community's licence cosigned by its quorum under its declared majority",
     [AFD, A("e", "RD", "af"), glic("l", cosigners=("B",))], "RD", "l", None, OK),
    ("(b) one member's is testimony", [AFD, A("e", "RD", "af"), glic("l")], "RD", "l", None, NA),
    ("(b) under a declared unanimous protocol two of three are not its quorum",
     [AFU, A("e", "RD", "af"), glic("l", cosigners=("B",))], "RD", "l", None, NA),
    ("(b) and three of three are", [AFU, A("e", "RD", "af"), glic("l", cosigners=("B", "C"))], "RD", "l", None, OK),
    ("(b) an affiliation with no officer is dissolved: its members' licence has no standing over its own past",
     [AF, A("e", "RD", "af"), glic("l", cosigners=("B", "C"))], "RD", "l", None, NA),
    ("(d) a licence issued before the affiliation's dissolution stands and reads lapsed",
     [AFD, A("e", "RD", "af"), glic("l", cosigners=("B",)), ADIS("dis", ("l",))], "RD", "l", None, (False, "lapsed")),
    ("(d) a dissolved authority's licence of a class its record did not declare at issuance never stood",
     [AFD, A("e", "RD", "af"), glic("l", cosigners=("B",), cls="dental"), ADIS("dis", ("l",))], "RD", "l", None,
     (False, "licence_class_not_trusted")),
    ("(d) one issued after it is testimony", [AFD, A("e", "RD", "af"), ADIS("dis", ("af",)),
                                             glic("l", cosigners=("B",)) | {"names": ("dis",)}], "RD", "l", None, NA),
    ("(d) a dissolved authority's own edges end with its record: no hop through it",
     [AFD, A("e", "RD", "af", depth=1), A("f", "A", "K", on_behalf="af", names=("af",), cosigners=("B",)),
      ADIS("dis", ("f",)), klic("l")], "RD", "l", KCH, NR),
    ("(b) a locked community's quorum: its licence concludes nothing", [GN, A("e", "RD", "g"),
                                                                       glic("l", "g", cosigners=("B", "C"))],
     "RD", "l", None, (False, "licensure_authority_locked")),
    ("(b) an affiliation is never locked: its officers' quorum issues with no duty holder",
     [AFD, A("e", "RD", "af"), glic("l", cosigners=("B",))], "RD", "l", None, OK),
    ("(b) a license seat conferred before the lock: its holder keeps issuing within the seat's term",
     [G1, G1LT, GLA, G1LD, A("e", "RD", "g"), glic("l", "g", "X") | {"names": ("ld",), "asserted_at": 50}], "RD", "l",
     None, OK),
    ("(b) and not after the term ends", [G1, G1LT, GLA, G1LD, A("e", "RD", "g"),
                                        glic("l", "g", "X") | {"names": ("ld",), "asserted_at": 150}], "RD", "l",
     None, NA),
    ("(b) an affiliation's officers confer a license seat under its protocol (two of three officers)",
     [AFD, A("e", "RD", "af"), ALO, ALA, glic("l", "af", "X") | {"names": ("ala",)}], "RD", "l", None, OK),
    ("(b) and one officer alone does not", [AFD, A("e", "RD", "af"), ALO1, ALA,
                                           glic("l", "af", "X") | {"names": ("ala",)}], "RD", "l", None, NA),
    ("(b) a member who is no officer confers nothing with one officer",
     [AFD1, A("e", "RD", "af"), dict(ALO1, signer="B", cosigners=()), ALA, glic("l", "af", "X") | {"names": ("ala",)}],
     "RD", "l", None, NA),
    ("(b) a live key of the person's roster is the person", [E0, KRO, KRA, klic("l", signer="d", names=("kra",))],
     "RD", "l", KCH, OK),
    ("(b) a key not seated in the licence's past is not", [E0, KRO, KRA, klic("l", signer="d")], "RD", "l", KCH, NA),
    ("(b) a license seat its duty holders conferred: the holder's licence is the community's act",
     [GD, A("e", "RD", "g"), GLO, GLA, glic("l", "g", "X", cls=M) | {"names": ("gla",)}], "RD", "l", None, OK),
    ("(b) one of two duty holders confers no license seat",
     [GD, A("e", "RD", "g"), GLO1, GLA, glic("l", "g", "X", cls=M) | {"names": ("gla",)}], "RD", "l", None, NA),
    ("(b) a locked community confers no license seat",
     [GN, A("e", "RD", "g"), GLO, GLA, glic("l", "g", "X", cls=M) | {"names": ("gla",)}], "RD", "l", None, NA),
    ("(d) the duty holders withdraw the seat: a licence after it is testimony",
     [GD, A("e", "RD", "g"), GLO, GLA, GLU, glic("l", "g", "X", cls=M) | {"names": ("glu",)}], "RD", "l", None, NA),
    ("a class the charter does not declare", [E0, klic("l", "dental")], "RD", "l", KCH,
     (False, "licence_class_not_trusted")),
]

# ---- the r73 attack (review-scratch 3bc1e46, r73/a1 to a3), each a case ----------------------------------------
LW = (False, "licensure_link_withdrawn")
LK = (False, "licensure_authority_locked")
R_KU = ST.unseat("ku", "K", "d", "key", "K", "self", ("kra",))           # K evicts its key d
R_RU = ST.unseat("ru", "RD", "d", "key", "RD", "self", ("ra",))          # RD evicts its key d
R_LD = ST.withdraw("ld", "A", "g", (), scope="moderate")                  # G1's lone holder lays its duty down: locked
R_LDA = ST.withdraw("lda", "A", "g", (), scope="moderate")
R_LDB = ST.withdraw("ldb", "B", "g", (), scope="moderate")
R_AMD = ST.offer("amd", "A", (), "record", "af", "group", ("af",), head=("af",), cosigners=("B", "C"),
                 counted=ST.OFFICER, consensus_protocol="unanimous", declared_cohort="affiliations",
                 licence_classes=((M, True), (L, False)))              # af amends its protocol to unanimous
R_SO = lambda sc, obj, signer="B": ST.offer("so", signer, signer, sc, obj, "self", (obj,))
CASES += [
    ("r73 E1 K evicts d; d's licence naming the eviction", [E0, KRO, KRA, R_KU, klic("l", signer="d", names=("ku",))],
     "RD", "l", KCH, NA),
    ("r73 E2 K evicts d; d's licence naming only kra (concurrent with the eviction): cut",
     [E0, KRO, KRA, R_KU, klic("l", signer="d", names=("kra",))], "RD", "l", KCH, LW),
    ("r73 E3 RD evicts d; d writes RD's edge naming only ra: cut, no edge",
     [RO, RA, R_RU, A("e", "d", "Z", on_behalf="RD", names=("ra",)), CH.licensure("l", "Z", "Z", M)], "RD", "l",
     {"Z": (M,)}, NR),
    ("r73 E4 RD evicts d; d's withdrawal of RD's edge, concurrent with the eviction, ends nothing",
     [RO, RA, E0, R_RU, ST.withdraw("w", "d", "e", ("ra",)), klic("l")], "RD", "l", KCH, OK),
    ("r73 K0 locked: the quorum's licence naming the lay-down",
     [G1, R_LD, A("e", "RD", "g"), glic("l", "g", cosigners=("B",)) | {"names": ("ld",)}], "RD", "l", None, LK),
    ("r73 K2 locked: the quorum's licence naming only g (concurrent with the lay-down)",
     [G1, R_LD, A("e", "RD", "g"), glic("l", "g", cosigners=("B",))], "RD", "l", None, LK),
    ("r73 K3 an edge from before the lock stands (a locked group signs no NEW edge)",
     [G1, A("e", "RD", "g", depth=1), A("f", "A", "K", on_behalf="g", names=("g",)), dict(R_LD, names=("f",)),
      klic("l")], "RD", "l", KCH, OK),
    ("r73 K4 after the lock the ex-holder's edge naming only g: cut, no edge",
     [G1, R_LD, A("e", "RD", "g", depth=1), A("f", "A", "K", on_behalf="g", names=("g",)), klic("l")], "RD", "l", KCH,
     NR),
    ("r73 K5 and naming the lay-down: no edge", [G1, R_LD, A("e", "RD", "g", depth=1),
                                                A("f", "A", "K", on_behalf="g", names=("ld",)), klic("l")],
     "RD", "l", KCH, NR),
    ("r73 K6 B lays down, A the lone holder signs alone",
     [GD, R_LDB, A("e", "RD", "g", depth=1), A("f", "A", "K", on_behalf="g", names=("ldb",)), klic("l")], "RD", "l",
     KCH, OK),
    ("r73 S1 the holders withdraw X's seat; X's licence naming it",
     [GD, A("e", "RD", "g"), GLO, GLA, GLU, glic("l", "g", "X") | {"names": ("glu",)}], "RD", "l", None, NA),
    ("r73 S2 and X's licence naming only gla (concurrent with the unseat): cut",
     [GD, A("e", "RD", "g"), GLO, GLA, GLU, glic("l", "g", "X") | {"names": ("gla",)}], "RD", "l", None, LW),
    ("r73 S3 a term-bearing seat; a licence stating no instant meets no term",
     [G1, G1LT, GLA, G1LD, A("e", "RD", "g"), glic("l", "g", "X") | {"names": ("ld",)}], "RD", "l", None, NA),
    ("r73 S4 and one stating 50, within the term", [G1, G1LT, GLA, G1LD, A("e", "RD", "g"),
                                                    glic("l", "g", "X") | {"names": ("ld",), "asserted_at": 50}],
     "RD", "l", None, OK),
    ("r73 S5 an instant earlier than a row the licence cites (the seat's offer at 10)",
     [G1, G1LT, GLA, A("e", "RD", "g"), glic("l", "g", "X") | {"names": ("gla",), "asserted_at": 5}], "RD", "l", None,
     (False, "licensure_instant_before_its_past")),
    ("r73 P1 af amends to unanimous; two officers' licence naming the amendment",
     [AFD, R_AMD, A("e", "RD", "af"), glic("l", cosigners=("B",)) | {"names": ("amd",)}], "RD", "l", None, NA),
    ("r73 P2 and naming only af (concurrent with the amendment): judged under it, cut",
     [AFD, R_AMD, A("e", "RD", "af"), glic("l", cosigners=("B",))], "RD", "l", None, LW),
    ("r73 B1 A and B lay down; their concurrent conferral is cut; X's licence naming both lay-downs",
     [GD, R_LDA, R_LDB, A("e", "RD", "g"), GLO, GLA, glic("l", "g", "X") | {"names": ("gla", "lda", "ldb")}], "RD", "l",
     None, NA),
    ("r73 B1c and a conferral naming the lay-downs", [GD, R_LDA, R_LDB, A("e", "RD", "g"),
                                                      dict(GLO, names=("g", "lda", "ldb")), GLA,
                                                      glic("l", "g", "X") | {"names": ("gla",)}], "RD", "l", None, NA),
    ("r73 O1 dissolved AF: a founder's own officer seat revives nothing",
     [AF, R_SO(ST.OFFICER, "af"), A("e", "RD", "af"), glic("l", "af", "B") | {"names": ("so",)}], "RD", "l", None, NA),
    ("r73 O2 one-officer AFD1: a member's own officer seat",
     [AFD1, R_SO(ST.OFFICER, "af"), A("e", "RD", "af"), glic("l", "af", "B") | {"names": ("so",)}], "RD", "l", None,
     NA),
    ("r73 O3 AFD1: a member's own license seat", [AFD1, R_SO("license", "af"), A("e", "RD", "af"),
                                                  glic("l", "af", "B") | {"names": ("so",)}], "RD", "l", None, NA),
    ("r73 O4 locked GN: a founder's own license seat", [GN, R_SO("license", "g"), A("e", "RD", "g"),
                                                        glic("l", "g", "B") | {"names": ("so",)}], "RD", "l", None, NA),
    ("r73 O5 locked GN: a founder's own duty seat, then its lone conferral",
     [GN, R_SO("duty", "g"), A("e", "RD", "g"), dict(GLO1, signer="B", names=("so",)), GLA,
      glic("l", "g", "X") | {"names": ("gla",)}], "RD", "l", None, NA),
    ("an edge within its term at the licence's instant",
     [A("e", "RD", "K") | {"asserted_at": 10, "expires_at": 100}, klic("l") | {"asserted_at": 50}], "RD", "l", KCH, OK),
    ("an edge whose term has ended at the licence's instant",
     [A("e", "RD", "K") | {"asserted_at": 10, "expires_at": 100}, klic("l") | {"asserted_at": 150}], "RD", "l", KCH,
     NR),
    ("a term-bearing edge and a licence stating no instant",
     [A("e", "RD", "K") | {"asserted_at": 10, "expires_at": 100}, klic("l")], "RD", "l", KCH, NR),
]

# (name, the edge row, the refusal or None)
REFUSALS = [
    ("absent classes, absent depth", A("e", "RD", "K"), None),
    ("a sorted list", A("e", "RD", "K", (L, M)), None),
    ("an empty list", A("e", "RD", "K", ()), "trust_accepts_classes_malformed"),
    ("an unsorted list", A("e", "RD", "K", (M, L)), "trust_accepts_classes_malformed"),
    ("a class twice", A("e", "RD", "K", (M, M)), "trust_accepts_classes_malformed"),
    ("depth 0", A("e", "RD", "K", depth=0), None),
    ("depth 5", A("e", "RD", "K", depth=5), None),
    ("depth 6", A("e", "RD", "K", depth=6), "trust_accepts_depth_out_of_range"),
    ("a negative depth", A("e", "RD", "K", depth=-1), "trust_accepts_depth_out_of_range"),
]

REF_FIELDS = ("dst", "on_behalf", "authority")      # the objects an edge row and a licence name, for the fixture

PLANTS = ("edge_any_signer", "roster_unread", "duty_unread", "lock_unread", "quorum_fixed_majority",
          "roster_issuer_unread", "license_seat_unread", "term_unread",
          "affiliation_edge_duty_count", "dissolved_edges_kept", "lapsed_unread", "lapsed_class_unread",
          "pending_unread",
          "judged_at_read", "bears_unread", "refusal_unread", "depth_unread", "depth_absent_refused",
          "withdrawn_unread", "withdraw_by_anyone", "issuer_unread", "chain_unread", "quorum_unread",
          "ends_unread", "cut_unread", "self_seat_ungated", "untimed_term_met", "instant_unread",
          "edge_term_unread")


@contextlib.contextmanager
def planted(plant):
    saved = (set(TR.MUT), set(ST.MUT))
    if plant:
        TR.MUT.add(plant)
        ST.MUT.add(plant)
    try:
        yield
    finally:
        TR.MUT.clear(); TR.MUT |= saved[0]
        ST.MUT.clear(); ST.MUT |= saved[1]


def arrive(order):
    return CK.arrive(list(order), lambda r, P, past: ST.seat_rule(r, P, past))


def answers(case, every_order=False):
    _name, rows, reader, lid, supplied, _want = case
    out, kept = set(), True
    for o in (itertools.islice(itertools.permutations(rows), ORDER_CAP) if every_order else [rows]):
        S = arrive(o)
        kept &= bool(S.C.get(lid))
        out.add(TR.read_licence(S, reader, lid, supplied=supplied))
    return out, kept


def misses(plant=None, every_order=False):
    hit = []
    with planted(plant):
        for c in CASES:
            got, kept = answers(c, every_order)
            if got != {c[5]}:
                hit.append("%s: got %s, expected %s" % (c[0], sorted(got, key=str), c[5]))
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
        print("  plant %-24s %s" % (plant, "caught by %d cases, first: %s" % (len(hit), hit[0]) if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % plant)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases (each in up to %d arrival orders), %d refusal cases, %d of %d planted breaks caught"
          % ("ok" if not problems else "%d problems" % len(problems), len(CASES), ORDER_CAP, len(REFUSALS), caught,
             len(PLANTS)))
    return 1 if problems else 0


def fixture(with_refs):
    """The cases with the model's answers, for the crate (tests/trust_rows.rs, through tools/kernel_fixtures.py)."""
    out = {"cases": [], "refusals": []}
    for name, rows, reader, lid, supplied, _want in CASES:
        refs = {}
        S = arrive(rows)
        ok, why = TR.read_licence(S, reader, lid, supplied=supplied)
        out["cases"].append({"name": name, "rows": with_refs(rows, refs), "refs": refs, "reader": reader,
                             "licence": lid, "supplied": {k: sorted(v) for k, v in sorted((supplied or {}).items())},
                             "honoured": ok, "reason": why})
    for name, r, _want in REFUSALS:
        refs = {}
        out["refusals"].append({"name": name, "rows": with_refs([r], refs), "refs": refs, "refusal": TR.refusal(r)})
    return out


if __name__ == "__main__":
    sys.exit(main())
