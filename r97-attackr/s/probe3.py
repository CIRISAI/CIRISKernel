exec(open(__file__.replace("probe3.py","lib.py")).read())
AFD = C.AFD
AMD = ST.offer("amd","A",(),"record","af","group",("af",),head=("af",),cosigners=("B","C"),counted=ST.OFFICER,consensus_protocol="unanimous",declared_cohort="affiliations",licence_classes=((M,True),(L,False)))
S = arrive([AFD,AMD]); print("amd without policy concludes:", S.C.get("amd"))
S = arrive([AFD,dict(AMD,policy="cosigned_act")]); print("amd with cosigned_act concludes:", S.C.get("amd"))
P1 = [AFD,dict(AMD,policy="cosigned_act"),A("e","RD","af"),C.glic("l",cosigners=("B",))|{"names":("amd",)}]
S = arrive(P1); print("P1 with policy:", TR.read_licence(S,"RD","l",now=NOW))
P2 = [AFD,dict(AMD,policy="cosigned_act"),A("e","RD","af"),C.glic("l",cosigners=("B",))]
S = arrive(P2); print("P2 with policy:", TR.read_licence(S,"RD","l",now=NOW))
