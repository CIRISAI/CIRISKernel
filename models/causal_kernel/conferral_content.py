"""
conferral_content.py: room content after a member's seat ends, where the END names the rows held good
(the Constitution's proposal of 2026-11-22, second form, for CC 2.4.1.1 and persist v62.0). A reference: from a
set of rows, for every content row of the member, whether it is COUNTED at its own head and whether it is IN
FORCE (in the room's content) now, and the rule that decides it.

The proposal.
1. A content row (a message, a file placement, a reaction, and an edit or a retraction of one: on the wire each
   is a composer its author signs) is an act under its signer's membership. It names the roster head it is at
   and, in `prev`, its author's current newest content rows in the room: its predecessors, a set. A person
   signs from several devices, under one key or several, so a series forks routinely; a row that names both
   branches joins them. "The member's own row" means signed by any key of the member (B and B2 here); M is a
   co-member, whose rows are not this member's.
2. A row that ends the member's seat (a counted removal, or the member's own resignation) names in
   `trusted_through` the newest rows of the member its signers hold good: the tips, a set.
3. NOTHING WAITS ON CONTENT. A tip is not among the rows an end names for the door, and a predecessor is not
   among the rows a content row names for it: `prev`, `trusted_through` and a retraction's `target` are read by
   the fold and make no row wait. A tip that is not held keeps nothing; when it arrives, it and its held
   ancestors are kept. A predecessor that is not held is not followed, so what lies behind it is not kept
   until it arrives. A row named by id is fixed by that id: what an ended member signs later is never the row
   a tip or a predecessor already names.
4. After the end, a content row of the member is in the room's content when it is a named tip that is held, or
   an ancestor of one along `prev` among its author's own rows. Every other content row of theirs counts at its
   own head and is not in the room's content.
5. Tips only grow: a later counted row of the same body (`tips`) may name further tips, and the kept set is the
   union. No co-member receipts content.

6. SEAT BY SEAT. A seat is one stay: from the roster version that admits the member to the end of that stay.
   A later version that admits the member again begins another seat. A content row, and an end, belong to the
   seat of the head they name; a row adding tips belongs to the seat of the end it extends. Each seat's
   content is judged by that seat's own ends and tips and by nothing of another seat:
   - the head a row names decides, never when it was signed or received: a row signed after a re-admission
     that names an old head is a row of the old seat;
   - a re-admission restores nothing: what an earlier end did not hold good stays out;
   - the walk from a tip does not cross seats, so rejoining, naming old rows as predecessors and leaving again
     brings nothing back;
   - a row naming a head at which the member does not sit belongs to no seat and does not count.

7. RECEIPTS. No rule reads a receipt of a content row (`receipt`): no co-member receipts content, and the
   count's own receipt keeps nothing, since the count's word is its tips.
8. THE READER'S LINE (CC 2.7.8, CC 2.7.9; checkpoint.own_line and settle, sibling-safe as checkpoint.behind, the
   rulings of 2026-11-27). The counted acts the line reads are the roster versions, the ends and the rows adding
   tips. The reader's acknowledgements (`ack`, signer R: every row the reader signs in the room) each acknowledge
   the counted acts in their past that are not already void for the line the reader's earlier acknowledgements
   (those in its own past) drew. A counted act is behind a line act where every head it names is strictly in the
   past of one of the line act's OWN heads (a roster version's, the versions it names; an end's or a tips row's,
   its `head`) and it is not in that act's past; a sibling at the line act's head is not behind it. Every counted
   act behind the line, and every one built on a void one, is void for this reader: an end so void ends nothing
   (`end_void.line`), a tips row so void adds nothing. The line is monotone: acknowledgements accumulate in any
   order, an act behind ANY acknowledged act is void, an acknowledged act included, and acknowledging never
   un-voids. The line voids no content row (conferral_end.py, section C).
9. KEY REMOVALS (`keyend`, `removes` a key of the member) are the person's own key roster's acts: a key of the
   member signs one (its eviction of the key, or the key's own revocation). Key-level, each reaches every room:
   it cuts every row of the member that key signs which is not in its past. A cut content row does not count
   (`K.key_removed`), is not held good and is not followed; a cut retraction is not read. A key removal voids
   no end: the member's eviction of a key it resigned under would otherwise undo its resignation. A row of that
   shape the room's count signs is not read: a room's count ends a SEAT, an end, in its own room only.
10. ROOMS. Every row but a key removal belongs to its `room` (one room where none is named), and each room is
   judged by its own rows alone: a tip, a predecessor, a retraction's target, an end, a head or an
   acknowledgement of another room is not read.

No instant is read and no arrival order: the answer is a function of the held rows. One member and its content
are modelled (keys B and B2); other members' content is untouched by any of this.

Rows (the kernel's row shape: `id`, `kind`, `signer`, the ids it `names`, and the fields a rule reads):
    head   a roster version; `names` the heads it extends; `seat`: "admits" where the version admits the member
           (a stay begins), "out" where it does not list the member, absent or "sits" where the member sits on
    act    a content row of the member: `signer` the key (B or B2), `head` the roster head it names, `prev` the
           list of its predecessors (empty for a first row), and for an edit or a retraction `target`, the row
           it composes on, and `compose` ("edit" or "retract"). An edit is a content row like any other, and
           no rule reads its `target`. A retraction is read: see W.retracted
    end    an end of the member's seat: `signer` "count" (a counted removal) or a key of the member (its own
           resignation), `head` (h_e), `trusted_through` the tips it holds good (a list; empty where its signers
           hold none, which on the wire is the member's absence). The tips are NOT in `names`
    tips   a later row naming further tips: `extends` the end it adds to (which it names), `trusted_through`,
           and `head`, the roster head it is counted over (a counted row names one; no rule here reads it)
    receipt  a receipt of a content row (`of`), by the count or a co-member. Not read
    ack    the reader's acknowledgement: `names` what it acknowledges (signer R)
    keyend a removal of the member's key `removes`, by a key of the member; it has no room
Every row may name its `room`.

Which ends count:
    end_void.stale_head  E1: the end has a head later than h_e in its own past: it concludes nothing
    end_void.line        the end is void for the reader's line (8.)
    end_void.seat_ended  the end has a counting end of the seat in its own past: the seat was already ended
Whether an end counts is decided by its own causal past alone, so no row the member signs later changes it;
the reader's own acknowledgements are the only other rows read. In particular the member's own end is NOT voided for naming a head later than another end's: under that rule the
exhaustive check found the member reviving a row that named its first resignation, by signing a second one at
an older head. An extra end of the member's own only ever takes rows out (E3, E4, and the rule below).

Whose tips are read (`merge`). The proposal's third point read literally is `union`, and
check_conferral_content.py shows that under it an ended member adds content for ever, by signing a further
resignation at the head it last sat at. The reference's default closes that:
    count_first             (default) the count's word: the union of the tips of every counted end that is not
                            stale and of every counted `tips` row. The member's own ends are read only where no
                            counted end counts, and then a row stays only where EVERY one of them holds it
                            good, so a second resignation can remove but never add. A `tips` row signed by the
                            member is never read.
    union                   the union of the tips of every end that counts, the member's own included, and of
                            every counted `tips` row
    count_first_self_union  count_first, but where only the member's own ends speak, the union of them

Rules for a content row, in the order they decide (the name a failing test reports):
    no_seat          the row names a head at which the member does not sit: not counted
    K.key_removed    a key removal that is read cuts the row: not counted
    no_end           no end counts: counted and in force
    E4.names_end     the row has a counting end in its past: not counted
    E3.later_head    the row names a head that has a counting end's h_e in its past: the seat is ended there
    W.retracted      counted, not in force: a retraction of the row by the member, under any of its keys, is
                     held (a person retracts from a second device). The Constitution's ruling of 2026-11-22:
                     an author's retraction of its own row takes effect whenever it is signed, before or after
                     an end, whether or not the retraction itself counts or is kept, and a retraction of a
                     retraction restores nothing. It can only take a row out. A co-member's is not read
    T.held_good      counted and in force: a held tip that is read, or its ancestor along `prev` among the
                     member's own rows, by any of its keys
    E2.forward       counted at its own head, not in force: not held good
"""

KEYS, COUNT = ("B", "B2"), "count"
MERGES = ("count_first", "union", "count_first_self_union")
MUT = set()            # planted breaks, switched on by check_conferral_content.py (PLANTS)


def _past(rows):
    by = {r["id"]: r for r in rows}
    memo = {}

    def anc(i):
        if i not in memo:
            memo[i] = set()
            out = set()
            for n in by[i].get("names", ()):
                out.add(n)
                if n in by:
                    out |= anc(n)
            memo[i] = out
        return memo[i]
    return by, anc


