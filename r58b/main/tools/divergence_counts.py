"""Print the counts of data/divergences.json by status and by implementer, and check that
data/divergences.tsv lists the same entries. This reads the list; it does not run the cases, which
need the parent repository's toolchain (REVIEW.md, "Runs in the parent repository")."""
import collections
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, "data", "divergences.json"), encoding="utf-8"))
entries = d["entries"]
status = collections.Counter(e["status"] for e in entries)
who = collections.Counter(e["implementer"] for e in entries)
rows = [r for r in csv.DictReader((l for l in open(os.path.join(ROOT, "data", "divergences.tsv"), encoding="utf-8")
                                   if not l.startswith("#")), delimiter="\t")]
same = sorted(e["id"] for e in entries) == sorted(r["id"] for r in rows)
for k, v in sorted(status.items()):
    print("status %-14s %d" % (k, v))
for k, v in sorted(who.items()):
    print("implementer %-9s %d" % (k, v))
print("tsv lists the same %d entries: %s" % (len(entries), same))
print("divergences: %d entries; %s" % (len(entries), ", ".join("%d %s" % (v, k) for k, v in sorted(status.items()))))
sys.exit(0 if same else 1)
