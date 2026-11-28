import sys, os, random
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import seat as ST, check_lone_acts as L, check_charter as CC
CK = ST.CK; act = L.act; W = L.W; T, F = True, False
def lrun(name, rows, concl, force, n=30):
    a = L.answer(rows, concl, force); rnd = random.Random(5); d = 0
    for _ in range(n):
        t = list(rows[1:]); rnd.shuffle(t)
        if L.answer([rows[0]] + t, concl, force) != a: d += 1
    print("%-86s %s  orders differ %d/%d" % (name, a, d, n))
def crun(name, rows, concl, asks, sc="member"):
    out = set()
    for o in CC.orders(rows):
        S = CC.arrive(list(o)); Q = ST.Seats(S)
        out.add((tuple((i, bool(S.C.get(i))) for i in sorted(concl)), tuple((k, Q.stands(k, s, ob)) for k, s, ob in asks)))
    print("%-86s %s" % (name, sorted(out)))
QW, QR = L.QW, L.QR
lrun("control: p1 withholds p3, p1 releases (target=qw)", W + [QW, QR], {"qr": T}, {"qw": T})
lrun("R1 p2 releases p1's withhold", W + [QW, act("qr", "quarantine:release", "p2", names=("qw",), target="qw")], {"qr": T}, {"qw": T})
lrun("R2 a release of a release", W + [QW, QR, act("qr2", "quarantine:release", "p1", names=("qr",), target="qr")], {"qr2": T}, {"qw": T})
lrun("R3 a release citing qw (old shape, no target)", W + [QW, act("qr", "quarantine:release", "p1", names=("qw",), cites=("qw",))], {"qr": T}, {"qw": T})
lrun("R3b release target=qw plus a stray cite of qw1 (p2's withhold of p1)", W + [QW, act("qw1", "quarantine:withhold", "p2", target="p1"),
     act("qr", "quarantine:release", "p1", names=("qw", "qw1"), target="qw", cites=("qw1",))], {"qr": T}, {"qw": T, "qw1": T})
lrun("R4 double release", W + [QW, QR, act("qrb", "quarantine:release", "p1", names=("qr",), target="qw")], {"qr": T, "qrb": T}, {"qw": T})
# R5 the withholder's release, then the withholder lays slash down; p2 had receipted the withhold (keeps it in force)
RCPT = CK.row("q2", "ack", "p2", ("qw",), of="qw")
LAYS = ST.withdraw("ls", "p1", "g", ("qr",), scope="slash")
lrun("R5 p2 receipts qw; p1 releases; p1 lays slash down after the release", W + [QW, RCPT, QR, LAYS], {"qr": T, "ls": T}, {"qw": T, "qr": T})
LAYC = ST.withdraw("ls", "p1", "g", ("qw",), scope="slash")
lrun("R5b same, the lay-down concurrent with the release", W + [QW, RCPT, QR, LAYC], {"qr": T, "ls": T}, {"qw": T, "qr": T})
# R6 the withhold's target is the release's signer? p1 withholds p1 (itself) then releases
lrun("R6 p1 withholds itself and releases", W + [act("qs", "quarantine:withhold", "p1", target="p1"),
     act("qr", "quarantine:release", "p1", names=("qs",), target="qs")], {"qs": T, "qr": T}, {"qs": T})
# cites: duplicates, string
LF = lambda cites: ST.offer("lf", "p2", (), "act", "g", "group", ("td", "o2", "o3", "o4", "g"), head=("g",), cites=cites, policy="moderation_overturn")
OBS = [L.OB("o2", "p2"), L.OB("o3", "p3"), L.OB("o4", "p4")]
lrun("K1 lift cites 'td' as a string", W + [L.TD] + OBS + [LF("td")], {"lf": T}, {"td": T})
lrun("K2 lift cites (td, td)", W + [L.TD] + OBS + [LF(("td", "td"))], {"lf": T}, {"td": T})
# countersign bypass: the lone officer's OWN conferral (conf seat) of the officer role on a sock C
ONE, RMB = CC.ONE, CC.RMB
OC = ST.offer("oc", "A", "C", ST.OFFICER, "a1", "seat", ("a1b",), under="a1", cosigners=("C",))
crun("C1 A confers officer on sock C by conf seat (under the founding row); A+C remove B",
     ONE + [CC.A1OB if False else OC, dict(RMB(("a1b",), cos=("C",)), names=("a1b", "oc", "ob"))], {"oc": 1, "rm": 1},
     [("C", ST.OFFICER, "a1"), ("B", "member", "a1")])
OCs = ST.offer("oc", "A", "C", ST.OFFICER, "a1", "self", ("a1b",), cosigners=("C",))
crun("C2 the same by conf self", ONE + [OCs, dict(RMB(("a1b",), cos=("C",)), names=("a1b", "oc", "ob"))], {"oc": 1, "rm": 1},
     [("C", ST.OFFICER, "a1"), ("B", "member", "a1")])
# C3 the lone officer admits C (exempt) with role officer stated on an admission of scope "member"? (that is the appointment)
# C4 an admission (scope member) carrying duty_holders for officer
ADM = ST.offer("ad", "A", ("C",), "member", "a1", "group", ("a1b",), head=("a1b",), cosigners=("C",), counted=ST.OFFICER,
               duty_holders=((ST.OFFICER, ("C",)),))
crun("C4 an admission of C carrying duty_holders officer", ONE + [ADM], {"ad": 1}, [("C", ST.OFFICER, "a1"), ("C", "member", "a1")])
