"""
key_end.py: a key's own end, as rows of the kernel (formal/causal_kernel/causal_kernel.py, imported in place).

A key record states `vu` (its `valid_until`); `vf` is the record's own signed instant (`asserted_at`). Which records must state an end is read from the
record alone: its `typ` (identity_type) and whether it is a room key. A `user` key (a person) and an accord holder's
key MUST NOT state one; a room key and a pseudonym need not. Every other node or agent record states one, and the bound is self-contained:
vf <= vu and vu - vf <= CEIL, read from the row and nothing else (the door).
A renewal is a further record of the same key that names (supersedes) its own earlier record. It counts whenever it
was signed: a renewal signed after the end revives the key, so a back-dated one gains nothing over it.

Rows (dicts of causal_kernel.row):
    rec      a key's claim of itself. signer = key. A renewal names the record it continues (same key). A rotation
             names the old key's record, carries succ_of = the old key, and both signatures (sigs) and the old
             key's own instant at_old.
    att      an attestation by `signer` at its own instant `at`, naming the record it was signed under (`cover`),
             optionally `about` a key and naming further rows.
    edge     a trust edge `signer -> to`, an att with `to`.
    revoke   the key's own revocation, `ra` = revoked_after (statements after it do not count; never withdrawn).

Layers
    kept       CK.kept with WF below (the row alone).
    concluded  RULE below: reads only the row's past (the record it names). It never reads now.
    derived    answers(S, now): live and ended keys, the successor, reach, score, and each row's lapse.

The only instants compared are one key's own: a row's `at` against the record it names (same signer); a rotation's at_old
against the old key's record (signed by the old key). No two signers' instants are compared, and nothing is ranked by an instant or a digest.

A row LAPSES at now when its signer's key has ended and no row that has not lapsed has it in its past. A seat
serves and keeps exactly the rows that have not lapsed (RETAINED), which is route.py's closure with the seeds
"rows of a key that has not ended".
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import causal_kernel as CK  # noqa: E402

K = CK.K
INF = float("inf")
CEIL = 10                         # stands for key_record_max_secs (365 days); the grid's unit is ~36.5 days
END_REQUIRED = {"node", "agent"}  # identity types whose record must state an end, outside a private room
END_FORBIDDEN = {"user", "accord_holder"}   # a person's own key and an accord holder's: no person loses their self to a clock
# any other type (a pseudonym of CC 5.4.6) may state an end and need not
MUT = set()                       # planted breaks, switched on by the check


# ---- rows ------------------------------------------------------------------------------------------------
def rec(id, key, vf, vu, names=(), typ="node", succ_of=None, at_old=None, sigs=None, room=False):
    return CK.row(id, "rec", key, names, key=key, vf=vf, vu=vu, typ=typ, succ_of=succ_of, at_old=at_old,
                  sigs=frozenset(sigs if sigs is not None else ({key} | ({succ_of} if succ_of else set()))), room=room)


def att(id, signer, at, cover, about=None, names=()):
    return CK.row(id, "att", signer, (cover,) + tuple(names), at=at, cover=cover, about=about)


def edge(id, signer, to, at, cover, names=()):
    return CK.row(id, "edge", signer, (cover,) + tuple(names), at=at, cover=cover, to=to)


def revoke(id, key, ra, names=()):
    """A revocation of `key` by itself after its own instant `ra`; `names`: the key's rows it has in its past."""
    return CK.row(id, "revoke", key, tuple(names), key=key, ra=ra)


# ---- the door: the row alone -----------------------------------------------------------------------------
def needs_end(r):
    """Read from the record alone: its identity type and whether it is a room key."""
    if "wording" in MUT:      # the ruling as worded: no owner-binding at federation scope (another row)
        return r["typ"] in END_REQUIRED and not r.get("_fed_binding_held", False)
    return r["typ"] in END_REQUIRED and not r["room"]


