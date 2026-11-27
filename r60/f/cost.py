import os, time; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G5 = room(5)
H = [ballot("ba","A","B"), ballot("bb","B","B"), ballot("bc","C","C"), ballot("bd","D","C"), ballot("be","E","C")]
ids = tuple(b["id"] for b in H)
def run(label, extra, tail):
    ST._EMEMO.clear(); t = time.time()
    S = CK.concluded(CK.kept([G5, LM] + H + extra + tail), E.RULE); Q = ST.Seats(S)
    return time.time() - t
for N in (64, 128, 256, 512):
    # flood 1: N concurrent receipts by D of a seating that does not stand (two non-nested seatings)
    s1 = elect("s1","B",("ba","bb")); s2 = elect("s2","C",("bc","bd"))
    acks = [ack("r%d"%i,"E","s1",("lm",)) for i in range(N)]
    t1 = run("acks", [s1, s2] + acks, [elect("su","C",ids,cites=("r0",))])
    # flood 2: N ballot+withdraw pairs by E after the vacancy, then a seating
    fl = []
    for i in range(N):
        fl += [ballot("x%d"%i,"E","C"), ST.withdraw("w%d"%i,"E","x%d"%i,("x%d"%i,))]
    t2 = run("withdraws", fl, [elect("ec","C",ids,cites=tuple("w%d"%i for i in range(N)))])
    print("N=%3d  receipts flood %.2fs   withdrawal flood %.2fs" % (N, t1, t2))
    if max(t1, t2) > 4: break
ST._EMEMO.clear()
S = CK.concluded(CK.kept([G5, LM] + H + fl + [elect("ec","C",ids,cites=tuple("w%d"%i for i in range(N)))]), E.RULE)
print("ec concluded:", any(r["id"]=="ec" for r in S.Cs), "withdrawals concluded:", sum(1 for r in S.Cs if r["id"].startswith("w")))
