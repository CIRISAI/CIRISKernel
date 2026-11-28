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
    ("and with x final (F, G and A receipted it), it stands for both", "seat",
     CH.ROOM + recs() + [X5, rack("rF", "F"), rack("rA", "A"), KE.revoke("vC", "C", 2, names=("kC",)),
                         rack("rG", "G", ("x", "vC"))], [], "G", "x", None, True),
    ("a revocation by a rotated-away key is no end: C rotated to C2 holding x, then C's key (stolen) revokes itself "
     "after 0, the rotation in its past: x concludes", "seat", CH.ROOM + [X5],
     recs() + [QCX, KE.revoke("vC", "C", 0, names=("qC",))], None, "x", None, True),
    ("the person's roster ends a retired key: C2, C's successor, ends C from 2 on (its owner learned it was stolen), "
     "holding the rotation and x: x, signed at 3, is cut: concludes nothing", "seat", CH.ROOM + [X5],
     recs() + [QCX, KE.rend("eC", "C2", "C", 2, names=("qC",))], None, "x", None, False),
    ("and an end of C signed by a key that is not its successor (F) is no end: x concludes", "seat", CH.ROOM + [X5],
     recs() + [QCX, KE.rend("eC", "F", "C", 2, names=("qC",))], None, "x", None, True),
    ("k3.py's K3c as written (p2's revocation holds nothing): for a reader with no line, xm (p2's withdrawal of p1's "
     "moderate) and r2 are both cut, and x stays in force: AG removed", "window", RF.W + [RF.X, R2, RF.UND],
     LREC + [KE.revoke("v2", "p2", 0)], None, None, ("AG", "agent", "g"), False),
    ("and for p3, which cosigned xm (taken up): xm stands and r2 (not on p3's line) is cut: x falls out of force, AG "
     "is back", "window", RF.W + [RF.X, R2, RF.UND], LREC + [KE.revoke("v2", "p2", 0)], "p3", None, ("AG", "agent", "g"), True),
]


def cut_answer(rule, seat_rows, key_rows, reader, probe, seat):
    for m in ("_READER_MEMO", "_VOID_MEMO", "_EMEMO", "_SEATS_OF"): getattr(ST, m).clear()
    R0 = WRULE if rule == "window" else RULE
    S1 = CK.concluded(CK.kept(list(seat_rows)), R0)
    final = frozenset(i for i in S1.by if ST.final_by_ack(S1, i))
    KS = KE.state(list(seat_rows) + list(key_rows))
    ST.KEY_VIEW.append(lambda rid, k: KE.counts_by(KS, rid, k, reader, final))
    try:
        for m in ("_READER_MEMO", "_VOID_MEMO", "_EMEMO", "_SEATS_OF"): getattr(ST, m).clear()
        S = CK.concluded(CK.kept(list(seat_rows)), R0)
        if seat: return ST.Seats(S).stands(*seat), sorted(final)
        return bool(S.C.get(probe)), sorted(final)
    finally:
        ST.KEY_VIEW.pop()


def finals(seat_rows, rule):
    """The counts final by acknowledgement, over the rows as they conclude with no key view."""
    for m in ("_READER_MEMO", "_VOID_MEMO", "_EMEMO", "_SEATS_OF"): getattr(ST, m).clear()
    S1 = CK.concluded(CK.kept(list(seat_rows)), rule)
    return frozenset(i for i in S1.by if ST.final_by_ack(S1, i))


def lone_answer(seat_rows, key_rows, view, probe):
    KS = KE.state(list(seat_rows) + list(key_rows))
    fin = finals(seat_rows, WRULE)
    ST.KEY_VIEW.append((lambda rid, k: KE.counts_by(KS, rid, k, None, fin)) if view else None)
    try:
        for m in ("_READER_MEMO", "_VOID_MEMO", "_EMEMO", "_SEATS_OF"): getattr(ST, m).clear()
        S = CK.concluded(CK.kept(list(seat_rows)), WRULE)
        return (bool(S.C.get(probe)) if probe else None), ST.Seats(S).stands("AG", "agent", "g")
    finally:
        ST.KEY_VIEW.pop()


def answer(rule, seat_rows, key_rows, view):
    KS = KE.state(list(seat_rows) + list(key_rows))
    fin = finals(seat_rows, WRULE if rule == "window" else RULE)
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
          ("taken_up_unread", KE.MUT), ("final_count_unread", KE.MUT))
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
    return bad


def fixture():
    """For the crate (tests/key_view.rs) and for persist to replay: each case's rows, the per-(row, key) answers of
    key_end.counts_by, and the voices and conclusion of x with and without the key view."""
    out = []
    for name, rule, sr, kr, view, v, c in CASES:
        fin = sorted(finals(sr, WRULE if rule == "window" else RULE))
        KS = KE.state(list(sr) + list(kr))
        keys = sorted({q["signer"] for q in sr} | {k for q in sr for k in q.get("cosigners", ())})
        per = [[rid, k, KE.counts_by(KS, rid, k)] for rid in SIGNED if rid in KS.by for k in keys]
        out.append({"name": name, "rule": rule, "seat": [r["id"] for r in sr], "rows": list(sr) + list(kr), "view": view,
                    "counts": per, "voices": sorted(v) if v is not None else None, "concluded": c, "final": fin})
    for name, sr, kr, view, probe, (c, st) in LONE:
        fin = sorted(finals(sr, WRULE))
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
                                                                   len(CASES) + len(LONE) + len(CUT), len(PLANTS) - len(missed), len(PLANTS)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
