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
import check_key_person as KP  # noqa: E402

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
    p = WN.opener("p", "h1", "holders@count", "g", ("g",))
    return [g, p, WN.answer("c2", "h2", "p", "confirm"), WN.receipt("r", "h3", "p", 0),
            WN.landing("x", "h3", "p", "r", "confirmed", WN.secs("holders@count"), ("c2",))]


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
# the person's self roster SP (the key-person lane's reading): P1 its genesis key, P2 and C added by its own count
SP = [KP.found("SP", "P1"), KP.add("aP2", "SP", "P2", ("P1",), ("SP",)), KP.add("aC", "SP", "C", ("P1", "P2"), ("aP2",))]


def VOID(i, signers, rot, key="T", heads=("aC",)):
    """The self roster's void of a rotation (T3, the carrier confirmed): its counted eviction of the rotated-to key,
    citing the rotation (refs.also.cites)."""
    e = KP.evict(i, "SP", key, tuple(signers), heads)
    return dict(e, names=tuple(e["names"]) + (rot,))


Q2X = KE.rec("q2", "C2", 2, None, names=("kC", "x"), succ_of="C", at_old=2, typ="pseudonym")   # the owner's, holding x
# r92 worlds
TKEYS = [KE.rec("k" + k, k, 0, None, typ="pseudonym") for k in ("T1", "T2", "T3")]
NQ_ROOM = ST.found("Q", "T1", ("T1", "T2", "T3"), {"moderate": ("T1",)}, cosigners=("T2", "T3"))
NQ = ST.unseat("nq", "T1", "T3", "member", "Q", "group", ("Q",), head=("Q",), policy="community_remove",
               cosigners=("T2",), rend_of="C", ra=0)
NG = ST.unseat("ng", "A", "F", "member", "g", "group", ("aG",), head=("aG",), policy="community_remove",
               cosigners=("B", "D", "E", "G"), rend_of="C", ra=0)
NV = dict(ST.unseat("nv", "T1", "C2", "member", "Q", "group", ("Q",), head=("Q",), policy="community_remove",
                    cosigners=("T2",)), names=("Q", "qC"))
HROOM = [ST.found("h", "A", ("A", "B", "D", "P1"), {"moderate": ("A",)}, cosigners=("B", "D", "P1"))]
EVC = KP.evict("eC", "SP", "C", ("P1", "P2"), ("aC",))


def XP(extra):
    """An admission of Z to h by A, B and P1's device C, its past holding P's self-roster rows."""
    return ST.offer("xp", "A", "Z", "member", "h", "group", ("h",) + tuple(extra), head=("h",), policy="community_invite",
                    cosigners=("B", "C", "Z"), at=3)


