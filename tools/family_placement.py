#!/usr/bin/env python3
"""
family_placement.py: derive the placement table the kernel reads from the Constitution's family model
(manifests/family_model.json, CC 3.1), and pin it.

Writes, from the parent's file:
    data/family_placement.json                 the derived table with its source: path, branch, commit, sha256
    crates/ciris-kernel/src/audience_table.rs  the same table as a Rust constant (`audience::FAMILIES`)

For each family the placement cell gives one of:
    allowed     the placements a row of the family may take: the default (rule `default`: any of
                self_collective, targeted_family, targeted_room, commons, chosen by the emitter for each row,
                CC 3.4.5.1), or the placements the CC table pins (source cc-table, a word or a set of words)
    undecided   the cell is not table data (source code-v61, prose or gap, or no placement word): the kernel
                answers Undecided naming the family, never a default

A re-pin is one command:

    python3 -I tools/family_placement.py [path/to/family_model.json] [--provisional | --final]
        [--branch B --commit C]       the source's branch and commit, where the file is not read from a checkout
                                      at that commit (`git show C:manifests/family_model.json > file`)
Two patterns that tie on some name (equally many literal segments) are refused: the script writes nothing.

    python3 -I tools/family_placement.py --check [path]   exit 1 if the Rust constant is not the vendored table's,
                                                          or (with a path) the vendored table is not that file's
"""
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "family_placement.json")
RUST = os.path.join(ROOT, "crates", "ciris-kernel", "src", "audience_table.rs")
PLACEMENTS = ("self_collective", "targeted_family", "targeted_room", "commons", "addressed")
RUST_NAME = {"self_collective": "SelfCollective", "targeted_family": "TargetedFamily",
             "targeted_room": "TargetedRoom", "commons": "Commons", "addressed": "Addressed"}


def opt(argv, name):
    """The value after `--name`, where given."""
    return argv[argv.index(name) + 1] if name in argv else None


def source_path(argv):
    vals = {opt(argv, "--branch"), opt(argv, "--commit")}
    for a in argv[1:]:
        if not a.startswith("--") and a not in vals:
            return os.path.abspath(a)
    for p in (os.path.join(ROOT, "..", "CIRISConstitution", "manifests", "family_model.json"),
              os.path.join(os.path.expanduser("~"), "CIRISConstitution", "manifests", "family_model.json")):
        if os.path.exists(p):
            return os.path.abspath(p)
    sys.exit("family_placement: give the path of the Constitution's manifests/family_model.json")


def git(repo, *args):
    try:
        return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _placeholder(s):
    return s.startswith("{") and s.endswith("}")


def _match(pattern, name):
    """The number of literal segments by which `pattern` matches `name`, or None (audience.py's rule)."""
    p, n = pattern.split(":"), name.split(":")
    if p[-1] == "*":
        if len(n) < len(p):
            return None
        p, n = p[:-1], n[:len(p) - 1]
    elif len(p) != len(n):
        return None
    lit = 0
    for a, b in zip(p, n):
        if _placeholder(a):
            continue
        if a != b:
            return None
        lit += 1
    return lit


def ties(patterns):
    """Every name two patterns both match on which the most literal matching patterns tie: (name, patterns). For
    each pair, the names that unify the two segment by segment, at every length up to the longer plus two."""
    out = []
    pats = sorted(patterns)
    for i, p in enumerate(pats):
        for q in pats[i + 1:]:
            P, Q = p.split(":"), q.split(":")
            for length in range(1, max(len(P), len(Q)) + 3):
                def seg(X, k):
                    if X[-1] == "*" and k >= len(X) - 1:
                        return "*"
                    return X[k] if k < len(X) else None
                segs = []
                for k in range(length):
                    a, b = seg(P, k), seg(Q, k)
                    if a is None or b is None:
                        segs = None
                        break
                    lit = {x for x in (a, b) if x != "*" and not _placeholder(x)}
                    if len(lit) > 1:
                        segs = None
                        break
                    segs.append(lit.pop() if lit else "zz")
                if segs is None:
                    continue
                name = ":".join(segs)
                if _match(p, name) is None or _match(q, name) is None:
                    continue
                hits = [(_match(f, name), f) for f in pats if _match(f, name) is not None]
                best = max(k for k, _ in hits)
                top = [f for k, f in hits if k == best]
                if len(top) > 1:
                    out.append((name, top))
    return out


def seat_family(row):
    """A family whose rows seat or end a seat conferred by a body (a room's roster, or a person's own key roster):
    its confers cell is a seat or an ending binding the body and the holder, or a selector that seats by the body's
    count. Only a seat offer or unseat of such a family seats keys within its audience (audience.seats_of)."""
    c = row.get("confers")
    v = c.get("value") if isinstance(c, dict) else c
    if isinstance(v, dict):
        rel = str(v.get("relation", "")).split("|")
        return ("seat" in rel or "ending" in rel) and "body" in str(v.get("binds", ""))
    return isinstance(v, str) and "seat (the body's count" in v


def placement_of(row):
    """(allowed placements, None) or (None, why it is undecided)."""
    p = row["placement"]
    v, src = p.get("value"), p.get("source")
    if p.get("rule") == "default":
        return list(PLACEMENTS[:4]), None
    words = v if isinstance(v, list) else [v] if isinstance(v, str) else []
    if src == "cc-table" and words and all(w in PLACEMENTS for w in words):
        return [w for w in PLACEMENTS if w in words], None
    return None, "%s: %s" % (src, v if v is not None else "no placement")


