"""r78k: attacks on the r74 fixes. python3 -I atk_r78k.py <kp models/causal_kernel> <rk models/causal_kernel>"""
import sys, random, copy, subprocess, json
which = sys.argv[3] if len(sys.argv) > 3 else "both"
if which in ("rk", "both") and len(sys.argv) > 3:
    pass

def orders(rows, f, n=60, seed=5, first=True):
    got = f(rows)
    rnd, bad = random.Random(seed), 0
    for _ in range(n):
        t = list(rows[1:] if first else rows); rnd.shuffle(t)
        if f(([rows[0]] if first else []) + t, arrive=True) != got: bad += 1
    return got, bad

if which == "rk":
    sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
    import room_key_vectors as V
    RK, ST, CK = V.RK, V.ST, V.CK
    NODE, HA, HB = V.NODE, V.HA, V.HB
    def go(name, extra, r, records=V.RECORDS):
        def f(rows, arrive=False):
            S = CK.arrive(rows, lambda q, P, past: ST.seat_rule(q, P, past)) if arrive else \
                CK.concluded(CK.kept(rows), lambda q, P, past: ST.seat_rule(q, P, past))
            return RK.node_row_check(r, records, RK.node_row_facts(S, r, records))
        got, bad = orders(V.NODE_BASE + list(extra) + [V.kernel_row(r)], f)
        print("%-86s %s differ=%d/60" % (name, got, bad))
    # B1: an unsigned duplicate binding of the same owner beside the signed one; the owner withdraws the SIGNED one
    # concurrently at head m1; the row at m1's head names the duplicate (rule 4 read on the duplicate's ends only)
    OBD = ST.offer("obd", NODE, "rk:a0", "owner", NODE, "self", ("g",))          # the node's own offer, a0 never signed
    go("B0 control: signed ob withdrawn at m1, row at m1 under ob (n3)", [V.OB, V.M1, V.WOB_C],
       V.node_row("y0", ["ob"], [HA], ("m1",)))
    go("B1 same, row at m1 under the unsigned duplicate obd", [V.OB, OBD, V.M1, V.WOB_C],
       V.node_row("y1", ["obd"], [HA], ("m1",)))
    go("B1' withdrawal of ob in the row's past, row under obd", [V.OB, OBD, V.M1, V.WOB_C],
       V.node_row("y1b", ["obd"], [HA], ("wob",)))
    # B2: a person's room key (record identity_type person) signs a node-style row under a binding of its own
    OBP = ST.offer("obp", "rk:a1", "rk:b0", "owner", "rk:a1", "self", ("g",), cosigners=("rk:b0",))
    r = V.node_row("y2", ["obp"], [HB], kid="rk:a1")
    go("B2 rk:a1 (a person's room key of vA) as a node owned by rk:b0 (vB)", [OBP], r)
    # B3: the owner seat held by acceptance rather than cosignature
    OBA = ST.offer("oba", NODE, "rk:b0", "owner", NODE, "self", ("g",))
    ACC = ST.accept("acc", "rk:b0", "oba")
    go("B3 owner seat by rk:b0's separate acceptance", [OBA, ACC], V.node_row("y3", ["oba"], [HB], ("acc",)))
    go("B3' the acceptance concurrent with the row (not in its past)", [OBA, ACC], V.node_row("y3b", ["oba"], [HB]))
    # B4: the owner's acceptance withdrawn concurrently, row at the withdrawal's head
    M2 = ST.R("m2", "note", "vC", ("acc",))
    WACC = ST.withdraw("wacc", "rk:b0", "acc", ("acc", "m2"))
    go("B4 acceptance withdrawn at head m2 (concurrent), row at m2 under oba", [OBA, ACC, M2, WACC],
       V.node_row("y4", ["oba"], [HB], ("m2",)))
    # B5: node revoked concurrently with the row, row at the revocation's head (rule 4 via `names`)
    M3 = ST.R("m3", "note", "vB", ("ob",))
    RVN = ST.unseat("rvn", NODE, NODE, "registered", NODE, "self", ("recn", "m3"), head=("m3",))
    go("B5 node revokes itself at head m3, concurrent; row at m3", [V.OB, V.RECN, M3, RVN],
       V.node_row("y5", ["ob"], [HA], ("m3", "recn")))
    sys.exit(0)

sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import check_key_person as KP, check_room_keys as C
ST, CK, WN = KP.ST, KP.CK, KP.WN
RULE, RULE_W = KP.RULE, KP.RULE_W
found, add, evict, admit_z, BASE = KP.found, KP.add, KP.evict, KP.admit_z, KP.BASE

