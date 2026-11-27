exec(open(__file__.replace("n3.py","lib.py")).read())
KCH = C.KCH; klic = C.klic; glic = C.glic
NA = (False,"licensure_delegator_not_authority"); NR = (False,"authority_not_reached"); OK=(True,None)
G2 = ST.found("g","A",("A","B","C"),{"moderate":("A","B"),"review":("A",)},cosigners=("B","C"),licence_classes=((M,False),))
GLO, GLA = C.GLO, C.GLA
LDR = ST.withdraw("ldr","A","g",(),scope="review")             # A lays down review only; still holds moderate
duty = lambda S: sorted(ST.Seats(S).holders("duty","g"))
run("N6 A lays down review (still moderate) concurrent with A,B's license seat for X", [G2,LDR,A("e","RD","g"),GLO,GLA,glic("l","g","X")|{"names":("gla",)}], "RD","l", want=OK, extra=duty)
run("N6c control: no lay-down", [G2,A("e","RD","g"),GLO,GLA,glic("l","g","X")|{"names":("gla",)}], "RD","l", want=OK)
EDGE = A("f","A","K",on_behalf="g",names=("g",),cosigners=("B",))
run("N6b same lay-down concurrent with A,B's onward edge (the edge's own past: g)", [G2,LDR,A("e","RD","g",depth=1),EDGE,klic("l")], "RD","l",KCH, want=OK)
# an unrelated withdrawal by A over g: A withdraws its acceptance of a detect seat
DT = ST.offer("dt","A","A","detect","g","self",("g",)); 
WDT = ST.withdraw("wdt","A","dt",("dt",))
run("N6d A withdraws its own detect seat, concurrent with the license seat", [G2,DT,WDT,A("e","RD","g"),GLO,GLA,glic("l","g","X")|{"names":("gla",)}], "RD","l", want=OK)
# solo founder
GS = ST.found("g","A",("A",),{},licence_classes=((M,False),))
run("N7 room founded by A alone (no map): A's edge for g", [GS,A("e","RD","g",depth=1),A("f","A","K",on_behalf="g",names=("g",)),klic("l")], "RD","l",KCH, extra=duty)
run("N7b A's quorum licence for g", [GS,A("e","RD","g"),glic("l","g")], "RD","l", extra=duty)
# edge term judged at the licence's own word
ET = dict(A("e","RD","K"), asserted_at=0, expires_at=100)
run("N8 reader's edge expires 100; licence (no past instants) states 50, no now", [ET,klic("l")|{"asserted_at":50}], "RD","l",KCH)
run("N8b same, licence states 150", [ET,klic("l")|{"asserted_at":150}], "RD","l",KCH)
run("N8c same, licence states no instant", [ET,klic("l")], "RD","l",KCH)