CC = CK.row("cC", "cosign", "C", ("aG",), of="x", at=3)
XCC = x_row("ABDE", at=3, cites=("cC",))
RXV = [rack("rF", "F", ("x", "vC")), rack("rG", "G", ("x", "vC")), rack("rA", "A", ("x", "vC"))]

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
     recs() + [QCX, KE.revoke("vC", "C", 0, names=("x", "qC"))], None, "x", None, True),
    ("and one concurrent with the rotation (naming only x) is no end either while the rotation stands (r114, ruled "
     "(1)): x concludes", "seat", CH.ROOM + [X5],
     recs() + [QCX, KE.revoke("vC", "C", 0, names=("x",))], None, "x", None, True),
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
     "its past): no end while the rotation stands (r114, ruled (1)), x concludes", "seat", CH.ROOM + [X0],
     recs() + [QDX, KE.revoke("vD", "D", 0)], None, "x", None, True),
    ("K1g: and the same revocation naming the rotation is a retired key's: no end, x concludes", "seat", CH.ROOM + [X0],
     recs() + [QDX, KE.revoke("vD", "D", 0, names=("qD",))], None, "x", None, True),
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
    # r92 T3: the self roster's count settles a rotation (voids it); a rotation it does not void stands
    ("N2a: a person's device C (P's self roster: P1, P2, C), rotated by the thief to T naming only C's record: an end "
     "of C: x (C's vote at 0) is cut for a reader with no line", "seat", CH.ROOM + [X0] + SP + recs() + [KT, QT0], [],
     None, "x", None, False),
    ("N2b: P's roster (P1 and P2) evicts T citing the thief's rotation: the rotation is VOIDED, no end, and x is restored "
     "for a reader with no line", "seat", CH.ROOM + [X0] + SP + recs() + [KT, QT0, VOID("vT", ("P1", "P2"), "qT")], [],
     None, "x", None, True),
    ("an honest rotation the roster does not void stands: C to C2 naming only C's record, an end: x is cut", "seat",
     CH.ROOM + [X0] + SP + recs() + [QC0], [], None, "x", None, False),
    ("a fork (the thief's qT and the owner's q2 holding x): the roster voids qT, and q2 stands: x, in q2's past, "
     "concludes", "seat", CH.ROOM + [X0] + SP + recs() + [KT, QT0, Q2X, VOID("vT", ("P1", "P2"), "qT")], [], None, "x",
     None, True),
    ("edge (2): the old key it claims to succeed is no voice of the void: P1 and the stolen C sign it; C is the "
     "subject, so P1 alone does not carry the roster's count: not voided, x stays cut", "seat",
     CH.ROOM + [X0] + SP + recs() + [KT, QT0, VOID("vT", ("P1", "C"), "qT")], [], None, "x", None, False),
    ("the residual: a one-key roster (C alone) cannot void: the stolen C's own void is no voice of it: x stays cut",
     "seat", CH.ROOM + [X0, KP.found("S1", "C")] + recs() + [KT, QT0, dict(KP.evict("vT", "S1", "T", ("C",), ("S1",)),
                                                                          names=("S1", "qT"))], [], None, "x", None, False),
    # r92 T1 (with G33): an eviction ends a key as the person's, never its liveness, and only k's own self roster's
    ("N1b: a counted removal in a room the attacker owns (Q: T1, T2, T3), marked as an end of C: no end of C's "
     "liveness: x concludes", "seat", CH.ROOM + [X0, NQ_ROOM, NQ], recs() + TKEYS, None, "x", None, True),
    ("N1c: the same through an unrelated removal in the room itself (F removed by five), marked as an end of C: x "
     "concludes", "seat", CH.ROOM + [X0, NG], recs(), None, "x", None, True),
    ("N1d: a void from a room that is not the person's self roster (Q evicts C2 citing the owner's rotation) voids "
     "nothing: the owner's rotation C to C2 (naming only C's record) still cuts the thief's x at 3", "seat",
     CH.ROOM + [XS, NQ_ROOM] + recs() + TKEYS + [QC0, NV], [], None, "x", None, False),
    ("G33: an evicted device's later vote is no voice for its person: the room h seats A, B, D and the person P1; x2 by "
     "A, B and P1's device C concludes (three of four); with P's roster's eviction of C in its past, C speaks for no "
     "member: x2 concludes nothing", "seat", SP + HROOM + [XP(("aC",))], recs(), None, "xp", None, True),
    ("and with the eviction in its past", "seat", SP + [EVC] + HROOM + [XP(("eC",))], recs(), None, "xp", None, False),
    # r92 T2: clean reads every voice of the count: the signers of named cosign rows too
    ("N3a: C's late cosign row of x (at 3, outside C's revocation's past), no receipts: C's voice cut, x (A B D E and "
     "C) concludes nothing", "seat", CH.ROOM + recs() + [VC2, CC, XCC], [], None, "x", None, False),
    ("N3b: with receipts by F, G and A each holding the revocation: C is a voice of x through its cosign row, so none is "
     "clean: not final, x concludes nothing", "seat", CH.ROOM + recs() + [VC2, CC, XCC] + RXV, [], None, "x", None, False),
    ("N3c (control): C a signer of x, the same receipts: not final, x concludes nothing", "seat",
     CH.ROOM + recs() + [VC2, X5] + RXV, [], None, "x", None, False),
    ("the pin: a receipt holding a withdrawal of the act is not clean: F, G and A receipt x, A's holding B's withdrawal "
     "of x: two clean of three, x is not final (the final set the fixture carries)", "seat",
     CH.ROOM + [X5, rack("rF", "F"), rack("rG", "G"), ST.withdraw("wX", "B", "x", ("x",)), rack("rA", "A", ("x", "wX"))],
     recs(), None, "x", None, True),
    ("k3.py's K3c as written (p2's revocation holds nothing): for a reader with no line, xm (p2's withdrawal of p1's "
     "moderate) and r2 are both cut, and x stays in force: AG removed", "window", RF.W + [RF.X, R2, RF.UND],
     LREC + [KE.revoke("v2", "p2", 0)], None, None, ("AG", "agent", "g"), False),
    ("and for p3, which only cosigned xm (STRICT own_row, review-48 R2s: a cosignature listed on another's row is no "
     "row of p3's line): p3 has no line, xm and r2 are cut as for a fresh reader, and x stays in force",
     "window", RF.W + [RF.X, R2, RF.UND], LREC + [KE.revoke("v2", "p2", 0)], "p3", None, ("AG", "agent", "g"), False),
]


