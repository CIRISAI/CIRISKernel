#!/usr/bin/env python3
"""
check_key_view.py: the key view (CutSpec::key_view), the end rule read at the voices step of every seat count.

A count reads each voice by the end rule (key_end.counts_by): a key's signature on the row it signed (the counted row,
for its signer and each cosigner; a cosign row it names, for that row's signer) counts only where that row is in the
causal past of each of the key's own ends (a self-revocation, the row's own instant before its revoked_after; a
rotation naming the key's record), never because a live row cites it. The key view is read over ONE causal order of
the seat and key lanes, which the caller builds from its store (persist's key records are rows of its own store).
With no key view, every voice counts: only for a caller with no key lane.

    python3 -I check_key_view.py     the cases and planted breaks
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import seat as ST  # noqa: E402
import key_end as KE  # noqa: E402
import check_count_heads as CH  # noqa: E402
import check_election as EL  # noqa: E402
import window as WN  # noqa: E402
import check_agent_removal as AR  # noqa: E402
import check_removal_in_force as RF  # noqa: E402

CK = ST.CK
RULE = CH.RULE
OBJ = CH.OBJ
KEYS = tuple("ABCDEFGZ")


def x_row(signers, at=3, cites=()):
    """A counted admission of Z at aG by `signers` (the first the signer, the rest cosigners), signed at `at`."""
    return ST.offer("x", signers[0], "Z", "member", OBJ, "group", ("aG",) + tuple(cites), head=("aG",),
                    policy="community_invite", cosigners=tuple(signers[1:]) + ("Z",), at=at)


def recs(**ends):
    """A record for every key (0 .. its end, or none), each its own key's."""
    return [KE.rec("k" + k, k, 0, ends.get(k), typ="pseudonym") for k in KEYS]


WRULE = lambda r, P, past: WN.rule(r, P, past)


def halt_rows():
    """A halt (h1) confirmed by h2's answer: the landing `x` of 'confirmed' by h3 counts h1 and h2, two of three."""
    g = ST.offer("g", "h1", ("h1", "h2", "h3"), "holder", "@", "self", cosigners=("h2", "h3"))
    p = WN.opener("p", "h1", "halt_fuse", "g", ("g",))
    return [g, p, WN.answer("c2", "h2", "p", "confirm"), WN.receipt("r", "h3", "p", 0),
            WN.landing("x", "h3", "p", "r", "confirmed", WN.secs("halt_fuse"), ("c2",))]


HKEYS = [KE.rec("k" + k, k, 0, None, typ="pseudonym") for k in ("h1", "h2", "h3")]
ELECTION = [EL.G5, EL.LM] + EL.H5 + [dict(EL.EC, id="x")]         # C seated by three first choices of five
EKEYS = [KE.rec("k" + k, k, 0, None, typ="pseudonym") for k in "ABCDE"]
EROT = [KE.rec("qE", "E2", 1, None, names=("kE",), succ_of="E", at_old=1, typ="pseudonym")]

