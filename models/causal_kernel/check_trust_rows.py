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
    edge_countersign_unread  (seat.py) a one-officer affiliation's onward edge needs no countersign (item 8)
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
    amendment_as_cut         (d) a licence failing only under a concurrent amendment reads as cut (link_withdrawn)
    instant_over_reader      (b) a licence's instant is bounded below by every row the reader holds, not its own past
    scope_unread             (d) an end cuts every act of its key over the object, whatever scope it ends
    (retired: line_unread, the reader's acknowledged line unread: the line is kept, for a reader that took up a change
    whose bytes it no longer holds, but every row the model holds that a line covers it also holds as growth, so the
    held-growth rule (growth_held_unread) decides every case the model can build)
    termless_edge_walked     (d) an edge stating no term is walked
    lone_batch_unread        (a), (b) a holder's own concurrent lone duty conferrals are re-counted against each other
    end_scope_keyed          (d) an end cuts by the scope its target names, not by every standing its key loses
    one_end_at_a_time        (d) a key's loss is read with only the one end removed: a second end cancels the cut
    (retired at the one-target merge, each with no case the model can build that tells it apart:
    reseat_masks, a re-seat after the end masking the cut of a vote concurrent with the end: the seat model reads the
    concurrent end of a voice itself, so the vote is discounted there whatever the lane's cut reads (traced on the r81
    re-seat cases, with the re-seat brought into the judged rows: the lane's loss reads False and the licence is still
    cut);
    first_lost_only, one end removing several voices discounting only the first: no end ends two voices (a counted end
    has one target, as ruled; a withdrawal or lay-down ends its signer's own seat; a conferrer's withdrawal of an
    accepted conferral ends no seat), so every lost voice is still discounted, by its own end;
    ends_in_force_unread, an end the seat model holds out of force still ending a seat: the loss is read through the
    seat model's holders, which already drop a contested end, and a lone removal is of an agent's seat, which the seat
    model's ends name as no seat; the lane's own skip is kept as a shortcut)
    own_licence_uncountersigned  (b) a one-officer body's own licence stands without the countersign
    end_cuts_counted_row     (d) an end cuts a whole counted row its key signed, not only its voice
    (retired: built_on_cut_kept, a row built on a cut row kept. The seat model voids what rests on a cut row itself:
    a counted act counts only if the counted acts among its heads count, and a regrown lone conferral seats nothing;
    the lane's own built-on cut, wider than that, is gone)
    growth_ends_read         (a), (d) an end read as growth: the re-count, not the end rule, decides a cut (r81 E3)
    behind_grows             (seat.py) a row from behind the act (its heads in the act's past, older than the act's) is
                             growth against it: an acceptance of an offer in its past (r97 A1), an old-head batch (r98)
    growth_ends_unread       (seat.py) the grown body keeps the ends the reader holds (r97 V1, V2)
    ahead_unread             (seat.py) a row behind its signers' own later change is not re-counted against it (r97 B6, r99)
    stale_line_ahead         (seat.py) a change built on a row from behind the act counts as ahead of it (r99 k3)
    counted_recount_unread   (a) a counted seat conferral from an old past not re-counted against held growth (r95)
    still_holds_end_past     (d) whether the key still holds a standing is read over the end's past, not the judged rows
    growth_held_unread       (a), (b) an authority act concurrent with growth of its body the reader holds is not
                             re-counted over the grown body

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
TERM = {"asserted_at": 0, "expires_at": 10 ** 6}     # every edge carries a term (CC 4.4.3.12); the cases read at NOW_AT


def A(*a, **k):
    """An acceptance edge row with a term (an edge stating none is not walked)."""
    return dict(TR.accepts(*a, **k), **TERM)


NOW_AT = 50                                           # the caller's instant every case reads at, unless NOW says

AF = ST.found("af", "A", ("A", "B", "C"), cosigners=("B", "C"), declared_cohort="affiliations",
              licence_classes=((M, True), (L, False)))           # no officer: an affiliation DISSOLVED (CC 4.4.3.12)
AFD = ST.found("af", "A", ("A", "B", "C"), {ST.OFFICER: ("A", "B", "C")}, cosigners=("B", "C"),
               declared_cohort="affiliations", licence_classes=((M, True), (L, False)))   # three officers: majority declared
EWD = ST.withdraw("ewd", "A", "f", ("f",))                     # the officer's withdrawal of edge f
AFD1 = ST.found("af", "A", ("A", "B", "C"), {ST.OFFICER: ("A",)}, cosigners=("B", "C"), declared_cohort="affiliations",
                licence_classes=((M, True), (L, False)))         # one officer: its authority (the body is its officers)
AFD1O = dict(AFD1, official="O")                               # the same, its designated official O
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
ALO = ST.offer("alo", "A", ("X",), "license", "af", "group", ("af",), head=("af",), cosigners=("B",), counted=ST.OFFICER,
               policy="cosigned_act")      # the acts row's choice (`row`): the offer states which of its policies it takes
ALO1 = ST.offer("alo", "A", ("X",), "license", "af", "group", ("af",), head=("af",), counted=ST.OFFICER,
                policy="cosigned_act")
ALA = ST.accept("ala", "X", "alo")
# the affiliation's dissolution, by two of its three officers under its protocol, naming `names`
ADIS = lambda i, names: ST.offer(i, "A", (), "record", "af", "group", tuple(names) + ("af",), head=("af",),
                                 cosigners=("B",), counted=ST.OFFICER, dissolved_at=100, policy="cosigned_act")
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
    ("item 8: a one-officer affiliation's edge by its officer alone is a proposal: not walked",
     [AFD1O, A("e", "RD", "af", depth=1), A("f", "A", "K", on_behalf="af", names=("af",)), klic("l")], "RD", "l", KCH,
     NR),
    ("and with its designated official O's voice on the edge's own row (G15): walked",
     [AFD1O, A("e", "RD", "af", depth=1), A("f", "A", "K", on_behalf="af", names=("af",), cosigners=("O",)), klic("l")],
     "RD", "l", KCH, OK),
    ("and the officer withdraws the countersigned edge: ended, not walked",
     [AFD1O, A("e", "RD", "af", depth=1), A("f", "A", "K", on_behalf="af", names=("af",), cosigners=("O",)), EWD,
      klic("l")], "RD", "l", KCH, NR),
    ("an outside voice that is no countersigner (X) decides nothing: not walked",
     [AFD1O, A("e", "RD", "af", depth=1), A("f", "A", "K", on_behalf="af", names=("af",), cosigners=("X",)), klic("l")],
     "RD", "l", KCH, NR),
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
                 counted=ST.OFFICER, consensus_protocol="unanimous", declared_cohort="affiliations", policy="cosigned_act",
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
    ("r73 P2 and naming only af (concurrent with the amendment): judged under it, its count not met",
     [AFD, R_AMD, A("e", "RD", "af"), glic("l", cosigners=("B",))], "RD", "l", None, NA),
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
    ("founding gives no lone path: a founding signer who holds no duty, its own license seat over GD",
     [GD, R_SO("license", "g", "C"), A("e", "RD", "g"), glic("l", "g", "C") | {"names": ("so",)}], "RD", "l", None, NA),
    ("and a founding duty holder of two, its own license seat alone",
     [GD, R_SO("license", "g", "A"), A("e", "RD", "g"), glic("l", "g", "A") | {"names": ("so",)}], "RD", "l", None, NA),
    ("an edge within its term at the caller's instant (50)",
     [A("e", "RD", "K") | {"asserted_at": 10, "expires_at": 100}, klic("l") | {"asserted_at": 50}], "RD", "l", KCH, OK),
    ("an edge whose term has ended at the caller's instant (150)",
     [A("e", "RD", "K") | {"asserted_at": 10, "expires_at": 100}, klic("l") | {"asserted_at": 50}], "RD", "l", KCH,
     NR),
    ("r77 N8 a term-bearing edge read with no caller's instant: not walked (never at the licence's own instant)",
     [A("e", "RD", "K") | {"asserted_at": 0, "expires_at": 100}, klic("l") | {"asserted_at": 50}], "RD", "l", KCH, NR),
    ("r77 K3 an edge stating no term is not walked (every edge carries one)",
     [dict(TR.accepts("e", "RD", "K")), klic("l")], "RD", "l", KCH, NR),
]
# ---- the r77 attack (review-scratch ebd8200, r77/n1 to n5), each a case ------------------------------------------
ACK = lambda i, obj, head: CK.row(i, "ack", "RD", (head,), room=obj, head=(head,))   # the reader takes up a change
R_DC, R_DCA = ST.offer("dc", "A", "C", "moderate", "g", "self", ("g",)), ST.accept("dca", "C", "dc")  # A confers on C
R_LS, R_LSA = ST.offer("ls", "A", "X", "license", "g", "self", ("g",)), ST.accept("lsa", "X", "ls")   # A alone, at g
R_AOB = ST.offer("aob", "A", ("B",), "member", "af", "group", ("af",), head=("af",), cosigners=("B",),
                 counted=ST.OFFICER, role=ST.OFFICER)                                              # A appoints B
