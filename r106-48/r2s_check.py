import sys
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
exec(open(sys.argv[2]).read().split("# ---- r97 re-run")[0].split("sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True")[1])
import key_end as KE
A3b = B("b", "N", "O") + [G("g0", "O", "Q", ("x:",), 1, ("ab",)), rev("rv", "O", 3, ("g0",)),
                          G("gt", "O", "A", ("trace:",), 1, ("g0",)), N_("n", "N", ("ab",))]
OX = ST.offer("ox", "X", "X2", "member", "X", "self", ("gt",), cosigners=("N",))
S = C.state(A3b + [OX, N_("m", "X", ("n", "ox"))])
print("ox concluded:", bool(S.C.get("ox")), " own_row(ox, N):", KE.own_row(S, S.by["ox"], "N"),
      " gt counts for N:", KE.counts_by(S, "gt", "O", "N"), " for no reader:", KE.counts_by(S, "gt", "O"))