# (c) protects only a voice valid when cast, whatever final set a caller gives: read directly through counts_by
DIRECT = [
    ("a voice whose own end is in the final count's past never stands, x given as final", CH.ROOM + recs() + [VC2, XL],
     "x", "C", {"x"}, False),
    ("and one whose end is not in its past stands when x is final", CH.ROOM + recs() + [VC2, X5], "x", "C", {"x"}, True),
]


# reader-level answers of counts_by after the two passes (roster acts, finality): (name, seat rows, key rows, row, key,
# reader, expected)
TAT = KE.att("aT", "T", 3, "kT", about="X")                    # the rotated-to key T's own row
KREV = lambda i, k, ra, names: CK.row(i, "revoke", k, tuple(names), key=k, ra=ra)   # a key's own revocation, naming rows
KK = [KE.rec("kN", "N", 0, None, typ="pseudonym"), KE.att("aN", "N", 2, "kN"), KREV("rvN", "N", 3, ("kN",)),
      KE.att("nt", "N", 2, "kN", names=("aN",))]                                  # K1: a thief's row and its note as N
KH = [KE.rec("kT", "T", 0, None, typ="pseudonym"), KE.rec("kF", "F", 0, None, typ="pseudonym"),
      KE.att("aT", "T", 2, "kT"), KREV("rvT", "T", 3, ("kT",)), KE.att("rF", "F", 2, "kF", names=("aT",)),
      KREV("rvF", "F", 5, ("rF",))]                                              # an honest note, its key ended later
KR2 = [KE.rec("kT", "T", 0, None, typ="pseudonym"), KE.att("aT", "T", 2, "kT"), KREV("rvT", "T", 3, ("kT",)),
       CK.row("nx", "note", "X", ("aT",), cosigners=("F",))]                   # R2: X's note claims F as a cosigner
KUN = [KE.rec("kT", "T", 0, None, typ="pseudonym"), KE.att("aT", "T", 2, "kT"), KREV("rvT", "T", 3, ("kT",)),
       KE.att("rF", "F", 2, "kT", names=("aT",))]                              # F's own row, concluding nothing
KCO = [KE.rec("kT", "T", 0, None, typ="pseudonym"), KE.att("aT", "T", 2, "kT"), KREV("rvT", "T", 3, ("kT",)),
       ST.cosign("cF", "F", "x"), ST.offer("x", "Z", ("Z",), "member", "@", "self", ("cF", "aT"))]   # F a voice of x
KRG = lambda names: [KE.rec("kT", "T", 0, None, typ="pseudonym"), KE.att("aT", "T", 2, "kT"),
                     KREV("rvT", "T", 3, ("kT",)), CK.row("rF", "note", "F", ("aT",)),
                     ST.unseat("uF", "F", "F", "registered", "F", "self", names)]    # F's own seat-lane revocation
