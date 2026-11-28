"""r90-49: attacks on the election close (C1 to C5) at release-0.5.0-wip. Run: python3 -I attack_close.py <tree root>"""
import sys
sys.path.insert(0, sys.argv[1] + "/models/causal_kernel")
import check_election as EL  # noqa: E402

ST, R = EL.ST, EL.ST.R
G5, LM, H5, IDS5, EC, CLOSE = EL.G5, EL.LM, EL.H5, EL.IDS5, EL.EC, EL.CLOSE
ballot, decline, elect, ack, admit, leave = EL.ballot, EL.decline, EL.elect, EL.ack, EL.admit, EL.leave
MOD, NOMOD, T, F = EL.MOD, EL.NOMOD, EL.T, EL.F
ONLY = sys.argv[2:] or None

def run(name, rows, asks=None, seating=None, want_closed=None, orders=40):
    if ONLY and not any(o in name for o in ONLY): return
    rows = EL.at_newest(rows)
    out = []
    if asks is not None:
        got = EL.answers(rows, asks)
        want = [w for _, _, w in asks]
        bad = next((p for p in EL.orders(rows, orders) if EL.answers([rows[0]] + list(p), asks, arrive=True) != got), None)
        out.append("seats %s%s%s" % (dict(zip([k for k, _, _ in asks], got)), "" if got == want else "  (EXPECTED %s)" % want,
                                     "" if bad is None else "  ORDER-DEPENDENT at %s" % [r["id"] for r in bad]))
    if seating:
        got = EL.closed(rows, seating)
        bad = next((p for p in EL.orders(rows, orders) if EL.closed([rows[0]] + list(p), seating, arrive=True) != got), None)
        out.append("closed(%s)=%s%s%s" % (seating, got, "" if want_closed in (None, got) else "  (EXPECTED %s)" % want_closed,
                                          "" if bad is None else "  ORDER-DEPENDENT at %s" % [r["id"] for r in bad]))
    print("%-78s %s" % (name[:78], "; ".join(out)))

ACKS = ("k1", "k2", "k4")
# ---- a decline after the close ----
run("D1 C declines after its own closed seating; B's seating over set+decline, after close",
    [G5, LM] + H5 + [EC] + CLOSE + [decline("dc", "C", names=ACKS), elect("eb", "B", IDS5 + ("dc",), cites=ACKS)],
    MOD("C") + NOMOD("B"), "ec", T)
run("D2 the same, B's seating concurrent with the receipts (names no receipt)",
    [G5, LM] + H5 + [EC] + CLOSE + [decline("dc", "C", names=("ec",)), elect("eb", "B", IDS5 + ("dc",))],
    MOD("C") + NOMOD("B"), "ec", T)
run("D3 decline before any receipt: B's superset seating stands (control)",
    [G5, LM] + H5 + [EC, decline("dc", "C", names=("ec",)), elect("eb", "B", IDS5 + ("dc",))], MOD("B") + NOMOD("C"))
run("D4 receipts of C's seating after B's superset seating is in their past: C's did not stand there",
    [G5, LM] + H5 + [EC, decline("dc", "C", names=("ec",)), elect("eb", "B", IDS5 + ("dc",))]
    + [ack(k, s, "ec", ("eb",)) for k, s in (("k1", "A"), ("k2", "B"), ("k4", "D"))], MOD("B") + NOMOD("C"), "ec", F)
run("D5 a voter's decline after the close (D declines), D's seating attempt",
    [G5, LM] + H5 + [EC] + CLOSE + [decline("dd", "D", names=ACKS)], MOD("C"), "ec", T)
# ---- a tie ----
H4 = H5[:4]
run("T1 A,B for B against C,D for C: C's seating concludes nothing",
    [G5, LM] + H4 + [elect("ec", "C", tuple(b["id"] for b in H4))], NOMOD("B", "C"))
run("T2 the tie, both seatings written, three receipts each",
    [G5, LM] + H4 + [elect("ec", "C", tuple(b["id"] for b in H4)), elect("eb", "B", tuple(b["id"] for b in H4))]
    + [ack("k" + s.lower(), s, "ec") for s in "ABD"] + [ack("j" + s.lower(), s, "eb") for s in "ACD"],
    NOMOD("B", "C"), "ec", F)
run("T3 the tie broken by a concurrent second ballot of E (fork): E no voice",
    [G5, LM] + H4 + [ballot("be", "E", "C"), ballot("be2", "E", "B")]
    + [elect("ec", "C", tuple(b["id"] for b in H4) + ("be", "be2"))], NOMOD("B", "C"))