# (name, rule, seat rows, key rows, key view on?, the voices of x (None: not a seat count's), x concluded)
CASES = [
    ("a cosigned row: C, one cosigner, revoked itself after 2 (naming nothing); x signed at 3: C's voice drops, "
     "A B D E F stay (five of seven, the admission's count: x concludes)", "seat",
     CH.ROOM + [x_row("ABCDEF")], recs() + [KE.revoke("vC", "C", 2)], True, set("ABDEFZ"), True),
    ("the same with five signers (A B C D E): C's voice drops and x is four of seven: concludes nothing", "seat",
     CH.ROOM + [x_row("ABCDE")], recs() + [KE.revoke("vC", "C", 2)], True, set("ABDEZ"), False),
    ("a revocation that names x (C revoked after 9, x signed at 3, in its past): C's voice counts", "seat",
     CH.ROOM + [x_row("ABCDE")], recs() + [KE.revoke("vC", "C", 9, names=("x",))], True, set("ABCDEZ"), True),
    ("a rotated key's late vote: D rotated to D2 at 1, the rotation naming D's record and not x: D's voice drops", "seat",
     CH.ROOM + [x_row("ABCDE")], recs() + [KE.rec("qD", "D2", 1, None, names=("kD",), succ_of="D", at_old=1, typ="pseudonym")],
     True, set("ABCEZ"), False),
    ("an expired key's in-time vote: E's record ends at 4, x signed at 3 under it (no end row): E counts", "seat",
     CH.ROOM + [x_row("ABCDE")], recs(E=4), True, set("ABCDEZ"), True),
    ("the documented default, no key view (only for a caller with no key lane): C revoked late counts", "seat",
     CH.ROOM + [x_row("ABCDE")], recs() + [KE.revoke("vC", "C", 2)], False, set("ABCDEZ"), True),
    ("and with no key view the rotated D counts", "seat", CH.ROOM + [x_row("ABCDE")],
     recs() + [KE.rec("qD", "D2", 1, None, names=("kD",), succ_of="D", at_old=1, typ="pseudonym")], False, set("ABCDEZ"), True),
    ("a cosign row by C naming x (C's own row, signed at 3), C revoked late: that voice drops", "seat",
     CH.ROOM + [CK.row("cC", "cosign", "C", ("aG",), of="x", at=3), x_row("ABDE", cites=("cC",))],
     recs() + [KE.revoke("vC", "C", 2)], True, set("ABDEZ"), False),
    ("and the same cosign row with no key view: C's cosign counts", "seat", CH.ROOM + [CK.row("cC", "cosign", "C", ("aG",), of="x", at=3),
                                                                         x_row("ABDE", cites=("cC",))],
     recs() + [KE.revoke("vC", "C", 2)], False, set("ABCDEZ"), True),
    ("a revoked key's late window answer: h2 revoked itself (naming nothing) and its confirm c2 drops; the landing of "
     "'confirmed' (h1 and h2, two of three) is h1 alone: concludes nothing", "window", halt_rows(),
     HKEYS + [KE.revoke("v2", "h2", 0)], True, None, False),
    ("and with no key view (the documented default) the late confirm counts: the landing concludes", "window", halt_rows(),
     HKEYS + [KE.revoke("v2", "h2", 0)], False, None, True),
    ("a rotated key's late ballot: E rotated to E2, the rotation not naming E's ballot: it drops, C and B tie two to two, "
     "and C's seating concludes nothing", "seat", ELECTION, EKEYS + EROT, True, None, False),
    ("and with no key view the ballot counts: C seated", "seat", ELECTION, EKEYS + EROT, False, None, True),
]


# r86 (review-51b): the lift's objections, a lone removal's single-key receipts, and a lone act, each by the end rule.
# (name, seat rows, key rows, key view on?, probe: the row whose conclusion is read (or None), the seat asked,
#  expected (concluded, stands))
LREC = [KE.rec("k" + k, k, 0, None, typ="pseudonym") for k in ("m1", "m2", "MOD", "AG", "p1", "p2", "p3")]
LIFT = AR.A + [AR.XA, AR.O1, AR.O2, AR.RSA]
R2 = RF.receipt("r2", "p2", "x")
LONE = [
    ("K2e: a lift objection by a key revoked late: m2's revocation holds the room up to lm, not its objection o2: o2 "
     "drops, the re-seating rs concludes nothing and AG stays removed", LIFT,
     LREC + [KE.revoke("v2", "m2", 0, names=("lm",))], True, "rs", (False, False)),
    ("K2f (control): m2's revocation holds o2: the re-seating concludes", LIFT,
     LREC + [KE.revoke("v2", "m2", 0, names=("o2",))], True, "rs", (True, True)),
    ("and K2e with no key view: o2 counts, the re-seating concludes", LIFT,
     LREC + [KE.revoke("v2", "m2", 0, names=("lm",))], False, "rs", (True, True)),
    ("K3c: a single key's receipt of a lone removal by a key revoked late: p2's revocation holds xm (its withdrawal of "
     "p1's moderate) and not its receipt r2: r2 drops, nothing keeps x in force once p1's moderate ends, AG is back",
     RF.W + [RF.X, R2, RF.UND], LREC + [KE.revoke("v2", "p2", 0, names=("xm",))], True, None, (None, True)),
    ("and K3c with no key view: r2 keeps x in force", RF.W + [RF.X, R2, RF.UND],
     LREC + [KE.revoke("v2", "p2", 0, names=("xm",))], False, None, (None, False)),
    ("K3e: a lone act by a revoked key: p1's revocation holds ag, not its lone removal x: x does not stand, AG stays",
     RF.W + [RF.X], LREC + [KE.revoke("v1", "p1", 0, names=("ag",))], True, "x", (False, True)),
    ("and K3e with no key view: x stands, AG removed", RF.W + [RF.X], LREC + [KE.revoke("v1", "p1", 0, names=("ag",))],
     False, "x", (True, False)),
]


