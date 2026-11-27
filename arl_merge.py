p = "/home/emoore/CIRISKernel/.claude/worktrees/agent-ad781c03a48920203/crates/ciris-kernel/CHANGELOG.md"
L = open(p).read().split("\n")
out = []
for l in L:
    if l.startswith("<<<<<<< ") or l.startswith(">>>>>>> "): continue
    if l == "=======": out.append(""); continue
    out.append(l)
s = "\n".join(out)
while "\n\n\n" in s: s = s.replace("\n\n\n", "\n\n")
open(p, "w").write(s)
