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
                        scope: no default is taken (12 at this pin, which the Constitution is asked to fill)
    cases        hand-written answers: the audience of each placement as keys; named_within; a targeted row
                 with no room; an unknown family; the copy rule (same room, same signer, signer in the audience,
                 concluded; a refused row carries nothing)

    Planted breaks (audience.MUT), each caught: undecided_defaulted, pinned_unread, named_within_unread,
    copy_cross_room, copy_any_signer, copy_unconcluded, match_first, seats_not_within (the keys a seat row seats
    or removes held to named_within), history_unread (every row read as history_on_join full).

    python3 -I check_audience.py      exit 1 on any difference
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import audience as AU  # noqa: E402

ROSTER = {"r1": ("a", "b", "c"), "r2": ("a", "e"), "r3": ("a", "b", "j")}
PERSON = {"a": ("a", "a2")}
roster = lambda room: ROSTER.get(room, ())
person = lambda k: PERSON.get(k, (k,))
# the cohort scope words a generated row takes, one per placement
SCOPES = (("self", None), ("family", "r1"), ("community", "r1"), ("federation", None), ("addressed", None))


def row(i, family, scope, signer="a", room=None, named=(), names=(), concluded=True, kind=None, obj=None, to=(),
        history=None, seats=()):
    """A row. `kind` "offer" or "unseat", with `obj` and `to`, makes it a seat row: the keys it seats or removes
    are derived from it (audience.seats_of), never stated."""
    r = {"id": i, "family": family, "scope": scope, "signer": signer, "room": room, "named": list(named),
         "names": list(names), "concluded": concluded}
    if seats and not kind:                       # the earlier form (review scripts): a seat offer over its room
        kind, obj, to = "offer", room, seats
    if kind:
        r.update(kind=kind, obj=obj, to=list(to))
    if history:
        r["history_on_join"] = history
    return r


def seat_row(i, kind, room, to, **kw):
    """A seat offer or unseat over `room`, naming the keys it seats or removes."""
    return row(i, "partner_role:member", "community", room=room, named=list(to), kind=kind, obj=room, to=to, **kw)