# R1 and R2 (the Constitution's ruling: a key end is a cut). Two passes: the counts final by acknowledgement are read
# over the rows as they conclude with no key view (a final act is not reopened by a later cut); then the reader's
# conclusion through the key view with the reader's line and those counts.
def rack(i, k, names=("x",)):
    """A member's clean receipt of x (an `ack` naming x, `of` x): its own row, and so on its line."""
    return CK.row(i, "ack", k, tuple(names), of="x")


X5 = x_row("ABCDE")                                   # needs five of seven (community_invite)
REC3 = [rack("rF", "F"), rack("rG", "G"), rack("rA", "A")]   # n - t + 1 = 7 - 5 + 1 = 3 receipts: final
QC0 = KE.rec("qC", "C2", 1, None, names=("kC",), succ_of="C", at_old=1, typ="pseudonym")   # holds no old rows
QCX = KE.rec("qC", "C2", 4, None, names=("kC", "x"), succ_of="C", at_old=4, typ="pseudonym")  # holds x
X0 = x_row("ABCDE", at=0)
XS = x_row("ABCDE", at=3)
XL = x_row("ABCDE", at=3, cites=("vC",))              # signed at 3, its past holding C's revocation: a late vote
VC2 = KE.revoke("vC", "C", 2, names=("kC",))
KT = KE.rec("kT", "T", 0, None, typ="pseudonym")
QT0 = KE.rec("qT", "T", 1, None, names=("kC",), succ_of="C", at_old=1, typ="pseudonym")
QDX = KE.rec("qD", "D2", 1, None, names=("kD", "x"), succ_of="D", at_old=1, typ="pseudonym")
Q2H = KE.rec("q2", "C2", 4, None, names=("kC", "x"), succ_of="C", at_old=4, typ="pseudonym")
# the person's self roster: P's devices P1, P2 and C (modelled as a group of the person's keys); an end of C is the
# roster's own counted removal of C, carrying `rend_of` and its `ra`
PROSTER = [ST.found("P", "P1", ("P1", "P2", "C"), {"moderate": ("P1",)}, cosigners=("P2", "C"))]


def REND(i, signers, ra=2, names=()):
    return ST.unseat(i, signers[0], "C", "member", "P", "group", ("P",) + tuple(names), head=("P",),
                     policy="community_remove", cosigners=tuple(signers[1:]), rend_of="C", ra=ra)


