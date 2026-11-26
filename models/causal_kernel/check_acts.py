#!/usr/bin/env python3
"""
check_acts.py: which act a counted row is (seat.act_of), and which policy rows an act may take (seat.policy_for), as
the Constitution's acts table (data/governance_policy_acts.tsv) writes them, and the seat rule's refusal that reads
them (seat.in_force).

The act is decided from the row's kind (offer, unseat), its scope and its object (the object's kind, read from its
founding row's scope: seat.KINDS, a community where it names none), never from the policy it states. Each case names
one row of a set and the act it is; each query case names (act, scope class, kind) and the policy rows and choice the
table gives. CONCLUDE: whether a row concludes with the acts table and without it; the protocol rows are counted under
the room's protocol in force, one of the closed set (data/consensus_protocols.tsv, PROTOCOL_WORDS), with the record's
numbers and over the protocol's body. TIPS: who stands (the wait at tips across a change of protocol; a node's seat
by scope and kind). PENDING: two rows of the independent read (A1, A3) that hold once the head rules and room-keys-fix
are merged; reported, not failed on.

Planted breaks, each of which must change a case's answer:
    lift_unread         an offer naming a removal of the same seat is read as an admission, not the lift
    election_unread     an offer of a duty under the ranked count is read as the duty holders' conferral
    recall_by_policy    an unseat of a duty is told recall from withdrawal by the policy it states, not by `counted`
    kind_unread         every founding row is a community (an accord's row an admission, and so on)
    key_kind_unread     a key object has no kind
    detect_unread       a detector seat's conferral is no act
    binding_off         the acts table is not read: a counted row is counted under any policy it states
    stated_policy_free  a row's stated policy is not held to its act's rows (a fixed act's, or the row's choice)
    protocol_unread     a protocol row (cosigned_act, community_remove) is counted as a row-declared threshold
    gate_reads_stated   the duty gate reads the stated policy, not the one in force (step 4)
    subkind_unread      a community record's cohort_subkind is not read: no infrastructure community
    amendment_unread    a change of the record's protocol is not read: the founding protocol stays in force (step 5)
    record_unread       a change of the record is no act (record_change unread): it concludes nothing (step 5)
    regime_unread       a stated regime other than the protocol in force is not refused (step 5)
    regime_stated       tips are read by their stated regime, not the protocol in force: tips across a change fold
    protocol_set_open   any word is a protocol: a record change may install a policy word (the review's A2)
    row_need            a declared count reads the counted row's `need`, not the record's number (A2)
    protocol_body_free  a count under the protocol is taken over whatever body the row names (A2, A4)
    disagreeing_first   of two concurrent changes naming different protocols, one is in force
    any_amendment       any change of the record in the past is in force, not the newest
    record_by_founding  a change of the record is counted under the founding protocol, not the one in its own past
    body_free           a recall or a withdrawal of a duty counts whatever body the row names (A4)
    kind_partial        a founding row of a scope KINDS does not name has no kind: the binding is off there (A5)
    election_any_duty   a ranked offer of any duty is the election's seating (A7)
    node_consent_asked  a node's seat over an infrastructure community waits for the node's acceptance (A6)
    consent_one_waives  a row's `consent = "one"` waives the seated key's acceptance (A6)

    python3 -I check_acts.py      exit 1 on any difference
"""
import contextlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import seat as ST  # noqa: E402

CK = ST.CK
OBJ = "g"

GM = ST.offer("g", "A", ("A", "B", "C"), "member", "@", "self", cosigners=("B", "C"))
FH = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("A",)}, cosigners=("B", "C"), duties=("verify",))
GA = ST.offer("g", "h1", ("h1", "h2", "h3"), "holder", "@", "self", cosigners=("h2", "h3"))       # an accord
GS = ST.offer("g", "d1", ("d1", "d2", "d3"), "self", "@", "self", cosigners=("d2", "d3"))         # a self roster
GC = ST.offer("g", "A", ("A", "B", "C"), "club", "@", "self", cosigners=("B", "C"))         # a room founded in `club`
GI = ST.offer("g", "f1", ("f1", "f2", "f3"), "member", "@", "self", cosigners=("f2", "f3"),
              cohort_subkind="infrastructure")                                                     # an infrastructure community


def grp(i, kind, k, scope, policy, heads=("g",), obj=OBJ, **kw):
    mk = ST.offer if kind == "offer" else ST.unseat
    signer = kw.pop("signer", "A")
    return mk(i, signer, k, scope, obj, "group", tuple(heads) + tuple(kw.pop("cites", ())), head=tuple(heads), policy=policy,
              **kw)


