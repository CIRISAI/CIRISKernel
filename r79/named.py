import sys
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import check_audience as CA, audience as AU
row = CA.row
m = row("m", "chat:general", "community", signer="a", room="r2", named=["c"])     # a mentions c while c sat in r2
before = {"r2": ("a", "c", "e")}; after = {"r2": ("a", "e")}                       # c removed later
for tag, R in (("node before c's removal", before), ("node after c's removal", after)):
    got = AU.audiences([m, row("d", "chat:general", "community", signer="e", room="r2", names=["m"])],
                       lambda room: R.get(room, ()), CA.person)
    print(tag, {k: CA.enc(v) for k, v in got.items()})
