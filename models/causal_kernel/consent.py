"""
consent.py: THE CONSENT PEER SET, over the causal kernel and seat.py (CC 3.3.7, CC 2.7.5, CC 5.2, CC 6.1.5).

A `consent:replication:v1` grant is one signer's DIRECTED row to one named peer, naming the classes it moves
(`attestation_prefixes`). It moves those classes and nothing else (CC 5.2: "names the class it moves and moves that
class and nothing else"). It is Seats-shaped: an offer by one key to another, standing until withdrawn, with a
class-containment check on top. G -> P and P -> G are two grants, each on its own; a bilateral peering is both
in force.

Rows (dicts of causal_kernel.row):
    grant      kind "grant": signer G, `peer` P (the one key of subject_key_ids), `classes` (the
               attestation_prefixes, a CC 2.6.1.2 set: sorted ascending, deduplicated), `at` (asserted_at), `until`
               (valid_until, optional: the term), `fed` (cohort_scope is federation; default True).
    withdraws  kind "withdraws" (or "recants"): signer, `of` the grant it retracts, whole (CC 3.3.7 Revocation).
    announce   kind "announce": a node's announcement of itself (CC 5.4.6), signer the node.
    revoke     key_end.revoke: a key's own revocation, `ra` its revoked_after.
    seat rows  the owner binding (seat.py: an offer of scope `owner` over the node, and the owner's acceptance).
    any other  a node's own row, read only as a place in the causal order (`at_row`).

Concluded (RULE, the row and its past):
    a grant concludes when it is well formed: one peer, and its classes non-empty strings, sorted ascending with
        no duplicate (CC 3.3.7: "sorted ascending + deduplicated", so two holders agree byte for byte); and, placed
        at federation scope, only where both its signer and its peer have announced themselves in its past ("A
        grant that an unannounced node signs or is named in is never placed at federation"; it is held by the two
        nodes and no other, `fed` False).
    a withdrawal concludes when the row it names is a concluded grant and its signer is one of three keys (the
        Constitution, reading CC 3.3.7 whole): the grant's signer G; the peer P the grant names (CC 2.4.1.1 rule 2,
        "stop sending to me"); or G's one owner by the owner binding, read over the withdrawal's own past (the
        owner's word governs). Any other key's withdrawal concludes nothing.
    every other row as seat.seat_rule concludes it.

Derived, read AT A ROW (`at_row`; None reads every held row, the reader's whole holding):
    the past     at_row and the rows in its causal past.
    voice        the grant's signature counts against each of its signer's own revocations (r86: a key end is a
                 cut) where the grant is in the revocation's past, or the grant's instant is before the
                 revocation's revoked_after and the grant does not have the revocation in its past (a row that names
                 the end is after it, whatever instant it states). Any other grant of the key is no grant.
    the fold     the default fold, CAUSAL FIRST (the Constitution on CC 3.5.1): of one signer's grants to one peer in
                 the past that carry a voice, those no other of them has in its past; of those (concurrent), the
                 latest asserted_at, then the lowest id. A grant with an earlier one in its past is later whatever
                 either states. An earlier grant is replaced (a narrowing is a supersedes with the narrower set),
                 and a withdrawal or the term of the latest revives no earlier one (CC 3.3.7: on revoke the node
                 "MUST cease replicating the named prefixes to P").
    withdrawn    the end is a cut (CC 2.4.1.1, as ruled 2026-11-21): a held withdrawal of the grant ends it at every
                 row that is not in the withdrawal's past. So a withdrawal in at_row's past, and one concurrent with
                 at_row, end it there; only a row the withdrawal comes after still reads the grant.
    term         `until` read at the caller's instant `now`, half-open (lib covers_at): in force while now < until.
                 A grant with a term and no instant given is not in force.
    in force     the fold's winner, in the past, with a voice, not withdrawn, inside its term.

    peer_set(principal)   the peers named by the principal's grants in force at at_row.
    bilateral(a, b)       a's grant to b and b's grant to a both in force.
    principals(node)      the node itself (CC 3.3.7: G is the granting node) and its ONE owner by the owner binding
                          read over at_row's past (seat.Seats.one: two live owners is none, CC 3.2): the owner's
                          grant for one of its own nodes is the second form.
    may_send(node, peer, class)  the grant in force, from a principal of the node to that peer, whose classes
                          cover the class; else None.
    covers(classes, c)    an entry ending in ':' is a CC 3.1 namespace prefix and covers every class it starts
                          (trailing colon significant); any other entry is a corpus class name and covers itself only.

Planted breaks (MUT), each must change a case of check_consent.py:
    classes_unread          a grant moves every class
    prefix_no_colon         an entry covers by raw prefix, colon or not
    fold_earliest           the earliest grant wins the fold, not the latest
    fold_highest_id         an instant tie goes to the highest id
    fold_instant_first      the fold reads the instant before the past (the reading before the ruling)
    fold_live_only          the fold picks among live grants only: a withdrawn or lapsed latest revives the one before
    withdraw_any_signer     a withdrawal by any key ends the grant
    withdraw_signer_only    only the grant's signer withdraws it (the reading before the ruling)
    withdraw_owner_now      the owner who may withdraw read over every held row, not the withdrawal's past
    withdraw_by_past        a withdrawal ends the grant only at rows that have it in their past (concurrent unread)
    term_unread             the term is not read
    term_closed             the term read as closed: in force at until itself
    owner_any               any key's grant moves the node's rows
    owner_two_one           with two live owners, either owner's grant moves the node's rows
    revoked_unread          a revoked key's grant keeps its voice
    revoked_backdated       a grant that has its signer's revocation in its past keeps its voice by a back-dated instant
    future_grant            a grant not in at_row's past is read
    federation_unannounced  a grant at federation scope concludes with an unannounced party
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import seat as ST  # noqa: E402

CK = ST.CK
K = CK.K
MUT = set()
ENDS = ("withdraws", "recants")


# ---- rows ------------------------------------------------------------------------------------------------
def grant(id, signer, peer, classes, at, names=(), until=None, fed=True):
    return CK.row(id, "grant", signer, names, peer=peer, classes=tuple(classes), at=at, until=until, fed=fed)


def withdraws(id, signer, of, names=(), kind="withdraws"):
    return CK.row(id, kind, signer, tuple(names) + ((of,) if of not in names else ()), of=of)


def announce(id, node, names=()):
    return CK.row(id, "announce", node, names)


def note(id, signer, names=()):
    """A node's own row: a place in the causal order to read at."""
    return CK.row(id, "note", signer, names)


