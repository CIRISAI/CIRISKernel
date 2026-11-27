import sys, os, random
T = sys.argv[1]; sys.path.insert(0, os.path.join(T, "models/causal_kernel")); sys.dont_write_bytecode = True
import check_election as E
ST, CK, R = E.ST, E.CK, E.R
SC = "/tmp/claude-1000/-home-emoore-CIRISKernel/9f476e19-79a3-4f60-8019-6f13a6523575/scratchpad"
def load(path):
    src = open(path).read().split("\n", 1)[1]
    g = {"E": E, "ST": ST, "CK": CK, "R": R, "ballot": E.ballot, "decline": E.decline, "elect": E.elect, "ack": E.ack,
         "admit": E.admit, "leave": E.leave, "room": E.room, "LM": E.LM, "show": lambda *a, **k: (None, None)}
    src = src.split("Q, S_ = show(")[0] if "Q, S_ = show(" in src else src
    exec(src, g); return g
def mods(rows, own=None):
    S = CK.concluded(CK.kept(list(rows)), E.RULE); Q = ST.Seats(S, own=own)
    ks = sorted({k for r in rows for k in (r.get("to") or ()) if isinstance(k, str)} | {r["signer"] for r in rows})
    base = sorted(k for k in ks if Q.stands(k, "moderate", "g"))
    rnd = random.Random(3); diff = 0
    for _ in range(40):
        t = list(rows[1:]); rnd.shuffle(t)
        S2 = CK.arrive([rows[0]] + t, E.RULE); Q2 = ST.Seats(S2, own=own)
        if sorted(k for k in ks if Q2.stands(k, "moderate", "g")) != base: diff += 1
    return base, diff
def ackd(rows, head):
    return rows + [R("akR", "ack", "R", (head,), room="g", head=(head,))]
j1 = load(SC + "/r51g/s/j1.py"); h2 = load(SC + "/r51f/s/h2.py"); f2 = load(SC + "/r51d/s/f2.py"); g3 = load(SC + "/r51e/s/g3.py"); g2 = load(SC + "/r51e/s/g2.py")
rowsets = [
  ("J1b", j1["honest"] + [j1["lm1"]] + j1["x"], "aI"),
  ("J1d", j1["honest2"] + [j1["lm1b"]] + j1["x2"], "rI"),
  ("H2b", h2["honest"] + [h2["lm1"]] + h2["xb"] + [h2["s2"], h2["kc"]], "aI"),
  ("N1 F2b", f2["rows"] + [f2["lm2"]] + f2["H"] + [f2["ed"], f2["lm1"], f2["eb"]], "aG"),
  ("N1 F2e", f2["rows"] + [f2["lm2"]] + f2["H"] + [f2["ed"], f2["lm1"], f2["eb"]] + f2["ak"], "aG"),
  ("G2", g2["rows"], "g"),
  ("G3b", g3["rows"] + [g3["lm2"]] + g3["H"] + [g3["ed"], g3["lm1"]] + g3["xb"] + g3["wb"] + [g3["eb"]], "aG"),
  ("G3c", g3["rows"] + [g3["lm2"]] + g3["H"] + [g3["ed"]] + g3["ak"] + [g3["lm1"]] + g3["xb"] + g3["wb"] + [g3["eb"]], "aG"),
  ("G3d", g3["rows"] + [g3["lm2"]] + g3["H"] + [g3["ed"], g3["lm1"]] + g3["xb"] + g3["wb"] + [g3["eb"]] + g3["ak2"], "aG"),
]
b2 = [c for c in E.CASES if c[0].startswith("F2, (3) (b2")][0]
rowsets.append(("b2", b2[1], "aF"))
print("%-8s | %-28s | %-28s | %-28s | %-28s" % ("case", "union, no ack", "union, acked", "inter, no ack", "inter, acked"))
for name, rows, head in rowsets:
    out = []
    for mode in ("union", "inter"):
        ST.CLOSE_BASE = mode; ST._EMEMO.clear()
        out.append(mods(rows)); out.append(mods(ackd(rows, head), "R"))
    print("%-8s | %-28s | %-28s | %-28s | %-28s" % ((name,) + tuple("%s (%d/40 orders differ)" % (o[0], o[1]) for o in out)))
