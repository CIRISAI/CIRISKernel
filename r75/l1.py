import sys, os, random
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import seat as ST, window as WN, check_lone_acts as L
CK = ST.CK; RULE = L.RULE; act = L.act; W = L.W; T, F = True, False
def run(name, rows, concl, force, n=40):
    a = L.answer(rows, concl, force)
    rnd = random.Random(5); d = 0
    for _ in range(n):
        t = list(rows[1:]); rnd.shuffle(t)
        if L.answer([rows[0]] + t, concl, force) != a: d += 1
    print("%-78s %s  orders differ %d/%d" % (name, a, d, n))
# 1. a fake lift: an offer of scope act naming td, on ANOTHER room the attacker p3 controls with a sock Z
X = ST.found("x", "p3", ("p3", "Z"), {}, cosigners=("Z",))
FL = ST.offer("lf", "p3", (), "act", "x", "group", ("td", "x"), head=("x",), content="td", policy="community_invite", cosigners=("Z",))
run("fake lift on room x (p3 + sock Z), content td", W + [L.TD, X, FL], {"td": T, "lf": T}, {"td": T})
FL2 = dict(FL, policy="moderation_overturn")
run("same, policy moderation_overturn", W + [L.TD, X, FL2], {"lf": T}, {"td": T})
FL3 = ST.offer("lf", "p3", ("p3",), "act", "p3", "group", ("td",), head=("td",), content="td", policy="community_invite", cosigners=())
run("fake lift over the key p3 itself (obj a key)", W + [L.TD, FL3], {"lf": T}, {"td": T})
# 2. self-release: p2 withholds p1 (a slash holder); p1 releases the withhold naming it
QW1 = act("qw1", "quarantine:withhold", "p2", target="p1")
QR1 = act("qr1", "quarantine:release", "p1", names=("qw1",), target="p1", of="qw1")
run("p2 withholds p1; p1 releases its own withhold", W + [QW1, QR1], {"qw1": T, "qr1": T}, {"qw1": T})
# 2b: p1 withheld by p2, then p2 is withheld by p1 concurrently: does p1's release still work
# 3. slashing verdict against the slasher itself? p1 slashes p1? (self) ; p1 releases a withhold of p3 by p2
QW3 = act("qw3", "quarantine:withhold", "p2", target="p3")
QR3 = act("qr3", "quarantine:release", "p1", names=("qw3",), target="p3", of="qw3")
run("p2 withholds p3; p1 (other holder) releases it", W + [QW3, QR3], {"qr3": T}, {"qw3": T})
# 4. reconsideration on a takedown of ANOTHER room by a review holder of this room
G2 = ST.found("g2", "q1", ("q1", "q2", "q3"), {"takedown": ("q1",), "review": ("q2",)}, cosigners=("q2", "q3"))
C2 = CK.row("c2", "post", "q3", ("g2",), room="g2")
TD2 = act("td2", L.TDK, "q1", heads=("g2",), names=("c2",), obj="g2", of="c2")
RCx = act("rc", "reconsideration:new_evidence", "p4", heads=("g",), names=("td2",), of="td2", outcome="reversed")
run("p4 (review in g) reverses a takedown in g2", W + [G2, C2, TD2, RCx], {"td2": T, "rc": T}, {"td2": T})
# 5. lone act with obj g but naming a head in another room
TDh = act("td", L.TDK, "p1", heads=("g2",), names=("c1",), of="c1")
run("takedown in g naming head g2", W + [G2, TDh], {"td": T}, {"td": T})
# 6. takedown of a content row in ANOTHER room by a g takedown holder
TDo = act("td", L.TDK, "p1", names=("c2",), of="c2")
run("p1 (takedown in g) takes down c2, a row of room g2", W + [G2, C2, TDo], {"td": T}, {"td": T})
# 7. lift stuffing: objections by non-members / duplicate objections by one key
LS = L.LIFT(("o2", "o2b", "oz"))
run("lift with p2 twice and a non-member", W + [L.TD, L.OB("o2", "p2"), L.OB("o2b", "p2"), L.OB("oz", "ZZ"), LS], {"lf": T}, {"td": T})
# 8. a lift naming objections to another act
LO = L.LIFT(("o2", "o3"))
run("lift whose objections are to another act (qw)", W + [L.TD, L.QW, L.OB("o2", "p2", "qw"), L.OB("o3", "p3", "qw"), LO], {"lf": T}, {"td": T})
