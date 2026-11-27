import sys, random
sys.path.insert(0, sys.argv[1])
sys.dont_write_bytecode = True
import check_room_keys as C
ST, CK, WN = C.ST, C.CK, C.WN
OBJ = "g"
M = ("m1", "m2", "m3", "m4")

def run(name, rows, asks, concl=()):
    S = CK.concluded(CK.kept(list(rows)), C.RULE)
    def rd(S):
        Q = ST.Seats(S)
        return ({i: bool(S.C.get(i)) for i in concl}, sorted(Q.roster(OBJ)),
                [(k, sc, Q.stands(k, sc, OBJ)) for k, sc in asks])
    got = rd(S)
    rnd = random.Random(7); bad = 0
    for _ in range(60):
        t = list(rows[1:]); rnd.shuffle(t)
        if rd(CK.arrive([rows[0]] + t, C.RULE)) != got: bad += 1
    print("%-66s %s  differ=%d/60" % (name, got, bad))

for priv, W in (("private", C.PV), ("public", C.PB)):
    # B1: founder m4 writes a standing acceptance and withdraws it (a decline, no end); then an outsider X writes an
    # offer naming it (it concludes nothing). Does m4's withdrawal become an end of its stay?
    sa = ST.accept("sa", "m4", None, ("ag",), scope="member", obj=OBJ)
    w = ST.withdraw("w", "m4", "sa", ("sa",))
    x = ST.offer("xo", "X", "m4", "member", OBJ, "self", ("sa",))
    run("B1 %s: m4 withdraws unused standing acc" % priv, W + [sa, w], [("m4", "member"), ("m4", "moderate")], ("w",))
    run("B1 %s: + outsider X's non-concluding offer naming sa" % priv, W + [sa, w, x], [("m4", "member"), ("m4", "moderate")], ("w", "xo"))
    # B1b: the same with a counted (concluding) agent offer naming sa
    xa = ST.offer("xa", "m1", "m4", "guest", OBJ, "group", ("sa",), head=("sa",), policy="community_invite", cosigners=("m2", "m3"))
    run("B1b %s: + counted `guest` offer naming sa" % priv, W + [sa, w, xa], [("m4", "member")], ("xa",))
    # B2: honest re-admission after resignation: new offer, q cosigns it, after the end
    run("B2 %s: q resigns, then new admission (q cosigns) naming wq" % priv, W + [C.WQ, C.rejoin("aq2", "q", ("wq",))], [("q", "member")], ("aq2",))
    acc_after = [C.WQ, C.admit("aq2", "q", M, ("wq",), joiner=False), ST.accept("a2", "q", "aq2")]
    run("B2b %s: q resigns, new offer, NEW acceptance after" % priv, W + acc_after, [("q", "member")], ("aq2", "a2"))
    # B3: removed from agent, admitted as member (over-bar check)
    run("B3 %s: AG counted out of agent; count admits AG as member" % priv, W + [C.XA, C.rejoin("am", "AG", ("xa",))], [("AG", "member")], ("am",))
    # B4: a founder (seated by founding signature only) resigns: is it out?
    run("B4 %s: founder m4 withdraws founding row" % priv, W + [ST.withdraw("w4", "m4", "g", ("ag",))], [("m4", "member")], ("w4",))
    # B5: q seated by an admission it cosigned (no acceptance row), withdraws it: an end?
    run("B5 %s: q (cosigned aq) withdraws aq; later admission" % priv, W + [C.WQ, C.rejoin("aq2", "q", ("wq",))], [("q", "member")], ("wq", "aq2"))
    # B6: z declines, then accepts the declined offer afterwards (self), then a re-admission
    oz = C.admit("oz", "z", M, ("ag",), joiner=False)
    rows = W + [oz, ST.withdraw("wz", "z", "oz", ("oz",)), ST.accept("az", "z", "oz", ("wz",)), C.admit("oz2", "z", M, ("az",))]
    run("B6 %s: z declines, accepts declined offer later, readmit" % priv, rows, [("z", "member")], ("wz", "az", "oz2"))

# RK2: room of one (single founder), admission by the founder's count
g1 = ST.found("g", "f", ("f",), membership="private")
a1 = ST.offer("a1", "f", "q", "member", OBJ, "group", ("g",), head=("g",), policy="community_invite", cosigners=("q",))
run("R1 room of one: f's count admits q", [g1, a1], [("q", "member")], ("a1",))
run("R1b room of one: f's count removes q, readmit", [g1, a1, ST.unseat("x1", "f", "q", "member", OBJ, "group", ("a1",), head=("a1",), policy="community_remove"),
     ST.offer("a2", "f", "q", "member", OBJ, "group", ("x1",), head=("x1",), policy="community_invite", cosigners=("q",))], [("q", "member")], ("x1", "a2"))
# lone duty holder's own conferral of a duty (one-founder room declares duties via lone founder)
gd = ST.found("g", "f", ("f",), {"moderate": ("f",)})
run("R2 lone duty holder confers moderate alone (self)", [gd, a1, ST.offer("cm", "f", "q", "moderate", OBJ, "self", ("a1",), cosigners=("q",))],
    [("q", "moderate")], ("a1", "cm"))
run("R2b lone duty holder confers `duty` alone (self)", [gd, a1, ST.offer("cd", "f", "q", "duty", OBJ, "self", ("a1",), cosigners=("q",))],
    [("q", "duty"), ("q", "member")], ("cd",))
for sc in ("member:x", "agent:x", "founder:x", "guest"):
    run("R3 removed q, m1 alone offers `%s`" % sc, C.PV + [C.XQ, ST.offer("o", "m1", "q", sc, OBJ, "self", ("xq",), cosigners=("q",))],
        [("q", "member"), ("q", "agent"), ("q", sc)], ("o",))
