"""
charter.py: CHARTER COVERAGE for licensing authorities (CC 3.4.7; CC 4.4.3.12, 4.4.3.34), read from rows.

A licensing authority is an AFFILIATION: a community record of kind `affiliation` (its founding row's group kind,
seat.kind_of). Its charter is that record's own declared `licence_classes`; there is no separate charter row. "The
charter enumerates the licence classes the affiliation issues."

    the record in force   the charter is read at read: over the rows the READER holds, never at a licence's own
                          instant, so a class a later amendment drops stops matching every licence of it, those
                          issued before the amendment included.
    a version             a change of the affiliation's record (a counted offer of scope `record` over it, the act
                          record_change, seat.act_of) that concludes under the affiliation's declared protocol and
                          counts for the reader (the cut, the reader's line, built on: seat.Seats). A change below the
                          protocol concludes nothing and leaves the charter as it was. The acts table carries no
                          row for it yet: seat.PENDING_ACTS models it (cosigned_act, fixed). A record change is no
                          act against a member, so the outside countersign a one-seat affiliation's acts against a
                          member need (CC 4.4.3.12) is not asked of it.
    unstated              a version that states no `licence_classes` (a rename, a protocol) leaves the classes as
                          they were at its head.
    the wait              (the Constitution's derived reading) two version tips that differ wait: the classes
                          declared are those every tip lists, until a version names them all. A version naming
                          them all that states none keeps the classes in force at its head: the common ones.
    the reader's side     an acceptance edge admits the classes it lists (`trust_classes`), every class when it lists
                          none; the walk intersects the classes hop by hop (the crate's trust::reaches, written here as
                          the model's own walk). A licence is honoured where the reader's walk reaches its authority
                          for its class AND the authority's charter declares the class.
    a licence             a `licensure` row is admitted as a row whatever class it states; a class the charter does not
                          declare is honoured by no reader (`licence_class_not_trusted`). That is a reading, never a
                          refusal at the door.

The root's charter (the trust root bundle's `charter`: a scope list, sub_delegation) is another lane's fold. It meets
this one at `charters(..., supplied=...)`: a charter supplied for an authority is intersected with the one read from
rows, so the root's scope reaches the reading the same way.

    declared(S, aff, own)        the classes the affiliation's record in force declares for the reader, or None
    charters(S, own, supplied)   every affiliation held -> its declared classes, with the supplied charters met
    reaches(edges, frm, c, b, a) the trust walk
    honours(edges, reader, ch, auth, cls)
    read_licence(S, edges, reader, lic, own, supplied)  -> (honoured, reason)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import seat as ST  # noqa: E402

CK, K = ST.CK, ST.K
MUT = set()          # planted breaks, switched on by check_charter.py
HOP_CAP = 5          # CC 4.1.1: the traversal cap


def is_version(q, aff):
    """A change of affiliation `aff`'s record: a counted offer of scope `record` over it (the act record_change)."""
    return q["kind"] == "offer" and q.get("conf") == "group" and q.get("obj") == aff and q.get("scope") == "record" \
        and q.get("dissolved_at") is None


def states(q):
    """The row states its licence classes (a founding record always does: none listed is none declared)."""
    return q.get("licence_classes") is not None or q.get("obj") == q["id"]


def classes(q):
    return frozenset(q.get("licence_classes") or ())


def declared(S, aff, own=None, seats=None):
    """The classes affiliation `aff`'s record in force declares, over the rows S holds, for reader `own`: None where no
    concluded founding row of an affiliation is held (no charter, so no class is declared)."""
    g = S.by.get(aff)
    if g is None or not S.C.get(aff):
        return None
    if ST.kind_of(S.by, aff) != "affiliation" and "any_record_kind" not in MUT:
        return None
    Q = seats if seats is not None else ST.Seats(S, own=own)
    S = Q.S                                         # the rows as they conclude for this reader (seat.reader_state)
    rows = S.rows if "below_protocol_read" in MUT else S.Cs
    vs = [q for q in rows if is_version(q, aff)
          and ("below_protocol_read" in MUT or (Q.cut.counts(q) and q["id"] not in Q.stale))]
    if "one_seat_countersign" in MUT and len(ST.signers(g) & frozenset(g["to"])) == 1:
        vs = []                                     # MUTATION: a one-seat affiliation's record change needs a countersign
    if not vs:
        return classes(g)
    # the order among the versions, read over the concluded rows alone (as seat.protocol_record)
    by = {q["id"]: q for q in S.Cs}
    if "below_protocol_read" in MUT:
        by = dict(S.by)
    anc = {q["id"]: K.ancestors(by, q["id"]) for q in vs}
    memo = {}

    def at(v):
        """The classes in force at version v: its own where it states them; else those in force at its head."""
        if v["id"] in memo:
            return memo[v["id"]]
        if states(v) or "unstated_clears" in MUT:
            out = classes(v)
        else:
            out = in_force([q for q in vs if q["id"] in anc[v["id"]]])
        memo[v["id"]] = out
        return out

    def in_force(sub):
        if not sub:
            return classes(g)
        tips = [q for q in sub if not any(q["id"] in anc[x["id"]] for x in sub)]
        if "join_unread" in MUT:
            tips = sub                              # MUTATION: every version is a tip: a join decides nothing
        if "fork_first" in MUT:
            tips = [min(tips, key=lambda q: q["id"])]
        got = [at(t) for t in tips]
        if "fork_union" in MUT:
            return frozenset().union(*got)
        return frozenset.intersection(*got)

    if "at_founding" in MUT:
        return classes(g)
    return in_force(vs)