REM = grp("xr", "unseat", "X", "agent", "community_remove", window="moderation_overturn")
# (name, rows, the row asked, (act, scope class, kind) or None)
CASES = [
    ("an admission of a member", [GM, grp("r", "offer", "D", "member", "community_invite")], "r", ("admit", "member", "community")),
    ("an admission of an agent", [GM, grp("r", "offer", "X", "agent", "community_invite")], "r", ("admit", "agent", "community")),
    ("a removal of a member, whatever policy it states", [GM, grp("r", "unseat", "B", "member", "accord_halt")], "r",
     ("remove", "member", "community")),
    ("a removal of an agent (a lone removal by its shape)", [GM, REM], "xr", ("remove", "agent", "community")),
    ("the lift: an offer naming a removal of the same seat", [GM, REM, grp("r", "offer", "X", "agent", "moderation_overturn",
                                                                          cites=("xr",), content="xr")],
     "r", ("lift", "agent", "community")),
    ("an offer naming a removal of another key's seat is an admission", [GM, REM, grp("r", "offer", "Y", "agent", "community_invite",
                                                                                        cites=("xr",), content="xr")],
     "r", ("admit", "agent", "community")),
    ("the duty holders' conferral of moderate", [FH, grp("r", "offer", "B", "moderate", "duty_confer", counted="duty")], "r",
     ("duty_confer", "duty", "community")),
    ("a conferral of a duty the record declares", [FH, grp("r", "offer", "B", "verify", "duty_confer", counted="duty")], "r",
     ("duty_confer", "duty", "community")),
    ("a members' count conferring moderate (no election named) is a conferral by its shape, whatever it states",
     [GM, grp("r", "offer", "B", "moderate", "community_invite")], "r", ("duty_confer", "duty", "community")),
    ("the election's seating: an offer of a duty under the ranked count (the one act read from the stated policy, for "
     "this tag: the election is not answered safely by it)",
     [GM, grp("r", "offer", "B", "moderate", "moderator_election")], "r", ("election_seating", "moderate", "community")),
    ("an offer of moderate naming a row, under an admission's policy, is a conferral by its shape (no structural "
     "election in this tag)",
     [GM, grp("r", "offer", "B", "moderate", "community_invite", of="g")], "r", ("duty_confer", "duty", "community")),
    ("the holders' withdrawal: an unseat of a duty counted over the duty holders",
     [FH, grp("r", "unseat", "A", "moderate", "moderator_recall", counted="duty")], "r", ("duty_withdraw", "duty", "community")),
    ("the recall: an unseat of a duty counted over the members, whatever it states",
     [FH, grp("r", "unseat", "A", "moderate", "duty_withdraw")], "r", ("recall", "duty", "community")),
    ("the holders' conferral of a detector seat (CC 4.5.7)",
     [FH, grp("r", "offer", "N", "detect:list1", "duty_confer", counted="duty")], "r", ("seat_confer", "detect", "community")),
    ("the holders' withdrawal of a detector seat (CC 4.5.7: 'withdrawn by the count of (iv)')",
     [FH, grp("r", "unseat", "N", "detect:list1", "duty_withdraw", counted="duty")], "r", ("seat_withdraw", "detect", "community")),
    ("another scope that is no duty and no roster seat is no act",
     [FH, grp("r", "offer", "N", "verify2", "duty_confer", counted="duty")], "r", None),
    ("an accord's counted row is a standing act", [GA, grp("r", "offer", "h4", "holder", "accord_majority", counted="holder")], "r",
     ("standing_act", "any", "accord")),
    ("an accord's grant of another scope too", [GA, grp("r", "offer", "A2", "infra", "accord_majority", counted="holder")], "r",
     ("standing_act", "any", "accord")),
    ("a self roster's admission of a key", [GS, grp("r", "offer", "d4", "self", "self_roster_add", counted="self")], "r",
     ("admit", "key", "self")),
    ("a self roster's removal of a key", [GS, grp("r", "unseat", "d3", "key", "self_roster_evict", counted="self")], "r",
     ("remove", "key", "self")),
    ("a counted row over a key object is the self roster's", [grp("r", "offer", "K2", "key", "self_roster_add", heads=(), obj="KY")], "r",
     ("admit", "key", "self")),
    ("an infrastructure community's admission of a founder (the record's cohort_subkind)",
     [GI, grp("r", "offer", "f4", "founder", "cosigned_act", cosigners=("f2", "f4"))], "r", ("admit", "founder", "infrastructure")),
    ("its seating of a node", [GI, grp("r", "offer", "n1", "node", "cosigned_act", cosigners=("f2",))], "r",
     ("admit", "node", "infrastructure")),
    ("its removal of a node", [GI, grp("r", "unseat", "n1", "node", "cosigned_act", cosigners=("f2",))], "r",
     ("remove", "node", "infrastructure")),
    ("a member's seat over an infrastructure community is no act there (founders and nodes only)",
     [GI, grp("r", "offer", "m1", "member", "community_invite", cosigners=("f2", "m1"))], "r", None),
    ("a node's seat over a community is the community's admission of a roster seat, which the table does not bind",
     [GM, grp("r", "offer", "n1", "node", "community_invite", cosigners=("B",))], "r", ("admit", "node", "community")),
    ("a change of a community's record is record_change", [GM, grp("r", "offer", (), "record", "cosigned_act",
                                                                    consensus_protocol="quorum:1/4")], "r",
     ("record_change", "record", "community")),
    ("a row that is not counted is no act", [GM, ST.offer("r", "A", "D", "member", OBJ, "seat", ("g",), under="g")], "r", None),
    ("a counted row with no scope is no act (an answer, as the crate's, not an exception)",
     [GM, grp("r", "offer", "X", None, "accord_halt")], "r", None),
    ("a ranked offer of review is review's conferral: the election seats moderate alone (CC 4.5.13)",
     [FH, grp("r", "offer", "B", "review", "moderator_election", counted="member")], "r", ("duty_confer", "duty", "community")),
    ("an unseat of a duty counted over the agents is no act: a recall counts the members exactly",
     [FH, grp("r", "unseat", "A", "moderate", "moderator_recall", counted="agent")], "r", None),
    ("an unseat of a duty counted over one duty's holders is no act: a withdrawal counts the duty holders exactly",
     [FH, grp("r", "unseat", "A", "moderate", "duty_withdraw", counted="moderate")], "r", None),
    ("a founding row of a scope KINDS does not name founds a community: the binding reaches every room",
     [GC, grp("r", "offer", "X", "member", "community_invite", counted="club")], "r", ("admit", "member", "community")),
    ("an object that is a row and no founding row has no kind",
     [CK.row("q", "note", "A", ()), grp("r", "offer", "D", "member", "community_invite", heads=(), obj="q", cites=("q",))], "r", None),
]

