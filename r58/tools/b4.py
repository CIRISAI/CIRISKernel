import sys
sys.path.insert(0, sys.argv[1])
import seat as ST, window as WN
CK = ST.CK
RULE = lambda r, P, past: WN.rule(r, P, past)
G = ST.offer("g", "A", ("A", "B", "C", "D"), "member", "@", "self", cosigners=("B", "C", "D"))
o = ST.offer("o", "A", "X", "member", "g", "self", ("g",), cosigners=("X",))
S = CK.concluded(CK.kept([G, o]), RULE); Q = ST.Seats(S)
print("founder A alone seats X:", Q.stands("X", "member", "g"))
