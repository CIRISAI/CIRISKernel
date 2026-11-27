"""r82 keys2.py: key removals at ed6d3fb. Usage: python3 -I keys2.py <models/causal_kernel>"""
import sys
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import conferral_content as CC
H0, act, keyend, head, ack = CC.H0, CC.act, CC.keyend, CC.head, CC.ack
G0 = head("G0", room="r2")
def show(tag, rows):
    a = CC.answers(rows); print(tag); [print("   ", k, a[k]["rule"]) for k in sorted(a)]
b1, b2, g1 = act("b1", "H0"), act("b2", "H0", "b1"), dict(act("g1", "G0"), room="r2")
show("1 a thief of B signs B's own revocation naming nothing (needs no count)", [H0, G0, b1, b2, g1, keyend("k", "B")])
show("2 the same, a reader had acknowledged b1 before holding the revocation", [H0, G0, b1, b2, g1, ack("a1", ["b1"]), keyend("k", "B")])
show("3 B2 evicts B, the caller says it concludes, naming nothing", [H0, G0, b1, b2, g1, keyend("k", "B", signer="B2", concludes=True)])
show("4 an acknowledgement in room r2 keeps a row of room H0's room?", [H0, G0, b1, dict(ack("a2", ["b1", "G0"]), room="r2"), keyend("k", "B")])
