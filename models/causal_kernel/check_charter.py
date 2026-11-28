#!/usr/bin/env python3
"""
check_charter.py: charter coverage for licensing authorities (charter.py; CC 3.4.7, CC 4.4.3.12, 4.4.3.34).

DECLARED: the (class, legal_weight) pairs a community's record in force declares, over the rows a reader holds (at the
caller's instant, where a case gives one). LICENCES: whether a reader honours a licence, and why not; every licence
row of every case is kept and concluded (admitted as a row, whatever class it states). EDGES: the admission of an
acceptance edge's trust_classes. COUNTERSIGN: a removal from an affiliation (CC 4.4.3.12): a one-seat body's is a
proposal, in force only with a countersign by the designated official or an overseer outside the seat. Every
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
    one_seat_countersign  a one-seat affiliation's record change is never read, even countersigned
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
    countersign_unread    (seat.py) a one-seat affiliation's removal is a decision without a countersign
    countersign_inside_seat  (seat.py) the acting seat may countersign its own act
    official_at_founding  (seat.py) the official is read from the founding record, not the record in force
    overseers_unread      (seat.py) a review holder of the overseeing body may not countersign
    withdrawal_clears_unread  (seat.py) the acting seat's withdrawal does not clear its proposal
    two_voices_unread     (seat.py) a body of two or more seats removes on one voice
    officer_from_founders (seat.py) the deciding seats are the founding record's signers, not the officer role
    affiliation_body_members  (seat.py) an affiliation's acts are counted over its members, not its officers
    no_officer_locks      (seat.py) an affiliation with no officer is not dissolved
    overseer_end_unread   (seat.py) an overseer's lay-down does not cut its countersign
    countersign_against_member_only  (seat.py) only the four acts against a member need a one-officer body's countersign
    countersign_at_heads_unread  (seat.py) a countersign in the past of a row's heads is not read with them: an
                          appointment decided there seats no officer at the heads

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


def aff(i="af", to=("A", "B", "C"), cls=(MW, LW), cohort="affiliations", officers=None, **kw):
    """A community's founding record: its members, each seated by its own signature, and its charter. An
    affiliation's founding record lists its first officers (`officers`, every member by default) with the officer
    role (CC 4.4.3.12: its body for every counted act)."""
    if cohort is not None:
        kw["declared_cohort"] = cohort
    if cls is not None:
        kw["licence_classes"] = tuple(cls)
    roles = {ST.OFFICER: tuple(to if officers is None else officers)} if cohort == "affiliations" else None
    return ST.found(i, to[0], to, roles, cosigners=tuple(to[1:]), **kw)


def rec(i, cls, heads=("af",), signer="A", cosigners=("B",), obj="af", counted=ST.OFFICER, **kw):
    """A version of the record, counted at `heads` (cls None: it states no classes), by an affiliation's officers."""
    if cls is not None:
        kw["licence_classes"] = tuple(cls)
    return ST.offer(i, signer, (), "record", obj, "group", tuple(heads), head=tuple(heads), cosigners=tuple(cosigners),
                    counted=counted, **kw)


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
A1 = aff("a1", to=("A",), cls=(MW,))                       # a one-seat affiliation (no official, no overseer)
A1OF = aff("a1", to=("A",), cls=(MW,), official="O")        # the same, its designated official O
A1V = rec("a1v", (MW, LW), heads=("a1",), cosigners=(), obj="a1")
A1W = ST.withdraw("a1w", "A", "a1")                         # its one member lays down its seat: no seat is left
A1B = ST.offer("a1b", "A", ("B",), "member", "a1", "group", ("a1",), head=("a1",), cosigners=("B",), counted=ST.OFFICER)  # appoints B
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
    ("item 8, ruled: a one-officer affiliation's change of its charter is a proposal (every act but an admission needs "
     "the countersign); with no official and no overseen_by nothing decides it, and the founding classes stand (edge "
     "(a): such a body can admit and do nothing else)", [A1, A1V], "a1", None, None, {MW}),
    ("and with its designated official's countersign naming the change, decided: legal is added",
     [A1OF, A1V, ST.R("vc", "countersign", "O", ("a1v",), of="a1v")], "a1", None, None, {MW, LW}),
    ("an appointed member is no voice (the body is its officers, CC 4.4.3.12): A's change beside appointed B is still "
     "the one officer's proposal", [A1, A1B, A1VB], "a1", None, None, {MW}),
    ("and B's signature beside A's decides nothing", [A1, A1B, A1VAB], "a1", None, None, {MW}),
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
    ("a one-officer affiliation's change adding legal is a proposal with no countersigner (edge (a)): legal is not declared",
     [A1, A1V, lic("l1", L, "a1")], [CH.edge("RD", "a1")], "RD", "l1", None, None, (False, "licence_class_not_trusted")),
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

