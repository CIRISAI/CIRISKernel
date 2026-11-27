exec(open(__file__.replace("probe.py","lib.py")).read())
G1 = C.G1
DC = ST.offer("dc","A","C","moderate","g","self",("g",)); DCA = ST.accept("dca","C","dc")
for heads in (("g",),("dc",),("dca",)):
    for cos in (("C",),()):
        g = ST.offer("glo","A",("X",),"license","g","group",("dca",),head=heads,cosigners=cos,counted="duty")
        S = arrive([G1,DC,DCA,g]); print(heads, cos, S.C.get("glo"))
g = ST.offer("glo","A",("X",),"license","g","group",("g",),head=("g",),counted="duty")
print("no dc:", arrive([G1,g]).C.get("glo"))
WC = ST.withdraw("wc","C","g",("dca",))
S = arrive([G1,DC,DCA,WC]); Q=ST.Seats(S)
print("after C withdraws g: wc concl", S.C.get("wc"), "members", sorted(Q.holders("member","g")), "duty", sorted(Q.holders("duty","g")))
DC1 = ST.offer("dc1","A","C","moderate","g","self",("g",)); DA1 = ST.accept("da1","C","dc1")
DC2 = ST.offer("dc2","A","B","moderate","g","self",("g",)); DA2 = ST.accept("da2","B","dc2")
g2 = ST.offer("glo","A",("X",),"license","g","group",("da1",),head=("dc1",),cosigners=("C",),counted="duty"); GLA=ST.accept("gla","X","glo")
S = arrive([G1,DC1,DA1,DC2,DA2,g2,GLA]); Q=ST.Seats(S)
print("F4d glo concl", S.C.get("glo"), "license holders", sorted(Q.holders("license","g")), "tips", [t["id"] for t in Q.tips("g")])
S2 = arrive([G1,DC1,DA1,g2,GLA]); print("   without dc2: license", sorted(ST.Seats(S2).holders("license","g")))
l = C.glic("l","g","X")|{"names":("gla",)}
S = arrive([G1,DC1,DA1,DC2,DA2,g2,GLA,TR.accepts("e","RD","g")|{"asserted_at":0,"expires_at":10**6},l])
print("   standing:", TR.standing(S,"l","RD"), "issuance own past:", TR.issuance(TR.ended_for_reader(S,S.by["l"],False),S.by["l"]), "with read:", TR.issuance(TR.ended_for_reader(S,S.by["l"]),S.by["l"]))
