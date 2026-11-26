"""Round 3: the silent colluder, S against itself, beside L'; void sets and conclusions under each form, 60 orders."""
import sys, os, random
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import seat as ST, check_count_heads as CH
CK = ST.CK; OBJ = "g"; admit, remove = CH.admit, CH.remove
import importlib.util as _u
_sp = _u.spec_from_file_location("lprime", os.path.join(os.path.dirname(os.path.abspath(__file__)), "lprime.py"))
LP = _u.module_from_spec(_sp); _sp.loader.exec_module(LP)
G = CH.G
# the silent colluder: A signs the honest admissions with C (and the newcomers); B signs nothing after g
def silent(n):
    rows, mem, prev = [G], ["A", "C"], "g"
    for k in "DEFG":
        rows.append(admit("a" + k, k, tuple(mem), (prev,))); mem.append(k); prev = "a" + k
    sg, fp = ["A", "B"], "g"
    for i in range(1, n + 1):
        rows.append(admit("p%d" % i, "X%d" % i, tuple(sg), (fp,))); sg.append("X%d" % i); fp = "p%d" % i
    return rows, fp
W = []
for n in (1, 2, 8):
    rows, fp = silent(n)
    W.append(("silent B, chain n=%d: C..G remove A at (aG, %s)" % (n, fp), rows + [remove("xr", "A", tuple("CDEFG"), ("aG", fp))], "xr"))
    W.append(("silent B, chain n=%d: the packers A,B,X.. remove C at (aG, %s)" % (n, fp),
              rows + [remove("xr", "C", ("A", "B") + tuple("X%d" % i for i in range(1, n + 1)), ("aG", fp))], "xr"))
# S against itself: A and B sign q1 (admit D) and q2 (admit X) at g, then q1b (admit E at q1) and q2b (admit Y at q2)
SA = [G, admit("q1", "D", ("A", "B"), ("g",)), admit("q2", "X", ("A", "B"), ("g",)),
      admit("q1b", "E", ("A", "B", "D"), ("q1",)), admit("q2b", "Y", ("A", "B", "X"), ("q2",))]
W.append(("S against itself: A,B,C admit Z at (q1b, q2b)", SA + [admit("rz", "Z", ("A", "B", "C"), ("q1b", "q2b"))], "rz"))
W.append(("S against itself, the honest side extended by C: C,D,E admit Z at (q1b, q2b)",
          SA + [admit("q1c", "F", ("A", "B", "C", "D", "E"), ("q1b",)), admit("rz", "Z", ("C", "D", "E", "F"), ("q1c", "q2b"))], "rz"))
for nm, rows in LP.W.items():
    W.append((nm, rows + [LP.rem("xa", "A", ("C", "D", "E", "F", "G"), ("xd", "aG"))], "xa"))
def ans(S, a):
    P = [q for q in S.Cs if q["id"] in S.anc.get(a, ())]
    return bool(S.C.get(a)), tuple(sorted(ST.signers_void(S.by[a], P))) if P and "fold" in ST.PROTO else ()
for name, rows, a in W:
    S = CK.concluded(CK.kept(list(rows)), CH.RULE)
    base = ans(S, a)
    rnd = random.Random(7); diff = 0
    for _ in range(60):
        t = list(rows[1:]); rnd.shuffle(t)
        if ans(CK.arrive([rows[0]] + t, CH.RULE), a) != base: diff += 1
    print("%-72s %s void=%s members=%s orders differing %d/60" % (name[:72], "T" if base[0] else "F", list(base[1]),
          "".join(sorted(ST.Seats(S).holders("member", OBJ))), diff))
