exec(open(__file__.replace("probe.py","lib.py")).read())
G3 = ST.found("g","A",("A","B","C","D","E","F"),{"moderate":("A","B","C")},cosigners=("B","C","D","E","F"),licence_classes=((M,False),))
DCC = ST.offer("dcc","A","D","moderate","g","group",("g",),head=("g",),cosigners=("B","C"),counted="duty",policy="duty_confer")
DCA = ST.accept("dca","D","dcc")
for nm, wd in (("withdraw dca names dca", ST.withdraw("wd","D","dca",("dca",))), ("withdraw dcc (D in to)", ST.withdraw("wd","D","dcc",("dca",))),
               ("withdraw dcc scope moderate", ST.withdraw("wd","D","dcc",("dca",),scope="moderate"))):
    S = arrive([G3,DCC,DCA,wd]); print(nm, "concl", S.C.get("wd"), sorted(ST.Seats(S).holders("duty","g")))
