exec(open(__file__.replace("k4.py","lib.py")).read())
import check_duty_seats as DS
R10 = DS._R10; RDDE, RC2, RSYB = DS._RDDE, DS._RC2, DS._RSYB
def seat(rows, own=None):
    S = arrive(rows); Q = ST.Seats(ST.reader_state(S, own) if own else S, own=own)
    return {"later": {r["id"]: S.C.get(r["id"]) for r in rows[2:-1]}, "seated": {k: Q.stands(k,"moderate","g") for k in "DFI"}}
def later(i, scope, to, signers, heads=("dde",)):
    return ST.offer(i, signers[0], to, scope, "g", "group", heads, head=heads, cosigners=tuple(signers[1:])+tuple(x for x in ((to,) if isinstance(to,str) else to) if x not in signers), counted="duty", policy="duty_confer" if scope!="license" else None)
for nm, L in (("c2 (theirs): A,B,C confer slash on A", RC2),
              ("A,B,D confer slash on A", later("c3","slash","A",("A","B","D"))),
              ("A,B,C confer license on Y (counted duty)", later("c4","license","Y",("A","B","C"))),
              ("A,B,C,D confer moderate on J", later("c5","moderate","J",("A","B","C","D"))),
              ("C,D,E confer slash on C (no A or B)", later("c6","slash","C",("C","D","E")))):
    L = {k: v for k, v in L.items() if not (k == "policy" and v is None)}
    print("%-44s" % nm, seat([R10,RDDE,L,RSYB]))
RK = CK.row("rk","ack","R",("dde",),room="g",head=("dde",))
print("%-44s" % "reader R acked dde (line past g)", seat([R10,RDDE,RK,RSYB],"R"))
RK2 = CK.row("rk","ack","R",("c2",),room="g",head=("c2",))
print("%-44s" % "reader R acked c2 (theirs)", seat([R10,RDDE,RC2,RK2,RSYB],"R"))