def key_cuts(rows):
    """{row id}: the member's rows a key removal cuts. A key removal (`keyend`, `removes` the key) is read where it
    is the key's own revocation (signed by the key it removes), or a CONCLUDED act of the person's own key roster
    under that roster's own rule (`concludes`, the caller's: the self-roster count of the seat model; a lone second
    key does not evict the first unless the roster's policy says one key suffices). It is key-level and reaches
    every room: it cuts every row that key signs which is not in its past, nor reachable along `prev` from a row it
    names (review r84: an honest revocation names its last trusted row, and what lies behind it stands), unless the reader had taken the row up
    already: a row in the past of one of the reader's acknowledgements (`ack`, in any room) that does not have the
    removal in its past stands (the monotone line: what the reader took up stays). Nothing else anchors a row:
    another key's row built on it proves nothing (review r83). The caller duty: an honest revocation names the
    key's last trusted rows, and what it names stands. The residual: a thief holding a key can revoke it naming
    nothing and take its unnamed rows out for every reader that had not taken them up. A reader applies only the key
    removals it holds: the caller places a key removal at commons, or in every room the key sits in. A row of that
    kind the room's count signs is not read: a room's count ends a SEAT, in its room only.
    MUTATIONS key_end_unread; count_key_end_read (one the count signs is read); unconcluded_key_end_read (an act of
    the roster that does not conclude is read); key_cut_past_line (a row the reader took up is cut)."""
    if "key_end_unread" in MUT:
        return set()
    by, anc = _past(rows)

    def read(q):
        if q["kind"] != "keyend":
            return False
        if q["signer"] == COUNT:
            return "count_key_end_read" in MUT
        if q["signer"] not in KEYS:
            return False
        return q["signer"] == q["removes"] or q.get("concludes", False) or "unconcluded_key_end_read" in MUT
    ends = [q for q in rows if read(q)]
    acks = [a["id"] for a in rows if a["kind"] == "ack"]
    taken = lambda r, q: "key_cut_past_line" not in MUT and any(
        r["id"] in anc(a) and q["id"] not in anc(a) for a in acks)
    # MUTATION anchor_reenabled: the content anchor review r83 broke (a revoked key's row stands where another key's
    # row of the room was built on it, "before it held the removal"): causally the same as a row signed after the
    # removal that leaves it unnamed, so one colluding or sock key revives every forged row, a forged retraction
    # included. Removed; the only anchor that stands is the reader's own taken-up line
    others = [b for b in rows if b["kind"] == "act" and b["signer"] not in KEYS and b["signer"] != COUNT]
    built = lambda r, q: "anchor_reenabled" in MUT and r["kind"] == "act" and any(
        b.get("room") == r.get("room") and r["id"] in anc(b["id"]) and q["id"] not in anc(b["id"]) for b in others)
    def named(q):
        """The rows a key removal keeps by what it names: each named row, and every row of the member reachable from
        it along `prev` (the walk an end's tips take, held_good), within that row's room: a predecessor of another
        room is not read (rule 10). MUTATIONS prev_walk_unread: its causal past only; walk_crosses_rooms."""
        out, todo = set(), [(n, None) for n in q.get("names", ())]
        while todo and "prev_walk_unread" not in MUT:
            t, room = todo.pop()
            x = by.get(t)
            if x is None or x["kind"] != "act" or x["signer"] not in KEYS or t in out:
                continue
            if room is not None and x.get("room") != room[0] and "walk_crosses_rooms" not in MUT:
                continue
            out.add(t)
            todo.extend((p, (x.get("room"),)) for p in x.get("prev") or ())
        return out
    keeps = {q["id"]: named(q) for q in ends}
    cut = set()
    for r in rows:
        if r["signer"] not in KEYS or r["kind"] == "keyend":
            continue
        if any(q["removes"] == r["signer"] and r["id"] not in anc(q["id"]) and r["id"] not in keeps[q["id"]]
               and not taken(r, q) and not built(r, q) for q in ends):
            cut.add(r["id"])
    return cut


def own_heads(m):
    """The heads a counted act of the line is counted over: a roster version's own (the versions it names); an end's
    or a row adding tips', its `head`."""
    if m["kind"] == "head":
        return [n for n in m.get("names", ()) if n != m["id"]]
    return [m["head"]] if m.get("head") is not None else []


def behind(e, m, anc):
    """The sibling-safe line (checkpoint.behind, the ruling of 2026-11-27): counted act e is behind line act m where
    every head it names is strictly in the past of one of m's OWN heads and e is not in m's past. A sibling at m's
    head is not behind it. MUTATION line_not_sibling_safe: e's heads strictly in the past of m itself."""
    if e["id"] == m["id"] or e["id"] in anc(m["id"]):
        return False
    hs = own_heads(e)
    if "line_not_sibling_safe" in MUT:
        return bool(hs) and all(h in anc(m["id"]) for h in hs)
    return bool(hs) and all(any(h in anc(t) for t in own_heads(m)) for h in hs)


LINE_KINDS = ("head", "end", "tips")      # the counted acts the reader's line reads, one definition for all three


def line(rows, world=None):
    """(the reader's line, the counted acts void for it) in one room, as checkpoint.own_line and settle read them
    (CC 2.7.8, CC 2.7.9). The counted acts are the roster versions, the ends and the rows adding tips. Each of the
    reader's acknowledgements (`ack`: every row the reader signs in the room) acknowledges the counted acts in its
    past that are not already void for the line its earlier acknowledgements (those in its own past) drew. So
    acknowledgements accumulate in any order, a counted act behind ANY acknowledged act is void, an acknowledged
    one included, and nothing revives: acknowledging never un-voids. A counted act built on a void one (naming it
    as a head) is void. MUTATIONS line_unread; ack_unvoids (an acknowledgement takes up everything in its past)."""
    if "line_unread" in MUT:
        return set(), set()
    by, anc = _past(world or rows)
    acts = [m for m in rows if m["kind"] in LINE_KINDS]

    def void_for(ln):
        out = {m["id"] for m in acts if m["id"] not in ln and any(behind(m, by[c], anc) for c in ln)}
        changed = True
        while changed:
            changed = False
            for m in acts:
                if m["id"] not in out and m["id"] not in ln and any(h in out for h in own_heads(m)):
                    out.add(m["id"]); changed = True
        return out
    acks = sorted((a for a in rows if a["kind"] == "ack"), key=lambda a: (len(anc(a["id"])), a["id"]))
    got = {}
    for a in acks:
        cov = {m["id"] for m in acts if m["id"] in anc(a["id"])}
        if "ack_unvoids" in MUT:
            got[a["id"]] = cov
            continue
        prior = set().union(*[got[b["id"]] for b in acks if b["id"] in anc(a["id"])])
        got[a["id"]] = cov - void_for(prior)
    mine = set().union(*got.values()) if got else set()
    return mine, void_for(mine)


def counting_ends(rows, world=None):
    """{end id: None if it counts, else the rule that voids it}, for the ends among `rows` (one seat's). The
    causal past is read over `world`, every held row: an end's past is what it names, in any seat."""
    by, anc = _past(world or rows)
    ends = [r for r in rows if r["kind"] == "end"]
    later = lambda h, he: he in anc(h) if h in by else False
    _, void_line = line(rows, world)
    memo = {}

    def void(e):
        i = e["id"]
        if i in memo:
            return memo[i]
        if any(later(h, e["head"]) for h in anc(i) if h in by and by[h]["kind"] == "head"):
            memo[i] = "end_void.stale_head"     # decided from the heads alone, before any other end is asked
            return memo[i]
        if i in void_line:
            memo[i] = "end_void.line"           # void for this reader's line
            return memo[i]
        if "key_end_voids_end" in MUT and i in key_cuts(world or rows):
            memo[i] = "end_void.key_removed"    # MUTATION: a key removal voids the member's end under that key
            return memo[i]
        seated = any(o["id"] in anc(i) and void(o) is None for o in ends if o is not e)   # ends in e's own past
        memo[i] = "end_void.seat_ended" if seated else None
        return memo[i]
    return {e["id"]: void(e) for e in ends}


def held_good(rows, r, cut=frozenset()):
    """The content rows a row's tips hold good: each named tip that is held and is a content row of the member,
    and its ancestors along every `prev` that is a held row of the member (by any of its keys). A row a key
    removal cuts is neither held good nor followed."""
    by = {x["id"]: x for x in rows}
    out, todo = set(), list(r.get("trusted_through", ()))
    while todo:
        t = todo.pop()
        x = by.get(t)
        if x is None or x["kind"] != "act" or x["signer"] not in KEYS or t in out:
            continue
        if t in cut and "cut_row_followed" not in MUT:
            continue
        out.add(t)
        for q in x.get("prev") or ():
            p = by.get(q)
            if p is not None and p["signer"] in KEYS:          # the member's own row, by any of its keys
                todo.append(q)
    return out


def _adds(rows, self_tips, void_line=frozenset()):
    """The rows adding tips that are read: counted `tips` rows not void for the reader's line (and, under the plant
    receipt_keeps, a counted receipt of a content row, read as naming it). MUTATION line_tips_unread: a tips row the
    line holds void is read."""
    out = [r for r in rows if r["kind"] == "tips" and (r["signer"] == COUNT or self_tips)
           and (r["id"] not in void_line or "line_tips_unread" in MUT)]
    if "receipt_keeps" in MUT:
        out += [dict(r, trusted_through=[r["of"]]) for r in rows if r["kind"] == "receipt" and r["signer"] == COUNT]
    return out


