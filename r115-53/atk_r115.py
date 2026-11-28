"""r115-53: root-join-signers 671a41c. python3 -I atk_r115.py <models/trust_root>"""
import sys, random
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import check_root as C
RT, B, GR, RD, nxt = C.RT, C.B, C.GR, C.RD, C.nxt
B0, H3, FORK, REC, RL, RA = C.B0, C.H3, C.FORK, C.REC, C.RL, C.RA


def go(name, bs, rd, want, gs=()):
    got = C.answer(bs, (), gs, rd, want)
    rnd, bad = random.Random(3), 0
    for _ in range(30):
        t = list(bs); rnd.shuffle(t)
        bad += C.answer(t, (), gs, rd, want) != got
    print("%-96s %s differ=%d/30" % (name, got, bad))


W = {"concluded": {"j": None}, "heads": None, "holders": None}
w = lambda *ks: {"concluded": {k: None for k in ks}, "heads": None, "holders": None}
# A1: a join adding a new holder h9 that does not sign
go("A1 join of FORK tips adds h9, h9 does not sign", FORK + [nxt("j", ("s1", "s2"), H3 + ("h4", "h5", "h9"), ("h1", "h2", "h3"), version=2)],
   RD(anchor="b0", acks=("j",)), w("j"))
go("A1' the same with h9 signing", FORK + [nxt("j", ("s1", "s2"), H3 + ("h4", "h5", "h9"), ("h1", "h2", "h3", "h9"), version=2)],
   RD(anchor="b0", acks=("j",)), w("j"))
# A1b: a new holder named by a recovery KEY of an existing holder (owner-linked), unsigned
go("A1b join seats r:h1 (h1's recovery key) as a holder, r:h1 not signing",
   FORK + [nxt("j", ("s1", "s2"), H3 + ("h4", "h5", "r:h1"), ("h1", "h2", "h3"), version=2)], RD(anchor="b0", acks=("j",)), w("j"))
# A2: one branch recovers h3 -> h3b; the other keeps h3; the join re-seats the RETIRED h3
S1 = nxt("s1", "b0", H3 + ("h4",), ("h1", "h2"))
JR = lambda holders, signers, rec=None: nxt("j", ("rc", "s1"), holders, signers, version=2,
                                            **({"recovery": rec} if rec else {}))
go("A2 join (rc, s1) seats the retired h3 again, signed h1 h2 h3b", [B0, REC, S1, JR(("h1", "h2", "h3", "h4"), ("h1", "h2", "h3b"))],
   RD(anchor="b0", acks=("j",)), w("j"))
go("A2' the same, the retired h3 signing in place of h3b", [B0, REC, S1, JR(("h1", "h2", "h3", "h4"), ("h1", "h2", "h3"))],
   RD(anchor="b0", acks=("j",)), w("j"))
go("A2'' join seats h3b (the recovered key), signed h1 h2 h3 (retired)", [B0, REC, S1, JR(("h1", "h2", "h3b", "h4"), ("h1", "h2", "h3"))],
   RD(anchor="b0", acks=("j",)), w("j"))
go("A2''' join seats h3b, signed h1 h2 h4 (h3b's voice absent)", [B0, REC, S1, JR(("h1", "h2", "h3b", "h4"), ("h1", "h2", "h4"))],
   RD(anchor="b0", acks=("j",)), w("j"))
# A3: sibling recovery capture: a reader that acked ra first, then b2, sits at b0; do removed h1 h2 grant there?
g = (GR("g1", "b0", "uX", "room", ("h1", "h2")),)
go("A3 reader acks ra then b2: removed h1,h2 grant on b0", RL + [RA], RD(anchor="b0", acks=("ra", "b2")),
   {"heads": None, "holders": None, "grant": {"g1": None}}, g)
go("A3' reader acks b2 only: the same grant", RL + [RA], RD(anchor="b0", acks=("b2",)), {"heads": None, "grant": {"g1": None}}, g)
NB = nxt("nb", "b0", ("h1", "h2", "h3"), ("h1", "h2"), version=1, seats=("n9",))
go("A3'' removed h1,h2 sign a fresh b0 successor nb; reader acked ra,b2 then nb", RL + [RA, NB], RD(anchor="b0", acks=("ra", "b2", "nb")),
   {"concluded": {"nb": None}, "heads": None, "holders": None, "seats": None})
go("A3''' reader acked b2 then nb", RL + [NB], RD(anchor="b0", acks=("b2", "nb")), {"heads": None, "holders": None, "seats": None})
# A4: thumbprint anchors with three first bundles
B0z, B0y = dict(B0, id="b0z", seats=("n2",)), B("b0y", C.F, 0, ("h1", "h2", "h9"), seats=("n3",))
go("A4 thumbs H3: b0, b0z match, b0y does not", [B0, B0z, B0y], RD(thumbs=H3), {"heads": None, "holders": None})
go("A4' thumbs H3: b0, b0z, b0w all match", [B0, B0z, dict(B0, id="b0w", seats=("n4",))], RD(thumbs=H3), {"heads": None})
go("A4'' thumbs (h1 h2 h9): only b0y", [B0, B0z, B0y], RD(thumbs=("h1", "h2", "h9")), {"heads": None, "seats": None})
go("A4''' anchor b0 and thumbs H3 (both stated)", [B0, B0z, B0y], RD(anchor="b0", thumbs=H3), {"heads": None, "seats": None})
go("A4'''' anchor names a non-first bundle (b1) with thumbs H3", [B0, B0z, nxt("b1", "b0", H3, ("h1", "h2"))], RD(anchor="b1", thumbs=H3), {"heads": None})