CUT = [
    # (name, rule, seat rows, key rows, reader, probe row, seat asked or None, expected)
    ("the thief's wipe naming nothing (C's stolen key revokes itself, holding no row): for a reader with no line, "
     "x concludes nothing", "seat", CH.ROOM + [X5, rack("rF", "F")], recs() + [KE.revoke("vC", "C", 0)], None, "x", None, False),
    ("and for F, whose receipt took x up before it held the wipe: x concludes (settled on F's line)", "seat",
     CH.ROOM + [X5, rack("rF", "F")], recs() + [KE.revoke("vC", "C", 0)], "F", "x", None, True),
    ("and for G, which never took x up: x concludes nothing", "seat", CH.ROOM + [X5, rack("rF", "F")],
     recs() + [KE.revoke("vC", "C", 0)], "G", "x", None, False),
    ("and with x final by acknowledgement (three of seven receipts): x stands for everyone, a reader with no line too",
     "seat", CH.ROOM + [X5] + REC3, recs() + [KE.revoke("vC", "C", 0)], None, "x", None, True),
    ("an honest rotation from a device without the old rows (C to C2, naming only C's record): for a reader with no "
     "line, the in-time vote is cut (the caller duty: name the key's last rows)", "seat", CH.ROOM + [X5, rack("rF", "F")],
     recs() + [QC0], None, "x", None, False),
    ("and it holds for F, which took x up: x concludes", "seat", CH.ROOM + [X5, rack("rF", "F")], recs() + [QC0], "F",
     "x", None, True),
    ("and with x final, it holds for everyone", "seat", CH.ROOM + [X5] + REC3, recs() + [QC0], None, "x", None, True),
    ("the owner ends a stolen key after the thief voted on x (C's revocation holds C's record, not x): at F, which "
     "took x up first, the vote stands: x concludes", "seat", CH.ROOM + [X5, rack("rF", "F")],
     recs() + [KE.revoke("vC", "C", 2, names=("kC",))], "F", "x", None, True),
    ("and at G, which held the end first (its receipt names the revocation and x), the vote is cut: x concludes "
     "nothing", "seat", CH.ROOM + recs() + [X5, rack("rF", "F"), KE.revoke("vC", "C", 2, names=("kC",)),
                                            rack("rG", "G", ("x", "vC"))], [], "G", "x", None, False),
    ("and with x final (clean receipts by F, A and B; G's, holding the end, is not clean), it stands for both", "seat",
     CH.ROOM + recs() + [X5, rack("rF", "F"), rack("rA", "A"), rack("rB", "B"), KE.revoke("vC", "C", 2, names=("kC",)),
                         rack("rG", "G", ("x", "vC"))], [], "G", "x", None, True),
    ("a revocation by a rotated-away key is no end: C rotated to C2 holding x, then C's key (stolen) revokes itself "
     "after 0, the rotation in its past: x concludes", "seat", CH.ROOM + [X5],
     recs() + [QCX, KE.revoke("vC", "C", 0, names=("x",))], None, "x", None, True),
    ("the person's self roster ends a retired key: P's roster (P1, P2 and C, the person's devices) removes C from 2 on "
     "by its own count (P1 and P2), holding C's rotation to C2 and x: x, signed at 3, is cut: concludes nothing", "seat",
     CH.ROOM + [X5] + PROSTER + [REND("eC", ("P1", "P2"), names=("x",))], recs() + [QCX], None, "x", None, False),
    ("and a roster end the roster's count does not carry (C2, the successor, alone) is no end: x concludes", "seat",
     CH.ROOM + [X5] + PROSTER + [REND("eC", ("C2",), names=("x",))], recs() + [QCX], None, "x", None, True),
    # r89 (review-51b), S1: finality reads clean receipts and protects only voices valid when cast
    ("M1b: C revoked after 2 (holding C's record), then x signed with the stolen C at 3 holding the revocation, with "
     "receipts by F, G and the stolen C: C's own receipt is not clean, x is not final, and the late vote is cut: x "
     "concludes nothing", "seat", CH.ROOM + recs() + [VC2, XL, rack("rF", "F"), rack("rG", "G"), rack("rC", "C")], [],
     None, "x", None, False),
    ("M1d: x signed with C at 3 concurrent with C's revocation (not holding it), receipted by F, G and the stolen C: "
     "C's own receipt is not clean (C's key is cut at it), two clean of three needed: not final, and the vote outside "
     "the revocation's past is cut: x concludes nothing", "seat",
     CH.ROOM + recs() + [VC2, X5, rack("rF", "F"), rack("rG", "G"), rack("rC", "C")], [], None, "x", None, False),
    ("M1c: the same with receipts by F, G and A, each holding the revocation: none is clean, x is not final: concludes "
     "nothing", "seat", CH.ROOM + recs() + [VC2, XL, rack("rF", "F", ("x", "vC")), rack("rG", "G", ("x", "vC")),
                                            rack("rA", "A", ("x", "vC"))], [], None, "x", None, False),
    # S2: a revocation by k is no end where any concluded rotation of k is held
    ("K1g: D rotated to D2 holding x, then whoever holds the retired D revokes it, naming nothing (the rotation not in "
     "its past): no end, x concludes", "seat", CH.ROOM + [X0], recs() + [QDX, KE.revoke("vD", "D", 0)], None, "x", None, True),
    # S3: the thief rotates an unrotated key; a fork of a key; roster ends by the roster's count
    ("M2a EDGE (the stated residual, a person with one key): the thief rotates C (never rotated) to T, naming only C's "
     "record: an end of C like a revocation: the owner's vote x at 0 is cut for a reader with no line", "seat",
     CH.ROOM + [X0], recs() + [KT, QT0], None, "x", None, False),
    ("M2b: the owner then revokes C holding x and the thief's rotation: no end (a rotation of C is held), and x stays "
     "cut by the thief's rotation", "seat", CH.ROOM + [X0], recs() + [KT, QT0, KE.revoke("vO", "C", 0, names=("qT", "x"))],
     None, "x", None, False),
    ("M2c: or the owner rotates C to C2 holding x: two rotations, a FORK of C: both are ends, x is outside the "
     "thief's: cut", "seat", CH.ROOM + [X0], recs() + [KT, QT0, KE.rec("q2", "C2", 2, None, names=("kC", "x", "qT"),
                                                                      succ_of="C", at_old=2, typ="pseudonym")],
     None, "x", None, False),
    ("and M2c for F, which took x up: x concludes (limb b protects it across the fork)", "seat",
     CH.ROOM + [X0, rack("rF", "F")], recs() + [KT, QT0, KE.rec("q2", "C2", 2, None, names=("kC", "x", "qT"), succ_of="C",
                                                                at_old=2, typ="pseudonym")], "F", "x", None, True),
    ("M3a: the owner rotates C to C2 at 4 holding the thief's x (at 3); P's roster ends C from 2 on by its count: x is "
     "cut", "seat", CH.ROOM + [XS] + PROSTER + [REND("eC", ("P1", "P2"), names=("x",))], recs() + [Q2H], None, "x", None,
     False),
    ("M3b: the thief also rotates old C to T (a fork): the roster end does not hang on a successor and still ends C: "
     "x is cut", "seat", CH.ROOM + [XS] + PROSTER + [REND("eC", ("P1", "P2"), names=("x",))],
     recs() + [KT, Q2H, KE.rec("qT", "T", 4, None, names=("kC",), succ_of="C", at_old=4, typ="pseudonym")], None, "x", None,
     False),
    ("M3c: the thief's rotation to T holds x: still a fork, and the roster end still ends C from 2 on: x is cut", "seat",
     CH.ROOM + [XS] + PROSTER + [REND("eC", ("P1", "P2"), names=("x",))],
     recs() + [KT, Q2H, KE.rec("qT", "T", 4, None, names=("kC", "x"), succ_of="C", at_old=4, typ="pseudonym")], None, "x",
     None, False),
    ("M3d: T (the thief, no device of P's roster) alone signs a roster end of C from 0: the roster's count is not met, "
     "no end; the owner's x at 0, held by T's rotation, concludes", "seat",
     CH.ROOM + [X0] + PROSTER + [REND("eT", ("T",), ra=0, names=("x",))],
     recs() + [KT, KE.rec("qT", "T", 1, None, names=("kC", "x"), succ_of="C", at_old=1, typ="pseudonym")], None, "x", None,
     True),
    ("k3.py's K3c as written (p2's revocation holds nothing): for a reader with no line, xm (p2's withdrawal of p1's "
     "moderate) and r2 are both cut, and x stays in force: AG removed", "window", RF.W + [RF.X, R2, RF.UND],
     LREC + [KE.revoke("v2", "p2", 0)], None, None, ("AG", "agent", "g"), False),
    ("and for p3, which cosigned xm (taken up): xm stands and r2 (not on p3's line) is cut: x falls out of force, AG "
     "is back", "window", RF.W + [RF.X, R2, RF.UND], LREC + [KE.revoke("v2", "p2", 0)], "p3", None, ("AG", "agent", "g"), True),
]


