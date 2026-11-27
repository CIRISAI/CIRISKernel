import sys, time
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import check_agent_seat as C
ST, CK = C.ST, C.CK
n = int(sys.argv[2])
rows = list(C.W3); prev = "ag"
for i in range(n):
    rows.append(C.lone("x%d" % i, "p1", "AG", (prev,))); prev = "x%d" % i
t = time.time()
S = CK.concluded(CK.kept(list(rows)), C.RULE)
Q = ST.Seats(S)
print(n, round(time.time() - t, 2), "s")
