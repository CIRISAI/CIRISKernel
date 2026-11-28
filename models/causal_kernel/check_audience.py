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

    Planted breaks (audience.MUT), each caught: undecided_defaulted, pinned_unread, named_within_unread, the copy
    rule's copy_any_carrier, copy_any_signer, copy_unconcluded, copy_off_roster and key_grant_carried, match_first,
    seats_not_within, seats_any_obj, named_within_current, history_unread and word_read (history_of), tie_first.
    copy_cross_room is not planted: a room row's carriage is bounded by its own room's roster, which already
    serves it, so a carrier of another room adds nothing observable.

    python3 -I check_audience.py      exit 1 on any difference
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import audience as AU  # noqa: E402

ROSTER = {"r1": ("a", "b", "c"), "r2": ("a", "e"), "r3": ("a", "b", "j")}
PERSON = {"a": ("a", "a2"), "a2": ("a", "a2")}
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


def seat_row(i, kind, room, to, family="membership:invite", **kw):
    """A seat offer or unseat over `room`, naming the keys it seats or removes: by default of membership, a seat of
    the roster itself (a joiner, a removed key); ballot:moderator_acceptance seats a duty, a member only."""
    return row(i, family, "community", room=room, named=list(to), kind=kind, obj=room, to=to, **kw)


