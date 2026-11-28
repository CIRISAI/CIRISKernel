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
        return p["key"] == r["succ_of"] and covers(p, r["at_old"])   # the old key, inside its own record
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


def successor(S, k, ret=None):
    """The one key the frontier of k's concluded rotations names; two keys spoken leave it empty. Given the
    retained set, it reads only rotations that have not lapsed, as every derived answer does."""
    rots = [r for r in K.sel(S.Cs, kind="rec") if r["succ_of"] == k and (ret is None or r["id"] in ret)]
    if not rots:
        return None
    keys = sorted({r["key"] for r in CK.frontier(S, rots)})
    if "rank_successor" in MUT:
        return keys[0]                    # PLANT: the lower key id wins
    return keys[0] if len(keys) == 1 else None


def ends_of(S, k, roster=frozenset()):
    """Key k's ends, as rows:
        its self-revocations, but NONE where a concluded rotation of k is held at all (a retired key's revocation is
            no end, whoever signed it and whatever its past holds; MUTATION retired_key_revokes: only one with a
            rotation in its own past is none);
        every concluded rotation of k (a rotated holder speaks under its new key). Two rotations of one key are a
            FORK of the key: both are ends of the old key, and neither successor stands (successor) until the self
            roster's count settles which;
        an end by the person's self roster: a row of `roster` (the ids of the roster's acts CONCLUDED under that
            roster's own count rule, read by the seat over the roster) whose `rend_of` is k, from its `ra` on
            (MUTATION roster_end_unread). A thief holding one key cannot make one where the roster needs more.
    The residual, stated: a person with ONE key (a self roster of one), whose key is stolen, cannot be told from the
    thief: the thief can rotate or revoke it as the owner could."""
    rots = [r for r in S.Cs if r["kind"] == "rec" and r["succ_of"] == k]
    if "retired_key_revokes" in MUT:
        revs = [r for r in S.Cs if r["kind"] == "revoke" and r["key"] == k and r["signer"] == k
                and not any(x["id"] in S.anc[r["id"]] for x in rots)]
    else:
        revs = [] if rots else [r for r in S.Cs if r["kind"] == "revoke" and r["key"] == k and r["signer"] == k]
    rends = [] if "roster_end_unread" in MUT else [r for r in S.Cs if r.get("rend_of") == k and r["id"] in roster]
    return revs + rots + rends


def _own_rows(S, reader):
    """A reader's own rows: those it signed or cosigned."""
    return [r for r in S.Cs if r["signer"] == reader or reader in r.get("cosigners", ())]


def stands(S, rid, e, reader=None, final=frozenset()):
    """Row `rid` stands against end `e` (A KEY END IS A CUT, the Constitution's ruling): (a) it is in e's past (and,
    for an end stating an instant, its own instant before it); or (b) it is on the reader's own line from before the
    reader held e: a row the reader signed or cosigned is it, or has it in its past, without e there (taken up;
    MUTATION taken_up_unread); or (c) it is part of a count FINAL BY ACKNOWLEDGEMENT (final: the counts with n - t + 1
    clean receipts, seat.final_by_ack): that count, or a row it names (MUTATION final_count_unread). A final act is
    not reopened by a later cut."""
    r = S.by[rid]
    if rid in S.anc[e["id"]] and not (e.get("ra") is not None and instant(r) is not None and not instant(r) < e["ra"]):
        return True
    if reader is not None and "taken_up_unread" not in MUT and any(
            (a["id"] == rid or rid in S.anc[a["id"]]) and e["id"] not in S.anc[a["id"]] for a in _own_rows(S, reader)):
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
    return all(stands(S, r["id"], e) for e in ends_of(S, r["signer"]))


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
    return all(stands(S, rid, e, reader, final) for e in ends_of(S, k, roster))


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
