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
by scope and kind). PENDING: none left. A1, A3, K2, T5b and C1 held at the batch merge, and the settling count, FA6, T5 and C2 as ruled
after it: all are TIPS cases now; Q4 is a conclusion case (CONCLUDE_Q4).

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
    infra_any_quorum    an infrastructure community's quorum need not be its founders' strict majority (P1)
    infra_body_members  an infrastructure community's protocol counts its members, not its founders (P1)
    infra_m_recomputed  an infrastructure community's M is recomputed from the founders at the heads (the P1 redo's)
    (retired: infra_founder_by_widening, a plain founder widening over infrastructure concluding: the acts table at rc23
    8c75ae7 has no admit / founder / infrastructure row, so the binding refuses it before the protocol is read)
    infra_m_lowered     an infrastructure amendment may lower M
    infra_word_n_free   an infrastructure word's N need not be the founders the version leaves
    infra_unentrenched  an infrastructure record need not be entrenched
    infra_stalled_admits a stalled infrastructure room's founders' count admits and removes
    (retired: recovery_concludes, a recovery widening counted as a widening: no founder widening concludes at all now,
    so the plant breaks nothing a case can see)
    record_change_either_policy   a record change meets one of its joined policies, not both (Q1)
    one_voice_community_protocol  a community may declare a protocol under which one voice decides (Q1)
    founder_only_community        a community may declare founder_only (Q3)
    unstated_cosigned_blocks      the cosigned_act half of an `&` is a condition where the protocol states no rule
    unstated_floor_unread         the policy governing alone there takes no floor of two voices
    founders_all_signers          an infrastructure founding row's founders are all its signers, not those it seats (H5)
    family_founders_fixed         a family's founders are its founding roles alone, not the role standing at the heads (F1)
    family_floor_two              a family takes the community's closed set (no one-voice protocol)
    family_last_founder_refused   a family's last founder may not leave
    entrenched_amendable          an entrenched record's protocol may be changed (F5)
    entrenched_whole_record       an entrenched record refuses every amendment, not its protocol alone (F5)
    dissolve_leaves_seats         a dissolution ends no seat
    dissolve_unread               a row over a dissolved group concludes
    (retired at the heads merge: dissolve_any_heads, a dissolution at any heads: H1 asks every counted row, a
    dissolution included, to name the newest counted changes in its own past, so the plant breaks nothing a case sees;
    founder_role_survives_leave: the head rules read a key whose own leaving is in a row's past out of every scope at
    its heads, the founder role included)
    (retired: self_removal_as_leave, F3's self-only removal concluding: the member a removal names is no voice of it
    now (removal_counts_target), so the F3 refusal is that rule's consequence and the plant breaks nothing a case sees)
    role_unread                   an admission's `role: founder` is not read: the one-row founder admission seats no founder
    (role_outlives_stay, retired at the room-keys merge: a founder role conferred after founding outliving the member's
    stay; room-keys' F3 compares seats by what they hold, and `founder` holds `member`, so the member's end of its stay
    ends the role by that rule too, and no case can tell the plant from the tree)
    contested_both_out            counted removals that remove each other's voices concurrently are both in force
    role_on_own_offer             `role: founder` is read on an own or uncounted offer, or outside a family
    entrenched_weights_free       an entrenched weighted record's weights and threshold may be restated (E1)
    concurrent_amendments_free    concurrent founders' amendments do not freeze the founders' count (L1)
    infra_word_restated_always    an infrastructure amendment seating a founder must restate the word, even at or below N
    contested_scoped_to_kinds     the contested pair is read for a family and an infrastructure community only
    contested_voice_everywhere    a removal voids a voice whatever head the other row names (not from its own head on)
    negative_weight               a weighted record may weigh a key below zero
    removal_counts_target         a removal under the room's protocol counts the member it removes, over and as a voice
    removal_floor_unread          a community's counted removal takes no floor of two voices besides the member removed
    end_of_contested_end          rule (2) reads a removal rule 5 holds contested out as an earlier end (the settling count)
    dissolve_uncontested          a dissolution is read apart from rule 5: it is no cut over every seat (FA6)
    wait_reader_unread            the founders' amendment wait is read over a row's own past only, not the reader's (C2)
    contested_one_sided           a one-sided cut is contested too: rule 5 read beyond mutual dependence
    weights_twice_at_change       a change to a weighted record weighing one key twice concludes (W1)
    infra_record_frozen an infrastructure community's record does not change: its record_change is no act (P1)
    infra_record_simple_majority  its record change is counted as a community's, over the members (P1)
    record_change_as_admission    under open:self_admit an offer of another seat (an agent's, the record) is counted as an
                                  admission (N1)
    self_admit_removal_counted    a removal under open:self_admit takes two voices (the set states none) (N1)
    body_from_row       the body an act counts is the one the row states (`counted`, `over`), not the act's (N2)

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
GAF = ST.found("g", "A", ("A", "B", "C"), cosigners=("B", "C"), group_kind="affiliation",
               licence_classes=("medical", "legal"))                                               # an affiliation
GI = ST.offer("g", "f1", ("f1", "f2", "f3"), "founder", "@", "self", cosigners=("f2", "f3"),
              cohort_subkind="infrastructure", consensus_protocol="quorum:2/3",
              consensus_protocol_entrenched=True)                                                   # an infrastructure community


def grp(i, kind, k, scope, policy, heads=("g",), obj=OBJ, **kw):
    mk = ST.offer if kind == "offer" else ST.unseat
    signer = kw.pop("signer", "A")
    return mk(i, signer, k, scope, obj, "group", tuple(heads) + tuple(kw.pop("cites", ())), head=tuple(heads), policy=policy,
              **kw)


# a family (CC 3.3.4, 3.1.3.2, 4.5.12.5): founders by the founding record's roles (its `founder` entry), keyless
FAM = ST.found("g", "A", ("A", "B", "C"), {"founder": ("A",)}, cosigners=("B", "C"), group_kind="family",
               family_key_id="FK", consensus_protocol="founder_only")
FAM2 = ST.found("g", "A", ("A", "B", "C"), {"founder": ("A", "B")}, cosigners=("B", "C"), group_kind="family",
                family_key_id="FK", consensus_protocol="founder_only")
FAMJ = ST.found("g", "A", ("A", "B", "C"), {"founder": ("A",)}, cosigners=("B", "C"), group_kind="family",
                family_key_id="FK", consensus_protocol="majority")
FAMQ = dict(FAMJ, consensus_protocol="quorum:1/3")
FAME = dict(FAM, consensus_protocol_entrenched=True)
FADM = lambda i, k, signer="A", heads=("g",), counted="founder", scope="member", acc=True, cites=(): grp(
    i, "offer", k, scope, None, heads=heads, signer=signer, cosigners=(k,) if acc else (), counted=counted, cites=cites)
FREM = lambda i, k, signer="A", heads=("g",), counted="founder", scope="member", cosigners=(): grp(
    i, "unseat", k, scope, None, heads=heads, signer=signer, cosigners=cosigners, counted=counted)
FREC = lambda i, w=None, signer="A", heads=("g",), **kw: grp(i, "offer", (), "record", None, heads=heads, signer=signer,
                                                            counted="founder", consensus_protocol=w, **kw)
FDIS = lambda i="d", signer="A", heads=("g",): grp(i, "offer", (), "record", None, heads=heads, signer=signer,
                                                  counted="founder", dissolved_at=100)
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
    ("a family's founding record (group kind `family`) founds a family: an admission there is the family's",
     [FAM, FADM("r", "D")], "r", ("admit", "member", "family")),
    ("a promotion to the founder role is counted as an admission (F1)", [FAM, FADM("r", "B", scope="founder")], "r",
     ("admit", "member", "family")),
    ("a dissolution of the family is the act dissolve", [FAM, FDIS()], "d", ("dissolve", "record", "family")),
    ("and of a community", [GM, grp("d", "offer", (), "record", None, dissolved_at=100)], "d", ("dissolve", "record", "community")),
    ("a moderator's seat over a family is no act (F4: a family has no duty seats)",
     [FAM, grp("r", "offer", "B", "moderate", "duty_confer", counted="duty")], "r", None),
    ("a change of an infrastructure community's record is record_change (P1)",
     [GI, grp("r", "offer", (), "record", "cosigned_act", signer="f1", cosigners=("f2",), consensus_protocol="quorum:3/4")],
     "r", ("record_change", "record", "infrastructure")),
    ("a member's seat over an infrastructure community is no act there (founders and nodes only)",
     [GI, grp("r", "offer", "m1", "member", "community_invite", cosigners=("f2", "m1"))], "r", None),
    ("a node's seat over a community is the community's admission of a roster seat, which the table does not bind",
     [GM, grp("r", "offer", "n1", "node", "community_invite", cosigners=("B",))], "r", ("admit", "node", "community")),
    ("a change of a community's record is record_change", [GM, grp("r", "offer", (), "record", "cosigned_act",
                                                                    consensus_protocol="quorum:2/4")], "r",
     ("record_change", "record", "community")),
    ("a change of an affiliation's record (its charter) is record_change (CC 3.4.7; the acts table's row is pending)",
     [GAF, grp("r", "offer", (), "record", None, cosigners=("B",), licence_classes=("medical",))], "r",
     ("record_change", "record", "affiliation")),
    ("a member's seat over an affiliation is no act read here", [GAF, grp("r", "offer", "D", "member", None,
                                                                         cosigners=("B", "D"))], "r", None),
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
    (("record_change", "record", "affiliation"), (("cosigned_act",), "fixed")),   # seat.PENDING_ACTS
    (("admit", "founder", "infrastructure"), None),        # rc23 8c75ae7: a founder seat comes only by a record change
    (("remove", "node", "infrastructure"), (("cosigned_act",), "fixed")),
    (("record_change", "record", "infrastructure"), (("cosigned_act",), "fixed")),
    (("admit", "node", "community"), None),
    (("record_change", "record", "community"), (("cosigned_act&default_standing",), "fixed")),
    (("change", "content", "community"), (("default_content",), "fixed")),
    (("admit", "member", "family"), (("cosigned_act",), "fixed")),
    (("admit", "member", "accord"), None),
    (("recall", "duty", "self"), None),
]

# The refusal (step 3): (name, rows, the row asked, concludes with the acts table, concludes with none)
GM4 = ST.offer("g", "A", ("A", "B", "C", "D"), "member", "@", "self", cosigners=("B", "C", "D"))      # majority (default)
GMJ = ST.offer("g", "A", ("A", "B", "C", "D"), "member", "@", "self", cosigners=("B", "C", "D"), consensus_protocol="majority")
FH4 = ST.found("g", "A", ("A", "B", "C", "D"), {"moderate": ("A",)}, cosigners=("B", "C", "D"))     # A holds moderate
GN = ST.offer("g", "A", ("A", "B", "C", "D"), "member", "@", "self", cosigners=("B", "C", "D"), consensus_protocol=None)
AM1 = grp("am", "offer", (), "record", None, cosigners=("B", "C"), consensus_protocol="quorum:2/4")   # to any two of four
GM5 = ST.offer("g", "A", ("A", "B", "C", "D", "E"), "member", "@", "self", cosigners=("B", "C", "D", "E"))   # majority
GM6 = ST.offer("g", "A", tuple("ABCDEF"), "member", "@", "self", cosigners=tuple("BCDEF"))
GM7 = ST.offer("g", "A", tuple("ABCDEFG"), "member", "@", "self", cosigners=tuple("BCDEFG"))
REC = lambda i, w, heads=("g",), signer="A", cosigners=("B", "C"), to=(), **kw: grp(i, "offer", to, "record", None, heads=heads,
                                                                           signer=signer, cosigners=cosigners,
                                                                           consensus_protocol=w, **kw)
GQ = dict(GM4, consensus_protocol="quorum:3/4")                                                    # any three
GU = dict(GM4, consensus_protocol="unanimous")
GF = ST.offer("g", "A", ("A", "B", "C"), "founder", "@", "self", cosigners=("B", "C"), consensus_protocol="founder_only")
GW = dict(GM4, consensus_protocol="weighted:stake", need=5, weights=(("A", 3), ("B", 2), ("C", 1), ("D", 1)))
GO = dict(GM4, consensus_protocol="open:self_admit")
GWE = dict(GW, consensus_protocol_entrenched=True)
W_NEW = (("A", 3), ("B", 1), ("C", 1), ("D", 1))
GO3 = ST.offer("g", "A", ("A", "B", "C"), "member", "@", "self", cosigners=("B", "C"), consensus_protocol="open:self_admit")
GO2 = ST.offer("g", "A", ("A", "B"), "member", "@", "self", cosigners=("B",), consensus_protocol="open:self_admit")
GO1 = ST.offer("g", "A", ("A",), "member", "@", "self", consensus_protocol="open:self_admit")
AG = grp("ag", "offer", ("X", "Y", "Z"), "agent", "cosigned_act", cosigners=("B", "C", "X", "Y", "Z"))   # three agents
G6 = ST.found("g", "A", ("A", "B", "C", "D", "E", "F"), {"moderate": ("A", "B", "F"), "review": ("C", "D", "E")},
              cosigners=("B", "C", "D", "E", "F"))
IN1 = grp("na", "offer", "n1", "node", None, signer="f1", cosigners=("f2",), counted="founder")       # node n1 seated
IAM = lambda w, heads=("g",), cosigners=("f2",), signer="f1", i="am", seat=(), **kw: grp(
    i, "offer", seat, "record", None, heads=heads, signer=signer, cosigners=tuple(cosigners) + tuple(seat),
    counted="founder", consensus_protocol=w, consensus_protocol_entrenched=True,
    **(dict(kw, role="founder") if seat else kw))                     # a founders' amendment: seats `seat`, signed by it
IAD = lambda i, k, signers, heads=("g",): grp(i, "offer", k, "founder", None, heads=heads, signer=signers[0],
                                              cosigners=tuple(signers[1:]) + (k,), counted="founder")   # k cosigns its own
INODE = lambda signers, heads=("g",), cites=(): grp("r", "offer", "n1", "node", None, heads=heads, signer=signers[0],
                                                    cosigners=tuple(signers[1:]), counted="founder", cites=cites)
GI1 = ST.offer("g", "f1", ("f1",), "founder", "@", "self", cohort_subkind="infrastructure", consensus_protocol="quorum:1/1",
               consensus_protocol_entrenched=True)
GI5 = ST.offer("g", "f1", ("f1", "f2", "f3", "f4", "f5"), "founder", "@", "self", cosigners=("f2", "f3", "f4", "f5"),
               cohort_subkind="infrastructure", consensus_protocol="quorum:3/5", consensus_protocol_entrenched=True)
GI9 = ST.offer("g", "f1", tuple("f%d" % i for i in range(1, 10)), "founder", "@", "self",
               cosigners=tuple("f%d" % i for i in range(2, 10)), cohort_subkind="infrastructure",
               consensus_protocol="quorum:5/9", consensus_protocol_entrenched=True)                  # nine founders
GIU = {k: v for k, v in GI.items() if k != "consensus_protocol_entrenched"}
GI9_6 = [GI9, ST.withdraw("w7", "f7", "g", ("g",)), ST.withdraw("w8", "f8", "g", ("w7",)), ST.withdraw("w9", "f9", "g", ("w8",))]
SEAT5 = ("f2", "f3", "f4", "f5")                                                                    # with f1: five voices                         # not entrenched
# L1: two concurrent founders' amendments over four founders (3/4), and the version that reconciles them
L1 = None   # set below, once GI4 is built
# the growth 2/3 -> 3/4 -> 3/5 -> 4/6, each amendment counted at the previous M
GROW = [GI, IAM("quorum:3/4", i="a4", seat=("f4",)),
        IAM("quorum:3/5", i="a5", heads=("a4",), cosigners=("f2", "f3"), seat=("f5",)),
        IAM("quorum:4/6", i="a6", heads=("a5",), cosigners=("f2", "f3"), seat=("f6",))]
W3 = ST.withdraw("w3", "f3", "g", ("g",))                                                         # f3 leaves
W4 = ST.withdraw("w4", "f4", "g", ("g",))
FRMN = lambda signers, heads=("g",), cites=(): grp("xn", "unseat", "n1", "node", None, heads=heads, signer=signers[0],
                                                   cosigners=tuple(signers[1:]), counted="founder", cites=cites)
FRMF = lambda k, signers, heads=("g",): grp("x", "unseat", k, "founder", None, heads=heads, signer=signers[0],
                                            cosigners=tuple(signers[1:]), counted="founder")
RECOVER = lambda heads=("g",), cites=(): grp("rv", "offer", "f4", "founder", None, heads=heads, signer="f4",
                                             counted="founder", bundle="B1", cites=cites)
GI4 = ST.offer("g", "f1", ("f1", "f2", "f3", "f4"), "founder", "@", "self", cosigners=("f2", "f3", "f4"),
               cohort_subkind="infrastructure", consensus_protocol="quorum:3/4",
               consensus_protocol_entrenched=True)                                                   # four founders
L1 = [GI4, IAM("quorum:3/5", i="a5", cosigners=("f2", "f3"), seat=("f5",)),
      IAM("quorum:3/5", i="a6", signer="f2", cosigners=("f3", "f4"), seat=("f6",))]
L1X1 = grp("x1", "unseat", "f1", "founder", None, heads=("a5", "a6"), signer="f4", cosigners=("f5", "f6"), counted="founder")
L1X2 = grp("x2", "unseat", "f4", "founder", None, heads=("a5", "a6"), signer="f1", cosigners=("f2", "f3"), counted="founder")
L1RC = IAM("quorum:4/6", i="rc", heads=("a5", "a6"), cosigners=("f2", "f3", "f5", "f6"))
AMU = REC("am", "quorum:2/4", cosigners=("B", "C", "D"))                                         # all four, to any two
RM_A = lambda heads: grp("x", "unseat", "D", "member", "community_remove", heads=heads, cosigners=("B",))   # A and B
CONTESTED = (True, True)          # the contested pair: neither removal in force, both stay (CC 2.7.7 rule 5)
CONCLUDE = [
    ("an admission stating accord_halt (one voice) is no admission's policy: with the table it concludes nothing",
     [GM4, grp("r", "offer", "E", "member", "accord_halt", cosigners=("E",))], "r", False, True),
    ("a removal stating cosigned_act: the removal's policy is fixed (community_remove), so nothing with the table; "
     "without it the room's protocol counts it (three of four)",
     [GM4, grp("r", "unseat", "D", "member", "cosigned_act", cosigners=("B", "C"))], "r", False, True),
    ("a removal stating none is counted under community_remove, the room's protocol: majority, three of four",
     [GM4, grp("r", "unseat", "D", "member", None, cosigners=("B", "C"))], "r", True, False),
    ("a removal under community_remove counts over the other members (\"the member being removed is not counted\"): "
     "of four, A alone (one of the three others) does not remove D",
     [GMJ, grp("r", "unseat", "D", "member", "community_remove")], "r", False, False),
    ("and A and B (two of the three others, more than half) do", [GMJ, grp("r", "unseat", "D", "member",
                                                                         "community_remove", cosigners=("B",))], "r",
     True, True),
    ("in a room of seven, four others removing E count as four of six", [GM7, grp("r", "unseat", "E", "member", None,
                                                                                 cosigners=("B", "C", "D"))], "r",
     True, False),
    ("in a room of six, three others removing F are three of five (more than half), where counting F would make them "
     "three of six", [GM6, grp("r", "unseat", "F", "member", None, cosigners=("B", "C"))], "r", True, False),
    ("in a community one voice never decides who is in a room (CC 4.5.13): of three, A and B remove C (two voices "
     "besides C)", [GM, grp("r", "unseat", "C", "member", None, cosigners=("B",))], "r", True, False),
    ("and in a room of two, A alone removes nobody: the floor of two voices besides the member removed",
     [ST.offer("g", "A", ("A", "B"), "member", "@", "self", cosigners=("B",)), grp("r", "unseat", "B", "member", None)],
     "r", False, False),
    ("a family has no floor: under quorum:1/3 one member removes another", [FAMQ, FREM("x", "C", signer="B", counted="member")],
     "x", True, False),
    ("and the member removed is no voice: F with two others is two of five", [GM6, grp("r", "unseat", "F", "member", None,
                                                                                      cosigners=("B", "F"))], "r",
     False, False),
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
    ("a node's seat over an infrastructure community, under the founders' protocol (quorum:2/3): two of three "
     "founders seat it, its own signature not asked",
     [GI, grp("r", "offer", "n1", "node", None, signer="f1", cosigners=("f2",), counted="founder")], "r", True, False),
    ("a node is no voice in the founders' count (its seat holds no founder's): f1 and the node n1 do not admit a "
     "founder (one of three founders)",
     [GI, IN1, grp("r", "offer", "f4", "founder", None, signer="f1", cosigners=("n1", "f4"), heads=("na",), counted="founder")],
     "r", False, False),
    # ---- an infrastructure community (CC 3.1.3.2 and 3.2): M founder voices (absolute, never lowered), live at M + 1;
    # founder seats added only by a founders' amendment (or the stalled recovery widening); its record entrenched
    ("two of three founders restate the record (quorum:2/3)", [GI, IAM("quorum:2/3")], "am", True, False),
    ("and one founder alone does not", [GI, IAM("quorum:2/3", cosigners=())], "am", False, False),
    ("four founders (quorum:3/4, live at four): three restate the record", [GI4, IAM("quorum:3/4", cosigners=("f2", "f3"))],
     "am", True, False),
    ("and two of four do not", [GI4, IAM("quorum:3/4")], "am", False, False),
    ("a key that is no founder signing in a founder's place is no voice: f1 and m1 do not change it",
     [GI, IAM("quorum:2/3", cosigners=("m1",))], "am", False, False),
    ("the founders are the founding row's signers it seats: a cosigner Z it does not name is no founder, so the word "
     "2/3 states its three, and f1 and f2 seat a node (H5)", [dict(GI, cosigners=("f2", "f3", "Z")), INODE(("f1", "f2"))],
     "r", True, False),
    ("a plain founder widening concludes nothing: founder seats are added by a founders' amendment",
     [GI, IAD("a4", "f4", ("f1", "f2"))], "a4", False, False),
    ("growth by amendment: f1 and f2 (the present M, 2) seat f4, signed by f4, restating quorum:3/4", GROW[:2], "a4", True,
     False),
    ("then f1, f2, f3 (M 3) seat f5, restating quorum:3/5", GROW[:3], "a5", True, False),
    ("then f1, f2, f3 seat f6, restating quorum:4/6", GROW, "a6", True, False),
    ("3/4 is live only at four: after f4 joins and leaves, f1, f2, f3 seat no node",
     GROW[:2] + [ST.withdraw("w4", "f4", "a4", ("a4",)), INODE(("f1", "f2", "f3"), heads=("a4",), cites=("w4",))], "r", False, False),
    ("an amendment's word states the founders it leaves: 2/3 to 3/5 at three founders is refused (no room stalls "
     "itself by a record change)", [GI, IAM("quorum:3/5")], "am", False, False),
    ("an amendment seating a key without that key's signature concludes nothing",
     [GI, dict(IAM("quorum:3/4", i="a4", seat=("f4",)), cosigners=("f2",))], "a4", False, False),
    ("an amendment seating a founder states the word for the founders after it: f4 seated under 2/3 is refused",
     [GI, IAM("quorum:2/3", i="a4", seat=("f4",))], "a4", False, False),
    ("a stalled room makes no amendment seating a founder (it is a widening by the founders' count)",
     [GI, W3, IAM("quorum:3/3", i="a4", heads=("g",), cites=("w3",), seat=("f4",))], "a4", False, False),
    ("a room that lost founders refills its own seats while live, the word unchanged: of nine (5/9) six remain, and an "
     "amendment seating a seventh under 5/9 concludes", GI9_6 + [IAM(None, i="aa", heads=("g",), cites=("w9",), cosigners=SEAT5, seat=("fa",))],
     "aa", True, False),
    ("the same version naming 4/7 is a weakening (M below 5) and concludes nothing",
     GI9_6 + [IAM("quorum:4/7", i="aa", heads=("g",), cites=("w9",), cosigners=SEAT5, seat=("fa",))], "aa", False, False),
    ("and naming 5/7 concludes nothing (5 is not 7's strict majority)",
     GI9_6 + [IAM("quorum:5/7", i="aa", heads=("g",), cites=("w9",), cosigners=SEAT5, seat=("fa",))], "aa", False, False),
    ("a shrunk room does not restate downward: at six, 4/6 is refused",
     GI9_6 + [IAM("quorum:4/6", i="aa", heads=("g",), cites=("w9",), cosigners=SEAT5)], "aa", False, False),
    ("above N the version names the new word: of three (2/3), seating f4 under the unchanged word is refused",
     [GI, IAM(None, i="a4", seat=("f4",))], "a4", False, False),
    ("after a removal (3/5 down to four), an amendment seating a fifth restates 3/5",
     [GI5, FRMF("f5", ("f1", "f2", "f3")), IAM("quorum:3/5", i="a6", heads=("x",), cosigners=("f2", "f3"), seat=("f6",))],
     "a6", True, False),
    ("M is the record's, never recomputed: after 4/6 and one leaving (five founders), three (their majority) seat no node",
     GROW + [ST.withdraw("w6", "f6", "a6", ("a6",)), INODE(("f1", "f2", "f3"), heads=("a6",), cites=("w6",))], "r", False, False),
    ("and four do", GROW + [ST.withdraw("w6", "f6", "a6", ("a6",)), INODE(("f1", "f2", "f3", "f4"), heads=("a6",), cites=("w6",))], "r",
     True, False),
    ("M is never lowered, stalled or live (L5): of five (3/5), f1, f2, f3 do not change the record to quorum:2/3",
     [GI5, IAM("quorum:2/3", cosigners=("f2", "f3"))], "am", False, False),
    ("nor after two leave and the room is stalled",
     [GI5, W4, ST.withdraw("w5", "f5", "g", ("w4",)), IAM("quorum:2/3", heads=("g",), cites=("w5",), cosigners=("f2", "f3"))], "am",
     False, False),
    ("a lawful removal may leave the room stalled (S3): of four (3/4), f1, f2, f3 remove f4",
     [GI4, FRMF("f4", ("f1", "f2", "f3"))], "x", True, False),
    ("and then the three seat no node", [GI4, FRMF("f4", ("f1", "f2", "f3")), INODE(("f1", "f2", "f3"), heads=("x",))], "r",
     False, False),
    ("concurrent founders' amendments (L1): of four (3/4), f1, f2, f3 seat f5 while f2, f3, f4 seat f6, each restating "
     "3/5; over both, no founders' count concludes: f4, f5, f6 do not remove f1", L1 + [L1X1], "x1", False, False),
    ("nor f1, f2, f3 remove f4", L1 + [L1X2], "x2", False, False),
    ("the reconciling version names both, signed by f5 and f6, restating 4/6, counted at 3 over the common four",
     L1 + [L1RC], "rc", True, False),
    ("and missing f6's signature it concludes nothing", L1 + [dict(L1RC, cosigners=("f2", "f3", "f5"))], "rc", False, False),
    ("after it, a removal at the new M (4) concludes: f1, f2, f3, f5 remove f6",
     L1 + [L1RC, FRMF("f6", ("f1", "f2", "f3", "f5"), heads=("rc",))], "x", True, False),
    ("M is at least two: a room founded under quorum:1/1 does not act", [GI1, INODE(("f1",))], "r", False, False),
    ("an infrastructure record must be entrenched: a founding without the flag concludes nothing",
     [GIU, INODE(("f1", "f2"))], "r", False, False),
    ("no weakening: an amendment moving admission_quorum_basis away from founders concludes nothing",
     [GI, IAM("quorum:2/3", admission_quorum_basis="members")], "am", False, False),
    ("live at three of three (M = 2): f1 and f2 seat a node", [GI, INODE(("f1", "f2"))], "r", True, False),
    ("one founder leaves, and the room is stalled: f1 and f2 seat no node", [GI, W3, INODE(("f1", "f2"), heads=("g",), cites=("w3",))],
     "r", False, False),
    ("nor remove one", [GI, IN1, dict(W3, names=("na",)), FRMN(("f1", "f2"), heads=("na",), cites=("w3",))], "xn", False, False),
    ("the recovery widening concludes nothing here (undecided: stalled_recovery_needs_bundle)",
     [GI, W3, RECOVER(heads=("g",), cites=("w3",))], "rv", False, False),
    ("its count is over the founders: a count over the members concludes nothing",
     [GI, grp("r", "offer", "n1", "node", None, signer="f1", cosigners=("f2",))], "r", False, False),
    ("a row naming a bundle is never counted by the founders' count: in a live room, f1, f2, f3 and f4 on it admit nobody",
     [GI4, dict(RECOVER(), cosigners=("f1", "f2", "f3"))], "rv", False, False),
    ("a founder's removal is an ordinary counted removal by M founders, the word left as it is",
     [GI, FRMF("f3", ("f1", "f2"))], "x", True, False),
    ("an infrastructure founding row with no founder seat (founded in `member`): its body is empty, so nothing concludes",
     [ST.offer("g", "f1", ("f1", "f2", "f3"), "member", "@", "self", cosigners=("f2", "f3"), cohort_subkind="infrastructure",
               consensus_protocol="quorum:2/3", consensus_protocol_entrenched=True), INODE(("f1", "f2"))], "r", False, False),
    ("a founding word stating another N concludes nothing: quorum:2/3 over four founders",
     [dict(GI4, consensus_protocol="quorum:2/3"), INODE(("f1", "f2", "f3"))], "r", False, False),
    ("a change naming an M that is not N's strict majority (quorum:3/3) concludes nothing",
     [GI, IAM("quorum:3/3", cosigners=("f2", "f3"))], "am", False, False),
    ("nor a protocol of another kind (majority)", [GI, IAM("majority")], "am", False, False),
    ("a node's voice is not counted in a change of the record: f1 and the node n1 do not change it",
     [GI, IN1, IAM("quorum:2/3", heads=("na",), cosigners=("n1",))], "am", False, False),
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
    # ---- step 5: the protocol change; Q1: a change meets the protocol in force and the standing default (both) -
    ("a change of the record's protocol (record_change) is counted under the protocol in force in its own past and the "
     "standing default: A, B, C of four (majority, two thirds) change it to quorum:2/4", [GM4, AM1], "am", True, False),
    ("a removal naming the change is counted under the new protocol: of a unanimous room changed to quorum:2/4, A and B "
     "remove D", [GU, AMU, RM_A(("am",))], "x", True, False),
    ("a removal beside the change (not in its past) is counted under the old one (unanimous): A and B do not",
     [GU, AMU, RM_A(("g",))], "x", False, False),
    ("a change signed by A and B is no change (two of four: not a majority), and the protocol stays",
     [GM4, REC("am", "quorum:2/4", cosigners=("B",)), RM_A(("am",))], "x", False, False),
    ("two concurrent changes naming different protocols: none is in force, and the removal concludes nothing",
     [GM4, AM1, REC("am2", "majority", signer="B", cosigners=("C", "D")), RM_A(("am", "am2"))], "x", False, False),
    ("a row stating a regime other than the protocol in force concludes nothing (a consistency check); with no table "
     "the stated regime is not read", [GM4, grp("r", "offer", "E", "member", "cosigned_act", cosigners=("B", "C", "E"),
                                             regime="unanimous")], "r", False, True),
    ("a row stating the protocol in force as its regime is counted as any", [GM4, grp("r", "offer", "E", "member", "cosigned_act",
                                                                                     cosigners=("B", "C", "E"), regime="majority")],
     "r", True, True),
    ("a change of the record is counted under the protocol in force in its own past, not the founding one: after a "
     "unanimous room's change to majority, A, B and C change it again (three of four: not unanimous)",
     [GU, REC("am", "majority", cosigners=("B", "C", "D")), REC("am2", "quorum:2/4", heads=("am",))], "am2", True, False),
    ("the newest change is in force, not any change: after quorum:2/4 and then unanimous, A and B do not remove D",
     [GU, AMU, REC("am2", "unanimous", heads=("am",)), RM_A(("am2",))], "x", False, False),
    ("the order of changes is read over the concluded past: a change naming only a row that did not conclude (which "
     "names the earlier change) is concurrent with that change, the two disagree, and the removal concludes nothing",
     [GM4, AM1, grp("n", "offer", "Q", "member", "community_invite", heads=("am",)),
      dict(REC("am2", "majority", heads=("am",), signer="B", cosigners=("C", "D")), names=("n",)),
      grp("x", "unseat", "D", "member", "community_remove", heads=("am2",), cosigners=("B", "C"))], "x", False, False),
    ("Q1: a change must meet the protocol in force as well as the standing default: A, B and C of a unanimous room do "
     "not change it to majority", [GU, REC("am", "majority")], "am", False, False),
    ("and the standing default as well as the protocol: A, B and C of five (a majority, not two thirds) change nothing",
     [GM5, REC("am", "quorum:2/5")], "am", False, False),
    ("N3's rows: A, B and C of a unanimous room of four do not change it to quorum:1/1 (refused twice over)",
     [GU, REC("am", "quorum:1/1")], "am", False, False),
    ("no community declares a one-voice protocol (CC 4.5.13): A, B and C of a majority room do not change it to quorum:1/4",
     [GM4, REC("am", "quorum:1/4")], "am", False, False),
    ("nor founds a room under one: a removal in a room founded quorum:1/4 concludes nothing",
     [dict(GM4, consensus_protocol="quorum:1/4"), grp("r", "unseat", "D", "member", None)], "r", False, False),
    ("nor under a weighted record one of whose weights reaches its threshold",
     [dict(GW, weights=(("A", 5), ("B", 2), ("C", 1), ("D", 1))), grp("r", "offer", "E", "member", None, cosigners=("E",))],
     "r", False, False),
    ("a change to a weighted record that weighs one key twice is refused at the change (W1)",
     [GM4, REC("am", "weighted:r", cosigners=("B", "C", "D"), need=5, weights=(("A", 3), ("A", 3), ("B", 1)))], "am",
     False, False),
    ("a change stating a policy of its own (default_content) is refused: the change's policies are fixed",
     [GM4, grp("am", "offer", (), "record", "default_content", cosigners=("B", "C"), consensus_protocol="quorum:2/4")],
     "am", False, True),
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
    ("a change of the record naming a policy word (accord_halt) concludes nothing",
     [GM4, REC("am", "accord_halt")], "am", False, False),
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
    ("founder_only is no community protocol (Q3: a family's): one founder's admission concludes nothing",
     [GF, grp("r", "offer", "D", "member", "cosigned_act", counted="founder", cosigners=("D",))], "r", False, False),
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
     [GW, grp("r", "offer", "E", "member", "cosigned_act", signer="D", cosigners=("E",), need=1, weights=(("D", 9),))], "r",
     False, False),
    ("under weighted, the weights and threshold are the protocol: on an entrenched record, restating them concludes "
     "nothing (E1)", [GWE, REC("am", "weighted:stake", cosigners=("B", "C"), need=4, weights=W_NEW,
                               consensus_protocol_entrenched=True)], "am", False, False),
    ("not entrenched, the restatement is a protocol change counted under the weights in force (A, B, C: six of five)",
     [GW, REC("am", "weighted:stake", cosigners=("B", "C"), need=4, weights=W_NEW)], "am", True, False),
    ("a weight is a whole number: a record weighing D at -5 states no weights, and nothing concludes under it",
     [dict(GW, weights=(("A", 3), ("B", 2), ("C", 1), ("D", -5))), grp("r", "offer", "E", "member", "cosigned_act",
                                                                       cosigners=("B", "E"))], "r", False, False),
    ("nor does a change to such a record", [GW, REC("am", "weighted:stake", cosigners=("B", "C"), need=4,
                                                     weights=(("A", 3), ("B", 2), ("C", 1), ("D", -5)))], "am", False, False),
    ("a weighted record that weighs one key twice states no weights: A and B admit nobody",
     [dict(GW, weights=(("A", 3), ("A", 2), ("B", 2), ("C", 1), ("D", 1))),
      grp("r", "offer", "E", "member", "cosigned_act", cosigners=("B", "E"))], "r", False, False),
    ("open:self_admit: E's own signature admits E", [GO, grp("r", "offer", "E", "member", "cosigned_act", signer="E")], "r",
     True, True),
    ("and an admission E did not sign does not", [GO, grp("r", "offer", "E", "member", "cosigned_act", cosigners=("B", "C"))],
     "r", False, False),
    # ---- a family (CC 3.3.4, 3.1.3.2, 4.5.12.5; the Constitution's family rulings and F1 to F5) -------------------
    ("under founder_only one active founder admits, with the joiner's own acceptance", [FAM, FADM("r", "D")], "r", True, False),
    ("a member who is no founder does not", [FAM, FADM("r", "D", signer="B")], "r", False, False),
    ("one active founder removes a member", [FAM, FREM("x", "C")], "x", True, False),
    ("one active founder changes the record (its protocol included)", [FAM, FREC("am", "majority")], "am", True, False),
    ("one active founder dissolves the family", [FAM, FDIS()], "d", True, False),
    ("after the dissolution no row over the family concludes (group_dissolved)", [FAM, FDIS(), FADM("r", "D", heads=("d",))],
     "r", False, False),
    ("nor one with the dissolution in its past at an older head",
     [FAM, FDIS(), dict(FADM("r", "D", heads=("g",)), names=("g", "d"))], "r", False, False),
    ("an acceptance after the dissolution concludes nothing: D, offered membership before it, accepts after",
     [FAM, FADM("r", "D", acc=False), FDIS(heads=("r",)), ST.accept("ad", "D", "r", ("d",))], "ad", False, False),
    ("a dissolution is counted at the newest heads in its own past: one beside the family's last version concludes "
     "nothing", [FAM, FADM("r", "D"), dict(FDIS(heads=("g",)), names=("g", "r"))], "d", False, False),
    ("and one naming that version concludes", [FAM, FADM("r", "D"), FDIS(heads=("r",))], "d", True, False),
    ("an entrenched protocol: a change of the protocol concludes nothing (F5)", [FAME, FREC("am", "majority")], "am",
     False, False),
    ("nor a change of the entrenchment flag", [FAME, FREC("am", "founder_only", consensus_protocol_entrenched=False)], "am",
     False, False),
    ("every other amendment concludes under the protocol: a rename", [FAME, FREC("am", None, name="the Smiths")], "am", True, False),
    ("and admission is unaffected", [FAME, FADM("r", "D")], "r", True, False),
    ("a founder's leaving ends its role in a row with the leaving in its past, whatever head it names (FA4b)",
     [FAM2, ST.withdraw("lv", "B", "g", ("g",)), dict(FADM("r", "D", signer="B"), names=("g", "lv"))], "r", False, False),
    ("a role outside a family is read nowhere: a community's admission carrying role founder concludes nothing",
     [GM4, grp("r", "offer", "E", "member", "cosigned_act", cosigners=("B", "C", "E"), role="founder")], "r", False, True),
    ("a resigned founder holds no authority: after A's resignation A does not admit D",
     [FAM, ST.withdraw("wa", "A", "g", ("g",)), FADM("r", "D", cites=("wa",))], "r", False, False),
    ("with the last founder gone nothing concludes: B and C (members) do not admit D under founder_only",
     [FAM, ST.withdraw("wa", "A", "g", ("g",)), grp("r", "offer", "D", "member", None, cites=("wa",), signer="B",
                                                    cosigners=("C", "D"), counted="founder")], "r", False, False),
    ("no last-founder refusal: the last founder's resignation concludes", [FAM, ST.withdraw("wa", "A", "g", ("g",))], "wa",
     True, True),
    ("the way out (F2): A promotes B (with B's acceptance), then leaves; B admits D",
     [FAM, FADM("p", "B", scope="founder"), ST.withdraw("wa", "A", "g", ("p",)), FADM("r", "D", signer="B", heads=("p",), cites=("wa",))],
     "r", True, False),
    ("F1: a member is admitted with the founder role (an admission, and a promotion naming it), then admits E",
     [FAM, FADM("r", "D"), FADM("p", "D", scope="founder", heads=("r",)), FADM("r2", "E", signer="D", heads=("p",))], "r2",
     True, False),
    ("a one-row founder admission: D, admitted with the founder role, admits E",
     [FAM, dict(FADM("r", "D"), role="founder"), FADM("r2", "E", signer="D", heads=("r",))], "r2", True, False),
    ("a promotion without the member's acceptance seats no founder: B, offered the role, does not admit D",
     [FAM, FADM("p", "B", scope="founder", acc=False), FADM("r", "D", signer="B", heads=("p",))], "r", False, False),
    ("a demotion by another founder: A demotes B, and B no longer admits",
     [FAM2, FREM("x", "B", scope="founder"), FADM("r", "D", signer="B", heads=("x",))], "r", False, False),
    ("a self-demotion: B lays its own role down by its own row, and no longer admits",
     [FAM2, ST.withdraw("wb", "B", "g", ("g",), scope="founder"), FADM("r", "D", signer="B", cites=("wb",))], "r",
     False, False),
    ("and B's demotion stays B's role alone: B is still a member", [FAM2, ST.withdraw("wb", "B", "g", ("g",), scope="founder")],
     "wb", True, True),
    ("a demotion with no other active founder concludes nothing: A alone does not demote A",
     [FAM, FREM("x", "A", scope="founder")], "x", False, False),
    ("F3: a removal naming only its own signer, on that signature alone, concludes nothing (the resignation is the "
     "leaving), even where one voice would meet the count (quorum:1/3)", [FAMQ, FREM("x", "B", signer="B", counted="member")],
     "x", False, False),
    ("quorum:1/3 in a family concludes: one member admits D (no floor of two voices)",
     [FAMQ, FADM("r", "D", counted="member")], "r", True, False),
    ("a family record carrying a duty map concludes nothing (F4: duty_holders_on_family)",
     [ST.found("g", "A", ("A", "B", "C"), {"founder": ("A",), "moderate": ("B",)}, cosigners=("B", "C"),
               group_kind="family", family_key_id="FK", consensus_protocol="founder_only"), FADM("r", "D")], "r", False, False),
    ("a family is keyless: a row signed by its family key admits nobody", [FAM, FADM("r", "D", signer="FK")], "r", False, False),
    # ---- the body a recall and a withdrawal count ------------------------------------------------------------------
    ("three agents do not recall a person moderator: a recall counted over the agents concludes nothing",
     [FH4, AG, grp("r", "unseat", "A", "moderate", None, heads=("ag",), signer="X", cosigners=("Y", "Z"), counted="agent")],
     "r", False, False),
    ("two of the five other duty holders do not withdraw B's moderate by counting the moderators alone",
     [G6, grp("r", "unseat", "B", "moderate", None, signer="A", cosigners=("F",), counted="moderate")], "r", False, False),
    # ---- N1: open:self_admit and founder_only govern admissions alone ----------------------------------------------
    ("in an open room (open:self_admit) a key's own change of the record is no admission: X alone changes nothing",
     [GO, REC("am", "quorum:2/4", signer="X", cosigners=(), to=("X",))], "am", False, False),
    # the reading of `&`: where the protocol states no rule for the act (the sheet), the other policy governs alone,
    # with the community floor of two voices
    ("an open room changes its record under default_standing alone (open:self_admit states no rule for it): two of "
     "three", [GO3, REC("am", "majority", cosigners=("B",))], "am", True, False),
    ("and one of three does not", [GO3, REC("am", "majority", cosigners=())], "am", False, False),
    ("a two-member open room needs both", [GO2, REC("am", "majority", cosigners=())], "am", False, False),
    ("and both change it", [GO2, REC("am", "majority", cosigners=("B",))], "am", True, False),
    ("an open room's protocol admits to the member seat alone: X's own offer of an agent's seat concludes nothing",
     [GO, grp("r", "offer", "X", "agent", "cosigned_act", signer="X")], "r", False, False),
    ("a one-member open room's one member does not: the community floor of two voices",
     [GO1, REC("am", "majority", cosigners=())], "am", False, False),
    ("open:self_admit states no removal: A and B do not remove D",
     [GO, grp("r", "unseat", "D", "member", None, cosigners=("B",))], "r", False, False),
    ("nor in a room naming founder_only (no community protocol)", [GF, REC("am", "majority")], "am", False, False),
    ("in an infrastructure community no key admits itself: X's own founder admission concludes nothing",
     [dict(GI, consensus_protocol="open:self_admit"), grp("r", "offer", "X", "founder", "cosigned_act", signer="X",
                                                         counted="founder")], "r", False, False),
    # ---- N2: the body an act counts is the act's own ---------------------------------------------------------------
    ("A, the one moderator, does not admit X by counting over `moderate`: an admission counts the members",
     [FH4, grp("r", "offer", "X", "member", "community_invite", cosigners=("X",), counted="moderate")], "r", False, True),
    ("and the same admission counted over the members (A, B, C of four) concludes",
     [FH4, grp("r", "offer", "X", "member", "community_invite", cosigners=("B", "C", "X"))], "r", True, True),
    ("an accord's holder seated in a scope of its own (solo) does not admit X by counting over it",
     [GA, ST.offer("so", "h1", "h1", "solo", OBJ, "self", ("g",)),
      grp("r", "offer", "X", "holder", "accord_majority", heads=("so",), signer="h1", counted="solo", cosigners=("X",))],
     "r", False, False),
    ("and h1 and h2, counted over the holders, do", [GA, grp("r", "offer", "X", "holder", "accord_majority", signer="h1",
                                                            counted="holder", cosigners=("h2", "X"))], "r", True, True),
    ("an admission to g counted over another room (A's own, h) concludes nothing (its heads are h's, too)",
     [GM4, ST.offer("h", "A", ("A",), "member", "@", "self"),
      grp("r", "offer", "X", "member", "community_invite", heads=("h",), cosigners=("X",), over="h")], "r", False, False),
    ("an accord's counted row stating none is a standing act, counted under accord_majority",
     [GA, grp("r", "offer", "h4", "holder", None, counted="holder", cosigners=("h1", "h2", "h4"))], "r", True, False),
]