BALLOT = "ballot:moderator_acceptance"


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
    # a seat offer or unseat over the room: the keys a seat of the ROSTER seats or removes are within its audience
    # (ROSTER_SEAT_CASES, which wait until membership is stated); a seat of a DUTY (the moderator's acceptance)
    # seats a member at the row's own head, never an outsider (review r84)
    ("removal_names_removed_key", "the moderator's acceptance unseats c, a member at its head no longer on the "
     "roster: c is in its audience",
     [seat_row("x", "unseat", "r2", ["c"], family=BALLOT)],
     {"x": P("targeted_room", ["a", "c", "e"])}, {"at_head": {"x": ["a", "c", "e"]}}),
    ("duty_seat_outsider_refused", "the moderator's acceptance shaped as an offer to z, an outsider at its head: a "
     "duty seats a member, never an outsider, so z is held to named_within and the row is refused (review r84)",
     [seat_row("o", "offer", "r1", ["z"], family=BALLOT)], {"o": REF("named_outside_audience")}),
    ("non_roster_row_names_outsider", "a row that seats no one names z, off the roster: still refused",
     [row("m", "partner_role:member", "community", room="r1", named=["z"])], {"m": REF("named_outside_audience")}),
    ("roster_families_placed", "group:roster and membership are placed at the room (stated at d5d42bf): an offer "
     "of each seats j, who is in its audience",
     [seat_row("g", "offer", "r1", ["j"], family="group:roster"), seat_row("m", "offer", "r1", ["j"])],
     {"g": P("targeted_room", ROOM + ["j"]), "m": P("targeted_room", ROOM + ["j"])}),
    ("seats_not_person_level", "an identity:occurrence row shaped as an offer over r1 to z: a person-level row "
     "seats no key into a room's audience, so z is held to named_within (review r83, case o)",
     [row("o", "identity:occurrence", "community", room="r1", named=["z"], kind="offer", obj="r1", to=["z"])],
     {"o": REF("named_outside_audience")}),
    ("seats_only_a_seat_family", "a chat row shaped as an offer over its room names j in `to`: chat is no seat "
     "family, so j is held to named_within and the row is refused (review r82, 5d)",
     [row("v", "chat:general", "community", room="r1", named=["j"], kind="offer", obj="r1", to=["j"])],
     {"v": REF("named_outside_audience")}),
    # history_on_join changes no audience (CC 4.4.3.16 as the Constitution corrected it): j, admitted to r3 by `adm`
    # after m, is SERVED m, sealed by keys it lacks: served is not readable. `full` acts only on a kept stream, the
    # caller's (history_of)
    ("history_from_join", "the record states nothing (from_join): j is served m, not keyed for it",
     [row("m", "chat:general", "community", room="r3")], {"m": P("targeted_room", ["a", "b", "j"])}, {"joined": {"r3": {"j": "adm"}}, "before": [["m", "adm"]]}),
    ("history_record_full", "the record states full: j is served m, and the room's tier still gives it no earlier "
     "key; full acts only on a kept stream",
     [row("m", "chat:general", "community", room="r3")], {"m": P("targeted_room", ["a", "b", "j"])}, {"joined": {"r3": {"j": "adm"}}, "before": [["m", "adm"]], "history": {"r3": "full"}}),
    ("history_record_from_join", "the record states from_join: j is served m, not keyed for it",
     [row("m", "chat:general", "community", room="r3")], {"m": P("targeted_room", ["a", "b", "j"])}, {"joined": {"r3": {"j": "adm"}}, "before": [["m", "adm"]], "history": {"r3": "from_join"}}),
    ("history_row_full", "the row states full, the record from_join: served alike; the row's own full is read only "
     "for a kept stream",
     [row("m", "chat:general", "community", room="r3", history="full")], {"m": P("targeted_room", ["a", "b", "j"])},
     {"joined": {"r3": {"j": "adm"}}, "before": [["m", "adm"]], "history": {"r3": "from_join"}}),
    ("history_join_concurrent", "j was admitted concurrently with m: served m",
     [row("m", "chat:general", "community", room="r3")], {"m": P("targeted_room", ["a", "b", "j"])}, {"joined": {"r3": {"j": "adm"}}, "before": []}),
    ("history_row_after_join", "m has j's admission in its past: served m",
     [row("m", "chat:general", "community", room="r3")], {"m": P("targeted_room", ["a", "b", "j"])},
     {"joined": {"r3": {"j": "adm"}}, "before": [["adm", "m"]]}),
    ("removed_later_owed_nothing", "c was removed from r2's roster after m: the roster as it stands does not list c, "
     "and c is owed nothing further",
     [row("m", "chat:general", "community", room="r2")], {"m": P("targeted_room", ["a", "e"])}),
    ("targeted_no_room", "a targeted row names its room",
     [row("m", "chat:general", "community")], {"m": REF("no_room")}),
    ("held_shut_family_placed", "preserve_request, Undecided before d5d42bf, is placed by its scope",
     [row("q", "preserve_request", "self")], {"q": P("self_collective", ["a", "a2"])}),
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
    # the copy rule (carried: the Constitution's proposal c). Carriage is of rows; served is not readable
    ("copy_same_room", "an addressed row of a, named by d's concluded row in r1: d is not its signer, so it is not "
     "carried (c.3) and stays with its addressees",
     [row("x", "census:member:share", "addressed", room="r1", named=["d"]),
      row("m", "chat:general", "community", signer="d", room="r1", names=["x"])],
     {"x": P("addressed", ["a", "d"]), "m": P("targeted_room", ["a", "b", "c", "d"])}),
    ("copy_signer_outside", "a's addressed row, named by a room row of a2 (a's person, so a carrier c.3 admits) that "
     "is not in the row's audience: the gate of CC 5.2, it carries nobody",
     [row("x", "census:member:share", "addressed", room="r1", named=["d"]),
      row("m", "chat:general", "community", signer="a2", room="r1", names=["x"])],
     {"x": P("addressed", ["a", "d"]), "m": P("targeted_room", ["a", "a2", "b", "c"])}),
    ("copy_author_carries", "the author's self row, named by its own concluded row in r1: carried to r1's roster",
     [row("s", "chat:general", "self"), row("m", "chat:general", "community", room="r1", names=["s"])],
     {"s": P("self_collective", ["a", "a2", "b", "c"]), "m": P("targeted_room", ROOM)}),
    ("copy_person_carries", "the self row named by a concluded room row of a2, a key of a's person: carried",
     [row("s", "chat:general", "self"), row("m", "chat:general", "community", signer="a2", room="r1", names=["s"])],
     {"s": P("self_collective", ["a", "a2", "b", "c"]), "m": P("targeted_room", ["a", "a2", "b", "c"])}),
    ("copy_evicted_device", "a3 was a device of a, evicted from a's key roster: person(a) is the current roster "
     "(a, a2), so a3's room row naming a's self row carries nothing",
     [row("s", "chat:general", "self"), row("m", "chat:general", "community", signer="a3", room="r1", names=["s"])],
     {"s": P("self_collective", ["a", "a2"]), "m": P("targeted_room", ["a", "a3", "b", "c"])}),
    ("copy_unconcluded", "a namer that does not conclude carries nobody",
     [row("s", "chat:general", "self"), row("m", "chat:general", "community", room="r1", names=["s"], concluded=False)],
     {"s": P("self_collective", ["a", "a2"]), "m": P("targeted_room", ROOM)}),
    ("copy_from_refused", "a refused namer carries nobody",
     [row("s", "chat:general", "self"), row("m", "chat:general", "community", room="r1", names=["s"], named=["z"])],
     {"s": P("self_collective", ["a", "a2"]), "m": REF("named_outside_audience")}),
    ("copy_chain", "a commons row by b names a's room row, which names a's self row: the self row reaches r1's "
     "roster by a's own row; the room row is carried only by a room row of its room, so b's commons row adds nothing",
     [row("s", "chat:general", "self"), row("m", "chat:general", "community", room="r1", names=["s"]),
      row("c", "chat:general", "federation", signer="b", room="r1", names=["m"])],
     {"s": P("self_collective", ["a", "a2", "b", "c"]), "m": P("targeted_room", ROOM), "c": P("commons", AU.EVERYONE)}),
    ("copy_not_off_roster", "a's room row in r2 names c (a member at its head, removed since) and a's self row: "
     "the self row reaches r2's current roster, not c (c.2: nothing reaches a key off the roster)",
     [row("s", "chat:general", "self"), row("m", "chat:general", "community", room="r2", named=["c"], names=["s"])],
     {"s": P("self_collective", ["a", "a2", "e"]), "m": P("targeted_room", ["a", "c", "e"])},
     {"at_head": {"m": ["a", "c", "e"]}}),
    ("key_grant_never_carried", "a key grant of a, at self, named by a's own room row: a key grant is never "
     "carried; it is served per its own placement (here a's keys and the key it names) and opened only by that key",
     [row("k", "key_grant:content", "self", named=["d"]),
      row("m", "chat:general", "community", room="r1", names=["k"])],
     {"k": P("self_collective", ["a", "a2", "d"]), "m": P("targeted_room", ROOM)}),
    # the joiner (review r79, leak.py): served the room's rows as they stand, sealed by keys it lacks
    ("copy_reply_from_join", "j joined r3 after m0 and m1; b's reply d names m1, which names m0: j is served all "
     "three, as a current member, and holds the older two as ciphertext",
     [row("m0", "chat:general", "community", room="r3"),
      row("m1", "chat:general", "community", signer="b", room="r3", names=["m0"]),
      row("d", "chat:general", "community", signer="b", room="r3", names=["m1"])],
     {"m0": P("targeted_room", ["a", "b", "j"]), "m1": P("targeted_room", ["a", "b", "j"]), "d": P("targeted_room", ["a", "b", "j"])},
     {"joined": {"r3": {"j": "adm"}}, "before": [["m0", "adm"], ["m1", "adm"], ["m0", "m1"], ["m0", "d"], ["m1", "d"],
                                                 ["adm", "d"]]}),
    ("copy_admission_from_join", "j's admission names m1, which names m0: j holds the rows its admission names",
     [row("m0", "chat:general", "community", room="r3"),
      row("m1", "chat:general", "community", signer="b", room="r3", names=["m0"]),
      dict(row("adm", "chat:general", "community", room="r3", named=["j"]), names=["m1"])],
     {"m0": P("targeted_room", ["a", "b", "j"]), "m1": P("targeted_room", ["a", "b", "j"]), "adm": P("targeted_room", ["a", "b", "j"])},
     {"joined": {"r3": {"j": "adm"}}, "before": [["m0", "adm"], ["m1", "adm"], ["m0", "m1"]]}),
    ("copy_removed_key", "the removal of c names its head g1: c gets the removal alone",
     [row("g0", "chat:general", "community", signer="e", room="r2"),
      row("g1", "chat:general", "community", room="r2", names=["g0"]),
      dict(seat_row("x", "unseat", "r2", ["c"], family=BALLOT), names=["g1"])],
     {"g0": P("targeted_room", ["a", "e"]), "g1": P("targeted_room", ["a", "e"]), "x": P("targeted_room", ["a", "c", "e"])},
     {"at_head": {"x": ["a", "c", "e"]}}),
    # review r79 (named.py): named_within is read at the row's own head
    ("named_at_own_head", "a names c while c sat in r2; c is removed later: the row stays placed (placement is "
     "monotone), and is owed the current roster and the key it names",
     [row("m", "chat:general", "community", room="r2", named=["c"])], {"m": P("targeted_room", ["a", "c", "e"])},
     {"at_head": {"m": ["a", "c", "e"]}}),
    ("named_outsider_joins_later", "a row naming j before j sat in r3 stays refused after j joins",
     [row("m", "chat:general", "community", room="r3", named=["j"])], {"m": REF("named_outside_audience")},
     {"at_head": {"m": ["a", "b"]}}),
]

