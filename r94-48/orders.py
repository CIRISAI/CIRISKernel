"""Arrival orders for attack rows. python3 -I orders.py <src>/models/causal_kernel"""
import sys, itertools
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import consent as C, key_end as KE
G, W, N_, B = C.grant, C.withdraws, C.note, C.binding
cases = {
 "A1": ([G("g1","N","P",("capacity:",),1), KE.revoke("rv","N",3), G("gt","N","A",("capacity:","trace:"),2), N_("n","N",("g1","gt","rv"))], ("N","A","trace:x","n")),
 "A3": (B("b","N","O") + [KE.revoke("rv","O",3), G("gt","O","A",("trace:",),1), N_("n","N",("ab","gt"))], ("N","A","trace:x","n")),
 "A5": ([G("g1","N","P",("capacity:",),5), W("w","N","g1"), G("g2","N","P",("capacity:",),3,("w",)), N_("n","N",("g2",))], ("N","P","capacity:x","n")),
}
for k, (rows, (node, peer, cls, at)) in cases.items():
    got = {C.may_send(C.arrived(list(p)), node, peer, cls, at) for p in itertools.permutations(rows)}
    print(k, "answers over all orders:", got)
