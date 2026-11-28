import sys, os, random
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import seat as ST, check_lone_acts as L
CK = ST.CK; act = L.act; W = L.W; T = True
def run(name, rows, concl, force, n=30):
    a = L.answer(rows, concl, force); rnd = random.Random(5); d = 0
    for _ in range(n):
        t = list(rows[1:]); rnd.shuffle(t)
        if L.answer([rows[0]] + t, concl, force) != a: d += 1
    print("%-88s %s  orders differ %d/%d" % (name, a, d, n))
QW, QR = L.QW, L.QR
run("E2 p2 receipts qw AFTER the release (names qr)", W + [QW, QR, CK.row("q2", "ack", "p2", ("qr",), of="qw")], {"qr": T}, {"qw": T})
run("E2b p2 receipts qw concurrent with the release", W + [QW, QR, CK.row("q2", "ack", "p2", ("qw",), of="qw")], {"qr": T}, {"qw": T})
LAY = ST.withdraw("ls", "p1", "g", ("qw",), scope="slash")
run("E4 p2 receipts qw; p1 lays slash down; then p1 releases (names ls)", W + [QW, CK.row("q2", "ack", "p2", ("qw",), of="qw"), LAY,
    act("qr", "quarantine:release", "p1", names=("qw", "ls"), target="qw")], {"qr": T}, {"qw": T})
run("E5 p1 releases; p1 withholds p3 again (qw2 names qr)", W + [QW, QR, act("qw2", "quarantine:withhold", "p1", names=("qr",), target="p3")],
    {"qw2": T}, {"qw": T, "qw2": T})
run("E6 release concurrent with p1's second withhold qw2 of p3", W + [QW, QR, act("qw2", "quarantine:withhold", "p1", names=("qw",), target="p3")],
    {"qw2": T}, {"qw": T, "qw2": T})
