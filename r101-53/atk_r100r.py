"""r100-53, per reader: key-person 09923a2. python3 -I atk_r100r.py <kp models/causal_kernel>"""
import sys, random
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import check_key_person as KP
sys.path.insert(0, '/tmp/claude-1000/-home-emoore-CIRISKernel/9f476e19-79a3-4f60-8019-6f13a6523575/scratchpad/r101-53'); import rdr as RD
ST, CK, WN = KP.ST, KP.CK, KP.WN
RULE = KP.RULE
found, add, evict, admit_z = KP.found, KP.add, KP.evict, KP.admit_z
READERS = ("p4", None, "x")
def show(name, rows, f, readers=READERS):
    out = []
    base = rows
    for rd in readers:
        rows = RD.with_reader(ST, base, rd)
        g = lambda S: f(ST.reader_state(S, rd))
        got = g(CK.concluded(CK.kept(list(rows)), RULE))
        rnd, bad = random.Random(29), 0
        for _ in range(30):
            t = list(rows); rnd.shuffle(t)
            bad += g(CK.arrive(t, RULE)) != got
        out.append("%s:%s%s" % (rd, got, "" if not bad else "(differ %d/30)" % bad))
    print("%-92s %s" % (name, "  ".join(out)))
C = lambda rid: (lambda S: bool(S.C.get(rid)))
GW = KP.GW
EVT = evict("evt", "S1", "p1", ("p1b", "p1c"), ("a1c",))
RX = ST.offer("S1r", "p1", ("p1", "x"), "self", "@", "self", cosigners=("x",))
Z = lambda names, sig=("p1b", "p2", "p3"): admit_z(sig, names)
show("X1 admit naming a1c", GW + [RX, Z(("a1c",))], C("az"))
show("X2 admit naming a1c, S1r", GW + [RX, Z(("a1c", "S1r"))], C("az"))
show("X4 evicted, admit naming evt, S1r", GW + [RX, EVT, Z(("evt", "S1r"))], C("az"))
# P: p4, whose line took S1, later signs any row with S1r in its past (a tip-following client)
N4 = ST.R("n4", "note", "p4", ("S1r", "gc"))
show("P1 p4 signs a note naming the tips (S1r, gc); then admit naming a1c, S1r, n4", GW + [RX, N4, Z(("a1c", "S1r", "n4"))], C("az"))
show("P1' same, admit naming only a1c and S1r (n4 not in the count's past)", GW + [RX, N4, Z(("a1c", "S1r"))], C("az"))
V4 = ST.R("v4", "note", "p4", ("S1r",))
show("P2 p4 signs a row naming only S1r; admit naming a1c, S1r", GW + [RX, V4, Z(("a1c", "S1r"))], C("az"))
# P3: p4 cosigns the honest admission itself, which names S1r (it is among the tips)
Z4 = admit_z(("p1b", "p2", "p4"), ("a1c", "S1r"))
show("P3 p4 cosigns the admission naming a1c, S1r", GW + [RX, Z4], C("az"))
# P4: does the line take up S1 at all if p4's only row is the room's founding gc (names a1b, S2.. not S1's later rows)?
show("P4 person_keys(p1) per reader, rival held", GW + [RX], lambda S: sorted(ST.person_keys(S, "p1")))
show("P5 x + p2 + p3 admit naming S1r, a1c", GW + [RX, Z(("S1r", "a1c"), ("x", "p2", "p3"))], C("az"))
# T: the two-key person, readers m4 (its line took S through gr) and a fresh reader
GS, GD1 = KP.GS, KP.GD1
GR = ST.offer("gr", "g1", ("g1", "m2", "m3", "m4"), "member", "@", "self", cosigners=("m2", "m3", "m4"), names=("d1",))
RV2 = found("Sr", "g1"); TX2 = add("tx2", "Sr", "x9", ("g1",), ("Sr",))
def adm(signers, names):
    return ST.offer("az", signers[0], "z", "member", "gr", "group", ("gr",) + tuple(names), head=("gr",), policy="community_invite",
                    cosigners=tuple(signers[1:]) + ("z",))
B2 = [GS, GD1, GR, RV2, TX2]
show("T3 k1+m2+m3 admit naming tx2", B2 + [adm(("k1", "m2", "m3"), ("tx2",))], C("az"), ("m4", None))
show("T3g g1+m2+m3 admit naming tx2 (the thief genesis)", B2 + [adm(("g1", "m2", "m3"), ("tx2",))], C("az"), ("m4", None))
show("T3x x9+m2+m3 admit naming tx2", B2 + [adm(("x9", "m2", "m3"), ("tx2",))], C("az"), ("m4", None))
M4N = ST.R("m4n", "note", "m4", ("tx2", "gr"))
show("T6 m4 signs a note naming the tips (tx2, gr); k1+m2+m3 admit naming tx2", B2 + [M4N, adm(("k1", "m2", "m3"), ("tx2",))], C("az"), ("m4", None))