# ---- the countersign (CC 4.4.3.12; Affiliation.lean, its `admitted` and `validCountersign` as the reference) -------
# A1O: a one-seat affiliation (A) whose record names the designated official O and the overseeing body ob (the
# placeholder field, seat.OVERSEEN_BY); ob is a community of R1 and R2, R1 holding `review` over it. A appoints B.
OB = ST.found("ob", "R1", ("R1", "R2"), {"review": ("R1",)}, cosigners=("R2",))
A1O = aff("a1", to=("A",), cls=(MW,), official="O", **{ST.OVERSEEN_BY: "ob"})
A1OB = ST.offer("a1b", "A", ("B",), "member", "a1", "group", ("a1",), head=("a1",), cosigners=("B",), counted=ST.OFFICER)
RMB = lambda heads=("a1b",), signer="A", cos=(): ST.unseat("rm", signer, "B", "member", "a1", "group",
                                                         tuple(heads) + ("ob",), head=tuple(heads), cosigners=tuple(cos),
                                                         policy="affiliation_member_action", counted=ST.OFFICER)
CS = lambda k, names=("rm",), i="cs": ST.R(i, "countersign", k, tuple(names), of="rm")
WRM = ST.withdraw("wrm", "A", "rm", ("rm",))
ONE = [OB, A1O, A1OB]
# A, the one officer, appoints C an officer: an appointment carrying role officer, C cosigning (its own acceptance)
AOC = ST.offer("aoc", "A", ("C",), "member", "a1", "group", ("a1b",), head=("a1b",), cosigners=("C",), counted=ST.OFFICER,
               role=ST.OFFICER)
RM0 = ST.unseat("rm0", "A", "B", "member", "a1", "group", ("a1b",), head=("a1b",), policy="affiliation_member_action",
               counted=ST.OFFICER)
DIS1 = rec("dis1", None, heads=("a1b",), cosigners=(), obj="a1", dissolved_at=100)   # A alone dissolves a1
ACS = ST.R("acs", "countersign", "O", ("aoc",), of="aoc")             # the official's countersign of the appointment
RMBA = lambda cos=(): dict(RMB(("aoc",), cos=cos), names=RMB(("aoc",), cos=cos)["names"] + ("acs",))
VO2 = dict(rec("v", (MW,), heads=("a1",), cosigners=(), obj="a1", official="O2", **{ST.OVERSEEN_BY: "ob"}),
           names=("a1", "ob"))
A1OBV = dict(A1OB, names=("v",), head=("v",))
VCO = ST.R("vc", "countersign", "O", ("v",), of="v")                       # the replaced official's countersign
VCR = ST.R("vcr", "countersign", "R1", ("v", "ob"), of="v")               # the overseer's
A1OBV2 = dict(A1OB, names=("v", "vc"), head=("v",))
A1OBV3 = dict(A1OB, names=("v", "vcr"), head=("v",))
RMBV = lambda c="vc": dict(RMB(), names=RMB()["names"] + (c,))
REM = ST.unseat("rm", "A", "C", "member", "af", "group", ("af",), head=("af",), cosigners=("B",), policy="cosigned_act",
               counted=ST.OFFICER)