# (act, scope class, kind) -> (policy rows, choice), or None
QUERIES = [
    (("admit", "member", "community"), (("cosigned_act", "community_invite"), "row")),
    (("remove", "agent", "community"), (("community_remove",), "fixed")),
    (("duty_confer", "duty", "community"), (("duty_confer",), "fixed")),
    (("duty_withdraw", "duty", "community"), (("duty_withdraw",), "fixed")),
    (("recall", "duty", "community"), (("moderator_recall",), "fixed")),
    (("lift", "act", "community"), (("moderation_overturn",), "fixed")),
    (("lift", "agent", "community"), (("moderation_overturn",), "fixed")),
    (("seat_confer", "detect", "community"), (("duty_confer",), "fixed")),
    (("seat_withdraw", "detect", "community"), (("duty_withdraw",), "fixed")),
    (("election_seating", "moderate", "community"), (("moderator_election",), "fixed")),
    (("standing_act", "any", "accord"), (("accord_majority",), "fixed")),
    (("admit", "key", "self"), (("self_roster_add",), "fixed")),
    (("remove", "member", "affiliation"), (("affiliation_member_action", "cosigned_act"), "row")),
    (("admit", "founder", "infrastructure"), (("cosigned_act",), "fixed")),
    (("remove", "node", "infrastructure"), (("cosigned_act",), "fixed")),
    (("admit", "node", "community"), None),
    (("record_change", "record", "community"), (("cosigned_act", "default_standing", "default_content", "default_irreversible"), "row")),
    (("admit", "member", "accord"), None),
    (("recall", "duty", "self"), None),
]

