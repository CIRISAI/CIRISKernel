import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G7 = room(7); K7 = "ABCDEFG"
e1r = [ballot("ba","A","B"), ballot("bb","B","B"), elect("e1","B",("ba","bb")), ST.withdraw("wb","B","e1",("e1",))]
e2r = [ballot("ba2","A","C",("wb",),of="e1"), ballot("bc2","C","C",("wb",),of="e1"), ballot("bd2","D","C",("wb",),of="e1"),
       elect("e2","C",("ba2","bc2","bd2"),of="e1",vac=("wb",))]
atk = [ballot("be","E","D"), ballot("bf","F","D"), ballot("bg","G","D"),
       elect("e1x","D",("ba","bb","be","bf","bg"))]          # a fork from lm: a superset of e1's set, D 3 to B 2
for flag in (False, True):
    ST._EMEMO.clear()
    print("==== ELECTION_OPEN_NEXT =", flag)
    show("B4a honest: e1 (unclosed), B resigns, e2 of e1", [G7, LM] + e1r + e2r, K7)
    show("B4b + 3 of 7 fork the old election with a superset", [G7, LM] + e1r + e2r + atk, K7)
