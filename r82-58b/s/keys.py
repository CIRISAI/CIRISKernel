import sys
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import conferral_content as CC
H0, act, keyend, head = CC.H0, CC.act, CC.keyend, CC.head
G0 = head("G0", room="r2")
def show(tag, rows):
    a = CC.answers(rows); print(tag); [print("   ", k, a[k]) for k in sorted(a)]
b1, b2 = act("b1", "H0"), act("b2", "H0", "b1")
g1 = dict(act("g1", "G0"), room="r2")
s1 = act("s1", "H0", signer="B2")
show("1 B2 (a second key, say stolen) removes B, naming nothing: B's rows in both rooms",
     [H0, G0, b1, b2, g1, s1, keyend("k", "B", signer="B2")])
show("2 the same, and B then removes B2 naming everything: does B come back?",
     [H0, G0, b1, b2, g1, s1, keyend("k", "B", signer="B2"), keyend("k2", "B2", signer="B", names=("k", "b2", "g1", "s1"))])
show("3 B removes itself (self-revocation) naming b1 only: b2 cut",
     [H0, b1, b2, keyend("k", "B", names=("b1",))])
show("4 B2 signs a removal of B2 naming nothing, and B2 kept posting concurrently",
     [H0, s1, act("s2", "H0", "s1", signer="B2"), keyend("k", "B2", signer="B2", names=("s1",))])
