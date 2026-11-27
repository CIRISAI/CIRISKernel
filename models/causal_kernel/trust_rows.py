"""
trust_rows.py: THE READER'S TRUST WALK FROM ROWS, and the issuer's standing (CC 4.4.3.34; CC 4.5.4; CC 2.7.5), with
the Constitution's rulings of 2026-11-27 on (a) the authority set, (b) the issuer's standing, (c) the depth and (d)
withdrawal by ancestry.

An acceptance edge is a row: a `delegates_to` row bearing `trust:accepts:v1`, naming the authority it accepts (`dst`),
with `trust_classes` (absent: every class the charter declares) and `trust_depth`. Its owner is its signer, or the
authority it speaks for (`on_behalf`).

    (a) the authority set   an edge is its owner's where its signatures are the owner's authority set, read over the
                            edge's own causal past: for a person (a key), the key itself or any live key of its roster
                            (scope `key` over it); for a community, CC 4.5.4's authority_set(C), counted as a duty
                            conferral is (the acts row accept / trust_edge / community -> duty_confer, held in
                            seat.PENDING_ACTS until rc23-next has it): a strict majority of all its live duty holders,
                            never fewer than two where there are two or more, or a lone holder alone. There is no
                            members' fallback: a community with no duty holder is LOCKED (CC 4.5.4 (v)) and signs no
                            edge. A community record of any kind (an affiliation included) reads that row.
    admission               a `trust_classes` list that is present must be non-empty, sorted and name no class twice
                            (`trust_accepts_classes_malformed`, charter.edge_refusal); `trust_depth` absent reads as 0,
                            0 to 5 is admitted, any other is refused (`trust_accepts_depth_out_of_range`). A refused
                            edge is no edge.
    (d) ended               an edge is ended by a concluded withdrawal of it whose signatures are its owner's authority
                            set over the withdrawal's own past; for the reader's own edge that is the reader's removal,
                            which revokes at once, for that reader.
    the walk                breadth first from the reader's own edges; onward only from an authority's own edges; the
                            classes intersect hop by hop; a key expanded again only with more budget than before, so a
                            cycle is visited once; nothing is cached; within the cap of five (CC 4.1.1).
    (b) the issuer          a licence is the authority's act where, over the licence's own causal past, its emitter's
                            key IS the authority (a person is one voice across its keys: any live key of its roster),
                            or holds a `license` seat over it (a delegation whose chain resolves to the authority:
                            seat.Seats.stands; over a community the seat is conferred and withdrawn by its duty
                            holders' count, the acts rows seat_confer / seat_withdraw of scope `license`, held in
                            seat.PENDING_ACTS), or, for a community, the licence is cosigned by its quorum under its
                            DECLARED consensus_protocol (no bootstrap). Any other is testimony, out of the fold:
                            `licensure_delegator_not_authority`; a locked community's own licence is
                            `licensure_authority_locked`. A licence naming a link that is not held is not kept: it
                            waits.
    (d) by ancestry         the standing is judged at issuance, over the issuance's own past, never at receipt: a
                            withdrawal of a link in that past stops it; a withdrawal concurrent with the issuance holds
                            it out of force for a reader that holds the withdrawal (`licensure_link_withdrawn`); a
                            withdrawal with the issuance in its own past reaches nothing back.

A licence is honoured iff the walk reaches its authority for its class, the authority's record declares the class
(charter.py), and the licence is the authority's act in force.

    refusal(r)                    the admission's refusal of an edge row, or None
    edges_of(S)                   the admitted, live edges, each with its owner as `src`
    reaches(edges, frm, c, b, a)  the breadth-first walk
    standing(S, lic)              None, or why licence `lic` is not its authority's act in force
    read_licence(S, reader, lic, own, supplied, now)  -> (honoured, reason)
"""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import charter as CH  # noqa: E402

ST, CK = CH.ST, CH.CK
MUT = set()          # planted breaks, switched on by check_trust_rows.py
BEARS = "trust:accepts:v1"
HOP_CAP = CH.HOP_CAP