# (c) protects only a voice valid when cast, whatever final set a caller gives: read directly through counts_by
DIRECT = [
    ("a voice whose own end is in the final count's past never stands, x given as final", CH.ROOM + recs() + [VC2, XL],
     "x", "C", {"x"}, False),
    ("and one whose end is not in its past stands when x is final", CH.ROOM + recs() + [VC2, X5], "x", "C", {"x"}, True),
]


def plain(seat_rows, key_rows, rule):
    """The first pass, with no key view: the roster acts concluded under the roster's own count rule, and the counts
    final by acknowledgement over clean receipts (the key lane read for them by the plain end rule)."""
    for m in ("_READER_MEMO", "_VOID_MEMO", "_EMEMO", "_SEATS_OF"): getattr(ST, m).clear()
    S1 = CK.concluded(CK.kept(list(seat_rows)), rule)
    roster = frozenset(r["id"] for r in S1.Cs if r.get("rend_of") is not None)
    KS = KE.state(list(seat_rows) + list(key_rows))
    final = frozenset(i for i in S1.by if ST.final_by_ack(S1, i, KS, roster))
    return KS, roster, final


def cut_answer(rule, seat_rows, key_rows, reader, probe, seat):
    R0 = WRULE if rule == "window" else RULE
    KS, roster, final = plain(seat_rows, key_rows, R0)
    ST.KEY_VIEW.append(lambda rid, k: KE.counts_by(KS, rid, k, reader, final, roster))
    try:
        for m in ("_READER_MEMO", "_VOID_MEMO", "_EMEMO", "_SEATS_OF"): getattr(ST, m).clear()
        S = CK.concluded(CK.kept(list(seat_rows)), R0)
        if seat: return ST.Seats(S).stands(*seat), sorted(final)
        return bool(S.C.get(probe)), sorted(final)
    finally:
        ST.KEY_VIEW.pop()


