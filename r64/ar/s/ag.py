exec(open(__file__.replace("ag.py","lib.py")).read())
# honest: A (lone duty holder) confers moderate on C at aG; C accepts by cosigning. Two holders now.
DC1 = ST.offer("d1","A","C","moderate",OBJ,"group",("aG",),head=("aG",),policy="duty_confer",counted="duty",cosigners=("C",))
# A alone, from {g} (when A was the lone holder), confers moderate on B
DC0 = ST.offer("d0","A","B","moderate",OBJ,"group",("g",),head=("g",),policy="duty_confer",counted="duty",cosigners=("B",))
run("Ag1 honest d1 (A->C at aG); A alone d0 (A->B from {g})", ROOM+[DC1,DC0], ids=("d1","d0"), scopes=("member","moderate"))
DC2 = ST.offer("d2","A","D","moderate",OBJ,"group",("d1",),head=("d1",),policy="duty_confer",counted="duty",cosigners=("D",))
run("Ag2 control: A alone confers on D at d1 (two holders)", ROOM+[DC1,DC2], ids=("d1","d2"), scopes=("member","moderate"))
# C withdrawn as moderator by B? recall of C by A,B at (d1,d0)
WC = ST.unseat("wc","A","C","moderate",OBJ,"group",("d1","d0"),head=("d1","d0"),policy="duty_withdraw",counted="duty",cosigners=("B",))
run("Ag3 + A,B withdraw C's duty heads (d1,d0)", ROOM+[DC1,DC0,WC], ids=("d1","d0","wc"), scopes=("member","moderate"))
