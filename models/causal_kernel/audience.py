"""
audience.py: where a row is placed and who it is for, family by family (CC 3.4.5.1, CC 5.2), from the family
model's placement cells (data/family_placement.json, derived from the Constitution's manifests/family_model.json by
tools/family_placement.py). A reference: for a row, the placement it takes, and its audience as KEYS; or the
refusal; or Undecided, naming the family, where the family's cell is not table data. Mapping keys to nodes (the
claimed nodes of a key, CC 5.2's "nodes") is the store's.

The rules.
1. FAMILY. A row's family is matched against the family patterns of the table: a segment `{name}` matches one
   segment, a final `*` one or more. The pattern with the most literal segments that matches decides (an exact
   name beats `accord:*`). Two patterns that tie on a name decide nothing: refused, `family_ambiguous`
   (tools/family_placement.py refuses to write a table with a tie, and the pinned one has none). A family no
   pattern matches is refused: `family_unknown`.
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
       targeted_family,  the room's roster as it stands (Seats.roster over the rows held: the current members, the
                         ruling of CC 5.2: a member removed later is owed nothing further), less the members
                         admitted after the row unless its history_on_join is `full` (the row's own, else the
                         room record's, else `from_join`; CC 2.1, CC 4.4.3.16), and the keys the
       targeted_room     row names; a row there may name only keys within its audience (CC 5.2: "A row placed at
                         family, community or affiliations may name only keys within its audience"), read
                         against the members AT THE ROW'S OWN HEAD, so a row's placement never changes with a
                         later removal or admission: one naming a key that was off the roster there is refused,
                         `named_outside_audience`, and stays refused after that key joins. The current roster is
                         read only for who is OWED. The keys a seat offer or unseat over the room seats or
                         removes (seats_of: derived from the row, its `to` where its `obj` is its room; no
                         caller states them) are always within its audience, ahead of that rule: a pending
                         admission names its joiner, a removal its removed key. A targeted row names its room,
                         or it is refused, `no_room`. An unknown history_on_join word is absent: it falls
                         through to the record, then the default (the door refuses it)
       commons           everyone
       addressed         the keys it names, and its signer
4. COPY (CC 5.2: "A row carries its audience to the rows it names, when it is concluded, sits in the same room as
   the row it names, and its signer is already in that row's audience"; route.py's `closed`, Carry.lean). A row's
   audience includes that of every concluded row that names it, sits in the same room or is signed by the same
   key, and whose signer is already in its audience: the least fixed point, which only grows. A row refused or
   undecided carries nothing and receives nothing. THE PRECEDENCE (review r79; copy_bound, the one place it is
   stated): the copy rule never adds a key that the named row's own place() withholds. A key it adds must be owed
   that row under its own placement, history_on_join and the current roster, or be its own named or seat keys.
   So the copy rule adds no key here; and a joiner under from_join can receive a reply whose parent it is not
   owed.

Rows: `id`, `family`, `scope` (a cohort scope word, or "addressed"), `room` (the room or family a targeted row is
in; None elsewhere), `signer`, `named` (the keys it names: attested, subjects, for_key_id), `seats` (on a seat offer or unseat over the
room: the keys it seats or removes, among `named`), `names` (the rows it
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


AMBIGUOUS = "ambiguous"
HISTORY = ("full", "from_join")


def family_of(name, families=None):
    """The pattern that decides a family name: the most literal segments among those that match; AMBIGUOUS where
    two patterns tie (refused, `family_ambiguous`); None where none matches. MUTATIONS match_first: the first
    matching pattern in table order; tie_first: the first of a tie."""
    fams = FAMILIES if families is None else families
    hits = [(_match(p, name), p) for p in fams]
    hits = [(k, p) for k, p in hits if k is not None]
    if not hits:
        return None
    if "match_first" in MUT:
        return hits[0][1]
    best = max(k for k, _ in hits)
    top = [p for k, p in hits if k == best]
    return top[0] if len(top) == 1 or "tie_first" in MUT else AMBIGUOUS


# the caller's view of the room: `joined(room, key)`, the row that admitted the key (None for a founding member);
# `history(room)`, the history_on_join the room's record states (None where it states none); `past(a, b)`, row a
# is in row b's past; `at_head(room, row)`, the members of the room at the row's own head (seat.members_at). A
# targeted row naming a key needs it: there is no fallback to the current roster, which would make placement change
# with a later removal
NO_JOINS = {"joined": lambda room, k: None, "history": lambda room: None, "past": lambda a, b: False,
            "at_head": lambda room, row: None}


def _word(v):
    """A history_on_join word, or None: an unknown word is read as absent (the door refuses it). MUTATION
    word_read: an unknown word is read as stated."""
    return v if v in HISTORY or (v is not None and "word_read" in MUT) else None


def history_of(row, joins):
    """The row's history_on_join (CC 2.1: set per stream by its producer, an envelope member), else the one its
    room's record states, else the default `from_join` (signed_object.cddl). An unknown word is absent and falls
    through. MUTATION history_unread: always full."""
    if "history_unread" in MUT:
        return "full"
    return _word(row.get("history_on_join")) or _word(joins["history"](row.get("room"))) or "from_join"


def seats_of(row):
    """The keys a seat offer or unseat over the row's own room seats or removes (its `to`), derived from the row:
    no caller states them. Empty on every other row. MUTATION seats_any_obj: a seat row over another object too."""
    if row.get("kind") not in ("offer", "unseat"):
        return frozenset()
    if row.get("obj") != row.get("room") and "seats_any_obj" not in MUT:
        return frozenset()
    return frozenset(row.get("to", ()))


def place(row, roster, person, joins=NO_JOINS):
    """("placed", placement, audience) | ("refused", token) | ("undecided", family pattern) for one row, before
    the copy rule. An audience is a frozenset of keys or EVERYONE. `joins` is the caller's view of the room
    (NO_JOINS)."""
    fam = family_of(row["family"])
    if fam is None:
        return ("refused", "family_unknown")
    if fam == AMBIGUOUS:
        return ("refused", "family_ambiguous")
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
    # WHO IS OWED: the current roster (Seats.roster over the rows held), CC 5.2 as ruled: a row is owed to the
    # roster as it stands when the node replicates; a member removed since is owed nothing further. A member
    # admitted after the row (its admission has the row in its past) is owed it only where the history is `full`
    # (CC 2.1, CC 4.4.3.16); one admitted concurrently with the row is owed it
    members = frozenset(roster(row["room"]))
    joined = joins["joined"]
    owed = members if history_of(row, joins) == "full" else frozenset(
        k for k in members if joined(row["room"], k) is None or not joins["past"](row["id"], joined(row["room"], k)))
    # WHAT IT MAY NAME: the members at the row's own head (named_within, CC 5.2), so a row's placement never
    # changes with a later removal or admission. MUTATION named_within_current: read against the current roster
    at = joins["at_head"](row["room"], row["id"])
    if at is None and named - seats_of(row):
        raise ValueError("audience: the members at %s's own head are the caller's (joins['at_head'])" % row["id"])
    within = members if "named_within_current" in MUT else frozenset(at or ())
    # the keys a seat offer or unseat over the room seats or removes are within its audience, ahead of named_within
    seated = seats_of(row) if "seats_not_within" not in MUT else frozenset()
    if "named_within_unread" not in MUT and not (named - seated) <= within:
        return ("refused", "named_outside_audience")
    return ("placed", placement, owed | me | named | seats_of(row))


def _union(a, b):
    return EVERYONE if EVERYONE in (a, b) else a | b


def _within(k, a):
    return a == EVERYONE or k in a


def _meet(a, b):
    if a == EVERYONE:
        return b
    if b == EVERYONE:
        return a
    return a & b


def copy_bound(placed):
    """The keys the copy rule may add to a placed row: the keys its own place() owes it (its placement,
    history_on_join and the current roster, its named and seats keys). The one place the precedence is stated:
    the copy rule never adds a key that the row's own placement withholds. MUTATION copy_unbounded."""
    return EVERYONE if "copy_unbounded" in MUT else placed[2]


def audiences(rows, roster, person, joins=NO_JOINS):
    """{row id: its answer}, the copy rule applied: a placed row's audience grows by that of every concluded placed
    row naming it from the same room, or signed by the same key, whose signer is already in its audience, bounded
    by copy_bound."""
    out = {r["id"]: place(r, roster, person, joins) for r in rows}
    bound = {i: copy_bound(a) for i, a in out.items() if a[0] == "placed"}
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
                grown = _union(out[i][2], _meet(ad[2], bound[i]))
                if grown != out[i][2]:
                    out[i] = ("placed", out[i][1], grown); changed = True
    return out


def instance(pattern):
    """A family name the pattern matches, for the generated cases: each placeholder and a final `*` filled."""
    return ":".join("x" if s.startswith("{") or s == "*" else s for s in pattern.split(":"))
