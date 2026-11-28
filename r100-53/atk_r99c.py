"""r99-53 part 3: key-person 89558f5, the thief's counted take-up. python3 -I atk_r99c.py <kp models/causal_kernel>"""
import sys, random
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import check_key_person as KP
ST, CK, WN = KP.ST, KP.CK, KP.WN
RULE, RULE_W = KP.RULE, KP.RULE_W
found, add, evict, admit_z = KP.found, KP.add, KP.evict, KP.admit_z
def show(name, rows, f, rule=RULE):
    got = f(CK.concluded(CK.kept(list(rows)), rule))
    rnd, bad = random.Random(19), 0
    for _ in range(60):
        t = list(rows); rnd.shuffle(t)
        bad += f(CK.arrive(t, rule)) != got
    print("%-100s %s differ=%d/60" % (name, got, bad))
C = lambda rid: (lambda S: bool(S.C.get(rid)))
GW, GEV = KP.GW, KP.GEV
RIV = found("S1r", "p1")
TX = add("tx", "S1r", "x9", ("p1",), ("S1r",))                     # the thief's counted add of its own device
show("T1 3-key: thief (live p1) founds S1r and adds x9 by its count; tx concludes?", GW + [RIV, TX], C("tx"))
show("T1' honest p1b+p2+p3 admit z naming a1c and tx", GW + [RIV, TX, admit_z(("p1b", "p2", "p3"), ("a1c", "tx"))], C("az"))
show("T1'' the same naming only a1c (the thief's rows not in its past)", GW + [RIV, TX, admit_z(("p1b", "p2", "p3"), ("a1c",))], C("az"))
EVT = evict("evt", "S1", "p1", ("p1b", "p1c"), ("a1c",))
show("T2 the devices evict p1 from S1; admit naming evt and tx", GW + [RIV, TX, EVT, admit_z(("p1b", "p2", "p3"), ("evt", "tx"))], C("az"))
show("T2' x9 (thief device) + p2 + p3 after the eviction", GW + [RIV, TX, EVT, admit_z(("x9", "p2", "p3"), ("evt", "tx"))], C("az"))
# the two-key person: g1 (stolen) and k1 (honest); room members g1's person, m2, m3, m4
GS, GD1 = KP.GS, KP.GD1
GR = ST.offer("gr", "g1", ("g1", "m2", "m3", "m4"), "member", "@", "self", cosigners=("m2", "m3", "m4"), names=("d1",))
RV2 = found("Sr", "g1"); TX2 = add("tx2", "Sr", "x9", ("g1",), ("Sr",))
def adm(signers, names):
    return ST.offer("az", signers[0], "z", "member", "gr", "group", ("gr",) + tuple(names), head=("gr",), policy="community_invite",
                    cosigners=tuple(signers[1:]) + ("z",))
base2 = [GS, GD1, GR, RV2, TX2]
show("T3 2-key: thief g1 founds Sr + counted add; honest k1+m2+m3 admit z naming tx2", base2 + [adm(("k1", "m2", "m3"), ("tx2",))], C("az"))
EW = WN.secs("self_roster_evict")
lone = [WN.opener("op", "k1", "self_roster_evict", "S", ("d1",), target="g1"), WN.answer("og", "g1", "op", "object", ("op",)),
        WN.receipt("r", "k1", "op", 0), WN.landing("L", "k1", "op", "r", "landed", EW, ("og",))]
show("T4 2-key: k1 lone-evicts g1, the thief g1 objects: outcome", base2 + lone, lambda S: WN.outcome(S, "op", "recount"), RULE_W)
show("T4' ... and k1+m2+m3 admit z naming L and tx2", base2 + lone + [adm(("k1", "m2", "m3"), ("L", "tx2"))], C("az"), RULE_W)
show("T5 control 2-key, no rival: k1+m2+m3 admit z", [GS, GD1, GR, adm(("k1", "m2", "m3"), ("d1",))], C("az"))
