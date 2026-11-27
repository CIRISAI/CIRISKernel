import sys, os
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import check_audience as CA, audience as AU
row, J = CA.row, CA.joins_of
def show(tag, rows, w=None, ids=None):
    got = {i: CA.enc(a) for i, a in AU.audiences(rows, CA.roster, CA.person, J(w)).items()}
    print(tag); [print("   ", i, got[i]) for i in (ids or got)]
# r3 roster a,b,j; j admitted by adm, after m0 and m1 (from_join)
w = {"joined": {"r3": {"j": "adm"}}, "before": [["m0", "adm"], ["m1", "adm"], ["m0", "m1"], ["m0", "d"], ["m1", "d"], ["adm", "d"]]}
m0 = row("m0", "chat:general", "community", signer="a", room="r3")
m1 = row("m1", "chat:general", "community", signer="b", room="r3", names=["m0"])
show("1 from_join, nothing names the old rows (baseline)", [m0, m1], w)
d = row("d", "chat:general", "community", signer="b", room="r3", names=["m1"])
show("2 from_join, b replies after j's join naming m1 (m1 names m0)", [m0, m1, d], w)
adm = row("adm", "partner_role:member", "community", signer="a", room="r3", named=["j"], seats=["j"], names=["m1"])
show("3 from_join, only the admission row itself, naming its head m1", [m0, m1, adm], w)
# r1 roster a,b,c; z an outsider: a concluded offer to z naming its head
o = row("o", "partner_role:member", "community", signer="a", room="r1", named=["z"], seats=["z"], names=["h1"])
h1 = row("h1", "chat:general", "community", signer="b", room="r1", names=["h0"])
h0 = row("h0", "chat:general", "community", signer="c", room="r1")
show("4 a concluded offer to z (never accepted) naming its head h1", [h0, h1, o])
# r2 roster a,e; c removed by x naming its head g1; c owed nothing further
g0 = row("g0", "chat:general", "community", signer="e", room="r2")
g1 = row("g1", "chat:general", "community", signer="a", room="r2", names=["g0"])
x = row("x", "partner_role:member", "community", signer="a", room="r2", named=["c"], seats=["c"], names=["g1"])
show("5 removal of c naming its head g1", [g0, g1, x])