def kept(rows, merge="count_first", self_tips=False, world=None, cuts=None):
    """The content rows held good by the tips that are read under `merge`. `self_tips` is a plant: a `tips` row
    signed by the member is read."""
    cuts = cuts if cuts is not None else key_cuts(world or rows)
    void = counting_ends(rows, world)
    ends = [r for r in rows if r["kind"] == "end"]
    counts = [e for e in ends if void[e["id"]] is None]
    c_ends = [e for e in ends if e["signer"] == COUNT and void[e["id"]] != "end_void.stale_head"]
    own = [e for e in counts if e["signer"] in KEYS]
    adds = _adds(rows, self_tips, line(rows, world)[1])
    union = lambda rs: set().union(*[held_good(rows, r, cuts) for r in rs]) if rs else set()
    if merge == "union":
        return union(counts + adds)
    if any(e["signer"] == COUNT for e in counts):
        return union(c_ends + adds)
    if merge == "count_first_self_union":
        return union(own + adds)
    good = [held_good(rows, e, cuts) for e in own]
    return (set.intersection(*good) if good else set()) | union(adds)


def seats(rows, world=None):
    """{row id: its seat} for every content row, end and tips row. A seat is the set of the newest admitting
    heads in the past of the head the row names, that head included (the empty set where none admits: the one
    seat of a history with no re-admission). None for a row that names a head at which the member does not
    sit, a held row that is not a roster version of the room, a head that is not held, or (a tips row) an end
    that is not held: it belongs to no seat. A removal is the member's end and also a version of the roster: a
    row that names an end as its head names a head at which the member is out. `rows` are one room's;
    `world`, every held row, is read for the past."""
    by = {r["id"]: r for r in rows}
    _, anc = _past(world or rows)
    admits = [r["id"] for r in rows if r["kind"] == "head" and r.get("seat") == "admits"]

    def of_head(h):
        if h not in by or by[h].get("seat") == "out" or by[h]["kind"] != "head":
            return None                       # an end of the member's seat named as a head: the member is out at it
        mine = [a for a in admits if a == h or a in anc(h)]
        return frozenset(a for a in mine if not any(a in anc(b) for b in mine))
    out = {}
    for r in rows:
        if r["kind"] in ("act", "end"):
            out[r["id"]] = of_head(r["head"])
    for r in rows:
        if r["kind"] == "tips":
            out[r["id"]] = out.get(r["extends"])
        if r["kind"] == "receipt" and "receipt_keeps" in MUT:
            out[r["id"]] = out.get(r["of"])
    return out


def rooms(rows):
    """{room: its rows}: every row but a key removal belongs to the room it names (`room`; one room where none
    is named). A room's content is judged by its own rows alone. MUTATION rooms_mixed: one room."""
    out = {}
    for r in rows:
        if r["kind"] != "keyend":
            out.setdefault(None if "rooms_mixed" in MUT else r.get("room"), []).append(r)
    return out


def ended_seats(rows, merge="count_first"):
    """({(room, seat) with an end that counts}, {(room, seat) with a counted end that counts})."""
    some, counted = set(), set()
    for room, rr in rooms(rows).items():
        seat = seats(rr, rows)
        heads = [r for r in rr if r["kind"] == "head"]
        for s in {v for v in seat.values() if v is not None}:
            sub = heads + [r for r in rr if seat.get(r["id"]) == s] + [r for r in rr if r["kind"] == "ack"]
            void = counting_ends(sub, rows)
            ends = [r for r in sub if r["kind"] == "end" and void[r["id"]] is None]
            if ends:
                some.add((room, s))
            if any(e["signer"] == COUNT for e in ends):
                counted.add((room, s))
    return some, counted


def seat_of(rows):
    """{content row id: (room, seat)}, the key ended_seats uses."""
    out = {}
    for room, rr in rooms(rows).items():
        for i, s in seats(rr, rows).items():
            out[i] = (room, s) if s is not None else None
    return out


def answers(rows, merge="count_first", self_tips=False):
    """{content row id: {"counted": bool, "in_force": bool, "rule": str}} over the held `rows`: each room's rows
    judged by that room's own rows, and each seat's by that seat's own ends and tips."""
    cuts = key_cuts(rows)
    out = {}
    for rr in rooms(rows).values():
        out.update(_room_answers(rr, rows, merge, self_tips, cuts))
    return out


def _room_answers(rr, world, merge, self_tips, cuts):
    seat = seats(rr, world)
    heads = [r for r in rr if r["kind"] == "head"]
    acks = [r for r in rr if r["kind"] == "ack"]
    out = {r["id"]: {"counted": False, "in_force": False, "rule": "no_seat"}
           for r in rr if r["kind"] == "act" and r["signer"] in KEYS and seat[r["id"]] is None}
    # a retraction is read over all the room's held rows, whatever seat it or its target belongs to; one a key
    # removal cuts is not read
    by = {r["id"]: r for r in rr}
    retracted = {r["target"] for r in rr if r["kind"] == "act" and r.get("compose") == "retract"
                 and r["signer"] in KEYS and r.get("target") in by and by[r["target"]]["signer"] in KEYS
                 and (r["id"] not in cuts or "cut_retraction_read" in MUT)}
    for s in {v for v in seat.values() if v is not None}:
        out.update(_seat_answers(heads + acks + [r for r in rr if seat.get(r["id"]) == s], merge, self_tips,
                                 retracted, world, cuts))
    return out


def _seat_answers(rows, merge, self_tips, retracted, world, cuts):
    """The answers over the rows of one seat (and the roster heads and the reader's acknowledgements)."""
    assert merge in MERGES, merge
    by, anc = _past(world)
    void = counting_ends(rows, world)
    ends = [by[i] for i in sorted(void) if void[i] is None]
    later = lambda h, he: he in anc(h) if h in by else False
    good = kept(rows, merge, self_tips, world, cuts)
    out = {}
    for r in rows:
        if r["kind"] != "act" or r["signer"] not in KEYS:      # another member's row is not this member's content
            continue
        x = r["id"]
        if x in cuts:
            a = (False, False, "K.key_removed")
        elif any(e["id"] in anc(x) for e in ends):
            a = (False, False, "E4.names_end")
        elif any(later(r["head"], e["head"]) for e in ends):
            a = (False, False, "E3.later_head")
        elif x in retracted:
            a = (True, False, "W.retracted")
        elif not ends:
            a = (True, True, "no_end")
        elif x in good:
            a = (True, True, "T.held_good")
        else:
            a = (True, False, "E2.forward")
        out[x] = dict(zip(("counted", "in_force", "rule"), a))
    return out


def shown_first_held(rows, order, merge="count_first"):
    """The node-local fallback persist floated, NOT part of the proposal: a counted content row this reader held
    before it held any end that counts stays shown to this reader. {content row id: bool}. It reads the arrival
    `order`, so it is not a function of the held rows; check_conferral_content.py shows what follows."""
    final = answers(rows, merge)
    void = counting_ends(rows)                 # read over one seat: the cases it is run on have one
    first_end = min([order.index(i) for i in void if void[i] is None] or [len(order)])
    return {x: a["counted"] and (a["in_force"] or order.index(x) < first_end) for x, a in final.items()}


# ---- the case table: hand-written expectations, which the reference must meet --------------------------------
def _room(r, room):
    return dict(r, room=room) if room is not None else r


def head(i, *names, seat=None, room=None):
    return _room(dict({"id": i, "kind": "head", "signer": COUNT, "names": list(names)}, **({"seat": seat} if seat else {})),
                 room)


def act(i, h, prev=(), names=(), signer="B", **kw):
    prev = [prev] if isinstance(prev, str) else sorted(prev or ())
    # `names` is what the door waits on: the head and what the row cites. A predecessor and a retraction's
    # target are read by the fold and make no row wait
    return dict({"id": i, "kind": "act", "signer": signer, "head": h, "prev": prev,
                 "names": sorted(set(names) | {h})}, **kw)


def end(i, h, tips=(), signer=COUNT, names=(), room=None):
    return _room({"id": i, "kind": "end", "signer": signer, "head": h, "trusted_through": sorted(tips),
                  "names": sorted(set(names) | {h})}, room)          # the tips are not named: the end never waits


def tips(i, extends, tps, signer=COUNT, h="H0", room=None):
    return _room({"id": i, "kind": "tips", "signer": signer, "head": h, "extends": extends,
                  "trusted_through": sorted(tps), "names": sorted({extends, h})}, room)


def receipt(i, of, signer, names=(), room=None):
    """A receipt of a content row (`of`). No rule here reads it."""
    return _room({"id": i, "kind": "receipt", "signer": signer, "of": of, "names": sorted(set(names) | {of})}, room)


def ack(i, names, room=None, signer="R"):
    """The reader's acknowledgement of the rows it names: they and their past are on its line."""
    return _room({"id": i, "kind": "ack", "signer": signer, "names": sorted(names)}, room)


