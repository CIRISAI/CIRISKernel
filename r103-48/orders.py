"""r103-48 arrival orders. python3 -I orders.py <src>/models/causal_kernel <scripts>/attack.py"""
import sys, itertools, random
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
exec(open(sys.argv[2]).read().split("# ---- r97 re-run")[0].split("sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True")[1])
PR = [found_self("SO", "O"), add_self("aO2", "SO", "O2", ("O",), ("SO",)), add_self("aO3", "SO", "O3", ("O", "O2"), ("aO2",)),
      G("g", "O", "P", ("trace:",), 1, ("aO3",))]
EV = evict("ev", "SO", "O2", ("O", "O3"), ("aO3",))
FD = [G("g1", "N", "P", ("capacity:",), 10), G("h1", "N", "P", ("capacity:",), 10),
      G("g2", "N", "P", ("capacity:",), 1, ("g1",)), G("h2", "N", "P", ("capacity:",), 1, ("h1",)), N_("n", "N", ("g2", "h2"))]
CF = [G("g3", "N", "P", ("capacity:", "trace:"), 4), G("g2", "N", "P", ("capacity:",), 5), W("w", "N", "g2"),
      G("g4", "N", "P", ("capacity:",), 3, ("w",)), N_("n", "N", ("g3", "g4"))]
cases = {"FD1": (FD, ("N", "P", CAP, "n")), "CF1": (CF, ("N", "P", TRC, "n")),
         "PE1": (PR + [EV, W("w2", "O2", "g"), N_("n", "O", ("ev", "w2"))], ("O", "P", TRC, "n")),
         "PR1": (PR + [rev("rv2", "O2", 5, ("aO3",)), W("w2", "O2", "g"), N_("n", "O", ("rv2", "w2"))], ("O", "P", TRC, "n"))}
for k, (rows, (node, peer, cls, at)) in cases.items():
    rnd = random.Random(7)
    ps = list(itertools.permutations(rows)) if len(rows) <= 6 else [rnd.sample(rows, len(rows)) for _ in range(120)]
    got = {C.may_send(C.arrived(list(p)), node, peer, cls, at) for p in ps}
    print(k, "orders:", len(ps), "answers:", got)
