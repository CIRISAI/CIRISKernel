import sys, os, csv
W = sys.argv[1]
sys.path.insert(0, os.path.join(W, "models", "causal_kernel"))
import window as WN
path = os.path.join(W, "models", "causal_kernel", "window_adversary.tsv")
H = ["window","case","landing_concluded","void","contest","recount","property","void_holds","contest_holds","recount_holds"]
def hv(x): return "-" if x is None else ("holds" if x else "BROKEN")
lines = ["\t".join(H)]
for t in WN.adversary_table():
    lines.append("\t".join([t["window"], t["case"], str(t["landing_concluded"])] + [t["outcome"][h] for h in WN.RULES] + [t["property"]] + [hv(t["holds"][h]) for h in WN.RULES]))
new = "\n".join(lines) + "\n"
old = open(path, encoding="utf-8").read()
if "--write" in sys.argv:
    open(path, "w", encoding="utf-8").write(new); print("written", len(lines)-1)
else:
    o, n = old.splitlines(), new.splitlines()
    print("same" if old == new else "differs", len(o), len(n))
    for l in o:
        if l not in n: print("- " + l[:300])
    for l in n:
        if l not in o: print("+ " + l[:300])
