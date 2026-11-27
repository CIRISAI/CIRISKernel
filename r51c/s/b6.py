import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "b2.py")).read().split("show(")[0].split("lib.py\")).read())")[1])
base = [G5, lm1, aF, lm2] + H + [ef, ec]
rc = [ack("ka","A","ef"), ack("kb","B","ef"), ack("kc","C","ec")]
# the twins' closing bases differ: ef's (winner F) is A..E, 3 of 5; ec's (winner C) is A,B,D,E, and C's receipt is out: 2 of 4
wf = ST.withdraw("wf", "F", "ef", ("ka","kb","kc")); wc = ST.withdraw("wc", "C", "ec", ("wf",))
nx = [ballot("n1","A","A",("wc",),of="ef"), ballot("n2","B","A",("wc",),of="ef"), elect("en","A",("n1","n2"),of="ef")]
for flag in (False, True):
    ST.ELECTION_OPEN_NEXT = flag; ST._EMEMO.clear()
    print("==== ELECTION_OPEN_NEXT =", flag)
    show("B6 twins with different winners, receipts A,B (of ef), C (of ec); F resigns; next election names ef", base + rc + [wf, wc] + nx, "ABCDEF", n=200)
nx2 = [ballot("n1","A","A",("wc",),of="ec"), ballot("n2","B","A",("wc",),of="ec"), elect("en","A",("n1","n2"),of="ec")]
ST.ELECTION_OPEN_NEXT = False; ST._EMEMO.clear()
show("B6c the same, next election naming ec", base + rc + [wf, wc] + nx2, "ABCDEF", n=200)
