exec(open(__file__.replace("n4.py","lib.py")).read())
KCH = C.KCH; klic = C.klic; glic = C.glic; E0 = C.E0
OK=(True,None)
ZO = ST.offer("zo","Z","Z","x","Z","self"); ZW = dict(ST.withdraw("zw","Z","zo",("zo",)), asserted_at=10**9)
run("D0 control: K's licence stating 50, reader's edge", [E0,klic("l")|{"asserted_at":50}], "RD","l",KCH, want=OK)
run("D1 + unrelated key Z withdraws its own offer over Z, stating 1e9", [E0,klic("l")|{"asserted_at":50},ZO,ZW], "RD","l",KCH, want=OK)
run("D1b same, Z's withdrawal states 40 (earlier than the licence)", [E0,klic("l")|{"asserted_at":50},ZO,dict(ZW,asserted_at=40)], "RD","l",KCH, want=OK)
# a community licence under a termed seat
G1, G1LT, GLA = C.G1, C.G1LT, C.GLA
run("D2 control: termed seat 10..100, X's licence at 50", [G1,G1LT,GLA,A("e","RD","g"),glic("l","g","X")|{"names":("gla",),"asserted_at":50}], "RD","l", want=OK)
run("D2b + Z's unrelated withdrawal stating 1e9", [G1,G1LT,GLA,A("e","RD","g"),glic("l","g","X")|{"names":("gla",),"asserted_at":50},ZO,ZW], "RD","l", want=OK)
# the same through an edge's own term? edge_term with now None reads the licence's instant; Z cannot move that.
