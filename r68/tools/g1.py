import sys, itertools, random
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
G = ST.offer("g", "A", ("A", "B", "C"), "member", "@", "self", cosigners=("B", "C"), consensus_protocol="majority")
adm = lambda i, k, signers, heads: grp(i, "offer", k, "member", "cosigned_act", heads=heads, signer=signers[0], cosigners=tuple(signers[1:]) + (k,))
rem = lambda i, k, signers, heads: grp(i, "unseat", k, "member", None, heads=heads, signer=signers[0], cosigners=tuple(signers[1:]))
L = [G, adm("ad", "D", ("A", "B", "C"), ("g",)), adm("ae", "E", ("A", "B", "C", "D"), ("ad",))]
x = rem("x", "C", ("B", "D", "E"), ("ae",))                      # honest: 3 of 5 remove C
run("K0 honest removal of C", L + [x], [(k, "member") for k in "ABCDE"], orders=False)
z_same = rem("z", "B", ("A", "C"), ("ae",))                       # forged at the same head: 2 of 5
run("K1 forged A + C remove B at the same head ae", L + [x, z_same], [(k, "member") for k in "ABCDE"], orders=False)
z_old = rem("z", "B", ("A", "C"), ("g",))                         # forged at the founding head: 2 of 3
run("K2 forged A + C remove B at the OLD head g", L + [x, z_old], [(k, "member") for k in "ABCDE"], orders=False)
run("K2b forged at g alone (no honest x)", L + [z_old], [(k, "member") for k in "ABCDE"], orders=False)
S = CK.concluded(CK.kept(L + [x, z_old]), RULE); Q = ST.Seats(S)
print("dropped (contested/out):", sorted(Q.dropped))