R_AOBO = dict(R_AOB, cosigners=("B", "O"))       # with its official's voice on the row: the countersign (item 8, G15)
AFD1O = dict(AFD1, official="O")                               # AFD1 with its designated official O (item 8)
R_G2 = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("A", "B"), "review": ("A",)}, cosigners=("B", "C"),
                licence_classes=((M, False),))
R_LDR = ST.withdraw("ldr", "A", "g", (), scope="review")         # A lays down review only; it still holds moderate
R_ZO = ST.offer("zo", "Z", "Z", "x", "Z", "self")
R_ZW = dict(ST.withdraw("zw", "Z", "zo", ("zo",)), asserted_at=10 ** 9)   # an unrelated key's late-dated row
GROWN = [dict(GD, consensus_protocol="majority")]
for _k, _m, _pv in zip("DEFG", ("ABC", "ABCD", "ABCDE", "ABCDEF"), ("g", "aD", "aE", "aF")):
    GROWN.append(ST.offer("a" + _k, _m[0], (_k,), "member", "g", "group", (_pv,), head=(_pv,),
                          cosigners=tuple(_m[1:]) + (_k,), policy="community_invite"))
CASES += [
    ("r77 N1 A and C hold; A alone signs g's edge naming dca: not the body",
     [G1, R_DC, R_DCA, A("e", "RD", "g", depth=1), A("f", "A", "K", on_behalf="g", names=("dca",)), klic("l")], "RD",
     "l", KCH, NR),
    ("r77 N1b and naming only g, behind the reader's line (it took up dca): concludes nothing",
     [G1, R_DC, R_DCA, ACK("ak", "g", "dca"), A("e", "RD", "g", depth=1),
      A("f", "A", "K", on_behalf="g", names=("g",)), klic("l")], "RD", "l", KCH, NR),
    ("r77 N1b an OUTSIDER holding dca, acknowledging nothing: the edge is counted over the grown body",
     [G1, R_DC, R_DCA, A("e", "RD", "g", depth=1), A("f", "A", "K", on_behalf="g", names=("g",)), klic("l")], "RD",
     "l", KCH, NR),
    ("r77 N1b the outsider holding none of the growth: the residual (it cannot know)",
     [G1, A("e", "RD", "g", depth=1), A("f", "A", "K", on_behalf="g", names=("g",)), klic("l")], "RD", "l", KCH, OK),
    ("r77 an honest pre-growth edge the growth has in its past stands",
     [G1, A("e", "RD", "g", depth=1), A("f", "A", "K", on_behalf="g", names=("g",)),
      ST.offer("dc", "A", "C", "moderate", "g", "self", ("f",)), R_DCA, klic("l")], "RD", "l", KCH, OK),
    ("r77 N2 the outsider holding dca: the concurrent lone license seat is re-counted, X's licence testimony",
     [G1, R_DC, R_DCA, R_LS, R_LSA, A("e", "RD", "g"), glic("l", "g", "X") | {"names": ("lsa",)}], "RD", "l", None, NA),
    ("r77 N2 holding none of the growth: the residual",
     [G1, R_LS, R_LSA, A("e", "RD", "g"), glic("l", "g", "X") | {"names": ("lsa",)}], "RD", "l", None, OK),
    ("r77 N4c the outsider holding aob and its countersign: A's own licence counted over officers A and B",
     [AFD1O, R_AOBO, A("e", "RD", "af"), glic("l", "af", "A")], "RD", "l", None, NA),
    ("r77 N4c' holding aob uncountersigned (item 8): B is no officer, A's licence with O's voice on it stands",
     [AFD1O, R_AOB, A("e", "RD", "af"), glic("l", "af", "A", cosigners=("O",))], "RD", "l", None, OK),
    ("r77 N4c holding none: the residual (O's voice on A's licence, as item 8 asks of a one-officer body)",
     [AFD1O, A("e", "RD", "af"), glic("l", "af", "A", cosigners=("O",))], "RD", "l", None, OK),
    ("r77 N4e the outsider holding aob: A's edge for af", [AFD1O, R_AOBO, A("e", "RD", "af", depth=1),
                                                          A("f", "A", "K", on_behalf="af", names=("af",)),
                                                          klic("l")], "RD", "l", KCH, NR),
    ("r77 N4e holding none: under item 8 the lone officer's edge is a proposal, and with no official and no overseer "
     "nothing decides it: not walked", [AFD1, A("e", "RD", "af", depth=1),
                                        A("f", "A", "K", on_behalf="af", names=("af",)), klic("l")], "RD", "l",
     KCH, NR),
    ("r77 N5b the outsider holding the admissions to aG: A and B's quorum licence",
     GROWN + [A("e", "RD", "g"), glic("l", "g", cosigners=("B",))], "RD", "l", None, NA),
    ("r77 N5b holding none: two of three, the residual",
     [GROWN[0], A("e", "RD", "g"), glic("l", "g", cosigners=("B",))], "RD", "l", None, OK),
    ("r77 N2 A alone confers a license seat naming only g, behind the line: X's licence is testimony",
     [G1, R_DC, R_DCA, R_LS, R_LSA, ACK("ak", "g", "dca"), A("e", "RD", "g"),
      glic("l", "g", "X") | {"names": ("lsa", "dca")}], "RD", "l", None, NA),
    ("r77 N4c A alone, lone officer before B's appointment, licenses naming only af, behind the line",
     [AFD1O, R_AOBO, ACK("ak", "af", "aob"), A("e", "RD", "af"), glic("l", "af", "A")], "RD", "l", None, NA),
    ("r77 N4e and an edge for af naming only af, behind the line",
     [AFD1O, R_AOBO, ACK("ak", "af", "aob"), A("e", "RD", "af", depth=1),
      A("f", "A", "K", on_behalf="af", names=("af",)), klic("l")], "RD", "l", KCH, NR),
    ("r77 N5b a grown community: A and B's quorum licence naming only g, behind the line (it took up aG)",
     GROWN + [ACK("ak", "g", "aG"), A("e", "RD", "g"), glic("l", "g", cosigners=("B",))], "RD", "l", None, NA),
    ("r77 N5 and naming aG: two of seven, not its quorum", GROWN + [A("e", "RD", "g"),
                                                                  glic("l", "g", cosigners=("B",)) | {"names": ("aG",)}],
     "RD", "l", None, NA),
    ("r77 N6 A lays down review, still holding moderate: the concurrent license seat is not cut",
     [R_G2, R_LDR, A("e", "RD", "g"), GLO, GLA, glic("l", "g", "X") | {"names": ("gla",)}], "RD", "l", None, OK),
    ("r77 D1 an unrelated key's late-dated row sets no lower bound on a licence",
     [E0, klic("l") | {"asserted_at": 50}, R_ZO, R_ZW], "RD", "l", KCH, OK),
    ("r77 D2b nor on one under a termed seat", [G1, G1LT, GLA, A("e", "RD", "g"),
                                               glic("l", "g", "X") | {"names": ("gla",), "asserted_at": 50}, R_ZO,
                                               R_ZW], "RD", "l", None, OK),
]