KUR = [KE.rec("kN", "N", 0, None, typ="pseudonym"), KE.att("a1", "N", 1, "kN"),
       ST.unseat("ur", "N", "N", "registered", "N", "self", ("a1",)), KE.att("gt", "N", 2, "kN")]   # K1r
# r110 RK0-RK2 (review-48): a RETIRED key K (rotated to K2, the rotation naming K's attestation a1). Neither of its
# revocations is an end: a thief of the retired key cuts nothing the rotation kept, by either lane
RKR = [KE.rec("r0", "K", 0, 100), KE.att("a1", "K", 3, "r0"),
       KE.rec("rot", "K2", 0, 100, names=("r0", "a1"), succ_of="K", at_old=4)]
# r114, ruled (1): a rotation and a revocation of C, concurrent, in a person with the self roster SP. C's row xr is in
# the rotation qF's past (qF names it), not in the revocation rvC's
QF = KE.rec("qT", "T", 1, None, names=("kC", "xr"), succ_of="C", at_old=1, typ="pseudonym")
FK = CH.ROOM + SP + recs() + [KT, KE.att("xr", "C", 0, "kC"), QF, KREV("rvC", "C", 2, ("kC",))]
FK_AFTER = CH.ROOM + SP + recs() + [KT, KE.att("xr", "C", 0, "kC"), QF, KREV("rvC", "C", 2, ("kC", "qT"))]
FK_CASES = [
    ("r114 (a): an honest rotation and a concurrent revocation by a holder of the old key: the rotation stands, the "
     "revocation is no end, and the history the rotation kept counts (xr)", FK, [], "xr", "C", None, True),
    ("r114 (b): the owner's revocation and a concurrent rotation by another holder: the roster voids the rotation "
     "(its eviction of T citing qT), and the revocation is then the key's end: xr counts nothing",
     FK + [VOID("vT", ("P1", "P2"), "qT")], [], "xr", "C", None, False),
    ("r114: a revocation with the rotation in its past is no end (the key was retired first): xr counts",
     FK_AFTER, [], "xr", "C", None, True),
    # TR1v2 (ruled on r118): after the void, the thief rotates again (qT2, C to T2, naming its own row g2 but not the
    # void): the void and the revocation are C's end, so qT2 retires nothing and g2 counts nothing
    ("r118 TR1v2: after the roster's void, a second rotation without the void in its past retires nothing: g2 counts "
     "nothing", FK + [VOID("vT", ("P1", "P2"), "qT"), KE.att("g2", "C", 0, "kC"),
                      KE.rec("qT2", "T2", 1, None, names=("kC", "g2"), succ_of="C", at_old=1, typ="pseudonym")],
     [], "g2", "C", None, False),
]
ROSTER_DIRECT = FK_CASES + [
    ("r106 K1r: a key's row concurrent with its registered self-unseat (the seat lane's revocation) counts nothing",
     [], KUR, "gt", "N", None, False),
    ("and its row the self-unseat names counts", [], KUR, "a1", "N", None, True),
    ("own_row (iv), ruled strict: the reader's row concurrent with its own `registered` revocation is no row of its line",
     [], KRG(()), "aT", "T", "F", False),
    ("and one its honest revocation names stays in", [], KRG(("rF",)), "aT", "T", "F", True),
    ("own_row (iii), r101 R2: another key's note claiming the reader as a cosigner is no row of the reader's line",
     [], KR2, "aT", "T", "F", False),
    ("own_row (i): a row the reader signed takes the row up though it concluded nothing", [], KUN, "aT", "T", "F", True),
    ("STRICT own_row (review-48 R2s): a concluded offer the reader is a voice of through its cosign row (the cosign "
     "naming nothing) is no row of its line, and takes the row up for nothing", [], KCO, "aT", "T", "F", False),
    ("r97 K1: a thief holding the reader's key signs a note as the reader naming its own row, after the key's end: the "
     "note is no row of the reader's line, and the row counts nothing", [], KK, "aN", "N", "N", False),
    ("an honest note the reader signed before its own key's end still takes the row up", [], KH, "aT", "T", "F", True),
    ("edge (3): a voided rotation's rows by the rotated-to key fall by the cut rule: T's row aT, not in the void's past, "
     "counts nothing", CH.ROOM + SP + recs() + [KT, QT0, TAT, VOID("vT", ("P1", "P2"), "qT")], [], "aT", "T", None, False),
    ("and stands for F, which took it up before the void", CH.ROOM + SP + recs() + [KT, QT0, TAT, rack("rF", "F", ("aT",)),
                                                                                  VOID("vT", ("P1", "P2"), "qT")],
     [], "aT", "T", "F", True),
    ("G33: the evicted device C's own row as a bare key (an attestation after the eviction) counts: an eviction ends no "
     "liveness", SP + [EVC] + recs() + [KE.att("aB", "C", 4, "kC", about="X", names=("eC",))], [], "aB", "C", None, True),
]


