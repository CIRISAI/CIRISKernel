import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G5 = room(5); K5 = "ABCDE"
# a partition: {A, C} and {B, D}; E (one key) votes and receipts on both sides
al = [ballot("a1","A","B"), ballot("c1","C","B"), ballot("e1","E","B")]
s1 = elect("s1", "B", ("a1","c1","e1"))
be = [ballot("b2","B","C"), ballot("d2","D","C"), ballot("e2","E","C")]
s2 = elect("s2", "C", ("b2","d2","e2"))
r1 = [ack("ka","A","s1"), ack("kc","C","s1"), ack("ke1","E","s1")]        # 3 of {A,C,D,E}: closed on alpha
r2 = [ack("kb","B","s2"), ack("kd","D","s2"), ack("ke2","E","s2")]        # 3 of {A,B,D,E}: closed on beta
A_ = [G5, LM] + al + [s1] + r1
B_ = [G5, LM] + be + [s2] + r2
show("B3a alpha alone", A_, K5)
show("B3b beta alone", B_, K5)
show("B3c both branches held (E's receipts concurrent: no say)", [G5, LM] + al + [s1] + r1 + be + [s2] + r2, K5)
# next elections on each branch, after each holder lays the seat down
na = [ST.withdraw("wB","B","s1",("ka","kc","ke1")), ballot("n1","A","A",("wB",),of="s1"), ballot("n2","C","A",("wB",),of="s1"),
      elect("x1","A",("n1","n2"),of="s1")]
nb = [ST.withdraw("wC","C","s2",("kb","kd","ke2")), ballot("m1","B","D",("wC",),of="s2"), ballot("m2","D","D",("wC",),of="s2"),
      elect("x2","D",("m1","m2"),of="s2")]
show("B3d alpha with its next election", A_ + na, K5)
show("B3e both branches and both next elections held", [G5, LM] + al + [s1] + r1 + be + [s2] + r2 + na + nb, K5)
jn = admit("jx", "X", tuple("ABCD"), ("x1",))
show("B3f + an admission naming x1 and x2's pasts", [G5, LM] + al + [s1] + r1 + be + [s2] + r2 + na + nb + [R("j","note","A",("x1","x2"))], K5)
