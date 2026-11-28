"""r84-52 revive.py: revival paths for a revoked key's rows at 56f6ac2. Usage: python3 -I revive.py <models/causal_kernel>"""
import sys
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import conferral_content as CC
H0, act, keyend, end, tips, ack = CC.H0, CC.act, CC.keyend, CC.end, CC.tips, CC.ack
def show(tag, rows):
    a = CC.answers(rows); print(tag); [print("   ", k, a[k]["rule"]) for k in sorted(a)]
s1, f1 = act("s1", "H0", signer="B2"), act("f1", "H0", "s1", signer="B2")
k = keyend("k", "B2", signer="B2", names=("s1",))
show("1 the count's end names f1 as a tip after the revocation", [H0, s1, f1, k, end("E", "H0", ["f1"], names=("k",))])
show("2 the count's end names f1, signed before the revocation (concurrent)", [H0, s1, f1, end("E", "H0", ["f1"]), k])
show("3 a count tips row adds f1 to an end, after the revocation", [H0, s1, f1, k, end("E", "H0", ["s1"]), tips("A", "E", ["f1"])])
show("4 a reader ack of f1 that has the revocation in its past", [H0, s1, f1, k, ack("a1", ["f1", "k"])])
show("5 a reader ack of f1 concurrent with the revocation (the line: stands, by design)", [H0, s1, f1, k, ack("a1", ["f1"])])
show("6 B (the person's other key) names f1 as a prev of its own row", [H0, s1, f1, k, act("b1", "H0", "f1", ["f1"], signer="B")])
show("7 a second revocation of B2 by B that concludes and names f1", [H0, s1, f1, k, keyend("k2", "B2", signer="B", names=("f1",), concludes=True)])
show("8 B2 re-signs after the revocation, naming it", [H0, s1, f1, k, act("f2", "H0", "f1", ["k"], signer="B2")])
b1, b2 = act("b1", "H0"), act("b2", "H0", "b1")
show("9 B revokes itself naming its newest trusted row b2 (prev b1, not in b2's names)", [H0, b1, b2, keyend("k", "B", names=("b2",))])
b2n = act("b2", "H0", "b1", ["b1"])
show("10 the same, where b2 also names b1 (b1 in its causal past)", [H0, b1, b2n, keyend("k", "B", names=("b2",))])
