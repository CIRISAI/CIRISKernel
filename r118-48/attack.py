"""r118-48: wip ca3c01f (r114 ruling (1): no fork; a revocation is no end while an unvoided rotation stands).
python3 -I attack.py <src>/models/causal_kernel"""
import sys, itertools
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import seat as ST
import key_end as KE
CK = ST.CK
LANE = ("rec", "att", "edge", "revoke")
RULE = lambda r, P, past: KE.RULE(r, P, past) if r["kind"] in LANE else ST.seat_rule(r, P, past)
def state(rows): return CK.concluded(CK.kept(list(rows)), RULE)
def show(name, rows, roster=frozenset()):
    S = state(rows)
    print("%-78s ends=%s gt=%s a1=%s successor=%s" % (name, sorted(e["id"] for e in KE.key_ends(S, "N", roster)),
          KE.counts_by(S, "gt", "N", None, frozenset(), roster), KE.counts_by(S, "a1", "N", None, frozenset(), roster),
          KE.successor(S, "N", roster=roster)))
R0 = KE.rec("r0", "N", 0, 100)
A1 = KE.att("a1", "N", 2, "r0")
RV = KE.revoke("rv", "N", 5, ("a1",))
GT = KE.att("gt", "N", 3, "r0", names=("a1",))
ROT = KE.rec("rot", "N3", 0, 100, names=("r0", "gt"), succ_of="N", at_old=4)
base = [R0, A1, RV, GT, ROT]
show("TR1 owner revokes; thief rotates N->N3 concurrently, naming gt", base)
show("TR1v + the roster's void of the rotation (an eviction of N3 citing rot)", base + [CK.row("vd", "note", "S", ("rot",), to=("N3",))],
     roster=frozenset({"vd"}))
ROT2 = KE.rec("rot2", "N4", 0, 100, names=("r0", "gt"), succ_of="N", at_old=4)
show("TR1v2 + after the void, the thief's second rotation N->N4 (not voided)", base + [CK.row("vd", "note", "S", ("rot",), to=("N3",)), ROT2],
     roster=frozenset({"vd"}))
show("TR1h the owner rotates too, concurrently (N->N5): two rotations, a fork of rotations",
     base + [KE.rec("rot5", "N5", 0, 100, names=("r0", "a1"), succ_of="N", at_old=4)])
