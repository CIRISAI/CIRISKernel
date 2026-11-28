exec(open(__file__.replace("probe2.py","lib.py")).read())
GS = ST.found("g","A",("A",),{},licence_classes=((M,False),))
ADM = [ST.offer("m"+k,"A",(k,),"member","g","group",("g",),head=("g",),cosigners=(k,),policy="community_invite") for k in "CD"]
duty = lambda S: sorted(ST.Seats(S).holders("duty","g"))
for nm, rows in (
    ("two-key, names mC,mD", [ST.offer("dcd","A",("C","D"),"moderate","g","self",("mC","mD")), ST.accept("dac","C","dcd"), ST.accept("dad","D","dcd")]),
    ("one key C, names mC", [ST.offer("dc","A",("C",),"moderate","g","self",("mC",)), ST.accept("dac","C","dc")]),
    ("one key C, names g only", [ST.offer("dc","A",("C",),"moderate","g","self",("g",)), ST.accept("dac","C","dc")]),
):
    S = arrive([GS]+ADM+rows); print(nm, {r["id"]: S.C.get(r["id"]) for r in rows}, duty(S), sorted(ST.Seats(S).holders("member","g")))
G1 = C.G1
for nm, rows in (("G1 two-key to B,C", [ST.offer("dcd","A",("B","C"),"moderate","g","self",("g",)), ST.accept("dab","B","dcd"), ST.accept("dac","C","dcd")]),):
    S = arrive([G1]+rows); print(nm, {r["id"]: S.C.get(r["id"]) for r in rows}, duty(S))
