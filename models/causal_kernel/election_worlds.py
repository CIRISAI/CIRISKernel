"""
election_worlds.py: a world written before the election's opening row (the ruling of 2026-11-28), read with its
opening: for each election a legacy id names (the founding row, or a seating whose seat ended), the opening of the seat
end that id's vacancy is, signed by every member at its heads. A world that states its openings is read as written.
Used by the checks whose worlds hold an election only as a fixture (check_election's legacy cases among them); the
ruled election's own cases (check_election_close.py) state their openings.
"""
import seat as ST
CK = ST.CK
OBJ = "g"
RULE = lambda r, P, past: ST.seat_rule(r, P, past)


def opened(rows):
    """The election's opening (the ruling of 2026-11-28: the id is an `election_open` row) for a world written before
    it: for each election a ballot, decline or seating names by a legacy id (the founding row, or a seating whose
    seat ended), the opening of the seat end that id's vacancy is (the earliest end of its seat in the rows), signed by
    every member at its heads, its heads the newest counted changes in that end's past (the end itself where it is
    counted); and every row naming the legacy id names the opening instead. A world that states its openings is read
    as written."""
    if any(r["kind"] == "election_open" for r in rows): return list(rows)
    if not any(r["kind"] in ("ballot", "decline") or ST.is_election(r) for r in rows): return list(rows)
    # the openings depend on the set of rows, not their order: kept per set, applied to any order (arrival orders)
    key = frozenset(id(r) for r in rows)
    got = _MEMO.get(key)
    if got is None:
        work, done = list(rows), set()
        for _ in range(6):                 # a chain of elections: each opening once the seat before it has ended
            work, more = _open_once(work, done)
            if not more: break
        orig = {id(r) for r in rows}
        new = {r["id"]: r for r in work if id(r) not in orig}                  # renamed rows and openings, by id
        after = {}
        for i, r in enumerate(work):
            if r["kind"] == "election_open": after.setdefault(work[i - 1]["id"], []).append(r)
        got = _MEMO[key] = (new, after)
    new, after = got
    out = []
    for r in rows:
        out.append(new.get(r["id"], r) if r["kind"] != "election_open" else r)
        out += after.get(r["id"], [])
    return out


_MEMO = {}


def _open_once(rows, done):
    by = {r["id"]: r for r in rows}
    refs = sorted({r["of"] for r in rows if r.get("of") in by and (r["kind"] in ("ballot", "decline") or ST.is_election(r))
                   and r["of"] not in done})
    if not refs: return list(rows), False
    S = CK.concluded(CK.kept(list(rows)), RULE)
    past = lambda a, b: a in S.anc[b]
    ops, rename = [], {}
    for X in refs:
        e = by[X]
        if e["kind"] == "election_open": continue
        if e["id"] == OBJ:
            ends = [w for w in S.Cs if w["kind"] in ("withdraw", "unseat") and w.get("obj", OBJ) in (OBJ, None)
                    and ST.seat_end_slots(w, S.Cs, past, OBJ)]
            if not ends and not ST.id_seats(e): ends = [e]          # no duty seat: the founding row is the vacancy
        else:
            ends = [w for w in S.Cs if (w["kind"] == "withdraw" and w.get("target") == X) or
                    (w["kind"] == "unseat" and w.get("obj") == OBJ and e.get("to") and e["to"][0] in w.get("to", ())
                     and w.get("scope") == "moderate")]
        ends = [w for w in ends if not any(past(v["id"], w["id"]) for v in ends if v is not w)] or ends
        if not ends: continue
        # of concurrent ends: a counted end before a holder's lay-down (the counted end is the end); then the end the
        # election's own rows name most; then the earliest
        named = [n for r in rows if r.get("of") == X for n in r.get("names", ())]
        w = sorted(ends, key=lambda q: (q["kind"] != "unseat", -named.count(q["id"]), q["id"]))[0]
        P = [q for q in S.Cs if past(q["id"], w["id"])] + [w]
        byP = {q["id"]: q for q in P}
        acts = [q for q in P if q["id"] == OBJ or ST.change(q, OBJ, byP)]
        heads = tuple(sorted(q["id"] for q in acts if not any(past(q["id"], x["id"]) for x in acts)))
        mem = sorted(ST.members_at(P, past, OBJ, heads, "member") - ST.members_at(P, past, OBJ, heads, ST.AGENT))
        if not mem: continue
        oid = "op" if X == OBJ else "op_" + X
        ops.append((w["id"], ST.election_open(oid, mem[0], OBJ, w["id"], heads, cosigners=tuple(mem[1:]))))
        rename[X] = oid
        done.add(X)
    out = []
    for r in rows:
        if r.get("of") in rename and (r["kind"] in ("ballot", "decline") or ST.is_election(r)):
            oid = rename[r["of"]]
            r = dict(r, of=oid, names=tuple(r["names"]) + ((oid,) if oid not in r["names"] else ()))
            if ST.is_election(r) and not r.get("head") and any(o["id"] == oid and o["cites"][0] in o["head"] for _, o in ops):
                # a seating names the newest counted changes (H4): where the opening's end is itself a counted change
                # (a recall), that end, which the opening holds
                hs = next(o for _, o in ops if o["id"] == oid)["head"]
                r = dict(r, head=tuple(hs), names=tuple(r["names"]) + tuple(h for h in hs if h not in r["names"]))
        out.append(r)
        out += [o for end, o in ops if end == r["id"]]
    return out, bool(ops)