def accepts(i, signer, dst, trust_classes=None, depth=None, names=(), on_behalf=None, bears=BEARS, cosigners=()):
    """An acceptance edge as a row: `signer` (with `cosigners`, for `on_behalf` where it speaks for another) accepts
    `dst`. `depth` None: trust_depth absent."""
    kw = {} if on_behalf is None else {"on_behalf": on_behalf}
    if depth is not None:
        kw["trust_depth"] = depth
    if cosigners:
        kw["cosigners"] = tuple(cosigners)
    return CK.row(i, "delegates_to", signer, tuple(names), bears=bears, dst=dst,
                  trust_classes=None if trust_classes is None else tuple(trust_classes), **kw)


def is_community(S, a):
    """`a` is a held, concluded community record (a community, an infrastructure community, an affiliation)."""
    return a in S.by and bool(S.C.get(a)) and ST.kind_of(S.by, a) in CH.CHARTER_KINDS


def past_state(S, r):
    """The rows in row r's own causal past, with their conclusions: where its authority is judged."""
    if "judged_at_read" in MUT:
        return S
    sub = [q for q in S.rows if q["id"] in S.anc[r["id"]]]
    return CK.State(sub, {q["id"]: S.C.get(q["id"]) for q in sub})


def counted(yes, n):
    """A strict majority of n, never fewer than two where n is two or more; a lone holder alone (CC 4.5.4 (iv))."""
    if n == 0:
        return False
    if n == 1:
        return yes == 1
    return yes >= 2 and 2 * yes > n


def locked(T, community):
    """CC 4.5.4 (v): a community with no live duty holder is LOCKED: it signs no NEW onward acceptance edge, confers no
    license seat (the duty holders' count, seat.py, takes none) and issues no licence of its own, until an election
    seats a holder. A license seat's holder is no duty holder and keeps no room from locking. A license seat, or an
    edge, from before the lock stands until its term ends (seat_term, edge_term) or it is withdrawn, by ancestry
    (ended_for_reader). An affiliation is never locked:
    with no officer (its authority body) it is DISSOLVED (CC 4.4.3.12), and signs nothing either. seat.authority_body is the one source of
    whose keys these are."""
    return "lock_unread" not in MUT and not ST.authority_body(ST.Seats(T), community)


def seat_term(T, k, a, t):
    """Whether a license seat over `a` that seats `k` covers instant `t` (the licence's own), read as the crate's
    Seats::stands_at_instant reads it: a live seat of `k` giving `license` over `a` (any chain, its root any) whose
    seating offer's own term covers `t` (`asserted_at <= t < expires_at`; a missing bound does not limit), with the
    fold at tips. With `t` None (the licence states no instant), only a seat whose offer states no term: no instant
    means no term met (the r73 attack)."""
    if "term_unread" in MUT:
        return True
    Q = ST.Seats(T)
    fold = Q.tips_fold("license", a)
    if fold is not None and k not in fold:
        return False
    for rec in Q.recs:
        if rec["k"] == k and rec["obj"] == a and Q._has(rec, "license") and Q._member(rec):
            o = T.by[rec["offer"]]
            lo, hi = o.get("asserted_at"), o.get("expires_at")
            if t is None:
                if hi is None or "untimed_term_met" in MUT:
                    return True
            elif (lo is None or lo <= t) and (hi is None or t < hi):
                return True
    return False


def declared_count(T, signers, community):
    """(1) The cosignatures `signers` meet `community`'s DECLARED consensus_protocol in force over the rows T (a row's
    own past), counted over its members, as the seat rule counts a protocol row: the protocol's own numbers and
    weights, never the row's."""
    mem = ST.protocol_body(ST.Seats(T), community)
    if "quorum_fixed_majority" in MUT:
        return counted(len(signers & mem), len(mem))
    rec = ST.protocol_record({q["id"]: q for q in T.Cs}, community)
    if rec is None:
        return False
    pr = ST.community_rule(rec.get("consensus_protocol"), rec.get("need"), rec.get("weights"))
    if pr is None:
        return False
    kind, m, _n = pr
    need = m if kind == "quorum" else rec.get("need") if kind == "weighted" else None
    weights = rec.get("weights") if kind == "weighted" else None
    return ST.count_of("P:" + kind, True, (), mem, signers & mem, need, weights, signed=signers)


def is_the_authority(T, k, a):
    """(3) The licence's emitter `k` IS authority `a`: a person is one voice across its keys, so any live key of its
    roster (scope `key` over it, over the licence's own past) is the person."""
    if k == a:
        return True
    return a not in T.by and "roster_issuer_unread" not in MUT and k in ST.Seats(T).holders("key", a)