def finals(seat_rows, rule, key_rows=()):
    """The counts final by acknowledgement, over the rows as they conclude with no key view."""
    return plain(seat_rows, key_rows, rule)[2]


def lone_answer(seat_rows, key_rows, view, probe):
    KS = KE.state(list(seat_rows) + list(key_rows))
    fin = finals(seat_rows, WRULE, key_rows)
    ST.KEY_VIEW.append((lambda rid, k: KE.counts_by(KS, rid, k, None, fin)) if view else None)
    try:
        for m in ("_READER_MEMO", "_VOID_MEMO", "_EMEMO", "_SEATS_OF"): getattr(ST, m).clear()
        S = CK.concluded(CK.kept(list(seat_rows)), WRULE)
        return (bool(S.C.get(probe)) if probe else None), ST.Seats(S).stands("AG", "agent", "g")
    finally:
        ST.KEY_VIEW.pop()


def answer(rule, seat_rows, key_rows, view):
    KS = KE.state(list(seat_rows) + list(key_rows))
    fin = finals(seat_rows, WRULE if rule == "window" else RULE, key_rows)
    ST.KEY_VIEW.append((lambda rid, k: KE.counts_by(KS, rid, k, None, fin)) if view else None)
    try:
        ST._READER_MEMO.clear(); ST._VOID_MEMO.clear()
        S = CK.concluded(CK.kept(list(seat_rows)), WRULE if rule == "window" else RULE)
        P = [q for q in S.Cs if q["id"] in S.anc["x"]]
        return set(ST.voices(S.by["x"], P)), bool(S.C.get("x"))
    finally:
        ST.KEY_VIEW.pop()