def derive(path):
    raw = open(path, "rb").read()
    model = json.loads(raw)
    repo = os.path.dirname(os.path.dirname(path))
    fams = []
    for row in model["rows"]:
        allowed, why = placement_of(row)
        fams.append({"family": row["family"], "allowed": allowed, "undecided": why, "seat": seat_family(row)})
    fams.sort(key=lambda f: f["family"])
    tied = ties([f["family"] for f in fams])
    if tied:
        sys.exit("family_placement: family patterns tie, so a name would decide nothing: %s" % tied[:5])
    meta = model["_meta"]["placement"]
    return {
        "_source": {"repository": "CIRISConstitution", "path": "manifests/family_model.json",
                    "branch": opt(sys.argv, "--branch") or git(repo, "rev-parse", "--abbrev-ref", "HEAD"),
                    "commit": opt(sys.argv, "--commit") or git(repo, "rev-parse", "HEAD"),
                    "sha256": hashlib.sha256(raw).hexdigest(), "families": len(fams),
                    "on_the_default": sum(f["allowed"] == list(PLACEMENTS[:4]) and f["undecided"] is None
                                          and _is_default(model, f["family"]) for f in fams),
                    "pinned_by_the_table": sum(f["allowed"] is not None and not _is_default(model, f["family"])
                                               for f in fams),
                    "undecided": sum(f["undecided"] is not None for f in fams)},
        "placements": list(PLACEMENTS),
        "default": meta["default"],
        "scopes": meta["scopes"],
        "reach": meta["reach"],
        "copy": meta["copy"],
        "families": fams,
    }


def _is_default(model, fam):
    return any(r["family"] == fam and r["placement"].get("rule") == "default" for r in model["rows"])


def rust(table):
    s = table["_source"]
    out = ["// @generated by tools/family_placement.py from the Constitution's manifests/family_model.json",
           "// (branch %s, commit %s, sha256 %s%s). Do not edit: re-pin with that script."
           % (s["branch"], s["commit"], s["sha256"], ", provisional" if s.get("provisional") else ""),
           "",
           "use super::{FamilyPlacement, Placement};",
           "",
           "/// The family model's sha256, the pin of [`FAMILIES`].",
           "pub const FAMILY_MODEL_SHA256: &str = \"%s\";" % s["sha256"],
           "",
           "/// The cohort scope a row states, with the placement it is (the table's `scopes`, CC 5.2), and `addressed`.",
           "pub const SCOPES: &[(&str, Placement)] = &["]
    for sc in table["scopes"]:
        for c in sc["cohort_scope"]:
            if not any(l.startswith("    (%s," % json.dumps(c)) for l in out):
                out.append("    (%s, Placement::%s)," % (json.dumps(c), RUST_NAME[sc["placement"]]))
    out += ["    (\"addressed\", Placement::Addressed),", "];", "",
           "/// Every family of the family model with its placement cell: the placements its rows may take, or undecided",
           "/// (the cell is not table data). Sorted by family pattern.",
           "pub const FAMILIES: &[(&str, FamilyPlacement)] = &["]
    for f in table["families"]:
        if f["allowed"] is None:
            out.append("    (%s, FamilyPlacement::Undecided)," % json.dumps(f["family"]))
        else:
            ps = ", ".join("Placement::" + RUST_NAME[p] for p in f["allowed"])
            out.append("    (%s, FamilyPlacement::Allowed(&[%s]))," % (json.dumps(f["family"]), ps))
    out.append("];")
    out += ["", "/// The families whose seat offers and unseats seat or remove keys over a body (a room's roster, or a person's",
            "/// own key roster): the only ones whose `to` is within a row's audience ([`super::seats_of`]).",
            "pub const SEAT_FAMILIES: &[&str] = &["]
    out += ["    %s," % json.dumps(f["family"]) for f in table["families"] if f.get("seat")]
    out.append("];")
    return "\n".join(out) + "\n"


def main():
    if "--check" in sys.argv:
        # the Rust constant is the vendored table's; with a source path given, the table is that file's too
        table = json.load(open(DATA, encoding="utf-8"))
        bad = [] if open(RUST).read() == rust(table) else [RUST]
        if any(not a.startswith("--") and a not in {opt(sys.argv, "--branch"), opt(sys.argv, "--commit")}
               for a in sys.argv[1:]):
            fresh = derive(source_path(sys.argv))
            fresh["_source"]["provisional"] = table["_source"].get("provisional", False)
            if json.dumps(fresh, indent=1, ensure_ascii=False) + "\n" != open(DATA, encoding="utf-8").read():
                bad.append(DATA)
        for p in bad:
            print("family_placement: out of date: %s" % os.path.relpath(p, ROOT))
        print("family_placement: %s" % ("ok" if not bad else "%d out of date" % len(bad)))
        return 1 if bad else 0
    path = source_path(sys.argv)
    table = derive(path)
    table["_source"]["provisional"] = "--provisional" in sys.argv or (
        os.path.exists(DATA) and json.load(open(DATA)).get("_source", {}).get("provisional", False)
        and "--final" not in sys.argv)
    text = json.dumps(table, indent=1, ensure_ascii=False) + "\n"
    rs = rust(table)
    open(DATA, "w", newline="\n").write(text)
    open(RUST, "w", newline="\n").write(rs)
    s = table["_source"]
    print("family_placement: %d families (%d on the default, %d pinned by the table, %d undecided) from %s at %s, "
          "sha256 %s" % (s["families"], s["on_the_default"], s["pinned_by_the_table"], s["undecided"], s["branch"],
                         s["commit"], s["sha256"][:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
