exec(open(__file__.replace("a1.py","lib.py")).read())
KCH = C.KCH; E0 = C.E0; klic = C.klic; glic = C.glic
RO, RA = C.RO, C.RA
RU = ST.unseat("ru","RD","d","key","RD","self",("ra",))         # RD evicts its key d
KRO, KRA = C.KRO, C.KRA
KU = ST.unseat("ku","K","d","key","K","self",("kra",))          # K evicts its key d
NA = (False, "licensure_delegator_not_authority"); NR = (False, "authority_not_reached"); OK = (True, None)
print("== evicted key of a person")
run("E1 K evicts d; d's licence naming the eviction (control)", [E0,KRO,KRA,KU,klic("l",signer="d",names=("ku",))], "RD","l",KCH, want=NA)
run("E2 K evicts d; d's licence naming only kra (backdated)", [E0,KRO,KRA,KU,klic("l",signer="d",names=("kra",))], "RD","l",KCH, want=NA)
run("E3 RD evicts d; d writes RD's edge to Z naming only ra; Z's licence", [RO,RA,RU,A("e","d","Z",on_behalf="RD",names=("ra",)),CH.licensure("l","Z","Z",M)], "RD","l",{"Z":(M,)}, want=NR)
run("E4 RD evicts d; d withdraws RD's edge e to K naming ra,e", [RO,RA,E0,RU,ST.withdraw("w","d","e",("ra",)),klic("l")], "RD","l",KCH, want=OK)
print("== lock")
G1, G1LO, GLA, G1LD = C.G1, C.G1LO, C.GLA, C.G1LD
run("K1 locked community: quorum licence naming ld (control)", [G1,G1LD,A("e","RD","g"),glic("l","g",cosigners=("B",))|{"names":("ld",)}], "RD","l", want=(False,"licensure_authority_locked"))
run("K2 locked community: quorum licence naming only g (backdated)", [G1,G1LD,A("e","RD","g"),glic("l","g",cosigners=("B",))], "RD","l", want=(False,"licensure_authority_locked"))
run("K3 lone holder's edge f before the lock; lock; walk through f", [G1,A("e","RD","g",depth=1),A("f","A","K",on_behalf="g",names=("g",)),G1LD,klic("l")], "RD","l",KCH, want=NR)
run("K4 after the lock A (ex-holder) writes edge f naming only g (backdated)", [G1,G1LD,A("e","RD","g",depth=1),A("f","A","K",on_behalf="g",names=("g",)),klic("l")], "RD","l",KCH, want=NR)
print("== license seat ends")
GD, GLO, GLU = C.GD, C.GLO, C.GLU
run("S1 duty holders withdraw X's seat (unseat glu); X's licence naming glu (control)", [GD,A("e","RD","g"),GLO,GLA,GLU,glic("l","g","X")|{"names":("glu",)}], "RD","l", want=NA)
run("S2 same; X's licence naming only gla (concurrent with glu)", [GD,A("e","RD","g"),GLO,GLA,GLU,glic("l","g","X")|{"names":("gla",)}], "RD","l", want=(False,"licensure_link_withdrawn"))
G1LT = C.G1LT
run("S3 seat term 10..100; licence with no asserted_at after lock", [G1,G1LT,GLA,G1LD,A("e","RD","g"),glic("l","g","X")|{"names":("ld",)}], "RD","l", want=NA)
run("S4 seat term 10..100; licence states asserted_at 50 (any real time)", [G1,G1LT,GLA,G1LD,A("e","RD","g"),glic("l","g","X")|{"names":("ld",),"asserted_at":50}], "RD","l")
print("== protocol tightened, officer removed")
AFD = C.AFD
AMD = ST.offer("amd","A",(),"record","af","group",("af",),head=("af",),cosigners=("B","C"),counted=ST.OFFICER,consensus_protocol="unanimous",declared_cohort="affiliations",licence_classes=((M,True),(L,False)))
run("P1 af amends to unanimous; two officers' licence naming amd (control)", [AFD,AMD,A("e","RD","af"),glic("l",cosigners=("B",))|{"names":("amd",)}], "RD","l", want=NA)
run("P2 same; two officers' licence naming only af (backdated)", [AFD,AMD,A("e","RD","af"),glic("l",cosigners=("B",))], "RD","l", want=NA)
