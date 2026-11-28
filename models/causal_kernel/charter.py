"""
charter.py: CHARTER COVERAGE for licensing authorities (CC 3.4.7; CC 4.4.3.12, 4.4.3.34), read from rows.

"Anyone may be an authority under their own key, a community included." A community's charter is its record's own
`licence_classes`: each a class and its `legal_weight` (true or false). There is no separate charter row. "The
charter enumerates the licence classes the affiliation issues." An AFFILIATION is a community record whose
`declared_cohort` is `affiliations` (seat.kind_of); charter coverage reads `licence_classes` from any community record
(a community, an infrastructure community, an affiliation), and a community declaring a class with legal weight takes
on the affiliation's duties for it, whatever its declared_cohort. A family's record, an accord's and a self roster's are
no charter.

    the record in force   the charter is read at read: over the rows the READER holds, never at a licence's own
                          instant, so a class a later amendment drops stops matching every licence of it, those
                          issued before the amendment included.
    a version             a change of the community's record (a counted offer of scope `record` over it, the act
                          record_change, seat.act_of) that concludes under the record's protocol and counts for the
                          reader (the cut, the reader's line, built on: seat.Seats). A change below the protocol
                          concludes nothing and leaves the charter as it was. A record change is no act against a
                          member, so the outside countersign a one-seat affiliation's acts against a member need
                          (CC 4.4.3.12) is not asked of it.
    whole                 a version is the whole record: one that states no `licence_classes` declares none.
    the wait              (the Constitution's derived reading) two version tips that differ wait: the classes
                          declared are those every tip lists, until a version names them all. A class is listed
                          with its legal weight, and the pair is what tips must share (one function, meet()).
    dissolved             a dissolved group declares nothing (seat.Seats.dissolved: a concluded dissolution, or the
                          lapse of the last deciding seat, the no-signer dissolution). A record's own stated end
                          (`dissolves_at`) is read against the caller's clock (`now`), where it gives one: a version
                          whose end has passed declares nothing.
    the reader's side     an acceptance edge admits the classes it lists (`trust_classes`), every class when it lists
                          none (absent). Present, the list is non-empty, sorted and has no class twice; any other list
                          is refused at admission (`trust_accepts_classes_malformed`, edge_refusal()), so such an edge
                          is no edge. The walk intersects the classes hop by hop. A licence is honoured where the
                          reader's walk reaches its authority for its class AND the authority's charter declares it.
    a licence             a `licensure` row is admitted as a row whatever class it states; a class the charter does not
                          declare is honoured by no reader (`licence_class_not_trusted`). That is a reading, never a
                          refusal at the door.

The root's charter (the trust root bundle's `charter`: a scope list, sub_delegation) is another lane's fold. It meets
this one at `charters(..., supplied=...)`: a charter supplied for an authority is intersected with the one read from
rows, so the root's scope reaches the reading the same way.

    declared(S, aff, own, now)   the (class, legal_weight) pairs the record in force declares for the reader, or None
    charters(S, own, supplied, now)  every community held -> the classes it declares, with the supplied charters met
    edge_refusal(e)              None, or the admission's refusal of an acceptance edge
    reaches(edges, frm, c, b, a) the trust walk, over the edges admitted
    honours(edges, reader, ch, auth, cls)
    read_licence(S, edges, reader, lic, own, supplied, now)  -> (honoured, reason)
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
CHARTER_KINDS = ("community", "infrastructure", "affiliation")   # the community records: each may be an authority


def is_version(q, aff):
    """A change of community `aff`'s record: a counted offer of scope `record` over it (the act record_change)."""
    return q["kind"] == "offer" and q.get("conf") == "group" and q.get("obj") == aff and q.get("scope") == "record" \
        and q.get("dissolved_at") is None


def classes(q, now=None):
    """The (class, legal_weight) pairs a record version lists: none where it states none (a version is the whole
    record), and none once its own stated end (`dissolves_at`) is at or before `now`."""
    if now is not None and q.get("dissolves_at") is not None and now >= q["dissolves_at"] \
            and "dissolves_at_unread" not in MUT:
        return frozenset()
    out = frozenset((c, bool(w)) for c, w in (q.get("licence_classes") or ()))
    if "weight_unread" in MUT:
        out = frozenset((c, False) for c, _ in out)
    return out


def meet(sets):
    """The pairs every tip lists (the wait). MUTATION fork_union: those any lists."""
    if "fork_union" in MUT:
        return frozenset().union(*sets)
    return frozenset.intersection(*sets)


