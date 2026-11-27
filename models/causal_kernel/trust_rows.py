"""
trust_rows.py: THE READER'S TRUST WALK FROM ROWS, and the issuer's standing (CC 4.4.3.34; CC 2.7.5).

An acceptance edge is a row: a `delegates_to` row bearing `trust:accepts:v1`, naming the authority it accepts (`dst`),
with `trust_classes` (absent: every class the charter declares) and `trust_depth`. Whose edge it is: its signer's, or,
where it speaks for another (`on_behalf`), that authority's, if the ruling (a) says the signer speaks for it.

    admission   an edge whose `trust_classes` is present and empty, unsorted or names a class twice is refused
                (`trust_accepts_classes_malformed`, charter.edge_refusal: the one place); one whose depth the ruling
                (c) refuses is refused (`trust_accepts_depth_malformed`). A refused edge is no edge.
    ended       an edge the ruling (d) holds ended (by default: a concluded withdrawal of it by its signer, held by the
                reader) is no edge.
    the walk    breadth first from the reader's own edges (signed by the reader); an onward hop only from an
                authority's own edges (ruling (a)); the classes intersect hop by hop; each key expanded again only
                with more budget than before, so a cycle is visited once; nothing is cached across reads; depth within
                the cap of five (CC 4.1.1).
    the issuer  a licence is honoured iff the walk reaches its authority for its class, the authority's record
                declares the class (charter.py), and the licence row is the authority's act (ruling (b)).

The four rulings are with the Constitution, and plug in through `Rulings`; `PENDING` is what this model reads until
they land. Where a ruling is pending the answer is UNDECIDED and says so, never a silent pass:
    (a) speaks_for(S, row, src)   whether edge `row` is `src`'s own: True, False, or a pending reason. PENDING: a key
                                  speaks for itself alone; for a community authority `authority_set_pending`.
    (b) issued_by(S, lic, auth)   whether licence `lic` is `auth`'s act. PENDING: a key authority's licence is the one
                                  it signs; a community authority's `issuer_standing_pending`.
    (c) depth(d)                  the depth an edge stating `d` walks with, or None (refused). PENDING: 0 to 5, else
                                  refused.
    (d) ended(S, row)             whether edge `row` is ended for the reader. PENDING: a concluded withdrawal of it by
                                  its signer is held.

    edges_of(S, rulings)          the admitted, live edges, each with its owner, or a pending reason
    reaches(edges, frm, c, b, a)  the breadth-first walk
    read_licence(S, reader, lic, own, supplied, now, rulings)  -> (honoured, reason)
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


def accepts(i, signer, dst, trust_classes=None, depth=0, names=(), on_behalf=None, bears=BEARS):
    """An acceptance edge as a row: `signer` (or `on_behalf`, where it speaks for another) accepts `dst`."""
    kw = {} if on_behalf is None else {"on_behalf": on_behalf}
    return CK.row(i, "delegates_to", signer, tuple(names), bears=bears, dst=dst,
                  trust_classes=None if trust_classes is None else tuple(trust_classes), trust_depth=depth, **kw)


def is_community(S, a):
    """`a` is a held, concluded community record: an authority whose authority set is ruling (a)'s."""
    return a in S.by and bool(S.C.get(a)) and ST.kind_of(S.by, a) in CH.CHARTER_KINDS


class Rulings:
    """The rulings (a) to (d), as this model reads them until the Constitution's land (PENDING)."""

    def speaks_for(self, S, r, src):
        if r["signer"] == src or "edge_any_signer" in MUT:
            return True
        if is_community(S, src):
            return "authority_set_pending"
        return False

    def issued_by(self, S, lic, auth):
        if lic["signer"] == auth or "issuer_unread" in MUT:
            return True
        if is_community(S, auth):
            return "issuer_standing_pending"
        return False

    def depth(self, d):
        if "depth_unread" in MUT:
            return min(d, HOP_CAP) if isinstance(d, int) else 0
        return d if isinstance(d, int) and 0 <= d <= HOP_CAP else None

    def ended(self, S, r):
        if "withdrawn_unread" in MUT:
            return False
        # (MUTATION withdraw_by_anyone: any withdrawal held, concluded or not and by any key, ends it)
        return any(w["kind"] == "withdraw" and w.get("target") == r["id"] and (
            (S.C.get(w["id"]) and w["signer"] == r["signer"]) or "withdraw_by_anyone" in MUT) for w in S.rows)


PENDING = Rulings()


def refusal(r, rulings=PENDING):
    """The admission's refusal of an acceptance edge row, or None."""
    e = CH.edge(r["signer"], r["dst"], r.get("trust_classes"))
    if "refusal_unread" not in MUT:
        why = CH.edge_refusal(e)
        if why is not None:
            return why
    if rulings.depth(r.get("trust_depth")) is None:
        return "trust_accepts_depth_malformed"
    return None


def edges_of(S, rulings=PENDING):
    """The acceptance edges the rows S holds give: (edge, None) for each admitted, live edge whose owner is decided,
    (edge, reason) for one whose owner a pending ruling leaves undecided. An edge's `src` is its owner."""
    out = []
    for r in S.rows:
        if r["kind"] != "delegates_to" or not S.C.get(r["id"]):
            continue
        if r.get("bears") != BEARS and "bears_unread" not in MUT:
            continue
        if refusal(r, rulings) is not None or rulings.ended(S, r):
            continue
        src = r.get("on_behalf", r["signer"])
        who = rulings.speaks_for(S, r, src)
        if who is False:
            continue
        e = dict(CH.edge(src, r["dst"], r.get("trust_classes"), rulings.depth(r.get("trust_depth"))), row=r["id"])
        out.append((e, None if who is True else who))
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


def read_licence(S, reader, lic, own=None, supplied=None, now=None, rulings=PENDING):
    """(honoured, reason) for licence row `lic` held in S, read by `reader` over the rows S holds. The reasons:
    `licence_class_not_trusted` (the authority's record does not declare the class), `licence_not_the_authoritys_act`
    or a pending reason of ruling (b) (`issuer_standing_pending`), `authority_not_reached` (the reader's walk does not
    reach the authority for the class), or a pending reason of ruling (a) (`authority_set_pending`) where only an
    edge whose owner is undecided would reach it."""
    r = S.by.get(lic)
    if r is None:
        return False, "not_held"
    a, c = r["authority"], r["licence_class"]
    if c not in CH.charters(S, own, supplied, now).get(a, frozenset()):
        return False, "licence_class_not_trusted"
    who = rulings.issued_by(S, r, a)
    if who is False:
        return False, "licence_not_the_authoritys_act"
    if who is not True:
        return False, who
    es = edges_of(S, rulings)
    decided = [e for e, why in es if why is None or "pending_silent" in MUT]
    if reaches(decided, reader, c, HOP_CAP, a):
        return True, None
    pending = sorted({why for _, why in es if why is not None})
    if pending and reaches([e for e, _ in es], reader, c, HOP_CAP, a):
        return False, pending[0]
    return False, "authority_not_reached"
