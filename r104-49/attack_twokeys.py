"""r103-49: one person, two keys, two ballots. Room A, B, D, E and P1; C is a device of person P (P1's self roster).
Ballots A:B, D:D, E:D, P1:B, C:B (B casts none). Read by person: P has one ballot for B, so B 2, D 2: a tie, nobody.
Read by key: B 3 to 2, and B is seated. Also P1:B with C:D (two rankings: P no ballot, D 2 to 1? D's 2 ballots, B 1).
Run: python3 -I attack_twokeys.py <tree root>"""
import sys
sys.path.insert(0, sys.argv[1] + "/models/causal_kernel")
import check_election_close as CC  # noqa: E402
ST, KP, B, SEAT, OPEN, ACK = CC.ST, CC.KP, CC.B, CC.SEAT, CC.OPEN, CC.ACK
SP = [KP.found("SP", "P1"), KP.add("aC", "SP", "C", ("P1",), ("SP",))]
G = ST.found("g", "A", ("A", "B", "D", "E", "P1"), {"moderate": ("A",)}, cosigners=("B", "D", "E", "P1"))
op = OPEN("op", "lm", ("A", "B", "D"))
op = dict(op, names=tuple(op["names"]) + ("aC",))
for label, cb, win in (("C (P's device) also ranks B", "B", "B"), ("C ranks D, P1 ranks B", "D", "D")):
    hb = [B("ba", "A", "B"), B("bd", "D", "D"), B("be", "E", "D"), B("bp", "P1", "B"), B("bc", "C", cb, names=("aC",))]
    rows = SP + [G, CC.LM, op] + hb + [SEAT("es", win, tuple(b["id"] for b in hb))]
    print("%-32s %s's seating concludes / stands: %s" % (label, win, CC.answer(rows, "es", (win, "moderate"))))