def WF(r):
    if r["kind"] != "rec":
        return True
    vf, vu = r["vf"], r["vu"]
    if vu is None:
        return not needs_end(r)
    if r["typ"] in END_FORBIDDEN and "end_on_person" not in MUT:
        return False
    if vf > vu or (vf == vu and "end_closed" not in MUT):   # an equal end covers nothing (CC 2.6.2)
        return False
    if vu - vf > CEIL and "no_ceiling" not in MUT:
        return False
    if r["succ_of"] is not None and r["succ_of"] not in r["sigs"] and "rotation_one_sig" not in MUT:
        return False           # a rotation carries the old key's signature beside the new key's possession
    return r["key"] in r["sigs"]


def _end(r):
    return INF if r["vu"] is None else r["vu"]


def covers(r, t):
    """CC 2.6.2: a record covers an instant t when vf <= t < vu, half-open. One test for a key's liveness, for
    a row's own instant under the record it names, and for a rotation's old-key instant (CC 2.4.1.1)."""
    if "end_closed" in MUT:      # PLANT: the end read as inside the record
        return r["vf"] <= t <= _end(r)
    return r["vf"] <= t < _end(r)


# ---- concluded: the row against its past ---------------------------------------------------------------
CLOCK = [0]


def RULE(r, P, past):
    if r.get("stub"): return r["concl"]                          # a stub keeps its conclusion; its bytes are gone
    by = {q["id"]: q for q in P}
    if r["kind"] == "rec":
        prev = [by[n] for n in r["names"] if n in by and by[n]["kind"] == "rec"]
        if r["succ_of"] is None:
            if not r["names"]:
                return True                                   # a first record: possession is the door's
            if not prev:
                return False
            p = prev[0]
            if p["key"] != r["key"]:
                return False
            ok = True                                         # the key's own further record, whenever signed
            if "arrival_clock" in MUT:                        # PLANT: judged against the node's clock on first holding
                CLOCK[0] += 3
                ok = ok and CLOCK[0] < _end(p)
            return ok
        if not prev:
            return False
        p = prev[0]
        # the plain end rule (r114 TR2): a rotation is a row by the old key, so one with that key's own revocation (either
        # form: a key-lane revoke, a registered self-unseat) in its past is not the key's and concludes nothing (MUTATION
        # revoked_key_rotates). A revocation NOT in its past is the retired-key rule's (ends_of)
        import checkpoint as _CP
        k = r["succ_of"]
        if "revoked_key_rotates" not in MUT and any(
                (q["kind"] == "revoke" and q.get("key") == k and q["signer"] == k) or _CP.registered_self_unseat(q, k)
                for q in P):
            return False
        return p["key"] == k and covers(p, r["at_old"])   # the old key, inside its own record
    if r["kind"] in ("att", "edge"):
        c = by.get(r["cover"])
        if c is None or c["kind"] != "rec" or c["key"] != r["signer"]:
            return False
        if "conclude_reads_now" in MUT and CLOCK[0] >= _end(c):   # PLANT: conclusion reads now
            return False
        return covers(c, r["at"])
    return True                                               # a revocation: the key's own, never withdrawn


def state(rows):
    return CK.concluded(CK.kept(rows, WF), RULE)


def arrived(order):
    CLOCK[0] = 0
    return CK.arrive(order, RULE, wf=WF)


# ---- derived ---------------------------------------------------------------------------------------------
def recs(S, k):
    return [r for r in K.sel(S.Cs, kind="rec") if r["key"] == k]


def rev_bound(S, k):
    ras = [r["ra"] for r in K.sel(S.Cs, kind="revoke") if r["key"] == k and r["signer"] == k]
    return min(ras) if ras else INF


def live(S, k, now, witnessed_late=False):
    if now >= rev_bound(S, k):
        return False
    for r in recs(S, k):
        if covers(r, now):
            return True
    if "witness_revives" in MUT:      # PLANT: another voice's row naming a key's record extends it by the ceiling
        for r in recs(S, k):
            if any(r["id"] in q["names"] and q["signer"] != k for q in S.Cs) and r["vf"] <= now < _end(r) + CEIL:
                return True
    return False


def ended(S, k, now):
    """No record of k states an end after now, or k revoked itself by now. A record not yet begun is not ended."""
    if now >= rev_bound(S, k):
        return True
    rs = recs(S, k)
    if "end_from_newest" in MUT and rs:   # PLANT: one voice's newest record by its signed valid_from decides alone
        rs = [max(rs, key=lambda r: (r["vf"], r["id"]))]
    return all(_end(r) <= now for r in rs)


