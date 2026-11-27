"""
audience.py: where a row is placed and who it is for, family by family (CC 3.4.5.1, CC 5.2), from the family
model's placement cells (data/family_placement.json, derived from the Constitution's manifests/family_model.json by
tools/family_placement.py). A reference: for a row, the placement it takes, and its audience as KEYS; or the
refusal; or Undecided, naming the family, where the family's cell is not table data. Mapping keys to nodes (the
claimed nodes of a key, CC 5.2's "nodes") is the store's.

The rules.
1. FAMILY. A row's family is matched against the family patterns of the table: a segment `{name}` matches one
   segment, a final `*` one or more. The pattern with the most literal segments that matches decides (an exact
   name beats `accord:*`); the table has no two patterns that tie on a name (tools/family_placement.py and
   check_audience.py check it). A family no pattern matches is refused: `family_unknown`.
2. PLACEMENT. A row states its cohort scope; the placement is a function of it (the table's `scopes`): self ->
   self_collective; family -> targeted_family; community, affiliations -> targeted_room; species, biosphere,
   federation -> commons; and `addressed`, a row for the keys it names. A family on the default takes any of the
   first four, chosen by the emitter for each row (CC 3.4.5.1: "Scope is per-row; a family is not scope-pinned").
   A family the CC table pins takes only the placements its cell names: any other is refused,
   `placement_not_allowed`. A family whose cell is not table data (a code, prose or gap source) answers
   Undecided naming the family: no default is taken for it.
3. AUDIENCE, as keys. Every audience holds the row's signer and the keys the row names (CC 5.2, reach: "A row
   that names a node ... is always served to that node"):
       self_collective   the signer's own keys (the person's)
       targeted_family,  the room's roster (Seats.roster over the rows held: the current members) and the keys the
       targeted_room     row names; a row there may name only keys within its audience (CC 5.2: "A row placed at
                         family, community or affiliations may name only keys within its audience"): one naming a
                         key off the roster is refused, `named_outside_audience`. A targeted row names its room, or
                         it is refused, `no_room`
       commons           everyone
       addressed         the keys it names, and its signer
4. COPY (CC 5.2: "A row carries its audience to the rows it names, when it is concluded, sits in the same room as
   the row it names, and its signer is already in that row's audience"; route.py's `closed`, Carry.lean). A row's
   audience includes that of every concluded row that names it, sits in the same room or is signed by the same
   key, and whose signer is already in its audience: the least fixed point, which only grows. A row refused or
   undecided carries nothing and receives nothing.

Rows: `id`, `family`, `scope` (a cohort scope word, or "addressed"), `room` (the room or family a targeted row is
in; None elsewhere), `signer`, `named` (the keys it names: attested, subjects, for_key_id), `names` (the rows it
names), `concluded` (bool). `roster(room)` and `person(key)` are the caller's: the room's roster as Seats.roster
reads it, and the keys of the signer's person.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TABLE = json.load(open(os.path.join(ROOT, "data", "family_placement.json"), encoding="utf-8"))
PLACEMENTS = tuple(TABLE["placements"])
SCOPE_PLACEMENT = {}
for _s in TABLE["scopes"]:
    for _c in _s["cohort_scope"]:
        SCOPE_PLACEMENT[_c] = _s["placement"]
SCOPE_PLACEMENT["addressed"] = "addressed"
FAMILIES = {f["family"]: f for f in TABLE["families"]}
EVERYONE = "everyone"
TARGETED = ("targeted_family", "targeted_room")
MUT = set()            # planted breaks, switched on by check_audience.py


def _match(pattern, name):
    """The number of literal segments by which `pattern` matches `name`, or None."""
    p, n = pattern.split(":"), name.split(":")
    if p[-1] == "*":
        if len(n) < len(p):
            return None
        p, n = p[:-1], n[:len(p) - 1]
    elif len(p) != len(n):
        return None
    lit = 0
    for a, b in zip(p, n):
        if a.startswith("{") and a.endswith("}"):
            continue
        if a != b:
            return None
        lit += 1
    return lit


def family_of(name):
    """The pattern that decides a family name: the most literal segments among those that match. MUTATION
    match_first: the first matching pattern in table order."""
    hits = [(_match(p, name), p) for p in FAMILIES]
    hits = [(k, p) for k, p in hits if k is not None]
    if not hits:
        return None
    if "match_first" in MUT:
        return hits[0][1]
    best = max(k for k, _ in hits)
    top = [p for k, p in hits if k == best]
    assert len(top) == 1, (name, top)
    return top[0]


def place(row, roster, person):
    """("placed", placement, audience) | ("refused", token) | ("undecided", family pattern) for one row, before
    the copy rule. An audience is a frozenset of keys or EVERYONE."""
    fam = family_of(row["family"])
    if fam is None:
        return ("refused", "family_unknown")
    cell = FAMILIES[fam]
    placement = SCOPE_PLACEMENT.get(row["scope"])
    if placement is None:
        return ("refused", "scope_unknown")
    if cell["undecided"] is not None:
        if "undecided_defaulted" not in MUT:
            return ("undecided", fam)
        allowed = list(PLACEMENTS[:4])                 # MUTATION: a silent default
    else:
        allowed = cell["allowed"] if "pinned_unread" not in MUT else list(PLACEMENTS[:4])
    if placement not in allowed:
        return ("refused", "placement_not_allowed")
    named = frozenset(row.get("named", ()))
    me = frozenset({row["signer"]})
    if placement == "commons":
        return ("placed", placement, EVERYONE)
    if placement == "self_collective":
        return ("placed", placement, me | frozenset(person(row["signer"])) | named)
    if placement == "addressed":
        return ("placed", placement, me | named)
    if row.get("room") is None:
        return ("refused", "no_room")
    members = frozenset(roster(row["room"]))
    if "named_within_unread" not in MUT and not named <= members:
        return ("refused", "named_outside_audience")
    return ("placed", placement, members | me | named)


def _union(a, b):
    return EVERYONE if EVERYONE in (a, b) else a | b


def _within(k, a):
    return a == EVERYONE or k in a


def audiences(rows, roster, person):
    """{row id: its answer}, the copy rule applied: a placed row's audience grows by that of every concluded placed
    row naming it from the same room, or signed by the same key, whose signer is already in its audience."""
    out = {r["id"]: place(r, roster, person) for r in rows}
    by = {r["id"]: r for r in rows}
    namers = {i: [] for i in by}
    for d in rows:
        for n in d.get("names", ()):
            if n in namers:
                namers[n].append(d)
    changed = True
    while changed:
        changed = False
        for i, a in out.items():
            if a[0] != "placed":
                continue
            r = by[i]
            for d in namers[i]:
                ad = out[d["id"]]
                if ad[0] != "placed":
                    continue
                if not d.get("concluded") and "copy_unconcluded" not in MUT:
                    continue
                same_room = d.get("room") is not None and d.get("room") == r.get("room")
                if not (same_room or d["signer"] == r["signer"]) and "copy_cross_room" not in MUT:
                    continue                    # a row leaves its room only by its own signer's act
                if not _within(d["signer"], out[i][2]) and "copy_any_signer" not in MUT:
                    continue                    # a key outside the named row's audience carries nobody
                grown = _union(out[i][2], ad[2])
                if grown != out[i][2]:
                    out[i] = ("placed", out[i][1], grown); changed = True
    return out


def instance(pattern):
    """A family name the pattern matches, for the generated cases: each placeholder and a final `*` filled."""
    return ":".join("x" if s.startswith("{") or s == "*" else s for s in pattern.split(":"))