# The refusal (step 3): (name, rows, the row asked, concludes with the acts table, concludes with none)
GM4 = ST.offer("g", "A", ("A", "B", "C", "D"), "member", "@", "self", cosigners=("B", "C", "D"))      # majority (default)
GMJ = ST.offer("g", "A", ("A", "B", "C", "D"), "member", "@", "self", cosigners=("B", "C", "D"), consensus_protocol="majority")
FH4 = ST.found("g", "A", ("A", "B", "C", "D"), {"moderate": ("A",)}, cosigners=("B", "C", "D"))     # A holds moderate
GN = ST.offer("g", "A", ("A", "B", "C", "D"), "member", "@", "self", cosigners=("B", "C", "D"), consensus_protocol=None)
AM1 = grp("am", "offer", (), "record", "cosigned_act", cosigners=("B", "C"), consensus_protocol="quorum:1/4")   # to one of four
GQ = dict(GM4, consensus_protocol="quorum:3/4")                                                    # any three
GU = dict(GM4, consensus_protocol="unanimous")
GF = ST.offer("g", "A", ("A", "B", "C"), "founder", "@", "self", cosigners=("B", "C"), consensus_protocol="founder_only")
GW = dict(GM4, consensus_protocol="weighted:stake", need=5, weights={"A": 3, "B": 2, "C": 1, "D": 1})
GO = dict(GM4, consensus_protocol="open:self_admit")
AG = grp("ag", "offer", ("X", "Y", "Z"), "agent", "cosigned_act", cosigners=("B", "C", "X", "Y", "Z"))   # three agents
G6 = ST.found("g", "A", ("A", "B", "C", "D", "E", "F"), {"moderate": ("A", "B", "F"), "review": ("C", "D", "E")},
              cosigners=("B", "C", "D", "E", "F"))
