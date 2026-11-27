import os, time; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
G5, LM = E.G5, E.LM
for N in (4, 8, 16, 32):
    rows = [G5, LM, ballot("ba","A","B"), ballot("bb","B","B")]
    pads = [ballot("p%d"%i,"B","B") for i in range(N)]
    # N seatings of the same election by B, each over a different set (ba, bb, one pad): all equal size? (2,3) and different -> all beaten
    seats_ = [elect("s%d"%i,"B",("ba","bb","p%d"%i),"ABCDE") for i in range(N)]
    t = time.time(); _, Q, S = seats(rows + pads + seats_, "AB"); 
    print(N, "rows", len(rows)+2*N, "%.2fs" % (time.time()-t), "beaten", len(Q.beaten))
    if time.time()-t > 4: break
