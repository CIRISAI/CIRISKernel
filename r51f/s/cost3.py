import os, time; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G5 = room(5)
for N in (256,):
    ST._EMEMO.clear()
    H = [ballot("ba","A","C"), ballot("bb","B","B"), ballot("bc","C","C"), ballot("bd","D","C")]
    chain, prev = [], "lm"
    for i in range(N):                                    # E's N agreeing ballots, each naming the one before: no fork
        chain.append(ballot("e%d" % i, "E", "C", (prev,))); prev = "e%d" % i
    ec = elect("ec", "C", tuple(b["id"] for b in H + chain))
    acks = [ack("k1","A","ec"), ack("k2","B","ec"), ack("k4","D","ec")]
    t = time.time()
    S_ = CK.concluded(CK.kept([G5, LM] + H + chain + [ec] + acks), E.RULE); Q = ST.Seats(S_)
    dt = time.time() - t
    print("N=%3d  %.2fs  ec concluded %s  C seated %s" % (N, dt, any(r["id"] == "ec" for r in S_.Cs), Q.stands("C","moderate","g")))
    if dt > 6: break
