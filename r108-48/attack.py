"""r108-48: re-check of consent-set 87874be (key-end-retained 1c8dd70). New cases; r97-48, r103-48, r106-48 cover the rest.
python3 -I attack.py <src>/models/causal_kernel <r103-48 attack.py>"""
import sys, itertools
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
exec(open(sys.argv[2]).read().split("# ---- r97 re-run")[0].split("sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True")[1])
import key_end as KE
# RR: re-registration after a registered self-unseat: is the key's end permanent in the key view, and in the seat walk?
REC = ST.offer("rg", "N", "N", "registered", "N", "self")
UR = ST.unseat("ur", "N", "N", "registered", "N", "self", ("rg",))
RE = ST.offer("rg2", "N", "N", "registered", "N", "self", ("ur",))
GR = G("g2", "N", "P", ("trace:",), 5, ("rg2",))
for nm, rows in (("RR0 registered, then self-unseat", [REC, UR]), ("RR1 + re-registered by itself after the unseat", [REC, UR, RE]),
                 ("RR2 + a grant after the re-registration", [REC, UR, RE, GR])):
    S = C.state(rows)
    Q = ST.Seats(S)
    print(nm, "| concluded:", {r["id"]: bool(S.C.get(r["id"])) for r in rows}, "| registered holders:", sorted(Q.holders("registered", "N")),
          "| key_ends:", [e["id"] for e in KE.key_ends(S, "N")],
          "| send g2:" if GR in rows else "", C.may_send(S, "N", "P", TRC, None, None, kv=C.key_view(S)) if GR in rows else "")
# RT: a device rotated (key lane) concurrently with its withdrawal: cut through the key view
PR = [found_self("SO", "O"), add_self("aO2", "SO", "O2", ("O",), ("SO",)), add_self("aO3", "SO", "O3", ("O", "O2"), ("aO2",)),
      G("g", "O", "P", ("trace:",), 1, ("aO3",))]
R2 = KE.rec("r2", "O2", 0, 100)
ROT = KE.rec("rot", "O2b", 0, 100, names=("r2",), succ_of="O2", at_old=5)
show("RT1 O2 rotated to O2b concurrently with O2's withdrawal", PR + [R2, ROT, W("w2", "O2", "g"), N_("n", "O", ("rot", "w2", "g"))],
     [("wd", "w2", "g"), ("send", "O", "P", TRC, "n", None)])
show("RT0 control: the withdrawal in the rotation's past", PR + [R2, W("w2", "O2", "g", ("r2",)), dict(ROT, names=("r2", "w2")), N_("n", "O", ("rot", "w2", "g"))],
     [("wd", "w2", "g"), ("send", "O", "P", TRC, "n", None)])
# orders for K1r and PG1
K = [G("g1", "N", "P", ("capacity:",), 1), ST.unseat("ur", "N", "N", "registered", "N", "self", ("g1",)), G("gt", "N", "A", ("trace:",), 2, ("g1",)), N_("nt", "N", ("gt",))]
PG = PR + [rev("rvo", "O", 5, ("g",)), W("w2", "O2", "g"), N_("n", "O3", ("rvo", "w2"))]
for nm, rows, reader, q in (("K1r", K, "N", ("N", "A", TRC, None)), ("PG1", PG, None, ("O", "P", TRC, "n"))):
    got = set()
    for p in (itertools.permutations(rows) if len(rows) <= 6 else [__import__("random").Random(3).sample(rows, len(rows)) for _ in range(120)]):
        S = C.arrived(list(p)); got.add(C.may_send(S, *q, kv=C.key_view(S, reader)))
    print(nm, "answers over orders:", got)
