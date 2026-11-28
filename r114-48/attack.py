"""r114-48: wip b78e3de (RK2 fix). A rotation by a thief of the revoked key, after the revocation, unmakes it.
python3 -I attack.py <src>/models/causal_kernel"""
import sys, itertools
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import seat as ST
import key_end as KE
CK = ST.CK
LANE = ("rec", "att", "edge", "revoke")
RULE = lambda r, P, past: KE.RULE(r, P, past) if r["kind"] in LANE else ST.seat_rule(r, P, past)
def state(rows): return CK.concluded(CK.kept(list(rows)), RULE)
def reg_unseat(i, k, names=()): return ST.unseat(i, k, k, "registered", k, "self", tuple(names))
def show(name, rows, asks, orders=False):
    S = state(rows)
    print(name)
    for a in asks:
        if a[0] == "counts": got = KE.counts_by(S, a[1], a[2])
        elif a[0] == "ends": got = sorted(e["id"] for e in KE.key_ends(S, a[1]))
        elif a[0] == "concl": got = bool(S.C.get(a[1]))
        print("   ", a, "->", got)
    if orders:
        print("    over every order:", {KE.counts_by(CK.arrive(list(p), RULE), *orders) for p in itertools.permutations(rows)})

R0 = KE.rec("r0", "N", 0, 100)
A1 = KE.att("a1", "N", 2, "r0")                       # the honest row, named by the revocation
GT = KE.att("gt", "N", 3, "r0", names=("a1",))        # the thief's row, concurrent with the revocation
for form, REV in (("key lane", KE.revoke("rv", "N", 5, ("a1",))), ("seat lane", reg_unseat("rv", "N", ("r0", "a1")))):
    show("TR0 %s: honest revocation; thief row gt concurrent: gt counts nothing" % form, [R0, A1, REV, GT],
         [("concl", "rv"), ("ends", "N"), ("counts", "a1", "N"), ("counts", "gt", "N")])
    ROTc = KE.rec("rot", "N3", 0, 100, names=("r0", "gt"), succ_of="N", at_old=4)
    show("TR1 %s: + the thief rotates N to N3, naming gt (concurrent with the revocation)" % form, [R0, A1, REV, GT, ROTc],
         [("concl", "rot"), ("ends", "N"), ("counts", "gt", "N")], orders=("gt", "N"))
    ROTa = KE.rec("rot", "N3", 0, 100, names=("r0", "gt", "rv"), succ_of="N", at_old=4)
    show("TR2 %s: the thief's rotation has the revocation in its past" % form, [R0, A1, REV, GT, ROTa],
         [("concl", "rot"), ("ends", "N"), ("counts", "gt", "N")])
