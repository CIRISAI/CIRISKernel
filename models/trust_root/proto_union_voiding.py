"""r78 q4: the two readings of a person's concurrent acknowledgements side by side (root.UNION_VOIDING, a prototype
switch, off). argv[1]: the tree root."""
import sys; sys.path.insert(0, sys.argv[1] + "/models/trust_root")
import root as RT, check_root as CR
RD, nxt = RT.reader, CR.nxt
def row(name, bs, rd, gs=(), gid=None):
    out = []
    for u in (False, True):
        RT.UNION_VOIDING.append(u)
        R = RT.Root(bs, (), gs); f = R.in_force(rd)
        out.append("%s %s%s" % (",".join(R.heads(rd)), "".join(sorted(f[0])) if f else "-",
                                (" " + str(R.grant_in_force(gid, rd)[0])) if gid else ""))
        RT.UNION_VOIDING.pop()
    print("| %s | %s | %s |" % (name, out[0], out[1]))
C = ((), ())
print("| world | concurrent rows judged apart (now) | union voiding |\n|---|---|---|")
STL = CR.STL
row("CA1 d1: s0; d2: b2, b3", STL, RD(anchor="b0", acks=("s0","b2","b3"), after=((),(),(1,))))
row("CA2 + d2 acks b3 naming d1's row", STL, RD(anchor="b0", acks=("s0","b2","b3","b3"), after=((),(),(1,),(0,1,2))))
row("CA3 d1: b2, b3; d2: s0", STL, RD(anchor="b0", acks=("b2","b3","s0"), after=((),(0,),())))
row("CA1g grant by h1 h2 on s0", STL, RD(anchor="b0", acks=("s0","b2","b3"), after=((),(),(1,))), (CR.GR("gx","s0","uX","room",("h1","h2")),), "gx")
row("AO d1: b2; d2: s0", CR.AO, RD(anchor="b0", acks=("b2","s0"), after=C))
row("AO d1: s0; d2: b2", CR.AO, RD(anchor="b0", acks=("s0","b2"), after=C))
row("AO + later row naming both (b2)", CR.AO, RD(anchor="b0", acks=("b2","s0","b2"), after=((),(),(0,1))))
DL = CR.DL; DB3 = CR.DB3
row("DP d1: b2; d2: t", DL, RD(anchor="b0", acks=("b2","t"), after=C))
row("DP d1: t; d2: b2", DL, RD(anchor="b0", acks=("t","b2"), after=C))
row("DP3 d1: b2, b3; d2: t (attacker chain concurrent with honest b3)", DL + [DB3], RD(anchor="b0", acks=("b2","b3","t"), after=((),(0,),())))
row("DP3 d1: t; d2: b2, b3", DL + [DB3], RD(anchor="b0", acks=("t","b2","b3"), after=((),(),(1,))))
t2 = nxt("t2", "t", ("h1","h2","h3","X"), ("h1","h2","h3"), version=4)
row("DP3 + t2: a deeper attacker chain (t1 t t2) on d2", DL + [DB3, t2], RD(anchor="b0", acks=("b2","b3","t2"), after=((),(0,),())))
row("DP3 d1: b2, b3; d2: t1 only", DL + [DB3], RD(anchor="b0", acks=("b2","b3","t1"), after=((),(0,),())))
row("FORKC d1: s1; d2: s2 (no contest)", CR.FORKC, RD(anchor="b0", acks=("s1","s2"), after=C))
# every root case under both readings
moved = []
for r, name, bs, rv, gs, rd, want in CR.CASES:
    a = CR.answer(bs, rv, gs, rd, want)
    RT.UNION_VOIDING.append(True); b = CR.answer(bs, rv, gs, rd, want); RT.UNION_VOIDING.pop()
    if a != b: moved.append((name[:90], a, b))
print("\nroot cases moved under union voiding: %d of %d" % (len(moved), len(CR.CASES)))
for m in moved: print("  ", m)
