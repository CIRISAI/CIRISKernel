"""Run a check module's main() with the prototype switched on: proto_run.py <tree> <check> [fold]"""
import sys, os, runpy
tree, mod = sys.argv[1], sys.argv[2]
on = len(sys.argv) > 3
d = os.path.join(tree, "models/causal_kernel")
sys.path.insert(0, d)
import seat as ST
if on: ST.PROTO.update(sys.argv[3].split(","))
sys.argv = [os.path.join(d, mod + ".py")]
runpy.run_path(sys.argv[0], run_name="__main__")
