"""r91-49: the proposed close (1) to (4) on the G3 rows. The election is keyed by the vacancy its seating reads (1);
a lay-down outside it changes nothing there (2). The base: the electorate at that vacancy, the winner and the
departed apart; a strict majority of it receipting a seating of that election. Electorates come from seat.py's own
C1 reading (seating_view). Run: python3 -I probe_rule1.py <tree root>"""
import sys
sys.path.insert(0, sys.argv[1] + "/models/causal_kernel")
import check_election as EL  # noqa: E402
ST, ack, elect, R, OBJ = EL.ST, EL.ack, EL.elect, EL.ST.R, EL.OBJ

def proposed(rows, label):
    rows = EL.at_newest(rows)
    S = ST.CK.concluded(ST.CK.kept(list(rows)), EL.RULE)
    past = lambda a, b: a in S.anc[b]
    seats = [q for q in S.Cs if ST.is_election(q)]
    elections = {}
    for q in seats:
        v = ST.seating_view(q, [x for x in S.Cs if past(x["id"], q["id"])], past)
        elections.setdefault(frozenset(v[3]), []).append((q, frozenset(v[1])))
    gone = {k for k, _ in ST.departures(S.Cs, past, OBJ)}
    print(label)
    for vac, qs in sorted(elections.items(), key=lambda x: sorted(x[0])):
        for q, el in qs:
            base = el - {q["to"][0]} - gone
            yes = {a["signer"] for a in S.Cs if a["kind"] == "ack" and a.get("of") == q["id"]} & base
            print("   election at vacancy %-12s seating %s (winner %s): electorate %s, base %s, receipts %s: %s"
                  % (sorted(vac), q["id"], q["to"][0], "".join(sorted(el)), "".join(sorted(base)), "".join(sorted(yes)),
                     "CLOSED" if 2 * len(yes) > len(base) else "open"))

G3H, G3I, G3X = EL.G3H, EL.G3I, EL.G3X
ED = EL.G3ED                                                    # D's seating, vacancy lm2, all seven rank D
EB1 = elect("eb", "B", G3I + ("xb", "xc", "wbb", "wbc"), vac=("lm1",))   # B's seating states lm1 only (rule 1)
HON = EL.N1R + [EL.N1L2] + G3H + [ED] + [ack("k" + k.lower(), k, "ed") for k in "EFG"]
if __name__ == "__main__": proposed(HON, "honest: lm2 only; D's seating receipted by E, F, G")
if __name__ == "__main__": proposed(HON + [ack("kb", "B", "ed"), ack("kc", "C", "ed"), ack("ka", "A", "ed")][:1],
         "honest + B's receipt (4 of 6 needed)")
ATK = HON + [EL.N1L1] + G3X + [EB1]
if __name__ == "__main__": proposed(ATK, "A backdates lm1; B and C re-ballot; B's seating states lm1: no receipt yet")
if __name__ == "__main__": proposed(ATK + [ack("ja", "A", "eb"), ack("jc", "C", "eb")], "the same, A and C receipt B's seating")