# The wait at tips (step 5), and who stands: (name, rows, [(key, scope, stands)])
TIPS = [
    ("a family admission seats the joiner with its acceptance", [FAM, FADM("r", "D")], [("D", "member", True)]),
    ("and not without it", [FAM, FADM("r", "D", acc=False)], [("D", "member", False)]),
    ("a dissolution ends every seat over the family", [FAM, FDIS()], [("A", "member", False), ("B", "member", False),
                                                                     ("A", "founder", False)]),
    ("a promotion with acceptance seats the founder role", [FAM, FADM("p", "B", scope="founder")], [("B", "founder", True)]),
    ("a one-row founder admission (an admission carrying `role: founder`, accepted) seats the key as member and founder",
     [FAM, dict(FADM("r", "D"), role="founder")], [("D", "member", True), ("D", "founder", True)]),
    ("and the same row without the joiner's acceptance seats nobody", [FAM, dict(FADM("r", "D", acc=False), role="founder")],
     [("D", "member", False), ("D", "founder", False)]),
    ("a promoted founder who leaves the family holds no founder role", [FAM, FADM("p", "B", scope="founder"),
                                                                        ST.withdraw("wb", "B", "g", ("p",))],
     [("B", "founder", False), ("B", "member", False)]),
    ("a demotion ends the role and keeps the member", [FAM2, FREM("x", "B", scope="founder")],
     [("B", "founder", False), ("B", "member", True)]),
    ("a removal of a founder ends every seat it holds in the family, member and founder alike",
     [FAM2, FREM("x", "B")], [("B", "founder", False), ("B", "member", False)]),
    ("in an infrastructure community the founder seat is the founding seat itself: f1 and f2 remove f3 by an unseat of "
     "`founder`, and f3 holds no seat there", [GI, grp("x", "unseat", "f3", "founder", None, signer="f1", cosigners=("f2",),
                                                    counted="founder")],
     [("f3", "founder", False), ("f3", "member", False), ("f1", "founder", True)]),
    ("two founders removing each other concurrently (CC 2.7.7 rule 5, the contested pair): neither is in force, and "
     "both stay; a stuck family is not reachable by two members acting in good faith at the same moment",
     [FAM2, FREM("xa", "A", signer="B"), FREM("xb", "B")], [("A", "member", CONTESTED[0]), ("B", "member", CONTESTED[1])]),
    ("two founders demoting each other concurrently: both stay founders (FA5)",
     [FAM2, FREM("da", "B", scope="founder"), FREM("db", "A", signer="B", scope="founder")],
     [("A", "founder", True), ("B", "founder", True)]),
    ("an infrastructure pair (S4): of four (3/4), f1, f2, f3 remove f4 while f1, f2, f4 remove f3; neither is in force",
     [GI4, FRMF("f4", ("f1", "f2", "f3")), dict(FRMF("f3", ("f1", "f2", "f4")), id="x2")],
     [("f3", "founder", True), ("f4", "founder", True)]),
    ("a contested pair in a community too (CC 2.7.7 governs every group): of four, A and C remove D while A and D remove "
     "C at one head (each two of its three others, each needing the voice the other removes); neither is in force",
     [GM4, grp("x", "unseat", "D", "member", None, cosigners=("C",)), grp("x2", "unseat", "C", "member", None, cosigners=("D",))],
     [("C", "member", True), ("D", "member", True)]),
    ("a pair at different heads is read from the head each cut names: of four (3/4), X (f1, f2, f3) removes f4 at g "
     "while Y (f1, f2, f4) removes f3 at the later head r; f3's voice counts at X's own head, so X stands, and f4's is "
     "void from X's head on, so Y falls",
     [GI4, INODE(("f1", "f2", "f3")), FRMF("f4", ("f1", "f2", "f3")), dict(FRMF("f3", ("f1", "f2", "f4"), heads=("r",)), id="x2")],
     [("f4", "founder", False), ("f3", "founder", True)]),
    ("the one-sided variant is no pair: of five (3/5), X (f1, f2, f3) removes f4 and Y (f1, f2, f5) removes f3; Y needs "
     "nothing X removes and stands, X loses f3's voice and falls",
     [GI5, FRMF("f4", ("f1", "f2", "f3")), dict(FRMF("f3", ("f1", "f2", "f5")), id="x2")],
     [("f3", "founder", False), ("f4", "founder", True)]),
    ("a role on an own offer seats nothing: B's own offer of member to X carrying role founder (FA1b)",
     [FAM, ST.offer("o", "B", "X", "member", OBJ, "self", ("g",), cosigners=("X",), role="founder")], [("X", "founder", False)]),
    ("over infrastructure an own offer of a founder seat seats nothing (L6; P1-3)",
     [GI, ST.offer("o", "f1", "X", "founder", OBJ, "self", ("g",), cosigners=("X",))], [("X", "founder", False)]),
    ("a node's seat over an infrastructure community stands on the founders' count alone, by scope and kind",
     [GI, grp("r", "offer", "n1", "node", None, signer="f1", cosigners=("f2",), counted="founder")], [("n1", "node", True)]),
    ("every other seat needs the seated key's own consent: a flag `consent` on a counted admission waives nothing",
     [GM4, grp("r", "offer", "E", "member", "cosigned_act", cosigners=("B", "C"), consent="one")], [("E", "member", False)]),
    ("nor on a founder's seat over an infrastructure community",
     [GI, grp("r", "offer", "f4", "founder", None, signer="f1", cosigners=("f2",), consent="one", counted="founder")],
     [("f4", "founder", False)]),
    ("tips on either side of a change of protocol do not fold: X admitted under the new protocol at one tip, Y under "
     "two-path at another, and neither stands until a row names both",
     [GM4, AM1, grp("ax", "offer", "X", "member", "cosigned_act", heads=("am",), cosigners=("B", "X")),
      grp("ay", "offer", "Y", "member", "community_invite", cosigners=("B", "C", "Y"))],
     [("X", "member", False), ("Y", "member", False), ("B", "member", True)]),
    ("and once a row names both, both stand",
     [GM4, AM1, grp("ax", "offer", "X", "member", "cosigned_act", heads=("am",), cosigners=("B", "X")),
      grp("ay", "offer", "Y", "member", "community_invite", cosigners=("B", "C", "Y")),
      grp("az", "offer", "Z", "member", "cosigned_act", heads=("ax", "ay"), cosigners=("B", "Z"))],
     [("X", "member", True), ("Y", "member", True)]),
]