def keyend(i, removes, signer="B", names=(), concludes=False):
    """A removal of one key of the member (`removes`) from the person's own key roster, signed by a key of the
    member: an eviction (`concludes`: it concludes under the roster's own rule, the caller's), or the key's own
    revocation. Key-level, in every room."""
    return {"id": i, "kind": "keyend", "signer": signer, "removes": removes, "names": sorted(names),
            "concludes": concludes}


H0, H1 = head("H0"), head("H1", "H0")
HX, HA = head("HX", "H0", seat="out"), head("HA", "HX", seat="admits")
H2, G0 = head("H2", "H1"), head("G0", room="r2")
T, F = True, False
M1, M2, M3 = act("m1", "H0"), act("m2", "H0", "m1"), act("m3", "H0", "m2")
KEPT, OUT = (T, T, "T.held_good"), (T, F, "E2.forward")

# (name, about, rows, params, {act: (counted, in_force, rule)}, arrival orders a node may take them in)
CASES = [
    ("content_no_end", "no end held: a member's content rows count and are in the room's content",
     [H0, M1, M2], {}, {"m1": (T, T, "no_end"), "m2": (T, T, "no_end")}),
    ("removal_names_tip", "a counted removal names the newest row of the member's series: the whole series "
     "behind it stays in the room's content",
     [H0, M1, M2, M3, end("E", "H0", ["m3"])], {}, {"m1": KEPT, "m2": KEPT, "m3": KEPT}),
    ("removal_signers_hold_nothing", "the removal's signers held none of the member's content, so it names no "
     "tip: rows that reach a reader are counted at their head and not in the room's content, until a counted "
     "row names a tip",
     [H0, M1, M2, end("E", "H0")], {}, {"m1": OUT, "m2": OUT}),
    ("removal_in_flight_row", "the removers had not yet held m3 when they signed (it is concurrent with the end): "
     "m3 is out for everyone, honest or not; no rule can tell which",
     [H0, M1, M2, M3, end("E", "H0", ["m2"])], {}, {"m1": KEPT, "m2": KEPT, "m3": OUT}),
    ("in_flight_row_named_later", "the same rows, and then a counted row of the body names m3: tips only grow, "
     "and m3 is in the room's content from then on",
     [H0, M1, M2, M3, end("E", "H0", ["m2"]), tips("A", "E", ["m3"])], {}, {"m1": KEPT, "m2": KEPT, "m3": KEPT}),
    ("adding_row_waits_for_its_end", "a row that adds tips names the end it extends, so no node holds it before "
     "that end: in every arrival order the door allows, the end comes first",
     [H0, M1, M2, end("E", "H0", ["m1"]), tips("A", "E", ["m2"])], {}, {"m1": KEPT, "m2": KEPT},
     [["H0", "m1", "m2", "E", "A"], ["H0", "m1", "E", "m2", "A"]]),
    ("removed_member_keeps_posting", "after the removal the member signs m3 at the last head it sat at, not "
     "naming the end, and it arrives after the end at a node that never saw it: admitted, counted at its head, "
     "never in the room's content; the same answer in every arrival order",
     [H0, H1, M1, M2, end("E", "H0", ["m2"]), act("m3", "H0", "m2")], {}, {"m1": KEPT, "m2": KEPT, "m3": OUT},
     [["H0", "H1", "m1", "m2", "E", "m3"], ["H0", "m1", "m2", "m3", "H1", "E"]]),
    ("row_at_later_head", "a content row naming a roster head later than h_e: the member's seat is ended there, "
     "and the row does not count",
     [H0, H1, M1, end("E", "H0", ["m1"]), act("m2", "H1", "m1")], {},
     {"m1": KEPT, "m2": (F, F, "E3.later_head")}),
    ("row_names_end", "a content row that has the end in its past does not count, whatever head it names",
     [H0, M1, end("E", "H0", ["m1"]), act("m2", "H0", "m1", ["E"])], {},
     {"m1": KEPT, "m2": (F, F, "E4.names_end")}),
    ("resignation_names_tip", "the member's own resignation names its own newest row, which no one else holds "
     "yet: the resignation concludes at once (the seat ends; nothing waits), and when m2 arrives it and what is "
     "behind it are kept",
     [H0, M1, M2, end("R", "H0", ["m2"], "B")], {}, {"m1": KEPT, "m2": KEPT},
     [["H0", "m1", "R", "m2"], ["H0", "m1", "m2", "R"]]),
    ("end_names_tip_never_held", "the end names a tip that never arrives: it keeps nothing, and no rule tells "
     "this end from one that names no tip, so the member's held rows are out",
     [H0, M1, end("E", "H0", ["m9"])], {}, {"m1": OUT}),
    ("tip_arrives_after_end", "the removal names m2, and m2 reaches this node after the removal: out until then, "
     "kept from then on; the same answer in every arrival order once the rows are held",
     [H0, M1, end("E", "H0", ["m2"]), M2], {}, {"m1": KEPT, "m2": KEPT},
     [["H0", "m1", "E", "m2"], ["H0", "m1", "m2", "E"], ["H0", "E", "m1", "m2"]]),
    ("fork_of_one_series", "one key forked its own series (m2 and x2 both follow m1): the end names one branch, "
     "and only that branch and what is behind it stay; the other branch is out until a counted row names it",
     [H0, M1, M2, act("x2", "H0", "m1"), end("E", "H0", ["m2"])], {}, {"m1": KEPT, "m2": KEPT, "x2": OUT}),
    ("fork_both_branches_named", "the enders hold both branches of a fork and name both: tips are a set, and "
     "both branches stay",
     [H0, M1, M2, act("x2", "H0", "m1"), end("E", "H0", ["m2", "x2"])], {}, {"m1": KEPT, "m2": KEPT, "x2": KEPT}),
    ("fork_rejoined", "two devices forked the series (m2, x2) and a later row names both as its predecessors: "
     "one tip keeps both branches",
     [H0, M1, M2, act("x2", "H0", "m1"), act("j3", "H0", ["m2", "x2"]), end("E", "H0", ["j3"])], {},
     {"m1": KEPT, "m2": KEPT, "x2": KEPT, "j3": KEPT}),
    ("kept_post_edited_before_end", "the member edited its post m1 before the removal, and the edit is behind the "
     "named tip: the edit is kept with its target",
     [H0, M1, act("e2", "H0", "m1", target="m1", compose="edit"), end("E", "H0", ["e2"])], {},
     {"m1": KEPT, "e2": KEPT}),
    ("kept_post_edited_after_end", "after the removal the member signs an edit of its kept post m1 at the old "
     "head: the edit is a content row no tip names, so it is out though its target is kept. A composer does "
     "NOT follow its target into the content; if it did, an ended member would rewrite its kept posts",
     [H0, M1, end("E", "H0", ["m1"]), act("e2", "H0", "m1", target="m1", compose="edit")], {},
     {"m1": KEPT, "e2": OUT}),
    ("kept_post_retracted_after_end", "the same with a retraction: the retraction row is out of the content like "
     "any row no tip names, and it still takes effect: an author's retraction of its own row takes effect "
     "whenever it is signed, so the kept post leaves the room's content. It can only take a row out",
     [H0, M1, end("E", "H0", ["m1"]), act("w2", "H0", "m1", target="m1", compose="retract")], {},
     {"m1": (T, F, "W.retracted"), "w2": OUT}),
    ("post_retracted_no_end", "with no end held: a member retracts its own post, and the post is out",
     [H0, M1, act("w2", "H0", "m1", target="m1", compose="retract")], {},
     {"m1": (T, F, "W.retracted"), "w2": (T, T, "no_end")}),
    ("retraction_from_a_second_device", "the member retracts its post from its second key: its own retraction, "
     "and it takes effect",
     [H0, M1, end("E", "H0", ["m1"]), act("w2", "H0", target="m1", compose="retract", signer="B2")], {},
     {"m1": (T, F, "W.retracted"), "w2": OUT}),
    ("retraction_by_a_co_member", "a co-member signs a retraction of the member's post: not its author's, and "
     "not read by this rule",
     [H0, M1, end("E", "H0", ["m1"]), act("w2", "H0", target="m1", compose="retract", signer="M")], {},
     {"m1": KEPT}),
    ("retraction_of_a_retraction", "the member retracts its retraction: nothing is restored, or an ended member "
     "would add a row back",
     [H0, M1, end("E", "H0", ["m1"]), act("w2", "H0", "m1", target="m1", compose="retract"),
      act("w3", "H0", "w2", target="w2", compose="retract")], {},
     {"m1": (T, F, "W.retracted"), "w2": (T, F, "W.retracted"), "w3": OUT}),
    ("retraction_that_does_not_count", "the retraction names the end (so as an act under the ended seat it does "
     "not count, E4): it is still its author's own retraction and takes effect",
     [H0, M1, end("E", "H0", ["m1"]), act("w2", "H0", "m1", ["E"], target="m1", compose="retract")], {},
     {"m1": (T, F, "W.retracted"), "w2": (F, F, "E4.names_end")}),
    ("middle_of_chain_not_held", "the tip m3 is held, its predecessor m2 is not, and m1 behind that is held: "
     "nothing shows m1 is m3's ancestor, so m1 is not kept until m2 arrives",
     [H0, M1, M3, end("E", "H0", ["m3"])], {}, {"m1": OUT, "m3": KEPT}),
    ("middle_of_chain_arrives", "the same, and m2 arrives: m2 and m1 are kept; the same answer in every arrival "
     "order once all three are held, m2 last included",
     [H0, M1, M3, end("E", "H0", ["m3"]), M2], {}, {"m1": KEPT, "m2": KEPT, "m3": KEPT},
     [["H0", "m1", "m3", "E", "m2"], ["H0", "E", "m3", "m1", "m2"], ["H0", "m2", "m1", "m3", "E"]]),
    ("fork_other_branch_named_later", "the same fork, and a counted row then names the other branch's tip: both "
     "branches stay",
     [H0, M1, M2, act("x2", "H0", "m1"), end("E", "H0", ["m2"]), tips("A", "E", ["x2"])], {},
     {"m1": KEPT, "m2": KEPT, "x2": KEPT}),
    ("second_key_never_seen", "the member's second key signed a series the enders never held: the end names one "
     "tip, of the first key's series, and the whole second series is out",
     [H0, M1, M2, act("n1", "H0", signer="B2"), act("n2", "H0", "n1", signer="B2"), end("E", "H0", ["m2"])], {},
     {"m1": KEPT, "m2": KEPT, "n1": OUT, "n2": OUT}),
    ("second_key_named_later", "the same rows, and a counted row then names the second series' tip: it is in",
     [H0, M1, M2, act("n1", "H0", signer="B2"), act("n2", "H0", "n1", signer="B2"), end("E", "H0", ["m2"]),
      tips("A", "E", ["n2"])], {}, {"m1": KEPT, "m2": KEPT, "n1": KEPT, "n2": KEPT}),
    ("prev_across_the_members_keys", "a row signed by the member's second key names a row of its first key as "
     "its predecessor: both are the member's own, and the walk follows",
     [H0, M1, act("n1", "H0", "m1", signer="B2"), end("E", "H0", ["n1"])], {}, {"m1": KEPT, "n1": KEPT}),
    ("prev_through_a_co_members_row", "the member's row names a CO-MEMBER's row as its predecessor, and that row "
     "names the member's m1: the walk does not pass through another member's row, so m1 is not kept",
     [H0, M1, act("q1", "H0", "m1", signer="M"), act("n1", "H0", "q1"), end("E", "H0", ["n1"])], {},
     {"m1": OUT, "n1": KEPT}),
    ("two_removals_different_tips", "two counted removals of the member at one head, concurrent, naming "
     "different tips: both are the count's word, and the kept set is the union; nothing waits",
     [H0, M1, M2, M3, end("E", "H0", ["m3"]), end("E2", "H0", ["m2"])], {}, {"m1": KEPT, "m2": KEPT, "m3": KEPT}),
    ("removal_then_backdated_resignation", "after a removal that kept m1 only, the member signs m2 and a "
     "resignation at the old head naming m2, neither naming the removal: where a counted end counts the "
     "member's own end is not read, so m2 is not added",
     [H0, M1, end("E", "H0", ["m1"]), M2, end("R", "H0", ["m2"], "B")], {}, {"m1": KEPT, "m2": OUT}),
    ("removal_then_backdated_resignation_union", "the same rows under the proposal's third point read literally "
     "(`union`): the member's own later resignation adds m2. This is the hole count_first closes",
     [H0, M1, end("E", "H0", ["m1"]), M2, end("R", "H0", ["m2"], "B")], {"merge": "union"},
     {"m1": KEPT, "m2": KEPT}),
    ("two_resignations", "the member signs two resignations at one head naming different tips (a fork of its own "
     "end): a row stays only where both hold it good, so a second resignation never adds a row",
     [H0, M1, M2, end("R", "H0", ["m1"], "B"), end("R2", "H0", ["m2"], "B")], {}, {"m1": KEPT, "m2": OUT}),
    ("resignation_then_counted_tips", "the member resigned naming m1, and no counted row ends the seat; a "
     "counted row then names m2: the member's own tips are still read and the counted row's are added",
     [H0, M1, act("x1", "H0"), end("R", "H0", ["m1"], "B"), tips("A", "R", ["x1"])], {},
     {"m1": KEPT, "x1": KEPT}),
    ("resignation_counted_tips_then_narrowing", "the same, and the member then signs a second resignation "
     "naming nothing: it narrows the member's own tips to none, and what the counted row named stays",
     [H0, M1, act("x1", "H0"), end("R", "H0", ["m1"], "B"), tips("A", "R", ["x1"]), end("R2", "H0", [], "B")], {},
     {"m1": OUT, "x1": KEPT}),
    ("member_adds_tips_itself", "a row adding tips signed by the member is never read: only a counted row adds",
     [H0, M1, M2, end("E", "H0", ["m1"]), tips("A", "E", ["m2"], "B")], {}, {"m1": KEPT, "m2": OUT}),
    ("second_end_after_first", "a second removal that has the first in its past ends nothing (the seat was "
     "already ended), but it is a counted row of the body and its tips add",
     [H0, M1, M2, end("E", "H0", ["m1"]), end("E2", "H0", ["m2"], names=["E"])], {}, {"m1": KEPT, "m2": KEPT}),
    ("resignation_at_later_head", "a resignation naming a head later than the removal's h_e, concurrent with "
     "it: where a counted end counts the member's own end's tips are not read, so naming none takes nothing out",
     [H0, H1, M1, M2, end("E", "H0", ["m2"]), end("R", "H1", [], "B")], {}, {"m1": KEPT, "m2": KEPT}),
    ("backdated_resignation_uncounts_own_rows", "the member was removed at H1 with m2 (at H1) kept, and then signs "
     "a resignation at H0: E3 puts its own row at H1 at a head later than an end of its seat, so m2 no longer "
     "counts. An ended member can take its own rows out this way; conferral_end.py's reader's line bounds it",
     [H0, H1, M1, act("m2", "H1", "m1"), end("E", "H1", ["m2"]), end("R", "H0", [], "B")], {},
     {"m1": KEPT, "m2": (F, F, "E3.later_head")}),
    ("end_stale_head", "E1: an end naming H0 with H1 in its own past concludes nothing, and its tips are not read",
     [H0, H1, M1, end("E", "H0", ["m1"], names=["H1"])], {}, {"m1": (T, T, "no_end")}),
    ("tip_at_later_head", "the end names as a tip a row at a head later than h_e: naming it does not make it "
     "count (E3 decides first), and what is behind it at h_e is kept",
     [H0, H1, M1, act("m2", "H1", "m1"), end("E", "H0", ["m2"])], {}, {"m1": KEPT, "m2": (F, F, "E3.later_head")}),
    # a member seated again: H0 (seated) <- HX (not listed) <- HA (admitted again)
    ("rejoin_and_post", "the member left with m1 kept, was admitted again at HA, and posts n1 there: a new seat "
     "with no end, so n1 is in the room's content; m1 stays on the first end's word",
     [H0, HX, HA, M1, end("E", "H0", ["m1"]), act("n1", "HA")], {}, {"m1": KEPT, "n1": (T, T, "no_end")}),
    ("rejoin_restores_nothing", "a re-admission restores nothing: m2, which the first end did not hold good, "
     "stays out after the member is seated again",
     [H0, HX, HA, M1, M2, end("E", "H0", ["m1"]), act("n1", "HA")], {},
     {"m1": KEPT, "m2": OUT, "n1": (T, T, "no_end")}),
    ("stale_device_after_rejoin", "a row signed after the re-admission that names the OLD head: the head a row "
     "names decides, so it is a row of the old seat and is out; the device signs again at a current head",
     [H0, HX, HA, M1, end("E", "H0", ["m1"]), act("n1", "HA"), act("s2", "H0", "m1")], {},
     {"m1": KEPT, "n1": (T, T, "no_end"), "s2": OUT}),
    ("row_between_seats", "a row naming a head at which the member does not sit (after its end, before the "
     "re-admission): it belongs to no seat and does not count",
     [H0, HX, HA, M1, end("E", "H0", ["m1"]), act("g1", "HX", "m1")], {},
     {"m1": KEPT, "g1": (F, F, "no_seat")}),
    ("row_naming_the_removal_as_its_head", "the removal is the member's end and a version of the roster: a row of "
     "the member that names it as its head names a head at which the member is out, and does not count; a version "
     "built on the removal admits the member again and a row there is in a new seat",
     [H0, M1, end("E", "H0", ["m1"]), act("g1", "E", "m1"), head("HR", "E", seat="admits"), act("n1", "HR")], {},
     {"m1": KEPT, "g1": (F, F, "no_seat"), "n1": (T, T, "no_end")}),
    ("second_seat_tip_reaches_left_out_row", "the hole a second seat would open: the member rejoins, posts n1 "
     "naming m2 (which the first end left out) as its predecessor, and leaves again with n1 as the tip. The "
     "walk does not cross seats: n1 is kept, m2 stays out",
     [H0, HX, HA, M1, M2, end("E", "H0", ["m1"]), act("n1", "HA", "m2"), end("E2", "HA", ["n1"])], {},
     {"m1": KEPT, "m2": OUT, "n1": KEPT}),
    ("second_seat_tip_reaches_kept_row", "the same where the first end kept m2: it stays in, on the first "
     "end's word and not the second's",
     [H0, HX, HA, M1, M2, end("E", "H0", ["m2"]), act("n1", "HA", "m2"), end("E2", "HA", ["n1"])], {},
     {"m1": KEPT, "m2": KEPT, "n1": KEPT}),
    ("second_seat_ends_without_tips", "the second seat ends and its end holds nothing good: the second seat's "
     "rows are out, and the first seat's kept rows are untouched",
     [H0, HX, HA, M1, end("E", "H0", ["m1"]), act("n1", "HA"), end("E2", "HA")], {}, {"m1": KEPT, "n1": OUT}),
    ("keeps_first_end_after_rejoin", "a counted row adds a tip for the FIRST end after the member has rejoined: "
     "it cites that end, so it is read in the first seat, and m2 comes in",
     [H0, HX, HA, M1, M2, end("E", "H0", ["m1"]), act("n1", "HA"), tips("A", "E", ["m2"])], {},
     {"m1": KEPT, "m2": KEPT, "n1": (T, T, "no_end")}),
    ("first_end_names_second_seat_row", "the first end's adding row names a row of the second seat as a tip: "
     "a tip holds good only rows of its own seat, so after the second seat ends without it, n1 is out",
     [H0, HX, HA, M1, end("E", "H0", ["m1"]), act("n1", "HA"), tips("A", "E", ["n1"]), end("E2", "HA")], {},
     {"m1": KEPT, "n1": OUT}),
    ("two_first_seat_ends_after_rejoin", "two removals of the first seat, naming different tips, both arriving "
     "after the rejoin: they are ends of the first seat by the head they name; their tips join there, and the "
     "second seat is not ended",
     [H0, HX, HA, M1, M2, act("n1", "HA"), end("E", "H0", ["m1"]), end("Eb", "H0", ["m2"])], {},
     {"m1": KEPT, "m2": KEPT, "n1": (T, T, "no_end")}),
    ("backdated_resignation_after_rejoin", "after rejoining, the member signs a resignation at the old head "
     "naming nothing: it is an end of the old seat, where a counted end counts and its own end is not read; "
     "the second seat is not ended by it",
     [H0, HX, HA, M1, end("E", "H0", ["m1"]), act("n1", "HA"), end("R", "H0", [], "B")], {},
     {"m1": KEPT, "n1": (T, T, "no_end")}),
    ("retract_old_post_after_rejoin", "seated again, the member retracts a post of its first seat that the first "
     "end kept: a retraction is read across seats, and the post leaves the content",
     [H0, HX, HA, M1, end("E", "H0", ["m1"]), act("w1", "HA", target="m1", compose="retract")], {},
     {"m1": (T, F, "W.retracted"), "w1": (T, T, "no_end")}),
    ("tip_not_the_members", "a tip that is not a content row of the member is not read: here the end names a "
     "roster head as a tip, and nothing is held good",
     [H0, M1, end("E", "H0", ["H0"])], {}, {"m1": OUT}),
    # receipts together with tips: no rule reads a receipt of content; the count's word is its tips
    ("receipt_by_co_member_keeps_nothing", "a co-member receipts m2, which the end did not hold good: no "
     "co-member receipts content, and m2 stays out",
     [H0, M1, M2, end("E", "H0", ["m1"]), receipt("q2", "m2", "M")], {}, {"m1": KEPT, "m2": OUT}),
    ("counted_receipt_keeps_nothing", "the count receipts m2 after the end: a receipt is not a tip, and m2 stays "
     "out until a counted row names it in `trusted_through`",
     [H0, M1, M2, end("E", "H0", ["m1"]), receipt("q2", "m2", COUNT, ["E"])], {}, {"m1": KEPT, "m2": OUT}),
    ("counted_receipt_then_tips", "the same, and a counted row then names m2 as a tip: m2 is in by the tip",
     [H0, M1, M2, end("E", "H0", ["m1"]), receipt("q2", "m2", COUNT, ["E"]), tips("A", "E", ["m2"])], {},
     {"m1": KEPT, "m2": KEPT}),
    ("receipt_takes_nothing_out", "a receipt of a kept row changes nothing, whoever signs it",
     [H0, M1, end("E", "H0", ["m1"]), receipt("q1", "m1", "M", ["E"]), receipt("q2", "m1", COUNT, ["E"])], {},
     {"m1": KEPT}),
    ("receipt_with_no_end", "with no end held, a receipt changes nothing either",
     [H0, M1, receipt("q1", "m1", COUNT)], {}, {"m1": (T, T, "no_end")}),
    # the reader's line on an end (CC 2.7.8, sibling-safe: checkpoint.behind)
    ("line_voids_backdated_resignation", "the member was removed at H1 with m2 kept, then signed a resignation "
     "at H0 (backdated_resignation_uncounts_own_rows); a reader that acknowledged the removal holds the "
     "resignation behind its line (H0 is strictly older than H1, the removal's head), so for that reader it "
     "ends nothing and m2 still counts",
     [H0, H1, M1, act("m2", "H1", "m1"), end("E", "H1", ["m2"]), end("R", "H0", [], "B"), ack("k1", ["E"])], {},
     {"m1": KEPT, "m2": KEPT}),
    ("line_sibling_safe", "a removal at H0 and a reader that acknowledged H1, which is counted over H0: the "
     "removal is a sibling of H1, not behind it, and it ends the seat for that reader",
     [H0, H1, M1, M2, end("E", "H0", ["m1"]), ack("k1", ["H1"])], {}, {"m1": KEPT, "m2": OUT}),
    ("line_voids_end_two_heads_back", "a removal at H0 and a reader that acknowledged H2 (on H1, on H0): H0 is "
     "strictly older than H2's own head and the removal is not in H2's past, so it is behind the line and ends "
     "nothing for that reader",
     [H0, H1, H2, M1, M2, end("E", "H0", ["m1"]), ack("k1", ["H2"])], {},
     {"m1": (T, T, "no_end"), "m2": (T, T, "no_end")}),
    ("line_holds_what_it_acknowledges", "the same, where the reader acknowledged the removal too: an end on the "
     "reader's line is never behind it",
     [H0, H1, H2, M1, M2, end("E", "H0", ["m1"]), ack("k1", ["H2", "E"])], {}, {"m1": KEPT, "m2": OUT}),
    ("line_not_for_content", "the line voids no content row: a row at H0 for a reader that acknowledged H2 "
     "counts (section C)",
     [H0, H1, H2, M1, ack("k1", ["H2"])], {}, {"m1": (T, T, "no_end")}),
    ("line_acknowledging_never_unvoids", "the reader acknowledged H2, so the removal at H0 is behind its line; "
     "a later row of the reader names the removal: it adopts nothing, the removal stays void for this reader",
     [H0, H1, H2, M1, M2, end("E", "H0", ["m1"]), ack("k1", ["H2"]), ack("k2", ["E", "k1"])], {},
     {"m1": (T, T, "no_end"), "m2": (T, T, "no_end")}),
    ("line_acknowledged_first_then_behind", "the reader acknowledged the removal first and H2 later, in its "
     "own past: the removal is on the line, and an act of the line is never behind it",
     [H0, H1, H2, M1, M2, end("E", "H0", ["m1"]), ack("k1", ["E"]), ack("k2", ["H2", "k1"])], {},
     {"m1": KEPT, "m2": OUT}),
    ("line_concurrent_acknowledgements", "two acknowledgements of the reader, neither in the other's past, of the "
     "removal and of H2: each takes up what is in its past, and the removal is on the line",
     [H0, H1, H2, M1, M2, end("E", "H0", ["m1"]), ack("k1", ["E"]), ack("k2", ["H2"])], {},
     {"m1": KEPT, "m2": OUT}),
    ("line_holds_tips_row_void", "a counted row adds a tip at H0 while the reader's line stands at the removal at "
     "H1: the tips row is behind the line (H0 strictly older than H1) and adds nothing for this reader",
     [H0, H1, M1, M2, end("E", "H1", ["m1"]), tips("A", "E", ["m2"]), ack("k1", ["E"])], {},
     {"m1": KEPT, "m2": OUT}),
    ("line_tips_row_at_the_end_head", "the same tips row counted over H1, the removal's own head: a sibling, not "
     "behind it, and it adds m2",
     [H0, H1, M1, M2, end("E", "H1", ["m1"]), tips("A", "E", ["m2"], h="H1"), ack("k1", ["E"])], {},
     {"m1": KEPT, "m2": KEPT}),
    # key removals
    ("key_removed_rows_after_it_cut", "a key of the member is removed with n1 in the removal's past: n1 counts, "
     "and n2, which that key signed later, is cut",
     [H0, M1, act("n1", "H0", signer="B2"), keyend("x", "B2", names=["n1"], concludes=True), act("n2", "H0", "n1", signer="B2")],
     {}, {"m1": (T, T, "no_end"), "n1": (T, T, "no_end"), "n2": (F, F, "K.key_removed")}),
    ("cut_tip_keeps_nothing", "the end names as a tip a row a key removal cuts: it is not held good and the walk "
     "does not pass through it, so m1 behind it is out",
     [H0, M1, act("n2", "H0", "m1", signer="B2"), keyend("x", "B2", concludes=True), end("E", "H0", ["n2"])], {},
     {"m1": OUT, "n2": (F, F, "K.key_removed")}),
    ("key_removed_after_end", "the key is removed after the end, with the kept rows in its past: they stay; a "
     "later row of that key is cut",
     [H0, M1, act("n1", "H0", "m1", signer="B2"), end("E", "H0", ["n1"]), keyend("x", "B2", names=["E", "n1"], concludes=True),
      act("n2", "H0", "n1", signer="B2")], {}, {"m1": KEPT, "n1": KEPT, "n2": (F, F, "K.key_removed")}),
    ("member_revokes_key_keeps_its_resignation", "the member evicts the key it resigned under, the eviction not "
     "naming the resignation: a key removal voids no end (it would undo the resignation and bring every row back), "
     "and the seat stays ended",
     [H0, M1, M2, end("R", "H0", ["m1"], "B2"), keyend("x", "B2", "B", concludes=True)], {},
     {"m1": KEPT, "m2": OUT}),
    ("key_revokes_itself_keeps_its_resignation", "the same where the key revokes itself",
     [H0, M1, M2, end("R", "H0", ["m1"], "B2"), keyend("x", "B2", "B2")], {},
     {"m1": KEPT, "m2": OUT}),
    ("room_count_cannot_remove_a_key", "a row of the key removal's shape signed by the room's count is no key "
     "removal: the room's count ends a seat, in its room, and cuts no row of the key",
     [H0, M1, act("n1", "H0", signer="B2"), keyend("x", "B2", COUNT), act("n2", "H0", "n1", signer="B2")], {},
     {"m1": (T, T, "no_end"), "n1": (T, T, "no_end"), "n2": (T, T, "no_end")}),
    ("room_removal_is_that_room_only", "the room's count removes the member in this room, holding nothing good: "
     "the member's rows under both keys in room r2 stand, and so do its later rows there",
     [H0, G0, M1, act("p1", "G0", room="r2"), act("p2", "G0", "p1", signer="B2", room="r2"), end("E", "H0"),
      act("p3", "G0", "p2", ["E"], room="r2")], {},
     {"m1": OUT, "p1": (T, T, "no_end"), "p2": (T, T, "no_end"), "p3": (T, T, "no_end")}),
    ("retraction_under_a_removed_key", "a retraction signed by a removed key, not in the removal's past, is not "
     "read: the kept row stays",
     [H0, M1, end("E", "H0", ["m1"]), act("w2", "H0", target="m1", compose="retract", signer="B2"),
      keyend("x", "B2", concludes=True)], {}, {"m1": KEPT, "w2": (F, F, "K.key_removed")}),
    # more than one room: each room is judged by its own rows; a key is one key in every room
    ("end_in_another_room", "the member's seat ends in this room; in room r2, where it sits on, its row counts "
     "and is in force",
     [H0, G0, M1, act("p1", "G0", room="r2"), end("E", "H0", ["m1"])], {},
     {"m1": KEPT, "p1": (T, T, "no_end")}),
    ("tip_in_another_room", "an end names a row of room r2 as a tip: a tip holds good rows of its own room only, "
     "and when r2's seat ends without it, the row is out",
     [H0, G0, M1, act("p1", "G0", room="r2"), end("E", "H0", ["m1", "p1"]), end("E2", "G0", [], room="r2")], {},
     {"m1": KEPT, "p1": OUT}),
    ("head_of_another_room", "a content row of this room naming a roster version of room r2 names no head of its "
     "room: no seat",
     [H0, G0, act("m1", "G0")], {}, {"m1": (F, F, "no_seat")}),
    ("retraction_from_another_room", "a retraction in room r2 of a row of this room is not read",
     [H0, G0, M1, act("w1", "G0", target="m1", compose="retract", room="r2")], {},
     {"m1": (T, T, "no_end"), "w1": (T, T, "no_end")}),
    ("ack_in_another_room", "the reader's line is the room's: an acknowledgement in room r2 leaves this room's "
     "end in force",
     [H0, H1, H2, G0, M1, end("E", "H0", ["m1"]), ack("k1", ["G0", "H2"], room="r2")], {}, {"m1": KEPT}),
    # review r79 (keys.py): a key removal is read only as a concluded act of the person's own key roster, or the
    # key's own revocation; and the reader keeps what it already took up
    ("secondary_evicts_primary_alone", "B2 alone signs a removal of B that does not conclude under the person's key "
     "roster (one key does not suffice): it cuts nothing, in either room",
     [H0, G0, M1, act("m2", "H0", "m1"), dict(act("g1", "G0"), room="r2"), act("s1", "H0", signer="B2"),
      keyend("k", "B", signer="B2", concludes=False)], {},
     {"m1": (T, T, "no_end"), "m2": (T, T, "no_end"), "g1": (T, T, "no_end"), "s1": (T, T, "no_end")}),
    ("counter_removal", "the same, and B's concluded removal of B2 names B2's row s1: B's rows stand, B2's later row "
     "is cut",
     [H0, M1, act("s1", "H0", signer="B2"), keyend("k", "B", signer="B2", concludes=False),
      keyend("k2", "B2", signer="B", names=("k", "s1"), concludes=True), act("s2", "H0", "s1", signer="B2")], {},
     {"m1": (T, T, "no_end"), "s1": (T, T, "no_end"), "s2": (F, F, "K.key_removed")}),
    ("self_revocation", "B revokes itself naming m1: needing no count, it is read; m2, not in its past, is cut",
     [H0, M1, act("m2", "H0", "m1"), keyend("k", "B", signer="B", names=("m1",), concludes=False)], {},
     {"m1": (T, T, "no_end"), "m2": (F, F, "K.key_removed")}),
    ("key_cut_after_reader_took_up", "the reader acknowledged m2 before it held the removal of B (the "
     "acknowledgement does not have the removal in its past): m2 stands for this reader; m3, which it never took "
     "up, is cut",
     [H0, M1, act("m2", "H0", "m1"), act("m3", "H0", "m2"), ack("a1", ["m2"]),
      keyend("k", "B", signer="B", names=("m1",))], {},
     {"m1": (T, T, "no_end"), "m2": (T, T, "no_end"), "m3": (F, F, "K.key_removed")}),
    ("key_cut_reader_held_the_removal", "the reader's acknowledgement has the removal in its past too: it took up m2 "
     "knowing the key was removed, and m2 is cut",
     [H0, M1, act("m2", "H0", "m1"), keyend("k", "B", signer="B", names=("m1",)), ack("a1", ["m2", "k"])], {},
     {"m1": (T, T, "no_end"), "m2": (F, F, "K.key_removed")}),
    # a key's own revocation naming nothing (the Constitution's ruling of review r82; review r83): the residual, and
    # no anchor but the reader's own line
    ("thief_revokes_naming_nothing", "a thief holding B2 revokes it naming nothing: B2's rows the reader had not taken "
     "up are out for this reader (the residual of the end rule)",
     [H0, M1, act("s1", "H0", signer="B2"), act("s2", "H0", "s1", signer="B2"), keyend("k", "B2", signer="B2")], {},
     {"m1": (T, T, "no_end"), "s1": (F, F, "K.key_removed"), "s2": (F, F, "K.key_removed")}),
    ("member_reply_anchors_nothing", "a co-member's reply to s1 keeps nothing: it cannot be told from a reply signed "
     "after the revocation that leaves it unnamed",
     [H0, M1, act("s1", "H0", signer="B2"), act("s2", "H0", "s1", signer="B2"), act("q1", "H0", "s1", ["s1"], signer="M"),
      keyend("k", "B2", signer="B2")], {},
     {"m1": (T, T, "no_end"), "s1": (F, F, "K.key_removed"), "s2": (F, F, "K.key_removed")}),
    ("anchor_colluding_reply", "review r83 row 1: the owner revokes B2 naming its last trusted row s1; the thief's "
     "forgeries f1, f2 are out, and a colluding co-member's reply to f2 that leaves the revocation unnamed keeps them out",
     [H0, act("s1", "H0", signer="B2"), act("f1", "H0", "s1", signer="B2"), act("f2", "H0", "f1", signer="B2"),
      keyend("k", "B2", signer="B2", names=("s1",)), act("q", "H0", "f2", ["f2"], signer="M")], {},
     {"s1": (T, T, "no_end"), "f1": (F, F, "K.key_removed"), "f2": (F, F, "K.key_removed")}),
    ("anchor_ordinary_row", "row 2: a co-member's ordinary row with f2 in its past keeps nothing",
     [H0, act("s1", "H0", signer="B2"), act("f1", "H0", "s1", signer="B2"), act("f2", "H0", "f1", signer="B2"),
      keyend("k", "B2", signer="B2", names=("s1",)), act("q", "H0", (), ["f2"], signer="M")], {},
     {"s1": (T, T, "no_end"), "f1": (F, F, "K.key_removed"), "f2": (F, F, "K.key_removed")}),
    ("anchor_sock_key", "row 3: the reply is by a key X the thief controls: it keeps nothing",
     [H0, act("s1", "H0", signer="B2"), act("f1", "H0", "s1", signer="B2"), act("f2", "H0", "f1", signer="B2"),
      keyend("k", "B2", signer="B2", names=("s1",)), act("q", "H0", "f2", ["f2"], signer="X")], {},
     {"s1": (T, T, "no_end"), "f1": (F, F, "K.key_removed"), "f2": (F, F, "K.key_removed")}),
    ("anchor_forged_retraction", "row 9: B2's forged retraction of B's m1, revoked, then replied to by a co-member: "
     "the retraction stays cut, so it is not read and m1 stands",
     [H0, M1, act("s1", "H0", signer="B2"), act("rt", "H0", "s1", ["m1"], signer="B2", compose="retract", target="m1"),
      keyend("k", "B2", signer="B2", names=("s1",)), act("q", "H0", "rt", ["rt"], signer="M")], {},
     {"m1": (T, T, "no_end"), "s1": (T, T, "no_end"), "rt": (F, F, "K.key_removed")}),
    # review r84 (revive.py): a key removal keeps what it names AND what lies behind it along `prev`
    ("revocation_keeps_prev_chain", "row 9: B revokes itself naming its newest trusted row b2, whose `prev` is b1 "
     "(b1 not in b2's names): both stand",
     [H0, act("b1", "H0"), act("b2", "H0", "b1"), keyend("k", "B", names=("b2",))], {},
     {"b1": (T, T, "no_end"), "b2": (T, T, "no_end")}),
    ("revocation_keeps_named_past", "row 10: the same where b2 also names b1: both stand",
     [H0, act("b1", "H0"), act("b2", "H0", "b1", ["b1"]), keyend("k", "B", names=("b2",))], {},
     {"b1": (T, T, "no_end"), "b2": (T, T, "no_end")}),
    ("second_revocation_names_f1", "row 7: a concluded second removal of B2 by B names f1, after the first named "
     "s1: s1 stands; f1 stays cut, since a row any removal cuts is cut (a later removal never uncuts, or a thief "
     "holding the key would revoke it again naming its forgeries)",
     [H0, act("s1", "H0", signer="B2"), act("f1", "H0", "s1", signer="B2"), keyend("k", "B2", signer="B2", names=("s1",)),
      keyend("k2", "B2", signer="B", names=("f1",), concludes=True)], {},
     {"s1": (T, T, "no_end"), "f1": (F, F, "K.key_removed")}),
    ("count_end_tip_after_revocation", "rows 1 and 2: the count's end names f1 as a tip; the revocation named s1: "
     "s1 is not cut, f1 is, and the walk from the tip does not pass through the cut f1",
     [H0, act("s1", "H0", signer="B2"), act("f1", "H0", "s1", signer="B2"), keyend("k", "B2", signer="B2", names=("s1",)),
      end("E", "H0", ["f1"], names=("k",))], {},
     {"s1": (T, F, "E2.forward"), "f1": (F, F, "K.key_removed")}),
    # review r85 (prevwalk.py): the walk stays in its room; and two residuals of the caller duty, stated as EDGE cases
    ("revocation_walk_stays_in_room", "row 5: s1's predecessor g0 is B2's row of room r2: the walk from s1 does not "
     "cross rooms, so g0, not in the removal's past, is cut",
     [H0, G0, dict(act("g0", "G0", signer="B2"), room="r2"), act("s1", "H0", "g0", signer="B2"),
      keyend("k", "B2", signer="B2", names=("s1",))], {},
     {"g0": (F, F, "K.key_removed"), "s1": (T, T, "no_end")}),
    ("EDGE_forgery_chained_by_the_device", "row 2, residual A: the honest device chained s1 onto the thief's f0 "
     "(s1's prev is f0); naming s1 keeps f0. The duty: name last trusted rows whose prev chains hold no foreign row",
     [H0, act("f0", "H0", signer="B2"), act("s1", "H0", "f0", signer="B2"), keyend("k", "B2", signer="B2", names=("s1",))],
     {}, {"f0": (T, T, "no_end"), "s1": (T, T, "no_end")}),
    ("EDGE_forgery_chained_through_the_other_key", "row 3, residual A: the chain from s1 runs through B's b1 to the "
     "thief's f0, and naming s1 keeps f0",
     [H0, act("f0", "H0", signer="B2"), act("b1", "H0", "f0", signer="B"), act("s1", "H0", "b1", signer="B2"),
      keyend("k", "B2", signer="B2", names=("s1",))], {},
     {"f0": (T, T, "no_end"), "b1": (T, T, "no_end"), "s1": (T, T, "no_end")}),
    ("EDGE_owner_names_the_thiefs_revocation", "row 7, residual B: the owner's revocation names the thief's, which "
     "names the forgery f1: a removal with another in its past inherits what that one names, so f1 stands. The duty: "
     "never name, or build on, the thief's revocation",
     [H0, act("s1", "H0", signer="B2"), act("f1", "H0", "s1", signer="B2"), keyend("kt", "B2", signer="B2", names=("f1",)),
      keyend("k", "B2", signer="B2", names=("s1", "kt"))], {},
     {"s1": (T, T, "no_end"), "f1": (T, T, "no_end")}),
    ("key_end_not_held", "the reader does not hold the removal of B2 (the caller places a key removal at commons, "
     "or in every room the key sits in): nothing is cut",
     [H0, M1, act("n1", "H0", signer="B2"), act("n2", "H0", "n1", signer="B2")], {},
     {"m1": (T, T, "no_end"), "n1": (T, T, "no_end"), "n2": (T, T, "no_end")}),
    ("key_removal_reaches_every_room", "a key removal is of the key, in every room: its later row in r2 is cut",
     [H0, G0, act("p1", "G0", signer="B2", room="r2"), keyend("x", "B2", concludes=True)], {}, {"p1": (F, F, "K.key_removed")}),
]