def plain(seat_rows, key_rows, rule):
    """The first pass, with no key view: the roster acts concluded under the roster's own count rule, and the counts
    final by acknowledgement over clean receipts (the key lane read for them by the plain end rule)."""
    for m in ("_READER_MEMO", "_VOID_MEMO", "_EMEMO", "_SEATS_OF"): getattr(ST, m).clear()
    S1 = CK.concluded(CK.kept(list(seat_rows)), rule)
    roster = ST.self_roster_ends(S1)
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


# own_row over ONE state with the seat rows concluded by the seat rule and the key lane by key_end.RULE (the caller's
# combined conclusion): (name, rows, row, key, reader, expected)
def combined(rows):
    rule = lambda r, P, past: KE.RULE(r, P, past) if r["kind"] in ("rec", "att", "edge", "revoke") else RULE(r, P, past)
    return CK.concluded(CK.kept(list(rows)), rule)


KUC = lambda cos: [KE.rec("kT", "T", 0, None, typ="pseudonym"), KE.att("aT", "T", 2, "kT"), KREV("rvT", "T", 3, ("kT",)),
                   ST.offer("x", "Z", "F", "member", "Q", "self", ("aT",), cosigners=cos)]   # Z's offer over Q's key: no
# r114 TR (review-48): N's honest row a1, its revocation rv (either form) naming a1, and the thief's row gt with N's
# key, concurrent with rv. A rotation by the thief WITH rv in its past is no row of N's (the plain end rule) and
# concludes nothing, so rv stays an end and gt counts nothing (TR2). One concurrent with rv stands, and rv is no end
# while it stands (ruled (1)); only the self roster's void of the rotation restores rv (FK below)
TRB = [KE.rec("r0", "N", 0, 100), KE.att("a1", "N", 2, "r0"), KE.att("gt", "N", 3, "r0", names=("a1",))]
TRV = {"key lane": KE.revoke("rv", "N", 5, ("a1",)),
       "seat lane": ST.unseat("rv", "N", "N", "registered", "N", "self", ("r0", "a1"))}
TRROT = lambda names: KE.rec("rot", "N3", 0, 100, names=names, succ_of="N", at_old=4)
TR_CASES = [c for form, rv in TRV.items() for c in (
    ("r114 TR0 (%s): the thief's row concurrent with the honest revocation counts nothing" % form,
     TRB + [rv], "gt", "N", None, False),
    ("r114 TR0 (%s): and the honest row the revocation names counts" % form, TRB + [rv], "a1", "N", None, True),
    ("r114 TR2 (%s): the thief's rotation with the revocation in its past concludes nothing: gt still counts nothing"
     % form, TRB + [rv, TRROT(("r0", "gt", "rv"))], "gt", "N", None, False),
    ("r114 TR2 (%s): and the rotated-to key's own row, covered by that rotation, concludes nothing" % form,
     TRB + [rv, TRROT(("r0", "gt", "rv")), KE.att("n3", "N3", 1, "rot")], "n3", "N3", None, False),
    ("r118 TR1h (%s): the one-key owner's last resort: its own rotation (N to N5, naming a1), concurrent with the "
     "thief's, forks the key: the thief's row counts nothing (a person of one key denies a second holder of that key "
     "only by ending the identity: no successor stands)" % form,
     TRB + [rv, TRROT(("r0", "gt")), KE.rec("rot5", "N5", 0, 100, names=("r0", "a1"), succ_of="N", at_old=3)],
     "gt", "N", None, False),
    ("r114 (c) TR1 (%s), ruled (1): a rotation concurrent with the owner's revocation, in a person with no self roster "
     "to void it, stands and the revocation is no end: gt counts (the stated residual)" % form,
     TRB + [rv, TRROT(("r0", "gt"))], "gt", "N", None, True))]
