"""Arrival orders for the re-attack rows. python3 -I orders.py <src>/models/causal_kernel"""
import sys, itertools, random
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import consent as C
CK, ST = C.CK, C.ST
W, N_, B = C.withdraws, C.note, C.binding
def G(*a, fed=False, **kw): return C.grant(*a, fed=fed, **kw)
def rev(id, key, ra, names=()): return CK.row(id, "revoke", key, tuple(names), key=key, ra=ra)
cases = {
 "K1 reader N": ([G("g1","N","P",("capacity:",),1), rev("rv","N",3,("g1",)), G("gt","N","A",("trace:",),2,("g1",)), N_("nt","N",("gt",))],
                 "N", ("N","A","trace:x",None)),
 "A3 reader N": (B("b","N","O") + [G("g0","O","Q",("x:",),1,("ab",)), rev("rv","O",3,("g0",)), G("gt","O","A",("trace:",),1,("g0",)), N_("n","N",("ab","gt"))],
                 "N", ("N","A","trace:x","n")),
 "F1": (B("b","N","O") + [G("gn","N","P",("trace:",),1,("ab",)), ST.withdraw("wb","O","ab",("gn",)), W("wo","O","gn"), N_("n","N",("wb","wo"))],
        None, ("N","P","trace:x","n")),
 "CF1": ([G("g3","N","P",("capacity:","trace:"),4), G("g2","N","P",("capacity:",),5), W("w","N","g2"), G("g4","N","P",("capacity:",),3,("w",)), N_("n","N",("g3","g4"))],
         None, ("N","P","trace:x","n")),
}
for k, (rows, reader, (node, peer, cls, at)) in cases.items():
    ps = list(itertools.permutations(rows)) if len(rows) <= 6 else [random.Random(1).sample(rows, len(rows)) for _ in range(200)]
    got = set()
    for p in ps:
        S = C.arrived(list(p))
        got.add(C.may_send(S, node, peer, cls, at, kv=C.key_view(S, reader)))
    print(k, "orders:", len(ps), "answers:", got)
