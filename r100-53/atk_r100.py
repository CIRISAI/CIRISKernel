"""r100-53: key-person 89558f5, the cosigned rival. python3 -I atk_r100.py <kp models/causal_kernel>"""
import sys, random
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import check_key_person as KP
ST, CK, WN = KP.ST, KP.CK, KP.WN
RULE = KP.RULE
found, add, evict, admit_z = KP.found, KP.add, KP.evict, KP.admit_z
def show(name, rows, f, rule=RULE):
    got = f(CK.concluded(CK.kept(list(rows)), rule))
    rnd, bad = random.Random(23), 0
    for _ in range(60):
        t = list(rows); rnd.shuffle(t)
        bad += f(CK.arrive(t, rule)) != got
    print("%-104s %s differ=%d/60" % (name, got, bad))
C = lambda rid: (lambda S: bool(S.C.get(rid)))
PK = lambda S: sorted(ST.person_keys(S, "p1"))
GW = KP.GW
EVT = evict("evt", "S1", "p1", ("p1b", "p1c"), ("a1c",))
# the cosigned rival: S1r founded by p1, cosigned by the thief's fresh key x (seats p1 and x)
RX = ST.offer("S1r", "p1", ("p1", "x"), "self", "@", "self", cosigners=("x",))
show("X0 the cosigned rival concludes?", GW + [RX], C("S1r"))
show("X1 no eviction, no counted row: honest p1b+p2+p3 admit naming a1c only", GW + [RX, admit_z(("p1b", "p2", "p3"), ("a1c",))], C("az"))
show("X2 ... naming a1c and S1r (the rival in its past)", GW + [RX, admit_z(("p1b", "p2", "p3"), ("a1c", "S1r"))], C("az"))
T = ST.cosign("t", "x", "t", ("S1r", "a1c"))
show("X3 ... naming a thief cosign row t (by x) over S1r and a1c", GW + [RX, T, admit_z(("p1b", "p2", "p3"), ("t",))], C("az"))
show("X3' person_keys(p1) with the rival held", GW + [RX], PK)
show("X4 the devices evict p1 from S1; admit naming evt and S1r", GW + [RX, EVT, admit_z(("p1b", "p2", "p3"), ("evt", "S1r"))], C("az"))
show("X4' person_keys(p1) after the eviction", GW + [RX, EVT], PK)
show("X4'' the rival founded AFTER the eviction (names evt); admit naming it", GW + [EVT, dict(RX, names=("evt",)), admit_z(("p1b", "p2", "p3"), ("S1r",))], C("az"))
# x's own rows as the person's
show("X5 no eviction: x + p2 + p3 admit z naming S1r and a1c", GW + [RX, admit_z(("x", "p2", "p3"), ("S1r", "a1c"))], C("az"))
show("X5' after the eviction: x + p2 + p3", GW + [RX, EVT, admit_z(("x", "p2", "p3"), ("evt", "S1r"))], C("az"))
show("X5'' after the eviction: x + p1b + p2 (two persons? one?)", GW + [RX, EVT, admit_z(("x", "p1b", "p2"), ("evt", "S1r"))], C("az"))
# the thief's counted add on S1r, before and after the eviction
TX = add("tx", "S1r", "y", ("p1", "x"), ("S1r",))
show("Y1 before eviction: p1+x add y to S1r; concludes?", GW + [RX, TX], C("tx"))
show("Y2 ... honest admit naming a1c and tx", GW + [RX, TX, admit_z(("p1b", "p2", "p3"), ("a1c", "tx"))], C("az"))
show("Y3 after eviction (tx before it): admit naming evt and tx", GW + [RX, TX, EVT, admit_z(("p1b", "p2", "p3"), ("evt", "tx"))], C("az"))
TXa = add("txa", "S1r", "y", ("p1", "x"), ("S1r", "evt"))
show("Y4 the add after the eviction (names evt); concludes?", GW + [RX, EVT, TXa], C("txa"))
show("Y5 ... honest admit naming txa", GW + [RX, EVT, TXa, admit_z(("p1b", "p2", "p3"), ("txa",))], C("az"))
TXx = add("txx", "S1r", "y", ("x",), ("S1r", "evt"))
show("Y6 after eviction x alone adds y to S1r; concludes? then honest admit naming it", GW + [RX, EVT, TXx, admit_z(("p1b", "p2", "p3"), ("txx",))], C("az"))
show("Y6' y + p2 + p3 after Y6", GW + [RX, EVT, TXx, admit_z(("y", "p2", "p3"), ("txx",))], C("az"))