def binding(id, node, owner, names=()):
    """The owner binding (CC 3.2): the node's offer of its `owner` seat to the owner, and the owner's acceptance."""
    return [ST.offer(id, node, owner, "owner", node, "self", names), ST.accept("a" + id, owner, id)]


# ---- concluded -------------------------------------------------------------------------------------------
def well_formed(r):
    cs = r["classes"]
    return (isinstance(r.get("peer"), str) and bool(r["peer"]) and all(isinstance(c, str) and c for c in cs)
            and list(cs) == sorted(set(cs)) and bool(cs))


def _owner_over(rows, key):
    """key's one owner over a set of concluded rows (seat.Seats.one: none, or two, is None)."""
    return ST.Seats(CK.State(rows, {r["id"]: True for r in rows})).one("owner", key)


def may_withdraw(g, k, P):
    """Whether key k may withdraw grant g, by the rows P (the withdrawal's concluded past)."""
    if "withdraw_any_signer" in MUT:
        return True
    if k == g["signer"]:
        return True
    if "withdraw_signer_only" in MUT:
        return False
    return k == g["peer"] or _owner_over(P, g["signer"]) == k


def consent_rule(r, P, past):
    k = r["kind"]
    if k == "grant":
        if not well_formed(r):
            return False
        if r.get("fed", True) and "federation_unannounced" not in MUT:
            announced = {q["signer"] for q in P if q["kind"] == "announce"}
            return r["signer"] in announced and r["peer"] in announced
        return True
    if k in ENDS:
        g = next((q for q in P if q["id"] == r.get("of")), None)
        if g is None or g["kind"] != "grant":
            return False
        return may_withdraw(g, r["signer"], P)
    return True


RULE = lambda r, P, past: ST.seat_rule(r, P, past, other=consent_rule)


def state(rows):
    S = CK.concluded(CK.kept(list(rows)), RULE)
    if "withdraw_owner_now" in MUT:     # PLANT: the owner who may withdraw read over every held row
        C = dict(S.C)
        for w in S.rows:
            if w["kind"] in ENDS and not C[w["id"]]:
                g = S.by.get(w["of"])
                if g is not None and g["kind"] == "grant" and C.get(g["id"]) \
                        and _owner_over([q for q in S.rows if C[q["id"]]], g["signer"]) == w["signer"]:
                    C[w["id"]] = True
        S = CK.State(S.rows, C)
    return S


def arrived(order):
    if "withdraw_owner_now" in MUT:
        return state(order)
    return CK.arrive(list(order), RULE)


# ---- derived ---------------------------------------------------------------------------------------------
def _past(S, at_row):
    """The ids at at_row and in its past; every held id where at_row is None."""
    if at_row is None:
        return frozenset(S.by)
    return frozenset(S.anc[at_row]) | {at_row}


def _in(S, a, b):
    """a is b or in b's past."""
    return a == b or a in S.anc[b]


def covers(classes, c):
    if "classes_unread" in MUT:
        return True
    if "prefix_no_colon" in MUT:
        return any(c.startswith(e) for e in classes)
    return any(c.startswith(e) if e.endswith(":") else c == e for e in classes)


