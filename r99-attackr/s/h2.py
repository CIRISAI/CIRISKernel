exec(open(__file__.replace("h2.py","lib.py")).read())
import check_election as EL
glic = C.glic
OK=(True,None); NA=(False,"licensure_delegator_not_authority"); LW=(False,"licensure_link_withdrawn")
duty = lambda S: sorted(ST.Seats(S).holders("duty","g"))
G = ST.found("g","A",tuple("ABCDEFGH"),{"moderate":("A","B","C")},cosigners=tuple("BCDEFGH"),licence_classes=((M,False),))
GLA = ST.accept("gla","X","glo"); LX = glic("l","g","X")|{"names":("gla",)}
conf = lambda i, to, voices, heads=("g",), names=None: ST.offer(i,voices[0],to,"moderate","g","group",tuple(names or heads),head=heads,cosigners=tuple(voices[1:])+tuple(to),counted="duty",policy="duty_confer")
print("== batch at the same heads, one voice extra or missing")
DDE3 = conf("dde",("D","E"),("A","B","C"))
run("M1 A,B,C seat D,E at g; later A,B (C missing) seat F at g", [G,DDE3,conf("ff",("F",),("A","B")),A("e","RD","g"),glic("l","g","Q")], "RD","l", extra=lambda S:(bool(S.C.get("ff")),duty(S)))
DDE2 = conf("dde",("D","E"),("A","B"))
run("M2 A,B seat D,E at g; later A,B,C (C extra) seat F at g", [G,DDE2,conf("ff",("F",),("A","B","C")),A("e","RD","g"),glic("l","g","Q")], "RD","l", extra=lambda S:(bool(S.C.get("ff")),duty(S)))
run("M3 A,B seat D,E at g; later A,B,D (D seated by dde, not a holder at g) seat F at g", [G,DDE2,conf("ff",("F",),("A","B","D")),A("e","RD","g"),glic("l","g","Q")], "RD","l", extra=lambda S:(bool(S.C.get("ff")),duty(S)))
print("== an end whose own past contains the act")
DCC = conf("dcc",("D",),("A","B","C")); DCA = ST.accept("dca","D","dcc")
GLO = ST.offer("glo","A",("X",),"license","g","group",("g",),head=("g",),cosigners=("B",),counted="duty")
WDc = ST.withdraw("wd","D","dcc",("dca","dcc"))
WDa = ST.withdraw("wd","D","dcc",("dca","dcc","glo"))
run("N1 D seated concurrently; D withdraws, NOT naming glo: 2 of 3", [G,DCC,DCA,WDc,GLO,GLA,A("e","RD","g"),LX], "RD","l", want=OK)
run("N2 D withdraws naming glo (the act in the end's past): by ancestry 2 of 4", [G,DCC,DCA,WDa,GLO,GLA,A("e","RD","g"),LX], "RD","l")
print("== an acceptance of an offer partly in the act's past")
DDE = conf("dde",("D","E"),("A","B","C"))
DAD = ST.accept("dad","D","dde"); DAE = ST.accept("dae","E","dde")
GLO2 = ST.offer("glo","A",("X",),"license","g","group",("dde","dad"),head=("dde",),cosigners=("B","C"),counted="duty")   # A,B,C: 3 of 4 at its head
GLO3 = dict(GLO2, cosigners=("B",))                                                                                    # A,B: 2 of 4 at its head
run("P1 dde (D,E) in glo's past, D accepted there, E accepts concurrently; A,B,C confer (3 of 5)", [G,DDE,DAD,GLO2,GLA,DAE,A("e","RD","g"),LX], "RD","l", want=OK, extra=duty)
run("P2 same, A,B confer (2 of 4 at its head, 2 of 5 held)", [G,DDE,DAD,GLO3,GLA,DAE,A("e","RD","g"),LX], "RD","l", want=NA, extra=duty)
HDS = ST.offer("hds","A",("D",),"moderate","g","group",("g",),head=("g",),cosigners=("B","C","D"),counted="duty",policy="duty_confer")
OFF2 = conf("off2",("E",),("A","B","C"),heads=("hds",))     # heads in glo's past, the offer itself concurrent
GLO4 = ST.offer("glo","A",("X",),"license","g","group",("hds",),head=("hds",),cosigners=("B",),counted="duty")   # A,B of A,B,C,D
run("P3 an offer whose head (hds) is in glo's past but the offer is concurrent; E accepts", [G,HDS,OFF2,ST.accept("oe","E","off2"),GLO4,GLA,A("e","RD","g"),LX], "RD","l", want=NA, extra=duty)
print("== the election seating beside a conferral")
G5, LM, H5, EC = EL.G5, EL.LM, EL.H5, EL.EC
G5c = dict(G5, licence_classes=((M,False),))
GA = ST.offer("glo","A",("X",),"license","g","group",("g",),head=("g",),counted="duty")     # A alone, before its lay-down
run("L1 A (lone) confers license from g, concurrent with its lay-down and the election of C", [G5c,LM]+H5+[EC,GA,GLA,A("e","RD","g"),LX], "RD","l", want=LW, extra=duty)
GC = ST.offer("glo","C",("X",),"license","g","group",("ec",),head=("ec",),counted="duty")
run("L2 control: C (elected) confers license after ec", [G5c,LM]+H5+[EC,GC,GLA,A("e","RD","g"),LX], "RD","l", want=OK, extra=duty)