def orders(rows):
    """Every arrival order the door allows: a row arrives only after the rows it names."""
    ids = {r["id"] for r in rows}
    by = {r["id"]: r for r in rows}
    out = []

    def go(done, seq):
        if len(seq) == len(rows):
            out.append(list(seq)); return
        for r in rows:
            if r["id"] not in done and all(n in done or n not in ids for n in by[r["id"]]["names"]):
                done.add(r["id"]); seq.append(r["id"]); go(done, seq); seq.pop(); done.discard(r["id"])
    go(set(), [])
    return out


def check_cases():
    """Every case: the reference gives the hand-written answer, and the same in every arrival order."""
    problems = []
    for c in CASES:
        name, about, rows, params, want = c[:5]
        got = answers(rows, **params)
        for x, (cnt, frc, rule) in want.items():
            g = got.get(x)
            if g != {"counted": cnt, "in_force": frc, "rule": rule}:
                problems.append("%s: %s expected %s, reference %s" % (name, x, (cnt, frc, rule), g))
        if set(got) != set(want):
            problems.append("%s: acts %s, expectations for %s" % (name, sorted(got), sorted(want)))
        by = {r["id"]: r for r in rows}
        for o in orders(rows)[:200]:
            if answers([by[i] for i in o], **params) != got:
                problems.append("%s: order %s differs" % (name, o))
    return len(CASES), problems


