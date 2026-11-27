import sys
sys.path.insert(0, sys.argv[1])
import seat as ST
CK, R = ST.CK, ST.R
rows = [ST.offer("0", "1", ("1",), "member", "@", "self")]
rows += [ST.offer("o2", "1", "2", "member", "0", "self", ("0",), cosigners=("2",)),
         ST.offer("f3", "1", "3", "founder", "0", "self", ("0",), cosigners=("3",))]
rows += [ST.withdraw("w2", "2", "o2", ("o2",))]
rows += [R("v1", "note", "1", ("0", "o2", "f3")), R("v2", "note", "1", ("w2", "f3"))]
RULE = lambda r, P, past: ST.seat_rule(r, P, past)
S = CK.concluded(CK.kept(rows), RULE)
print({r["id"]: S.C.get(r["id"]) for r in rows})
P = S.Cs; past = lambda a, b: a in S.anc[b]
for h in (("v1",), ("v2",)):
    print(h, ST.members_at(P, past, "0", h), ST.members_at(P, past, "0", h, "founder"))