RM_A = lambda heads: grp("x", "unseat", "D", "member", "community_remove", heads=heads)                # A alone
CONCLUDE = [
    ("an admission stating accord_halt (one voice) is no admission's policy: with the table it concludes nothing",
     [GM4, grp("r", "offer", "E", "member", "accord_halt", cosigners=("E",))], "r", False, True),
    ("a removal stating cosigned_act: the removal's policy is fixed (community_remove), so nothing with the table; "
     "without it the room's protocol counts it (three of four)",
     [GM4, grp("r", "unseat", "D", "member", "cosigned_act", cosigners=("B", "C"))], "r", False, True),
    ("a removal stating none is counted under community_remove, the room's protocol: majority, three of four",
     [GM4, grp("r", "unseat", "D", "member", None, cosigners=("B", "C"))], "r", True, False),
    ("a removal under community_remove in a room of majority: A and B, two of four, are not more than half",
     [GMJ, grp("r", "unseat", "D", "member", "community_remove", cosigners=("B",))], "r", False, False),
    ("and A, B and C are: the room's protocol, not one the row states",
     [GMJ, grp("r", "unseat", "D", "member", "community_remove", cosigners=("B", "C"))], "r", True, True),
    ("a removal in a room whose record declares no protocol concludes nothing, with the table or without",
     [GN, grp("r", "unseat", "D", "member", "community_remove", cosigners=("B", "C", "D"))], "r", False, False),
    ("an admission under cosigned_act is counted under the room's protocol (majority: three of four)",
     [GMJ, grp("r", "offer", "E", "member", "cosigned_act", cosigners=("B", "C", "E"))], "r", True, True),
    ("an admission under cosigned_act where the record declares no protocol concludes nothing",
     [GN, grp("r", "offer", "E", "member", "cosigned_act", cosigners=("B", "C", "D", "E"))], "r", False, False),
    ("an admission under community_invite (the two-path) is its own count: two thirds, three of four",
     [GMJ, grp("r", "offer", "E", "member", "community_invite", cosigners=("B", "C", "E"))], "r", True, True),
    ("a counted row of a scope that is no act over a community concludes nothing with the table",
     [FH, grp("r", "offer", "N", "verify2", "accord_halt")], "r", False, True),
    ("a detector seat's conferral stating accord_halt is refused (its policy is fixed: duty_confer)",
     [FH, grp("r", "offer", "N", "detect:list1", "accord_halt", counted="duty")], "r", False, True),
    ("a duty conferral stating no policy is counted under duty_confer, its act's fixed row (step 4: the duty gate "
     "reads the policy in force); with no table the gate wants duty_confer stated",
     [FH, grp("r", "offer", "B", "review", None, counted="duty", cosigners=("B",))], "r", True, False),
    ("a node's seat over an infrastructure community, under the founders' protocol (majority): two of three "
     "founders seat it, its own signature not asked",
     [GI, grp("r", "offer", "n1", "node", None, signer="f1", cosigners=("f2",))], "r", True, False),
    ("a node is no voice in the founders' count (its seat holds no member's): f1 and the node n1 do not admit a "
     "founder (one of three founders)",
     [GI, grp("na", "offer", "n1", "node", None, signer="f1", cosigners=("f2",)),
      grp("r", "offer", "f4", "founder", None, signer="f1", cosigners=("n1", "f4"), heads=("na",))], "r", False, False),
    ("a node's seat over a community concludes nothing (the table binds it over infrastructure only)",
     [GM4, grp("r", "offer", "n1", "node", "community_invite", cosigners=("B", "C"))], "r", False, True),
    # ---- the recall told by its act ------------------------------------------------------------------------------
    ("a members' unseat of a duty is the recall, counted over the members less the holder: B and C of A, B, C, D "
     "(two of three others) do not recall A",
     [FH4, grp("r", "unseat", "A", "moderate", "moderator_recall", signer="B", cosigners=("C",))], "r", False, False),
    ("and B, C and D do", [FH4, grp("r", "unseat", "A", "moderate", "moderator_recall", signer="B", cosigners=("C", "D"))],
     "r", True, True),
    ("a duty holders' unseat stating moderator_recall is no recall (its act is the withdrawal, fixed duty_withdraw): "
     "with the table it concludes nothing",
     [FH4, grp("r", "unseat", "A", "moderate", "moderator_recall", signer="B", counted="duty", cosigners=("C", "D"))],
     "r", False, False),
    ("a members' unseat of a duty stating another policy (community_remove) is refused: the recall's row is fixed",
     [FH4, grp("r", "unseat", "A", "moderate", "community_remove", signer="B", cosigners=("C", "D"))], "r", False, True),
    # ---- step 5: the protocol change ------------------------------------------------------------------------------
    ("a change of the record's protocol (record_change) is counted under the protocol in force in its own past: three "
     "of four, majority, change it to quorum:1/4", [GM4, AM1], "am", True, True),
    ("a removal naming the change is counted under the new protocol: A alone removes D", [GM4, AM1, RM_A(("am",))], "x",
     True, True),
    ("a removal beside the change (not in its past) is counted under the old one: A alone does not",
     [GM4, AM1, RM_A(("g",))], "x", False, False),
    ("a change signed by A alone is no change (one of four under majority), and the protocol stays",
     [GM4, grp("am", "offer", (), "record", "cosigned_act", signer="A", consensus_protocol="quorum:1/4"), RM_A(("am",))], "x",
     False, False),
    ("two concurrent changes naming different protocols: none is in force, and the removal concludes nothing",
     [GM4, AM1, grp("am2", "offer", (), "record", "cosigned_act", cosigners=("B", "C"), consensus_protocol="majority"),
      RM_A(("am", "am2"))], "x", False, False),
    ("a row stating a regime other than the protocol in force concludes nothing (a consistency check); with no table "
     "the stated regime is not read", [GM4, grp("r", "offer", "E", "member", "cosigned_act", cosigners=("B", "C", "E"),
                                             regime="unanimous")], "r", False, True),
    ("a row stating the protocol in force as its regime is counted as any", [GM4, grp("r", "offer", "E", "member", "cosigned_act",
                                                                                     cosigners=("B", "C", "E"), regime="majority")],
     "r", True, True),
    ("a change of the record is counted under the protocol in force in its own past, not the founding one: A alone "
     "changes it again under quorum:1/4 (one of four under the founding majority)",
     [GM4, AM1, grp("am2", "offer", (), "record", "cosigned_act", heads=("am",), signer="A", consensus_protocol="majority")],
     "am2", True, True),
    ("the newest change is in force, not any change: after quorum:1/4 and then majority, A alone does not remove D",
     [GM4, AM1, grp("am2", "offer", (), "record", "cosigned_act", heads=("am",), signer="A", consensus_protocol="majority"),
      RM_A(("am2",))], "x", False, False),
    ("the order of changes is read over the concluded past: a change naming only a row that did not conclude (which "
     "names the earlier change) is concurrent with that change, the two disagree, and the removal concludes nothing",
     [GM4, AM1, grp("n", "offer", "Q", "member", "community_invite", heads=("am",)),
      dict(grp("am2", "offer", (), "record", "default_content", heads=("am",), signer="B", cosigners=("C", "D"),
               consensus_protocol="majority"), names=("n",)),
      grp("x", "unseat", "D", "member", "community_remove", heads=("am2",), cosigners=("B", "C"))], "x", False, False),
    # ---- the protocol set (data/consensus_protocols.tsv): a word outside it is no protocol --------------------------
    ("a removal in a room declaring two_thirds (no protocol of the set) concludes nothing",
     [dict(GM4, consensus_protocol="two_thirds"), grp("r", "unseat", "D", "member", "community_remove", cosigners=("B", "C"))],
     "r", False, False),
    ("a room declaring quorum with no numbers declares no protocol",
     [dict(GM4, consensus_protocol="quorum"), grp("r", "unseat", "D", "member", None, cosigners=("B", "C"), need=1)],
     "r", False, False),
    ("quorum:5/4 (m above n) and quorum:03/4 (a leading zero) are no protocol",
     [dict(GM4, consensus_protocol="quorum:5/4"), grp("r", "unseat", "D", "member", None, cosigners=("B", "C", "D"))],
     "r", False, False),
    ("quorum:03/4 is no protocol", [dict(GM4, consensus_protocol="quorum:03/4"),
                                    grp("r", "unseat", "D", "member", None, cosigners=("B", "C", "D"))], "r", False, False),
    ("a change of the record naming a policy word (accord_halt) concludes nothing; with no table it is read as any change",
     [GM4, grp("am", "offer", (), "record", "cosigned_act", cosigners=("B", "C"), consensus_protocol="accord_halt")],
     "am", False, True),
    ("a quorum's number is the record's: under quorum:3/4 A alone stating need=1 does not admit E",
     [GQ, grp("r", "offer", "E", "member", "cosigned_act", cosigners=("E",), need=1)], "r", False, False),
    ("and A alone stating need=1 does not remove B", [GQ, grp("r", "unseat", "B", "member", None, need=1)], "r", False, False),
    ("and A, B and C do, whatever need the row states", [GQ, grp("r", "unseat", "D", "member", None, cosigners=("B", "C"), need=9)],
     "r", True, False),
    ("unanimous: every member signs an admission (A, B, C, D)",
     [GU, grp("r", "offer", "E", "member", "cosigned_act", cosigners=("B", "C", "D", "E"))], "r", True, True),
    ("and three of four do not admit", [GU, grp("r", "offer", "E", "member", "cosigned_act", cosigners=("B", "C", "E"))], "r",
     False, False),
    ("unanimous removal: every member but D, and a strict majority of the roster",
     [GU, grp("r", "unseat", "D", "member", None, cosigners=("B", "C"))], "r", True, False),
    ("and A and B do not remove D", [GU, grp("r", "unseat", "D", "member", None, cosigners=("B",))], "r", False, False),
    ("founder_only: one founder admits, counted over the founders",
     [GF, grp("r", "offer", "D", "member", "cosigned_act", counted="founder", cosigners=("D",))], "r", True, True),
    ("a count under the protocol is over the protocol's body: the same admission counted over the members concludes nothing",
     [GF, grp("r", "offer", "D", "member", "cosigned_act", cosigners=("D",))], "r", False, False),
    ("and over a narrower body (one duty's holders) concludes nothing: A, the one moderator, alone does not admit E",
     [FH4, grp("r", "offer", "E", "member", "cosigned_act", counted="moderate", cosigners=("E",))], "r", False, False),
    ("founder_only states no removal: a founders' removal concludes nothing",
     [GF, grp("r", "unseat", "C", "founder", None, counted="founder", cosigners=("B",))], "r", False, False),
    ("weighted: the record's weights and threshold (A 3, B 2: five of five) admit E",
     [GW, grp("r", "offer", "E", "member", "cosigned_act", cosigners=("B", "E"))], "r", True, True),
    ("and B, C and D (four) do not", [GW, grp("r", "offer", "E", "member", "cosigned_act", signer="B", cosigners=("C", "D", "E"))],
     "r", False, False),
    ("a row's own weights and threshold are not read: D stating weight 9 and need 1 does not admit E",
     [GW, grp("r", "offer", "E", "member", "cosigned_act", signer="D", cosigners=("E",), need=1, weights={"D": 9})], "r",
     False, False),
    ("open:self_admit: E's own signature admits E", [GO, grp("r", "offer", "E", "member", "cosigned_act", signer="E")], "r",
     True, True),
    ("and an admission E did not sign does not", [GO, grp("r", "offer", "E", "member", "cosigned_act", cosigners=("B", "C"))],
     "r", False, False),
    # ---- the body a recall and a withdrawal count ------------------------------------------------------------------
    ("three agents do not recall a person moderator: a recall counted over the agents concludes nothing",
     [FH4, AG, grp("r", "unseat", "A", "moderate", None, heads=("ag",), signer="X", cosigners=("Y", "Z"), counted="agent")],
     "r", False, False),
    ("two of the five other duty holders do not withdraw B's moderate by counting the moderators alone",
     [G6, grp("r", "unseat", "B", "moderate", None, signer="A", cosigners=("F",), counted="moderate")], "r", False, False),
    ("an accord's counted row stating none is a standing act, counted under accord_majority",
     [GA, grp("r", "offer", "h4", "holder", None, counted="holder", cosigners=("h1", "h2", "h4"))], "r", True, False),
]