# the seats of the ROSTER itself (membership, group:roster): placed once the Constitution states their cells; until
# then they answer Undecided and these cases wait (cases_now)
ROSTER_SEAT_FAMILY = "membership:{stage}"
ROSTER_SEAT_CASES = [
    ("admission_names_joiner", "a pending admission of j at the room names j, who is not on the roster yet: j is "
     "in its audience",
     [seat_row("v", "offer", "r1", ["j"], concluded=False)], {"v": P("targeted_room", ROOM + ["j"])}),
    ("seat_row_names_outsider", "the same admission also names z, a key it does not seat: refused",
     [dict(seat_row("v", "offer", "r1", ["j"]), named=["j", "z"])], {"v": REF("named_outside_audience")}),
    ("copy_unaccepted_outsider", "a concluded offer to z, never accepted, names its head h1: z gets the offer alone",
     [row("h0", "chat:general", "community", signer="c", room="r1"),
      row("h1", "chat:general", "community", signer="b", room="r1", names=["h0"]),
      dict(seat_row("o", "offer", "r1", ["z"]), names=["h1"])],
     {"h0": P("targeted_room", ROOM), "h1": P("targeted_room", ROOM), "o": P("targeted_room", ROOM + ["z"])}),
]

# seats_of over each kind of row: (row, the keys it seats). It reads no placement, so it runs at every pin
SEATS = [
    (seat_row("v", "offer", "r1", ["j"]), ["j"]),
    (seat_row("x", "unseat", "r1", ["c"], family="group:roster"), ["c"]),
    (seat_row("b", "offer", "r1", ["j"], family=BALLOT), ["j"]),
    (row("v", "membership:invite", "community", room="r1", named=["j"], kind="offer", obj="r9", to=["j"]), []),
    (row("v", "chat:general", "community", room="r1", named=["j"], kind="offer", obj="r1", to=["j"]), []),
    (row("v", "identity:occurrence", "community", room="r1", named=["j"], kind="offer", obj="r1", to=["j"]), []),
    (row("v", "membership:invite", "community", room="r1", named=["j"]), []),
]


