"""Which bundles, after resign(), still lack a voice join_signers requires; and which cases depend on resign."""
import sys
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import check_root as C
RT = C.RT
def unsigned(bs):
    R = RT.Root(bs); out = []
    for b in bs:
        if not b["prev"] or b.get("recovers") is not None or any(p not in R.by for p in b["prev"]): continue
        have = {k for k, _ in b["stmts"]}
        miss = [h for h, ks in R.join_signers(b) if not (ks & have)]
        if miss: out.append((b["id"], miss, bool(b.get("bare"))))
    return out
seen = set()
for r, n, bs, rv, gs, rd, w in C.CASES:
    u = unsigned(bs)
    if u: print("UNSIGNED after resign:", r, "|", n[:90], u)
for n, rows, bs, gs, rd, c, why, f4 in C.RECOVERY:
    u = unsigned(bs) if bs else []
    if u: print("UNSIGNED (recovery):", n[:90], u)
for n, bs, gs, rd, gid, w in C.SUB_CASES:
    u = unsigned(bs)
    if u: print("UNSIGNED (sub):", n[:90], u)
# which cases need resign: answer without it differs from want
import importlib
raw = importlib.reload(C)   # CASES rebuilt resigned again; get raw by undoing: re-read via un-resigned list is not kept