PLANTS = (("key_view_unread", ST.MUT), ("cosigner_key_unchecked", ST.MUT), ("window_key_view_unread", ST.MUT),
          ("ballot_key_view_unread", ST.MUT), ("lift_key_view_unread", ST.MUT), ("receipt_key_view_unread", ST.MUT),
          ("lone_key_view_unread", ST.MUT), ("retired_key_revokes", KE.MUT), ("roster_end_unread", KE.MUT),
          ("taken_up_unread", KE.MUT), ("final_count_unread", KE.MUT), ("final_protects_late", KE.MUT),
          ("receipt_unclean_counts", ST.MUT))
SIGNED = ("x", "cC", "c2", "be", "o2", "r2")                                   # the rows whose per-key answers the fixture carries


def run():
    bad = []
    for name, rule, sr, kr, view, v, c in CASES:
        gv, gc = answer(rule, sr, kr, view)
        if gc != c or (v is not None and gv != v): bad.append("%s: got %s" % (name, (gv, gc)))
    for name, sr, kr, view, probe, want in LONE:
        got = lone_answer(sr, kr, view, probe)
        if got != want: bad.append("%s: got %s" % (name, got))
    for name, rule, sr, kr, reader, probe, seat, want in CUT:
        got = cut_answer(rule, sr, kr, reader, probe, seat)[0]
        if got != want: bad.append("%s: got %s" % (name, got))
    for name, rows, rid, k, fin, want in DIRECT:
        got = KE.counts_by(KE.state(rows), rid, k, None, frozenset(fin))
        if got != want: bad.append("%s: got %s" % (name, got))
    return bad


def fixture():
    """For the crate (tests/key_view.rs) and for persist to replay: each case's rows, the per-(row, key) answers of
    key_end.counts_by, and the voices and conclusion of x with and without the key view."""
    out = []
    for name, rule, sr, kr, view, v, c in CASES:
        fin = sorted(finals(sr, WRULE if rule == "window" else RULE, kr))
        KS = KE.state(list(sr) + list(kr))
        keys = sorted({q["signer"] for q in sr} | {k for q in sr for k in q.get("cosigners", ())})
        per = [[rid, k, KE.counts_by(KS, rid, k)] for rid in SIGNED if rid in KS.by for k in keys]
        out.append({"name": name, "rule": rule, "seat": [r["id"] for r in sr], "rows": list(sr) + list(kr), "view": view,
                    "counts": per, "voices": sorted(v) if v is not None else None, "concluded": c, "final": fin})
    for name, sr, kr, view, probe, (c, st) in LONE:
        fin = sorted(finals(sr, WRULE, kr))
        KS = KE.state(list(sr) + list(kr))
        keys = sorted({q["signer"] for q in sr} | {k for q in sr for k in q.get("cosigners", ())})
        per = [[rid, k, KE.counts_by(KS, rid, k)] for rid in SIGNED if rid in KS.by for k in keys]
        out.append({"name": name, "rule": "window", "seat": [r["id"] for r in sr], "rows": list(sr) + list(kr),
                    "view": view, "counts": per, "voices": None, "probe": probe, "concluded": c, "final": fin,
                    "stands": ["AG", "agent", "g", st]})
    for name, rule, sr, kr, reader, probe, seat, want in CUT:
        got, final = cut_answer(rule, sr, kr, reader, probe, seat)
        e = {"name": name, "rule": rule, "seat": [r["id"] for r in sr], "rows": list(sr) + list(kr), "view": True,
             "counts": [], "voices": None, "reader": reader, "final": final, "probe": probe}
        if seat: e["stands"] = list(seat) + [want]
        else: e["concluded"] = want
        out.append(e)
    return out


def main():
    bad = run()
    for b in bad: print(b)
    missed = []
    for p, mut in PLANTS:
        mut.add(p)
        try:
            hit = run()
        finally:
            mut.discard(p)
        print("  plant %-24s %s" % (p, "caught by: " + hit[0][:90] if hit else "NOT CAUGHT"))
        if not hit: missed.append(p)
    ok = not bad and not missed
    print("RESULT: %s: %d cases, %d of %d planted breaks caught" % ("ok" if ok else "%d problems" % (len(bad) + len(missed)),
                                                                   len(CASES) + len(LONE) + len(CUT) + len(DIRECT), len(PLANTS) - len(missed), len(PLANTS)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
