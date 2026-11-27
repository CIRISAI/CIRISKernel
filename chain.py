import sys, itertools
sys.path.insert(0, sys.argv[1])
import seat as ST, window as WN, check_removal_in_force as CR
CK = ST.CK
RULE = lambda r, P, past: WN.rule(r, P, past)
base = [CR.G, CR.AGS3, CR.CM1, CR.CM2]
x = CR.lone("x", "A1", "A2", ("cm2",))
lay = ST.withdraw("la1", "A1", "cm1", ("x",), scope="moderate")
z = CR.lone("z", "A2", "A3", ("cm2",), cites=("x",))
for name, rows in (("x, lay, z", base + [x, lay, z]), ("x, z", base + [x, z])):
    S = CK.concluded(CK.kept(rows), RULE); Q = ST.Seats(S)
    res = (sorted(Q.dropped), sorted(Q.roster("g")))
    bad = ""
    for p in itertools.permutations(rows[1:]):
        Q2 = ST.Seats(CK.arrive([rows[0]] + list(p), RULE))
        if (sorted(Q2.dropped), sorted(Q2.roster("g"))) != res: bad = "ORDER-DIFF"; break
    print(name, res, bad)