run("T4 a 3-way first-round tie A:B B:C C:D D:B E:C... weakest tie seats nobody",
    [G5, LM, ballot("ba", "A", "B"), ballot("bb", "B", "C"), ballot("bc", "C", "D"), ballot("bd", "D", "E"),
     ballot("be", "E", "A"), elect("ec", "C", ("ba", "bb", "bc", "bd", "be"))], NOMOD("A", "B", "C", "D", "E"))
# ---- ballot stuffing ----
X = admit("ax", "X", tuple("ABCDE"), ("lm",))
run("S1 X admitted after the vacancy ballots for B and receipts C's: no voice, not in the base",
    [G5, LM] + H5 + [X, ballot("bx", "X", "B", ("ax",)), EC, ack("k1", "A", "ec"), ack("k2", "B", "ec"), ack("kx", "X", "ec")],
    MOD("C"), "ec", F)
run("S2 an outsider Y's ballots named in B's seating: set ignores it",
    [G5, LM] + H5[:4] + [ballot("by1", "Y", "B"), ballot("by2", "Y", "B"), elect("eb", "B", tuple(b["id"] for b in H5[:4]) + ("by1", "by2"))],
    NOMOD("B"))
run("S3 B votes twice in a chain (no withdrawal), same ranking: one ballot",
    [G5, LM] + H5 + [ballot("bb2", "B", "B", ("bb",)), elect("ec", "C", IDS5 + ("bb2",))], MOD("C"))
run("S4 A re-votes in a chain for C without withdrawing its ballot for B: A no ballot, C 3 of 4",
    [G5, LM] + H5 + [ballot("ba2", "A", "C", ("ba",)), elect("ec", "C", IDS5 + ("ba2",))], MOD("C"))
run("S5 the winner's own receipt and repeated receipts by A: A, A, C close nothing",
    [G5, LM] + H5 + [EC, ack("k1", "A", "ec"), ack("k1b", "A", "ec", ("k1",)), ack("kc", "C", "ec")], MOD("C"), "ec", F)
run("S6 an outsider Y and the departed E receipt: A, B + Y, E(left before) of base A,B,D: closes (2 of 3)",
    [G5, LM] + H5 + [EC, leave("le", "E", "g", ("ec",)), ack("k1", "A", "ec"), ack("k2", "B", "ec"), ack("ky", "Y", "ec"),
                     ack("ke", "E", "ec", ("le",))], MOD("C"), "ec", T)
run("S7 the same with E's receipt before its leaving (H1 holds it): base A,B,D,E, A,B,E: 3 of 4 closes",
    [G5, LM] + H5 + [EC, ack("ke", "E", "ec"), leave("le", "E", "g", ("ke",)), ack("k1", "A", "ec"), ack("k2", "B", "ec")],
    MOD("C"), "ec", T)
run("S8 E's receipt before leaving, and only A besides: 2 of 4, open",
    [G5, LM] + H5 + [EC, ack("ke", "E", "ec"), leave("le", "E", "g", ("ke",)), ack("k1", "A", "ec")], MOD("C"), "ec", F)
# ---- receipts across the electorate (C5) ----
run("R1 receipts split across C's seating and a rival containing it, 2 + 2: neither closes",
    [G5, LM] + H5 + [EC, decline("dd", "D", names=("ec",)), elect("ex", "C", IDS5 + ("dd",)),
                     ack("k1", "A", "ec"), ack("k2", "B", "ec"), ack("j4", "D", "ex"), ack("j5", "E", "ex")], MOD("C"), "ex")
run("R2 a person's concurrent receipts of two sets: no say (A); B, D: 2 of 4 open",
    [G5, LM] + H5 + [EC, decline("dd", "D", names=("ec",)), elect("ex", "C", IDS5 + ("dd",)),
                     ack("k1", "A", "ec"), ack("j1", "A", "ex"), ack("k2", "B", "ec"), ack("k4", "D", "ec")], MOD("C"), "ec")
run("R3 the receipts name the rival before receipting C's narrower seating: C's did not stand in their past",
    [G5, LM] + H5 + [EC, decline("dd", "D", names=("ec",)), elect("ex", "C", IDS5 + ("dd",))]
    + [ack("k" + s.lower(), s, "ec", ("ex",)) for s in "ABD"], MOD("C"), "ec", F)