# The protocol set (data/consensus_protocols.tsv): (word, what seat.protocol_rule reads it as, or None)
PROTOCOL_WORDS = [
    ("founder_only", ("founder_only", None, None)), ("unanimous", ("unanimous", None, None)), ("majority", ("majority", None, None)),
    ("open:self_admit", ("open:self_admit", None, None)), ("quorum:2/3", ("quorum", 2, 3)), ("quorum:3/3", ("quorum", 3, 3)),
    ("quorum:999999999/999999999", ("quorum", 999999999, 999999999)), ("weighted:stake", ("weighted", None, None)),
    ("quorum:4/3", None), ("quorum:0/3", None), ("quorum:03/4", None), ("quorum:1000000000/1000000000", None),
    ("quorum:2", None), ("quorum:2/3/4", None), ("quorum:+2/3", None), ("quorum: 2/3", None), ("quorum", None),
    ("weighted:", None), ("weighted", None), ("two_thirds", None), ("one", None), ("open", None), ("Majority", None),
    ("accord_halt", None), ("cosigned_act", None), ("", None), ("quorum:２/3", None),
    ("quorum:2/4", ("quorum", 2, 4)), ("quorum:3/5", ("quorum", 3, 5)), ("quorum:1/1", ("quorum", 1, 1)),
]
# What the sheet says each protocol states a rule for (seat.protocol_states): (word, act, states)
SHEET_ANSWERS = [(w, act, ST.protocol_states(ST.protocol_rule(w)[0], act))
                 for w in ("founder_only", "unanimous", "majority", "quorum:2/3", "weighted:stake", "open:self_admit")
                 for act in ("admit", "remove", "other")]