OWN_DIRECT = TR_CASES + [
    ("r110 RK0: K rotated to K2, the rotation naming a1: a1 counts", RKR, "a1", "K", None, True),
    # r114, ruled (1): a revocation is no end while a rotation of the key stands, the rotation in its past or concurrent
    ("r110 RK1: and the retired key's key-lane self-revocation, the rotation in its past, is no end: a1 still counts",
     RKR + [KE.revoke("rv", "K", 1, ("r0", "rot"))], "a1", "K", None, True),
    ("r110 RK2: and the retired key's registered self-unseat, the rotation in its past, is no end either: a1 counts",
     RKR + [ST.unseat("ur", "K", "K", "registered", "K", "self", ("r0", "rot"))], "a1", "K", None, True),
    ("r110 RK1: and one concurrent with the rotation (not naming a1) is no end while the rotation stands: a1 counts",
     RKR + [KE.revoke("rv", "K", 1, ("r0",))], "a1", "K", None, True),
    ("r110 RK2: and a registered self-unseat concurrent with the rotation is no end either: a1 counts",
     RKR + [ST.unseat("ur", "K", "K", "registered", "K", "self", ("r0",))], "a1", "K", None, True),
    ("r106 U2: a registered self-unseat that concluded nothing is no end: the reader's concurrent row still takes up",
     [KE.rec("kT", "T", 0, None, typ="pseudonym"), KE.att("aT", "T", 2, "kT"), KREV("rvT", "T", 3, ("kT",)),
      CK.row("rF", "note", "F", ("aT",)), ST.unseat("uF", "F", "F", "registered", "F", "group", ())],
     "aT", "T", "F", True),
    ("own_row (ii): a seat row listing the reader as a cosigner that concluded nothing is no row of its line (S5, S6)",
     KUC(("F",)), "aT", "T", "F", False),
]