def successor(S, k, ret=None, roster=frozenset()):
    """The one key the frontier of k's concluded rotations names; two keys spoken leave it empty. Given the
    retained set, it reads only rotations that have not lapsed, as every derived answer does."""
    rots = [r for r in K.sel(S.Cs, kind="rec") if r["succ_of"] == k and (ret is None or r["id"] in ret)
            and not voided(S, r, roster)]
    if not rots:
        return None
    keys = sorted({r["key"] for r in CK.frontier(S, rots)})
    if "rank_successor" in MUT:
        return keys[0]                    # PLANT: the lower key id wins
    return keys[0] if len(keys) == 1 else None


def voided(S, rot, roster=frozenset()):
    """A rotation of a key is VOIDED by the person's self roster (the Constitution's ruling, T3): a concluded eviction
    from the person's self roster (an id of `roster`: seat.self_roster_ends, the roster's own count, read by the
    key-person lane) that removes the rotated-to key and cites the rotation (`names`, refs.also.cites). Voided, the
    rotation is no end of the old key and its successor does not stand; the old key is restored exactly as it was
    (where it is the stolen one, the roster removes it too: voiding is not removal). In a fork the roster's act names
    the one it voids, and the other stands. A one-key roster cannot void (the residual). MUTATION rotation_void_unread."""
    if "rotation_void_unread" in MUT: return False
    return any(e in S.by and tuple(S.by[e].get("to", ())) == (rot["key"],) and rot["id"] in S.by[e]["names"]
               for e in roster)


def ends_of(S, k, roster=frozenset()):
    """Key k's ends, as rows (its LIVENESS: G33, only the key's own acts end it):
        its self-revocations, ordered against its rotations (the Constitution's ruling (1) on r114): a rotation with
            k's revocation (either form) in its past concludes nothing (RULE), and the key is ended (TR2); a
            revocation is no end WHILE an unvoided rotation of k stands, the rotation in its past or concurrent with
            it, so the key's history counts (there is no fork between a rotation and a revocation). The remedy the
            other way is the self roster's void of the rotation: voided, it ends nothing, and the revocation is then
            the key's end (revocation_stands). MUTATION retired_key_revokes (only a revocation with a rotation in its
            own past is none: a concurrent one ends the key);
        every concluded rotation of k not voided by the person's self roster (voided; a rotated holder speaks under
            its new key). Two rotations of one key are a FORK of the key: both are ends of the old key, and neither
            successor stands until the self roster's count settles which (voids one).
    An eviction from the person's self roster (a roster end) is NOT an end here: it ends the key AS A KEY OF THAT
    PERSON (G33), read by the person map at each count's voices (seat.person_of, the key-person lane: from the cut,
    by the roster's cut rule, the key is no voice of the person and holds none of its standing), and a row the key
    signs as itself is read as any unowned key's. The caller presents the person's self-roster rows.
    The residual, stated: a person with ONE key (a self roster of one), whose key is stolen, cannot be told from the
    thief: the thief can rotate or revoke it as the owner could, and no roster can void a rotation."""
    rots = [r for r in S.Cs if r["kind"] == "rec" and r["succ_of"] == k and not voided(S, r, roster)]
    revs = [r for r in S.Cs if r["kind"] == "revoke" and r["key"] == k and r["signer"] == k
            and revocation_stands(S, r, k, rots, roster)]
    # a voided rotation's rotated-to key: the roster's voiding act ends it, by the cut rule like any ended key's (what
    # a reader took up and what is final stand; MUTATION voided_successor_kept)
    voids = [] if "voided_successor_kept" in MUT else [
        S.by[e] for e in roster if e in S.by and tuple(S.by[e].get("to", ())) == (k,)
        and any(n in S.by and S.by[n]["kind"] == "rec" and S.by[n].get("succ_of") is not None and S.by[n]["key"] == k
                for n in S.by[e]["names"])]
    return revs + rots + voids


