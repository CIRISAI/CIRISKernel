"""r82 named.py: r79's named.py with a head view (joins['at_head']). Usage: python3 -I named.py <models/causal_kernel>"""
import sys
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import check_audience as CA, audience as AU
row = CA.row
m = row("m", "chat:general", "community", signer="a", room="r2", named=["c"])     # a mentions c while c sat in r2
d = row("d", "chat:general", "community", signer="e", room="r2", names=["m"])
at = {"m": ["a", "c", "e"], "d": ["a", "e"]}
for tag, R in (("node before c's removal", {"r2": ("a", "c", "e")}), ("node after c's removal", {"r2": ("a", "e")})):
    got = AU.audiences([m, d], lambda room: R.get(room, ()), CA.person, CA.joins_of({"at_head": at}))
    print(tag, {k: CA.enc(v) for k, v in got.items()})
# the converse: a row naming z before z joined, read after z joins
z = row("z1", "chat:general", "community", signer="a", room="r2", named=["z"])
got = AU.audiences([z], lambda room: ("a", "e", "z"), CA.person, CA.joins_of({"at_head": {"z1": ["a", "e"]}}))
print("row naming z before z joined, read after z joined", {k: CA.enc(v) for k, v in got.items()})