# (name, rows, {row: concludes}, [(key, the affiliation, stands as a member)])
COUNTERSIGN = [
    ("a one-seat affiliation's removal of a member, alone: it concludes as a proposal and B stays a member",
     ONE + [RMB()], {"rm": True}, [("B", "a1", True)]),
    ("countersigned by the designated official, outside the seat: a decision, B is out",
     ONE + [RMB(), CS("O")], {"rm": True, "cs": True}, [("B", "a1", False), ("A", "a1", True)]),
    ("countersigned by the acting seat itself: no countersign (the seat cannot be its own second voice)",
     ONE + [RMB(), CS("A")], {"cs": False}, [("B", "a1", True)]),
    ("countersigned by a review holder of the overseeing body (naming the body's record, its seat's basis): a "
     "decision", ONE + [RMB(), CS("R1", ("rm", "ob"))], {"cs": True},
     [("B", "a1", False)]),
    ("countersigned by a member of the overseeing body holding no review seat: none", ONE + [RMB(), CS("R2", ("rm", "ob"))],
     {"cs": False}, [("B", "a1", True)]),
    ("countersigned by a key that is neither: none", ONE + [RMB(), CS("X")], {"cs": False}, [("B", "a1", True)]),
    ("the acting seat withdraws the proposal, and a countersign naming the withdrawal concludes nothing",
     ONE + [RMB(), WRM, CS("O", ("wrm",))], {"wrm": True, "cs": False}, [("B", "a1", True)]),
    ("the withdrawal concurrent with the countersign clears the proposal: B stays",
     ONE + [RMB(), WRM, CS("O")], {"wrm": True, "cs": True}, [("B", "a1", True)]),
    ("item 8: a record change naming a new official O2, not countersigned, is a proposal: O is still the official, and "
     "O's countersign of the removal decides it", [OB, A1O, VO2, A1OBV, RMB(), CS("O")],
     {"v": True, "rm": True, "cs": True}, [("B", "a1", False)]),
    ("the change countersigned by O, the official it replaces: O2 is the official, and O's countersign of the removal "
     "is none", [OB, A1O, VO2, VCO, A1OBV2, RMBV(), CS("O")], {"vc": True, "rm": True, "cs": False},
     [("B", "a1", True)]),
    ("and O2's decides", [OB, A1O, VO2, VCO, A1OBV2, RMBV(), CS("O2")], {"cs": True}, [("B", "a1", False)]),
    ("edge (b): O refuses to sign its own replacement; only the overseer replaces it: R1 countersigns the change, and "
     "O2's countersign then decides", [OB, A1O, VO2, VCR, A1OBV3, RMBV("vcr"), CS("O2")], {"vcr": True, "cs": True},
     [("B", "a1", False)]),
    ("an official who is the seat (the record names A) is no outside key", [OB, aff("a1", to=("A",), cls=(MW,),
                                                                             official="A"), A1OB, RMB(), CS("A")],
     {"cs": False}, [("B", "a1", True)]),
    ("a body of three deciding seats decides under its own protocol: A and B remove C, two voices, no countersign",
     [AF, REM], {"rm": True}, [("C", "af", False)]),
    ("and one voice of such a body removes nobody", [AF, dict(REM, cosigners=())], {"rm": False}, [("C", "af", True)]),
    # the paths (the Constitution's ruling): affiliation_member_action is one officer and one eligible outside key;
    # two officers do not meet it. cosigned_act is the path of two officers or more
    ("two officers removing a member under affiliation_member_action do not meet it (its voices are one officer and "
     "one outside key)", [AF, dict(REM, policy="affiliation_member_action")], {"rm": False}, [("C", "af", True)]),
    ("one officer's removal under cosigned_act does not meet it (the protocol path is of two officers or more)",
     ONE + [dict(RMB(), policy="cosigned_act")], {"rm": False}, [("B", "a1", True)]),
    ("and countersigned by the official it is still none: the countersign decides only the one-officer path",
     ONE + [dict(RMB(), policy="cosigned_act"), CS("O")], {"rm": False}, [("B", "a1", True)]),
    # the same paths for every act the row chooses between them (record_change, dissolve, a license seat, an edge)
    ("two officers' change of the record under affiliation_member_action does not meet it",
     [AF, rec("vp", (MW,), policy="affiliation_member_action")], {"vp": False}, []),
    ("and under cosigned_act it does (two of three, the protocol)", [AF, rec("vp", (MW,), policy="cosigned_act")],
     {"vp": True}, []),
    ("two officers' dissolution under affiliation_member_action does not meet it",
     [AF, rec("dp", None, policy="affiliation_member_action", dissolved_at=100)], {"dp": False}, []),
    ("one officer's change of the record under cosigned_act does not meet it",
     [OB, A1O, A1OB, rec("vq", (MW,), heads=("a1b",), cosigners=(), obj="a1", policy="cosigned_act")], {"vq": False}, []),
    ("one officer's dissolution under cosigned_act does not meet it",
     [OB, A1O, A1OB, dict(DIS1, policy="cosigned_act")], {"dis1": False}, []),
    ("a key that is no deciding seat signs no removal: B, appointed, with A", ONE + [RMB(cos=("B",))], {"rm": False},
     [("B", "a1", True)]),
    ("r75: an overseer seated AFTER the removal is no overseer of it: R1 confers review over ob on R2, R2 countersigns",
     ONE + [RMB(), ST.offer("rv", "R1", "R2", "review", "ob", "group", ("ob",), head=("ob",), policy="duty_confer",
                            counted="duty", cosigners=("R2",)), CS("R2", ("rm", "rv"))], {"cs": False},
     [("B", "a1", True)]),
    ("r75: an ex-overseer countersigns nothing: R1 lays its review down after the removal, then countersigns",
     ONE + [RMB(), ST.withdraw("ld", "R1", "ob", ("ob",), scope="review"), CS("R1", ("rm", "ld"))], {"cs": False},
     [("B", "a1", True)]),
    ("r75: and R1's lay-down concurrent with its countersign cuts it (the end rule): nothing decided",
     ONE + [RMB(), CS("R1", ("rm", "ob")), ST.withdraw("ld", "R1", "ob", ("ob",), scope="review")], {"cs": True},
     [("B", "a1", True)]),
    ("the acting seat's withdrawal after the decision (the countersign in its past) is a new act and undoes nothing: "
     "B stays out", ONE + [RMB(), CS("O"), ST.withdraw("wrm", "A", "rm", ("cs",))], {"cs": True, "wrm": True},
     [("B", "a1", False)]),
    # ---- the officers (the ruling on officers: `role: officer`, the body of every counted act) ------------------------
    ("item 8: A, the one officer, appoints C as an officer, and O countersigns the appointment: two officers, so A alone "
     "no longer removes B (two voices needed), countersign or not",
     ONE + [AOC, ACS, RMBA(), CS("O")], {"aoc": True, "rm": False}, [("C", "a1", True), ("B", "a1", True)]),
    ("and A and C, the two officers, remove B: a decision, no countersign asked",
     ONE + [AOC, ACS, RMBA(("C",))], {"rm": True}, [("B", "a1", False)]),
    ("edge (a): a one-officer affiliation with no official and no overseen_by admits B (an admission is the one act "
     "needing no countersign), and its removal of B is a proposal nothing can decide",
     [A1, A1B, RM0], {"a1b": True, "rm0": True}, [("B", "a1", True)]),
    ("item 8: the one officer's dissolution is a proposal: with no countersign every seat stands",
     ONE + [DIS1], {"dis1": True}, [("A", "a1", True), ("B", "a1", True)]),
    ("and with the official's countersign naming it, the affiliation is dissolved: every seat over it ends",
     ONE + [DIS1, ST.R("dc", "countersign", "O", ("dis1",), of="dis1")], {"dc": True},
     [("A", "a1", False), ("B", "a1", False)]),
    ("item 8, ruled (r75 c1): the appointment of a sock officer by the one officer is itself a proposal: without the "
     "countersign C is no officer, so A and C remove nobody", ONE + [AOC, RMB(("aoc",), cos=("C",))],
     {"aoc": True, "rm": False}, [("C", "a1", False), ("B", "a1", True)]),
    ("an appointment with the officer role and no acceptance seats nobody, and A stays the one officer: a proposal",
     ONE + [dict(AOC, cosigners=()), RMB(("aoc",))], {"rm": True}, [("C", "a1", False), ("B", "a1", True)]),
    ("the one officer lays its role down by its own row: no officer is left, and the affiliation is dissolved (not "
     "locked, no election): every seat over it ends",
     ONE + [ST.withdraw("lo", "A", "a1", ("a1b",), scope=ST.OFFICER)], {"lo": True}, [("A", "a1", False), ("B", "a1", False)]),
    ("an affiliation founded with no officer listed is dissolved at founding", [aff("a0", to=("A", "B"), cls=(MW,), officers=())],
     {}, [("A", "a0", False)]),
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


def countersign_answers(case, every_order=False):
    _name, rows, concl, asks = case
    out = set()
    for order in (orders(rows) if every_order else [rows]):
        S = arrive(list(order))
        Q = ST.Seats(S)
        out.add((tuple(bool(S.C.get(i)) for i in sorted(concl)), tuple(Q.stands(k, "member", o) for k, o, _ in asks)))
    return out


PLANTS = ("charter_unread", "at_issuance", "below_protocol_read", "fork_union", "fork_first", "join_unread",
          "unstated_keeps", "community_unread", "family_read", "weight_unread", "one_seat_countersign", "at_founding",
          "dissolved_declares", "dissolves_at_unread", "empty_edge_admits_all", "absent_means_none",
          "edge_classes_unread", "last_hop_only", "affiliation_unread", "affiliation_admit_unread",
          "countersign_unread", "countersign_inside_seat", "official_at_founding", "overseers_unread",
          "withdrawal_clears_unread", "two_voices_unread", "affiliation_path_unread", "officer_from_founders", "affiliation_body_members",
          "no_officer_locks", "overseer_end_unread", "countersign_against_member_only",
          "countersign_at_heads_unread")


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
        for c in COUNTERSIGN:
            want = (tuple(c[2][i] for i in sorted(c[2])), tuple(w for _, _, w in c[3]))
            got = countersign_answers(c, every_order)
            if got != {want}:
                hit.append("countersign %s: got %s, expected %s" % (c[0], sorted(got), want))
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
    print("RESULT: %s: %d declared cases, %d licence cases (each in up to %d arrival orders), %d edge cases, %d countersign "
          "cases, %d of %d planted breaks caught" % ("ok" if not problems else "%d problems" % len(problems),
                                                    len(DECLARED), len(LICENCES), ORDER_CAP, len(EDGES), len(COUNTERSIGN),
                                                    caught, len(PLANTS)))
    return 1 if problems else 0


def fixture(with_refs):
    """The cases with the model's answers, for the crate (tests/charter.rs, through tools/kernel_fixtures.py): rows as
    the models build them, each object a reference (`refs` names them); an edge's ends and an authority are names, a
    row where a row of the case has that id and a key otherwise. `with_refs`: kernel_fixtures.py's. An edge's classes
    are null where trust_classes is absent."""
    out = {"declared": [], "licences": [], "edges": []}
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
    return out


if __name__ == "__main__":
    sys.exit(main())
