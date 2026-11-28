import sys, os
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import check_delegation as D
ST, CK, RT = D.ST, D.CK, D.RT
rows = [D.ROOM, D.RS, D.RD1]
live = RT.Root([dict(D.B0R, charter=D.CSUB)], (), (D.GA,)), D.ANCHOR
lapsed = RT.Root([dict(D.B0R, charter=D.CSUB), D.GROW], (), (D.GA,)), RT.reader(anchor="b0", acks=("b1",))
with ST.root_view(*live):
    S = CK.concluded(CK.kept(list(rows)), lambda r, P, past: ST.seat_rule(r, P, past))
with ST.root_view(*lapsed):
    Q = ST.Seats(S)
    print("concluded while in force, read after the lapse: uA infra", Q.stands("uA", "infra", "room"), "| B infra:detect", Q.stands("B", "infra:detect", "room"))
    S2 = CK.concluded(CK.kept(list(rows)), lambda r, P, past: ST.seat_rule(r, P, past))
    Q2 = ST.Seats(S2); print("re-concluded after the lapse:            uA infra", Q2.stands("uA", "infra", "room"), "| B", Q2.stands("B", "infra:detect", "room"))
# arrival: rs arrives while in force, rd1 after the lapse
with ST.root_view(*live):
    S3 = CK.arrive([D.ROOM, D.RS], lambda r, P, past: ST.seat_rule(r, P, past))
print("rs concluded at arrival:", S3.C.get("rs"))
