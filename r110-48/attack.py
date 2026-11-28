"""r110-48: key-ends 5d98369 (off release-0.5.0-wip be94547), read through key_end and seat directly (no consent).
python3 -I attack.py <src>/models/causal_kernel"""
import sys, itertools
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import seat as ST
import key_end as KE
CK = ST.CK
LANE = ("rec", "att", "edge", "revoke")
RULE = lambda r, P, past: KE.RULE(r, P, past) if r["kind"] in LANE else ST.seat_rule(r, P, past)
def state(rows): return CK.concluded(CK.kept(list(rows)), RULE)
def note(i, k, names=()): return CK.row(i, "note", k, tuple(names))
def reg_unseat(i, k, names=(), conf="self", **kw): return ST.unseat(i, k, k, "registered", k, conf, tuple(names), **kw)
def show(name, rows, asks):
    S = state(rows)
    print(name)
    for a in asks:
        if a[0] == "counts": got = KE.counts_by(S, a[1], a[2], a[3] if len(a) > 3 else None)
        elif a[0] == "ends": got = sorted(e["id"] for e in KE.key_ends(S, a[1]))
        elif a[0] == "concl": got = bool(S.C.get(a[1]))
        elif a[0] == "rep": got = ST.rep_of([q for q in S.Cs if q["id"] in S.anc[a[1]] or q["id"] == a[1]], a[2])
        print("   ", a, "->", got)
    return S

# K1r direct: a row of N concurrent with N's concluded registered self-unseat counts nothing
show("K1r", [note("a0", "N"), reg_unseat("ur", "N", ("a0",)), note("gt", "N", ("a0",))],
     [("concl", "ur"), ("ends", "N"), ("counts", "a0", "N"), ("counts", "gt", "N")])
# U2 direct: an unconcluded registered self-unseat is no end
show("U2", [note("a0", "N"), reg_unseat("ux", "N", ("a0",), conf="group", policy="accord_majority"), note("gt", "N", ("a0",))],
     [("concl", "ux"), ("ends", "N"), ("counts", "gt", "N")])
# PG1 direct: the genesis key's key-lane revocation: its device speaks for no one at a row that has it
SO = ST.offer("SO", "O", ("O",), "self", "@", "self")
A2 = ST.offer("aO2", "O", "O2", "self", "SO", "group", ("SO",), head=("SO",), policy="self_roster_add", counted="self", cosigners=("O2",))
show("PG1", [SO, A2, KE.revoke("rvo", "O", 5, ("aO2",)), note("n", "O2", ("rvo",)), note("m", "O2", ("aO2",))],
     [("rep", "m", "O2"), ("rep", "n", "O2")])
# RK: a RETIRED key (rotated away). Its key-lane revocation is no end (ends_of: "a retired key's revocation is no
# end"); its registered self-unseat IS one (key_ends adds it whatever rotation is held). A thief of the retired key
# cuts the old key's honest rows the rotation kept, by an unseat that does not name them.
R0 = KE.rec("r0", "K", 0, 100)
A1 = KE.att("a1", "K", 3, "r0")
ROT = KE.rec("rot", "K2", 0, 100, names=("r0", "a1"), succ_of="K", at_old=4)
show("RK0 rotation names a1: a1 counts", [R0, A1, ROT], [("ends", "K"), ("counts", "a1", "K")])
show("RK1 + the retired key's key-lane self-revocation, not naming a1", [R0, A1, ROT, KE.revoke("rv", "K", 1, ("r0",))],
     [("ends", "K"), ("counts", "a1", "K")])
show("RK2 + the retired key's registered self-unseat, not naming a1", [R0, A1, ROT, reg_unseat("ur", "K", ("r0",))],
     [("concl", "ur"), ("ends", "K"), ("counts", "a1", "K")])
# orders
for nm, rows, q in (("K1r", [note("a0", "N"), reg_unseat("ur", "N", ("a0",)), note("gt", "N", ("a0",))], ("gt", "N")),
                    ("RK2", [R0, A1, ROT, reg_unseat("ur", "K", ("r0",))], ("a1", "K"))):
    got = {KE.counts_by(CK.arrive(list(p), RULE), *q) for p in itertools.permutations(rows)}
    print(nm, "over every order:", got)