# ---- the r80 attack (review-scratch fac316d, r80/m1 to m4), each a case ------------------------------------------
_DC1, _DA1 = ST.offer("dc1", "A", "C", "moderate", "g", "self", ("g",)), ST.accept("da1", "C", "dc1")
_DC2, _DA2 = ST.offer("dc2", "A", "B", "moderate", "g", "self", ("g",)), ST.accept("da2", "B", "dc2")
_GLO_C = ST.offer("glo", "A", ("X",), "license", "g", "group", ("dca",), head=("dc",), cosigners=("C",), counted="duty")
_AOB = ST.offer("aob", "A", ("B",), "member", "af", "group", ("af",), head=("af",), cosigners=("B",),
                counted=ST.OFFICER, role=ST.OFFICER)
_LSO = ST.offer("lso", "A", ("X",), "license", "af", "group", ("aob",), head=("aob",), cosigners=("B",),
                policy="cosigned_act",
                counted=ST.OFFICER)                    # names the appointment's countersign: B an officer at its head
_RV = ST.offer("rv", "A", "A", "review", "g", "group", ("g",), head=("g",), cosigners=("B",), counted="duty",
               policy="duty_confer")
_GLO_RV = ST.offer("glo", "A", ("X",), "license", "g", "group", ("rv",), head=("rv",), cosigners=("B",), counted="duty",
                   policy="duty_confer")
