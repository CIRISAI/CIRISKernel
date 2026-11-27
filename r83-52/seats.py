"""r83-52 seats.py: seat families at 62b4ba5. Usage: python3 -I seats.py <extracted models/causal_kernel>"""
import sys
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import check_audience as CA, audience as AU
row, J, enc = CA.row, CA.joins_of, CA.enc
R = {"r1": ("a", "b", "c"), "r2": ("a", "e")}
def run(tag, rows, at=None):
    got = AU.audiences(rows, lambda rm: R.get(rm, ()), CA.person, J({"at_head": at or {}}))
    print(tag); [print("   ", i, enc(got[i])) for i in got]
for fam in ("group:roster", "membership:invite", "ballot:moderator_acceptance", "identity:occurrence", "self:delegates_to"):
    run("offer of %s over r1 to outsider z, naming z, naming its head h1 (h1 -> h0)" % fam,
        [row("h0", "chat:general", "community", signer="c", room="r1"),
         row("h1", "chat:general", "community", signer="b", room="r1", names=["h0"]),
         row("o", fam, "community", room="r1", named=["z"], kind="offer", obj="r1", to=["z"], names=["h1"])])
run("removal of c over r2 as ballot:moderator_acceptance unseat, naming its head g1",
    [row("g0", "chat:general", "community", signer="e", room="r2"),
     row("g1", "chat:general", "community", room="r2", names=["g0"]),
     row("x", "ballot:moderator_acceptance", "community", room="r2", named=["c"], kind="unseat", obj="r2", to=["c"], names=["g1"])],
    at={"x": ["a", "c", "e"]})
