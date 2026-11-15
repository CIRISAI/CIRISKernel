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
    text = open(os.path.join(SPEC, "Door.tla"), encoding="utf-8").read()
    names = {int(r): sorted(int(x) for x in body.replace(" ", "").split(",") if x)
             for r, body in re.findall(r"r = (\d+) -> \{([^}]*)\}", text)}
    rows = int(re.search(r"Rows == 1\.\.(\d+)", text).group(1))
    malformed = [int(x) for x in re.findall(r"WF\(r\) == r # (\d+)", text)]
    assert sorted(names) == list(range(1, rows + 1)), names
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
