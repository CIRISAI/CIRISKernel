"""Apply each named plant of tools/kernel_crate_plants.sh in place, run cargo test --release, restore. One at a time."""
import os, shlex, subprocess, sys
root = "/home/emoore/CIRISKernel/.claude/worktrees/agent-ad781c03a48920203"
crate = root + "/crates/ciris-kernel"
names = sys.argv[1:]
lines = open(root + "/tools/kernel_crate_plants.sh").read().split("\n")
plants = {}
for l in lines:
    if l.startswith("plant "):
        try: parts = shlex.split(l)
        except ValueError: continue
        plants[parts[1]] = parts[2:5]
bad = 0
for n in names:
    f, old, new = plants[n]
    path = os.path.join(crate, f)
    src = open(path).read()
    assert old in src, n
    open(path, "w").write(src.replace(old, new, 1))
    try:
        r = subprocess.run(["cargo", "test", "--offline", "--release", "-q"], cwd=crate, capture_output=True, text=True)
    finally:
        open(path, "w").write(src)
    tail = [x for x in (r.stdout + r.stderr).split("\n") if "FAILED" in x or "error" in x][:2]
    print("%s  %s  %s" % ("caught     " if r.returncode else "NOT CAUGHT ", n, tail), flush=True)
    bad += not r.returncode
sys.exit(1 if bad else 0)
