import sys; sys.path.insert(0, sys.argv[1])
import seat as ST, check_count_heads as CH
CK=ST.CK
aD = CH.admit("aD","D",("A","B","C"),("g",)); aE = CH.admit("aE","E",("A","B","C"),("aD",))
c1 = CH.admit("c1","H",("A","B","C"),("aD",)); c2 = CH.admit("c2","J",("A","B","C","H"),("c1",))
HC4=[CH.G,aD,aE,c1,c2]
DCX = CH.ROOM + [CH.DC("dc", "B", ("g",)), CH.remove("xg", "G", CH.FIVE, ("aG",), ("dc",))]
for m in (None, "fork_by_depth", "t_unread"):
    if m: ST.MUT.add(m)
    for nm, W in (("HC4", HC4), ("H7dc", DCX)):
        S = CK.concluded(CK.kept(list(W)), CH.RULE); Q = ST.Seats(S)
        print(m, nm, "".join(sorted(Q.holders("member","g"))), sorted(Q.stale))
    if m: ST.MUT.discard(m)