# the successor of a key with the self roster's acts (name, seat rows, key rows, key, expected)
# "this device was stolen" (ruled on r118, reading (a)): the self roster evicts the stolen key C and voids the thief's
# rotation qT, two acts of one target each, signed together. C is then no key of the person, and no later rotation of
# C (qT2, the thief's again) yields the person's key. (name, rows, key, the person it speaks for)
STOLEN = CH.ROOM + SP + recs() + [KT, QT0, VOID("vT", ("P1", "P2"), "qT"), KP.evict("eC", "SP", "C", ("P1", "P2"), ("aC",))]
QT2 = KE.rec("qT2", "T2", 1, None, names=("kC",), succ_of="C", at_old=1, typ="pseudonym")
PERSON = [
    ("this device was stolen: before the roster acts, C speaks for P1", CH.ROOM + SP + recs() + [KT, QT0], "C", "P1"),
    ("this device was stolen: the roster's eviction of C and void of qT, two one-target acts: C speaks for no person",
     STOLEN, "C", "C"),
    ("and a later rotation of C by its holder (qT2) yields no key of the person", STOLEN + [QT2], "T2", "T2"),
]
SUCCESSOR = [
    ("this device was stolen: the void and the eviction leave C no successor", STOLEN, [], "C", None),
    ("a rotation the self roster voided names no successor", CH.ROOM + SP + recs() + [KT, QT0, VOID("vT", ("P1", "P2"), "qT")],
     [], "C", None),
    ("the same rotation, not voided, names its key", CH.ROOM + SP + recs() + [KT, QT0], [], "C", "T"),
    # r116: the void is read from the self roster's own concluded counted acts (seat.self_roster_ends over the rows),
    # never from a row's shape: X, no key of SP, writes an unseat of T citing qT, shaped like the roster's eviction
    ("r116: a row shaped like the roster's eviction (X's unseat of T citing qT, X no key of the roster) voids nothing",
     CH.ROOM + SP + recs() + [KT, QT0, dict(ST.unseat("vX", "X", "T", "self", "SP", "group", ("SP",), head=("SP",),
                                                      policy="self_roster_evict", counted="self"),
                                            names=("SP", "qT"))], [], "C", "T"),
    ("r114 (a): a rotation with a concurrent revocation stands: its key succeeds", FK, [], "C", "T"),
    ("r114 (b): the roster voids the rotation: no successor", FK + [VOID("vT", ("P1", "P2"), "qT")], [], "C", None),
    ("r118 TR1v2: and a second rotation without the void in its past names no successor either",
     FK + [VOID("vT", ("P1", "P2"), "qT"), KE.att("g2", "C", 0, "kC"),
           KE.rec("qT2", "T2", 1, None, names=("kC", "g2"), succ_of="C", at_old=1, typ="pseudonym")], [], "C", None),
    ("r110 RK2: a registered self-unseat with the rotation in its past is no end: the rotation's key "
     "succeeds", [ST.unseat("ur", "K", "K", "registered", "K", "self", ("r0", "rot"))],
     [KE.rec("r0", "K", 0, None, typ="pseudonym"), KE.att("a1", "K", 3, "r0"),
      KE.rec("rot", "K2", 0, None, names=("r0", "a1"), succ_of="K", at_old=4, typ="pseudonym")], "K", "K2"),
]
PLANTS = (("key_view_unread", ST.MUT), ("cosigner_key_unchecked", ST.MUT), ("window_key_view_unread", ST.MUT),
          ("ballot_key_view_unread", ST.MUT), ("lift_key_view_unread", ST.MUT), ("receipt_key_view_unread", ST.MUT),
          ("lone_key_view_unread", ST.MUT), ("retired_key_revokes", KE.MUT),
          ("taken_up_unread", KE.MUT), ("reader_line_unchecked", KE.MUT), ("own_unconcluded_unread", KE.MUT),
          ("own_claimed_cosigner", KE.MUT), ("registered_end_unread", KE.MUT), ("registered_unconcluded_counted", KE.MUT), ("retired_registered_ends", KE.MUT), ("revoked_key_rotates", KE.MUT), ("void_reopens", KE.MUT), ("final_count_unread", KE.MUT), ("final_protects_late", KE.MUT),
          ("receipt_unclean_counts", ST.MUT), ("rotation_void_unread", KE.MUT), ("voided_successor_kept", KE.MUT),
          ("disputed_key_voices", ST.MUT), ("clean_signers_only", ST.MUT), ("roster_end_any_object", ST.MUT))
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
    for name, sr, kr, rid, k, reader, want in ROSTER_DIRECT:
        KS, roster, final = plain(sr, kr, RULE)
        got = KE.counts_by(KS, rid, k, reader, final, roster)
        if got != want: bad.append("%s: got %s" % (name, got))
    for name, rows, rid, k, reader, want in OWN_DIRECT:
        CS = combined(rows)
        if CS.C.get("x") or CS.C.get("uF"): bad.append("%s: the unconcluded row concluded" % name)
        got = KE.counts_by(CS, rid, k, reader)
        if got != want: bad.append("%s: got %s" % (name, got))
    for name, sr, kr, k, want in SUCCESSOR:
        KS, roster, final = plain(sr, kr, RULE)
        got = KE.successor(KS, k, None, roster)
        if got != want: bad.append("%s: got %s" % (name, got))
    for name, rows, k, want in PERSON:
        S = combined(rows)
        got = ST.rep_of(list(S.Cs), k)
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
                                                                   len(CASES) + len(LONE) + len(CUT) + len(DIRECT) + len(ROSTER_DIRECT) + len(SUCCESSOR) + len(PERSON) + len(OWN_DIRECT), len(PLANTS) - len(missed), len(PLANTS)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