def check_seats():
    problems = []
    for r, want in SEATS:
        got = sorted(AU.seats_of(r))
        if got != want:
            problems.append("seats: %s %s %s gives %s, want %s" % (r["family"], r.get("kind"), r.get("obj"), got, want))
    return problems


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
PLANTS = [(("undecided_defaulted",), "undecided"), (("pinned_unread",), "pinned_self"),
          (("named_within_unread",), "named_outside_audience"),
          (("copy_any_carrier",), "copy_same_room"), (("copy_any_signer",), "copy_signer_outside"),
          (("copy_unconcluded",), "copy_unconcluded"), (("copy_off_roster",), "copy_not_off_roster"),
          (("key_grant_carried",), "key_grant_never_carried"),
          (("match_first",), "table"), (("seats_not_within",), "admission_names_joiner"),
          (("seats_any_obj",), "seats"), (("duty_seats_outsider",), "duty_seat_outsider_refused"),
          (("seats_any_family",), "seats_only_a_seat_family"),
          (("seats_person_level",), "seats_not_person_level"),
          (("named_within_current",), "named_at_own_head"),
          (("history_unread",), "history"), (("word_read",), "history"),
          (("tie_first",), "ties"), (("follows_unread",), "follow"), (("narrower_by_keys",), "follow"),
          (("follows_any_ref",), "custody_by_cites_is_not_named"),
          (("cites_any_family",), "duty_cites_its_permission_and_more")]


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
    if set(AU.CITES_CLASS) != {f for f, r in AU.FOLLOWS_REF.items() if r == "cites"} or \
            not all(any(c == k for c in AU.CITED_AS.values()) for k in AU.CITES_CLASS.values()):
        problems.append("derivation: a cites class has no family in the table")
    if set(AU.FOLLOWS) != set(AU.FOLLOWS_REF):
        problems.append("derivation: the follows families %s have references %s" % (sorted(AU.FOLLOWS), sorted(AU.FOLLOWS_REF)))
    if AU.KEY_GRANT not in AU.FAMILIES:
        problems.append("derivation: the key grant family %s is not in the table" % AU.KEY_GRANT)
    if AU.SEAT_FAMILIES != {"ballot:moderator_acceptance", "group:roster", "membership:{stage}"}:
        problems.append("derivation: the seat families are %s" % sorted(AU.SEAT_FAMILIES))
    if FP.ties(list(AU.FAMILIES)):
        problems.append("derivation: the pinned table ties: %s" % FP.ties(list(AU.FAMILIES))[:3])
    return problems


