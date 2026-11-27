import sys, os
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import check_charter as CC
ST, CK = CC.ST, CC.CK
OB, A1O, A1OB, RMB, CS, ONE = CC.OB, CC.A1O, CC.A1OB, CC.RMB, CC.CS, CC.ONE
def run(name, rows, concl, asks):
    got = CC.countersign_answers((name, rows, concl, asks), every_order=True)
    print("%-92s %s" % (name, sorted(got)))
    return got
# 1. an overseer seated AFTER the act: R2 given review over ob by R1 (the lone review holder), not in rm's past
RV = ST.offer("rv", "R1", "R2", "review", "ob", "group", ("ob",), head=("ob",), policy="duty_confer", counted="duty", cosigners=("R2",))
run("R2 made a review holder of ob after rm; R2 countersigns naming rv (concl cs, rm; B member?)",
    ONE + [RMB(), RV, CS("R2", ("rm", "rv"))], {"cs": 1, "rv": 1}, [("B", "a1", None)])
# 2. an overseer whose review ended BEFORE the countersign (after the act): R1 lays review down, then countersigns
LD = ST.withdraw("ld", "R1", "ob", ("ob",), scope="review")
run("R1 lays its review down after rm, then countersigns naming the lay-down",
    ONE + [RMB(), LD, CS("R1", ("rm", "ld"))], {"cs": 1, "ld": 1}, [("B", "a1", None)])
# 3. non-officer B appoints itself officer
SELF = ST.offer("sb", "B", ("B",), "member", "a1", "group", ("a1b",), head=("a1b",), counted=ST.OFFICER, role=ST.OFFICER)
run("B (a member, no officer) appoints itself officer", ONE + [SELF], {"sb": 1}, [("B", "a1", None)])
SELF2 = ST.offer("sb", "B", ("B",), ST.OFFICER, "a1", "group", ("a1b",), head=("a1b",), counted="member")
run("B confers scope officer on itself counted over members", ONE + [SELF2], {"sb": 1}, [("B", "a1", None)])
# 4. lone officer appoints a sock officer, then the two remove B: no countersign
AOC = CC.AOC
run("A appoints sock C officer; A and C remove B (no countersign)", ONE + [AOC, RMB(("aoc",), cos=("C",))], {"rm": 1}, [("B", "a1", None)])
# 5. the target countersigns its own removal (record names B the official)
A1B_OFF = CC.aff("a1", to=("A",), cls=(CC.MW,), official="B")
run("official is the target B; B countersigns its own removal", [A1B_OFF, A1OB, RMB(("a1b",)), CS("B")], {"cs": 1}, [("B", "a1", None)])
