import sys, itertools
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
F4 = lambda proto, **kw: ST.offer("g", "A", ("A", "B", "C", "D"), "member", "@", "self", cosigners=("B", "C", "D"), consensus_protocol=proto, **kw)
rc = lambda i, proto, signer, cos, heads=("g",), **kw: grp(i, "offer", kw.pop("to", ()), "record", None, heads=heads, signer=signer, cosigners=cos, consensus_protocol=proto, **kw)
rmD = lambda heads, signer="A", cos=(): grp("x", "unseat", "D", "member", None, heads=heads, signer=signer, cosigners=cos)
# E1 entrenched weighted: restate the same word with new weights
WE = F4("weighted:r", need=5, weights=(("A", 2), ("B", 2), ("C", 2), ("D", 2)), consensus_protocol_entrenched=True)
ch = rc("am", "weighted:r", "A", ("B", "C"), need=4, weights=(("A", 3), ("B", 1), ("C", 1), ("D", 1)), consensus_protocol_entrenched=True)
run("E1 entrenched weighted: A,B,C restate weighted:r with new weights/threshold", [WE, ch], [])
run("E1b then A alone (3) + B (1) remove D (threshold now 4)", [WE, ch, rmD(("am",), "A", ("B",))], [("D", "member")])
# E2 drop the field: a change with no protocol but flag False
run("E2 change with no protocol, flag False", [F4("majority", consensus_protocol_entrenched=True), rc("am", None, "A", ("B", "C"), consensus_protocol_entrenched=False)], [])
run("E2b then a change to unanimous", [F4("majority", consensus_protocol_entrenched=True), rc("am", None, "A", ("B", "C"), consensus_protocol_entrenched=False), rc("am2", "unanimous", "A", ("B", "C", "D"), heads=("am",))], [])
# E3 quorum entrenched: restate quorum:2/4 with need? (word fixes m)
# E4 concurrent same-word changes, different weights: no protocol in force; then a free change?
c1 = rc("c1", "weighted:r", "A", ("B", "C"), need=5, weights=(("A", 2), ("B", 2), ("C", 2), ("D", 2)), consensus_protocol_entrenched=True)
c2 = rc("c2", "weighted:r", "B", ("C", "D"), need=5, weights=(("A", 1), ("B", 2), ("C", 2), ("D", 3)), consensus_protocol_entrenched=True)
run("E4 two concurrent entrenched restatements, then a change to majority naming both", [WE, c1, c2, rc("am", "majority", "A", ("B", "C", "D"), heads=("c1", "c2"))], [])
