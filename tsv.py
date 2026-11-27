import sys
root = sys.argv[1]
sys.path.insert(0, root + "/models/causal_kernel"); sys.dont_write_bytecode = True
import window as W
cols = ["window", "case", "landing_concluded", "void", "contest", "recount", "property", "void_holds", "contest_holds", "recount_holds"]
out = ["\t".join(cols)]
tot = {h: 0 for h in W.RULES}; checks = 0; rows = 0
for t in W.adversary_table():
    rows += 1
    h = lambda r: "-" if t["needs"] is None else ("holds" if t["holds"][r] else "BROKEN")
    if t["needs"] is not None:
        checks += 1
        for r in W.RULES: tot[r] += not t["holds"][r]
    out.append("\t".join([t["window"], t["case"], str(t["landing_concluded"])] + [t["outcome"][r] for r in W.RULES] + [t["property"]] + [h(r) for r in W.RULES]))
text = "\n".join(out) + "\n"
if len(sys.argv) > 2: open(sys.argv[2], "w").write(text)
else: sys.stdout.write(text)
print("rows %d checks %d broken %s" % (rows, checks, tot), file=sys.stderr)