def speaks_for(T, signers, src):
    """(a) The keys `signers` are `src`'s authority set over the rows T (a row's own past)."""
    if "edge_any_signer" in MUT:
        return True
    if src in T.by:
        if not is_community(T, src):
            return False
        # an affiliation's edge is its officers' act under its declared protocol (the officers ruling: the acts row
        # accept / trust_edge / affiliation -> cosigned_act, held in seat.PENDING_ACTS)
        if ST.kind_of(T.by, src) == "affiliation" and "affiliation_edge_duty_count" not in MUT:
            rule = None if "pending_unread" in MUT else ST.policy_for("accept", "trust_edge", "affiliation")
            return rule is not None and rule[0] == ("cosigned_act",) and declared_count(T, signers, src)
        # the acts row binds the count (MUTATION pending_unread: the table without the pending row)
        rule = None if "pending_unread" in MUT else ST.policy_for("accept", "trust_edge", "community")
        if rule is None or rule[0] != ("duty_confer",):
            return False
        Q = ST.Seats(T)
        if "duty_unread" in MUT:
            return counted(len(signers & Q.holders("member", src)), len(Q.holders("member", src)))
        # (2) no members' fallback: a community with no duty holder is locked, and signs no edge
        if locked(T, src):
            return False
        duty = ST.authority_body(Q, src)
        return counted(len(signers & duty), len(duty))
    # a person: the key itself, or a live key of its roster
    if src in signers:
        return True
    return "roster_unread" not in MUT and bool(signers & ST.Seats(T).holders("key", src))


def object_of(S, q):
    """The group or key a row acts over: its object, the authority it speaks for, or a licence's authority; an
    acceptance's, its offer's object."""
    if q["kind"] == "accept" and q.get("of") in S.by:
        return S.by[q["of"]].get("obj")
    return q.get("obj") or q.get("on_behalf") or q.get("authority")


def is_end(q):
    """An end the reader reads over its own rows: a withdrawal (a lay-down, a resignation, a conferrer's withdrawal, an
    edge's withdrawal), an unseat (a counted removal or withdrawal of a seat, a key's eviction from a roster), or a
    change of a group's record (an amendment of its protocol or of what it declares)."""
    return q["kind"] in ("withdraw", "unseat") or (q["kind"] == "offer" and q.get("conf") == "group"
                                                   and q.get("scope") == "record")


def ends_keys(S, e):
    """The (key, object) seats end `e` ends: an unseat's keys over its object; a withdrawal by a seated key of its own
    seat, or by the conferrer of an offer's seats (a counted offer's conferrer is its count, and its signer ends
    nothing alone); a change of the record ends no seat."""
    if e["kind"] == "unseat":
        return {(k, e.get("obj")) for k in e.get("to", ())}
    if e["kind"] != "withdraw":
        return set()
    t = S.by.get(e.get("target"))
    if t is None:
        return set()
    if t["kind"] == "accept":
        return {(e["signer"], object_of(S, t))}
    if t["kind"] != "offer":
        return set()
    if e["signer"] in t.get("to", ()):
        return {(e["signer"], t.get("obj"))}
    if e["signer"] in ST.signers(t) and t.get("conf") != "group":
        return {(k, t.get("obj")) for k in t.get("to", ())}
    return set()


def cut_state(S, rows):
    """The rows `rows` with every row an end among them cuts taken out: a row signed by a key whose seat over the row's
    object the end ends, concurrent with that end (neither in the other's past). Rows in an end's past stand (nothing
    reaches back); rows after it are judged at their own past."""
    ends = [e for e in rows if is_end(e) and S.C.get(e["id"])]
    cut = set()
    if "cut_unread" not in MUT:
        for e in ends:
            ks = ends_keys(S, e)
            if not ks:
                continue
            for q in rows:
                if q["id"] == e["id"] or q["id"] in S.anc[e["id"]] or e["id"] in S.anc[q["id"]]:
                    continue
                o = object_of(S, q)
                if any(k in ST.signers(q) and o == ob for k, ob in ks):
                    cut.add(q["id"])
    kept = [q for q in rows if q["id"] not in cut]
    return CK.State(kept, {q["id"]: S.C.get(q["id"]) for q in kept})


