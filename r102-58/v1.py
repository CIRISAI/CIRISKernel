import sys, os, random
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import seat as ST, check_lone_acts as L
CK = ST.CK; act = L.act; W = L.W; T = True
def run(name, rows, concl, force, n=30):
    a = L.answer(rows, concl, force); rnd = random.Random(5); d = 0
    for _ in range(n):
        t = list(rows[1:]); rnd.shuffle(t)
        if L.answer([rows[0]] + t, concl, force) != a: d += 1
    print("%-92s %s  orders differ %d/%d" % (name, a, d, n))
QW, QR = L.QW, L.QR
RC = CK.row("q2", "ack", "p2", ("qw",), of="qw")                       # p2 receipts the withhold
LAYC = ST.withdraw("ls", "p1", "g", ("qw",), scope="slash")             # p1's lay-down, concurrent with the release
# p2 (now the lone slash holder) re-seats p1 in slash, by the duty holders' count, after the lay-down and the release
RS = lambda names: ST.offer("rs", "p2", "p1", "slash", "g", "group", names, head=("g",), policy="duty_confer", counted="duty", cosigners=("p1",))
run("control: receipt, release, concurrent lay-down (release cut)", W + [QW, RC, QR, LAYC], {"qr": T, "ls": T}, {"qw": T, "qr": T})
run("V1 the same, then p1 re-seated in slash (names ls and qr)", W + [QW, RC, QR, LAYC, RS(("ls", "qr", "g"))], {"rs": T}, {"qw": T, "qr": T})
run("V1b re-seat naming ls only (concurrent with qr)", W + [QW, RC, QR, LAYC, RS(("ls", "g"))], {"rs": T}, {"qw": T, "qr": T})
# V2 a release of an already-lapsed withhold: p1 withholds (no receipt), lays slash down (qw lapses), is re-seated, then releases
LAY = ST.withdraw("ls", "p1", "g", ("qw",), scope="slash")
QRL = act("qr", "quarantine:release", "p1", names=("qw", "rs"), target="qw")
run("V2 qw lapsed by p1's lay-down; p1 re-seated; p1 releases qw", W + [QW, LAY, RS(("ls", "g")), QRL], {"rs": T, "qr": T}, {"qw": T, "qr": T})
run("V2b qw lapsed, p1 re-seated, no release: does qw revive?", W + [QW, LAY, RS(("ls", "g"))], {"rs": T}, {"qw": T})
# V3 receipted withhold, lay-down, re-seat, then a release by p1 (names rs)
run("V3 receipted qw; p1 lays down; re-seated; then releases", W + [QW, RC, LAY, RS(("ls", "g")), QRL], {"rs": T, "qr": T}, {"qw": T, "qr": T})
# V2/V3 again with the release at the newest counted change (head rs)
QRH = act("qr", "quarantine:release", "p1", heads=("rs",), names=("qw",), target="qw")
run("V2' qw lapsed; p1 re-seated; p1 releases at head rs", W + [QW, LAY, RS(("ls", "g")), QRH], {"rs": T, "qr": T}, {"qw": T, "qr": T})
run("V3' receipted qw; p1 lays down; re-seated; p1 releases at head rs", W + [QW, RC, LAY, RS(("ls", "g")), QRH], {"rs": T, "qr": T}, {"qw": T, "qr": T})