_X = glic("l", "g", "X") | {"names": ("gla",)}
CASES += [
    ("r80 F1 C (a duty holder by A's lone conferral) resigns from g, concurrent with A and C's license conferral: cut",
     [G1, R_DC, R_DCA, ST.withdraw("wc", "C", "g"), _GLO_C, GLA, A("e", "RD", "g"), _X], "RD", "l", None, LW),
    ("r80 F1' a resignation naming dca concludes nothing (it names no newest head, H4): no end, nothing cut",
     [G1, R_DC, R_DCA, ST.withdraw("wc", "C", "g", ("dca",)), _GLO_C, GLA, A("e", "RD", "g"), _X], "RD", "l", None, OK),
    ("r80 F1c with no resignation", [G1, R_DC, R_DCA, _GLO_C, GLA, A("e", "RD", "g"), _X], "RD", "l", None, OK),
    ("r80 F2 an appointed officer withdraws its appointment, concurrent with the officers' license conferral: cut",
     [AFD1O, dict(_AOB, cosigners=("B", "O")), ST.withdraw("wb", "B", "aob", ("aob",)), _LSO, ST.accept("lsa", "X", "lso"), A("e", "RD", "af"),
      glic("l", "af", "X") | {"names": ("lsa",)}], "RD", "l", None, LW),
    ("r80 F2c with no withdrawal", [AFD1O, dict(_AOB, cosigners=("B", "O")), _LSO, ST.accept("lsa", "X", "lso"), A("e", "RD", "af"),
                                    glic("l", "af", "X") | {"names": ("lsa",)}], "RD", "l", None, OK),
    ("r80 F3 A lays down moderate concurrent with its counted review seat and the conferral: A still a holder",
     [GD, _RV, ST.withdraw("ldm", "A", "g", (), scope="moderate"), _GLO_RV, GLA, A("e", "RD", "g"), _X], "RD", "l",
     None, OK),
    ("r80 F4 two concurrent lone conferrals; an edge by A and C naming da1",
     [G1, _DC1, _DA1, _DC2, _DA2, A("e", "RD", "g", depth=1),
      A("f", "A", "K", on_behalf="g", names=("da1",), cosigners=("C",)), klic("l")], "RD", "l", KCH, OK),
    ("r80 F4b and naming both", [G1, _DC1, _DA1, _DC2, _DA2, A("e", "RD", "g", depth=1),
                                 A("f", "A", "K", on_behalf="g", names=("da1", "da2"), cosigners=("C",)), klic("l")],
     "RD", "l", KCH, OK),
    ("r80 F4e a holder's own concurrent lone conferrals are one batch: A, B and C's conferral naming both stands",
     [G1, _DC1, _DA1, _DC2, _DA2, ST.offer("glo", "A", ("X",), "license", "g", "group", ("da1", "da2"),
                                          head=("dc1", "dc2"), cosigners=("B", "C"), counted="duty"), GLA,
      A("e", "RD", "g"), _X], "RD", "l", None, OK),
    ("r80 F4g and A and C's conferral at dc1, the reader holding dc2 too",
     [G1, _DC1, _DA1, ST.offer("glo", "A", ("X",), "license", "g", "group", ("da1",), head=("dc1",), cosigners=("C",),
                               counted="duty"), GLA, _DC2, _DA2, A("e", "RD", "g"), _X], "RD", "l", None, OK),
]

# ---- the r81 attack (review-scratch 2797fb0, r81/charter b1, b2), each a case -----------------------------------
_GY = ST.offer("gy", "A", ("Y",), "license", "g", "group", ("da1",), head=("dc1",), cosigners=("C",), counted="duty")
_GYA = ST.accept("gya", "Y", "gy")
_B = [G1, _DC1, _DA1, _GY, _GYA, _DC2, _DA2]
_L1 = ST.withdraw("l1", "A", "g", (), scope="moderate")
_G3 = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("A", "B", "C")}, cosigners=("B", "C"),
               licence_classes=((M, False),))
_GLO_G = ST.offer("glo", "A", ("X",), "license", "g", "group", ("g",), head=("g",), cosigners=("B",), counted="duty")
_U1 = ST.unseat("u1", "B", "A", "moderate", "g", "group", ("g",), head=("g",), cosigners=("C",), counted="duty",
                policy="duty_withdraw")
_RC = ST.offer("rc", "B", ("A",), "moderate", "g", "group", ("u1",), head=("u1",), cosigners=("C", "A"),
               counted="duty", policy="duty_confer")             # B and C seat A again, naming its removal
CASES += [
    ("r81 B3 A's later lone conferral (dc2) re-counted against the grown body's counted act gy: X's licence via it falls",
     _B + [ST.offer("gx", "A", ("X",), "license", "g", "group", ("da2", "gya"), head=("gy", "dc2"), cosigners=("B",),
                    counted="duty"), ST.accept("gxa", "X", "gx"), A("e", "RD", "g"),
           glic("l", "g", "X") | {"names": ("gxa",)}], "RD", "l", None, NA),
    ("r81 B4 and A and B's edge for g on it", _B + [A("e", "RD", "g", depth=1),
                                                     A("f", "A", "K", on_behalf="g", names=("da2", "gya"),
                                                       cosigners=("B",)), klic("l")], "RD", "l", KCH, NR),
    ("r81 E1 two identical lay-downs concurrent with A and B's conferral: still cut",
     [GD, _L1, ST.withdraw("l2", "A", "g", (), scope="moderate"), A("e", "RD", "g"), GLO, GLA, _X], "RD", "l", None, LW),
    ("r81 E2 a lay-down and a full resignation, both concurrent: still cut",
     [GD, _L1, ST.withdraw("l3", "A", "g", ()), A("e", "RD", "g"), GLO, GLA, _X], "RD", "l", None, LW),
    ("r81 E3 the same removal written twice", [_G3, _U1, dict(_U1, id="u2"), _GLO_G, GLA, A("e", "RD", "g"), _X], "RD",
     "l", None, LW),
    ("r81 E3b the removal and A's own resignation", [_G3, _U1, ST.withdraw("rs", "A", "g"), _GLO_G, GLA,
                                                    A("e", "RD", "g"), _X], "RD", "l", None, LW),
    ("r81 the re-seat does not mask the cut: A removed by u1, seated again naming it, voting concurrent with u1",
     [_G3, _U1, _RC, _GLO_G, GLA, A("e", "RD", "g"), _X], "RD", "l", None, LW),
    ("r81 and a vote after the genuine re-seat stands",
     [_G3, _U1, _RC, dict(_GLO_G, names=("rc",), head=("rc",)), GLA, A("e", "RD", "g"), _X], "RD", "l", None, OK),
]

# ---- the r87 attack (review-scratch b525c50, r87-attackr/c1), each a case ---------------------------------------
_GLO3 = ST.offer("glo", "A", ("X",), "license", "g", "group", ("g",), head=("g",), cosigners=("B", "C"), counted="duty")
_RC_C = ST.withdraw("rc", "C", "g")
_RC_B = ST.withdraw("rc", "B", "g")
CASES += [
    ("r87 C1c A, B and C confer a license seat on X", [_G3, _GLO3, GLA, A("e", "RD", "g"), _X], "RD", "l", None, OK),
    ("r87 C1 C resigns concurrently: its voice is discounted, A and B are still two of three",
     [_G3, _GLO3, GLA, _RC_C, A("e", "RD", "g"), _X], "RD", "l", None, OK),
    ("r87 C1b and Y's seat built on that conferral stands",
     [_G3, _GLO3, GLA, ST.offer("gy", "A", ("Y",), "license", "g", "group", ("gla",), head=("glo",), cosigners=("B",),
                                counted="duty"), ST.accept("gya", "Y", "gy"), _RC_C, A("e", "RD", "g"),
      glic("ly", "g", "Y") | {"names": ("gya",)}], "RD", "ly", None, OK),
    ("r87 C1d A and B confer, C (no voice of it) resigns concurrently", [_G3, _GLO_G, GLA, _RC_C, A("e", "RD", "g"), _X],
     "RD", "l", None, OK),
    ("r87 and where the resigner was needed (A and B of three, B resigns): the count fails, cut",
     [_G3, _GLO_G, GLA, _RC_B, A("e", "RD", "g"), _X], "RD", "l", None, LW),
]

