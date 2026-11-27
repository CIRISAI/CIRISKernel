import sys; sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode=True
import seat as ST, window as WN
CK=ST.CK; RULE=lambda r,P,past: WN.rule(r,P,past)
M=("m1","m2","m3","m4")
g=ST.found("g","m1",M,{"moderate":M},cosigners=M[1:])
om=ST.offer("om","m1","z","member","g","self",("g",),cosigners=("z",))
S=CK.concluded(CK.kept([g,om]),RULE); print("main: m1 alone admits z:", S.C.get("om"), "z" in ST.Seats(S).holders("member","g"))
g2=ST.found("g","m1",M,cosigners=M[1:])
of=ST.offer("of","m1","z","founder","g","self",("g",),cosigners=("z",))
S=CK.concluded(CK.kept([g2,of]),RULE); print("main: m1 alone seats z founder:", S.C.get("of"), "z" in ST.Seats(S).holders("member","g"))
