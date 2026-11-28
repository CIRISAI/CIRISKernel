import sys, os
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import check_charter as CC
ST = CC.ST
ONE, RMB, CS = CC.ONE, CC.RMB, CC.CS
def run(name, rows, concl, asks):
    print("%-90s %s" % (name, sorted(CC.countersign_answers((name, rows, concl, asks), every_order=True))))
run("control: rm + CS(O)", ONE + [RMB(), CS("O")], {"rm": 1, "cs": 1}, [("B", "a1", None)])
# G15 as written: O's voice is ON the act's row (a cosigner), and bridged as a Countersign row of it
run("G15: rm cosigned by O on its row, and the bridged CS(O)", ONE + [RMB(cos=("O",)), CS("O")], {"rm": 1, "cs": 1}, [("B", "a1", None)])
run("G15: rm cosigned by O, no bridge row", ONE + [RMB(cos=("O",))], {"rm": 1}, [("B", "a1", None)])
# the same voice bridged twice (two Countersign rows of one key)
run("two bridged rows of one key O", ONE + [RMB(), CS("O"), CS("O", i="cs2")], {"cs": 1, "cs2": 1}, [("B", "a1", None)])
# a bridged row whose signer is ineligible (a member, the target, the seat)
run("bridged CS by the target B", ONE + [RMB(), CS("B")], {"cs": 1}, [("B", "a1", None)])
run("bridged CS by X (no seat)", ONE + [RMB(), CS("X")], {"cs": 1}, [("B", "a1", None)])
# a bridged CS that is NOT in the act's future (concurrent: on the wire it is on the act row, so it is the act itself)
run("CS(O) naming nothing (concurrent with rm)", ONE + [RMB(), CS("O", names=())], {"cs": 1}, [("B", "a1", None)])
# under G15 the countersign is the act row itself: a later withdrawal names the act (and so has the voice in its past),
# but the bridged view is a separate row that withdrawal does not name
WD = ST.withdraw("wrm", "A", "rm", ("rm",))
run("bridged CS(O); A's later withdrawal names rm only (not the view)", ONE + [RMB(), CS("O"), WD], {"cs": 1, "wrm": 1}, [("B", "a1", None)])
run("control: the withdrawal names the CS row", ONE + [RMB(), CS("O"), ST.withdraw("wrm", "A", "rm", ("cs",))], {"cs": 1, "wrm": 1}, [("B", "a1", None)])
