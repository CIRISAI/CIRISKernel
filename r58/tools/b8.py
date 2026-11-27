import sys
sys.path.insert(0, sys.argv[1])
import seat as ST, check_acts as AC
r = AC.grp("r", "offer", "X", None, "accord_halt")
by = {"g": AC.GM4, "r": r}
try: print(ST.act_of(r, by))
except Exception as e: print("act_of raised", type(e).__name__, e)
el = AC.grp("e", "offer", "B", "review", "moderator_election", counted="member")
print("ranked offer of review:", ST.act_of(el, {"g": AC.FH, "e": el}))