def joins_of(w):
    """A case's joins: `joined` {room: {key: admitting row}}, `history` {room: the record's value}, `before` [[row,
    admitting row]]: the row is in the admitting row's past."""
    w = w or {}
    before = {tuple(p) for p in w.get("before", ())}
    at = w.get("at_head", {})
    return {"joined": lambda room, k: w.get("joined", {}).get(room, {}).get(k),
            "history": lambda room: w.get("history", {}).get(room),
            "past": lambda a, b: (a, b) in before,
            "at_head": lambda room, i: at.get(i, roster(room))}       # a case that states none: no member changed


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
    # a seat offer or unseat over the room: the keys it seats or removes are within its audience. group:roster and
    # membership answer Undecided at this pin, so the rule is shown on a placed consent family (partner_role)
    ("admission_names_joiner", "a pending admission of j at the room names j, who is not on the roster yet: j is "
     "in its audience",
     [seat_row("v", "offer", "r1", ["j"], concluded=False)],
     {"v": P("targeted_room", ROOM + ["j"])}),
    ("removal_names_removed_key", "a removal of c, read where the roster no longer lists c, names c: c is in its "
     "audience",
     [seat_row("x", "unseat", "r2", ["c"])],
     {"x": P("targeted_room", ["a", "c", "e"])}),
    ("seat_row_names_outsider", "the same admission also names z, a key it does not seat: refused",
     [dict(seat_row("v", "offer", "r1", ["j"]), named=["j", "z"])],
     {"v": REF("named_outside_audience")}),
    ("non_roster_row_names_outsider", "a row that seats no one names z, off the roster: still refused",
     [row("m", "partner_role:member", "community", room="r1", named=["z"])], {"m": REF("named_outside_audience")}),
    ("roster_family_undecided", "group:roster itself answers Undecided at this pin, its seats apart",
     [dict(seat_row("g", "offer", "r1", ["j"]), family="group:roster")], {"g": UND("group:roster")}),
    ("seats_derived_not_stated", "an offer over ANOTHER object names j: its `to` is no seat of this room, and j is "
     "held to named_within",
     [row("v", "partner_role:member", "community", room="r1", named=["j"], kind="offer", obj="r9", to=["j"])],
     {"v": REF("named_outside_audience")}),
    # history_on_join (CC 2.1, CC 4.4.3.16): j was admitted to r3 by `adm`, after the row m (m in adm's past)
    ("history_from_join", "the room's record states nothing: the default from_join, and j, admitted after m, is "
     "not owed m",
     [row("m", "chat:general", "community", room="r3")], {"m": P("targeted_room", ["a", "b"])},
     {"joined": {"r3": {"j": "adm"}}, "before": [["m", "adm"]]}),
    ("history_record_full", "the room's record states history_on_join full: j is owed m",
     [row("m", "chat:general", "community", room="r3")], {"m": P("targeted_room", ["a", "b", "j"])},
     {"joined": {"r3": {"j": "adm"}}, "before": [["m", "adm"]], "history": {"r3": "full"}}),
    ("history_record_from_join", "the room's record states from_join: j is not owed m",
     [row("m", "chat:general", "community", room="r3")], {"m": P("targeted_room", ["a", "b"])},
     {"joined": {"r3": {"j": "adm"}}, "before": [["m", "adm"]], "history": {"r3": "from_join"}}),
    ("history_row_full", "the row's producer keeps it (its own history_on_join full), the record stating from_join: "
     "j is owed m",
     [row("m", "chat:general", "community", room="r3", history="full")], {"m": P("targeted_room", ["a", "b", "j"])},
     {"joined": {"r3": {"j": "adm"}}, "before": [["m", "adm"]], "history": {"r3": "from_join"}}),
    ("history_join_concurrent", "j was admitted concurrently with m: neither is in the other's past, so the "
     "admission is not after m and j is owed m under from_join",
     [row("m", "chat:general", "community", room="r3")], {"m": P("targeted_room", ["a", "b", "j"])},
     {"joined": {"r3": {"j": "adm"}}, "before": []}),
    ("history_row_after_join", "m has j's admission in its past (m is signed after the join): j is owed m under "
     "from_join",
     [row("m", "chat:general", "community", room="r3")], {"m": P("targeted_room", ["a", "b", "j"])},
     {"joined": {"r3": {"j": "adm"}}, "before": [["adm", "m"]]}),
    ("removed_later_owed_nothing", "c was removed from r2's roster after m: the roster as it stands does not list c, "
     "and c is owed nothing further",
     [row("m", "chat:general", "community", room="r2")], {"m": P("targeted_room", ["a", "e"])}),
    ("targeted_no_room", "a targeted row names its room",
     [row("m", "chat:general", "community")], {"m": REF("no_room")}),
    ("undecided_family", "a family whose placement cell is not table data answers Undecided naming the family",
     [row("k", "stream:head", "community", room="r1"), row("q", "preserve_request", "self")],
     {"k": UND("stream:head"), "q": UND("preserve_request")}),
    ("undecided_by_pattern", "an undecided family matched by a pattern names the pattern",
     [row("k", "custody:blob", "community", room="r1")], {"k": UND("custody:{kind}")}),
    # families the Constitution's placement lane stated (d103e60): undecided before it
    ("ack_placed", "an acknowledgement (act:ack) is placed by its scope: at the community, the roster",
     [row("k", "act:ack", "community", room="r1")], {"k": P("targeted_room", ROOM)}),
    ("window_not_commons", "a window row is placed at self, a family or a room, never the commons",
     [row("k", "window:open", "community", room="r1"), row("q", "window:open", "federation")],
     {"k": P("targeted_room", ROOM), "q": REF("placement_not_allowed")}),
    ("key_record_room_or_commons", "a key record is placed at a room or the commons, not at self",
     [row("k", "key:record", "federation"), row("q", "key:record", "self")],
     {"k": P("commons", AU.EVERYONE), "q": REF("placement_not_allowed")}),
    ("contribution_commons", "a contribution is pinned to the commons",
     [row("k", "contribution:person", "federation"), row("q", "contribution:person", "community", room="r1")],
     {"k": P("commons", AU.EVERYONE), "q": REF("placement_not_allowed")}),
    ("unknown_family", "a family no pattern matches is refused",
     [row("m", "nosuch:thing", "community", room="r1")], {"m": REF("family_unknown")}),
    ("most_literal_pattern", "accord:lifecycle is its own family, not accord:*",
     [row("m", "accord:lifecycle", "self"), row("n", "accord:other", "self")],
     {"m": P("self_collective", ["a", "a2"]), "n": P("self_collective", ["a", "a2"])}),
    # the copy rule
    ("copy_same_room", "an addressed row in room r1, named by a concluded row in r1 whose signer d it addresses: "
     "the copy rule adds no key the addressed row's own placement withholds, so it stays with its addressees",
     [row("x", "census:member:share", "addressed", room="r1", named=["d"]),
      row("m", "chat:general", "community", signer="d", room="r1", names=["x"])],
     {"x": P("addressed", ["a", "d"]), "m": P("targeted_room", ["a", "b", "c", "d"])}),
    ("copy_signer_outside", "the namer's signer b is not in the addressed row's audience: it carries nobody",
     [row("x", "census:member:share", "addressed", room="r1", named=["d"]),
      row("m", "chat:general", "community", signer="b", room="r1", names=["x"])],
     {"x": P("addressed", ["a", "d"]), "m": P("targeted_room", ROOM)}),
    ("copy_other_room", "the namer is in another room and signed by another key: the row does not leave its room",
     [row("x", "census:member:share", "addressed", room="r2", named=["d"]),
      row("m", "chat:general", "community", signer="d", room="r1", names=["x"])],
     {"x": P("addressed", ["a", "d"]), "m": P("targeted_room", ["a", "b", "c", "d"])}),
    ("copy_author_carries", "the author's self row named by its row in r1: the copy rule adds no key a self row's "
     "placement withholds, so it stays with the author's own keys",
     [row("s", "chat:general", "self"), row("m", "chat:general", "community", room="r1", names=["s"])],
     {"s": P("self_collective", ["a", "a2"]), "m": P("targeted_room", ROOM)}),
    ("copy_unconcluded", "a namer that does not conclude carries nobody",
     [row("s", "chat:general", "self"), row("m", "chat:general", "community", room="r1", names=["s"], concluded=False)],
     {"s": P("self_collective", ["a", "a2"]), "m": P("targeted_room", ROOM)}),
    ("copy_from_refused", "a refused namer carries nobody",
     [row("s", "chat:general", "self"), row("m", "chat:general", "community", room="r1", names=["s"], named=["z"])],
     {"s": P("self_collective", ["a", "a2"]), "m": REF("named_outside_audience")}),
    ("copy_chain", "a commons row by b names the room row, which names the author's self row: each keeps the "
     "audience its own placement owes it",
     [row("s", "chat:general", "self"), row("m", "chat:general", "community", room="r1", names=["s"]),
      row("c", "chat:general", "federation", signer="b", room="r1", names=["m"])],
     {"s": P("self_collective", ["a", "a2"]), "m": P("targeted_room", ROOM), "c": P("commons", AU.EVERYONE)}),
    # review r79 (leak.py): the copy rule never adds a key the named row's own place() withholds
    ("copy_reply_from_join", "j joined r3 after m0 and m1 (from_join); b's reply d after the join names m1, which "
     "names m0: d reaches j, m1 and m0 do not. A joiner under from_join can receive a reply whose parent it is not owed",
     [row("m0", "chat:general", "community", room="r3"),
      row("m1", "chat:general", "community", signer="b", room="r3", names=["m0"]),
      row("d", "chat:general", "community", signer="b", room="r3", names=["m1"])],
     {"m0": P("targeted_room", ["a", "b"]), "m1": P("targeted_room", ["a", "b"]), "d": P("targeted_room", ["a", "b", "j"])},
     {"joined": {"r3": {"j": "adm"}}, "before": [["m0", "adm"], ["m1", "adm"], ["m0", "m1"], ["m0", "d"], ["m1", "d"],
                                                 ["adm", "d"]]}),
    ("copy_admission_from_join", "j's admission names its head m1: it carries none of the older rows to j",
     [row("m0", "chat:general", "community", room="r3"),
      row("m1", "chat:general", "community", signer="b", room="r3", names=["m0"]),
      dict(seat_row("adm", "offer", "r3", ["j"]), names=["m1"])],
     {"m0": P("targeted_room", ["a", "b"]), "m1": P("targeted_room", ["a", "b"]), "adm": P("targeted_room", ["a", "b", "j"])},
     {"joined": {"r3": {"j": "adm"}}, "before": [["m0", "adm"], ["m1", "adm"], ["m0", "m1"]]}),
    ("copy_unaccepted_outsider", "a concluded offer to z, never accepted, names its head h1: z gets the offer, not h1 "
     "or h0",
     [row("h0", "chat:general", "community", signer="c", room="r1"),
      row("h1", "chat:general", "community", signer="b", room="r1", names=["h0"]),
      dict(seat_row("o", "offer", "r1", ["z"]), names=["h1"])],
     {"h0": P("targeted_room", ROOM), "h1": P("targeted_room", ROOM), "o": P("targeted_room", ROOM + ["z"])}),
    ("copy_removed_key", "the removal of c names its head g1: c gets the removal, not g1 or g0",
     [row("g0", "chat:general", "community", signer="e", room="r2"),
      row("g1", "chat:general", "community", room="r2", names=["g0"]),
      dict(seat_row("x", "unseat", "r2", ["c"]), names=["g1"])],
     {"g0": P("targeted_room", ["a", "e"]), "g1": P("targeted_room", ["a", "e"]), "x": P("targeted_room", ["a", "c", "e"])}),
    # review r79 (named.py): named_within is read at the row's own head
    ("named_at_own_head", "a names c while c sat in r2; c is removed later: the row stays placed (placement is "
     "monotone), and is owed the current roster and the key it names",
     [row("m", "chat:general", "community", room="r2", named=["c"])], {"m": P("targeted_room", ["a", "c", "e"])},
     {"at_head": {"m": ["a", "c", "e"]}}),
    ("named_outsider_joins_later", "a row naming j before j sat in r3 stays refused after j joins",
     [row("m", "chat:general", "community", room="r3", named=["j"])], {"m": REF("named_outside_audience")},
     {"at_head": {"m": ["a", "b"]}}),
    # review r79: an unknown history_on_join word is absent, and falls through to the record
    ("history_unknown_word_record_full", "the row states history_on_join 'always', a word the door refuses: read as "
     "absent, the record's full decides and j is owed m",
     [row("m", "chat:general", "community", room="r3", history="always")], {"m": P("targeted_room", ["a", "b", "j"])},
     {"joined": {"r3": {"j": "adm"}}, "before": [["m", "adm"]], "history": {"r3": "full"}}),
    ("history_unknown_word_default", "the same word with the record silent: the default from_join, j is not owed m",
     [row("m", "chat:general", "community", room="r3", history="always")], {"m": P("targeted_room", ["a", "b"])},
     {"joined": {"r3": {"j": "adm"}}, "before": [["m", "adm"]]}),
    ("history_unknown_record_word", "the record states an unknown word: absent, the default from_join",
     [row("m", "chat:general", "community", room="r3")], {"m": P("targeted_room", ["a", "b"])},
     {"joined": {"r3": {"j": "adm"}}, "before": [["m", "adm"]], "history": {"r3": "sometimes"}}),
]

