import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G7 = room(7); K7 = "ABCDEFG"
H = [ballot("b"+k.lower(), k, r) for k, r in zip(K7, "BBBCCCC")]
ids = tuple(b["id"] for b in H)
ec = elect("ec", "C", ids)                                  # C 4, B 3
close = [ack("k"+k.lower(), k, "ec") for k in "ABDE"]        # 4 of the 6 others: closed
show("B1a honest: C over seven ballots, closed by A,B,D,E", [G7, LM] + H + [ec] + close, K7)
# F and G withdraw their ballots, naming nothing of the election; a note by B names both withdrawals
wd = [ST.withdraw("wf", "F", "bf", ("bf",)), ST.withdraw("wg", "G", "bg", ("bg",))]
note = R("nt", "note", "B", ("wf", "wg"))
eb = elect("eb", "B", ids, cites=("nt",))                    # the SAME set; F, G's ballots gone in its past: B 3, C 2
show("B1b B's twin over the same set, after the close", [G7, LM] + H + [ec] + close + wd + [note, eb], K7)
show("B1c same, before any receipt", [G7, LM] + H + [ec] + wd + [note, eb], K7)
