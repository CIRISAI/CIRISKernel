import sys; sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode=True
import check_key_person as KP
ST,CK,WN=KP.ST,KP.CK,KP.WN
import inspect; print(inspect.signature(WN.opener))
S1=KP.found("S1","p1"); A=KP.add("a1b","S1","p1b",("p1",),("S1",))
S1x=KP.found("S1x","p1"); D=KP.add("ad","S1x","d",("p1",),("S1x",))
op=WN.opener("op","p1","self_roster_add","S1",("a1b",))
op=dict(op, to=("k7",))
def out(rows): return WN.outcome(CK.concluded(CK.kept(rows),KP.RULE_W),"op","recount")
base=[S1,A,S1x,D,op]
print("none:", out(base))
print("p1 withdraws:", out(base+[WN.answer("w","p1","op","withdraw",("op","ad"))]))
print("d (p1's key in another roster p1 founded) withdraws:", out(base+[WN.answer("w","d","op","withdraw",("op","ad"))]))
print("p1b withdraws:", out(base+[WN.answer("w","p1b","op","withdraw",("op","ad"))]))
