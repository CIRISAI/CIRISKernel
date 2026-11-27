import sys, itertools
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
G3 = ST.offer("g", "A", ("A", "B", "C"), "member", "@", "self", cosigners=("B", "C"), consensus_protocol="majority")
adm = lambda i, k, signers, heads: grp(i, "offer", k, "member", "cosigned_act", heads=heads, signer=signers[0], cosigners=tuple(signers[1:]) + (k,))
rem = lambda i, k, signers, heads: grp(i, "unseat", k, "member", None, heads=heads, signer=signers[0], cosigners=tuple(signers[1:]))
L = [G3, adm("ad", "D", ("A", "B", "C"), ("g",)), adm("ae", "E", ("A", "B", "C"), ("ad",)),
     rem("xa", "A", ("C", "D", "E"), ("ae",)), rem("xb", "B", ("C", "D", "E"), ("xa",))]
run("S0 legit line: A, B removed", L, [(k, "member") for k in "ABCDE"], orders=False)
# A and B, removed, change the protocol at the founding head (where they are 2 of 3)
am = grp("am", "offer", (), "record", "cosigned_act", heads=("g",), signer="A", cosigners=("B",), consensus_protocol="one")
run("S1 + A,B's change to `one` at head g", L + [am], [(k, "member") for k in "ABCDE"], orders=False)
# A alone, on its line, admits its friend F under `one`
af = adm("af", "F", ("A",), ("am",))
run("S2 + A alone admits F at head am", L + [am, af], [(k, "member") for k in "ABCDEF"], orders=False)
# a legit member C merges heads: an admission of G naming both tips, by C, D, E
mg = grp("mg", "offer", "G", "member", "cosigned_act", heads=("xb", "af"), signer="C", cosigners=("D", "E", "G"))
run("S3 + C, D, E admit G naming both tips", L + [am, af, mg], [(k, "member") for k in "ABCDEFG"], orders=False)
# after the merge, F alone removes C under `one`?
xf = rem("xc", "C", ("F",), ("mg",))
run("S4 + F alone removes C at head mg", L + [am, af, mg, xf], [(k, "member") for k in "ABCDEFG"], orders=False)
