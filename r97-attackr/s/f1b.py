exec(open(__file__.replace("f1b.py","lib2.py")).read())
glic = C.glic; KCH = C.KCH; klic = C.klic
OK=(True,None); NA=(False,"licensure_delegator_not_authority"); LW=(False,"licensure_link_withdrawn"); NR=(False,"authority_not_reached")
AF1 = dict(C.AFD1, official="O")                                  # one officer A
AF3 = dict(C.AFD, official="O")                                   # officers A, B, C
off = lambda S: sorted(ST.Seats(S).holders(ST.OFFICER,"af"))
AOBO = dict(C.R_AOB, cosigners=("B","O"))                         # A appoints B officer, O countersigns
LSA = ST.accept("lsa","X","lso"); LX = glic("l","af","X")|{"names":("lsa",)}
def lso(signers, policy, heads=("af",), names=None):
    return ST.offer("lso",signers[0],("X",),"license","af","group",tuple(names or heads),head=heads,cosigners=tuple(signers[1:]),counted=ST.OFFICER,policy=policy)
print("== policy mismatches")
run("P1 one officer, A + O, policy affiliation_member_action (as ruled)", [AF1,lso(("A","O"),"affiliation_member_action"),LSA,A("e","RD","af"),LX], "RD","l", want=OK)
run("P2 one officer, A + O, policy cosigned_act", [AF1,lso(("A","O"),"cosigned_act"),LSA,A("e","RD","af"),LX], "RD","l", want=NA)
run("P3 one officer, A alone, policy cosigned_act", [AF1,lso(("A",),"cosigned_act"),LSA,A("e","RD","af"),LX], "RD","l", want=NA)
run("P4 three officers, A + O, policy affiliation_member_action", [AF3,lso(("A","O"),"affiliation_member_action"),LSA,A("e","RD","af"),LX], "RD","l", want=NA)
run("P5 three officers, A,B, policy cosigned_act (as ruled)", [AF3,lso(("A","B"),"cosigned_act"),LSA,A("e","RD","af"),LX], "RD","l", want=OK)
run("P6 three officers, A,B + O, policy affiliation_member_action", [AF3,lso(("A","B","O"),"affiliation_member_action"),LSA,A("e","RD","af"),LX], "RD","l", want=NA)
print("== the officer count changing concurrently")
WB = ST.withdraw("wb","B","aob",("aob",))
base = [AF1,AOBO]
run("Q0 control: officers A,B; A,B confer under cosigned_act", base+[lso(("A","B"),"cosigned_act",("aob",)),LSA,A("e","RD","af"),LX], "RD","l", want=OK, extra=off)
run("Q1 B resigns concurrently: A alone remains, no countersign", base+[WB,lso(("A","B"),"cosigned_act",("aob",)),LSA,A("e","RD","af"),LX], "RD","l", want=LW, extra=off)
run("Q2 A alone (1 of 2) under cosigned_act, B resigns concurrently", base+[WB,lso(("A",),"cosigned_act",("aob",)),LSA,A("e","RD","af"),LX], "RD","l", want=NA, extra=off)
run("Q3 A + O under affiliation_member_action at aob (two officers then), B resigns concurrently", base+[WB,lso(("A","O"),"affiliation_member_action",("aob",)),LSA,A("e","RD","af"),LX], "RD","l", extra=off)
AOB_NOO = C.R_AOB
run("Q4 A + O under affiliation_member_action from af, concurrent with countersigned aob (growth)", [AF1,AOBO,lso(("A","O"),"affiliation_member_action"),LSA,A("e","RD","af"),LX], "RD","l", want=NA, extra=off)
print("== the onward edge and the licence, one officer")
run("E1 A's edge for af with O on it", [AF1,A("e","RD","af",depth=1),A("f","A","K",on_behalf="af",names=("af",),cosigners=("O",)),klic("l")], "RD","l",KCH, want=OK)
run("E2 A's edge for af with O, concurrent with countersigned aob (body grew)", [AF1,AOBO,A("e","RD","af",depth=1),A("f","A","K",on_behalf="af",names=("af",),cosigners=("O",)),klic("l")], "RD","l",KCH, want=NR, extra=off)
run("E3 A's licence with O, concurrent with countersigned aob", [AF1,AOBO,A("e","RD","af"),glic("l","af","A",cosigners=("O",))], "RD","l", want=NA, extra=off)
print("== dissolved")
DIS1 = ST.offer("dis","A",(),"record","af","group",("af",),head=("af",),cosigners=("O",),counted=ST.OFFICER,dissolved_at=100,policy="affiliation_member_action")
run("X1 countersigned dissolution; A + O licence after", [AF1,DIS1,A("e","RD","af"),glic("l","af","A",cosigners=("O",))|{"names":("dis",)}], "RD","l", want=NA, extra=lambda S: ST.Seats(S).dissolved("af"))
run("X2 countersigned dissolution; A + O licence concurrent (names af)", [AF1,DIS1,A("e","RD","af"),glic("l","af","A",cosigners=("O",))], "RD","l", want=(False,"lapsed"))
DIS0 = dict(DIS1, cosigners=())
run("X3 uncountersigned dissolution; A + O licence after", [AF1,DIS0,A("e","RD","af"),glic("l","af","A",cosigners=("O",))|{"names":("dis",)}], "RD","l", want=OK, extra=lambda S: ST.Seats(S).dissolved("af"))
