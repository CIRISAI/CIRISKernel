#!/usr/bin/env python3
"""
check_conferral_two.py: one row that needs two standings (models/tla/CONFERRAL_END.md section J).

A node N is its owner's by an owner binding and holds a duty by a root grant. One act (a build row) needs both.
Each standing has its own record:

    the grant     head G0 (the bundle in force); EG, the count's end of the grant, naming G0
    the binding   B0 (N is O1's); B1, a re-binding to O2, naming B0: the end of O1's binding at B0 and the
                  first row of O2's; AC, O2's acceptance of the grant under B1, naming B1

An act is judged under each record by conferral_end.answers, and the two answers are joined bit by bit: it
counts for an owner when it counts under the grant and under that owner's binding, and it is in force when it
is in force under both. What differs between the readings is how the act is placed against the binding:

    one         the act names the grant's head only (the text of CC 3.1.2.1 as it stood)
    named       it also names the binding row it is under: B0, or B1
    named_acc   it also names the row that seats it with its owner: B0, or under the new binding O2's
                acceptance AC (which names B1). An act naming B1 itself counts for nobody

"The binding in the act's causal past" is not a fourth reading. A row has in its past only what it, or a row
it names, names; so the binding is in an act's past only if the act names it or names a row that does.

Every world is built from a true history the graph does not show: for each act, which of B1 and AC its signer
held when it signed. An honest node names the newest row of its reading that it holds. A backdating node names
B0 though it holds B1. Every set of rows a reader may hold (closed under names) is judged.

Properties:
    old_owner   an honest act signed holding B1 does not count for O1
    consent     an act counts for O2 only if its signer held AC when it signed
    one_owner   no act counts for both owners
    kept        an honest act signed before B1 counts under O1's binding; one signed holding AC counts under
                O2's once the reader holds AC
    backdated   a backdated act never counts for O2, and is in force for O1 only by O1's own receipt
    grant_end   once the reader holds EG, an act the count did not receipt is in force for neither owner

Expected: `named_acc` holds all six. `one` breaks old_owner, consent, one_owner and backdated (under `one` an
act names the same rows whoever signs it, so a backdated act counts for O2 as any other does), and `named`
breaks consent. The run fails unless it finds exactly those, which is this file's planted break.

    python3 -I check_conferral_two.py      exit 1 on any difference
"""
import itertools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import conferral_end as CE  # noqa: E402

READINGS = ("one", "named", "named_acc")
PROPS = ("old_owner", "consent", "one_owner", "kept", "backdated", "grant_end")
EXPECTED = {"one": {"old_owner", "consent", "one_owner", "backdated"}, "named": {"consent"}, "named_acc": set()}
A = CE.CONFERRER


def binding_name(reading, held, honest):
    """The binding-side row an act names, given what its signer held of B1 and AC when it signed."""
    if reading == "one":
        return None
    if not honest or "B1" not in held:
        return "B0"
    return "AC" if reading == "named_acc" and "AC" in held else "B1"


def worlds():
    """(rows, acts): rows by id with `names`; acts as {id: (held at signing, honest)}."""
    for has_b1, has_ac, has_eg, n_acts, qg, qb in itertools.product((0, 1), (0, 1), (0, 1), (1, 2), (0, 1), (0, 1)):
        if has_ac and not has_b1:
            continue
        levels = [frozenset()] + ([frozenset({"B1"})] if has_b1 else []) + ([frozenset({"B1", "AC"})] if has_ac else [])
        for hs in itertools.combinations_with_replacement(range(len(levels)), n_acts):    # a series only learns
            for honest in itertools.product((True, False), repeat=n_acts):
                if any(not h and "B1" not in levels[k] for h, k in zip(honest, hs)):
                    continue                                    # nothing to backdate before B1 is held
                rows = {"G0": [], "B0": []}
                if has_b1:
                    rows["B1"] = ["B0"]
                if has_ac:
                    rows["AC"] = ["B1"]
                if has_eg:
                    rows["EG"] = ["G0"]
                acts = {"x%d" % (i + 1): (levels[k], honest[i]) for i, k in enumerate(hs)}
                if qg:
                    rows["qg"] = ["x1"]
                if qb:
                    rows["qb"] = ["x1"]
                yield rows, acts


