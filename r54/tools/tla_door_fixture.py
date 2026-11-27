#!/usr/bin/env python3
"""
tla_door_fixture.py: dump every reachable state of models/tla/Door.tla with TLC and write them, with the
spec's own rows, as crates/ciris-kernel/tests/fixtures/tla_door.json, which tests/tla_door.rs replays through
the crate's door (`layers::kept`, `layers::arrive`).

    python3 -I tools/tla_door_fixture.py --jar PATH          write the fixture
    python3 -I tools/tla_door_fixture.py --jar PATH --check  exit 1 if the committed fixture differs
"""
import json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(ROOT, "models", "tla")
OUT = os.path.join(ROOT, "crates", "ciris-kernel", "tests", "fixtures", "tla_door.json")


def spec_rows():
    """Door.tla's rows at the N of Door.cfg: row r names r - 1 and r // 2 (below r), every fifth row also N + 1,
    which is never offered, and every seventh row is malformed. Checked against the spec's text."""
    text = open(os.path.join(SPEC, "Door.tla"), encoding="utf-8").read()
    assert "({r - 1, r \\div 2} \\cap 1..(r - 1)) \\cup (IF r % 5 = 0 THEN {N + 1} ELSE {})" in text
    assert "WF(r) == r % 7 # 0" in text
    n = int(re.search(r"N = (\d+)", open(os.path.join(SPEC, "Door.cfg"), encoding="utf-8").read()).group(1))
    names = {r: sorted({x for x in (r - 1, r // 2) if 1 <= x < r} | ({n + 1} if r % 5 == 0 else set()))
             for r in range(1, n + 1)}
    malformed = [r for r in range(1, n + 1) if r % 7 == 0]
    return names, malformed


def states(jar):
    with tempfile.TemporaryDirectory() as d:
        dump = os.path.join(d, "states")
        subprocess.run(["java", "-cp", jar, "tlc2.TLC", "-workers", "1", "-metadir", os.path.join(d, "meta"),
                        "-dump", dump, "-config", "Door.cfg", "Door.tla"], cwd=SPEC, check=True,
                       stdout=subprocess.DEVNULL)
        text = open(dump + ".dump", encoding="utf-8").read()
    out = []
    for block in re.split(r"State \d+:", text)[1:]:
        st = {}
        for var in ("offered", "held", "waiting"):
            m = re.search(var + r" = \{([^}]*)\}", block)
            st[var] = sorted(int(x) for x in m.group(1).replace(" ", "").split(",") if x)
        out.append(st)
    uniq = {json.dumps(s, sort_keys=True): s for s in out}      # one entry per distinct state
    return sorted(uniq.values(), key=lambda s: (s["offered"], s["held"]))


def main():
    jar = sys.argv[sys.argv.index("--jar") + 1]
    names, malformed = spec_rows()
    text = json.dumps({"names": {str(k): v for k, v in names.items()}, "malformed": malformed, "states": states(jar)},
                      sort_keys=True, separators=(",", ":")) + "\n"
    if "--check" in sys.argv:
        same = os.path.exists(OUT) and open(OUT, encoding="utf-8").read() == text
        print("tla_door fixture: %s" % ("current" if same else "OUT OF DATE"))
        return 0 if same else 1
    open(OUT, "w", encoding="utf-8", newline="\n").write(text)
    print("tla_door fixture: %d states" % len(json.loads(text)["states"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
