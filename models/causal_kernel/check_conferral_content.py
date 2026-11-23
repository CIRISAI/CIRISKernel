#!/usr/bin/env python3
"""
check_conferral_content.py: room content after a member's seat ends, where the end names the rows held good
(conferral_content.py; the Constitution's proposal of 2026-11-22, second form). Checked three ways.

    case table   every case of conferral_content.CASES: the reference gives the hand-written counted, in_force
                 and rule for every content row, in every arrival order the door allows (up to 200 per case)
    fixture      crates/ciris-kernel/tests/fixtures/conferral_content.json: the reference, run on each case's
                 rows, gives every answer the fixture states, and each listed arrival order ends at it
    every world  every history to a bound, built row by row, every row naming only earlier rows: two roster
                 heads; up to three content rows of the member, each naming up to two earlier ones as `prev`
                 and optionally an earlier end, or retracting an earlier one; up to two ends, each a counted removal or the member's own, at
                 either head, optionally stale or naming the earlier end; one row adding tips, counted or the
                 member's own; four rows in all besides the heads (`--rows N`). An end's or an adding row's
                 tips may be rows not held or not signed yet. By default one key signs and the tip sets are
                 none, each single row and one pair; `--wide` has two keys and every pair. Every extension of a
                 held set by rows of the member alone, and by one counted row, is compared:

        cannot_add      once an end counts, no end and no tips row the member signs puts a row into the room's
                        content, and a content row the member signs enters only where a tip named before it
                        holds it good (a tip may name a row not yet held: the end never waits on one)
        word_stands     a row the count's tips hold good stays, whatever the member signs, unless the member
                        retracts it (W.retracted) or the member's own backdated end puts it at a later head
                        than an end of its seat (E3.later_head): the reader's line bounds that, and the run
                        reports how often it happens
        retract_removes a retraction never puts a row into the room's content
        tips_grow       a counted row adding tips never takes a row out, and changes no count
        further_end     a further counted end takes a row out only by E3.later_head
        counted_alike   whether a row counts never depends on whose tips are read
        set_function    the answer does not depend on the order the rows are listed in

    Plants, each of which must break cannot_add: `union` (the proposal's third point read literally: the
    member's own ends add), `count_first_self_union` (the member's own ends add where no counted end counts),
    and a `tips` row signed by the member that is read.

    The node-local fallback (a row held before the end stays shown to that reader) is not part of the proposal.
    The run reports, over the case table, in how many cases two arrival orders of one set of rows show
    different rooms.

    python3 -I check_conferral_content.py [--rows N] [--workers N]      exit 1 on any difference
    (three worker processes and the calling one, as the other checks here)
"""
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import conferral_content as CC  # noqa: E402

FIXTURE = os.path.join(ROOT, "crates", "ciris-kernel", "tests", "fixtures", "conferral_content.json")
HEADS = [CC.head("H0"), CC.head("H1", "H0")]
MAX_ROWS, MAX_ACTS, MAX_ENDS, MAX_TIPS = 4, 3, 2, 1
WIDE = False     # --wide: two keys and every pair of tips; the default is one key and the tip sets below


def next_rows(rows):
    """Every row that may be signed next: it names only rows already signed."""
    acts = [r["id"] for r in rows if r["kind"] == "act"]
    ends = [r["id"] for r in rows if r["kind"] == "end"]
    n_tips = sum(r["kind"] == "tips" for r in rows)
    if len(acts) < MAX_ACTS:
        i = "a%d" % (len(acts) + 1)
        for key in (CC.KEYS if WIDE else CC.KEYS[:1]):
            for h in ("H0", "H1"):
                for prev in [()] + [c for n in (1, 2) for c in itertools.combinations(acts, n)]:
                    for cite in [None] + ends:
                        yield CC.act(i, h, prev, [cite] if cite else [], signer=key)
                for target in acts:                   # a retraction of an earlier row, its own or not
                    yield CC.act(i, h, (), signer=key, target=target, compose="retract")
    # a tip may be a row not signed yet (a1 to a3 by id): the end does not wait on its tips
    every = ["a%d" % n for n in range(1, MAX_ACTS + 1)]
    tip_sets = [()] + [c for k in (1, 2) for c in itertools.combinations(every, k)]
    if not WIDE:
        tip_sets = [(), ("a1",), ("a2",), ("a3",), ("a1", "a2")]
    if len(ends) < MAX_ENDS:
        i = "e%d" % (len(ends) + 1)
        for signer in (CC.COUNT, "B"):
            for h in ("H0", "H1"):
                extras = [()] + ([("H1",)] if h == "H0" else []) + [(e,) for e in ends]
                for tp in tip_sets:
                    for extra in extras:
                        yield CC.end(i, h, tp, signer, extra)
    if n_tips < MAX_TIPS and ends:
        for signer in (CC.COUNT, "B"):
            for e in ends:
                for tp in tip_sets[1:]:
                    yield CC.tips("t1", e, tp, signer)      # at H0; no rule reads an adding row's head


