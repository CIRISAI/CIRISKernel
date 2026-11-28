"""r96-53: key-person a96ba2f. python3 -I atk_r96.py <kp models/causal_kernel>"""
import sys, random
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import check_key_person as KP
ST, CK = KP.ST, KP.CK
RULE = KP.RULE
found, add, evict, admit_z, SP, GC = KP.found, KP.add, KP.evict, KP.admit_z, KP.SP, KP.GC


def stable(rows, f):
    got = f(CK.concluded(CK.kept(list(rows)), RULE))
    rnd, bad = random.Random(11), 0
    for _ in range(60):
        t = list(rows); rnd.shuffle(t)
        bad += f(CK.arrive(t, RULE)) != got
    return got, bad


def conc(name, rows, rid):
    got, bad = stable(rows, lambda S: bool(S.C.get(rid)))
    print("%-92s %s=%s differ=%d/60" % (name, rid, got, bad))


def show(name, rows, f):
    got, bad = stable(rows, f)
    print("%-92s %s differ=%d/60" % (name, got, bad))

# p1's roster S1 with two devices p1b, p1c; the devices evict the genesis key p1
P1B = KP.P1B
P1C = add("a1c", "S1", "p1c", ("p1", "p1b"), ("a1b",))
EVG = evict("evg", "S1", "p1", ("p1b", "p1c"), ("a1c",))
GCx = dict(GC, names=("a1b", "S2", "S3", "S4"))
W = [SP[1], SP[2], SP[3], SP[4], P1B, GCx, P1C, EVG]
conc("E0 the devices p1b+p1c evict p1 (3-key roster, 2 of 3 with p1 no voice)", W, "evg")
conc("E1 then p1+p2+p3 admit z (p1 an evicted genesis: no voice)", W + [admit_z(("p1", "p2", "p3"), ("evg",))], "az")
conc("E1' p1b+p2+p3 admit z (a live device speaks for the person)", W + [admit_z(("p1b", "p2", "p3"), ("evg",))], "az")
# route 1: p1 founds a second roster of the same identity
S1N = found("S1n", "p1")
conc("E2 p1 founds S1n (same identity p1) after its eviction; p1+p2+p3 admit z", W + [dict(S1N, names=("evg",)),
     admit_z(("p1", "p2", "p3"), ("evg", "S1n"))], "az")
show("E2' person_keys(p1) after the second roster", W + [dict(S1N, names=("evg",))], lambda S: sorted(ST.person_keys(S, "p1")))
# route 2: p1 adds a new device to its own new roster and votes through it
AN = add("an", "S1n", "p1n", ("p1",), ("S1n",))
conc("E3 p1's new device p1n (in S1n) + p2 + p3 admit z", W + [dict(S1N, names=("evg",)), AN,
     admit_z(("p1n", "p2", "p3"), ("an",))], "az")
conc("E3' p1, p1b, p1n all sign with p2: one voice? (needs 3 of 4)", W + [dict(S1N, names=("evg",)), AN,
     admit_z(("p1", "p1b", "p1n", "p2"), ("an",))], "az")
# route 3: re-admitted to S1 by the devices' count
RE = add("re", "S1", "p1", ("p1b", "p1c"), ("evg",))
conc("E4 the devices re-admit p1 to S1 (the roster's count); p1+p2+p3 admit z", W + [RE, admit_z(("p1", "p2", "p3"), ("re",))], "az")
# eviction counts
S = found("S", "g1"); D1 = add("d1", "S", "k1", ("g1",), ("S",)); D2 = add("d2", "S", "k2", ("g1", "k1"), ("d1",))
conc("V1 2-key roster: the device k1 evicts the genesis g1 alone", [S, D1, evict("v", "S", "g1", ("k1",), ("d1",))], "v")
conc("V2 2-key roster: the genesis g1 evicts the device k1 alone (a stolen device)", [S, D1, evict("v", "S", "k1", ("g1",), ("d1",))], "v")
conc("V3 3-key roster: k1 alone evicts g1", [S, D1, D2, evict("v", "S", "g1", ("k1",), ("d2",))], "v")
conc("V4 3-key roster: g1 alone evicts k1", [S, D1, D2, evict("v", "S", "k1", ("g1",), ("d2",))], "v")
conc("V5 3-key roster: g1+k2 evict k1", [S, D1, D2, evict("v", "S", "k1", ("g1", "k2"), ("d2",))], "v")
conc("V6 3-key roster: k1 signs its own eviction with g1 (k1 no voice of it)", [S, D1, D2, evict("v", "S", "k1", ("g1", "k1"), ("d2",))], "v")
conc("V7 2-key roster: g1 adds a third key alone (k1 stolen, not signing)", [S, D1, add("d3", "S", "k3", ("g1",), ("d1",))], "d3")
# nodes_of and person_keys
NODE = "nd"
OB = ST.offer("ob", NODE, "p1b", "owner", NODE, "self", ("a1b",), cosigners=("p1b",))
base = [SP[1], P1B, OB]
show("N1 nodes_of(p1b) with a live binding", base, lambda S: sorted(ST.nodes_of(S, "p1b")))
show("N2 the binding withdrawn by its owner", base + [ST.withdraw("w", "p1b", "ob", ("ob",))], lambda S: sorted(ST.nodes_of(S, "p1b")))
show("N3 the owner seat unseated (revoked) by its owner", base + [ST.unseat("uo", "p1b", "p1b", "owner", NODE, "seat", ("ob",), under="ob")],
     lambda S: sorted(ST.nodes_of(S, "p1b")))
show("N4 the node's own withdrawal of the binding", base + [ST.withdraw("w", NODE, "ob", ("ob",))], lambda S: sorted(ST.nodes_of(S, "p1b")))
show("N5 an unsigned binding to p1 (the node's own offer)", [SP[1], ST.offer("ob", NODE, "p1", "owner", NODE, "self", ("S1",))],
     lambda S: sorted(ST.nodes_of(S, "p1")))
show("N6 two owners (p1b, p2)", base + [SP[2], ST.offer("ob2", NODE, "p2", "owner", NODE, "self", ("S2",), cosigners=("p2",))],
     lambda S: sorted(ST.nodes_of(S, "p1b")))
EVB = evict("evb", "S1", "p1b", ("p1", "p1c"), ("a1c",))
show("N7 the owner p1b evicted from its roster (the node still its?)", [SP[1], P1B, P1C, OB, EVB], lambda S: sorted(ST.nodes_of(S, "p1b")))
show("K1 person_keys(p1), devices p1b p1c", [SP[1], P1B, P1C], lambda S: sorted(ST.person_keys(S, "p1")))
show("K2 person_keys(p1) after evicting p1b", [SP[1], P1B, P1C, EVB], lambda S: sorted(ST.person_keys(S, "p1")))
RVc = ST.unseat("rvc", "p1c", "p1c", "registered", "p1c", "self", ("rcc",)); RCc = ST.offer("rcc", "p1c", "p1c", "registered", "p1c", "self", ("a1c",))
show("K3 person_keys(p1) after p1c revoked itself", [SP[1], P1B, P1C, RCc, RVc], lambda S: sorted(ST.person_keys(S, "p1")))
show("K4 person_keys(p1) after p1 evicted by its devices", [SP[1], P1B, P1C, EVG], lambda S: sorted(ST.person_keys(S, "p1")))
show("K5 person_keys(p1) with p1b also in p2's roster", [SP[1], SP[2], P1B, add("x", "S2", "p1b", ("p2",), ("S2",))],
     lambda S: sorted(ST.person_keys(S, "p1")))