def declared(S, aff, own=None, now=None, seats=None):
    """The (class, legal_weight) pairs community `aff`'s record in force declares, over the rows S holds, for reader
    `own` at the caller's instant `now` (None: no clock is read): None where no concluded founding row of a community
    record is held (no charter, so no class is declared); empty where the group is dissolved."""
    g = S.by.get(aff)
    if g is None or not S.C.get(aff):
        return None
    kind = ST.kind_of(S.by, aff)
    if not (kind == "affiliation" or (kind in CHARTER_KINDS and "community_unread" not in MUT)
            or (kind == "family" and "family_read" in MUT)):
        return None
    Q = seats if seats is not None else ST.Seats(S, own=own)
    if Q.dissolved(aff) and "dissolved_declares" not in MUT:
        return frozenset()
    S = Q.S                                         # the rows as they conclude for this reader (seat.reader_state)
    rows = S.rows if "below_protocol_read" in MUT else S.Cs
    vs = [q for q in rows if is_version(q, aff)
          and ("below_protocol_read" in MUT or (Q.cut.counts(q) and q["id"] not in Q.stale))]
    if "one_seat_countersign" in MUT and len(ST.signers(g) & frozenset(g["to"])) == 1:
        vs = []                                     # MUTATION: a one-seat affiliation's record change needs a countersign
    if not vs or "at_founding" in MUT:
        return classes(g, now)
    # the order among the versions, read over the concluded rows alone (as seat.protocol_record)
    by = dict(S.by) if "below_protocol_read" in MUT else {q["id"]: q for q in S.Cs}
    anc = {q["id"]: K.ancestors(by, q["id"]) for q in vs}

    def at(v):
        if states(v):
            return classes(v, now)
        # MUTATION unstated_keeps: a version stating none keeps the classes in force at its head
        sub = [q for q in vs if q["id"] in anc[v["id"]]]
        return in_force(sub) if sub else classes(g, now)

    def states(v):
        return "unstated_keeps" not in MUT or v.get("licence_classes") is not None

    def in_force(sub):
        tips = [q for q in sub if not any(q["id"] in anc[x["id"]] for x in sub)]
        if "join_unread" in MUT:
            tips = sub                              # MUTATION: every version is a tip: a join decides nothing
        if "fork_first" in MUT:
            tips = [min(tips, key=lambda q: q["id"])]
        return meet([at(t) for t in tips])

    return in_force(vs)


def charters(S, own=None, supplied=None, now=None):
    """Every community whose founding row S holds and concludes -> the classes its record in force declares, for reader
    `own` at `now`; a charter supplied for an authority (the root's scope, another lane's fold) is met with it: the
    classes both declare. A supplied charter for an authority held here as no community stands alone."""
    Q = ST.Seats(S, own=own)
    out = {}
    for g in S.Cs:
        if g["kind"] == "offer" and g.get("obj") == g["id"]:
            d = declared(S, g["id"], own, now, Q)
            if d is not None:
                out[g["id"]] = frozenset(c for c, _ in d)
    for a, cs in (supplied or {}).items():
        out[a] = out[a] & frozenset(cs) if a in out else frozenset(cs)
    return out


# ---- the reader's walk (the crate's trust::reaches) ----------------------------------------------------------------
def edge(src, dst, trust_classes=None, depth=0):
    """An acceptance edge: `src` accepts `dst` as a licensor for `trust_classes` (None: absent, every class the charter
    declares; a list: those), with `depth` further hops past `dst`."""
    return {"src": src, "dst": dst, "classes": None if trust_classes is None else tuple(trust_classes), "depth": depth}


def edge_refusal(e):
    """The admission's refusal of an acceptance edge, or None: a `trust_classes` list that is present must be non-empty,
    sorted and name no class twice (CC 4.4.3.34); any other is `trust_accepts_classes_malformed`, and the edge is no
    edge. THE ONE PLACE the empty list is read."""
    cs = e["classes"]
    if cs is None:
        return None
    if "empty_edge_admits_all" in MUT and not cs:
        return None
    if not cs or any(a >= b for a, b in zip(cs, cs[1:])):
        return "trust_accepts_classes_malformed"
    return None


def admits(e, c):
    if "absent_means_none" in MUT:
        return e["classes"] is not None and c in e["classes"]
    if "edge_classes_unread" in MUT:
        return True
    return e["classes"] is None or not e["classes"] or c in e["classes"]


def reaches(edges, frm, c, budget, a):
    """The walk from `frm` with `budget` hops reaches authority `a` for class `c`, over the edges admitted: each key
    expanded with the greatest budget it has been reached with; an onward hop's budget is the lesser of what is left
    and the edge's own depth."""
    edges = [e for e in edges if edge_refusal(e) is None]
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
    """A licence: of class `cls`, issued under `authority` (the community's founding row)."""
    return CK.row(i, "licensure", signer, tuple(names), authority=authority, licence_class=cls)


def read_licence(S, edges, reader, lic, own=None, supplied=None, now=None):
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
    ch = charters(T, own, supplied, now)
    a, c = r["authority"], r["licence_class"]
    if not ("charter_unread" in MUT or c in ch.get(a, frozenset())):
        return False, "licence_class_not_trusted"
    if not reaches(edges, reader, c, HOP_CAP, a):
        return False, "authority_not_reached"
    return True, None


def state(rows):
    """The rows kept and concluded under the seat rule."""
    return CK.concluded(CK.kept(list(rows)), lambda r, P, past: ST.seat_rule(r, P, past))
