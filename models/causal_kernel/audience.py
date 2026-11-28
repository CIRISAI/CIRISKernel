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
3. AUDIENCE, as keys: who may be SERVED the row. Served is not readable: a room row's content is sealed under the
   room's epoch keys, and the tier gives a joiner the current epoch's key only (CC 4.4.3.16); key wraps are the
   wrap set's (Seats.roster), not this. Every audience holds the row's signer and the keys the row names (CC 5.2,
   reach: "A row that names a node ... is always served to that node"):
       self_collective   the signer's own keys (the person's)
       targeted_family,  the room's roster as it stands (Seats.roster over the rows held: the current members, the
                         ruling of CC 5.2: a member removed later is owed nothing further), and the keys the row
       targeted_room     names. history_on_join changes no audience: a later joiner is served the older room rows,
                         sealed by keys it lacks; `full` acts only on a kept stream, through its producer's own
                         key grants within the catch-up bound (CC 5.1), the caller's (history_of reads the word;
                         an unknown word is absent and falls through, and the door refuses it). A row there may
                         name only keys within its audience (CC 5.2: "A row placed at family, community or
                         affiliations may name only keys within its audience"), read against the members AT THE
                         ROW'S OWN HEAD, so its placement never changes with a later removal or admission: one
                         naming a key that was off the roster there is refused, `named_outside_audience`, and stays
                         refused after that key joins. The keys a seat offer or unseat over the room seats or
                         removes (seats_of: derived from the row, its `to` where its `obj` is its room) are always
                         within its audience, ahead of that rule. A targeted row names its room, or it is refused,
                         `no_room`
       commons           everyone
       addressed         the keys it names, and its signer
4. COPY (CC 5.2: "a joiner holds the rows its own admission names, and a reply carries the row it answers to a
   later joiner"; a row waits for what it names, CC 2.7.3). Carriage is of rows (`carried`, the one place it is
   stated; the Constitution's proposal c): a room row is carried by a concluded room row of the same room, to that
   row's audience on the room's current roster; nothing reaches a key off the roster (an offered key that never
   accepted gets the offer alone, a removed key its removal alone); a self or addressed row is carried only by a
   concluded row of its own signer or that signer's person; the carrier's signer is already in the row's audience;
   a key grant is never carried (CC 3.3.2): it is served per its placement, which is the content's scope, so it is
   purged, taken down and replicated with the content, and only the key it names can open it; in a room the
   members see that a grant exists and to which key, never the key. The least fixed point, which only grows. A
   row refused or undecided carries nothing and receives nothing. The consequence: a joiner may hold the room's
   whole named reply chain, as ciphertext it cannot read.

Rows: `id`, `family`, `scope` (a cohort scope word, or "addressed"), `room` (the room or family a targeted row is
in; None elsewhere), `signer`, `named` (the keys it names: attested, subjects, for_key_id), `kind`, `obj`, `to` (on
a seat offer or unseat), `names` (the rows it names), `concluded` (bool), `history_on_join`. `roster(room)` and
`person(key)` are the caller's: the room's roster as Seats.roster reads it, and the keys of the signer's person.
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
SEAT_FAMILIES = frozenset(f["family"] for f in TABLE["families"] if f.get("seat"))
FOLLOWS = {f["family"]: f["follows"] for f in TABLE["families"] if f.get("follows")}
# the reference by which a row of a follows family names the row it follows (the ruling G34): the role its family
# already uses for that row, where one exists (a custody report's evidence_refs, the content's address; a stream
# head's sub, the stream it heads), else refs.also.cites (an ownership row cites the binding it mirrors, a duty the
# permission it attaches to). The caller resolves a reference to the row id
FOLLOWS_REF = {"custody:{kind}": "evidence", "stream:head": "stream",
               "ownership:{relation}:{target_kind}:{version}": "cites", "duty:{kind}": "cites"}


def followed_of(r):
    """The row a row of a follows family follows, by its family's reference (FOLLOWS_REF): (id or None, why).
    `cites` must name exactly one row; none or several name none. MUTATION follows_any_ref: any of the references."""
    role = FOLLOWS_REF.get(family_of(r["family"]))
    if "follows_any_ref" in MUT:
        for k in ("evidence", "stream"):
            if r.get(k):
                return r[k], None
        c = r.get("cites") or []
        return (c[0], None) if c else (None, "follows_not_named")
    if role == "cites":
        c = r.get("cites") or []
        if len(c) > 1:
            return None, "follows_ambiguous"
        return (c[0], None) if c else (None, "follows_not_named")
    return (r.get(role), None) if r.get(role) else (None, "follows_not_named")
DUTY_SEAT_FAMILIES = frozenset(f["family"] for f in TABLE["families"] if f.get("seat") == "duty")
KEY_GRANT = "key_grant:{axis}"            # the key grant family's pattern, read as the resolved family
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


# the caller's view of the room: `history(room)`, the history_on_join the room's record states (None where it states
# none; read by history_of for a kept stream, never for an audience); `at_head(room, row)`, the members of the room
# at the row's own head (seat.members_at). `joined` and `past` are no longer read (history changes no audience). A
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
    through. It changes no audience here: who is served is the roster as it stands. It is what a caller reads for
    a KEPT STREAM, where `full` lets the producer's own key grants reach a late joiner within the catch-up bound
    (CC 5.1; the caller's). MUTATION history_unread: always full."""
    if "history_unread" in MUT:
        return "full"
    return _word(row.get("history_on_join")) or _word(joins["history"](row.get("room"))) or "from_join"


def seats_of(row):
    """The keys a seat offer or unseat over the row's own room seats or removes (its `to`), derived from the row:
    no caller states them. Only a row of a ROOM SEAT FAMILY (one whose seats a room's body confers: group:roster,
    membership, the moderator's acceptance) seats anyone: a chat row cannot use `to` to pass named_within, and a
    person-level row (identity:occurrence, self:delegates_to) never seats keys into a room's audience. Empty on
    every other row. MUTATIONS seats_any_obj: a seat row over another object too; seats_any_family: a row of any
    family; seats_person_level: the person-level families too."""
    if row.get("kind") not in ("offer", "unseat"):
        return frozenset()
    fam = family_of(row["family"])
    person_level = ("identity:occurrence", "identity:occurrence_revocation", "self:delegates_to")
    if fam not in SEAT_FAMILIES and "seats_any_family" not in MUT and not (
            "seats_person_level" in MUT and fam in person_level):
        return frozenset()
    if row.get("obj") != row.get("room") and "seats_any_obj" not in MUT:
        return frozenset()
    return frozenset(row.get("to", ()))


def place(row, roster, person, joins=NO_JOINS, families=None):
    """("placed", placement, audience) | ("refused", token) | ("undecided", family pattern) for one row, before
    the copy rule. An audience is a frozenset of keys or EVERYONE. `joins` is the caller's view of the room
    (NO_JOINS). `families` is the table (the pinned FAMILIES; a synthetic one keeps the Undecided path tested)."""
    table = FAMILIES if families is None else families
    fam = family_of(row["family"], table)
    if fam is None:
        return ("refused", "family_unknown")
    if fam == AMBIGUOUS:
        return ("refused", "family_ambiguous")
    cell = table[fam]
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
    # roster as it stands when the node replicates; a member removed since is owed nothing further
    members = frozenset(roster(row["room"]))
    # history_on_join does not change who is SERVED: a later joiner is served the older room rows, sealed by keys it
    # lacks (served is not readable; the tier gives the current epoch's key only, CC 4.4.3.16). `full` acts only on
    # a kept stream, through its producer's own key grants: the caller's (history_of)
    owed = members
    # WHAT IT MAY NAME: the members at the row's own head (named_within, CC 5.2), so a row's placement never
    # changes with a later removal or admission. MUTATION named_within_current: read against the current roster
    at = joins["at_head"](row["room"], row["id"])
    if at is None and named - seats_of(row):
        raise ValueError("audience: the members at %s's own head are the caller's (joins['at_head'])" % row["id"])
    within = members if "named_within_current" in MUT else frozenset(at or ())
    # the keys a seat offer or unseat over the room seats or removes are within its audience, ahead of named_within
    seated = seats_of(row) if "seats_not_within" not in MUT else frozenset()
    # a seat of a DUTY over the room (the moderator's acceptance) seats a member at the row's own head, never an
    # outsider: only such keys pass. MUTATION duty_seats_outsider
    if fam in DUTY_SEAT_FAMILIES and "duty_seats_outsider" not in MUT:
        seated = seated & within
    if "named_within_unread" not in MUT and not (named - seated) <= within:
        return ("refused", "named_outside_audience")
    return ("placed", placement, owed | me | named | seated)


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


def carried(r, a, d, ad, roster, person):
    """The keys a concluded placed row d naming r carries r to, or None: the copy rule of CC 5.2 as the
    Constitution read it (proposal c, the one place it is stated). Carriage is of ROWS: served is not readable, and
    a row reaches a key that lacks the epoch's key sealed.
        c.1  a room row is carried by a concluded room row of the same room, to the carrier's audience;
        c.2  only to keys on the room's current roster: nothing reaches a key off it (an offered key that never
             accepted, a removed key);
        c.3  a self or an addressed row is carried only by a concluded row of its own signer (or that signer's
             person), into that row's audience (bounded by c.2 where the carrier is a room row). THE CONTRACT: the
             caller's `person(key)` is the person's CURRENT, concluded key roster (seat.as_persons on the key-person
             lane, once merged; no separate notion): an evicted or revoked key leaves the person and carries
             nothing;
    the gate of CC 5.2 kept: the carrier's signer is already in r's audience. A key grant is never carried: it
    is served per its placement (the content's scope) and opened only by the key it names. MUTATIONS copy_cross_room, copy_off_roster, copy_any_carrier, copy_any_signer,
    copy_unconcluded, key_grant_carried."""
    if not d.get("concluded") and "copy_unconcluded" not in MUT:
        return None
    if family_of(r["family"]) == KEY_GRANT and "key_grant_carried" not in MUT:
        return None
    if not _within(d["signer"], a[2]) and "copy_any_signer" not in MUT:
        return None
    on_roster = lambda aud, room: aud if "copy_off_roster" in MUT else _meet(aud, frozenset(roster(room)))
    if a[1] in TARGETED:
        if ad[1] not in TARGETED:
            return None
        if d.get("room") != r.get("room") and "copy_cross_room" not in MUT:
            return None
        return on_roster(ad[2], r["room"])
    if d["signer"] != r["signer"] and d["signer"] not in person(r["signer"]) and "copy_any_carrier" not in MUT:
        return None
    return on_roster(ad[2], d["room"]) if ad[1] in TARGETED else ad[2]


def _persons_within(a, b, person):
    """Every PERSON audience a holds is one audience b holds (the ruling: "narrower" is over persons): a key of a is
    within b where b holds it or another key of its person. MUTATION narrower_by_keys: by keys."""
    if b == EVERYONE:
        return True
    if a == EVERYONE:
        return False
    if "narrower_by_keys" in MUT:
        return a <= b
    return all(k in b or any(x in b for x in person(k)) for k in a)


def follow(r, own, followed, rule, person=lambda k: (k,)):
    """A row of a `follows` family (FOLLOWS: custody, duty, ownership, stream:head) placed at the scope of the row it
    follows (followed_of: by its family's reference, the ruling G34): its own answer where that holds, else the
    refusal. rule "same": the
    placement and the audience of the followed row; "narrower": every person of its audience is a person of the
    followed row's (the Constitution's ruling: over persons, not keys and not the placement word; `person` is the
    person contract, the person's current key roster). MUTATION follows_unread."""
    if own[0] != "placed" or "follows_unread" in MUT:
        return own
    fid, why = followed_of(r)
    if fid is None:
        return ("refused", why)
    if followed is None:
        return ("refused", "follows_not_held")
    if followed[0] != "placed":
        return ("refused", "follows_unplaced")
    if rule == "same":
        return own if own[1] == followed[1] and own[2] == followed[2] else ("refused", "follows_mismatch")
    return own if _persons_within(own[2], followed[2], person) else ("refused", "follows_wider")


def audiences(rows, roster, person, joins=NO_JOINS):
    """{row id: its answer}, the follows rule and then the copy rule applied (carried): a placed row's audience grows
    by the keys every concluded placed row naming it carries it to; the least fixed point, which only grows."""
    out = {r["id"]: place(r, roster, person, joins) for r in rows}
    # follows, along chains of followers: each against its followed row's answer, once that one is settled
    followers = [r for r in rows if out[r["id"]][0] == "placed" and family_of(r["family"]) in FOLLOWS]
    while followers:
        ready = [r for r in followers if followed_of(r)[0] not in {f["id"] for f in followers}]
        if not ready:                                          # a cycle of followers: none is placed
            for r in followers:
                out[r["id"]] = ("refused", "follows_unplaced")
            break
        for r in ready:
            out[r["id"]] = follow(r, out[r["id"]], out.get(followed_of(r)[0]), FOLLOWS[family_of(r["family"])],
                                  person)
        followers = [r for r in followers if r not in ready]
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
            for d in namers[i]:
                ad = out[d["id"]]
                if ad[0] != "placed":
                    continue
                add = carried(by[i], out[i], d, ad, roster, person)
                if add is None:
                    continue
                grown = _union(out[i][2], add)
                if grown != out[i][2]:
                    out[i] = ("placed", out[i][1], grown); changed = True
    return out


def instance(pattern):
    """A family name the pattern matches, for the generated cases: each placeholder and a final `*` filled."""
    return ":".join("x" if s.startswith("{") or s == "*" else s for s in pattern.split(":"))