_GLO_AB = ST.offer("glo", "A", ("X",), "license", "g", "group", ("g",), head=("g",), cosigners=("B",), counted="duty")
_GY_BC = ST.offer("gy", "B", ("Y",), "license", "g", "group", ("gla",), head=("glo",), cosigners=("C",), counted="duty")
CASES += [
    ("r87 C2c a one-officer affiliation's own licence, uncountersigned: a proposal, testimony",
     [AFD1O, A("e", "RD", "af"), glic("l", "af", "A")], "RD", "l", None, NA),
    ("r87 C2c with its official's countersign: honoured",
     [AFD1O, A("e", "RD", "af"), glic("l", "af", "A", cosigners=("O",))], "RD", "l",
     None, OK),
    ("r87 C2c' a voice on it from a key that is neither the official nor an overseer: no countersign, testimony",
     [AFD1O, A("e", "RD", "af"), glic("l", "af", "A", cosigners=("Z",))], "RD", "l", None, NA),
    ("a row built on a conferral an END cuts is cut with it: B and C's seat for Y on A and B's, A laying down",
     [_G3, _GLO_AB, GLA, _GY_BC, ST.accept("gya", "Y", "gy"), _L1, A("e", "RD", "g"),
      glic("ly", "g", "Y") | {"names": ("gya",)}], "RD", "ly", None, LW),
]

# ---- review-54's DRY audit: the seat model's voices path and its ends, read as Seats reads them ------------------
_G4 = ST.found("g", "A", ("A", "B", "C", "D"), {"moderate": ("A", "B", "C", "D")}, cosigners=("B", "C", "D"),
               licence_classes=((M, False),))
_U_C = ST.unseat("u1", "A", "C", "moderate", "g", "group", ("g",), head=("g",), cosigners=("B",), counted="duty",
                 policy="duty_withdraw")                          # A and B remove C's duty
_U_A = ST.unseat("u2", "C", "A", "moderate", "g", "group", ("g",), head=("g",), cosigners=("D",), counted="duty",
                 policy="duty_withdraw")                          # C and D remove A's, concurrently: rule 5 contests both
_GLO_CD = ST.offer("glo", "C", ("X",), "license", "g", "group", ("g",), head=("g",), cosigners=("D", "B"),
                   counted="duty")                                # C, D and B: three of four duty holders
_CB = CK.row("cb", "cosign", "B", ("g",), of="cx")                 # B's cosign row for the conferral's content
_GLO_CS = ST.offer("glo", "A", ("X",), "license", "g", "group", ("g", "cb"), head=("g",), counted="duty", content="cx")
CASES += [
    # the licence names both removals: rule 5 is read over its own past too (with u1 alone there, A and B's removal
    # of C is uncontested and concurrent with C's conferral, so C's voice is discounted at issuance)
    ("DRY a removal rule 5 holds contested out ends nothing: C's conferral beside it stands",
     [_G4, _U_C, _U_A, _GLO_CD, GLA, A("e", "RD", "g"), glic("l", "g", "X") | {"names": ("gla", "u1", "u2")}],
     "RD", "l", None, OK),
    ("DRY a voice given by a cosign row is a voice the end discounts: B resigns, A alone of three, cut",
     [_G3, _CB, _GLO_CS, GLA, _RC_B, A("e", "RD", "g"), _X], "RD", "l", None, LW),
    ("DRY and with no resignation the cosign row's voice makes A and B two of three",
     [_G3, _CB, _GLO_CS, GLA, A("e", "RD", "g"), _X], "RD", "l", None, OK),
]

_GLO_4 = ST.offer("glo", "A", ("X",), "license", "g", "group", ("g",), head=("g",), cosigners=("B", "C", "D"),
                  counted="duty")                                 # all four duty holders
_U_AB = dict(ST.unseat("u12", "C", "A", "moderate", "g", "group", ("g",), head=("g",), cosigners=("D",),
                       counted="duty", policy="duty_withdraw"),
             to=("A", "B"), cuts=ST._slots(("A", "B"), "moderate", "g"))   # C and D remove A's and B's duty in one row
_U_A1 = ST.unseat("u1", "C", "A", "moderate", "g", "group", ("g",), head=("g",), cosigners=("D",), counted="duty",
                  policy="duty_withdraw")                          # C and D remove A's duty
_U_B1 = ST.unseat("u2", "C", "B", "moderate", "g", "group", ("g",), head=("g",), cosigners=("D",), counted="duty",
                  policy="duty_withdraw")                          # and B's, in a row of its own
CASES += [
    # one target per counted end (ruled): a removal naming two keys concludes nothing, so it ends neither
    ("review-53 D1 one unseat naming two voices of a counted row is no counted end: it concludes nothing, the licence "
     "stands", [_G4, _GLO_4, GLA, _U_AB, A("e", "RD", "g"), _X], "RD", "l", None, OK),
    ("review-53 D1 two one-target removals of two voices of a counted row discount both: C and D are two of four, cut",
     [_G4, _GLO_4, GLA, _U_A1, _U_B1, A("e", "RD", "g"), _X], "RD", "l", None, LW),
]

# ---- the r95 attack (review-scratch 828398d, r95-attackr/f1, f2, f5): a counted conferral of a seat written from an
# old past is re-counted against the body's growth the reader holds, as a licence and an edge are (recount_on_growth,
# the one re-count) ---------------------------------------------------------------------------------------------------
_G1L = ST.offer("glo", "A", ("X",), "license", "g", "group", ("g",), head=("g",), counted="duty")   # A alone, from g
_DCC = ST.offer("dcc", "A", "C", "moderate", "g", "group", ("g",), head=("g",), cosigners=("C",), counted="duty",
                policy="duty_confer")                             # A (the lone holder) and C: C a holder, counted
_G5 = ST.found("g", "A", ("A", "B", "C", "D", "E"), {"moderate": ("A", "B", "C")}, cosigners=("B", "C", "D", "E"),
               licence_classes=((M, False),))
