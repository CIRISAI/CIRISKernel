"""
consent.py: THE CONSENT PEER SET, over the causal kernel and seat.py (CC 3.3.7, CC 2.7.5, CC 5.2, CC 6.1.5).

A `consent:replication:v1` grant is one signer's DIRECTED row to one named peer, naming the classes it moves
(`attestation_prefixes`). It moves those classes and nothing else (CC 5.2: "names the class it moves and moves that
class and nothing else"). It is Seats-shaped: an offer by one key to another, standing until withdrawn, with a
class-containment check on top. G -> P and P -> G are two grants, each on its own; a bilateral peering is both
in force. A grant PERMITS and never obliges: a node may always send less, with no row.

Rows (dicts of causal_kernel.row):
    grant      kind "grant": signer G, `peer` P (the one key of subject_key_ids), `classes` (the
               attestation_prefixes, a CC 2.6.1.2 set: sorted ascending, deduplicated), `at` (asserted_at), `until`
               (valid_until, optional: the term), `fed` (cohort_scope is federation; default True).
    withdraws  kind "withdraws" (or "recants"): signer, `of` the grant it retracts, whole (CC 3.3.7 Revocation).
    announce   kind "announce": a node's announcement of itself (CC 5.4.6), signer the node.
    key lane   key_end rows (records, rotations, a key's own revocation), concluded by key_end.RULE in the same
               causal order: the key view reads them.
    seat rows  the owner binding (seat.py: an offer of scope `owner` over the node, and the owner's acceptance), and
               the self rosters the person map reads.
    any other  a node's own row, read only as a place in the causal order (`at_row`).

Concluded (RULE, the row and its past):
    a grant concludes when it is well formed: one peer, and its classes non-empty strings, sorted ascending with
        no duplicate (CC 3.3.7: "sorted ascending + deduplicated", so two holders agree byte for byte).
    a withdrawal concludes when the row it names is a concluded grant. WHO may withdraw is derived (below).
    the key lane as key_end.RULE concludes it; every other row as seat.seat_rule concludes it.

Derived, read AT A ROW (`at_row`; None reads every held row, the reader's whole holding):
    the past     at_row and the rows in its causal past. An at_row that is not held reads nothing.
    voice        THE KEY VIEW (key_end.counts_by, the end rule every count reads: a key end is a cut): the grant's
                 signer's signature counts only where the grant is in the past of each of the key's ends
                 (revocation, rotation), or taken up on the reader's own line before it held the end, or part of a
                 count final by acknowledgement. A stated instant never helps a grant concurrent with an end. The
                 reader, its final counts and the self roster are the caller's (`kv`; default: no reader).
    placement    a grant at federation scope is a grant only where its signer and its peer each have an announcement
                 in its past whose signature counts by the key view ("A grant that an unannounced node signs or is
                 named in is never placed at federation"). A grant held between the two (`fed` False) reads no
                 announcement: its placement, holding it between the two nodes and serving it to no other, is the
                 replication layer's (Edge's duty).
    the fold     THE ONE DEFAULT FOLD (fold_default, the twin of derived::fold_default): causal first, and a row
                 beats every row something in its own past beat (r97 CF1: a fork cannot revive a beaten branch);
                 of the rows left, the latest asserted_at, then the lowest id.
    withdrawn    the end is a cut (CC 2.4.1.1, as ruled 2026-11-21): a held withdrawal that counts ends the grant at
                 every row that is not in the withdrawal's past.
    who withdraws  ONE RULE (the Constitution, A3): may_withdraw(w, g) where, over w's past,
                 - w's signer is g's signer AS A PERSON: the same key, or a live key of the same person (seat.rep_of,
                   the person map), so another device of the granting person withdraws a thief's grant;
                 - w's signer is A NAMED PARTY (CC 2.4.1.1 rule 2): the peer ("stop sending to me"), or a node the
                   grant is FOR (a node whose one owner is g's signer's person), where it is not the signer;
                 - w's signer's person OWNS g's signer (seat.Seats.owner, the one owner reading).
                 The two arms that stand on an ownership are cut by its END (the end rule): a held row that ends
                 that ownership and is concurrent with w voids w (r97 F1, F3: a former owner cannot withdraw by
                 leaving its own end out of the withdrawal's past).
    term         `until` read at the caller's instant `now`, half-open (lib covers_at): in force while now < until.
                 A grant with a term and no instant given is not in force.
    in force     the fold's winner, in the past, with a voice, placed, not withdrawn, inside its term.
    caller duty  `now` is the caller's instant for the term only (as charter's edge terms read it): nodes agree on an
                 answer with a term only where they read it at the same now.
    the owner    read at the reading row: a grant an owner made before it owned the node moves the node's rows once
                 the binding is in the reading row's past (the owner's grant stands on the owner's word, not on the
                 binding at its signing).

    peer_set(principal)   the peers named by the principal's grants in force at at_row.
    bilateral(a, b)       a's grant to b and b's grant to a both in force.
    principals(node)      the node itself (CC 3.3.7: G is the granting node) and its ONE owner, seat.Seats.owner over
                          at_row's past (the one owner reading: two live owners is none, CC 3.2; a re-binding ends the
                          binding it has in its past): the owner's grant for one of its own nodes is the second form.
    may_send(node, peer, class)  the grant in force, from a principal of the node to that peer, whose classes
                          cover the class; else None.
    covers(classes, c)    an entry ending in ':' is a CC 3.1 namespace prefix and covers every class it starts
                          (trailing colon significant); any other entry is a corpus class name and covers itself only.

The residual, stated: a person with one key, whose key is stolen and then revoked, has no other device to withdraw a
grant the thief made that a reader took up; the peer, and a node the grant is for, still may (A3).

Planted breaks (MUT), each must change a case of check_consent.py:
    classes_unread          a grant moves every class
    prefix_no_colon         an entry covers by raw prefix, colon or not
    fold_earliest           the earliest grant wins the fold, not the latest
    fold_highest_id         an instant tie goes to the highest id
    fold_instant_first      the fold reads the instant before the past (the reading before the ruling)
    fold_inherit_unread     a row beats only the rows in its own past, not those its past beat (r97 CF1)
    fold_live_only          the fold picks among live grants only: a withdrawn or lapsed latest revives the one before
    withdraw_any_signer     a withdrawal by any key ends the grant
    withdraw_signer_only    only the grant's signing key withdraws it
    withdraw_person_unread  the signer read as a key, not a person: another device of the person cannot withdraw
    withdraw_node_unread    a node the grant is for is no named party
    withdraw_owner_now      the owner who may withdraw read over every held row, not the withdrawal's past
    ownership_end_unread    an ownership's end does not cut a concurrent withdrawal by that owner
    withdraw_by_past        a withdrawal ends the grant only at rows that have it in their past (concurrent unread)
    term_unread             the term is not read
    term_closed             the term read as closed: in force at until itself
    owner_any               any key's grant moves the node's rows
    owner_two_one           with two live owners, either owner's grant moves the node's rows
    revoked_unread          a revoked key's grant keeps its voice (the key view unread)
    voice_wrong_key         the key view asked about the peer's key, not the grant's signer's
    withdrawn_none_unread   read over every held row (at_row None), a withdrawal ends nothing
    future_grant            a grant not in at_row's past is read
    federation_unannounced  a grant at federation scope is placed with an unannounced party
    announcement_unviewed   an announcement counts without the key view
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import seat as ST  # noqa: E402
import key_end as KE  # noqa: E402

CK = ST.CK
K = CK.K
MUT = set()
ENDS = ("withdraws", "recants")
SEAT_KINDS = ("offer", "accept", "withdraw", "unseat")


# ---- rows ------------------------------------------------------------------------------------------------
def grant(id, signer, peer, classes, at=None, names=(), until=None, fed=True):
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
    return (r.get("peer") is not None and all(isinstance(c, str) and c for c in cs)
            and list(cs) == sorted(set(cs)) and bool(cs))


def consent_rule(r, P, past):
    k = r["kind"]
    if k == "grant":
        return well_formed(r)
    if k in ENDS:
        g = next((q for q in P if q["id"] == r.get("of")), None)
        return g is not None and g["kind"] == "grant"
    return True


KEY_LANE = ("rec", "att", "edge", "revoke")


def RULE(r, P, past):
    if r["kind"] in KEY_LANE:
        return KE.RULE(r, P, past)
    return ST.seat_rule(r, P, past, other=consent_rule)


def state(rows):
    return CK.concluded(CK.kept(list(rows)), RULE)


def arrived(order):
    return CK.arrive(list(order), RULE)


# ---- the readings consent takes from the seat model: one each ---------------------------------------------
def _rows_before(S, rid, inclusive=False):
    """The concluded rows in rid's past (with rid where `inclusive`)."""
    anc = S.anc[rid]
    return [q for q in S.Cs if q["id"] in anc or (inclusive and q["id"] == rid)]


