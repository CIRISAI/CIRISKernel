exec(open(__file__.replace("k2.py","lib.py")).read())
import check_duty_seats as DS
glic = C.glic
NA=(False,"licensure_delegator_not_authority")
R10 = dict(DS._R10, licence_classes=((M,False),)); RDDE, RC2, RSYB = DS._RDDE, DS._RC2, DS._RSYB
def seat(rows, own=None):
    S = arrive(rows); Q = ST.Seats(ST.reader_state(S, own) if own else S, own=own)
    return {k: Q.stands(k,"moderate","g") for k in "DFI"}
print("seat walk, their rows: fresh reader", seat([R10,RDDE,RC2,RSYB]), " no c2:", seat([R10,RDDE,RSYB]))
GL = ST.offer("glo","A",("X",),"license","g","group",("c2","syb"),head=("c2","syb"),cosigners=("B","F","G","H","I"),counted="duty"); GLA = ST.accept("gla","X","glo")
LX = glic("l","g","X")|{"names":("gla",)}
run("T1 trust walk, their rows + A,B,F..I license (heads c2, syb)", [R10,RDDE,RC2,RSYB,GL,GLA,A("e","RD","g"),LX], "RD","l", want=NA)
GL0 = dict(GL, names=("dde","syb"), head=("dde","syb"))
try: run("T2 same, the licence's conferral names dde,syb (not c2); reader holds c2", [R10,RDDE,RC2,RSYB,GL0,GLA,A("e","RD","g"),LX], "RD","l", want=NA)
except KeyError as e: print("T2 CRASH: KeyError", e)
# my B8: the later row by the signers is a license conferral (not a duty)
GY = ST.offer("gy","A",("Y",),"license","g","group",("dde",),head=("dde",),cosigners=("B","D"),counted="duty"); GYA = ST.accept("gya","Y","gy")
print("seat walk, B8 (later row a license conferral):", seat([R10,RDDE,GY,GYA,RSYB]))
AK = CK.row("ak","ack","A",("dde",),room="g",head=("dde",))
print("seat walk, B10 (A's ack of dde):", seat([R10,RDDE,AK,RSYB]))
RK = CK.row("rk","ack","R",("dde",),room="g",head=("dde",))
print("seat walk, B9 reader R acked dde:", seat([R10,RDDE,RK,RSYB],"R"))
