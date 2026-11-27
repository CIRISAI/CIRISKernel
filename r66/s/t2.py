exec(open(__file__.replace("t2.py","lib.py")).read())
FIVE = CH.FIVE
DCg = lambda i, to: ST.offer(i, "A", to, "moderate", OBJ, "group", ("g",), head=("g",), policy="duty_confer", counted="duty", cosigners=(to,))
# T2a repetition: two founders strip the room of seven to the founders, one concurrent tip at g per step
rows = ROOM + [DCg("d1","B"), remove("x1","G",("A","B"),("d1","aG"))]
run("T2a step1 remove G", rows, ids=("d1","x1"))
rows2 = rows + [DCg("d2","C"), remove("x2","F",("A","B"),("d2","x1"))]
run("T2a step2 remove F heads (d2,x1)", rows2, ids=("d2","x2"))
rows3 = rows2 + [admit("t3","X",("A","B"),("g",)), remove("x3","E",("A","B"),("t3","x2"))]
run("T2a step3 tip=A,B admit X at g; remove E heads (t3,x2)", rows3, ids=("t3","x3"))
rows4 = rows3 + [admit("t4","Y",("A","B"),("g",)), remove("x4","C",("A","B"),("t4","x3"))]
run("T2a step4 remove founder C heads (t4,x3)", rows4, ids=("t4","x4"))
run("T2a step4 reader D (signed aE etc.)", rows4, own="D", ids=("t4","x4"))
run("T2a step4 reader Q with no row", rows4, own="Q", ids=("t4","x4"))
# T2b: tip by an own conferral (conf self, a non-roster scope) by a founder in a room with NO duty holders
G2 = ST.found("g", "A", ("A","B","C"), None, cosigners=("B","C"))
R2 = [G2]; m = ["A","B","C"]; prev = "g"
for k in "DEFG":
    R2.append(admit("a"+k, k, tuple(m), (prev,))); m.append(k); prev = "a"+k
SC = ST.offer("sc", "C", "C", "foo", OBJ, "self", ("g",))
run("T2b control: C's self conferral of scope foo concludes?", R2 + [SC], ids=("sc",), scopes=("member","foo"))
run("T2b B,C remove G heads (sc,aG)", R2 + [SC, remove("xg","G",("B","C"),("sc","aG"))], ids=("sc","xg"))
# T2c room of one: A founds alone, invites N1, N2 concurrently; A alone admits N3 at (n1,n2); then removes N1 at (n3,?)
G1 = ST.found("g", "A", ("A",), None)
N1 = admit("n1","N1",("A",),("g",)); N2 = admit("n2","N2",("A",),("g",))
run("T2c A alone admits N3 heads (n1,n2)", [G1, N1, N2, admit("n3","N3",("A",),("n1","n2"))], ids=("n1","n2","n3"))
run("T2c' A alone removes N1 heads (n1,n2)", [G1, N1, N2, remove("xn","N1",("A",),("n1","n2"))], ids=("xn",))
run("T2c'' A alone removes N1 heads (n1, n2b) with n2b a fresh tip at g", [G1, N1, admit("n2b","N2",("A",),("g",)), remove("xn","N1",("A",),("n1","n2b"))], ids=("xn",))
run("T2c''' after N1 admitted (single tip), A makes tip t at g and removes N1 heads (t,n1)", [G1, N1, admit("t","Z",("A",),("g",)), remove("xn","N1",("A",),("t","n1"))], ids=("t","xn"))