def owner_over(rows, key):
    """key's one owner over a set of concluded rows: THE owner reading, seat.Seats.owner."""
    return ST.Seats(CK.State(rows, {r["id"]: True for r in rows})).owner(key)


def person_over(rows, key):
    """The person key `key` speaks for over a set of concluded rows: THE person map, seat.rep_of (None: none)."""
    return ST.rep_of(list(rows), key)


def ownership_ends(S, node, owner):
    """The held rows that end `owner`'s ownership of `node`: one with `owner` the node's owner over its past and not
    over its past with it (a withdrawal of the binding, a re-binding, a second binding that makes two owners)."""
    return [e for e in S.Cs if e["kind"] in SEAT_KINDS
            and owner_over(_rows_before(S, e["id"]), node) == owner
            and owner_over(_rows_before(S, e["id"], True), node) != owner]


def _uncut(S, w, node, owner):
    """THE END RULE on an ownership: withdrawal w, standing on `owner` owning `node`, is cut by any end of that
    ownership concurrent with it (an end in w's past already ended it there; one after w leaves w standing)."""
    if "ownership_end_unread" in MUT:
        return True
    return all(e["id"] in S.anc[w["id"]] or w["id"] in S.anc[e["id"]] for e in ownership_ends(S, node, owner))


def may_withdraw(S, w, g):
    """ONE RULE (the Constitution, A3): the signer as a person, any named party, or the owner over the signer."""
    if "withdraw_any_signer" in MUT:
        return True
    k = w["signer"]
    if k == g["signer"]:
        return True
    if "withdraw_signer_only" in MUT:
        return False
    rows = S.Cs if "withdraw_owner_now" in MUT else _rows_before(S, w["id"])
    pw, pg = person_over(rows, k), person_over(rows, g["signer"])
    if pw is not None and pw == pg and "withdraw_person_unread" not in MUT:
        return True
    if k == g["peer"]:
        return True
    o = owner_over(rows, k)                                  # w's signer a node the grant is for
    if o is not None and person_over(rows, o) == pg and pg is not None and "withdraw_node_unread" not in MUT \
            and _uncut(S, w, k, o):
        return True
    o = owner_over(rows, g["signer"])                        # w's signer's person owns the grant's signer
    if o is not None and pw is not None and person_over(rows, o) == pw and _uncut(S, w, g["signer"], o):
        return True
    return False