EXPECT_SHEET = {("founder_only", "other"): False, ("open:self_admit", "remove"): False,
                ("open:self_admit", "other"): False}
# The protocol of an infrastructure community (P1): a quorum of its founders' strict majority, N // 2 + 1 of N
INFRA_WORDS = [("quorum:2/3", ("quorum", 2, 3)), ("quorum:3/4", ("quorum", 3, 4)), ("quorum:3/5", ("quorum", 3, 5)),
               ("quorum:2/2", ("quorum", 2, 2)), ("quorum:4/7", ("quorum", 4, 7)), ("quorum:1/1", None), ("quorum:1/2", None),
               ("quorum:2/5", None), ("quorum:3/3", None), ("quorum:2/4", None), ("quorum:3/6", None), ("majority", None),
               ("unanimous", None), ("founder_only", None), ("weighted:stake", None), ("two_thirds", None)]
# An infrastructure room's recovery widening while stalled (CC 3.2): undecided, with its reason. (name, rows, row, reason)
UNDECIDED = [
    ("stalled (f3 left): the recovery widening is undecided", [GI, W3, RECOVER(heads=("g",), cites=("w3",))], "rv",
     "stalled_recovery_needs_bundle"),
    ("live: the same row is no recovery", [GI, RECOVER()], "rv", None),
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
         grp("am", "offer", (), "record", None, heads=("g",), signer="A", cosigners=("B",),
             consensus_protocol="quorum:2/5"),
         _adm("af", "F", ("A", "B"), ("am",)),
         grp("mg", "offer", "G", "member", "cosigned_act", heads=("xb", "af"), signer="C", cosigners=("D", "E", "G")),
         _rem("xc", "C", ("F",), ("mg",))]
