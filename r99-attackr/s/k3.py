exec(open(__file__.replace("k3.py","lib.py")).read())
import check_duty_seats as DS, traceback
glic = C.glic
R10 = dict(DS._R10, licence_classes=((M,False),)); RDDE, RC2, RSYB = DS._RDDE, DS._RC2, DS._RSYB
GL0 = ST.offer("glo","A",("X",),"license","g","group",("dde","syb"),head=("dde","syb"),cosigners=("B","F","G","H","I"),counted="duty"); GLA = ST.accept("gla","X","glo")
LX = glic("l","g","X")|{"names":("gla",)}
rows = [R10,RDDE,RC2,RSYB,GL0,GLA,A("e","RD","g"),LX]
S = arrive(rows); print("concluded:", {r["id"]: S.C.get(r["id"]) for r in rows if r["id"] in ("dde","c2","syb","glo")})
import random
crash = 0
for i in range(40):
    t = list(rows); random.Random(i).shuffle(t)
    try: TR.read_licence(arrive(t),"RD","l",now=NOW)
    except KeyError: crash += 1
print("crash in %d/40 orders" % crash)
# minimal: without the licence, just Seats + edges?
try: print("standing only:", TR.standing(S,"l","RD"))
except KeyError as e: print("standing crashes:", e)