# ---- derived ---------------------------------------------------------------------------------------------
def _past(S, at_row):
    """The ids at at_row and in its past; every held id where at_row is None; none where at_row is not held."""
    if at_row is None:
        return frozenset(S.by)
    if at_row not in S.by:
        return frozenset()
    return frozenset(S.anc[at_row]) | {at_row}


def _held(S, at_row):
    return at_row is None or at_row in S.by


def _in(S, a, b):
    """a is b or in b's past."""
    return a == b or a in S.anc[b]


def covers(classes, c):
    if "classes_unread" in MUT:
        return True
    if "prefix_no_colon" in MUT:
        return any(c.startswith(e) for e in classes)
    return any(c.startswith(e) if e.endswith(":") else c == e for e in classes)


def key_view(S, reader=None, final=frozenset(), roster=frozenset()):
    """The kernel's key view over S: key_end.counts_by, for `reader` (None: no reader's line)."""
    return lambda rid, k: KE.counts_by(S, rid, k, reader, final, roster)


def voice(S, g, kv):
    """The grant's signer's signature counts by the end rule (the key view)."""
    if "revoked_unread" in MUT:
        return True
    return kv(g["id"], g["peer"] if "voice_wrong_key" in MUT else g["signer"])


def placed(S, g, kv):
    """A grant at federation scope only where both parties announced in its past, each announcement counting by the
    key view."""
    if not g.get("fed", True) or "federation_unannounced" in MUT:
        return True
    anc = S.anc[g["id"]]
    def announced(k):
        return any(a["kind"] == "announce" and a["signer"] == k and a["id"] in anc
                   and ("announcement_unviewed" in MUT or kv(a["id"], k)) for a in S.Cs)
    return announced(g["signer"]) and announced(g["peer"])


def withdrawn(S, g, at_row):
    for w in S.Cs:
        if w["kind"] in ENDS and w["of"] == g["id"] and may_withdraw(S, w, g):
            if at_row is None:
                if "withdrawn_none_unread" in MUT:
                    continue
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


def _grants(S, at_row, kv):
    past = frozenset(S.by) if "future_grant" in MUT and _held(S, at_row) else _past(S, at_row)
    return [g for g in K.sel(S.Cs, kind="grant") if g["id"] in past and voice(S, g, kv) and placed(S, g, kv)]


def _instant_key(g):
    """The order among concurrent rows: the latest instant (none below any), then the lowest id (larger key wins)."""
    t = g.get("at")
    at = (t is not None, (-t if "fold_earliest" in MUT else t) if t is not None else 0)
    return (at, g["id"]) if "fold_highest_id" in MUT else (at, tuple(-ord(ch) for ch in g["id"]) + (1,))