# Dissolution with no signer: when every member has an end of their seat, the group is dissolved. (name, rows, dissolved)
DISSOLVED = [
    ("all members leave the family: it is dissolved", [FAM, ST.withdraw("wa", "A", "g", ("g",)),
                                                       ST.withdraw("wb", "B", "g", ("g",)), ST.withdraw("wc", "C", "g", ("g",))],
     True),
    ("two of three leave: it is not", [FAM, ST.withdraw("wa", "A", "g", ("g",)), ST.withdraw("wb", "B", "g", ("g",))], False),
    ("a concluded dissolution", [FAM, FDIS()], True),
]

PENDING = [
    ("A1: two removed members' change of the record at an old head (to quorum:2/5) installs nothing: A and B do not "
     "seat F under it, and F alone does not remove C", _LINE, [(k, "member", k in "CDEG") for k in "ABCDEFG"]),
    ("A3: one founder's own offer seats no key in a room of several founders",
     [GM4, ST.offer("o", "A", "X", "member", OBJ, "self", ("g",), cosigners=("X",))], [("X", "member", False)]),
    ("the settling count (S4): a removal written forward naming both contested rows as its heads, f1, f2, f3 removing "
     "f4, concludes (neither earlier row in force there): needs the heads' reading of a past holding both",
     [GI4, FRMF("f4", ("f1", "f2", "f3")), dict(FRMF("f3", ("f1", "f2", "f4")), id="x2"),
      dict(FRMF("f4", ("f1", "f2", "f3"), heads=("x", "x2")), id="xs")], [("f4", "founder", False), ("f3", "founder", True)]),
    # FA6, restated by the ruling of 2026-11-27: A's demotion of B and B's dissolution at g are concurrent cuts that each
    # undo the other (the demotion removes the voice the dissolution needs, the dissolution ends the seat the demotion
    # needs): a dissolution is a cut over every seat for rule 5, so the two are contested and neither counts. The edge
# (confirmed by the Constitution): with only the two founders under founder_only nothing settles the pair (no third
# founder's count exists), so the family stands, and its members can leave
    ("FA6: A demotes B and B dissolves, both at g: contested cuts (rule 5, a dissolution a cut over every seat), neither "
     "counts: the family stands and B is still a founder", [FAM2, FREM("dm", "B", scope="founder"), FDIS("d", signer="B")],
     [("A", "member", True), ("C", "member", True), ("B", "founder", True)]),
    ("FA6: the same read by A, which acknowledged its own demotion: a sibling at its head is not behind it (the "
     "sibling-safe line), and rule 5 decides as for every reader", [FAM2, FREM("dm", "B", scope="founder"),
                                                                   FDIS("d", signer="B")],
     [("A", "member", True), ("C", "member", True), ("B", "founder", True)], "A"),
    ("FA6, the variant: B's dissolution names the demotion as its head: the demotion is in force there, B is no founder "
     "there, and the dissolution concludes nothing", [FAM2, FREM("dm", "B", scope="founder"),
                                                      FDIS("d", signer="B", heads=("dm",))],
     [("A", "member", True), ("C", "member", True), ("B", "member", True), ("B", "founder", False)]),
]
# review-54 on 091b14d (r62): rule 5 contests only among removals not void for the row or reader (the head rules'
# S''), and a reader holding two concurrent below-N seatings reads the founders common to them (reader_state)
GK = ST.offer("g", "A", ("A", "B", "C"), "member", "@", "self", cosigners=("B", "C"), consensus_protocol="majority")
_kadm = lambda i, k, signers, heads: grp(i, "offer", k, "member", "cosigned_act", heads=heads, signer=signers[0],
                                         cosigners=tuple(signers[1:]) + (k,))