_DDE = ST.offer("dde", "A", ("D", "E"), "moderate", "g", "group", ("g",), head=("g",), cosigners=("B", "C", "D", "E"),
                counted="duty", policy="duty_confer")             # A, B and C seat D and E: five holders
_GAB = ST.offer("glo", "A", ("X",), "license", "g", "group", ("g",), head=("g",), cosigners=("B",), counted="duty")
_AF1, _AF3 = dict(AFD1, official="O"), dict(AFD, official="O")    # one officer A; officers A, B, C (official O)
_LSO = lambda signers, policy: ST.offer("lso", signers[0], ("X",), "license", "af", "group", ("af",), head=("af",),
                                        cosigners=tuple(signers[1:]), counted=ST.OFFICER, policy=policy)
_LSA = ST.accept("lsa", "X", "lso")
_LX = glic("l", "af", "X") | {"names": ("lsa",)}
_AOD = ST.offer("aod", "A", ("D",), "member", "af", "group", ("af",), head=("af",), cosigners=("B", "D"),
                counted=ST.OFFICER, role=ST.OFFICER, policy="cosigned_act")   # A and B appoint D officer: four
CASES += [
    ("r95 Q5c A, the lone holder, confers a license seat on X by a counted row from g", [G1, _G1L, GLA, A("e", "RD", "g"),
     _X], "RD", "l", None, OK),
    ("r95 Q5 and A and C's counted conferral of moderate on C beside it, held: A alone is 1 of 2, X holds no seat",
     [G1, _DCC, _G1L, GLA, A("e", "RD", "g"), _X], "RD", "l", None, NA),
    ("r95 Q6 and A's lone conferral on C (accepted) beside it, held: A alone is 1 of 2, X holds no seat",
     [G1, R_DC, R_DCA, _G1L, GLA, A("e", "RD", "g"), _X], "RD", "l", None, NA),
    ("r95 Q8c A and B confer a license seat on X from g: 2 of the 3 holders", [_G5, _GAB, GLA, A("e", "RD", "g"), _X],
     "RD", "l", None, OK),
    ("r95 Q8 and D and E seated beside it by a counted conferral, held: A and B are 2 of 5, X holds no seat",
     [_G5, _DDE, _GAB, GLA, A("e", "RD", "g"), _X], "RD", "l", None, NA),
    ("r95 Q8a and a conferral after the growth, A, B, C and D from dde: 4 of 5, X's seat stands",
     [_G5, _DDE, dict(_GAB, names=("dde",), head=("dde",), cosigners=("B", "C", "D")), GLA, A("e", "RD", "g"), _X],
     "RD", "l", None, OK),
    ("r95 Q6a and A and C's conferral after the lone growth (naming its acceptance): 2 of 2, X's seat stands",
     [G1, R_DC, R_DCA, dict(_G1L, names=("dca",), head=("dc",), cosigners=("C",)), GLA, A("e", "RD", "g"), _X], "RD",
     "l", None, OK),
    ("r95 Q4c one officer: A with O's voice confers a license seat on X under affiliation_member_action",
     [_AF1, _LSO(("A", "O"), "affiliation_member_action"), _LSA, A("e", "RD", "af"), _LX], "RD", "l", None, OK),
    ("r95 Q4 and A's countersigned appointment of B as officer beside it, held: the conferral is re-counted against "
     "two officers, X holds no seat",
     [_AF1, R_AOBO, _LSO(("A", "O"), "affiliation_member_action"), _LSA, A("e", "RD", "af"), _LX], "RD", "l", None, NA),
    ("r95 Q7c officers A, B, C: A and B confer a license seat on X under cosigned_act (2 of 3)",
     [_AF3, _LSO(("A", "B"), "cosigned_act"), _LSA, A("e", "RD", "af"), _LX], "RD", "l", None, OK),
    ("r95 Q7 and A, B and D's appointment of D as officer beside it, held: A and B are 2 of 4, X holds no seat",
     [_AF3, _AOD, _LSO(("A", "B"), "cosigned_act"), _LSA, A("e", "RD", "af"), _LX], "RD", "l", None, NA),
    ("r95 Q7b the officers' own quorum licence, A and B from af, D appointed beside it: 2 of 4 (held before r95)",
     [_AF3, _AOD, A("e", "RD", "af"), glic("l", "af", "A", cosigners=("B",))], "RD", "l", None, NA),
]

# ---- the r97 attack (review-scratch e78aaa5, r97-attackr/g1, g2): the edges of the re-count on growth ---------------
_G6 = ST.found("g", "A", ("A", "B", "C", "D", "E", "F"), {"moderate": ("A", "B", "C")}, cosigners=("B", "C", "D", "E", "F"),
               licence_classes=((M, False),))
_DCD = ST.offer("dcc", "A", "D", "moderate", "g", "group", ("g",), head=("g",), cosigners=("B", "C"), counted="duty",
                policy="duty_confer")                             # A, B and C offer D moderate (D's acceptance to come)
_DCDA = ST.accept("dca", "D", "dcc")
_GLO_DC = ST.offer("glo", "A", ("X",), "license", "g", "group", ("dcc",), head=("dcc",), cosigners=("B",),
                   counted="duty")                                # A and B at dcc: 2 of the 3 seated there
_GLO_G6 = ST.offer("glo", "A", ("X",), "license", "g", "group", ("g",), head=("g",), cosigners=("B",), counted="duty")
_WDA = ST.withdraw("wd", "D", "dca", ("dca", "dcc"))             # D withdraws its acceptance (naming the newest head, H4)
_L1C = ST.withdraw("l1", "C", "g", (), scope="moderate")          # C lays down moderate
_G10 = ST.found("g", "A", tuple("ABCDEFGHIJ"), {"moderate": ("A", "B", "C")}, cosigners=tuple("BCDEFGHIJ"),
                licence_classes=((M, False),))
_DDE2 = ST.offer("dde", "A", ("D", "E"), "moderate", "g", "group", ("g",), head=("g",), cosigners=("B", "D", "E"),
                 counted="duty", policy="duty_confer")            # A and B seat D and E (2 of 3): five holders
_SYB = ST.offer("syb", "A", ("F", "G", "H", "I"), "moderate", "g", "group", ("g",), head=("g",),
                cosigners=("B", "F", "G", "H", "I"), counted="duty", policy="duty_confer")   # A and B again, from g