def charters(S, own=None, supplied=None):
    """Every affiliation whose founding row S holds and concludes -> the classes its record in force declares, for
    reader `own`; a charter supplied for an authority (the root's scope, another lane's fold) is met with it: the
    classes both declare. A supplied charter for an authority held here as no affiliation stands alone."""
    Q = ST.Seats(S, own=own)
    out = {}
    for g in S.Cs:
        if g["kind"] == "offer" and g.get("obj") == g["id"]:
            d = declared(S, g["id"], own, Q)
            if d is not None:
                out[g["id"]] = d
    for a, cs in (supplied or {}).items():
        out[a] = out[a] & frozenset(cs) if a in out else frozenset(cs)
    return out


# ---- the reader's walk (the crate's trust::reaches) ----------------------------------------------------------------
def edge(src, dst, trust_classes=None, depth=0):
    """An acceptance edge: `src` accepts `dst` as a licensor for `trust_classes` (absent or empty: every class the
    charter declares), with `depth` further hops past `dst`."""
    return {"src": src, "dst": dst, "classes": tuple(trust_classes or ()), "depth": depth}


def admits(e, c):
    if "absent_means_none" in MUT:
        return c in e["classes"]
    if "edge_classes_unread" in MUT:
        return True
    return not e["classes"] or c in e["classes"]


def reaches(edges, frm, c, budget, a):
    """The walk from `frm` with `budget` hops reaches authority `a` for class `c`: each key expanded with the greatest
    budget it has been reached with; an onward hop's budget is the lesser of what is left and the edge's own depth."""
    best, todo = {frm: budget}, [frm]
    while todo:
        k = todo.pop()
        b = best[k]
        if b == 0:
            continue
        for e in edges:
            if e["src"] != k:
                continue
            # MUTATION last_hop_only: an onward hop's classes are not read, only those of the hop that arrives
            if not (admits(e, c) or ("last_hop_only" in MUT and e["dst"] != a)):
                continue
            if e["dst"] == a:
                return True
            nb = min(b - 1, e["depth"])
            if nb > best.get(e["dst"], -1):
                best[e["dst"]] = nb
                todo.append(e["dst"])
    return False


def honours(edges, reader, ch, auth, cls):
    """The reader honours a licence of class `cls` issued by `auth`: its walk, within the cap, reaches `auth` for `cls`,
    and `auth`'s charter (`ch`: charters()) declares `cls`."""
    declares = "charter_unread" in MUT or cls in ch.get(auth, frozenset())
    return declares and reaches(edges, reader, cls, HOP_CAP, auth)


def licensure(i, signer, authority, cls, names=()):
    """A licence: of class `cls`, issued under `authority` (the affiliation's founding row)."""
    return CK.row(i, "licensure", signer, tuple(names), authority=authority, licence_class=cls)


def read_licence(S, edges, reader, lic, own=None, supplied=None):
    """(honoured, reason) for the licence row `lic` held in S, read by `reader` over every row S holds:
    `licence_class_not_trusted` where its authority's charter does not declare its class, `authority_not_reached`
    where the reader's walk does not reach the authority for it, `not_held` where S does not keep it."""
    r = S.by.get(lic)
    if r is None:
        return False, "not_held"
    T = S
    if "at_issuance" in MUT:                       # MUTATION: the charter read in the licence's own past
        sub = [q for q in S.rows if q["id"] in S.anc[lic]]
        T = CK.State(sub, {q["id"]: S.C.get(q["id"]) for q in sub})
    ch = charters(T, own, supplied)
    a, c = r["authority"], r["licence_class"]
    if not ("charter_unread" in MUT or c in ch.get(a, frozenset())):
        return False, "licence_class_not_trusted"
    if not reaches(edges, reader, c, HOP_CAP, a):
        return False, "authority_not_reached"
    return True, None


def state(rows):
    """The rows kept and concluded under the seat rule."""
    return CK.concluded(CK.kept(list(rows)), lambda r, P, past: ST.seat_rule(r, P, past))