def fold_default(S, group, rank=lambda r: 0):
    """THE ONE DEFAULT FOLD over one signer's rows on one target (the twin of derived::fold_default): the rows of the
    top kind; a row beats each row in its own past and every row something in its own past beat (causal first: a
    fork cannot revive a branch a row in its past beat), and beats a concurrent row of a lower instant key; the
    winner is beaten by no row it is not concurrent with through that inheritance, of those the latest instant, then
    the lowest id. None where every row is beaten (a split that names nothing settles nothing)."""
    if not group:
        return None
    top = max(rank(r) for r in group)
    g = [r for r in group if rank(r) == top]
    if "fold_instant_first" in MUT:
        return max(g, key=_instant_key)
    beat, strong = {}, set()
    for y in sorted(g, key=lambda r: len(S.anc[r["id"]])):
        st = {x["id"] for x in g if x["id"] in S.anc[y["id"]]}
        if "fold_inherit_unread" not in MUT:
            for z in list(st):
                st |= beat[z]
        strong |= st
        beat[y["id"]] = st | {x["id"] for x in g if x is not y and x["id"] not in S.anc[y["id"]]
                              and y["id"] not in S.anc[x["id"]] and _instant_key(y) > _instant_key(x)}
    left = [r for r in g if r["id"] not in strong]
    return max(left, key=_instant_key) if left else None


def winners(S, at_row=None, now=None, kv=None):
    """The default fold for each (signer, peer)."""
    kv = kv or key_view(S)
    groups = {}
    for g in _grants(S, at_row, kv):
        if "fold_live_only" in MUT and (withdrawn(S, g, at_row) or not in_term(g, now)):
            continue
        groups.setdefault((g["signer"], g["peer"]), []).append(g)
    out = {k: fold_default(S, gs) for k, gs in groups.items()}
    return {k: w for k, w in out.items() if w is not None}


def in_force(S, g_id, at_row=None, now=None, kv=None):
    """Whether grant g_id is in force at at_row (None: over every held row), at the caller's instant now."""
    g = S.by.get(g_id)
    if g is None or g["kind"] != "grant" or not S.C.get(g_id):
        return False
    w = winners(S, at_row, now, kv).get((g["signer"], g["peer"]))
    return w is not None and w["id"] == g_id and not withdrawn(S, g, at_row) and in_term(g, now)


def grants_in_force(S, principal, at_row=None, now=None, kv=None):
    return [g for (s, _), g in sorted(winners(S, at_row, now, kv).items())
            if s == principal and not withdrawn(S, g, at_row) and in_term(g, now)]


def peer_set(S, principal, at_row=None, now=None, kv=None):
    """The peers named by the principal's grants in force at at_row."""
    return frozenset(g["peer"] for g in grants_in_force(S, principal, at_row, now, kv))


def bilateral(S, a, b, at_row=None, now=None, kv=None):
    """A bilateral peering: a's grant to b and b's grant to a, both in force."""
    return b in peer_set(S, a, at_row, now, kv) and a in peer_set(S, b, at_row, now, kv)


def _sub(S, at_row):
    """The concluded rows of at_row's past (with at_row)."""
    ids = _past(S, at_row)
    return [r for r in S.Cs if r["id"] in ids]


def owner(S, node, at_row=None):
    """The node's one owner over at_row's past: THE owner reading, seat.Seats.owner (None with none, or two)."""
    return owner_over(_sub(S, at_row), node)


def principals(S, node, at_row=None):
    if "owner_any" in MUT:
        return frozenset(g["signer"] for g in K.sel(S.Cs, kind="grant"))
    if "owner_two_one" in MUT:
        rows = _sub(S, at_row)
        hs = ST.Seats(CK.State(rows, {r["id"]: True for r in rows})).holders("owner", node)
        return frozenset({node}) | frozenset(hs)
    o = owner(S, node, at_row)
    return frozenset({node} | ({o} if o is not None else set()))


def may_send(S, node, peer, row_class, at_row=None, now=None, kv=None):
    """The grant under which node may send peer a row of row_class at at_row, or None."""
    for p in sorted(principals(S, node, at_row)):
        for g in grants_in_force(S, p, at_row, now, kv):
            if g["peer"] == peer and covers(g["classes"], row_class):
                return g["id"]
    return None


def replication_set(S, node, addressed, at_row=None, now=None, kv=None):
    """Edge's fan-out: the operator-addressed peers that are in the consent peer set of a principal of the node."""
    ps = frozenset().union(*(peer_set(S, p, at_row, now, kv) for p in principals(S, node, at_row)))
    return frozenset(addressed) & ps