_krem = lambda i, k, signers, heads: grp(i, "unseat", k, "member", None, heads=heads, signer=signers[0],
                                         cosigners=tuple(signers[1:]))
KL = [GK, _kadm("ad", "D", ("A", "B", "C"), ("g",)), _kadm("ae", "E", ("A", "B", "C", "D"), ("ad",))]
G6M = ST.offer("g", "A", tuple("ABCDEF"), "member", "@", "self", cosigners=tuple("BCDEF"))
T5H = grp("h", "offer", "Q", "member", "cosigned_act", signer="A", cosigners=("B", "C", "D", "Q"))
C1A = IAM(None, i="a", heads=("g",), cites=("w9",), cosigners=SEAT5, seat=("X1", "X2", "X3"))
C1B = IAM(None, i="b", heads=("g",), cites=("w9",), signer="f2", cosigners=("f3", "f4", "f5", "f6"), seat=("Y1", "Y2", "Y3"))
C2XA = grp("xa", "unseat", "f3", "founder", None, heads=("a",), signer="X1", cosigners=("X2", "X3", "f1", "f2"), counted="founder")
C2XB = grp("xb", "unseat", "f1", "founder", None, heads=("b",), signer="Y1", cosigners=("Y2", "Y3", "f3", "f4"), counted="founder")
PENDING += [
    ("K2: a forged removal (A with removed C) at the old head g is void for every reader holding ae (S''), so the "
     "honest removal of C stands and B is kept",
     KL + [_krem("x", "C", ("B", "D", "E"), ("ae",)), _krem("z", "B", ("A", "C"), ("g",))],
     [("C", "member", False), ("B", "member", True)]),
    # T5, restated by the ruling of 2026-11-27: the old expectation (y1 behind h, so y2 stands) assumed the line before
    # it was sibling-safe. Under the sibling-safe line y1 at g is a lawful sibling of h (h names g), not stale, so rule
    # 5's "from the head the cut names" gives y1 standing and y2 falling
    ("T5: y1 (A, B, C, D at g) is a sibling of h, which names g, and not behind it (the sibling-safe line); rule 5 from "
     "the head each cut names: y1 stands and y2 at h falls: E out, A kept",
     [G6M, T5H, _krem("y1", "E", "ABCD", ("g",)), _krem("y2", "A", "BCDE", ("h",))], [("A", "member", True), ("E", "member", False)]),
    ("T5b: swapped, y2 at g (E did not sign h) is not behind h; y2 stands, y1' falls: A out, E kept (as today)",
     [G6M, T5H, _krem("y1", "E", "ABCD", ("h",)), _krem("y2", "A", "BCDE", ("g",))], [("A", "member", False), ("E", "member", True)]),
    ("C1: a reader holding two concurrent below-N seatings reads the founders common to them: X1 to X3 and Y1 to Y3 "
     "are no founders for it", GI9_6 + [C1A, C1B], [(k, "founder", False) for k in ("X1", "X2", "X3", "Y1", "Y2", "Y3")]),
    ("C2: for that reader neither line's later removal stands: f3 and f1 are kept",
     GI9_6 + [C1A, C1B, C2XA, C2XB], [("f3", "founder", True), ("f1", "founder", True)]),
]
# flipped at the batch merge (heads b2d5aa4, room-keys-fix 1a059be, election2 8910e02): the pending rows that hold on
# the merged tree are failing cases now (A1, A3, K2, T5b, C1), and so, as ruled after it, are the settling count (rule
# (2) reads only ends in force), FA6 (a dissolution contested as a cut), T5 (restated to the sibling-safe line) and C2
# (the amendment wait read through reader_state)
HELD = ("A1:", "A3:", "K2:", "T5b:", "C1:", "the settling count (S4)", "FA6", "T5:", "C2:")
# the guard on the restatement (the Constitution's ruling, 2026-11-27): only MUTUAL dependence is contested. A lawful
# removal at head h of a voice a sibling change at h needed, the sibling touching no voice of the remover, stands, and
# the sibling falls (rule 4, from the head the cut names)
G8 = ST.offer("g", "A", tuple("ABCDEFGH"), "member", "@", "self", cosigners=tuple("BCDEFGH"))
TIPS += [
    ("the one-sided sibling: B, C, D and E remove F at g; A, B, F and G remove H at g, needing F's voice, and touching "
     "none of the first removal's: the first stands (F out) and the sibling falls (H kept): only mutual dependence is "
     "contested", [G8, _krem("x", "F", "BCDE", ("g",)), _krem("y", "H", "ABFG", ("g",))],
     [("F", "member", False), ("H", "member", True)]),
]
TIPS += [c for c in PENDING if c[0].startswith(HELD)]
PENDING = [c for c in PENDING if not c[0].startswith(HELD)]
# Q4, restated by the ruling of 2026-11-27: am2 names am, the newest counted change in its past (n did not conclude), so
# it is not concurrent with am, and the accidental freeze cannot arise: am2 concludes. That is Q4's purpose, met by H1
CONCLUDE_Q4 = [
    ("Q4: a change naming the record in force (am) as its head, past an admission that did not conclude, concludes (no "
     "freeze: H1)",
     [GM4, AM1, grp("n", "offer", "Q", "member", "community_invite", heads=("am",)),
      dict(REC("am2", "unanimous", heads=("am",), signer="B", cosigners=("C", "D")), names=("n",))], "am2", True),
]
PENDING_CONCLUDE = []