# The wait at tips (step 5), and who stands: (name, rows, [(key, scope, stands)])
TIPS = [
    ("a node's seat over an infrastructure community stands on the founders' count alone, by scope and kind",
     [GI, grp("r", "offer", "n1", "node", None, signer="f1", cosigners=("f2",))], [("n1", "node", True)]),
    ("every other seat needs the seated key's own consent: a flag `consent` on a counted admission waives nothing",
     [GM4, grp("r", "offer", "E", "member", "cosigned_act", cosigners=("B", "C"), consent="one")], [("E", "member", False)]),
    ("nor on a founder's seat over an infrastructure community",
     [GI, grp("r", "offer", "f4", "founder", None, signer="f1", cosigners=("f2",), consent="one")], [("f4", "founder", False)]),
    ("tips on either side of a change of protocol do not fold: X admitted under the new protocol at one tip, Y under "
     "two-path at another, and neither stands until a row names both",
     [GM4, AM1, grp("ax", "offer", "X", "member", "cosigned_act", heads=("am",), cosigners=("X",)),
      grp("ay", "offer", "Y", "member", "community_invite", cosigners=("B", "C", "Y"))],
     [("X", "member", False), ("Y", "member", False), ("B", "member", True)]),
    ("and once a row names both, both stand",
     [GM4, AM1, grp("ax", "offer", "X", "member", "cosigned_act", heads=("am",), cosigners=("X",)),
      grp("ay", "offer", "Y", "member", "community_invite", cosigners=("B", "C", "Y")),
      grp("az", "offer", "Z", "member", "cosigned_act", heads=("ax", "ay"), cosigners=("Z",))],
     [("X", "member", True), ("Y", "member", True)]),
]