def by_member(r):
    return r["signer"] in CC.KEYS


class Run:
    def __init__(self, merge="count_first", self_tips=False, limit=None):
        self.merge, self.self_tips, self.limit = merge, self_tips, limit
        self.worlds = self.pairs = self.e3 = 0
        self.bad = {}

    def ans(self, rows):
        return CC.answers(rows, self.merge, self.self_tips)

    def fail(self, prop, rows, note):
        self.bad.setdefault(prop, (note, [(r["id"], r["kind"], r["signer"], r.get("head"), r.get("prev"),
                                          r.get("trusted_through"), r["names"]) for r in rows]))

    def go(self, rows, path, descend=True):
        """`path[j]`: for the prefix of `rows` of length len(HEADS) + j, its answers, whether an end counts in it,
        and whether a counted end does."""
        if self.limit is not None and self.bad:
            return
        a = self.ans(rows)
        void = CC.counting_ends(rows)
        counts = [r for r in rows if r["kind"] == "end" and void[r["id"]] is None]
        info = (a, bool(counts), any(e["signer"] == CC.COUNT for e in counts))
        self.worlds += 1
        added = rows[len(HEADS):]
        if added:
            last = added[-1]
            # extensions by the member alone: every prefix from which only the member signed
            k = len(rows)
            while k > len(HEADS) and by_member(rows[k - 1]):
                k -= 1
                pa, p_end, p_count_end = path[k - len(HEADS)]
                if p_end:
                    self.pairs += 1
                    # the same content rows, without the ends and tips rows the member signed since
                    base = self.ans(rows[:k] + [r for r in rows[k:] if r["kind"] == "act"])
                    for x, v in a.items():
                        if v["in_force"] and not base[x]["in_force"]:
                            self.fail("cannot_add", rows, "%s is in the content by an end or a tips row the member "
                                                          "signed after an end counted" % x)
                        if v["in_force"] and x not in pa and not any(
                                x in CC.held_good(rows, r) for r in rows[:k] if r["kind"] in ("end", "tips")):
                            self.fail("cannot_add", rows, "%s is in the content and no tip named before it holds "
                                                          "it good" % x)
                if p_count_end:
                    for x, v in pa.items():
                        if v["in_force"] and not a[x]["in_force"]:
                            if a[x]["rule"] == "E3.later_head":
                                self.e3 += 1
                            elif a[x]["rule"] != "W.retracted":
                                self.fail("word_stands", rows, "%s leaves the content by %s" % (x, a[x]["rule"]))
            pa, p_end, p_count_end = path[len(rows) - 1 - len(HEADS)]
            if last.get("compose") == "retract":
                self.pairs += 1
                for x, v in pa.items():
                    if a[x]["in_force"] and not v["in_force"]:
                        self.fail("retract_removes", rows, "%s enters the content when a retraction is signed" % x)
            if last["signer"] == CC.COUNT and last["kind"] == "tips":
                self.pairs += 1
                for x, v in pa.items():
                    if (v["in_force"] and not a[x]["in_force"]) or v["counted"] != a[x]["counted"]:
                        self.fail("tips_grow", rows, "%s changes when a counted row adds tips" % x)
            if last["signer"] == CC.COUNT and last["kind"] == "end" and p_count_end:
                self.pairs += 1
                for x, v in pa.items():
                    if v["in_force"] and not a[x]["in_force"] and a[x]["rule"] != "E3.later_head":
                        self.fail("further_end", rows, "%s leaves the content by %s" % (x, a[x]["rule"]))
            if self.merge == "count_first" and not self.self_tips:
                for m in CC.MERGES[1:]:
                    o = CC.answers(rows, m)
                    if any(o[x]["counted"] != a[x]["counted"] for x in a):
                        self.fail("counted_alike", rows, "a count differs under %s" % m)
                if CC.answers(rows[::-1], self.merge) != a:
                    self.fail("set_function", rows, "the answer depends on the order of the list")
        if descend and len(added) < MAX_ROWS:
            for r in next_rows(rows):
                self.go(rows + [r], path + [info])
        return info