PLANTS = ("lift_unread", "election_unread", "recall_by_policy", "kind_unread", "key_kind_unread", "detect_unread",
          "binding_off", "stated_policy_free", "protocol_unread", "gate_reads_stated",
          "subkind_unread", "amendment_unread", "record_unread", "regime_unread",
          "regime_stated", "protocol_set_open", "row_need", "protocol_body_free", "disagreeing_first", "any_amendment",
          "record_by_founding", "body_free", "kind_partial", "election_any_duty", "node_consent_asked",
          "consent_one_waives", "infra_any_quorum", "infra_body_members", "infra_m_recomputed", "infra_stalled_admits",
          "infra_m_lowered", "infra_word_n_free", "infra_unentrenched", "infra_record_frozen",
          "infra_record_simple_majority", "record_change_as_admission", "self_admit_removal_counted", "body_from_row",
          "record_change_either_policy", "one_voice_community_protocol", "founder_only_community",
          "unstated_cosigned_blocks", "unstated_floor_unread", "founders_all_signers", "weights_twice_at_change",
          "family_founders_fixed", "family_floor_two", "family_last_founder_refused", "entrenched_amendable",
          "entrenched_whole_record", "dissolve_leaves_seats", "dissolve_unread", "role_unread",
          "contested_both_out", "role_on_own_offer", "entrenched_weights_free",
          "concurrent_amendments_free", "infra_word_restated_always", "contested_scoped_to_kinds",
          "contested_voice_everywhere", "negative_weight", "removal_counts_target", "removal_floor_unread",
          "end_of_contested_end", "dissolve_uncontested", "wait_reader_unread", "contested_one_sided")


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


