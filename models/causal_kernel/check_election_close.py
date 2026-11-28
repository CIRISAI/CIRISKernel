#!/usr/bin/env python3
"""
check_election_close.py: the election close as ruled (the Constitution, 2026-11-28; review-49's r90, r91 and r93).

    1. ONE ELECTION PER SEAT END: the vacancy is the seat's end as the reader's roster takes it; two concurrent ends
       are a fork and open nothing until a counted end the roster takes, with both in its past, resolves it (and is
       the vacancy); a holder's own lay-down concurrent with a counted end of its seat is no fork.
    2. An OPENING row (`election_open`) cites the seat end (in its past), names the newest counted changes, and is
       counted by a strict majority of the members as persons at those heads, floor min(2, members), no window, no duty.
    3. The ELECTORATE is the roster at the opening's heads.
    4. Two openings for one seat are contested, neither in force, until an opening with both in its past is counted.
    5. Departures are read as the reader's roster takes them.
    6. A reader holding rival ends or openings its roster takes gets no closed answer (it waits).
    7. Inputs: persons at each input's own past; an ended key's input only before its end (the key view); the winner's
       acceptance through the key view; clean receipts only. The id is the opening's row id, named by ref.
    8. The close base is (3)'s electorate; a seating names the opening and cites its ballots; the close takes a reader.

    python3 -I check_election_close.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import seat as ST  # noqa: E402
import key_end as KE  # noqa: E402
import check_election as EL  # noqa: E402
import check_key_person as KP  # noqa: E402

CK, R, OBJ = ST.CK, ST.R, EL.OBJ
RULE = EL.RULE
T, F = True, False
G5, LM = EL.G5, EL.LM


def OPEN(i, end, signers, heads=("g",)):
    return ST.election_open(i, signers[0], OBJ, end, heads, cosigners=tuple(signers[1:]))


def B(i, k, ranking, op="op", names=()):
    return R(i, "ballot", k, (op,) + tuple(names), ranking=tuple(ranking), of=op)


def SEAT(i, k, ballots, op="op", heads=("g",), signer=None):
    return ST.offer(i, signer or k, k, "moderate", OBJ, "group", (op,) + tuple(ballots) + tuple(heads), head=tuple(heads),
                    policy="moderator_election", of=op)


ACK = EL.ack
OP5 = OPEN("op", "lm", ("A", "B", "C"))
H5 = [B("ba", "A", "B"), B("bb", "B", "B"), B("bc", "C", "C"), B("bd", "D", "C"), B("be", "E", "C")]
IDS = tuple(b["id"] for b in H5)
HONEST = [G5, LM, OP5] + H5 + [SEAT("ec", "C", IDS)]


def answer(rows, sid, ask=("C", "moderate"), reader=None, keys=None):
    """(the ask's standing, sid closed for the reader) with the key view over `keys` (key rows) where given."""
    if keys is not None:
        KS = KE.state(list(rows) + list(keys))
        ST.KEY_VIEW.append(lambda rid, k: KE.counts_by(KS, rid, k))
    else:
        ST.KEY_VIEW.append(None)
    try:
        for m in ("_READER_MEMO", "_VOID_MEMO", "_EMEMO", "_SEATS_OF"): getattr(ST, m).clear()
        S = CK.concluded(CK.kept(list(rows)), RULE)
        Q = ST.Seats(S, own=reader)
        return Q.stands(ask[0], ask[1], OBJ), closed(S, sid, reader)
    finally:
        ST.KEY_VIEW.pop()


def closed(S, sid, reader):
    """election_closed(S, sid, reader): the close read on the reader's line (its void and its seat ends)."""
    return ST.election_closed(S, sid, reader)


RULE5 = HONEST + [ST.unseat("u1", "A", "D", "member", OBJ, "group", ("g",), head=("g",), policy="community_remove",
                           cosigners=("B", "C")),
                  ST.unseat("u2", "C", "A", "member", OBJ, "group", ("g",), head=("g",), policy="community_remove",
                           cosigners=("D", "E")),
                  ACK("k1", "A", "ec", ("u1", "u2")), ACK("k2", "B", "ec"), ACK("k4", "D", "ec", ("u1", "u2"))]
RECS = [KE.rec("k" + k, k, 0, None, typ="pseudonym") for k in "ABCDEFGX"]
CASES = [
    ("rule 2: the honest election: the opening (A, B, C of five) at g, C three to two; closed by A, B and D", 
     HONEST + [ACK("k1", "A", "ec"), ACK("k2", "B", "ec"), ACK("k4", "D", "ec")], "ec", {}, (T, T)),
    ("rule 2: an opening by two of five (A, B) concludes nothing, and nothing is seated",
     [G5, LM, OPEN("op", "lm", ("A", "B"))] + H5 + [SEAT("ec", "C", IDS)], "ec", {}, (F, F)),
    ("rule 2: a room of one opens and seats alone (floor min(2, members))",
     [EL.G1, LM, OPEN("op", "lm", ("A",)), B("ba", "A", "A"), SEAT("ea", "A", ("ba",))], "ea",
     {"ask": ("A", "moderate")}, (T, T)),
    ("rule 2: an opening at an old head (it holds aX, X's admission after g, and names g as its head) concludes "
     "nothing, and nothing is seated",
     [G5, LM, EL.admit("ax", "X", tuple("ABCDE"), ("g",)), dict(OPEN("op", "lm", ("A", "B", "C"), ("g",)),
                                                              names=("lm", "g", "ax"))]
     + H5 + [SEAT("ec", "C", IDS, heads=("ax",))], "ec", {}, (F, F)),
    ("rule 3: the electorate is the roster at the opening's heads: X, admitted after the opening, does not vote",
     [G5, LM, OP5, EL.admit("ax", "X", tuple("ABCDE"), ("g",)), B("bx", "X", "B"), B("bx2", "D", "B")] +
     [B("ba", "A", "B"), B("bc", "C", "C"), B("be", "E", "C"), B("bb", "B", "C")] +
     [SEAT("ec", "C", ("bx", "bx2", "ba", "bc", "be", "bb"), heads=("ax",))], "ec", {}, (T, F)),
    ("rule 1: two concurrent lay-downs of A's seat (lm and A's backdated lm0) are a fork: an opening citing either "
     "concludes nothing where it holds both, and nothing is seated",
     [G5, LM, ST.withdraw("lm0", "A", "g", ("g",), scope="moderate"), dict(OPEN("op", "lm", ("A", "B", "C")),
                                                                          names=("lm", "lm0", "g"))] + H5 + [SEAT("ec", "C", IDS)],
     "ec", {}, (F, F)),
    ("rule 1: a holder's lay-down concurrent with a counted end (B, C, D recall A) is no fork: the recall is the end, "
     "and the opening citing it seats C",
     [G5, LM, ST.unseat("rc", "B", "A", "moderate", OBJ, "group", ("g",), head=("g",), policy="moderator_recall",
                        cosigners=("C", "D")), OPEN("op", "rc", ("A", "B", "C"), ("rc",))] + H5 +
     [SEAT("ec", "C", IDS, heads=("rc",))], "ec", {}, (T, F)),
    ("rule 4: two openings for one end, neither in the other's past (A B C and C D E): contested, neither in force, "
     "and no seating of either stands for a reader holding both",
     [G5, LM, OP5, OPEN("op2", "lm", ("C", "D", "E"))] + H5 + [SEAT("ec", "C", IDS)] +
     [B("b2" + k.lower(), k, "B", "op2") for k in "BDE"] + [SEAT("eb", "B", ("b2b", "b2d", "b2e"), op="op2")], "ec", {},
     (F, F)),
    ("rule 4: and an opening with both in its past resolves: it is the election, the rivals' ballots are void, and "
     "the members vote again under it",
     [G5, LM, OP5, OPEN("op2", "lm", ("C", "D", "E")), dict(OPEN("op3", "lm", ("A", "B", "D")), names=("lm", "g", "op", "op2"))]
     + H5 + [B("c" + k.lower(), k, "C", "op3") for k in "ACD"] + [SEAT("ec3", "C", ("ca", "cc", "cd"), op="op3")],
     "ec3", {}, (T, F)),
    ("rule 6: a fresh reader (no acknowledgement) holding two rival openings gets no closed answer: it waits",
     [G5, LM, OP5, OPEN("op2", "lm", ("C", "D", "E"))] + H5 + [SEAT("ec", "C", IDS), ACK("k1", "A", "ec"),
                                                               ACK("k2", "B", "ec"), ACK("k4", "D", "ec")],
     "ec", {}, (F, F)),
    ("rule 7: one person, one say in the close: P's two devices (P1 genesis, C added) receipt once; A, B and the "
     "person P (via C and P1) are three of four other: closed", None, "ec", {}, (T, T)),
    ("rule 7: an ended key's receipt is no say: D revoked itself after 0, holding its founding signature and its "
     "ballot, not its receipt: A and B are two of four: "
     "not closed", HONEST + [ACK("k1", "A", "ec"), ACK("k2", "B", "ec"), ACK("k4", "D", "ec")], "ec",
     {"keys": RECS + [KE.revoke("vD", "D", 0, names=("g", "bd"))]}, (T, F)),
    ("rule 7: the winner's acceptance through the key view: C revoked itself after 0, holding its founding signature, "
     "its cosign of the opening and its ballot, not its seating: C's seating concludes nothing", HONEST, "ec",
     {"keys": RECS + [KE.revoke("vC", "C", 0, names=("g", "op", "bc"))]}, (F, F)),
    ("rule 7: a ballot's withdrawal by an ended key is no withdrawal: D, revoked holding its founding signature and "
     "its ballot, withdraws the ballot after: D's ballot counts, C three to two",
     [G5, LM, OP5] + H5 + [ST.withdraw("wd", "D", "bd", ("bd",)), SEAT("ec", "C", IDS + ("wd",))], "ec",
     {"keys": RECS + [KE.revoke("vD", "D", 0, names=("g", "bd"))]}, (T, F)),
    ("rule 2: an opening citing no seat end (the founding row) concludes nothing",
     [G5, LM, OPEN("op", "g", ("A", "B", "C"))] + H5 + [SEAT("ec", "C", IDS)], "ec", {}, (F, F)),
    ("rule 7: a decline by an ended key is no decline: E, revoked holding its founding signature and its ballot, "
     "declines after: C still wins",
     [G5, LM, OP5] + H5 + [R("de", "decline", "E", ("op", "be"), of="op"), SEAT("ec", "C", IDS + ("de",))], "ec",
     {"keys": RECS + [KE.revoke("vE", "E", 0, names=("g", "be"))]}, (T, F)),
    ("rule 5: a removal the reader's roster does not take leaves the base unchanged: a counted removal of D signed by "
     "A alone concludes nothing, and D's receipt still counts: closed",
     HONEST + [ST.unseat("rd", "A", "D", "member", OBJ, "group", ("g",), head=("g",), policy="community_remove"),
               ACK("k1", "A", "ec"), ACK("k2", "B", "ec"), ACK("k4", "D", "ec")], "ec", {}, (T, T)),
    ("rule 2 by persons: the room seats A and both of person P's keys (P1 and its device C); an opening signed by P1 "
     "and C is one person of two: concludes nothing, and nothing is seated", None, "open_persons", {}, (F, F)),
    ("rule 5: a contested pair of counted removals (A, B, C remove D; C, D, E remove A, concurrently) is taken by no "
     "roster: no departure and no fork of A's lay-down; A, B and D receipt C's seating: closed", RULE5,
     "ec", {}, (T, T)),
    ("G3c plus C (r90-49): A's backdated lay-down forks the end; C's receipt of B's seating closes nothing, and B is "
     "not seated", EL.G3C + [ACK("jc", "C", "eb")], "eb", {"ask": ("B", "moderate")}, (F, F)),
]


def person_world(device_opens=False):
    if device_opens:
        SP = [KP.found("SP", "P1"), KP.add("aC", "SP", "C", ("P1",), ("SP",))]
        G = ST.found("g", "A", ("A", "P1", "C"), {"moderate": ("A",)}, cosigners=("P1", "C"))
        op = dict(OPEN("op", "lm", ("P1", "C")), names=("lm", "g", "aC"))
        return SP + [G, LM, op, B("bp", "P1", "A"), B("bc", "C", "A"), B("ba", "A", "A")] + \
            [SEAT("eb", "A", ("bp", "bc", "ba"), signer="A")]
    return _person_world()


def _person_world():
    """A five-room where C is a device of person P (P1 its genesis key, seated in the room as itself? no: P1 is the
    member; C its device): the room seats A, B, D, E and P1; P1's self roster holds C."""
    SP = [KP.found("SP", "P1"), KP.add("aC", "SP", "C", ("P1",), ("SP",))]
    G = ST.found("g", "A", ("A", "B", "D", "E", "P1"), {"moderate": ("A",)}, cosigners=("B", "D", "E", "P1"))
    hb = [B("ba", "A", "B"), B("bb", "B", "B", names=()), B("bd", "D", "B"), B("bp", "P1", "D"), B("be", "E", "D")]
    op = OPEN("op", "lm", ("A", "B", "D"))
    rows = SP + [G, LM, dict(op, names=tuple(op["names"]) + ("aC",))] + hb + [SEAT("eb", "B", tuple(b["id"] for b in hb), signer="B")]
    rows += [ACK("k1", "A", "eb"), ACK("kp", "P1", "eb"), ACK("kc", "C", "eb", ("aC",)), ACK("kd", "D", "eb")]
    return rows


PLANTS = ("end_fork_unread", "open_old_heads", "open_by_key", "openings_both_stand",
          "close_no_wait", "close_key_view_unread", "close_receipt_unclean",
          "acceptance_key_view_unread", "inputs_key_view_unread", "rival_openings_read", "electorate_at_seating",
          "departures_raw", "fork_untaken_end")


def run():
    bad = []
    for name, rows, sid, kw, want in CASES:
        if rows is None:
            kw = dict(kw, ask=("A", "moderate") if sid == "open_persons" else ("B", "moderate"))
            rows = person_world(sid == "open_persons"); sid = "eb"
        got = answer(rows, sid, kw.get("ask", ("C", "moderate")), kw.get("reader"), kw.get("keys"))
        if got != want: bad.append("%s: got %s" % (name, got))
    return bad


def main():
    bad = run()
    for b in bad: print(b)
    missed = []
    for p in PLANTS:
        ST.MUT.add(p)
        try:
            hit = run()
        finally:
            ST.MUT.discard(p)
        print("  plant %-28s %s" % (p, "caught by: " + hit[0][:80] if hit else "NOT CAUGHT"))
        if not hit: missed.append(p)
    ok = not bad and not missed
    print("RESULT: %s: %d cases, %d of %d planted breaks caught" % ("ok" if ok else "%d problems" % (len(bad) + len(missed)),
                                                                   len(CASES), len(PLANTS) - len(missed), len(PLANTS)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
