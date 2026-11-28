"""r85-52 prevwalk.py: the key removal's prev walk and the duty-seat gate at 0df16b6. Usage: python3 -I prevwalk.py <models/causal_kernel>"""
import sys
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import conferral_content as CC, check_audience as CA, audience as AU
H0, act, keyend, end, head = CC.H0, CC.act, CC.keyend, CC.end, CC.head
G0 = head("G0", room="r2")
def show(tag, rows):
    a = CC.answers(rows); print(tag); [print("   ", k, a[k]["rule"]) for k in sorted(a)]
s1 = act("s1", "H0", signer="B2")
f1 = act("f1", "H0", "s1", signer="B2")
k = keyend("k", "B2", signer="B2", names=("s1",))
# a forged prev: the thief signs f0 whose prev claims s1's successor slot; can a forgery be dragged in by a prev?
show("1 forgery f2 claims prev s1 and the owner names s1: f2 is a successor, not behind s1", [H0, s1, f1, act("f2", "H0", "s1", signer="B2"), k])
show("2 the honest row s1 itself lists a forged prev? (s1 prev = f0, f0 signed by the thief concurrently)",
     [H0, act("f0", "H0", signer="B2"), act("s1", "H0", "f0", signer="B2"), keyend("k", "B2", signer="B2", names=("s1",))])
show("3 the prev chain runs through B's row (the person's other key) to a B2 forgery",
     [H0, act("f0", "H0", signer="B2"), act("b1", "H0", "f0", signer="B"), act("s1", "H0", "b1", signer="B2"), keyend("k", "B2", signer="B2", names=("s1",))])
show("4 the prev chain runs through a co-member's row",
     [H0, act("f0", "H0", signer="B2"), act("m1", "H0", "f0", signer="M"), act("s1", "H0", "m1", signer="B2"), keyend("k", "B2", signer="B2", names=("s1",))])
show("5 the prev chain runs into another room's row of B2",
     [H0, G0, dict(act("g0", "G0", signer="B2"), room="r2"), act("s1", "H0", "g0", signer="B2"), keyend("k", "B2", signer="B2", names=("s1",))])
show("6 the thief revokes B2 naming its forgery f1; the owner's revocation names s1, concurrent with it",
     [H0, s1, f1, keyend("kt", "B2", signer="B2", names=("f1",)), k])
show("7 the same, the owner's revocation having the thief's in its past (it named it)",
     [H0, s1, f1, keyend("kt", "B2", signer="B2", names=("f1",)), keyend("k", "B2", signer="B2", names=("s1", "kt"))])
show("8 a removal naming a co-member's row as a tip whose prev is a cut B2 row",
     [H0, s1, f1, act("m1", "H0", "f1", signer="M"), keyend("k", "B2", signer="B2", names=("m1",))])
# the duty-seat gate
R = {"r1": ("a", "b", "c")}
def place(tag, rows, at):
    got = AU.audiences(rows, lambda rm: R.get(rm, ()), CA.person, CA.joins_of({"at_head": at}))
    print(tag); [print("   ", i, CA.enc(got[i])) for i in got]
print("duty seat families:", sorted(AU.DUTY_SEAT_FAMILIES), " room seat families:", sorted(AU.SEAT_FAMILIES))
r = lambda i, kind, to, **kw: CA.row(i, "ballot:moderator_acceptance", "community", room="r1", named=list(to), kind=kind, obj="r1", to=to, **kw)
place("9 moderator acceptance offer to outsider z", [r("o", "offer", ["z"])], {"o": ["a", "b", "c"]})
place("10 moderator acceptance offer to member b", [r("o", "offer", ["b"])], {"o": ["a", "b", "c"]})
place("11 unseat of moderator c, c a member at its head, removed since", [r("u", "unseat", ["c"])], {"u": ["a", "b", "c"]})
place("12 offer to j, who joined after the row's head (on the current roster, not at head)", [r("o", "offer", ["j"])], {"o": ["a", "b", "c"]})