def undecided(rows, rid, plant=None):
    with planted(plant):
        S = CK.concluded(CK.kept(list(rows)), lambda r, P, past: ST.seat_rule(r, P, past))
        P = [q for q in S.Cs if q["id"] in S.anc[rid]]
        return ST.stalled_recovery(S.by[rid], P, lambda a, b: a in S.anc[b])


def dissolved(rows, plant=None):
    with planted(plant):
        S = CK.concluded(CK.kept(list(rows)), lambda r, P, past: ST.seat_rule(r, P, past))
        return ST.Seats(S).dissolved(OBJ)


def tip_answers(plant=None, cases=None):
    out = []
    with planted(plant):
        for c in (TIPS if cases is None else cases):
            rows, asks, own = c[1], c[2], (c[3] if len(c) > 3 else None)    # an optional reader
            S = CK.concluded(CK.kept(list(rows)), lambda r, P, past: ST.seat_rule(r, P, past))
            Q = ST.Seats(S, own=own)
            out.append([Q.stands(k, sc, OBJ) for k, sc, _ in asks])
    return out


def main():
    problems = []
    for (name, _rows, asks, *_own), got in zip(TIPS, tip_answers()):
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
    for name, rows, want in DISSOLVED:
        got = dissolved(rows)
        if got != want:
            problems.append("dissolved %s: got %s, expected %s" % (name, got, want))
    for w, act, got in SHEET_ANSWERS:
        if got != EXPECT_SHEET.get((w, act), True):
            problems.append("the sheet: %s states a rule for %s: got %s" % (w, act, got))
    for w, want in INFRA_WORDS:
        if ST.infrastructure_rule(w) != want:
            problems.append("an infrastructure protocol word %r: got %s, expected %s" % (w, ST.infrastructure_rule(w), want))
    for name, rows, rid, want in UNDECIDED:
        if undecided(rows, rid) != want:
            problems.append("undecided %s: got %s, expected %s" % (name, undecided(rows, rid), want))
    for name, rows, rid, want in CONCLUDE_Q4:
        if concludes(rows, rid, True) != want:
            problems.append("%s: got %s, expected %s" % (name, concludes(rows, rid, True), want))
    for name, rows, rid, want in PENDING_CONCLUDE:
        got = concludes(rows, rid, True)
        print("  pending (does not hold on the merged tree): %s: %s" % (name, "holds" if got == want else
                                                                     "does not hold yet (got %s)" % got))
    for c, got in zip(PENDING, tip_answers(cases=PENDING)):
        want = [w for _, _, w in c[2]]
        print("  pending (does not hold on the merged tree): %s: %s" % (c[0], "holds" if got == want else
                                                                     "does not hold yet (got %s)" % got))
    caught = 0
    for plant in PLANTS:
        hit = [name for name, rows, rid, want in CASES if answer(rows, rid, plant) != want]
        hit += [c[0] for c in CONCLUDE if concludes(c[1], c[2], True, plant) != c[3]]
        hit += [c[0] for c in CONCLUDE_Q4 if concludes(c[1], c[2], True, plant) != c[3]]
        hit += ["tips: " + c[0] for c, got in zip(TIPS, tip_answers(plant)) if got != [w for _, _, w in c[2]]]
        hit += ["dissolved: " + c[0] for c in DISSOLVED if dissolved(c[1], plant) != c[2]]
        hit += ["undecided: " + c[0] for c in UNDECIDED if undecided(c[1], c[2], plant) != c[3]]
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
