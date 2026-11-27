import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G7 = E.ROOM(7); LM = E.LM
K7 = "ABCDEFG"
H = [ballot("b"+k.lower(), k, r) for k, r in zip("ABCDEF", ["B","B","B","C","C","C"])] + [ballot("bg","G","B")]
ch = [ST.withdraw("wg","G","bg",("bg",)), ballot("bg2","G","C",("wg",))]
ids = tuple("b"+k for k in "abcdef")
ec = elect("ec","C",ids+("bg","wg","bg2"),K7)
pad = [ballot("pv%d"%i,"A","ABCD") for i in range(3)]          # A's void ballots (rank four): count nothing, add rows
eb = elect("eb","B",ids+("bg",)+tuple(p["id"] for p in pad),K7)   # its past holds no wg: G's old ballot counts
show("A9a 7-room: B over a set hearing all seven, G only by its old ballot, padded by A's void ballots", [G7, LM] + H + ch + [ec] + pad + [eb], K7)
ec3 = elect("ec3","C",ids+("bg","wg","bg2")+tuple(p["id"] for p in pad),K7)
show("A9b C answers over the union", [G7, LM] + H + ch + [ec] + pad + [eb, ec3], K7)
pad2 = [ballot("pw%d"%i,"A","ABCD") for i in range(3)]
eb4 = elect("eb4","B",ids+("bg",)+tuple(p["id"] for p in pad+pad2),K7)
show("A9c A pads three more, B re-signs: B again", [G7, LM] + H + ch + [ec] + pad + [eb, ec3] + pad2 + [eb4], K7)
