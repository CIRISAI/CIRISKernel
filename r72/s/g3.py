exec(open(__file__.replace("g3.py","lib.py")).read())
H5 = ("h1","h2","h3","h4","h5")
L = [B0, nxt("b1","b0",H5,("h1","h2")), nxt("b2","b1",("h3","h4","h5"),("h3","h4","h5"),version=2)]
g1 = GR("g1","b0","uX","room",("h1","h2"))                   # removed h1,h2 naming the genesis bundle
ak = AK("k2","b2",names=("g1",))                                # the reader's next acceptance edge names what it holds
run("G5 removed holders' grant on b0; the reader's later acceptance edge of b2 names it", L, gs=(g1, ak), rd=RD(anchor="b0", acks=("b2",), rows=("k2",)), gids=("g1",))
import check_root as CR2
rows = CR.STALLED + [CR.RCV()]
print("G6 stalled infra recovery on it ->", CR.recovery_answer(rows, L, (dict(g1, id="B1", to="f4", scope="g"), dict(ak, names=("B1",))), RD(anchor="b0", acks=("b2",), rows=("k2",))))
