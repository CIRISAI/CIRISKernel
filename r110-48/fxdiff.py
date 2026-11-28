"""Leaf diff of two JSON files. python3 -I fxdiff.py old.json new.json"""
import json, sys
a, b = (json.load(open(p)) for p in sys.argv[1:3])
out = []
def walk(x, y, path):
    if type(x) != type(y): out.append((path, str(x)[:120], str(y)[:120])); return
    if isinstance(x, dict):
        for k in sorted(set(x) | set(y)):
            if k not in x or k not in y: out.append((path + "/" + k, str(x.get(k))[:120], str(y.get(k))[:120]))
            else: walk(x[k], y[k], path + "/" + k)
    elif isinstance(x, list):
        if len(x) != len(y): out.append((path, "len %d" % len(x), "len %d" % len(y)))
        for i, (p, q) in enumerate(zip(x, y)): walk(p, q, "%s[%d]" % (path, i))
    elif x != y: out.append((path, str(x)[:120], str(y)[:120]))
walk(a, b, "")
print(len(out), "differences")
for o in out[:12]: print("  ", o)
