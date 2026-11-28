"""r106-48 arrival orders. python3 -I orders.py <src>/models/causal_kernel <r103-48 attack.py>"""
import sys, itertools, random
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
exec(open(sys.argv[2]).read().split("# ---- r97 re-run")[0].split("sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True")[1])
K = [G("g1", "N", "P", ("capacity:",), 1), rev("rv", "N", 3, ("g1",)), G("gt", "N", "A", ("trace:",), 2, ("g1",))]
REG = ST.unseat("ur", "N", "N", "registered", "N", "self", ("g1",))
PR = [found_self("SO", "O"), add_self("aO2", "SO", "O2", ("O",), ("SO",)), add_self("aO3", "SO", "O3", ("O", "O2"), ("aO2",)),
      G("g", "O", "P", ("trace:",), 1, ("aO3",))]
EV = evict("ev", "SO", "O2", ("O", "O3"), ("aO3",))
A3 = B("b", "N", "O") + [G("g0", "O", "Q", ("x:",), 1, ("ab",)), rev("rv", "O", 3, ("g0",)),
                         G("gt", "O", "A", ("trace:",), 1, ("g0",)), N_("n", "N", ("ab", "gt"))]
cases = {"K1r": ([K[0], REG, K[2]], None, ("N", "A", TRC, None)),
         "PE1": (PR + [EV, W("w2", "O2", "g"), N_("n", "O", ("ev", "w2", "g"))], None, ("O", "P", TRC, "n")),
         "U2": (A3 + [ST.unseat("ux", "N", "N", "registered", "N", "group", ("ab",), policy="accord_majority")], "N", ("N", "A", TRC, "n"))}
for k, (rows, reader, (node, peer, cls, at)) in cases.items():
    rnd = random.Random(7)
    ps = list(itertools.permutations(rows)) if len(rows) <= 6 else [rnd.sample(rows, len(rows)) for _ in range(120)]
    got = set()
    for p in ps:
        S2 = C.arrived(list(p)); got.add(C.may_send(S2, node, peer, cls, at, kv=C.key_view(S2, reader)))
    print(k, "orders:", len(ps), "answers:", got)
