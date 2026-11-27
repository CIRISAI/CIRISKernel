"""A/B of two builds of crates/ciris-kernel/examples/persist_paths.rs: each bench at each size runs alone in a
process of its own (`=name`), the two binaries alternating, for a number of rounds; prints, per bench and
size, the median over rounds of each binary's median, the ratio (before / after) and the allocations per
call. The host's load average is printed before and after. A bench only one binary has is printed with the
other side empty.

    python3 -I tools/kernel_bench_ab.py BEFORE AFTER [--rounds 3] [--sizes 3,16,128,1024] [--only substr]
        [--names a,b,c] [--timeout 120] > table.tsv

`--names` runs those benches only (exact names); a run that exceeds the timeout prints empty.
"""
import os
import statistics
import subprocess
import sys


def names(binary):
    out = subprocess.run([binary, "--list"], capture_output=True, text=True, stdin=subprocess.DEVNULL).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


def run(binary, name, size, timeout):
    try:
        out = subprocess.run(
            [binary, "=" + name, "--sizes", str(size)],
            capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL,
        ).stdout
    except subprocess.TimeoutExpired:
        return None
    for line in out.splitlines()[1:]:
        f = line.split("\t")
        if f[0] == name and f[2] != "skipped":
            return float(f[2]), f[5]
    return None


def main():
    a = sys.argv[1:]
    before, after = a[0], a[1]
    opt = {"--rounds": "3", "--sizes": "3,16,128,1024", "--only": "", "--timeout": "120", "--names": ""}
    for i in range(2, len(a), 2):
        opt[a[i]] = a[i + 1]
    rounds, timeout = int(opt["--rounds"]), float(opt["--timeout"])
    sizes = [int(x) for x in opt["--sizes"].split(",")]
    nb, na = names(before), names(after)
    every = [n for n in na if n not in nb] + nb
    every = sorted(set(every), key=lambda n: (na + nb).index(n))
    every = [n for n in every if opt["--only"] in n]
    if opt["--names"]:
        want = opt["--names"].split(",")
        every = [n for n in every if n in want]
    print("# load before:", os.getloadavg(), file=sys.stderr)
    print("bench\tsize\tbefore_ns\tafter_ns\tbefore/after\tallocs_before\tallocs_after")
    for size in sizes:
        for name in every:
            got = {before: [], after: []}
            allocs = {before: "", after: ""}
            for _ in range(rounds):
                for b, have in ((before, nb), (after, na)):
                    if name not in have:
                        continue
                    r = run(b, name, size, timeout)
                    if r:
                        got[b].append(r[0])
                        allocs[b] = r[1]
            mb = statistics.median(got[before]) if got[before] else None
            ma = statistics.median(got[after]) if got[after] else None
            ratio = f"{mb / ma:.2f}" if mb and ma else ""
            fmt = lambda x: f"{x:.0f}" if x is not None else ""
            print(f"{name}\t{size}\t{fmt(mb)}\t{fmt(ma)}\t{ratio}\t{allocs[before]}\t{allocs[after]}", flush=True)
    print("# load after:", os.getloadavg(), file=sys.stderr)


main()
