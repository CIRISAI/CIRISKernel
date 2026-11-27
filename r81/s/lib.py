import sys, os, random
sys.path.insert(0, os.path.join(sys.argv[1], "models/trust_root"))
sys.dont_write_bytecode = True
import root as RT, check_root as CR
B, RV, GR, RD, AK, nxt = RT.bundle, RT.revoke, RT.grant, RT.reader, RT.ack, CR.nxt
B0, F, H3, C1, C2 = CR.B0, CR.F, CR.H3, CR.C1, CR.C2
def ans(bs, rv, gs, rd, gids=()):
    R = RT.Root(bs, rv, gs)
    f = R.in_force(rd)
    return (R.heads(rd), tuple(sorted(f[0])) if f else None, tuple(sorted(R.void())),
            {g: R.grant_in_force(g, rd) for g in gids}, {i: R.counted(i)[0] for i in sorted(R.by)})
def run(name, bs, rv=(), gs=(), rd=None, gids=(), n=60):
    a = ans(bs, rv, gs, rd, gids); rnd = random.Random(7); d = 0
    for _ in range(n):
        b2 = list(bs); rnd.shuffle(b2); g2 = list(gs); rnd.shuffle(g2)
        if ans(b2, rv, g2, rd, gids) != a: d += 1
    print(name); print("   heads=%s holders=%s void=%s grants=%s" % a[:4]); print("   concluded=%s | orders differing %d/%d" % (a[4], d, n))
