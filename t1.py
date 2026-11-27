import sys
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import check_agent_seat as C
ST, WN, CK = C.ST, C.WN, C.CK
rows = C.W3 + [C.lone("x", "p1", "p2", ("ag",))]   # scope agent, p2 is a person moderator
S = CK.concluded(CK.kept(list(rows)), C.RULE)
Q = ST.Seats(S)
print("x concludes:", bool(S.C.get("x")))
print("p2 moderate:", Q.stands("p2", "moderate", "g"), "p2 member:", Q.stands("p2", "member", "g"))
print("members:", sorted(Q.holders("member","g")), "duty:", sorted(Q.holders("duty","g")))