def voice(S, g):
    """The grant's signature counts against each of its signer's own revocations (r86: a key end is a cut)."""
    if "revoked_unread" in MUT:
        return True
    for v in K.sel(S.Cs, kind="revoke"):
        if v["signer"] != g["signer"] or v["key"] != g["signer"]:
            continue
        if _in(S, g["id"], v["id"]):
            continue
        after = v["id"] in S.anc[g["id"]] and "revoked_backdated" not in MUT   # it names the end: after it
        if after or g.get("at") is None or not g["at"] < v["ra"]:
            return False
    return True


def withdrawn(S, g, at_row):
    for w in S.Cs:
        if w["kind"] in ENDS and w["of"] == g["id"]:
            if at_row is None:
                return True
            if "withdraw_by_past" in MUT:
                if _in(S, w["id"], at_row):
                    return True
            elif not (at_row != w["id"] and at_row in S.anc[w["id"]]):
                return True
    return False


def in_term(g, now):
    u = g.get("until")
    if u is None or "term_unread" in MUT:
        return True
    if now is None:
        return False
    return now <= u if "term_closed" in MUT else now < u


def _grants(S, at_row):
    past = frozenset(S.by) if "future_grant" in MUT else _past(S, at_row)
    return [g for g in K.sel(S.Cs, kind="grant") if g["id"] in past and voice(S, g)]


def _instant_key(g):
    """The order among concurrent grants: the latest instant, then the lowest id (larger key wins)."""
    at = -g["at"] if "fold_earliest" in MUT else g["at"]
    return (at, g["id"]) if "fold_highest_id" in MUT else (at, tuple(-ord(ch) for ch in g["id"]) + (1,))


def fold(S, group):
    """The default fold over one signer's rows on one target: causal first, then the instant, then the lowest id."""
    if not group:
        return None
    if "fold_instant_first" not in MUT:
        group = [g for g in group if not any(q is not g and g["id"] in S.anc[q["id"]] for q in group)]
    return max(group, key=_instant_key)


def winners(S, at_row=None, now=None):
    """The default fold for each (signer, peer)."""
    groups = {}
    for g in _grants(S, at_row):
        if "fold_live_only" in MUT and (withdrawn(S, g, at_row) or not in_term(g, now)):
            continue
        groups.setdefault((g["signer"], g["peer"]), []).append(g)
    return {k: fold(S, gs) for k, gs in groups.items()}


def in_force(S, g_id, at_row=None, now=None):
    """Whether grant g_id is in force at at_row (None: over every held row), at the caller's instant now."""
    g = S.by.get(g_id)
    if g is None or g["kind"] != "grant" or not S.C.get(g_id):
        return False
    w = winners(S, at_row, now).get((g["signer"], g["peer"]))
    return w is not None and w["id"] == g_id and not withdrawn(S, g, at_row) and in_term(g, now)


def grants_in_force(S, principal, at_row=None, now=None):
    return [g for (s, _), g in sorted(winners(S, at_row, now).items())
            if s == principal and not withdrawn(S, g, at_row) and in_term(g, now)]


def peer_set(S, principal, at_row=None, now=None):
    """The peers named by the principal's grants in force at at_row."""
    return frozenset(g["peer"] for g in grants_in_force(S, principal, at_row, now))


def bilateral(S, a, b, at_row=None, now=None):
    """A bilateral peering: a's grant to b and b's grant to a, both in force."""
    return b in peer_set(S, a, at_row, now) and a in peer_set(S, b, at_row, now)


def _sub(S, at_row):
    """The state of at_row's past, with the conclusions the whole state gives (a row reads only its past)."""
    ids = _past(S, at_row)
    return CK.State([r for r in S.rows if r["id"] in ids], {i: c for i, c in S.C.items() if i in ids})


def owner(S, node, at_row=None):
    """The node's one owner by the owner binding over at_row's past (None with none, or with two)."""
    return ST.Seats(_sub(S, at_row)).one("owner", node)


def principals(S, node, at_row=None):
    if "owner_any" in MUT:
        return frozenset(g["signer"] for g in K.sel(S.Cs, kind="grant"))
    if "owner_two_one" in MUT:
        hs = ST.Seats(_sub(S, at_row)).holders("owner", node)
        return frozenset({node}) | frozenset(hs)
    o = owner(S, node, at_row)
    return frozenset({node} | ({o} if o is not None else set()))


def may_send(S, node, peer, row_class, at_row=None, now=None):
    """The grant under which node may send peer a row of row_class at at_row, or None."""
    for p in sorted(principals(S, node, at_row)):
        for g in grants_in_force(S, p, at_row, now):
            if g["peer"] == peer and covers(g["classes"], row_class):
                return g["id"]
    return None


def replication_set(S, node, addressed, at_row=None, now=None):
    """Edge's fan-out: the operator-addressed peers that are in the consent peer set of a principal of the node."""
    ps = frozenset().union(*(peer_set(S, p, at_row, now) for p in principals(S, node, at_row)))
    return frozenset(addressed) & ps