def revocation_stands(S, rv, k, rots, roster=frozenset()):
    """Whether revocation rv of key k (either form) is an end of k against k's unvoided rotations `rots` (ruled (1) on
    r114): none while a rotation stands, in rv's past or concurrent with it (a rotation with rv in ITS past concludes
    nothing, RULE, so it is not among `rots`). The crate's key_end::revocation_stands."""
    if "retired_key_revokes" in MUT: return not any(x["id"] in S.anc[rv["id"]] for x in rots)
    return not rots


def _before(S, rid, e):
    """THE PLAIN END RULE, limb (a): row rid is in end e's past (and, for an end stating an instant, its own instant
    before it)."""
    r = S.by[rid]
    return rid in S.anc[e["id"]] and not (e.get("ra") is not None and instant(r) is not None and not instant(r) < e["ra"])


def own_row(S, a, own, roster=frozenset(), voices=None):
    """THE READER'S OWN ROW, one definition for every reader's line (limb (b) of the end rule, and the line
    seat/checkpoint.takes_up reads): row `a` (a dict of S) is reader `own`'s where
        (i)   own signed it itself, concluded or not (its cosign rows among them);
        (ii)  never because another signer's row lists own as a cosigner, a seat row included (STRICT, review-48 R2s:
              an offer over the signer's own object concludes on its word alone, so a forged cosigner breaks no count);
        (iii)  each only where own's key stands at it, by the key-end cut over the key's one set of ends (ruled): the
              row is in the PAST of each of key_ends(own) (the key lane's revocations, rotations and roster voids,
              and a concluded `registered` unseat of own by own; the plain end rule). A row concurrent with the key's end, or after
              it, is no row of its line (r97 K1); an honest revocation names its last honest rows, so they stay in.
    Limb (b) reads these rows per row against each end, with no ordering; any order rule is the person lane's, on
    top. `voices`: seat.voices by default. MUTATIONS reader_line_unchecked ((iv) unread), own_unconcluded_unread
    ((i) concluded rows only), own_claimed_cosigner ((ii): any row listing own)."""
    # the one definition is checkpoint.own_row (the crate's seat::own_row); the key's own ends are this lane's
    import checkpoint as _CP
    import seat as _ST
    vs = voices or _ST.voices
    def no_key_view(r, P):                   # (ii) is read with no key view: the key view is (iv)'s
        _ST.KEY_VIEW.append(None)
        try:
            return vs(r, P)
        finally:
            _ST.KEY_VIEW.pop()
    es = None
    def ends_ok(r):
        nonlocal es
        if es is None: es = key_ends(S, own, roster)   # the key's ONE set of ends: both forms, a retired key's none
        return all(_before(S, r["id"], e) for e in es)
    return _CP.own_row(S, a, own, ends_ok, no_key_view, MUT)


def registered_self_unseat(q, k):
    """checkpoint.registered_self_unseat, the one definition (the crate's seat::registered_self_unseat)."""
    import checkpoint as _CP
    return _CP.registered_self_unseat(q, k)


def key_ends(S, k, roster=frozenset()):
    """THE ONE SET OF ENDS OF KEY k, for every reader of a key's ends (a count's voices and every signature the key
    view reads, a grant's, an announcement's, a withdrawal's; the person map's 'a key of the person'; a reader's own
    rows): the key lane's ends (ends_of: its self-revocations, its unvoided rotations, the roster's void of a rotation
    to it) and each CONCLUDED unseat of k's `registered` seat by k itself (the seat lane's revocation; one that
    concluded nothing ends nothing, r106 U2). r106 K1r, PG1. MUTATIONS registered_end_unread (the seat-lane form
    unread), registered_unconcluded_counted (an unconcluded one ends the key)."""
    out = list(ends_of(S, k, roster))
    import checkpoint as _CP
    # the seat lane's revocation ordered against k's rotations by the same rule (r110 RK2, r114): revocation_stands
    rots = [e for e in out if e["kind"] == "rec" and e.get("succ_of") == k]
    keep = lambda q: revocation_stands(S, q, k, rots, roster)
    return out + [q for q in _CP.registered_ends(S, k, MUT, keep) if q not in out]


