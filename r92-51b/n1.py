import sys, os
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import check_key_view as CV
ST, KE, CK, CH = CV.ST, CV.KE, CV.CK, CV.CH
def run(name, sr, kr, reader=None, probe="x", seat=None, rule="seat"):
    got, fin = CV.cut_answer(rule, sr, kr, reader, probe, seat)
    print(name); print("   x concluded: %s | final: %s" % (got, fin))
R = CH.ROOM; recs = CV.recs; rack = CV.rack
X0 = CV.x_row("ABCDE", at=0)
# N1: a "roster end" made in a room the attacker owns: three keys of its own, a counted removal of one of them,
# carrying rend_of = C and ra 0
Q = ST.found("Q", "T1", ("T1", "T2", "T3"), {"moderate": ("T1",)}, cosigners=("T2", "T3"))
NQ = ST.unseat("nq", "T1", "T3", "member", "Q", "group", ("Q",), head=("Q",), policy="community_remove", cosigners=("T2",),
               rend_of="C", ra=0)
run("N1a control: C's honest vote x at 0", R + [X0], recs())
run("N1b a counted removal in the attacker's own room Q, carrying rend_of C, ra 0", R + [X0, Q, NQ],
    recs() + [KE.rec("k" + k, k, 0, None, typ="pseudonym") for k in ("T1", "T2", "T3")])
NG = ST.unseat("ng", "A", "F", "member", "g", "group", ("aG",), head=("aG",), policy="community_remove",
               cosigners=("B", "D", "E", "G"), rend_of="C", ra=0)
run("N1c the same through an unrelated removal in the room itself (F removed by five), rend_of C", R + [X0, NG], recs())
# N2: a multi-key person (P1, P2, C); the thief rotates C to T naming nothing: is it an end the roster can undo?
KT = KE.rec("kT", "T", 0, None, typ="pseudonym")
QT0 = KE.rec("qT", "T", 1, None, names=("kC",), succ_of="C", at_old=1, typ="pseudonym")
run("N2a a multi-key person's C, rotated by the thief to T naming nothing (P's roster present)", R + [X0] + CV.PROSTER,
    recs() + [KT, QT0])
REND_T = ST.unseat("eT", "P1", "C", "member", "P", "group", ("P",), head=("P",), policy="community_remove",
                   cosigners=("P2",), rend_of="T", ra=0)
run("N2b ... P's roster (P1, P2) ends T from 0 by its count: x still cut (the thief's rotation stays an end of C)",
    R + [X0] + CV.PROSTER + [REND_T], recs() + [KT, QT0])
# N3: finality and a cosign-row voice: C (stolen) cosigns x on a row of its own, concurrent with C's revocation;
# receipts by F, G and A all HOLD the revocation; C is no `signers(x)` voice, so the receipts are clean
vC = KE.revoke("vC", "C", 2, names=("kC",))
cC = CK.row("cC", "cosign", "C", ("aG",), of="x", at=3)
xc = CV.x_row("ABDE", at=3, cites=("cC",))
rx = [rack("rF", "F", ("x", "vC")), rack("rG", "G", ("x", "vC")), rack("rA", "A", ("x", "vC"))]
run("N3a C's late cosign row (at 3, concurrent with its revocation from 2), no receipts", R + recs() + [vC, cC, xc], [])
run("N3b ... three receipts, each holding the revocation", R + recs() + [vC, cC, xc] + rx, [])
xs = CV.x_row("ABCDE", at=3)
run("N3c control: C as a signers(x) voice, same receipts", R + recs() + [vC, xs] + rx, [])
# N4: the race: x concurrent with the revocation, receipts that do not hold it (stated cost)
run("N4 x (at 3) not holding vC; receipts F, G, A not holding vC", R + recs() + [vC, xs] + [rack(i, k) for i, k in (("rF","F"),("rG","G"),("rA","A"))], [])
