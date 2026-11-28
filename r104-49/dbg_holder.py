import sys
sys.argv = [sys.argv[0], sys.argv[1]]
src = open("attack_holder.py").read().split("for label, extra in")[0]
exec(src)
for extra_name, extra in (("honest only (no stale rows), lm0 still A's only lay-down", [LM0] + honest(())),):
    for reader in (None, "R"):
        rows = EL.N1R + extra + ([ACKR] if reader else [])
        ST.KEY_VIEW.append(None)
        S = CK.concluded(CK.kept(list(rows)), RULE)
        print(extra_name, reader, "ask", ask(rows, reader))
        if reader:
            print("   reader_ends", sorted(ST.reader_ends(S, reader)), "reader_void", sorted(ST.reader_void(S, reader)))
        ST.KEY_VIEW.pop()