# follow, the rule of a `follows` family, over answers stated directly (it reads no table, so it runs at every pin):
# (does the row name the row it follows, the row's own answer, the followed row's answer or None, rule, the result)
RM = ("placed", "targeted_room", frozenset("abc"))
FOLLOW = [
    (True, RM, RM, "same", RM),
    (True, RM, ("placed", "targeted_family", frozenset("abc")), "same", ("refused", "follows_mismatch")),
    (True, RM, ("placed", "targeted_room", frozenset("ae")), "same", ("refused", "follows_mismatch")),
    (True, ("placed", "self_collective", frozenset({"a", "a2"})), ("placed", "targeted_room", frozenset({"a", "a2", "b", "c"})),
     "narrower", ("placed", "self_collective", frozenset({"a", "a2"}))),
    (True, ("placed", "commons", AU.EVERYONE), RM, "narrower", ("refused", "follows_wider")),
    (True, RM, ("placed", "commons", AU.EVERYONE), "narrower", RM),
    (True, RM, ("refused", "named_outside_audience"), "same", ("refused", "follows_unplaced")),
    (True, RM, None, "same", ("refused", "follows_not_held")),
    # narrower is over persons: a's device a2 is off r1's roster, and a is on it, so a duty at self is within
    (True, ("placed", "self_collective", frozenset({"a", "a2"})), RM, "narrower",
     ("placed", "self_collective", frozenset({"a", "a2"}))),
    (True, ("placed", "self_collective", frozenset({"d"})), RM, "narrower", ("refused", "follows_wider")),
    (False, RM, RM, "same", ("refused", "follows_not_named")),
    (True, ("refused", "no_room"), RM, "same", ("refused", "no_room")),
]


def check_follow():
    problems = []
    for named, own, fol, rule, want in FOLLOW:
        r = row("f", "custody:blob", "community", room="r1")
        if named:
            r["evidence"] = "t"
        got = AU.follow(r, own, fol, rule, person)
        if got != want:
            problems.append("follow: %s %s against %s gives %s, want %s" % (rule, own, fol, got, want))
    return problems