# family names that tie: two patterns matching one name with as many literal segments; a synthetic table, since
# the pinned table has none (tools/family_placement.py refuses one). (families, name, the answer of family_of)
TIES = [
    (["x:{a}", "{b}:y"], "x:y", AU.AMBIGUOUS),
    (["x:{a}", "{b}:y"], "x:z", "x:{a}"),
    (["x:*", "x:{a}"], "x:y", AU.AMBIGUOUS),
    (["x:*", "x:y"], "x:y", "x:y"),
    (["x:*", "x:{a}"], "x:y:z", "x:*"),
]

# (planted breaks switched on together, the case that catches them). The copy rule's three gates are planted with
# its bound lifted (copy_unbounded): under the bound they are not observable
PLANTS = [(("undecided_defaulted",), "undecided_family"), (("pinned_unread",), "pinned_self"),
          (("named_within_unread",), "named_outside_audience"),
          (("copy_unbounded",), "copy_reply_from_join"),
          (("copy_unbounded", "copy_cross_room"), "copy_other_room"),
          (("copy_unbounded", "copy_any_signer"), "copy_signer_outside"),
          (("copy_unbounded", "copy_unconcluded"), "copy_unconcluded"),
          (("match_first",), "table"), (("seats_not_within",), "admission_names_joiner"),
          (("seats_any_obj",), "seats_derived_not_stated"),
          (("named_within_current",), "named_at_own_head"),
          (("history_unread",), "history_from_join"), (("word_read",), "history_unknown_word_record_full"),
          (("tie_first",), "ties")]