def conc(name, rows, rid, rule=RULE):
    def f(rs, arrive=False):
        S = CK.arrive(rs, rule) if arrive else CK.concluded(CK.kept(rs), rule)
        return bool(S.C.get(rid))
    got, bad = orders(rows, f, first=False)
    print("%-86s %s=%s differ=%d/60" % (name, rid, got, bad))

# P1: two rosters founded by one genesis key are one person; a device in rosters of two genesis keys is none
S1x = found("S1x", "p1"); D1 = add("ad1", "S1", "dd", ("p1", "p1b"), ("a1b",)); D2 = add("ad2", "S1x", "dd", ("p1",), ("S1x",))
conc("P1 dd in S1 and S1x (both p1's): dd+p2+p3 admit z", BASE + [S1x, D1, D2, admit_z(("dd", "p2", "p3"), ("ad1", "ad2"))], "az")
D3 = add("ad3", "S2", "dd", ("p2",), ("S2",))
conc("P1' dd in S1 (p1) and S2 (p2): dd+p2+p3 admit z (dd no voice)", BASE + [D1, D3, admit_z(("dd", "p2", "p3"), ("ad1", "ad3"))], "az")
conc("P1'' same, dd+p3+p4 (p2 not signing)", BASE + [D1, D3, admit_z(("dd", "p3", "p4"), ("ad1", "ad3"))], "az")
# P2: a genesis key that revoked itself: its devices speak for no one; is the base still counted with it?
REC = ST.offer("rec", "p1", "p1", "registered", "p1", "self")
RV = ST.unseat("rv", "p1", "p1", "registered", "p1", "self", ("rec", "a1b"))
conc("P2 p1 revoked; p2+p3+p4 admit z (base still 4?)", BASE + [REC, RV, admit_z(("p2", "p3", "p4"), ("rv",))], "az")
# P3: two members merge: p2 (no own roster) joins p1's roster as a device; does the base shrink?
GC2 = ST.offer("gc", "p1", ("p1", "q2", "p3", "p4"), "member", "@", "self", cosigners=("q2", "p3", "p4"), names=("a1b", "S3", "S4"))
B2 = [KP.SP[1], KP.SP[3], KP.SP[4], KP.P1B, GC2]
MQ = add("amq", "S1", "q2", ("p1", "p1b"), ("gc",))
conc("P3 control: q2 (own key, no roster) a member; p1+q2+p3 admit z (3 of 4)", B2 + [admit_z(("p1", "q2", "p3"))], "az")
conc("P3' q2 becomes p1's device after the founding: p1+q2+p3 (now 2 persons of 3)", B2 + [MQ, admit_z(("p1", "q2", "p3"), ("amq",))], "az")
conc("P3'' same, p1+p3 only", B2 + [MQ, admit_z(("p1", "p3"), ("amq",))], "az")

# W1: a window opened by an outsider key k7 over a self roster (keys counted); its own withdrawal
def wout(rows):
    S = CK.concluded(CK.kept(list(rows)), RULE_W)
    return S.C.get("op"), WN.outcome(S, "op", "recount")
S1 = found("S1", "p1"); A = add("a1b", "S1", "p1b", ("p1",), ("S1",))
op = dict(WN.opener("op", "k7", "self_roster_add", "S1", ("a1b",)), to=("k7",))
print("W1 outsider k7 opens self_roster_add over S1 (concludes?, outcome):", wout([S1, A, op]))
print("W1 k7 withdraws its own proposal:", wout([S1, A, op, WN.answer("w", "k7", "op", "withdraw", ("op",))]))
# W2: the opener revoked its key, then withdraws under it (Python: rep None -> sentinel equal to the opener's)
op2 = dict(WN.opener("op", "p1", "proposal@others", "gc", ("gc",)))
WB = KP.WBASE
RECp = ST.offer("rec", "p1", "p1", "registered", "p1", "self", ("op",))
RVp = ST.unseat("rv", "p1", "p1", "registered", "p1", "self", ("rec",))
print("W2 base:", wout(WB))
print("W2 p1 (opener) revokes, then answers withdraw:", wout(WB + [RECp, RVp, WN.answer("w", "p1", "op", "withdraw", ("op", "rv"))]))
print("W2' p1 withdraws, not revoked:", wout(WB + [WN.answer("w", "p1", "op", "withdraw", ("op",))]))
