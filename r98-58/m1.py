import sys, os, random
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import seat as ST, window as WN, check_lone_acts as L
CK = ST.CK; act = L.act; W = L.W; T, F = True, False
def run(name, rows, concl, force, n=30):
    a = L.answer(rows, concl, force)
    rnd = random.Random(5); d = 0
    for _ in range(n):
        t = list(rows[1:]); rnd.shuffle(t)
        if L.answer([rows[0]] + t, concl, force) != a: d += 1
    print("%-84s %s  orders differ %d/%d" % (name, a, d, n))
QW, QR, TD = L.QW, L.QR, L.TD
# M1 a release citing two withholds: the first valid (p3's), the second p2's withhold of p1 itself
QW1 = act("qw1", "quarantine:withhold", "p2", target="p1")
QR2 = act("qr", "quarantine:release", "p1", names=("qw", "qw1"), target="p3", cites=("qw", "qw1"))
run("M1 p1 releases (qw p3, qw1 = p2's withhold of p1): self-release by a second cite", W + [QW, QW1, QR2],
    {"qr": T}, {"qw": T, "qw1": T})
# M1b second cite a withhold of another key p4 by p2 (p1 releases p4 without naming p4)
QW4 = act("qw4", "quarantine:withhold", "p2", target="p4")
QR4 = act("qr", "quarantine:release", "p1", names=("qw", "qw4"), target="p3", cites=("qw", "qw4"))
run("M1b release citing qw (p3) and qw4 (p4)", W + [QW, QW4, QR4], {"qr": T}, {"qw": T, "qw4": T})
# M1c second cite not in the release's past at all (concurrent withhold)
QR5 = act("qr", "quarantine:release", "p1", names=("qw",), target="p3", cites=("qw", "qw4"))
run("M1c release citing qw and a concurrent qw4 (not in its past)", W + [QW, QW4, QR5], {"qr": T}, {"qw": T, "qw4": T})
# M2 a lift citing td (with its objections) and qw too
LF2 = ST.offer("lf", "p2", (), "act", "g", "group", ("td", "qw", "o2", "o3", "o4", "g"), head=("g",), cites=("td", "qw"),
               policy="moderation_overturn")
run("M2 lift citing td (objected) and qw (no objection)", W + [TD, QW, L.OB("o2","p2"), L.OB("o3","p3"), L.OB("o4","p4"), LF2],
    {"lf": T}, {"td": T, "qw": T})
# M2b a lift citing the act's ids in the other order
LF3 = dict(LF2, cites=("qw", "td"))
run("M2b lift citing (qw, td), objections to td", W + [TD, QW, L.OB("o2","p2"), L.OB("o3","p3"), L.OB("o4","p4"), LF3],
    {"lf": T}, {"td": T, "qw": T})
# M3 a reconsideration citing td (valid) and td2, a takedown of p4's... content row c4 by p2; p4 (review) is c4's author
C4 = CK.row("c4", "post", "p4", ("g",), room="g")
TD2 = act("td2", L.TDK, "p2", names=("c4",), of="c4")
RC2 = act("rc", "reconsideration:new_evidence", "p4", names=("td", "td2"), cites=("td", "td2"), outcome="reversed")
run("M3 p4 reconsiders (td, td2): td2 takes down p4's own c4", W + [TD, C4, TD2, RC2], {"rc": T}, {"td": T, "td2": T})
# M3b reconsideration citing td and a takedown in ANOTHER room
G2 = ST.found("g2", "q1", ("q1", "q2", "q3"), {"takedown": ("q1",), "review": ("q2",)}, cosigners=("q2", "q3"))
C2 = CK.row("c2", "post", "q3", ("g2",), room="g2")
TDX = act("tdx", L.TDK, "q1", heads=("g2",), names=("c2",), obj="g2", of="c2")
RC3 = act("rc", "reconsideration:new_evidence", "p4", names=("td", "tdx"), cites=("td", "tdx"), outcome="reversed")
run("M3b p4 (review in g) reconsiders (td, tdx in g2)", W + [TD, G2, C2, TDX, RC3], {"rc": T, "tdx": T}, {"td": T, "tdx": T})
# M4 double release: qw released by qr, then p2 withholds p3 again (qw2), release qr still cites only qw
QW2 = act("qw2", "quarantine:withhold", "p2", target="p3", names=("qr",))
run("M4 qw, qr releases it; qw2 re-withholds later", W + [QW, QR, QW2], {"qr": T, "qw2": T}, {"qw": T, "qw2": T})
QRb = act("qrb", "quarantine:release", "p2", names=("qr",), target="p3", cites=("qw",))
run("M4b a second release of the already released qw", W + [QW, QR, QRb], {"qrb": T}, {"qw": T})
# M5 reconsideration citing a takedown already reversed, outcome upheld: does it restore?
RCu = act("rc2", "reconsideration:new_evidence", "p4", names=("rc",), cites=("td",), outcome="upheld")
run("M5 td reversed by rc, then upheld by rc2", W + [TD, L.RC("p4"), RCu], {"rc": T, "rc2": T}, {"td": T})
# M6 lift naming the act in names but citing a different id (wrong act)
LFw = ST.offer("lf", "p2", (), "act", "g", "group", ("td", "o2", "o3", "o4", "g"), head=("g",), cites=("c1",), policy="moderation_overturn")
run("M6 lift whose cite is the content row, not the act", W + [TD, L.OB("o2","p2"), L.OB("o3","p3"), L.OB("o4","p4"), LFw], {"lf": T}, {"td": T})