def revocations(S, k, roster=frozenset()):
    """The key's own revocations among its ends (key_ends): either lane's, a key-lane revoke row or a concluded
    registered self-unseat. What the person map reads as 'the key's own end' (CC 2.4.1.1: "only the key's own
    revocation ends its liveness"): rotations and the roster's voids are the roster's to settle, and the person map
    is itself an input to the roster's count."""
    kinds = ("unseat",) if "person_key_lane_unread" in MUT else ("revoke", "unseat")   # MUTATION: key lane unread
    return [e for e in key_ends(S, k, roster) if e["kind"] in kinds]


def _own_rows(S, reader, roster=frozenset()):
    """A reader's own rows (own_row)."""
    return [a for a in S.rows if own_row(S, a, reader, roster)]


def stands(S, rid, e, reader=None, final=frozenset(), roster=frozenset()):
    """Row `rid` stands against end `e` (A KEY END IS A CUT, the Constitution's ruling): (a) it is in e's past (and,
    for an end stating an instant, its own instant before it); or (b) it is on the reader's own line from before the
    reader held e: a row the reader signed or cosigned is it, or has it in its past, without e there (taken up;
    MUTATION taken_up_unread); or (c) it is part of a count FINAL BY ACKNOWLEDGEMENT (final: the counts with n - t + 1
    clean receipts, seat.final_by_ack): that count, or a row it names (MUTATION final_count_unread). A final act is
    not reopened by a later cut."""
    if _before(S, rid, e):
        return True
    if reader is not None and "taken_up_unread" not in MUT and any(
            (a["id"] == rid or rid in S.anc[a["id"]]) and e["id"] not in S.anc[a["id"]]
            for a in _own_rows(S, reader, roster)):
        return True
    # (c) protects only a voice valid when cast: never one whose end is in the final count's own past (MUTATION
    # final_protects_late)
    if "final_count_unread" not in MUT and any(
            f in S.by and (rid == f or rid in S.by[f]["names"])
            and ("final_protects_late" in MUT or e["id"] not in S.anc[f]) for f in final):
        return True
    return False


def instant(r):
    """A row's own signed instant, where it states one: the ONE accessor counts and counts_by read (the crate's
    KeyEndRow::instant; the fixtures' rows give every row its `at`, as tests/common's adapter does). A row stating no
    instant is judged by its past alone: a revocation's revoked_after reaches only rows that state an instant."""
    return r.get("at")


def counts(S, r):
    """THE END RULE, for every count: a concluded statement of key k counts only where it is in the causal past of
    each of k's own ends (and, for a self-revocation, its own instant before the revoked_after k stated); with no
    such end, a concluded statement counts (its instant inside the record it names is the holder's word, bounded
    below by its own past: the licence term's residual and caller duty). Whether a live row cites it is never read:
    a count reads no anchor (the Constitution's ruling; only content may be anchored by others' rows)."""
    if not S.C.get(r["id"]) or r["kind"] not in ("att", "edge"): return bool(S.C.get(r["id"]))
    return all(stands(S, r["id"], e) for e in key_ends(S, r["signer"]))


def counts_by(S, rid, k, reader=None, final=frozenset(), roster=frozenset()):
    """THE END RULE for key k's signature on row `rid` (a statement, or a seat row k signed or cosigned, held in one
    causal order with k's key lane), for `reader` (None: no reader's line), the counts `final` final by
    acknowledgement: the row concluded, and standing against each of k's ends (stands). No cite is read.
    The cost, stated: nobody can tell the thief from the owner, so a thief's vote a reader took up before holding the
    end stands for that reader, and one in a final count stands for everyone; the remedy is the members' later count
    reversing the act. Readers can differ on a count not yet final until receipts or a later count settle it. A
    newcomer (a reader with no row) reads the plain cut and the final counts. Caller duty: an honest rotation or
    revocation names the key's last rows."""
    r = S.by.get(rid)
    if r is None or not S.C.get(rid): return False
    return all(stands(S, rid, e, reader, final, roster) for e in key_ends(S, k, roster))


def _wire_seat():
    import seat as _ST
    _ST.KE_COUNTS[0], _ST.KE_ENDS[0] = counts_by, ends_of


_wire_seat()


