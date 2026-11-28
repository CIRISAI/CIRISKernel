"""r106-49: a stale opening is never behind a reader's line. The honest election resolves the founders' stale
opening (its opening holds opg) and closes; then B and C write a second stale opening opg2 at g (citing lm0, only
g and lm0 in its past). Does D keep the seat? Readers: none; R acknowledged aG; R acknowledged ed.
Run: python3 -I attack_regrind.py <tree root> [orders]"""
import sys
sys.argv = sys.argv[:3]
exec(open("attack_line.py").read().split("WORLDS = [")[0])
OPG2 = CC.OPEN("opg2", "lm0", ("B", "C"), ("g",))
for label, extra in (("honest holding opg, closed", [LM0] + STALE + honest_h()),
                     ("+ a second stale opening opg2 at g", [LM0] + STALE + honest_h() + [OPG2])) if False else ():
    pass
def honest_h():
    rows = honest("lm0")
    rows[0] = dict(rows[0], names=tuple(rows[0]["names"]) + ("opg",))
    return rows
for label, extra in (("honest holding opg, closed", [LM0] + STALE + honest_h()),
                     ("+ a second stale opening opg2 at g", [LM0] + STALE + honest_h() + [OPG2]),
                     ("lm0 only, honest closed, + a stale opening at g", [LM0] + honest("lm0") + [OPG2])):
    for reader, rd, tag in ((None, [], "none"), ("R", RD["R"], "R@aG"), ("R", acks("ed"), "R@ed")):
        rows = EL.N1R + extra + rd
        got = ask(rows, reader, ("ed",))
        line = "%-50s %-6s moderate %s closed %s" % (label, tag, *got)
        if N:
            line += "  orders: %d of %d differ" % (sum(ask([rows[0]] + list(p), reader, ("ed",), arrive=True) != got
                                                       for p in EL.orders(rows, N)), N)
        print(line)
