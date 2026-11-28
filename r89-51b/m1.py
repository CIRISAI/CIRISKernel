import sys, os
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import check_key_view as CV
ST, KE, CK, CH = CV.ST, CV.KE, CV.CK, CV.CH
def run(name, sr, kr, reader=None, probe="x", seat=None, rule="seat"):
    got, fin = CV.cut_answer(rule, sr, kr, reader, probe, seat)
    print(name); print("   %s: %s | final: %s" % ("x concluded" if not seat else "%s %s" % (seat[0], seat[1]), got, fin))
R = CH.ROOM; recs = CV.recs; rack = CV.rack
# M1: the thief votes AFTER the owner's revocation is out; routine receipts (three of seven, one the stolen key's own)
vC = KE.revoke("vC", "C", 2, names=("kC",))
xl = CV.x_row("ABCDE", at=3, cites=("vC",))           # x signed at 3, its past holding the revocation: a late vote
run("M1a C revoked (ra 2), then x signed with the stolen C at 3 holding the revocation: no receipts", R + recs() + [vC, xl], [])
run("M1b ... and receipts by F, G and the stolen C itself (n - t + 1 = 3)", R + recs() + [vC, xl, rack("rF","F",("x",)),
    rack("rG","G",("x",)), rack("rC","C",("x",))], [])
run("M1c ... receipts by F, G and A, all holding the revocation", R + recs() + [vC, xl, rack("rF","F",("x","vC")),
    rack("rG","G",("x","vC")), rack("rA","A",("x","vC"))], [])
# M2: an unrotated stolen key: the thief ROTATES it to T, naming only C's record: a wipe the owner cannot answer
qT = KE.rec("qT", "T", 1, None, names=("kC",), succ_of="C", at_old=1, typ="pseudonym")
X0 = CV.x_row("ABCDE", at=0)
run("M2a C's honest vote x at 0, then the thief rotates C to T naming nothing", R + [X0], recs() + [KE.rec("kT","T",0,None,typ="pseudonym"), qT])
vCo = KE.revoke("vO", "C", 0, names=("qT", "x"))
run("M2b ... the owner then revokes C holding x and the thief's rotation: (no end: a rotation in its past)", R + [X0],
    recs() + [KE.rec("kT","T",0,None,typ="pseudonym"), qT, vCo])
q2 = KE.rec("q2", "C2", 2, None, names=("kC", "x", "qT"), succ_of="C", at_old=2, typ="pseudonym")
run("M2c ... or rotates C to C2 holding x: x still cut by the thief's rotation", R + [X0],
    recs() + [KE.rec("kT","T",0,None,typ="pseudonym"), qT, q2])
# M3: the owner rotated C to C2 holding x; the thief (old C) votes y before the owner learns; C2's roster end cuts it;
# the thief dodges by rotating old C to T too: two successors, no roster end
q2h = KE.rec("q2", "C2", 4, None, names=("kC", "x"), succ_of="C", at_old=4, typ="pseudonym")
xs = CV.x_row("ABCDE", at=3)                          # the thief's vote at 3, held by the owner's rotation (at 4)
eC = KE.rend("eC", "C2", "C", 2, names=("q2",))
run("M3a owner rotates C->C2 (holding x, the thief's vote at 3); C2's roster end from 2 cuts x", R + [xs],
    recs() + [q2h, eC])
qT2 = KE.rec("qT", "T", 4, None, names=("kC",), succ_of="C", at_old=4, typ="pseudonym")
run("M3b ... the thief also rotates old C to T: two successors; C2's roster end is no end", R + [xs],
    recs() + [KE.rec("kT","T",0,None,typ="pseudonym"), q2h, qT2, eC])
qT3 = KE.rec("qT", "T", 4, None, names=("kC", "x"), succ_of="C", at_old=4, typ="pseudonym")
run("M3c ... the thief's rotation of old C to T holds x: two successors, C2's roster end is no end, x stands", R + [xs],
    recs() + [KE.rec("kT","T",0,None,typ="pseudonym"), q2h, qT3, eC])
eT = KE.rend("eT", "T", "C", 0, names=("qT",))
run("M3d and T (the thief) alone as C's successor ends C from 0: the owner's in-time vote x (at 0) is cut", R + [X0],
    recs() + [KE.rec("kT","T",0,None,typ="pseudonym"), KE.rec("qT", "T", 1, None, names=("kC", "x"), succ_of="C", at_old=1, typ="pseudonym"), eT])
