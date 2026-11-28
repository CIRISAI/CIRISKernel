"""Cases where resign() added a statement by a key some predecessor seats: a voice that counts in the majority too."""
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1]); sys.path.insert(1, sys.argv[2]); import check_root as RAW
RT = RAW.RT
for r, nm, bs, rv, gs, rd, w in RAW.CASES:
    R = RT.Root(bs)
    for b in bs:
        if b.get("bare") or not b["prev"] or b.get("recovers") is not None or any(p not in R.by for p in b["prev"]): continue
        have = {k for k, _ in b["stmts"]}
        add = [min(ks) for _, ks in R.join_signers(b) if ks and not (ks & have)]
        base = set().union(*[set(R.by[p]["holders"]) for p in b["prev"]])
        voice = [k for k in add if k in base]
        if voice:
            print("resign adds a counted voice:", r, "|", nm[:100], "| bundle", b["id"], "adds", voice, "signers were", sorted(have))