def _subtree(job):
    """One worker's share: the histories that begin with the two rows of `job`."""
    kw, rows_max, wide, r1, r2 = job
    global MAX_ROWS, WIDE
    MAX_ROWS, WIDE = rows_max, wide
    run = Run(**kw)
    path = [run.go(list(HEADS), [], descend=False)]
    path.append(run.go(HEADS + [r1], path, descend=False))
    run.worlds, run.pairs, run.e3, run.bad = 0, 0, 0, {}    # the two prefixes are the caller's to count
    run.go(HEADS + [r1, r2], path)
    return run.worlds, run.pairs, run.e3, run.bad


def explore(workers=3, **kw):
    """Every history to the bound, the subtrees below the first two rows shared among `workers` processes."""
    import multiprocessing
    top = Run(**kw)
    path = [top.go(list(HEADS), [], descend=False)]
    jobs = []
    for r1 in next_rows(list(HEADS)):
        top.go(HEADS + [r1], path, descend=False)
        if MAX_ROWS >= 2:
            jobs += [(kw, MAX_ROWS, WIDE, r1, r2) for r2 in next_rows(HEADS + [r1])]
    with multiprocessing.Pool(workers) as pool:
        for w, p, e, bad in pool.imap_unordered(_subtree, jobs, chunksize=8):
            top.worlds += w; top.pairs += p; top.e3 += e
            for k, v in bad.items():
                top.bad.setdefault(k, v)
    return top


def first_held():
    """Over the case table: the cases where two arrival orders of one set of rows show different rooms under
    the node-local fallback, and the cases where it shows a row the proposal keeps out."""
    differ, shows_out = [], []
    for c in CC.CASES:
        name, _, rows, params = c[:4]
        seen = set()
        for o in CC.orders(rows)[:200]:
            s = CC.shown_first_held(rows, o, **params)
            seen.add(tuple(sorted(s.items())))
        if len(seen) > 1:
            differ.append(name)
        final = CC.answers(rows, **params)
        if any(v and not final[x]["in_force"] for t in seen for x, v in t):
            shows_out.append(name)
    return differ, shows_out


def main():
    global MAX_ROWS, WIDE
    WIDE = "--wide" in sys.argv
    if "--rows" in sys.argv:
        MAX_ROWS = int(sys.argv[sys.argv.index("--rows") + 1])
    n, problems = CC.check_cases()
    fx = json.load(open(FIXTURE, encoding="utf-8"))
    answers = 0
    for c in fx["cases"]:
        got = CC.answers(c["rows"], c["merge"])
        if got != c["answers"]:
            problems.append("fixture %s: the reference gives %s, the fixture %s" % (c["name"], got, c["answers"]))
        answers += len(c["answers"])
        by = {r["id"]: r for r in c["rows"]}
        for order in c["orders"]:
            held = set()
            for i in order:
                if not all(x in held or x not in by for x in by[i]["names"]):
                    problems.append("fixture %s: order %s takes %s before what it names" % (c["name"], order, i))
                held.add(i)
            if CC.answers([by[i] for i in order], c["merge"]) != c["answers"]:
                problems.append("fixture %s: order %s ends elsewhere" % (c["name"], order))
    if {c["name"] for c in fx["cases"]} != {c[0] for c in CC.CASES}:
        problems.append("the fixture's cases are not the table's")

    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 3
    run = explore(workers)
    for prop, (note, rows) in sorted(run.bad.items()):
        problems.append("%s: %s\n    %s" % (prop, note, "\n    ".join(map(str, rows))))

    plants = [("union", dict(merge="union")), ("count_first_self_union", dict(merge="count_first_self_union")),
              ("member's tips row read", dict(self_tips=True))]
    caught = 0
    for name, kw in plants:
        p = Run(limit=1, **kw)
        p.go(list(HEADS), [])
        if "cannot_add" in p.bad:
            caught += 1
        else:
            problems.append("plant %s: not caught" % name)

    differ, shows_out = first_held()
    for p in problems:
        print(p)
    print("first-held fallback (not part of the proposal): in %d of %d cases two arrival orders of one set of rows "
          "show different rooms; in %d it shows a row the proposal keeps out" % (len(differ), n, len(shows_out)))
    print("RESULT: %s: %d cases, %d content answers; %d histories of up to %d rows%s, %d extensions compared; a "
          "member's backdated end took a kept row out by E3 in %d; plants caught %d of %d"
          % ("ok" if not problems else "%d problems" % len(problems), n, answers, run.worlds, MAX_ROWS,
             " (wide)" if WIDE else "", run.pairs,
             run.e3, caught, len(plants)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
