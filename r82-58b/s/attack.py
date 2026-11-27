"""r82: attacks on audience.py at ed6d3fb. Usage: python3 -I attack.py <extracted models/causal_kernel>"""
import sys
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import check_audience as CA, audience as AU
row, J, enc = CA.row, CA.joins_of, CA.enc
R0 = {"r1": ("a", "b", "c"), "r2": ("a", "e")}
def run(tag, rows, roster=R0, person=None, at=None):
    P = person or {"a": ("a", "a2")}
    got = AU.audiences(rows, lambda rm: roster.get(rm, ()), lambda k: P.get(k, (k,)), J({"at_head": at or {}}))
    print(tag); [print("   ", i, enc(got[i])) for i in got]
# 1 key grant: "reaches only the key it names"
run("1 key_grant:content placed at community (r1), naming d... d off roster so name b",
    [row("k", "key_grant:content", "community", room="r1", named=["b"])])
run("1b key_grant:content at self naming d", [row("k", "key_grant:content", "self", named=["d"])])
# 2 a self row carried by another key: b's commons row naming a's self row (b not in its audience)
run("2 b's commons row names a's self row s", [row("s", "chat:general", "self"), row("c", "chat:general", "federation", signer="b", names=["s"])])
# 3 the person mapping as a carrier: a2 in person(a) (say its key was removed, or the mapping is stale)
run("3 a2 (in person(a)) publishes a's self row at commons",
    [row("s", "chat:general", "self"), row("c", "chat:general", "federation", signer="a2", names=["s"])])
run("3b a2 addresses outsider z, naming a's self row",
    [row("s", "chat:general", "self"), row("x", "census:member:share", "addressed", signer="a2", named=["z"], names=["s"])])
run("3c asymmetric mapping: X claims a (person(X) = {X, a}); X publishes a's self row",
    [row("s", "chat:general", "self"), row("c", "chat:general", "federation", signer="X", names=["s"])],
    person={"a": ("a",), "X": ("X", "a")})
# 4 off-roster by a carrier chain: a's self row carried into r1 by a's room row, then to z by a's addressed row
run("4 a's self row s -> a's room row m (r1) -> a's addressed row x to z",
    [row("s", "chat:general", "self"), row("m", "chat:general", "community", room="r1", names=["s"]),
     row("x", "census:member:share", "addressed", named=["z"], names=["s"])])
run("4b a room row m (r1, by b) named by a's addressed row x to z: does m leave the room?",
    [row("m", "chat:general", "community", signer="b", room="r1"),
     row("x", "census:member:share", "addressed", named=["z"], names=["m"])])
run("4c room row m (r1, by b) named by an r1 row d naming z at its head (z sat there, removed since)",
    [row("m", "chat:general", "community", signer="b", room="r1"),
     row("d", "chat:general", "community", signer="a", room="r1", named=["z"], names=["m"])], at={"d": ["a", "b", "c", "z"]})
run("4d an r1 room row carried by an r2 row of the same signer (cross-room)",
    [row("m", "chat:general", "community", room="r1"), row("d", "chat:general", "community", room="r2", names=["m"])])
# 5 removed member c (r1 is now a, b): served after removal?
R1 = {"r1": ("a", "b")}
run("5 a row signed at a stale head where c sat, naming c, after c's removal", 
    [row("m", "chat:general", "community", room="r1", named=["c"])], roster=R1, at={"m": ["a", "b", "c"]})
run("5b a second unseat of c, signed after the removal, naming the room's latest rows",
    [row("h", "chat:general", "community", signer="b", room="r1"),
     row("u2", "partner_role:member", "community", room="r1", named=["c"], kind="unseat", obj="r1", to=["c"], names=["h"])],
    roster=R1, at={"u2": ["a", "b"]})
run("5c an OFFER whose obj is the room but whose `to` is c (re-seat, never concluded by count), naming h",
    [row("h", "chat:general", "community", signer="b", room="r1"),
     row("o", "chat:general", "community", room="r1", kind="offer", obj="r1", to=["c"], names=["h"], concluded=False)],
    roster=R1, at={"o": ["a", "b"]})
run("5d the same offer with family chat:general (any family carries `to`) naming c",
    [row("o", "chat:general", "community", room="r1", kind="offer", obj="r1", to=["c", "z"], named=["c", "z"])],
    roster=R1, at={"o": ["a", "b"]})