def generated():
    """Every family pattern in every cohort scope: (pattern, name, scope, room, answer)."""
    out = []
    for p in sorted(AU.FAMILIES):
        name = AU.instance(p)
        for scope, room in SCOPES:
            r = row("x", name, scope, room=room, named=["b"] if room else [])
            heads = dict(AU.NO_JOINS, at_head=lambda rm, i: roster(rm))     # the generated rows: no member changes
            out.append((p, name, scope, room, enc(AU.place(r, roster, person, heads))))
    return out


# regard:{subject_kind} (a reader's weight at self, a vouch at federation), new at d103e60. The table states it at the
# four scopes of the default (a cc-table cell naming all four), so it is placed at a family and a room too. Its cases
# run once the pinned table holds it.
REGARD = "regard:{subject_kind}"
REGARD_CASES = [
    ("regard_self", "a regard placed at self: the reader's own weight, its own keys",
     [row("g", "regard:person", "self")], {"g": P("self_collective", ["a", "a2"])}),
    ("regard_federation", "a regard placed at the federation: a vouch, for everyone",
     [row("g", "regard:person", "federation")], {"g": P("commons", AU.EVERYONE)}),
    ("regard_in_a_room", "the table states regard at a family and a room as well: placed there, the roster",
     [row("g", "regard:person", "community", room="r1"), row("h", "regard:person", "family", room="r1")],
     {"g": P("targeted_room", ROOM), "h": P("targeted_family", ROOM)}),
    ("regard_not_addressed", "regard is not addressed",
     [row("g", "regard:person", "addressed", named=["d"])], {"g": REF("placement_not_allowed")}),
]


