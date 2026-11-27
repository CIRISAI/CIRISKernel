import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G5, LM = E.G5, E.LM
K5 = "ABCDE"
H = [ballot("ba","A","B"), ballot("bb","B","B"), ballot("bc","C","C"), ballot("bd","D","C"), ballot("be","E","C")]
ec = elect("ec","C",("ba","bb","bc","bd","be"),K5)
# D changes its mind after C is seated (and after C's next acts): withdraws and ranks B
ch = [ST.withdraw("wd","D","bd",("ec",)), ballot("bd2","D","B",("wd",))]
eb = elect("eb","B",("ba","bb","bc","bd","wd","bd2","be"),K5, heads=("lm",))
show("A8a one late change of mind, rival over the larger set", [G5, LM] + H + [ec] + ch + [eb], K5)
# A8b: padding instead of persons: D re-ranks nothing; B's ally A posts void ballots to out-row a set where D is heard only
# through its withdrawn ballot. C's set: (5 persons, 7 rows incl. wd, bd2); B's: omit bd2 -> D heard via bd+wd, pad with A's void ballots
ch2 = [ST.withdraw("wd","D","bd",("bd",)), ballot("bd2","D","C",("wd",))]       # D withdrew and re-ranked C (same choice)
ec2 = elect("ec","C",("ba","bb","bc","bd","wd","bd2","be"),K5)
pad = [ballot("pv%d"%i,"A","ABCD") for i in range(2)]
eb2 = elect("eb","B",("ba","bb","bc","bd","wd","be")+tuple(p["id"] for p in pad),K5)
show("A8b B over a set omitting D's fresh ballot, A's void ballots as padding: 2-2 tie -> no winner", [G5, LM] + H + ch2 + [ec2] + pad + [eb2], K5)