# a follows family placed at the scope of the row it follows (the next table states custody, duty and stream:head
# with `follows`): these run once the pinned table carries the marker
FOLLOWS_CASES = [
    ("custody_follows_its_content", "a custody row of a blob in r1 follows the blob's own scope: placed with it",
     [row("b", "file:blob", "community", room="r1"),
      dict(row("c", "custody:blob", "community", room="r1", names=["b"]), evidence="b")],
     {"b": P("targeted_room", ROOM), "c": P("targeted_room", ROOM)}),
    ("custody_wider_than_its_content", "a custody row at the commons of a blob placed in r1: refused",
     [row("b", "file:blob", "community", room="r1"),
      dict(row("c", "custody:blob", "federation", names=["b"]), evidence="b")],
     {"b": P("targeted_room", ROOM), "c": REF("follows_mismatch")}),
    ("duty_within_its_permission", "a duty at the family r1 on a permission placed in room r1: its audience is "
     "within the permission's, placed",
     [row("p", "consent:scope:read", "community", room="r1"),
      dict(row("d", "duty:keep", "family", room="r1", names=["p"]), cites=["p"])],
     {"p": P("targeted_room", ROOM), "d": P("targeted_family", ROOM)}),
    ("duty_at_self_within_its_permission", "a duty at self on a permission in r1, by a, whose device a2 is off r1's "
     "roster: narrower is over persons, and a is on the roster, so it is within (the ruling)",
     [row("p", "consent:scope:read", "community", room="r1"),
      dict(row("d", "duty:keep", "self", names=["p"]), cites=["p"])],
     {"p": P("targeted_room", ROOM), "d": P("self_collective", ["a", "a2"])}),
    ("duty_at_self_of_an_outsider", "a duty at self by d, a person off r1's roster, on a permission in r1: refused",
     [row("p", "consent:scope:read", "community", room="r1"),
      dict(row("d", "duty:keep", "self", signer="d", names=["p"]), cites=["p"])],
     {"p": P("targeted_room", ROOM), "d": REF("follows_wider")}),
    ("duty_wider_than_its_permission", "a duty at the commons on a permission placed in r1: refused",
     [row("p", "consent:scope:read", "community", room="r1"),
      dict(row("d", "duty:keep", "federation", names=["p"]), cites=["p"])],
     {"p": P("targeted_room", ROOM), "d": REF("follows_wider")}),
    # G34: each family names the row it follows by its own reference
    ("stream_head_follows_its_stream", "a stream head follows the stream it heads, by its sub",
     [row("st", "chat:general", "community", room="r1"),
      dict(row("h", "stream:head", "community", room="r1", names=["st"]), stream="st")],
     {"st": P("targeted_room", ROOM), "h": P("targeted_room", ROOM)}),
    ("ownership_cites_a_permission", "an ownership row cites a permission, not an owner binding: no cited row of "
     "the right family, refused",
     [row("ob", "consent:scope:own", "community", room="r1"),
      dict(row("o", "ownership:owner:key:v1", "community", room="r1", names=["ob"]), cites=["ob"])],
     {"ob": P("targeted_room", ROOM), "o": REF("follows_not_named")}),
    ("duty_cites_its_permission_and_more", "a duty cites its permission and an evidence row: the cited row of the "
     "right family is the followed row, the other is not read: placed",
     [row("p", "consent:scope:read", "community", room="r1"), row("ev", "chat:general", "community", room="r1"),
      dict(row("d", "duty:keep", "family", room="r1", names=["p", "ev"]), cites=["p", "ev"])],
     {"p": P("targeted_room", ROOM), "ev": P("targeted_room", ROOM), "d": P("targeted_family", ROOM)}),
    ("custody_by_cites_is_not_named", "a custody row names its content by evidence_refs; a cite of the blob row is "
     "not its reference: refused",
     [row("b", "file:blob", "community", room="r1"),
      dict(row("c", "custody:blob", "community", room="r1", names=["b"]), cites=["b"])],
     {"b": P("targeted_room", ROOM), "c": REF("follows_not_named")}),
    ("duty_citing_two_rows", "a duty that cites two rows names no one permission: refused",
     [row("p", "consent:scope:read", "community", room="r1"), row("p2", "consent:scope:write", "community", room="r1"),
      dict(row("d", "duty:keep", "family", room="r1", names=["p", "p2"]), cites=["p", "p2"])],
     {"p": P("targeted_room", ROOM), "p2": P("targeted_room", ROOM), "d": REF("follows_ambiguous")}),
    ("stream_head_names_no_stream", "a stream head that names no stream it heads: refused",
     [row("h", "stream:head", "community", room="r1")], {"h": REF("follows_not_named")}),
]


# the Undecided path, over a synthetic table (the pinned one has no undecided family since d5d42bf): (row family,
# scope, the answer)
SYNTH = {"test:open": {"family": "test:open", "allowed": None, "undecided": "gap: no placement"},
         "test:open:{kind}": {"family": "test:open:{kind}", "allowed": None, "undecided": "gap: no placement"},
         "test:placed": {"family": "test:placed", "allowed": ["self_collective"], "undecided": None}}
