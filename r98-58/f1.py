import sys, os
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import check_acts as CA
ST, CK = CA.ST, CA.CK
def run(name, rows, asks):
    S = CK.concluded(CK.kept(list(rows)), lambda r, P, past: ST.seat_rule(r, P, past))
    print("%-88s %s concluded:%s" % (name, [(k, at, ST.is_founder(S, k, "g", at)) for k, at in asks], {r["id"]: bool(S.C.get(r["id"])) for r in rows[1:]}))
X = CA.FREM("x", "B", scope="founder")          # A demotes B (founder_only), at head g
# B's own row naming the founding head with the demotion in its past
NB = ST.R("nb", "note", "B", ("g", "x"), head=("g",))
run("B demoted by x; B's note names head g with x in its past", [CA.FAM2, X, NB], [("B", "nb"), ("A", "nb")])
NB0 = ST.R("nb", "note", "B", ("x",))
run("control: B's note names x, no head", [CA.FAM2, X, NB0], [("B", "nb")])
# B's counted admission at head g with x in its past (does not conclude): is B a founder 'at' it?
RB = CA.FADM("rb", "D", signer="B", heads=("g",), cites=("x",))
run("B's counted admission at head g with x in its past", [CA.FAM2, X, RB], [("B", "rb")])
# several heads, one of them in the other's past
NB2 = ST.R("nb", "note", "B", ("g", "x"), head=("g", "x"))
run("note naming heads (g, x)", [CA.FAM2, X, NB2], [("B", "nb")])
