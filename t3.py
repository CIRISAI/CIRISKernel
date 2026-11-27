import sys
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import check_agent_seat as C
ST, CK = C.ST, C.CK
w = ST.withdraw("w", "p2", "g", ("ag",)); w = dict(w, scope="agent")
S = CK.concluded(CK.kept(C.W3 + [w]), C.RULE)
Q = ST.Seats(S)
print("w concl", bool(S.C.get("w")), "p2 member", Q.stands("p2","member","g"), "p2 moderate", Q.stands("p2","moderate","g"))