UNDECIDED = [("test:open", "community", UND("test:open")), ("test:open:x", "self", UND("test:open:{kind}")),
             ("test:placed", "self", P("self_collective", ["a", "a2"])), ("test:none", "self", REF("family_unknown"))]


def check_undecided():
    problems = []
    for fam, scope, want in UNDECIDED:
        got = enc(AU.place(row("u", fam, scope, room="r1" if scope == "community" else None), roster, person,
                           AU.NO_JOINS, SYNTH))
        if got != want:
            problems.append("undecided: %s at %s gives %s, want %s" % (fam, scope, got, want))
    return problems


# history_of: the word a caller reads for a kept stream (it changes no audience). (row's word, record's word, answer)
HISTORY = [(None, None, "from_join"), ("full", None, "full"), (None, "full", "full"), ("from_join", "full", "from_join"),
           ("always", "full", "full"), ("always", None, "from_join"), (None, "sometimes", "from_join")]


def check_history():
    problems = []
    for rw, rec, want in HISTORY:
        r = row("m", "chat:general", "community", room="r3", history=rw)
        got = AU.history_of(r, dict(AU.NO_JOINS, history=lambda room: rec))
        if got != want:
            problems.append("history: row %s, record %s gives %s, want %s" % (rw, rec, got, want))
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
    """The case table, with the regard cases once the pinned table holds that family, the roster seat cases once
    its cell is stated, and the follows cases once the table carries the marker."""
    roster_seats = AU.FAMILIES.get(ROSTER_SEAT_FAMILY, {}).get("undecided") is None and ROSTER_SEAT_FAMILY in AU.FAMILIES
    follows = "custody:{kind}" in AU.FOLLOWS
    return CASES + (REGARD_CASES if REGARD in AU.FAMILIES else []) + (ROSTER_SEAT_CASES if roster_seats else []) \
        + (FOLLOWS_CASES if follows else [])


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
            "history": [{"row": rw, "record": rec, "answer": a} for rw, rec, a in HISTORY],
            "seats": [{"row": r, "seats": w} for r, w in SEATS],
            "undecided": {"families": [[f, c["undecided"]] for f, c in SYNTH.items()],
                          "cases": [{"family": f, "scope": sc, "answer": w} for f, sc, w in UNDECIDED]},
            "follow": [{"named": n, "own": enc(o), "followed": enc(f) if f else None, "rule": ru, "answer": enc(w)}
                       for n, o, f, ru, w in FOLLOW],
            "generated": [{"family": p, "name": n, "scope": s, "room": r, "answer": a} for p, n, s, r, a in generated()],
            "cases": [{"name": n, "about": ab, "rows": rows, "joins": w[0] if w else {},
                       "answers": {i: enc(a) for i, a in
                                   AU.audiences(rows, roster, person, joins_of(w[0] if w else None)).items()}}
                      for n, ab, rows, _, *w in cases_now()]}


def main():
    problems = check_table() + check_cases() + check_derivation() + check_ties() + check_history() + check_seats() + check_follow() + check_undecided()
    if REGARD not in AU.FAMILIES:
        print("  %s is not in the pinned table yet: its %d cases wait for the re-pin" % (REGARD, len(REGARD_CASES)))
    caught = 0
    present = {c[0] for c in cases_now()} | {"table", "ties", "history", "seats", "follow", "undecided"}
    waiting = 0
    for muts, where in PLANTS:
        mut = "+".join(muts)
        if where not in present:
            waiting += 1
            print("  plant %-20s waits: its case %s runs once its family is stated" % (mut, where))
            continue
        AU.MUT.clear(); AU.MUT.update(muts)
        try:
            got = check_table() + check_cases() + check_ties() + check_history() + check_seats() + check_follow() + check_undecided()
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
          "%d cases; %d of %d planted breaks caught (%d wait)"
          % ("ok" if not problems else "%d problems" % len(problems), s["families"], s["on_the_default"],
             s["pinned_by_the_table"], s["undecided"], s["branch"], s["commit"][:7],
             ", provisional" if s.get("provisional") else "", len(generated()), len(cases_now()), caught, len(PLANTS) - waiting, waiting))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
