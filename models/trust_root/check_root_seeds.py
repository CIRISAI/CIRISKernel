"""check_root under several PYTHONHASHSEED values: nothing in the trust root's model may depend on iteration order.
Each seed runs check_root in full (every case, every plant) and builds root.json and root_reader.json; every seed must
give the same output and the same fixtures, byte for byte (a fixture built from a hash-order-dependent answer is a
bug)."""
import hashlib, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = ("0", "1", "2", "3", "17", "4242")
PROBE = ("import sys, json, hashlib; sys.path.insert(0, %r); import check_root as CR; "
         "print(hashlib.sha256(json.dumps([CR.fixture(False), CR.fixture(True), CR.reader_vectors()], sort_keys=True,"
         " default=repr).encode()).hexdigest())" % HERE)


def one(seed):
    env = dict(os.environ, PYTHONHASHSEED=seed)
    run = subprocess.run([sys.executable, "-I", os.path.join(HERE, "check_root.py")], env=env, capture_output=True,
                         text=True)
    fx = subprocess.run([sys.executable, "-I", "-c", PROBE], env=env, capture_output=True, text=True)
    return run.stdout + run.stderr, fx.stdout.strip() + fx.stderr


def main():
    got = {s: one(s) for s in SEEDS}
    base = got[SEEDS[0]]
    bad = [s for s in SEEDS if got[s] != base]
    for s in bad:
        which = [n for n, a, b in (("check_root output", got[s][0], base[0]), ("fixtures", got[s][1], base[1])) if a != b]
        print("PYTHONHASHSEED=%s differs from %s: %s" % (s, SEEDS[0], ", ".join(which)))
    ok = "ok" if not bad and "RESULT: ok" in base[0] else "%d seeds differ" % len(bad)
    print("RESULT: %s: check_root and its fixtures under %d hash seeds (%s)" % (ok, len(SEEDS), hashlib.sha256(
        (base[0] + base[1]).encode()).hexdigest()[:12]))
    return 0 if ok == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