# The protocol set (data/consensus_protocols.tsv): (word, what seat.protocol_rule reads it as, or None)
PROTOCOL_WORDS = [
    ("founder_only", ("founder_only", None)), ("unanimous", ("unanimous", None)), ("majority", ("majority", None)),
    ("open:self_admit", ("open:self_admit", None)), ("quorum:2/3", ("quorum", 2)), ("quorum:3/3", ("quorum", 3)),
    ("quorum:999999999/999999999", ("quorum", 999999999)), ("weighted:stake", ("weighted", None)),
    ("quorum:4/3", None), ("quorum:0/3", None), ("quorum:03/4", None), ("quorum:1000000000/1000000000", None),
    ("quorum:2", None), ("quorum:2/3/4", None), ("quorum:+2/3", None), ("quorum: 2/3", None), ("quorum", None),
    ("weighted:", None), ("weighted", None), ("two_thirds", None), ("one", None), ("open", None), ("Majority", None),
    ("accord_halt", None), ("cosigned_act", None), ("", None), ("quorum:２/3", None),
]

# The review's A1 and A3 (rows of r56/tools/b2.py and b4.py): the head rules' job and room-keys-fix's (RK2). They hold
# once `heads` and `room-keys-fix` are merged; until then main() reports them and does not fail on them.
G3 = ST.offer("g", "A", ("A", "B", "C"), "member", "@", "self", cosigners=("B", "C"))
_adm = lambda i, k, signers, heads: grp(i, "offer", k, "member", "cosigned_act", heads=heads, signer=signers[0],
                                        cosigners=tuple(signers[1:]) + (k,))
_rem = lambda i, k, signers, heads: grp(i, "unseat", k, "member", None, heads=heads, signer=signers[0],
                                        cosigners=tuple(signers[1:]))
_LINE = [G3, _adm("ad", "D", ("A", "B", "C"), ("g",)), _adm("ae", "E", ("A", "B", "C"), ("ad",)),
         _rem("xa", "A", ("C", "D", "E"), ("ae",)), _rem("xb", "B", ("C", "D", "E"), ("xa",)),
         grp("am", "offer", (), "record", "cosigned_act", heads=("g",), signer="A", cosigners=("B",),
             consensus_protocol="quorum:1/3"),
         _adm("af", "F", ("A",), ("am",)),
         grp("mg", "offer", "G", "member", "cosigned_act", heads=("xb", "af"), signer="C", cosigners=("D", "E", "G")),
         _rem("xc", "C", ("F",), ("mg",))]
