exec(open(__file__.replace("probe4.py","lib.py")).read())
import check_election as EL
G5c = dict(EL.G5, licence_classes=((M,False),))
for heads in (("ec",),("lm",),("ec","lm")):
    GC = ST.offer("glo","C",("X",),"license","g","group",heads,head=heads,counted="duty"); GLA = ST.accept("gla","X","glo")
    rows = [G5c,EL.LM]+EL.H5+[EL.EC,GC,GLA,A("e","RD","g"),C.glic("l","g","X")|{"names":("gla",)}]
    S = arrive(rows); Q = ST.Seats(S)
    print(heads, "glo", S.C.get("glo"), "license", sorted(Q.holders("license","g")), "duty", sorted(Q.holders("duty","g")), TR.read_licence(S,"RD","l",now=NOW))
