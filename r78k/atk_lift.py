"""Lift with the remover's device key objecting. python3 -I atk_lift.py <models/causal_kernel>"""
import sys, random
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import check_room_keys as C, check_key_person as KP
ST, CK, WN = C.ST, C.CK, C.WN
SM = KP.found("Sm1", "m1"); AD = KP.add("am1b", "Sm1", "m1b", ("m1",), ("Sm1",))
def run(name, objectors):
    objs = [WN.answer("o_" + k, k, "x", "object", ("x", "am1b")) for k in objectors]
    rows = C.PV + [SM, AD, C.XL] + objs + [C.lift("rs", "m2", "AG", "x", ("x",), tuple(o["id"] for o in objs))]
    got = bool(CK.concluded(CK.kept(rows), C.RULE).C.get("rs"))
    rnd, bad = random.Random(1), 0
    for _ in range(60):
        t = rows[1:]; rnd.shuffle(t)
        bad += bool(CK.arrive([rows[0]] + t, C.RULE).C.get("rs")) != got
    print("%-60s rs=%s differ=%d/60" % (name, got, bad))
run("objections m2, m3 (2 of 4, the author apart)", ("m2", "m3"))
run("objections m1b (the remover's device), m2, m3", ("m1b", "m2", "m3"))
run("objections m1 (the remover itself), m2, m3", ("m1", "m2", "m3"))
run("objections m2, m3, m4", ("m2", "m3", "m4"))

# K10: the room's agent key AG is also a device key of member m1's own self roster: does AG's signature vote for m1?
SA = KP.add("aAG", "Sm1", "AG", ("m1",), ("Sm1",))
def adm(i, signers, extra):
    return ST.offer(i, signers[0], "y", "member", "g", "group", ("ag",) + extra, head=("ag",), policy="community_invite",
                    cosigners=tuple(signers[1:]) + ("y",))
for name, sig, ex in (("AG, m2, m3, m4 (AG a key of m1's roster)", ("AG", "m2", "m3", "m4"), [SM, SA]),
                      ("AG, m2, m3, m4 (AG no roster key)", ("AG", "m2", "m3", "m4"), []),
                      ("m1, m2, m3, m4", ("m1", "m2", "m3", "m4"), [])):
    rows = C.PV + ex + [adm("ay", sig, tuple(r["id"] for r in ex))]
    got = bool(CK.concluded(CK.kept(rows), C.RULE).C.get("ay"))
    rnd, bad = random.Random(1), 0
    for _ in range(60):
        t = rows[1:]; rnd.shuffle(t)
        bad += bool(CK.arrive([rows[0]] + t, C.RULE).C.get("ay")) != got
    print("K10 %-56s ay=%s differ=%d/60" % (name, got, bad))
