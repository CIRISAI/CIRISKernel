import sys, os
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import check_charter as CC
ST = CC.ST
OB, SA, SAA2, A1O, A1OB, RMB = CC.OB, CC.SA, CC.SAA2, CC.A1O, CC.A1OB, CC.RMB
def run(name, rows, concl, asks):
    print("%-96s %s" % (name, sorted(CC.countersign_answers((name, rows, concl, asks), every_order=True))))
REC2 = dict(A1O, official="A2", names=("ob",))
# P1 the record names A2 official; A's binding of A2 is NOT in the removal's past (concurrent)
run("P1 official A2; SA/aa2 concurrent with the removal (A2's voice on it)",
    [OB, SA, SAA2, REC2, A1OB, dict(RMB(cos=("A2",)), names=("a1b", "ob"))], {"rm": 1}, [("B", "a1", None)])
# P3 the binding after the removal
run("P3 official A2; aa2 after the removal (names rm)",
    [OB, SA, REC2, A1OB, dict(RMB(cos=("A2",)), names=("a1b", "ob")), dict(SAA2, names=("SA", "rm"))], {"rm": 1}, [("B", "a1", None)])
# P2 the overseer R1 is a key of A's person (A's self roster holds R1)
SAR = ST.offer("ar1", "A", "R1", "self", "SA", "group", ("SA",), head=("SA",), policy="self_roster_add", counted="self", cosigners=("R1",))
run("P2 overseer R1 bound into A's self roster (in the act's past); R1's voice on A's removal",
    [OB, SA, SAR, dict(A1O, names=("ar1", "ob")), A1OB, dict(RMB(cos=("R1",)), names=("a1b", "ob", "ar1"))], {"rm": 1}, [("B", "a1", None)])
# P4 A2 bound to A, then removed from A's self roster in the act's past; A2 official
RMA2 = ST.unseat("xa2", "A", "A2", "self", "SA", "group", ("aa2",), head=("aa2",), policy="self_roster_remove", counted="self")
run("P4 A binds A2 then removes it from its self roster; A2 (official) on the removal",
    [OB, SA, SAA2, RMA2, dict(REC2, names=("xa2", "ob")), A1OB, dict(RMB(cos=("A2",)), names=("a1b", "ob", "xa2"))], {"rm": 1, "xa2": 1}, [("B", "a1", None)])