def ended_for_reader(S, r, read=True):
    """THE END RULE (the r73 attack), the one read of ends for every path (the emitter, the quorum, the seat, the edge):
    an END cuts every row of what it ends that is not in the end's past. The rows row `r`'s authority is judged over:
    its own past, with every end in it cutting the rows concurrent with it (`read` False: its existence at issuance);
    with `read`, every end the READER holds concurrent with `r` too (a key's eviction, an unseat, a lay-down and so the
    lock, an edge's withdrawal, an amendment of the record), each cutting what it ends there. Dissolution is read the
    same way (read_licence)."""
    if "judged_at_read" in MUT:
        return S
    past = S.anc[r["id"]]
    rows = [q for q in S.rows if q["id"] in past]
    if read and "ends_unread" not in MUT:
        rows += [q for q in S.rows if S.C.get(q["id"]) and is_end(q) and q["id"] not in past and q["id"] != r["id"]
                 and r["id"] not in S.anc[q["id"]]]
    return cut_state(S, rows)


def depth_of(r):
    """(c) The depth an edge walks with: absent reads as 0; 0 to 5; None (refused) otherwise."""
    d = r.get("trust_depth", 0 if "depth_absent_refused" not in MUT else None)
    if "depth_unread" in MUT and isinstance(d, int):
        return max(0, min(d, HOP_CAP))
    return d if isinstance(d, int) and not isinstance(d, bool) and 0 <= d <= HOP_CAP else None


def refusal(r):
    """The admission's refusal of an acceptance edge row, or None."""
    if "refusal_unread" not in MUT:
        why = CH.edge_refusal(CH.edge(r["signer"], r["dst"], r.get("trust_classes")))
        if why is not None:
            return why
    if depth_of(r) is None:
        return "trust_accepts_depth_out_of_range"
    return None


def owner(r):
    return r.get("on_behalf", r["signer"])


def ended(S, r):
    """(d) A concluded withdrawal of edge r whose signatures are its owner's authority set over its own past."""
    if "withdrawn_unread" in MUT:
        return False
    return any(w["kind"] == "withdraw" and w.get("target") == r["id"] and S.C.get(w["id"])
               and ("withdraw_by_anyone" in MUT or all(speaks_for(T, ST.signers(w), owner(r)) for T in (
                   ended_for_reader(S, w, False), ended_for_reader(S, w))))
               for w in S.rows)


def edge_term(r, t):
    """An edge's own term (`asserted_at <= t < expires_at`, as a license seat's) covers instant `t`: the caller's
    instant, or the licence's own; with no instant, only an edge that states no term."""
    if "edge_term_unread" in MUT:
        return True
    lo, hi = r.get("asserted_at"), r.get("expires_at")
    if t is None:
        return hi is None
    return (lo is None or lo <= t) and (hi is None or t < hi)


def edges_of(S, t=None):
    """The acceptance edges the rows S holds give at instant `t`: each admitted, live edge its owner's authority set
    signed (over its own past and with every end the reader holds), within its term, with its owner as `src`."""
    out, Q = [], ST.Seats(S)
    for r in S.rows:
        if r["kind"] != "delegates_to" or not S.C.get(r["id"]):
            continue
        # a dissolved authority's own edges end with its record (CC 4.4.3.12): no walk hops through it
        if owner(r) in S.by and Q.dissolved(owner(r)) and "dissolved_edges_kept" not in MUT:
            continue
        if r.get("bears") != BEARS and "bears_unread" not in MUT:
            continue
        if refusal(r) is not None or ended(S, r) or not edge_term(r, t):
            continue
        # its owner's authority set over its own past, and with every end the reader holds (ended_for_reader)
        if not all(speaks_for(T, ST.signers(r), owner(r))
                   for T in (ended_for_reader(S, r, False), ended_for_reader(S, r))):
            continue
        out.append(dict(CH.edge(owner(r), r["dst"], r.get("trust_classes"), depth_of(r)), row=r["id"]))
    return out