_RV10 = ST.offer("rv", "A", (), "record", "g", "group", ("g",), head=("g",), cosigners=tuple("BCDEFGHIJ"),
                 consensus_protocol="majority")                   # the members restate the record: a later head than g
_DFF10 = ST.offer("dff", "A", "F", "moderate", "g", "group", ("g",), head=("g",), cosigners=("B", "F"), counted="duty",
                  policy="duty_confer")                           # A and B seat F, at g
_GL_SYB = ST.offer("glo", "A", ("X",), "license", "g", "group", ("dde", "syb"), head=("dde", "syb"),
                   cosigners=("B", "F", "G", "H", "I"), counted="duty")
CASES += [
    ("r97 A0 D offered, never accepting: A and B (2 of the 3 seated at dcc) confer X's license seat",
     [_G6, _DCD, _GLO_DC, GLA, A("e", "RD", "g"), _X], "RD", "l", None, OK),
    ("r97 A1 and D's acceptance naming only dcc, concurrent with glo: an acceptance of an offer in the conferral's own "
     "past is no growth against it (D alone voids nothing)",
     [_G6, _DCD, _GLO_DC, GLA, _DCDA, A("e", "RD", "g"), _X], "RD", "l", None, OK),
    ("r97 A1b and D's acceptance after glo (naming it)",
     [_G6, _DCD, _GLO_DC, GLA, dict(_DCDA, names=("dcc", "glo")), A("e", "RD", "g"), _X], "RD", "l", None, OK),
    ("r97 V0 A and B confer X's license seat from g, nothing beside it", [_G6, _GLO_G6, GLA, A("e", "RD", "g"), _X],
     "RD", "l", None, OK),
    ("r97 V1 D seated beside it and then withdrawing its acceptance, held: the growth no longer seats, 2 of 3 stands",
     [_G6, _DCD, _DCDA, _WDA, _GLO_G6, GLA, A("e", "RD", "g"), _X], "RD", "l", None, OK),
    ("r97 V2 A and C seat D beside it while C lays down moderate, held: holders A, B, D, and A and B are 2 of 3",
     [_G6, dict(_DCD, cosigners=("C", "D")), _L1C, _GLO_G6, GLA, A("e", "RD", "g"), _X], "RD", "l", None, OK),
    # B4/B5, as ruled: rows by the same voices at the SAME heads are one batch, not re-counted against each other. A and
    # B, a majority at g, could seat D to I in one row at g, and a concurrent row at that head is causally the same:
    # "packing" here is a majority's power at that head. A batch at different heads, or by different voices, is
    # re-counted (B6)
    ("r97 B5 A and B seat D and E, and at g again F to I (one batch at g, as ruled), then A, B and F to I confer X's "
     "license seat: 6 of 9",
     [_G10, _DDE2, _SYB, _GL_SYB, GLA, A("e", "RD", "g"), _X], "RD", "l", None, OK),
]

# NOTE (attack-r r98 M3, review-scratch 4de5b1c, r98-attackr/s/h2.py; not exploitable, stated): A and B seat D and E
# at g, and A, B and D seat F at g. Different voices, so each is re-counted against the other. F's seating stands on a
# re-count that reads D's voice (A, B, D of A to E), while dde, the row seating D, fails its own re-count against F's.
# The two re-counts at one head do not read each other's results. A and B are the majority at g either way, so no
# outcome turns on it.

# the same worlds read at the seat (Seats.holders): whether X holds the license seat the counted conferral gives,
# (name, rows, [(key, scope, object, holds)])
# r99 (attack-r, k3): a licence built on a batch row from behind its signers' own later change (syb at g, behind
# A, B and C's c2 at dde): syb is cut for every reader holding c2, and the conferral naming it as a head (glo, heads
# dde and syb) is read over rows that no longer hold syb: it names a head it cannot count at, and X's licence is no
# one's (before the fix the walk raised on the missing row)
_R10L = ST.found("g", "A", tuple("ABCDEFGHIR"), {"moderate": ("A", "B", "C")}, cosigners=tuple("BCDEFGHIR"),
                 licence_classes=((M, False),))
_RDDE = ST.offer("dde", "A", ("D", "E"), "moderate", "g", "group", ("g",), head=("g",), cosigners=("B", "D", "E"),
                 counted="duty", policy="duty_confer")
_RC2 = ST.offer("c2", "A", "A", "slash", "g", "group", ("dde",), head=("dde",), cosigners=("B", "C"), counted="duty",
                policy="duty_confer")
_RSYB = ST.offer("syb", "A", ("F", "G", "H", "I"), "moderate", "g", "group", ("g",), head=("g",),
                 cosigners=("B", "F", "G", "H", "I"), counted="duty", policy="duty_confer")
_GL0 = ST.offer("glo", "A", ("X",), "license", "g", "group", ("dde", "syb"), head=("dde", "syb"),
                cosigners=("B", "F", "G", "H", "I"), counted="duty")
_RC4 = ST.offer("c4", "A", ("Y",), "license", "g", "group", ("dde",), head=("dde",), cosigners=("B", "C"),
                counted="duty")