def fixture():
    """The fixture, in the format of conferral_end.json: every case with its rows, parameters, arrival orders
    and every content row's answer."""
    _, problems = check_cases()
    assert not problems, problems
    cases = []
    for c in CASES:
        name, about, rows, params, want = c[:5]
        cases.append({"name": name, "about": about, "rows": rows, "merge": params.get("merge", "count_first"),
                      "orders": c[5] if len(c) > 5 else [[r["id"] for r in rows]],
                      "refused": None,
                      "answers": answers(rows, **params)})
    return {"about": "room content after a member's seat ends, where the end names the rows held good "
                     "(`trusted_through`): the Constitution's proposal of 2026-11-22 for CC 2.4.1.1, for persist "
                     "v62.0. Generated from models/causal_kernel/conferral_content.py; checked by "
                     "check_conferral_content.py. A PROPOSAL until the Constitution rules it",
            "roles": {"B": "a key of the member whose seat ends", "B2": "a second key of the same member",
                      "R": "the reader: its acknowledgements (`ack`) are its line",
                      "M": "a co-member: its rows are not this member's content and get no answer here",
                      "count": "a counted row (a roster version, a removal, a row adding tips)"},
            "merge": "whose tips are read: count_first (the reference's default), union (the proposal's third "
                     "point read literally) or count_first_self_union; see `rules`. The Constitution rules which",
            "refused": "null in every case here: every content row names its head",
            "rules": __doc__.split("Which ends count:")[1].strip(),
            "cases": cases}
