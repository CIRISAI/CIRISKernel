"""Attacks on room-key-vectors' node arm. python3 -I atk_rk.py <models/causal_kernel>"""
import sys, random, copy
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import room_key_vectors as V
RK, ST, CK = V.RK, V.ST, V.CK
NODE, HA, HB = V.NODE, V.HA, V.HB


def go(name, extra, r, records=V.RECORDS):
    f = RK.node_row_facts(V.node_state(extra, r), r, records)
    got = RK.node_row_check(r, records, f)
    rows = V.NODE_BASE + list(extra) + [V.kernel_row(r)]
    rnd, bad = random.Random(3), 0
    for _ in range(60):
        t = list(rows); rnd.shuffle(t)
        S = CK.arrive(t, lambda q, P, past: ST.seat_rule(q, P, past))
        if RK.node_row_check(r, records, RK.node_row_facts(S, r, records)) != got: bad += 1
    print("%-78s %s differ=%d/60" % (name, got, bad))

go("baseline n1", [V.OB], V.node_row("n1", ["ob"], [HA]))
# N1: the node names an owner that never consented (no cosignature by rk:b0)
OBX = ST.offer("obx", NODE, "rk:b0", "owner", NODE, "self", ("g",))
go("N1 node binds rk:b0 as owner WITHOUT rk:b0's signature, row names vB's head", [OBX], V.node_row("x1", ["obx"], [HB]))
# N2: the owner ends the binding by an unseat of `owner` (CC 2.4.1.1 owner's revocation), not a withdrawal
UO = ST.unseat("uo", "rk:a0", "rk:a0", "owner", NODE, "seat", ("ob",), under="ob")   # the owner revokes the binding (ENDS owner)
go("N2 owner rk:a0 unseats the owner seat (a revocation), row after it", [V.OB, UO], V.node_row("x2", ["ob"], [HA], ("uo",)))
# N3: the node key revokes itself (registered), row after it
REC = ST.offer("rec", NODE, NODE, "registered", NODE, "self", ("g",))
RV = ST.unseat("rv", NODE, NODE, "registered", NODE, "self", ("rec", "ob"))
go("N3 node key revoked itself, row after", [V.OB, REC, RV], V.node_row("x3", ["ob"], [HA], ("rv",)))
# N4: the signer's own record names another room / is no node
recs = copy.deepcopy(V.RECORDS); recs[NODE] = {"key": NODE, "room": V.OTHER, "identity_type": "node"}
go("N4 the node key's record names another room", [V.OB], V.node_row("x4", ["ob"], [HA]), recs)
recs2 = copy.deepcopy(V.RECORDS); recs2.pop(NODE)
go("N4' the node key has no record at all", [V.OB], V.node_row("x4b", ["ob"], [HA]), recs2)
r5 = V.node_row("x5", ["ob"], [HA]); r5["iss"] = "vA"
go("N5 iss != kid (iss names voice vA)", [V.OB], r5)
# N6: binding to two owners in one row: only the first is read
OB2T = ST.offer("obt", NODE, ("rk:b0", "rk:a0"), "owner", NODE, "self", ("g",), cosigners=("rk:a0",))
go("N6 one binding to (rk:b0, rk:a0), only rk:a0 signed, row names vA head", [OB2T], V.node_row("x6", ["obt"], [HA]))
go("N6' same, row names vB head", [OB2T], V.node_row("x6b", ["obt"], [HB]))
# N7: owner's key record ends / owner revoked itself
RECA = ST.offer("reca", "rk:a0", "rk:a0", "registered", "rk:a0", "self", ("g",))
RVA = ST.unseat("rva", "rk:a0", "rk:a0", "registered", "rk:a0", "self", ("reca", "ob"))
go("N7 the owning key revoked itself, row after", [V.OB, RECA, RVA], V.node_row("x7", ["ob"], [HA], ("rva",)))