CASES += [
    ("r99 k3 a licence built on a batch row from behind its signers' later change: glo names syb, cut for every "
     "reader holding c2; the walk reads it at a head it cannot count at, and X's licence is no one's (no crash)",
     [_R10L, _RDDE, _RC2, _RSYB, _GL0, GLA, A("e", "RD", "g"), _X], "RD", "l", None, NA),
]
SEATED_R99 = [
    ("r99 k4 the signers' later row is a LICENSE conferral (c4, A, B and C at dde): their row at g is behind it all the "
     "same, and F to I are not seated", [_R10L, _RDDE, _RC4, _RSYB],
     [("D", "duty", "g", True), ("F", "duty", "g", False), ("I", "duty", "g", False)]),
    ("r99 k3 at the seat: c2 stands (glo, built on syb from behind c2, is no change ahead of c2), syb and glo do not",
     [_R10L, _RDDE, _RC2, _RSYB, _GL0, GLA], [("A", "slash", "g", True), ("F", "duty", "g", False), ("X", "license", "g", False)]),
]
SEATED = SEATED_R99 + [
    ("r97 seat B4 A and B seat D and E, and at g again F to I beside it: one batch at one head (as ruled), all seated",
     [_G10, _DDE2, _SYB], [("E", "duty", "g", True), ("F", "duty", "g", True), ("I", "duty", "g", True)]),
    ("r97 seat B6 the same voices at a LATER head are no batch: A and B seat D and E at rv (after g), and F to I at g "
     "beside it, held: the seating at g is behind dde (its heads older, in dde's past), so it is no growth against dde "
     "and is itself re-counted (behind_act): dde seats D and E, F to I are unseated",
     [_G10, _RV10, dict(_DDE2, names=("rv",), head=("rv",)), _SYB],
     [("E", "duty", "g", True), ("F", "duty", "g", False), ("I", "duty", "g", False)]),
    ("r97 seat B7 and different voices at the same head are no batch: A, B and C seat D and E at g, A and B seat F at g "
     "beside it, held: A, B and C are 3 of 4 against F, A and B 2 of 5 against D and E, so F is unseated",
     [_G10, dict(_DDE2, cosigners=("B", "C", "D", "E")), _DFF10],
     [("E", "duty", "g", True), ("F", "duty", "g", False)]),
    ("r97 seat V2 A and C seat D beside C's lay-down: holders A, B, D", [_G6, dict(_DCD, cosigners=("C", "D")), _L1C],
     [("D", "duty", "g", True), ("C", "duty", "g", False)]),
    ("r95 seat Q5c A alone seats X's license from g", [G1, _G1L, GLA], [("X", "license", "g", True)]),
    ("r95 seat Q5 and the counted growth beside it, held: X holds no seat", [G1, _DCC, _G1L, GLA],
     [("C", "duty", "g", True), ("X", "license", "g", False)]),
    ("r95 seat Q6 and the lone growth beside it, held: X holds no seat", [G1, R_DC, R_DCA, _G1L, GLA],
     [("C", "duty", "g", True), ("X", "license", "g", False)]),
    ("r95 seat Q8 three holders grown to five beside A and B's conferral: X holds no seat", [_G5, _DDE, _GAB, GLA],
     [("E", "duty", "g", True), ("X", "license", "g", False)]),
    ("r95 seat Q4c one officer: A with O's voice seats X's license", [_AF1, _LSO(("A", "O"), "affiliation_member_action"),
     _LSA], [("X", "license", "af", True)]),
    ("r95 seat Q4 and B appointed officer beside it, held: X holds no seat",
     [_AF1, R_AOBO, _LSO(("A", "O"), "affiliation_member_action"), _LSA],
     [("B", ST.OFFICER, "af", True), ("X", "license", "af", False)]),
    ("r95 seat Q7 three officers grown to four beside A and B's conferral: X holds no seat",
     [_AF3, _AOD, _LSO(("A", "B"), "cosigned_act"), _LSA], [("D", ST.OFFICER, "af", True), ("X", "license", "af", False)]),
    ("r95 seat Q7a A, B and D seat X's license after D's appointment (naming it): 3 of 4, X's seat stands",
     [_AF3, _AOD, dict(_LSO(("A", "B", "D"), "cosigned_act"), names=("aod",), head=("aod",)), _LSA],
     [("X", "license", "af", True)]),
]

NOW = {"an edge whose term has ended at the caller's instant (150)": 150,
       "r77 N8 a term-bearing edge read with no caller's instant: not walked (never at the licence's own instant)": None}

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
          "pending_unread", "edge_countersign_unread",
          "judged_at_read", "bears_unread", "refusal_unread", "depth_unread", "depth_absent_refused",
          "withdrawn_unread", "withdraw_by_anyone", "issuer_unread", "chain_unread", "quorum_unread",
          "ends_unread", "cut_unread", "self_seat_ungated", "untimed_term_met", "instant_unread",
          "edge_term_unread", "amendment_as_cut",
          "instant_over_reader", "scope_unread", "termless_edge_walked",
          "growth_held_unread", "lone_batch_unread", "end_scope_keyed", "still_holds_end_past",
          "one_end_at_a_time", "growth_ends_read", "counted_recount_unread", "behind_grows", "growth_ends_unread", "ahead_unread", "stale_line_ahead",
          "end_cuts_counted_row", "own_licence_uncountersigned")


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
        out.add(TR.read_licence(S, reader, lid, supplied=supplied, now=NOW.get(case[0], NOW_AT)))
    return out, kept


def seated_answers(case, every_order=False):
    _name, rows, asks = case
    out = set()
    for o in (itertools.islice(itertools.permutations(rows), ORDER_CAP) if every_order else [rows]):
        Q = ST.Seats(arrive(o))
        out.add(tuple(k in Q.holders(sc, ob) for k, sc, ob, _ in asks))
    return out


def misses(plant=None, every_order=False):
    hit = []
    with planted(plant):
        for c in CASES:
            got, kept = answers(c, every_order)
            if got != {c[5]}:
                hit.append("%s: got %s, expected %s" % (c[0], sorted(got, key=str), c[5]))
            if not kept:
                hit.append("%s: the licence row is not admitted" % c[0])
        for c in SEATED:
            got = seated_answers(c, every_order)
            want = tuple(w for *_, w in c[2])
            if got != {want}:
                hit.append("%s: got %s, expected %s" % (c[0], sorted(got), want))
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
    print("RESULT: %s: %d cases (each in up to %d arrival orders), %d seat cases, %d refusal cases, %d of %d planted "
          "breaks caught" % ("ok" if not problems else "%d problems" % len(problems), len(CASES), ORDER_CAP, len(SEATED),
                             len(REFUSALS), caught,
             len(PLANTS)))
    return 1 if problems else 0


def fixture(with_refs):
    """The cases with the model's answers, for the crate (tests/trust_rows.rs, through tools/kernel_fixtures.py)."""
    out = {"cases": [], "refusals": []}
    for name, rows, reader, lid, supplied, _want in CASES:
        refs = {}
        S = arrive(rows)
        now = NOW.get(name, NOW_AT)
        ok, why = TR.read_licence(S, reader, lid, supplied=supplied, now=now)
        out["cases"].append({"name": name, "rows": with_refs(rows, refs), "refs": refs, "reader": reader,
                             "licence": lid, "now": now, "supplied": {k: sorted(v) for k, v in sorted((supplied or {}).items())},
                             "honoured": ok, "reason": why})
    for name, r, _want in REFUSALS:
        refs = {}
        out["refusals"].append({"name": name, "rows": with_refs([r], refs), "refs": refs, "refusal": TR.refusal(r)})
    return out


if __name__ == "__main__":
    sys.exit(main())
