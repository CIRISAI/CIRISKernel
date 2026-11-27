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
                            never fewer than two where there are two or more, or a lone holder alone; the members' count
                            where no duty holder is left. A community record of any kind (an affiliation included) reads
                            that row.
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
                            key IS the authority, or holds a `license` seat over it (a delegation whose chain resolves
                            to the authority: seat.Seats.stands), or, for a community, the licence is cosigned by its
                            quorum (a strict majority of its members, never fewer than two where there are two or more:
                            no bootstrap). Any other is testimony, out of the fold: `licensure_delegator_not_authority`.
                            A licence naming a link that is not held is not kept: it waits.
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


def speaks_for(T, signers, src):
    """(a) The keys `signers` are `src`'s authority set over the rows T (a row's own past)."""
    if "edge_any_signer" in MUT:
        return True
    if src in T.by:
        if not is_community(T, src):
            return False
        # the acts row binds the count (MUTATION pending_unread: the table without the pending row)
        rule = None if "pending_unread" in MUT else ST.policy_for("accept", "trust_edge", "community")
        if rule is None or rule[0] != ("duty_confer",):
            return False
        Q = ST.Seats(T)
        duty = frozenset() if "duty_unread" in MUT else Q.holders("duty", src)
        if duty:
            return counted(len(signers & duty), len(duty))
        if "members_fallback_unread" in MUT:
            return False
        mem = Q.holders("member", src)
        return counted(len(signers & mem), len(mem))
    # a person: the key itself, or a live key of its roster
    if src in signers:
        return True
    return "roster_unread" not in MUT and bool(signers & ST.Seats(T).holders("key", src))


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
               and ("withdraw_by_anyone" in MUT or speaks_for(past_state(S, w), ST.signers(w), owner(r)))
               for w in S.rows)


def edges_of(S):
    """The acceptance edges the rows S holds give: each admitted, live edge its owner's authority set signed, with its
    owner as `src`."""
    out = []
    for r in S.rows:
        if r["kind"] != "delegates_to" or not S.C.get(r["id"]):
            continue
        if r.get("bears") != BEARS and "bears_unread" not in MUT:
            continue
        if refusal(r) is not None or not speaks_for(past_state(S, r), ST.signers(r), owner(r)) or ended(S, r):
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


def standing(S, lic):
    """(b), (d): None where licence `lic` is its authority's act in force for the reader holding S; else
    `licensure_delegator_not_authority` (testimony: no standing over its own past) or `licensure_link_withdrawn` (a
    withdrawal concurrent with it, held, ends a link of its standing)."""
    r = S.by[lic]
    a, k = r["authority"], r["signer"]
    if k == a or "issuer_unread" in MUT:
        return None
    T = past_state(S, r)
    if is_community(T, a) and "quorum_unread" not in MUT:
        mem = ST.Seats(T).holders("member", a)
        if counted(len(ST.signers(r) & mem), len(mem)):
            return None
    if "chain_unread" in MUT or not ST.Seats(T).stands(k, "license", a):
        return "licensure_delegator_not_authority"
    if "concurrent_unread" in MUT:
        return None
    # (d) the withdrawals the reader holds that are concurrent with the issuance, read with its own past
    conc = [w for w in S.rows if w["kind"] == "withdraw" and S.C.get(w["id"]) and w["id"] not in S.anc[lic]
            and lic not in S.anc[w["id"]] and w["id"] != lic]
    if conc:
        rows = T.rows + conc
        T2 = CK.State(rows, {q["id"]: S.C.get(q["id"]) for q in rows})
        if not ST.Seats(T2).stands(k, "license", a):
            return "licensure_link_withdrawn"
    return None


def read_licence(S, reader, lic, own=None, supplied=None, now=None):
    """(honoured, reason) for licence row `lic` held in S, read by `reader` over the rows S holds:
    `licence_class_not_trusted` (the authority's record does not declare the class), the standing's reason
    (standing()), or `authority_not_reached` (the reader's walk does not reach the authority for the class)."""
    r = S.by.get(lic)
    if r is None:
        return False, "not_held"
    a, c = r["authority"], r["licence_class"]
    if c not in CH.charters(S, own, supplied, now).get(a, frozenset()):
        return False, "licence_class_not_trusted"
    why = standing(S, lic)
    if why is not None:
        return False, why
    if not reaches(edges_of(S), reader, c, HOP_CAP, a):
        return False, "authority_not_reached"
    return True, None
