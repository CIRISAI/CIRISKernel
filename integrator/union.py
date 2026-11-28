# union both sides of every conflict hunk in the files given (ours first), or `theirs`/`ours` with --take
import re, sys
take = None
args = sys.argv[1:]
if args and args[0].startswith("--take="): take = args[0][7:]; args = args[1:]
for p in args:
    s = open(p).read()
    def f(m):
        o, t = m.group(1), m.group(2)
        if take == "ours": return o
        if take == "theirs": return t
        return o + t
    s, n = re.subn(r"<<<<<<< [^\n]*\n(.*?)=======\n(.*?)>>>>>>> [^\n]*\n", f, s, flags=re.S)
    open(p, "w").write(s); print(p, n)