PENDING = [
    ("A1: two removed members' change of the record at an old head installs nothing: F is not seated by A alone, and "
     "F alone does not remove C", _LINE, [(k, "member", k in "CDEG") for k in "ABCDEFG"]),
    ("A3: one founder's own offer seats no key in a room of several founders",
     [GM4, ST.offer("o", "A", "X", "member", OBJ, "self", ("g",), cosigners=("X",))], [("X", "member", False)]),
]

PLANTS = ("lift_unread", "election_unread", "recall_by_policy", "kind_unread", "key_kind_unread", "detect_unread",
          "binding_off", "stated_policy_free", "protocol_unread", "gate_reads_stated",
          "subkind_unread", "amendment_unread", "record_unread", "regime_unread",
          "regime_stated", "protocol_set_open", "row_need", "protocol_body_free", "disagreeing_first", "any_amendment",
          "record_by_founding", "body_free", "kind_partial", "election_any_duty", "node_consent_asked",
          "consent_one_waives")


@contextlib.contextmanager
def planted(plant):
    saved = set(ST.MUT)
    if plant:
        ST.MUT.add(plant)
    try:
        yield
    finally:
        ST.MUT.clear(); ST.MUT |= saved


def answer(rows, rid, plant=None):
    by = {q["id"]: q for q in rows}
    r = by[rid]
    with planted(plant):
        return ST.act_of(r, by, is_key=r.get("obj") is not None and r.get("obj") not in by)


def concludes(rows, rid, bound, plant=None):
    with ST.binding(bound), planted(plant):
        S = CK.concluded(CK.kept(list(rows)), lambda r, P, past: ST.seat_rule(r, P, past))
        return bool(S.C.get(rid))


def tip_answers(plant=None, cases=None):
    out = []
    with planted(plant):
        for _, rows, asks in (TIPS if cases is None else cases):
            S = CK.concluded(CK.kept(list(rows)), lambda r, P, past: ST.seat_rule(r, P, past))
            Q = ST.Seats(S)
            out.append([Q.stands(k, sc, OBJ) for k, sc, _ in asks])
    return out


def main():
    problems = []
    for (name, _rows, asks), got in zip(TIPS, tip_answers()):
        if got != [w for _, _, w in asks]:
            problems.append("tips %s: got %s, expected %s" % (name, got, [w for _, _, w in asks]))
    for name, rows, rid, wb, wu in CONCLUDE:
        got = (concludes(rows, rid, True), concludes(rows, rid, False))
        if got != (wb, wu):
            problems.append("%s: got %s, expected %s" % (name, got, (wb, wu)))
    for name, rows, rid, want in CASES:
        got = answer(rows, rid)
        if got != want:
            problems.append("%s: got %s, expected %s" % (name, got, want))
    for q, want in QUERIES:
        got = ST.policy_for(*q)
        if got != want:
            problems.append("query %s: got %s, expected %s" % (q, got, want))
    # the protocol set is the Constitution's: the kinds seat.py parses are the table's kinds, in its order
    path = os.path.join(HERE, "..", "..", "data", "consensus_protocols.tsv")
    kinds = tuple(l.split("\t")[0] for l in open(path, encoding="utf-8") if l.strip() and not l.startswith(("#", "kind\t")))
    if kinds != ST.PROTOCOL_KINDS:
        problems.append("the protocol set: seat.py parses %s, the table lists %s" % (ST.PROTOCOL_KINDS, kinds))
    for w, want in PROTOCOL_WORDS:
        if ST.protocol_rule(w) != want:
            problems.append("protocol word %r: got %s, expected %s" % (w, ST.protocol_rule(w), want))
    for c, got in zip(PENDING, tip_answers(cases=PENDING)):
        want = [w for _, _, w in c[2]]
        print("  pending the heads and room-keys-fix merge: %s: %s" % (c[0], "holds" if got == want else
                                                                     "does not hold yet (got %s)" % got))
    caught = 0
    for plant in PLANTS:
        hit = [name for name, rows, rid, want in CASES if answer(rows, rid, plant) != want]
        hit += [c[0] for c in CONCLUDE if concludes(c[1], c[2], True, plant) != c[3]]
        hit += ["tips: " + c[0] for c, got in zip(TIPS, tip_answers(plant)) if got != [w for _, _, w in c[2]]]
        caught += bool(hit)
        print("  plant %-16s %s" % (plant, "caught by %d cases, first: %s" % (len(hit), hit[0]) if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % plant)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases, %d queries, %d refusal cases, %d of %d planted breaks caught"
          % ("ok" if not problems else "%d problems" % len(problems), len(CASES), len(QUERIES), len(CONCLUDE), caught,
             len(PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
