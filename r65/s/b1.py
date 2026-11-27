exec(open(__file__.replace("b1.py","lib.py")).read())
WM, XLM = CH.WM, CH.XLM
M4 = ("m1","m2","MOD","N")
run("B1 no reader: lone removal xl (head md, an in past), then honest admission of P by all four, head xl", WM + [XLM, admit("ap","P",M4,("xl",))], ids=("xl","ap"), scopes=("member","agent"))
run("B1r reader R acked an", WM + [ack("ak","R","an"), XLM, admit("ap","P",M4,("xl",))], own="R", ids=("xl","ap"), scopes=("member","agent"))
run("B1s reader R acked an; admission head an naming xl (W1 refuses)", WM + [ack("ak","R","an"), XLM, admit("ap","P",M4,("an",),("xl",))], own="R", ids=("xl","ap"), scopes=("member","agent"))
run("B1t reader R acked an; admission heads (xl,an)", WM + [ack("ak","R","an"), XLM, admit("ap","P",M4,("xl","an"))], own="R", ids=("xl","ap"), scopes=("member","agent"))
