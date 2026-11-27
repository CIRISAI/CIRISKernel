exec(open(__file__.replace("ts.py","lib.py")).read())
STL, STS, SETTLE = CR.STL, CR.STS, CR.SETTLE
rdA = RD(anchor="b0", acks=("s0","b2","b3","st","su"))
st = SETTLE("st","b1",("h3",),STS); su = SETTLE("su","s0",("h3",),STS)
run("TS1 two settlers by h3: toward b1 and toward s0", STL + [st, su], rd=rdA)
run("TS1b reader that acked only st", STL + [st, su], rd=RD(anchor="b0", acks=("s0","b2","b3","st")))
run("TS1c reader that acked only su", STL + [st, su], rd=RD(anchor="b0", acks=("s0","b2","b3","su")))
run("TS1d a reader with no acks", STL + [st, su], rd=RD(anchor="b0"))
