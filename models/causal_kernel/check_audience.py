#!/usr/bin/env python3
"""
check_audience.py: audience.py, the placement and the audience of a row family by family (CC 3.4.5.1, CC 5.2),
over the family model's placement cells (data/family_placement.json).

    table        every family pattern of the table: a name built from it resolves to it (no other pattern ties
                 or wins), and in each cohort scope its row is placed with the scope's audience, refused, or
                 Undecided naming the family, as its cell says:
        default         a family on the default is placed in self, family, community and federation, and refused
                        `addressed`
        pinned          a family the CC table pins is placed exactly in the placements its cell names
        undecided       a family whose cell is not table data answers Undecided naming the family in every
                        scope: no default is taken (the 22 the Constitution is asked to fill)
    cases        hand-written answers: the audience of each placement as keys; named_within; a targeted row
                 with no room; an unknown family; the copy rule (same room, same signer, signer in the audience,
                 concluded; a refused row carries nothing)

    Planted breaks (audience.MUT), each caught: undecided_defaulted, pinned_unread, named_within_unread,
    copy_cross_room, copy_any_signer, copy_unconcluded, match_first.

    python3 -I check_audience.py      exit 1 on any difference
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import audience as AU  # noqa: E402

ROSTER = {"r1": ("a", "b", "c"), "r2": ("a", "e")}
PERSON = {"a": ("a", "a2")}
roster = lambda room: ROSTER.get(room, ())
person = lambda k: PERSON.get(k, (k,))
# the cohort scope words a generated row takes, one per placement
SCOPES = (("self", None), ("family", "r1"), ("community", "r1"), ("federation", None), ("addressed", None))


def row(i, family, scope, signer="a", room=None, named=(), names=(), concluded=True):
    return {"id": i, "family": family, "scope": scope, "signer": signer, "room": room, "named": list(named),
            "names": list(names), "concluded": concluded}


def enc(a):
    if a[0] == "placed":
        return ["placed", a[1], AU.EVERYONE if a[2] == AU.EVERYONE else sorted(a[2])]
    return list(a)


P = lambda placement, keys: ["placed", placement, keys if keys == AU.EVERYONE else sorted(keys)]
REF = lambda t: ["refused", t]
UND = lambda f: ["undecided", f]
ROOM = sorted(ROSTER["r1"])

# (name, about, rows, {row: answer})
CASES = [
    ("default_room", "a chat row placed at the community: the roster and the key it names",
     [row("m", "chat:general", "community", room="r1", named=["b"])], {"m": P("targeted_room", ROOM)}),
    ("default_family", "the same family placed at a family: the family's roster",
     [row("m", "chat:general", "family", room="r1")], {"m": P("targeted_family", ROOM)}),
    ("default_self", "placed at self: the signer's own keys",
     [row("m", "chat:general", "self")], {"m": P("self_collective", ["a", "a2"])}),
    ("default_commons", "placed at the federation: everyone",
     [row("m", "chat:general", "federation")], {"m": P("commons", AU.EVERYONE)}),
    ("default_not_addressed", "a family on the default is not addressed: refused",
     [row("m", "chat:general", "addressed", named=["d"])], {"m": REF("placement_not_allowed")}),
    ("pinned_self", "device:label is pinned to self: placed there, refused at the community",
     [row("s", "device:label", "self"), row("t", "device:label", "community", room="r1")],
     {"s": P("self_collective", ["a", "a2"]), "t": REF("placement_not_allowed")}),
    ("pinned_room", "a moderator ballot is pinned to the room: refused at self",
     [row("s", "ballot:moderator", "self"), row("t", "ballot:moderator", "community", room="r1")],
     {"s": REF("placement_not_allowed"), "t": P("targeted_room", ROOM)}),
    ("pinned_addressed", "a member's census share is addressed: its audience is the keys it names and its signer",
     [row("s", "census:member:share", "addressed", named=["d"]), row("t", "census:member:share", "community", room="r1")],
     {"s": P("addressed", ["a", "d"]), "t": REF("placement_not_allowed")}),
    ("pinned_commons", "a holon claim is pinned to the commons",
     [row("s", "holon:claim", "federation"), row("t", "holon:claim", "family", room="r1")],
     {"s": P("commons", AU.EVERYONE), "t": REF("placement_not_allowed")}),
    ("pinned_subset", "a deferral request may be placed at self, a family or a room, not the commons",
     [row("s", "deferral:request", "federation"), row("t", "deferral:request", "family", room="r1")],
     {"s": REF("placement_not_allowed"), "t": P("targeted_family", ROOM)}),
    ("named_outside_audience", "a row at the community may name only keys within its audience: z is off the roster",
     [row("m", "chat:general", "community", room="r1", named=["z"])], {"m": REF("named_outside_audience")}),
    ("targeted_no_room", "a targeted row names its room",
     [row("m", "chat:general", "community")], {"m": REF("no_room")}),
    ("undecided_family", "a family whose placement cell is not table data answers Undecided naming the family",
     [row("k", "act:ack", "community", room="r1"), row("q", "key:record", "self")],
     {"k": UND("act:ack"), "q": UND("key:record")}),
    ("undecided_by_pattern", "an undecided family matched by a pattern names the pattern",
     [row("k", "window:open", "community", room="r1")], {"k": UND("window:{state}")}),
    ("unknown_family", "a family no pattern matches is refused",
     [row("m", "nosuch:thing", "community", room="r1")], {"m": REF("family_unknown")}),
    ("most_literal_pattern", "accord:lifecycle is its own family, not accord:*",
     [row("m", "accord:lifecycle", "self"), row("n", "accord:other", "self")],
     {"m": P("self_collective", ["a", "a2"]), "n": P("self_collective", ["a", "a2"])}),
    # the copy rule
    ("copy_same_room", "an addressed row in room r1, named by a concluded row in r1 whose signer d it addresses: "
     "it joins the namer's audience",
     [row("x", "census:member:share", "addressed", room="r1", named=["d"]),
      row("m", "chat:general", "community", signer="d", room="r1", names=["x"])],
     {"x": P("addressed", ["a", "b", "c", "d"]), "m": P("targeted_room", ["a", "b", "c", "d"])}),
    ("copy_signer_outside", "the namer's signer b is not in the addressed row's audience: it carries nobody",
     [row("x", "census:member:share", "addressed", room="r1", named=["d"]),
      row("m", "chat:general", "community", signer="b", room="r1", names=["x"])],
     {"x": P("addressed", ["a", "d"]), "m": P("targeted_room", ROOM)}),
    ("copy_other_room", "the namer is in another room and signed by another key: the row does not leave its room",
     [row("x", "census:member:share", "addressed", room="r2", named=["d"]),
      row("m", "chat:general", "community", signer="d", room="r1", names=["x"])],
     {"x": P("addressed", ["a", "d"]), "m": P("targeted_room", ["a", "b", "c", "d"])}),
    ("copy_author_carries", "the author's own row elsewhere: its self row named by its row in r1 joins r1's audience",
     [row("s", "chat:general", "self"), row("m", "chat:general", "community", room="r1", names=["s"])],
     {"s": P("self_collective", ["a", "a2", "b", "c"]), "m": P("targeted_room", ROOM)}),
    ("copy_unconcluded", "a namer that does not conclude carries nobody",
     [row("s", "chat:general", "self"), row("m", "chat:general", "community", room="r1", names=["s"], concluded=False)],
     {"s": P("self_collective", ["a", "a2"]), "m": P("targeted_room", ROOM)}),
    ("copy_from_refused", "a refused namer carries nobody",
     [row("s", "chat:general", "self"), row("m", "chat:general", "community", room="r1", names=["s"], named=["z"])],
     {"s": P("self_collective", ["a", "a2"]), "m": REF("named_outside_audience")}),
    ("copy_chain", "a commons row by b names the room row, which names the author's self row: both reach everyone",
     [row("s", "chat:general", "self"), row("m", "chat:general", "community", room="r1", names=["s"]),
      row("c", "chat:general", "federation", signer="b", room="r1", names=["m"])],
     {"s": P("self_collective", AU.EVERYONE), "m": P("targeted_room", AU.EVERYONE), "c": P("commons", AU.EVERYONE)}),
]

PLANTS = [("undecided_defaulted", "undecided_family"), ("pinned_unread", "pinned_self"),
          ("named_within_unread", "named_outside_audience"), ("copy_cross_room", "copy_other_room"),
          ("copy_any_signer", "copy_signer_outside"), ("copy_unconcluded", "copy_unconcluded"),
          ("match_first", "table")]


def generated():
    """Every family pattern in every cohort scope: (pattern, name, scope, room, answer)."""
    out = []
    for p in sorted(AU.FAMILIES):
        name = AU.instance(p)
        for scope, room in SCOPES:
            r = row("x", name, scope, room=room, named=["b"] if room else [])
            out.append((p, name, scope, room, enc(AU.place(r, roster, person))))
    return out


def check_table():
    problems = []
    for p in sorted(AU.FAMILIES):
        name = AU.instance(p)
        try:
            got = AU.family_of(name)
        except AssertionError as e:
            problems.append("table: %s ties: %s" % (name, e))
            continue
        if got != p:
            problems.append("table: %s resolves to %s, not %s" % (name, got, p))
    for p, name, scope, room, a in generated():
        cell = AU.FAMILIES[p]
        placement = AU.SCOPE_PLACEMENT[scope]
        if cell["undecided"] is not None:
            want = UND(p)
        elif placement not in cell["allowed"]:
            want = REF("placement_not_allowed")
        else:
            want = a if a[0] == "placed" and a[1] == placement else None
        if a != want:
            problems.append("table: %s at %s: %s" % (name, scope, a))
    return problems


def check_cases():
    problems = []
    for name, _, rows, want in CASES:
        got = {i: enc(a) for i, a in AU.audiences(rows, roster, person).items()}
        for i, w in want.items():
            if got.get(i) != w:
                problems.append("%s: %s is %s, want %s" % (name, i, got.get(i), w))
    return problems


def fixture():
    """The fixture: the table's source, every generated answer and every case with its answers."""
    assert not check_table() and not check_cases()
    return {"about": "the placement and the audience (keys) of a row, family by family: models/causal_kernel/"
                     "audience.py over data/family_placement.json; checked by check_audience.py",
            "source": AU.TABLE["_source"], "roster": {k: list(v) for k, v in ROSTER.items()},
            "person": {k: list(v) for k, v in PERSON.items()},
            "generated": [{"family": p, "name": n, "scope": s, "room": r, "answer": a} for p, n, s, r, a in generated()],
            "cases": [{"name": n, "about": ab, "rows": rows,
                       "answers": {i: enc(a) for i, a in AU.audiences(rows, roster, person).items()}}
                      for n, ab, rows, _ in CASES]}


def main():
    problems = check_table() + check_cases()
    caught = 0
    for mut, where in PLANTS:
        AU.MUT.clear(); AU.MUT.add(mut)
        try:
            got = check_table() + check_cases()
        finally:
            AU.MUT.clear()
        hit = any(g.startswith(where + ":") for g in got)
        caught += hit
        print("  plant %-20s %s (%s)" % (mut, "caught" if hit else "NOT CAUGHT", where))
        if not hit:
            problems.append("plant %s not caught by %s" % (mut, where))
    s = AU.TABLE["_source"]
    for p in problems:
        print(p)
    print("RESULT: %s: %d families (%d on the default, %d pinned, %d undecided; %s %s%s), %d generated answers, "
          "%d cases; %d of %d planted breaks caught"
          % ("ok" if not problems else "%d problems" % len(problems), s["families"], s["on_the_default"],
             s["pinned_by_the_table"], s["undecided"], s["branch"], s["commit"][:7],
             ", provisional" if s.get("provisional") else "", len(generated()), len(CASES), caught, len(PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
