import sys; sys.path.insert(0, ".")
import check_removal_in_force as C, seat as ST, checkpoint as CK
name = sys.argv[1]; rid = sys.argv[2]
case = [c for c in C.CASES if c[0].startswith(name)][0]
rows = case[1]
for r in rows: print(r["id"], r["kind"], r.get("signer"), "head", r.get("head"), "names", r.get("names"), r.get("target") or r.get("of") or "")
S = C.CK.concluded(C.CK.kept(list(rows)), C.RULE)
x = [r for r in rows if r["id"] == rid][0]
P = [q for q in S.Cs if q["id"] in S.anc.get(rid, ())]
past = lambda a, b: a in S.anc.get(b, ())
print("concluded", sorted(i for i in S.C if S.C[i]))
print("lone", ST.lone_removal(x, P, past))
print("newer", ST.newer_head_in_past(x.get("head", ()), None, P, past, x["obj"], ST.signers(x)))
print("mod at", ST.members_at(P, past, x["obj"], x["head"], "moderate"))
print("agent at", ST.members_at(P, past, x["obj"], x["head"], ST.AGENT))
Q = ST.seats_of(P)
print("full past holders moderate", Q.holders("moderate", x["obj"]), "agent", Q.holders(ST.AGENT, x["obj"]))
for r in rows:
    if r["id"] in ("cm1","cm2","x"): print(r)
Q2 = ST.Seats(S)
print("Seats(S) moderate", Q2.holders("moderate", x["obj"]))
rows2 = [r for r in rows if r["id"] != rid]
S2 = C.CK.concluded(C.CK.kept(list(rows2)), C.RULE)
print("Seats(S without y) moderate", ST.Seats(S2).holders("moderate", x["obj"]), ST.Seats(S2).roster(x["obj"]))
print("State(P)", ST.Seats(C.CK.State(list(P), {q["id"]: True for q in P})).holders("moderate", x["obj"]))
S3 = C.CK.concluded(C.CK.kept(list(P)), C.RULE)
print("concluded(P)", ST.Seats(S3).holders("moderate", x["obj"]), sorted(i for i in S3.C if S3.C[i]))
print([type(a) for a in P][:2], [q["id"] for q in P])