def check_derivation():
    """tools/family_placement.py reads a cell pinned to a set of placements apart, self and federation (the CC
    table's words self_collective and commons), as exactly that set, in the table's order."""
    sys.path.insert(0, os.path.join(AU.ROOT, "tools"))
    import family_placement as FP
    problems = []
    cell = lambda v, **kw: {"placement": dict({"value": v, "source": "cc-table"}, **kw)}
    for v, want in ((["commons", "self_collective"], (["self_collective", "commons"], None)),
                    ("commons", (["commons"], None)),
                    (["self_collective", "nowhere"], (None, "cc-table: ['self_collective', 'nowhere']"))):
        if FP.placement_of(cell(v)) != want:
            problems.append("derivation: %s gives %s" % (v, FP.placement_of(cell(v))))
    if FP.placement_of(cell(None, rule="default")) != (list(AU.PLACEMENTS[:4]), None):
        problems.append("derivation: the default")
    # a code-sourced cell is never table data, even where its words are all placement words (the Constitution's
    # ruling: community:listing, group:roster and membership stay Undecided until the text states them)
    code = {"placement": {"value": ["targeted_family", "targeted_room"], "source": "code-v61",
                          "closed": "targeted_family | targeted_room"}}
    if FP.placement_of(code)[0] is not None:
        problems.append("derivation: a code-sourced cell is read as table data")
    # the generator refuses a table whose patterns tie on a name, and finds no tie in the pinned one
    if not FP.ties(["x:{a}", "{b}:y"]) or not FP.ties(["x:*", "x:{a}"]) or FP.ties(["x:*", "x:y"]):
        problems.append("derivation: the tie check")
    if FP.ties(list(AU.FAMILIES)):
        problems.append("derivation: the pinned table ties: %s" % FP.ties(list(AU.FAMILIES))[:3])
    return problems


def check_ties():
    problems = []
    for fams, name, want in TIES:
        got = AU.family_of(name, {f: None for f in fams})
        if got != want:
            problems.append("ties: %s over %s is %s, want %s" % (name, fams, got, want))
    return problems


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


def cases_now():
    """The case table, with the regard cases once the pinned table holds that family."""
    return CASES + (REGARD_CASES if REGARD in AU.FAMILIES else [])


def check_cases():
    problems = []
    for name, _, rows, want, *w in cases_now():
        got = {i: enc(a) for i, a in AU.audiences(rows, roster, person, joins_of(w[0] if w else None)).items()}
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
            "ties": [{"families": f, "name": n, "answer": a} for f, n, a in TIES],
            "generated": [{"family": p, "name": n, "scope": s, "room": r, "answer": a} for p, n, s, r, a in generated()],
            "cases": [{"name": n, "about": ab, "rows": rows, "joins": w[0] if w else {},
                       "answers": {i: enc(a) for i, a in
                                   AU.audiences(rows, roster, person, joins_of(w[0] if w else None)).items()}}
                      for n, ab, rows, _, *w in cases_now()]}


def main():
    problems = check_table() + check_cases() + check_derivation() + check_ties()
    if REGARD not in AU.FAMILIES:
        print("  %s is not in the pinned table yet: its %d cases wait for the re-pin" % (REGARD, len(REGARD_CASES)))
    caught = 0
    for muts, where in PLANTS:
        mut = "+".join(muts)
        AU.MUT.clear(); AU.MUT.update(muts)
        try:
            got = check_table() + check_cases() + check_ties()
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
             ", provisional" if s.get("provisional") else "", len(generated()), len(cases_now()), caught, len(PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
