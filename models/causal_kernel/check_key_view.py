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


def answer(rule, seat_rows, key_rows, view):
    KS = KE.state(list(seat_rows) + list(key_rows))
    ST.KEY_VIEW.append((lambda rid, k: KE.counts_by(KS, rid, k)) if view else None)
    try:
        ST._READER_MEMO.clear(); ST._VOID_MEMO.clear()
        S = CK.concluded(CK.kept(list(seat_rows)), WRULE if rule == "window" else RULE)
        P = [q for q in S.Cs if q["id"] in S.anc["x"]]
        return set(ST.voices(S.by["x"], P)), bool(S.C.get("x"))
    finally:
        ST.KEY_VIEW.pop()


PLANTS = (("key_view_unread", ST.MUT), ("cosigner_key_unchecked", ST.MUT), ("window_key_view_unread", ST.MUT),
          ("ballot_key_view_unread", ST.MUT))
SIGNED = ("x", "cC", "c2", "be")                                   # the rows whose per-key answers the fixture carries


def run():
    bad = []
    for name, rule, sr, kr, view, v, c in CASES:
        gv, gc = answer(rule, sr, kr, view)
        if gc != c or (v is not None and gv != v): bad.append("%s: got %s" % (name, (gv, gc)))
    return bad


def fixture():
    """For the crate (tests/key_view.rs) and for persist to replay: each case's rows, the per-(row, key) answers of
    key_end.counts_by, and the voices and conclusion of x with and without the key view."""
    out = []
    for name, rule, sr, kr, view, v, c in CASES:
        KS = KE.state(list(sr) + list(kr))
        keys = sorted({q["signer"] for q in sr} | {k for q in sr for k in q.get("cosigners", ())})
        per = [[rid, k, KE.counts_by(KS, rid, k)] for rid in SIGNED if rid in KS.by for k in keys]
        out.append({"name": name, "rule": rule, "seat": [r["id"] for r in sr], "rows": list(sr) + list(kr), "view": view,
                    "counts": per, "voices": sorted(v) if v is not None else None, "concluded": c})
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
                                                                   len(CASES), len(PLANTS) - len(missed), len(PLANTS)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
