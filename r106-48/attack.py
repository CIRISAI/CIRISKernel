"""r106-48: re-check of consent-set 4afc727 (key-end-retained 8a11cca). New cases only; r97-48 and r103-48 cover the rest.
python3 -I attack.py <src>/models/causal_kernel <r103-48 attack.py>"""
import sys
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
exec(open(sys.argv[2]).read().split("# ---- r97 re-run")[0].split("sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True")[1])
PR = [found_self("SO", "O"), add_self("aO2", "SO", "O2", ("O",), ("SO",)), add_self("aO3", "SO", "O3", ("O", "O2"), ("aO2",)),
      G("g", "O", "P", ("trace:",), 1, ("aO3",))]
EV = evict("ev", "SO", "O2", ("O", "O3"), ("aO3",))
_show = show
def show(name, rows, asks, reader=None):
    S = C.state(rows)
    extra = [a for a in asks if a[0] == "concl_ux"]
    if extra: print("    ux concluded:", bool(S.C.get("ux")))
    _show(name, rows, [a for a in asks if a[0] != "concl_ux"], reader)
# controls: a live device withdraws
show("C1 O3 (live device) withdraws O's grant", PR + [W("w3", "O3", "g"), N_("n", "O", ("w3",))], [("wd", "w3", "g"), ("send", "O", "P", TRC, "n", None)])
show("C2 O2 withdraws, then is evicted (eviction has w2 in its past)",
     PR + [W("w2", "O2", "g"), dict(evict("ev", "SO", "O2", ("O", "O3"), ("aO3",)), names=("aO3", "w2")), N_("n", "O", ("w2", "ev"))],
     [("wd", "w2", "g"), ("person", "ev", "O2"), ("send", "O", "P", TRC, "n", None)])
show("C3 O2 withdraws; its later revocation names the withdrawal",
     PR + [W("w2", "O2", "g"), rev("rv2", "O2", 5, ("w2",)), N_("n", "O", ("rv2",))], [("wd", "w2", "g"), ("send", "O", "P", TRC, "n", None)])
# the genesis key's revocation: every device then speaks for no one
show("PG1 O (genesis) revoked; O2's withdrawal concurrent with it",
     PR + [rev("rvo", "O", 5, ("g",)), W("w2", "O2", "g"), N_("n", "O3", ("rvo", "w2"))], [("wd", "w2", "g")])
# R2: a row by another key claiming N as a cosigner is no row of N's line
K = [G("g1", "N", "P", ("capacity:",), 1), rev("rv", "N", 3, ("g1",)), G("gt", "N", "A", ("trace:",), 2, ("g1",))]
show("R2 a note by X claiming N as cosigner, naming the thief grant", K + [CK.row("nx", "note", "X", ("gt",), cosigners=("N",))],
     [("send", "N", "A", TRC, None, None)], reader="N")
# K1 in the seat-lane form: a registered unseat of N by N, the thief row concurrent with it
REG = ST.unseat("ur", "N", "N", "registered", "N", "self", ("g1",))
show("K1r registered self-unseat of N; thief grant and thief row as N concurrent", [K[0], REG, K[2], N_("nt", "N", ("gt",))],
     [("send", "N", "A", TRC, None, None)], reader="N")
show("K1r control: N's honest row before the unseat names g1 (taken up)", [K[0], N_("n0", "N", ("g1",)), ST.unseat("ur", "N", "N", "registered", "N", "self", ("n0",))],
     [("send", "N", "P", "capacity:x", None, None)], reader="N")
# an unconcluded registered unseat of N by N also cuts N's line (S.rows, not S.Cs)
show("K1r with no reader: the thief grant's own voice", [K[0], REG, K[2]], [("send", "N", "A", TRC, None, None)])
A3 = B("b", "N", "O") + [G("g0", "O", "Q", ("x:",), 1, ("ab",)), rev("rv", "O", 3, ("g0",)),
                         G("gt", "O", "A", ("trace:",), 1, ("g0",)), N_("n", "N", ("ab", "gt"))]
show("U0 A3 taken up by reader N (control)", A3, [("send", "N", "A", TRC, "n", None)], reader="N")
show("U2 A3 + a registered self-unseat of N that does not conclude, concurrent with n",
     A3 + [ST.unseat("ux", "N", "N", "registered", "N", "group", ("ab",), policy="accord_majority")],
     [("concl_ux",), ("send", "N", "A", TRC, "n", None)], reader="N")
show("U1 a registered self-unseat that does not conclude (conf group, no count) cuts N's line",
     [K[0], N_("n0", "N", ("g1",)), ST.unseat("ux", "N", "N", "registered", "N", "group", (), policy="accord_majority")],
     [("send", "N", "P", "capacity:x", None, None)], reader="N")
# R2s: R2 through a seat row: X's own self-conferred offer (concludes on X's word) lists N as a cosigner and names the
# thief's grant; N never signed anything naming it
A3b = B("b", "N", "O") + [G("g0", "O", "Q", ("x:",), 1, ("ab",)), rev("rv", "O", 3, ("g0",)),
                          G("gt", "O", "A", ("trace:",), 1, ("g0",)), N_("n", "N", ("ab",))]
show("R2s0 A3 without N naming gt: no reader line (control)", A3b + [N_("m", "N", ("n", "gt"))][:0] + [N_("m", "X", ("n", "gt"))],
     [("send", "N", "A", TRC, "m", None)], reader="N")
OX = ST.offer("ox", "X", "X2", "member", "X", "self", ("gt",), cosigners=("N",))
show("R2s1 X's self-conferred offer claiming N as cosigner, naming gt", A3b + [OX, N_("m", "X", ("n", "ox"))],
     [("concl_ux",), ("send", "N", "A", TRC, "m", None)], reader="N")
