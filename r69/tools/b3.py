import sys, itertools
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
GI = AC.GI
n = grp("r", "offer", "n1", "node", None, signer="f1", cosigners=("f2",))
run("N1 infra: node seat, no acceptance", [GI, n], [("n1", "node")])
run("N1b with n1's acceptance", [GI, n, ST.accept("an", "n1", "r")], [("n1", "node")])
nc = dict(n, consent="one")
run("N1c with consent=one", [GI, nc], [("n1", "node")])
fo = grp("r", "offer", "f4", "founder", None, signer="f1", cosigners=("f2",), consent="one")
run("N2 founder seat with consent=one, f4 never signs", [GI, fo], [("f4", "founder"), ("f4", "member")])
# lone infra founder
GL = ST.offer("g", "f1", ("f1",), "member", "@", "self", cohort_subkind="infrastructure", consensus_protocol="one")
run("N3 lone infra founder, protocol one: seats n1, n2 as nodes (consent one)", [GL, dict(grp("r", "offer", ("n1", "n2"), "node", None, signer="f1"), consent="one")], [("n1", "node"), ("n2", "node")])
# member admission in infra: refused; own offer (conf self) of member in infra?
o = ST.offer("o", "f1", "X", "member", OBJ, "self", ("g",), cosigners=("X",))
run("N4 infra: f1's own offer of member to X", [GI, o], [("X", "member")])
# record change in infra?
am = grp("am", "offer", (), "record", "cosigned_act", signer="f1", cosigners=("f2",), consensus_protocol="one")
run("N5 infra: record change by f1,f2", [GI, am], [])
# the lone founder in plain community: duties / moderate
