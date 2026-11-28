import sys
sys.argv = [sys.argv[0], sys.argv[1]]
exec(open("attack_line.py").read().split("WORLDS = [")[0])
rows = EL.N1R + [LM0] + STALE + honest("lm0") + acks("ed")
ST.KEY_VIEW.append(None)
S = CK.concluded(CK.kept(list(rows)), RULE)
past = lambda a, b: a in S.anc[b]
V, RE = ST.reader_void(S, "R"), ST.reader_ends(S, "R")
print("reader_void", sorted(V), "reader_ends", sorted(RE))
ST._RVOID.append(frozenset(V)); ST._RENDS.append(frozenset(RE))
tk = ST.taken(S.Cs) if hasattr(ST, "taken") else None
print("taken has opg:", tk is not None and any(q["id"] == "opg" for q in tk))
held = tk if tk is not None else S.Cs
print("op in force:", ST.opening_in_force(S.by["op"], held, past), "openings_for:", [o["id"] for o in ST.openings_for(S.by["op"], held, past)])