def judge(reading, rows, acts, held):
    """{act: {"O1": (counted, in_force), "O2": (counted, in_force)}} over the rows a reader holds."""
    xs = [x for x in acts if x in held]
    named = {x: binding_name(reading, *acts[x]) for x in xs}
    grant = [CE.head("G0")] + [CE.act(x, "G0") for x in xs]
    if "EG" in held:
        grant.append(dict(CE.end("G0"), id="EG"))
    if "qg" in held:
        grant.append(CE.receipt("qg", "x1", A))
    g = CE.answers(grant)
    old = [CE.head("B0")]
    for x in xs:
        b = named[x]
        old.append(CE.act(x, "B0" if b == "B0" else None, names=[b] if b else []))
    if "B1" in held:
        old.append(dict(CE.end("B0"), id="B1"))
    if "AC" in held:
        old.append({"id": "AC", "kind": "accept_grant", "signer": "O2", "names": ["B1"]})
    if "qb" in held:
        old.append(CE.receipt("qb", "x1", A))
    o = CE.answers(old)
    out = {}
    for x in xs:
        if reading == "one":
            new = "B1" in held and "AC" in held
        elif reading == "named":
            new = named[x] == "B1" and "AC" in held
        else:
            new = named[x] == "AC"
        gc, gf = g[x]["counted"], g[x]["in_force"]
        out[x] = {"O1": (gc and o[x]["counted"], gf and o[x]["in_force"]), "O2": (gc and new, gf and new),
                  "binding": (o[x]["counted"], new), "grant": (gc, gf)}
    return out


def names_of(reading, rows, acts):
    """Every row's names under a reading, the acts' included (an act names G0, its binding row, its predecessor)."""
    full = dict(rows)
    prev = None
    for x in sorted(acts):
        b = binding_name(reading, *acts[x])
        full[x] = ["G0"] + ([b] if b else []) + ([prev] if prev else [])
        prev = x
    return full


def closed_sets(full):
    ids = sorted(full)
    for bits in itertools.product((0, 1), repeat=len(ids)):
        held = {i for i, b in zip(ids, bits) if b}
        if {"G0", "B0"} <= held and all(set(full[i]) <= held for i in held):
            yield held


def main():
    broke = {r: {} for r in READINGS}
    n_worlds = n_states = 0
    for rows, acts in worlds():
        n_worlds += 1
        for reading in READINGS:
            full = names_of(reading, rows, acts)
            for held in closed_sets(full):
                n_states += 1
                got = judge(reading, rows, acts, held)
                for x, a in got.items():
                    signed_with, honest = acts[x]
                    c1, f1 = a["O1"]
                    c2, _ = a["O2"]
                    b_old, b_new = a["binding"]
                    bad = []
                    if honest and "B1" in signed_with and b_old:
                        bad.append("old_owner")
                    if b_new and "AC" not in signed_with:
                        bad.append("consent")
                    if b_old and b_new:
                        bad.append("one_owner")
                    if honest and "B1" not in signed_with and not b_old:
                        bad.append("kept")
                    if honest and "AC" in signed_with and "AC" in held and not b_new:
                        bad.append("kept")
                    if not honest and (b_new or (f1 and "B1" in held and not (x == "x1" and "qb" in held))):
                        bad.append("backdated")
                    if "EG" in held and not (x == "x1" and "qg" in held) and (f1 or a["O2"][1]):
                        bad.append("grant_end")
                    for p in bad:
                        broke[reading].setdefault(p, "%s signed holding %s%s; the reader holds %s" % (
                            x, sorted(signed_with) or "neither B1 nor AC", "" if honest else " (backdated)",
                            sorted(held)))
    problems = []
    for r in READINGS:
        if set(broke[r]) != EXPECTED[r]:
            problems.append("%s breaks %s, expected %s" % (r, sorted(broke[r]), sorted(EXPECTED[r])))
        for p in sorted(broke[r]):
            print("%-9s breaks %-9s %s" % (r, p, broke[r][p]))
        if not broke[r]:
            print("%-9s holds %s" % (r, ", ".join(PROPS)))
    print("%d true histories, %d (reading, held set) states" % (n_worlds, n_states))
    print("RESULT: %s" % ("ok: named_acc holds all %d properties; one and named break what is expected of them"
                          % len(PROPS) if not problems else "%d problems: %s" % (len(problems), problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
