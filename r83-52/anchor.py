"""r83-52 anchor.py: the content-only anchor at 62b4ba5. Usage: python3 -I anchor.py <extracted models/causal_kernel>"""
import sys
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import conferral_content as CC
H0, act, keyend, head, end, ack = CC.H0, CC.act, CC.keyend, CC.head, CC.end, CC.ack
G0 = head("G0", room="r2")
def show(tag, rows):
    a = CC.answers(rows); print(tag); [print("   ", k, a[k]["rule"]) for k in sorted(a)]
# the owner's case: B2 was stolen; the thief forges f1, f2; the owner revokes B2 naming its last trusted row s1
s1 = act("s1", "H0", signer="B2")
f1, f2 = act("f1", "H0", "s1", signer="B2"), act("f2", "H0", "f1", signer="B2")
k = keyend("k", "B2", signer="B2", names=("s1",))           # the owner, holding B2, revokes it naming s1 (the caller duty)
show("0 the owner revokes B2 naming s1: the forgeries f1, f2 out", [H0, s1, f1, f2, k])
show("1 a colluding co-member M replies to f2 AFTER the revocation, leaving it unnamed (backdated)",
     [H0, s1, f1, f2, k, act("q", "H0", "f2", ["f2"], signer="M")])
show("2 a co-member's ordinary row signed after f2 (not a reply: its head/merge has f2 in its past)",
     [H0, s1, f1, f2, k, act("q", "H0", (), ["f2"], signer="M")])
show("3 the reply is by a sock-puppet member X the thief controls (any key not of B, not the count)",
     [H0, s1, f1, f2, k, act("q", "H0", "f2", ["f2"], signer="X")])
show("4 the reply is by the room's count", [H0, s1, f1, f2, k, act("q", "H0", "f2", ["f2"], signer="count")])
show("5 the reply is by B (the person's other key)", [H0, s1, f1, f2, k, act("q", "H0", "f2", ["f2"], signer="B")])
show("6 the reply is in room r2", [H0, G0, s1, f1, f2, k, dict(act("q", "G0", "f2", ["f2"], signer="M"), room="r2")])
show("7 the reply names the revocation (honest late reply)", [H0, s1, f1, f2, k, act("q", "H0", "f2", ["f2", "k"], signer="M")])
# 8 the anchor against a counted removal: the member's seat ended by the count; does an anchored row stand past E-rules?
show("8 anchored forgery and a counted end of B's seat naming s1", [H0, s1, f1, f2, k, act("q", "H0", "f2", ["f2"], signer="M"), end("E", "H0", ["s1"])])
# 9 the anchor and a retraction: B2's forged retraction of B's m1, anchored by M's reply
m1 = act("m1", "H0")
r = act("rt", "H0", "s1", ["m1"], signer="B2", compose="retract", target="m1")
show("9 a forged retraction by B2 of m1, revoked, then anchored by M's backdated reply",
     [H0, m1, s1, r, k, act("q", "H0", "rt", ["rt"], signer="M")])
