"""r88-53: re-binding after an end, and routes around the owner's signature. python3 -I atk_r88.py <rk models/causal_kernel>"""
import sys, random
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import room_key_vectors as V
RK, ST, CK, R = V.RK, V.ST, V.CK, V.R
NODE, HA, HB = V.NODE, V.HA, V.HB
RULE = lambda q, P, past: ST.seat_rule(q, P, past)


def go(name, extra, r, records=V.RECORDS):
    rows = V.NODE_BASE + list(extra) + [V.kernel_row(r)]
    f = lambda S: RK.node_row_check(r, records, RK.node_row_facts(S, r, records))
    got = f(CK.concluded(CK.kept(rows), RULE))
    rnd, bad = random.Random(9), 0
    for _ in range(60):
        t = list(rows); rnd.shuffle(t)
        bad += f(CK.arrive(t, RULE)) != got
    print("%-92s %s differ=%d/60" % (name, got, bad))


OB, M1 = V.OB, V.M1
W = ST.withdraw("w", "rk:a0", "ob", ("ob",))                                   # a0 ends its binding
OB2 = ST.offer("ob2", NODE, "rk:a0", "owner", NODE, "self", ("w",), cosigners=("rk:a0",))   # a0 binds again after
go("R1 re-binding: ob withdrawn, ob2 signed by a0 with the withdrawal in its past; row under ob2", [OB, W, OB2],
   V.node_row("z1", ["ob2"], [HA]))
go("R1' the same row under the old ob", [OB, W, OB2], V.node_row("z1b", ["ob"], [HA], ("ob2",)))
# R2: a0 tidies an older duplicate signed binding AFTER re-binding: does that end ob2?
OBE = ST.offer("obe", NODE, "rk:a0", "owner", NODE, "self", ("g",), cosigners=("rk:a0",))
W2 = ST.withdraw("w2", "rk:a0", "obe", ("obe", "ob2"))
go("R2 a0 held ob and obe; withdraws ob, re-binds ob2, then withdraws old obe (w2 after ob2); row after w2",
   [OB, OBE, ST.withdraw("w", "rk:a0", "ob", ("ob", "obe")), dict(OB2, names=("w",)), W2],
   V.node_row("z2", ["ob2"], [HA], ("w2",)))
go("R2' control: same without w2, row naming ob2",
   [OB, OBE, ST.withdraw("w", "rk:a0", "ob", ("ob", "obe")), dict(OB2, names=("w",))],
   V.node_row("z2b", ["ob2"], [HA]))
# R3: a0 withdraws its ACCEPTANCE of an older binding after re-binding
OBA = ST.offer("oba", NODE, "rk:a0", "owner", NODE, "self", ("g",))
ACC = ST.accept("acc", "rk:a0", "oba")
WACC = ST.withdraw("wacc", "rk:a0", "acc", ("acc", "ob2x"))
OB2X = ST.offer("ob2x", NODE, "rk:a0", "owner", NODE, "self", ("acc",), cosigners=("rk:a0",))
go("R3 a0 bound by acceptance (oba+acc), signs ob2x, then withdraws acc; row after wacc under ob2x",
   [OBA, ACC, OB2X, WACC], V.node_row("z3", ["ob2x"], [HA], ("wacc",)))
# R4: a new owner after the old owner withdrew
OB3 = ST.offer("ob3", NODE, "rk:b0", "owner", NODE, "self", ("w",), cosigners=("rk:b0",))
go("R4 a0 withdraws ob; rk:b0 signs ob3 after; row under ob3, vB head", [OB, W, OB3], V.node_row("z4", ["ob3"], [HB]))
go("R4' both live (no withdrawal): row under ob3", [OB, dict(OB3, names=("g",))], V.node_row("z4b", ["ob3"], [HB], ("ob",)))
# R5: re-binding after the owner's revocation of the owner seat (an unseat)
UO = ST.unseat("uo", "rk:a0", "rk:a0", "owner", NODE, "seat", ("ob",), under="ob")
OB5 = ST.offer("ob5", NODE, "rk:a0", "owner", NODE, "self", ("uo",), cosigners=("rk:a0",))
go("R5 a0 revokes the owner seat (uo), then signs ob5 after it; row under ob5", [OB, UO, OB5], V.node_row("z5", ["ob5"], [HA]))
# R6: a re-binding concurrent with the old binding's withdrawal (neither in the other's past); row names both
OB6 = ST.offer("ob6", NODE, "rk:a0", "owner", NODE, "self", ("ob",), cosigners=("rk:a0",))
go("R6 ob6 signed concurrent with w (ob's withdrawal); row names ob6 and w", [OB, W, OB6], V.node_row("z6", ["ob6"], [HA], ("w",)))
# routes around the owner's signature
CS = ST.cosign("cs", "rk:b0", "obx", ("obx",))
OBX = ST.offer("obx", NODE, "rk:b0", "owner", NODE, "self", ("g",))
go("S1 a cosign row by rk:b0 naming the unsigned binding", [OBX, CS], V.node_row("s1", ["obx"], [HB], ("cs",)))
SACC = ST.accept("sacc", "rk:b0", None, ("g",), scope="owner", obj=NODE)
OBS = ST.offer("obs", NODE, "rk:b0", "owner", NODE, "self", ("sacc",))
go("S2 rk:b0's standing acceptance of `owner` over the node, named by the node's offer", [SACC, OBS], V.node_row("s2", ["obs"], [HB]))
OBY = ST.offer("oby", NODE, "rk:b0", "owner", NODE, "self", ("g",))
ACCY = ST.accept("accy", "rk:a0", "oby")
go("S3 an acceptance of oby by a0 (not the key oby names)", [OBY, ACCY], V.node_row("s3", ["oby"], [HB], ("accy",)))
OBG = ST.offer("obg", "vB", "rk:b0", "owner", NODE, "group", ("g",), head=("g",), policy="community_invite", cosigners=("vC", "rk:b0"))
go("S4 a counted (group) owner offer over the node key, signed by rk:b0", [OBG], V.node_row("s4", ["obg"], [HB]))
OBN = ST.offer("obn", "rk:b0", "rk:b0", "owner", NODE, "self", ("g",))
go("S5 the owner writes the binding itself (signer rk:b0, Conf self over the node key)", [OBN], V.node_row("s5", ["obn"], [HB]))
