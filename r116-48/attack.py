"""r116-48: wip 4d7f223 (r114 ruling: rotation and revocation ordered by their pasts; concurrent, a fork).
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
def show(name, rows, asks, orders=None, roster=frozenset()):
    S = state(rows)
    print(name)
    for a in asks:
        if a[0] == "counts": got = KE.counts_by(S, a[1], a[2], None, frozenset(), roster)
        elif a[0] == "ends": got = sorted(e["id"] for e in KE.key_ends(S, a[1], roster))
        elif a[0] == "concl": got = bool(S.C.get(a[1]))
        elif a[0] == "succ": got = KE.successor(S, a[1], roster=roster)
        print("   ", a, "->", got)
    if orders:
        print("    over every order:", {KE.counts_by(CK.arrive(list(p), RULE), orders[0], orders[1], None, frozenset(), roster)
                                       for p in itertools.permutations(rows)})

# TR: thief after the owner's revocation (both lanes)
R0 = KE.rec("r0", "N", 0, 100)
A1 = KE.att("a1", "N", 2, "r0")
GT = KE.att("gt", "N", 3, "r0", names=("a1",))
for form, REV in (("key", KE.revoke("rv", "N", 5, ("a1",))), ("seat", reg_unseat("rv", "N", ("r0", "a1")))):
    show("TR1 %s: thief rotation concurrent with the revocation (fork)" % form,
         [R0, A1, REV, GT, KE.rec("rot", "N3", 0, 100, names=("r0", "gt"), succ_of="N", at_old=4)],
         [("concl", "rot"), ("ends", "N"), ("counts", "a1", "N"), ("counts", "gt", "N"), ("succ", "N")], orders=("gt", "N"))
    show("TR2 %s: thief rotation with the revocation in its past" % form,
         [R0, A1, REV, GT, KE.rec("rot", "N3", 0, 100, names=("r0", "gt", "rv"), succ_of="N", at_old=4)],
         [("concl", "rot"), ("ends", "N"), ("counts", "gt", "N"), ("succ", "N")])
# RK: a retired key's thief makes a fork by a revocation that does not name the rotation
K0 = KE.rec("k0", "K", 0, 100)
KA = KE.att("ka", "K", 3, "k0")
ROT = KE.rec("krot", "K2", 0, 100, names=("k0", "ka"), succ_of="K", at_old=4)
show("RK0 rotation names ka", [K0, KA, ROT], [("ends", "K"), ("counts", "ka", "K"), ("succ", "K")])
for form, REV in (("key", KE.revoke("krv", "K", 1, ("k0",))), ("seat", reg_unseat("krv", "K", ("k0",)))):
    show("RKf %s: the retired key's thief revokes, not naming the rotation (fork)" % form, [K0, KA, ROT, REV],
         [("concl", "krv"), ("ends", "K"), ("counts", "ka", "K"), ("succ", "K")], orders=("ka", "K"))
    REVa = dict(REV, names=tuple(REV["names"]) + ("krot",))
    show("RKa %s: the same revocation naming the rotation" % form, [K0, KA, ROT, REVa],
         [("ends", "K"), ("counts", "ka", "K"), ("succ", "K")])
    # settlement: the caller's roster names an eviction of K citing the revocation (no self-roster rows held at all)
    EV = CK.row("ev", "note", "X", ("krv",), to=("K",))
    show("RKs %s: a row by X 'to' K citing krv, passed as roster (concluded? a note)" % form, [K0, KA, ROT, REV, EV],
         [("concl", "ev"), ("ends", "K"), ("counts", "ka", "K"), ("succ", "K")], roster=frozenset({"ev"}))