def reaches(edges, frm, c, budget, a):
    """The walk from `frm` with `budget` hops reaches authority `a` for class `c`: breadth first, each key expanded
    again only with more budget than before (a cycle once); an onward hop's budget is the lesser of what is left and
    the edge's own depth; an edge admits `c` where its trust_classes are absent or list it."""
    best, todo = {frm: budget}, collections.deque([frm])
    while todo:
        k = todo.popleft()
        b = best[k]
        if b == 0:
            continue
        for e in edges:
            if e["src"] != k or not CH.admits(e, c):
                continue
            if e["dst"] == a:
                return True
            nb = min(b - 1, e["depth"])
            if nb > best.get(e["dst"], -1):
                best[e["dst"]] = nb
                todo.append(e["dst"])
    return False


INSTANT_BEFORE_PAST = "licensure_instant_before_its_past"


def issuance(T, r):
    """The licence `r`'s standing over the rows T: None, `licensure_delegator_not_authority` (no standing: testimony),
    `licensure_authority_locked` (a locked community's quorum) or INSTANT_BEFORE_PAST (an instant earlier than a row
    it cites: a row cannot claim to predate what it names)."""
    a, k, t = r["authority"], r["signer"], r.get("asserted_at")
    if t is not None and "instant_unread" not in MUT and any(
            q.get("asserted_at") is not None and q["asserted_at"] > t for q in T.rows):
        return INSTANT_BEFORE_PAST
    if is_the_authority(T, k, a) or "issuer_unread" in MUT:
        return None
    if is_community(T, a) and "quorum_unread" not in MUT:
        # (2) a locked community issues no licence of its own: its quorum's licence is `licensure_authority_locked`
        # (a license seat conferred before the lock is read below, as any)
        if declared_count(T, ST.signers(r), a):
            if not locked(T, a):
                return None
            if not ST.Seats(T).stands(k, "license", a):
                return "licensure_authority_locked"
    if "chain_unread" in MUT or not ST.Seats(T).stands(k, "license", a) or not seat_term(T, k, a, t):
        return "licensure_delegator_not_authority"
    return None


def standing(S, lic):
    """(b), (d): None where licence `lic` is its authority's act in force for the reader holding S; else the reason it
    CONCLUDES NOTHING in the authority's fold (never a refusal: the licence row is admitted, and the reason reads other
    rows, CC 2.7.3). Its existence is judged over its own past (ended_for_reader with read False): issuance()'s reason.
    Then every end the reader holds is read over the reader's rows (ended_for_reader): a licence that stood and is cut
    so is `licensure_link_withdrawn`, or `licensure_authority_locked` where the end locks its community."""
    r = S.by[lic]
    why = issuance(ended_for_reader(S, r, False), r)
    if why is not None:
        return why
    why = issuance(ended_for_reader(S, r), r)
    if why is None:
        return None
    return why if why == "licensure_authority_locked" else "licensure_link_withdrawn"


def read_licence(S, reader, lic, own=None, supplied=None, now=None):
    """(honoured, reason) for licence row `lic` held in S, read by `reader` over the rows S holds:
    `lapsed` (its authority is dissolved: a licence that stood at issuance, its class declared and its standing
    held over its own past, stands and reads lapsed for every later use), `licence_class_not_trusted` (the authority's record does not declare the class), the standing's reason
    (standing()), or `authority_not_reached` (the reader's walk does not reach the authority for the class)."""
    r = S.by.get(lic)
    if r is None:
        return False, "not_held"
    a, c = r["authority"], r["licence_class"]
    # a dissolved authority (CC 4.4.3.12, "What stands after dissolution"): an issued licence stands, its authority
    # judged at issuance, and reads `lapsed` for every later use; one with no standing over its own past is testimony
    # (the issuance judgement first, over the licence's own past: its standing, then its class; only a licence that
    # stood then reads `lapsed`. MUTATION lapsed_class_unread: the class is not judged at issuance)
    if a in S.by and is_community(S, a) and ST.Seats(S).dissolved(a) and "lapsed_unread" not in MUT:
        why = standing(S, lic)
        if why is not None:
            return False, why
        if "lapsed_class_unread" not in MUT and \
                c not in CH.charters(past_state(S, r), own, supplied, now).get(a, frozenset()):
            return False, "licence_class_not_trusted"
        return False, "lapsed"
    if c not in CH.charters(S, own, supplied, now).get(a, frozenset()):
        return False, "licence_class_not_trusted"
    why = standing(S, lic)
    if why is not None:
        return False, why
    if not reaches(edges_of(S, now if now is not None else r.get("asserted_at")), reader, c, HOP_CAP, a):
        return False, "authority_not_reached"
    return True, None
