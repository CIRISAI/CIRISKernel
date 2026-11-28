exec(open(__file__.replace("f5.py","lib.py")).read())
glic = C.glic; GD = C.GD
OK=(True,None); NA=(False,"licensure_delegator_not_authority")
AF3 = dict(C.AFD, official="O")
off = lambda S: sorted(ST.Seats(S).holders(ST.OFFICER,"af"))
ADD = ST.offer("aod","A",("D",),"member","af","group",("af",),head=("af",),cosigners=("B","D"),counted=ST.OFFICER,role=ST.OFFICER,policy="cosigned_act")
LSO = ST.offer("lso","A",("X",),"license","af","group",("af",),head=("af",),cosigners=("B",),counted=ST.OFFICER,policy="cosigned_act"); LSA = ST.accept("lsa","X","lso")
LX = glic("l","af","X")|{"names":("lsa",)}
run("Q7c control: officers ABC; A,B confer license (2 of 3)", [AF3,LSO,LSA,A("e","RD","af"),LX], "RD","l", want=OK)
run("Q7 + A,B,D appoint D officer concurrently (4 officers): A,B from af", [AF3,ADD,LSO,LSA,A("e","RD","af"),LX], "RD","l", want=NA, extra=off)
LIC = glic("l","af","A",cosigners=("B",))
run("Q7b the officers' own quorum licence A,B from af, D appointed concurrently", [AF3,ADD,A("e","RD","af"),LIC], "RD","l", want=NA, extra=off)
# community: two holders A,B; C added by counted conferral concurrently; A,B confer license from g (2 of 3 still passes); use 3 -> 5
G3 = ST.found("g","A",("A","B","C","D","E"),{"moderate":("A","B","C")},cosigners=("B","C","D","E"),licence_classes=((M,False),))
DE = ST.offer("dde","A",("D","E"),"moderate","g","group",("g",),head=("g",),cosigners=("B","C","D","E"),counted="duty",policy="duty_confer")
GAB = ST.offer("glo","A",("X",),"license","g","group",("g",),head=("g",),cosigners=("B",),counted="duty"); GLA = ST.accept("gla","X","glo")
run("Q8 holders ABC grow to ABCDE (counted, held); A,B confer license from g (2 of 3, 2 of 5)", [G3,DE,GAB,GLA,A("e","RD","g"),glic("l","g","X")|{"names":("gla",)}], "RD","l", want=NA,
    extra=lambda S:(bool(S.C.get("dde")), sorted(ST.Seats(S).holders("duty","g"))))