def seeds(S, now, stubs=True):
    """Concluded rows whose key has not ended at now, every revocation and rotation (never withdrawn, never
    dropped), and (stubs) every row a count reads (counts: a compaction drops no stub a count reads)."""
    out = {r["id"] for r in S.Cs if r["kind"] in ("att", "edge") and counts(S, r)} if stubs else set()
    # and every end a count reads (a rotation, like a revocation, is never dropped: dropping it would revive the old
    # key's cut rows)
    out |= {r["id"] for r in S.Cs if r["kind"] == "rec" and r["succ_of"] is not None}
    for r in S.Cs:
        if r["kind"] == "revoke":
            out.add(r["id"]); continue
        k = r["key"] if r["kind"] == "rec" else r["signer"]
        if ended(S, k, now):
            continue
        if "seed_live_only" in MUT and not live(S, k, now):
            continue                      # PLANT: keep only rows of keys live now (a record not yet begun is dropped)
        out.add(r["id"])
    return out


def bytes_retained(S, now):
    """The rows whose BYTES are kept at now: rows of keys not ended, every revocation and rotation, and everything in
    their past (what a live row names). A row a count reads that is not among them (an expired key's in-time vote, its
    count settled) keeps its STUB for good (retained) and its bytes may drop."""
    s = seeds(S, now, stubs=False)
    return frozenset(s) | frozenset(a for i in s for a in S.anc[i] if a in S.by)


def retained(S, now):
    """The rows whose STUB is kept for good at now (digest, names, the fields a count reads, the conclusion): every
    row a count reads (counts), every row whose bytes are kept (bytes_retained), and everything in their past.
    Storage only: nothing counts by it."""
    if "drop_dead_signers" in MUT:        # PLANT: drop every row of an ended key, named or not
        return frozenset(seeds(S, now))
    s = seeds(S, now)
    return frozenset(s) | frozenset(a for i in s for a in S.anc[i] if a in S.by)


def reach(S, own, now, keys, ret=None):
    ret = retained(S, now) if ret is None else ret
    E = [e for e in K.sel(S.Cs, kind="edge") if e["id"] in ret and live(S, e["signer"], now) and live(S, e["to"], now)]
    return K.fix(lambda ks: ks | frozenset(e["to"] for e in E if e["signer"] in ks), frozenset({own}), len(keys) + 1)


def score(S, subject, now, ret=None):
    ret = retained(S, now) if ret is None else ret
    # a count: by the end rule (counts), never by what is retained (MUTATION ended_vote_retained_by_cite: a row a
    # live row cites counts too; score_reads_lapsed: every concluded row counts)
    return frozenset(a["signer"] for a in K.sel(S.Cs, kind="att") if a.get("about") == subject
                     and (counts(S, a) or "score_reads_lapsed" in MUT
                          or ("ended_vote_retained_by_cite" in MUT and a["id"] in ret)))


def answers(S, now, keys, parties, subjects):
    ret = retained(S, now)
    return {
        "live": frozenset(k for k in keys if live(S, k, now)),
        "ended": frozenset(k for k in keys if ended(S, k, now)),
        "succ": tuple((k, successor(S, k, ret)) for k in keys),
        "reach": tuple((p, reach(S, p, now, keys, ret)) for p in parties),
        "score": tuple((s, score(S, s, now, ret)) for s in subjects),
        "rows": frozenset((i, bool(S.C.get(i)), i in ret) for i in ret),
        "bytes": bytes_retained(S, now),
    }


def stub(r, concl):
    """A row's stub: its id, kind, signer, names, the fields a count reads, and its conclusion; its bytes dropped."""
    return dict(r, stub=True, concl=concl)


def compact(rows, S, now):
    """Drop the lapsed rows, and the bytes of a row whose stub alone is kept (MUTATION stub_drops_counted: a counted
    row whose bytes may drop is dropped whole)."""
    keep, byt = retained(S, now), bytes_retained(S, now)
    out = []
    for r in rows:
        if r["id"] not in keep: continue
        if r["id"] in byt: out.append(r); continue
        if "stub_drops_counted" in MUT: continue
        out.append(stub(r, bool(S.C.get(r["id"]))))
    return out
