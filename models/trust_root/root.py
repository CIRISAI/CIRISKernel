#!/usr/bin/env python3
"""The trust root's fork fold (persist's item 15): a root's lineage of genesis bundles, its count, its heads, the
fold at two tips, the bundle in force for one reader, and the root grants counted over it.

    the object   a bundle (`ceg-genesis-bundle/2`) is a signed object, not a row. Its payload: `holders`, `seats`
                 (serve_nodes), `charter` (one value), `version`, `family` (family_key_id, the lineage's name),
                 `recovery` (recovery_commitments: holder -> recovery key, keys exactly the holders) and `prev` (the
                 bundles it extends: refs.prev, then for a join refs.further_prev; refs.prev is the greatest version,
                 least id among equals, and a named predecessor in the past of another concludes nothing). `stmts` are its holders' statements, (key, iat), one per
                 key over the one payload; `iat` is the payload's.
    the count    the first bundle is counted over every holder it lists; a later one over a strict majority of its
                 predecessor's live holders; a JOIN by a strict majority of EACH named predecessor's live holders,
                 each voice a key that predecessor seats under the same key, whatever the charters, less the keys
                 retired across its branches (a join inherits the union of retired keys and spent commitments, and
                 revives nothing). A statement whose iat disagrees is Invalid on
                 its own, and the bundle is counted on the rest. A holder whose key is revoked with no bound leaves
                 the live holders; a statement its bound voids (on a bundle not at or before the bound) does not
                 count. The exception: a holder's own key recovery, a later bundle under that holder's recovery key
                 changing only its own seat (else `recovery_changes_other_seat`); a spent commitment (one a
                 recovery in the bundle's past used) concludes nothing. A recovery takes S'' like any bundle, the
                 holder (either key) its voice; recoveries of one seat are settled by T between them.
    the heads    `version` is prev's plus one (a join: the greater plus one) and `family` is prev's: a consistency
                 check, never ranked; a mismatch is Invalid. A later bundle is a counted change of the holders'
                 roster: it names the newest bundle in its signers' own past, and S'' and T at the fork point
                 apply to it as to a roster change (MINE, the Constitution's derived reading).
    the fold     two later bundles on one bundle are both tips, and no rule picks one. The holders and seats at
                 several tips are the guarded fold (CC 2.7.8). Tips whose regime differs do not fold: a bundle's
                 regime is its WHOLE charter, compared as one value (without recovery_commitments, which are per
                 holder), and the holders are then those common to the tips (and the seats likewise) until a bundle
                 names both. A recovery is a rotation of an existing seat, not an addition: the key it seats is in
                 the fold only where the holder's seat itself is in (CC 2.6.1.11).
    in force     per reader, never global: the reader's anchor (a bundle id, or the holders' thumbprints) names its
                 first bundle (else `genesis_bundle_not_anchored`), and any other first bundle is void for it; the
                 bundle in force is the newest of the lineage the reader has acknowledged (acceptance edges with
                 attached_head_digest), read by its line, in the order it acknowledged them: a bundle behind one it
                 acknowledged and not on its line is void for it, and so is every bundle built on one, a join
                 included; several acknowledged tips are folded; none, the anchor.
    grants       a root grant EXISTS where it is counted at a strict majority (accord_majority) over the live
                 holders of the bundles it names, and their charters carry its duty; it names the newest bundles in
                 its signers' own past (signers who saw s2 name s1 and s2, and are counted over their fold, or the
                 common holders where charters differ; one naming only s1 by signers who saw s2 concludes nothing); one made under either
                 successor stands as a row. It RESOLVES for a reader while its bundle is in the reader's lineage
                 (one of its heads, or in their past; not on a line behind it) and the scope of the bundle in force
                 at that reader still carries the duty (several tips: what all carry). A later bundle re-scopes
                 existing grants with no re-issuance.
    contested    two recoveries of one seat, neither in the other's past, are contested: neither replaces the seat
                 until a bundle names both, and the old key's seat stays as it was (the causal form of a spent
                 commitment).
    the costs    a recovery concurrent with an amend that changes the charter leaves the recovering holder no seat in
                 force until a bundle names both tips; it gives a holder majority nothing it lacks: the same majority
                 could remove that holder by an amend.
    residual     a holder's statement over a sibling bundle is not ordered against its grant, so it is not read; a grant on one tip is judged by the rows in its own past. It can matter only where that holder's voice is the
                 deciding one of an exact majority, and the statement over s2 and the grant on s1 are held evidence
                 the other holders can cite when they name both tips. A holder's own node that writes an acceptance
                 edge to each bundle it signs closes it for an honest holder.
    forked join  two joins of the same tips that do not fold with each other (their charters differ), neither in
                 the other's past, are contested: neither stands, and a reader that acknowledged them keeps the tips
                 they tried to join. A bundle naming every one settles them, counted by a strict majority of those
                 tips' common holders (so a forked settler ends at the same holders, never fewer). Two successors
                 of one bundle are no joins and fold as tips, and two joins under the SAME charter fold as any tips
                 do: concurrent successors are not contested.

Receipts, equivocation records and fork-attempt records move no head and are not read here.

MUT holds planted breaks, switched on by check_root.py.
"""

MUT = set()

INVALID, VOID, CONCLUDED, REFUSED = "invalid", "void", "concluded", "refused"


C0 = {"name": "c0", "duties": ("infra",)}


def bundle(id, family, version, holders, prev=(), charter=C0, seats=(), stmts=None, iat=0, recovery=None,
           recovers=None):
    """A bundle. stmts defaults to every holder of the predecessor... callers name them. recovers: (holder, new key)."""
    holders = tuple(holders)
    rec = dict(recovery) if recovery is not None else {k: "r:" + k for k in holders}
    return {"id": id, "kind": "bundle", "family": family, "version": version, "holders": holders,
            "prev": tuple(prev), "charter": charter, "seats": tuple(seats), "iat": iat, "recovery": rec,
            "stmts": tuple(stmts if stmts is not None else ((k, iat) for k in holders)), "recovers": recovers}


def revoke(key, bound=None):
    """A revocation of `key`; `bound` the last bundle its statements are good on (None: no bound)."""
    return {"kind": "revoke", "key": key, "bound": bound}


def ack(id, head, names=()):
    """A row of the root's lane: an acceptance edge whose attached_head_digest names bundle `head`."""
    return {"id": id, "kind": "ack", "head": head, "names": tuple(names)}


def grant(id, bundle_id, to, scope, signers, identity=("user",), duty="infra", names=()):
    """A root grant: a row counted over the holders of the bundles it names (`bundle_id`, one id or several), naming
    key `to` for room `scope`, of `duty` (the duty the bundles' charters must carry). `names`: the rows it names
    (acceptance edges and earlier grants); the bundles its signers had seen are derived from its causal past
    (seen_of)."""
    named = (bundle_id,) if isinstance(bundle_id, str) else tuple(bundle_id)
    return {"id": id, "kind": "grant", "bundle": named[0], "bundles": named, "to": to, "scope": scope,
            "signers": tuple(signers), "identity": tuple(identity), "duty": duty,
            "names": tuple(names)}


def duties(charter):
    """The duties a charter carries (its scope)."""
    return frozenset(charter.get("duties", ())) if isinstance(charter, dict) else frozenset()


def reader(anchor=None, thumbs=None, acks=(), rows=()):
    """A reader: its anchor (a first bundle's id, or the holders' thumbprints), the bundles it acknowledged, in the
    order it acknowledged them (its own line), and its own acknowledgement rows in the root's lane (`rows`)."""
    return {"anchor": anchor, "thumbs": frozenset(thumbs) if thumbs is not None else None, "acks": tuple(acks),
            "rows": frozenset(rows)}


# Grants sit on the reader's line (the Constitution's ruling), with bundles as heads. A grant naming a bundle strictly
# older than one the reader acknowledged, and not in the past of the reader's own acknowledgement rows, is void for
# that reader (MUTATION grant_line_unread). Kept as a list only so the planted break can switch it.
GRANT_LINE = [True]

# PROTOTYPES of the re-attack's two candidate fixes (review-58b on 272fcd6), off unless switched on (or by the
# environment, ROOT_SIBLING_T=1, ROOT_GRANT_COUNT=1), pending the Constitution:
#   SIBLING_T    two successors of one bundle signed by the same voices, neither in the other's past, are those
#                voices' self-fork, decided by T at the fork point (a tie keeps both)
#   GRANT_COUNT  in place of grants on the reader's line: a grant resolves for a reader only while its counted voices
#                are a strict majority of the reader's in-force holders (same key, live)
import os as _os  # noqa: E402
SIBLING_T = [bool(_os.environ.get("ROOT_SIBLING_T"))]
GRANT_COUNT = [bool(_os.environ.get("ROOT_GRANT_COUNT"))]


class Root:
    def __init__(self, bundles, revokes=(), grants=()):
        self.by = {b["id"]: b for b in bundles}
        self.revokes = list(revokes)
        self.rows = {g["id"]: g for g in grants}            # the root's lane: grants and acceptance edges
        self.grants = {g["id"]: g for g in grants if g["kind"] == "grant"}
        self._past, self._concl = {}, {}
        # a holder is one voice whatever key it signs with: its key, its recovery key, and the key a recovery seats
        self._own = {}
        for b in bundles:
            if b.get("recovers") is not None and len(b["prev"]) == 1 and b["prev"][0] in self.by:
                h, new = b["recovers"]
                rk = self.by[b["prev"][0]]["recovery"].get(h)
                for k in (new, rk):
                    if k is not None: self._union(h, k)

    def _find(self, k):
        while self._own.get(k, k) != k: k = self._own[k]
        return k

    def _union(self, a, b):
        ra, rb = self._find(a), self._find(b)
        if ra != rb: self._own[max(ra, rb)] = min(ra, rb)

    def owner(self, k):
        """The holder a key speaks for: its key, its recovery key, and the key a recovery seats are one voice."""
        return self._find(k)

    # ---- the lineage --------------------------------------------------------------------------------------
    def past(self, i):
        """The bundles in i's past (by prev), not i."""
        if i not in self._past:
            out = set()
            for p in self.by[i]["prev"]:
                if p in self.by:
                    out.add(p); out |= self.past(p)
            self._past[i] = frozenset(out)
        return self._past[i]

    def line(self, i):
        return self.past(i) | {i}

    # ---- the count ----------------------------------------------------------------------------------------
    def unbounded(self):
        return frozenset(r["key"] for r in self.revokes if r["bound"] is None)

    def live(self, holders):
        if "revoked_counts" in MUT: return frozenset(holders)
        return frozenset(holders) - self.unbounded()

    def voices(self, b):
        """The keys whose statement on b counts: iat agreeing, not voided by a bound. (A key revoked with no bound
        leaves the live holders, so a later count reads none of its statements: `base`.)"""
        out = set()
        for k, iat in b["stmts"]:
            if iat != b["iat"] and "iat_unread" not in MUT: continue            # Invalid on its own
            bounds = [r["bound"] for r in self.revokes if r["key"] == k and r["bound"] is not None]
            if bounds and "bound_unread" not in MUT and not any(b["id"] in self.line(x) for x in bounds if x in self.by):
                continue                                                          # after the bound
            out.add(k)
        return frozenset(out)

    def consistent(self, b):
        ps = [self.by[p] for p in b["prev"] if p in self.by]
        if len(ps) != len(b["prev"]): return False
        if set(b["recovery"]) != set(b["holders"]) and "commitments_unread" not in MUT: return False
        if not ps: return True
        if "version_unread" not in MUT and b["version"] != max(p["version"] for p in ps) + 1: return False
        if "family_unread" not in MUT and any(p["family"] != b["family"] for p in ps): return False
        if len(ps) >= 2:
            # the join's wire: refs.prev is the greatest version, least id among equals; refs.further_prev the rest;
            # a named predecessor in the past of another concludes nothing
            if "join_prev_unread" not in MUT and b["prev"][0] != min(b["prev"], key=lambda i: (-self.by[i]["version"], i)):
                return False
            if any(a in self.past(c) for a in b["prev"] for c in b["prev"]): return False
        return True

    def retired(self, prevs):
        """The keys retired across the branches of `prevs`: every key a recovery in their lines rotated out. A join
        inherits the union, and revives nothing (MUTATION retired_unread)."""
        if "retired_unread" in MUT: return frozenset()
        out = set()
        for p in prevs:
            for x in self.line(p):
                q = self.by[x]
                if q.get("recovers") is not None: out.add(q["recovers"][0])
        return frozenset(out)

    def meets(self, b, voices, within=None, prevs=None):
        """b's count on `voices`: one predecessor, a strict majority of its live holders; a JOIN, a strict majority
        of EACH named predecessor's live holders, each voice a key that predecessor seats under the same key, less the
        keys retired across its branches (MUTATION join_common_base: a strict majority of the holders common to
        them). `within`: only these holders (the fold's); `prevs`: these predecessors only (a merge counted without
        the void bundles it names)."""
        prevs = tuple(prevs if prevs is not None else b["prev"])
        if not prevs: return False
        if "count_over_own" in MUT:
            bases = [self.live(b["holders"])]
        elif len(prevs) >= 2 and "join_common_base" in MUT:
            bases = [self.live(frozenset.intersection(*[frozenset(self.by[p]["holders"]) for p in prevs]))]
        elif len(prevs) >= 2 and "join_union" in MUT:
            bases = [self.live(frozenset().union(*[frozenset(self.by[p]["holders"]) for p in prevs]))]
        else:
            gone = self.retired(prevs) if len(prevs) >= 2 else frozenset()
            bases = [self.live(self.by[p]["holders"]) - gone for p in prevs]
        if within is not None: bases = [x & within for x in bases]
        return all(2 * len(frozenset(voices) & x) > len(x) for x in bases)

    def contested_join(self, i):
        """A join (two predecessors or more) contested by a rival: a concluded join of the same predecessors under
        another charter, neither in the other's past. Joins that do not fold with each other may not both stand.
        Two successors of one bundle are no joins and fold as tips; two joins under the SAME charter fold as any
        tips do (MUTATION joins_fork_both: no join is contested)."""
        if "joins_fork_both" in MUT: return False
        b = self.by[i]
        if len(b["prev"]) < 2 or not self.counted(i)[0]: return False
        return any(x["id"] != i and len(x["prev"]) >= 2 and frozenset(x["prev"]) == frozenset(b["prev"])
                   and self.regime(x["id"]) != self.regime(i) and x["id"] not in self.past(i) and i not in self.past(x["id"])
                   and self.counted(x["id"])[0] for x in self.by.values())

    def base(self, b):
        """The live holders whose statements on b are voices: its predecessor's; a join's, each named predecessor's
        (the union, less the keys retired across its branches; its count is per predecessor, `meets`)."""
        if "count_over_own" in MUT: return self.live(b["holders"])
        ps = [self.by[p] for p in b["prev"]]
        if not ps: return frozenset()
        if len(ps) == 1: return self.live(ps[0]["holders"])
        return self.live(frozenset().union(*[frozenset(p["holders"]) for p in ps])) - self.retired(b["prev"])

    def recovery_ok(self, b):
        """A holder's own key recovery: (True, None), (False, reason), or None where b is no recovery."""
        if b.get("recovers") is None: return None
        h, new = b["recovers"]
        if len(b["prev"]) != 1: return (False, "recovery_changes_other_seat")
        p = self.by[b["prev"][0]]
        rk = p["recovery"].get(h)
        if rk is None or not any(k == rk and iat == b["iat"] for k, iat in b["stmts"]): return (False, "recovery_not_signed")
        want = tuple(new if k == h else k for k in p["holders"])
        others = {k: v for k, v in b["recovery"].items() if k != new}
        same = (b["holders"] == want and b["seats"] == p["seats"] and b["charter"] == p["charter"]
                and others == {k: v for k, v in p["recovery"].items() if k != h})
        if not same and "recovery_other_seat" not in MUT: return (False, "recovery_changes_other_seat")
        if "spent_unread" not in MUT:
            for x in self.past(b["id"]):
                q = self.by[x]
                if q.get("recovers") is not None and self.by[q["prev"][0]]["recovery"].get(q["recovers"][0]) == rk:
                    return (False, "recovery_commitment_spent")
        return (True, None)

    def counted(self, i):
        """The bundle's own count, its predecessors concluded: (True|False, reason)."""
        if i in self._concl: return self._concl[i]
        b = self.by[i]
        self._concl[i] = (False, "cycle")
        out = self._counted(b)
        self._concl[i] = out
        return out

    def _counted(self, b):
        if not self.consistent(b): return (False, INVALID)
        if any(not self.counted(p)[0] for p in b["prev"]): return (False, "prev_not_concluded")
        v = self.voices(b)
        if not b["prev"]:
            hs = frozenset(b["holders"])
            if "first_majority" in MUT: return (2 * len(v & hs) > len(hs), None)
            return (bool(hs) and hs <= v, None)
        rec = self.recovery_ok(b)
        if rec is not None: return rec
        return (self.meets(b, v), None)

    def concluded(self):
        return [i for i in self.by if self.counted(i)[0]]

    # ---- S'' and T on a forked bundle ----------------------------------------------------------------------
    def behind(self, b, c):
        """b is behind c: every bundle b extends is strictly in the past of a bundle c extends, b not in c's past."""
        if c["id"] == b["id"] or b["id"] in self.past(c["id"]) or not b["prev"]: return False
        cp = set().union(*[self.line(p) for p in c["prev"]]) if c["prev"] else set()
        return all(p in cp and p not in c["prev"] for p in b["prev"])

    def void(self):
        """S'': a later bundle every counted voice of which signed a bundle without it in its past that it is behind
        (self-forked), void by T at its fork point: of the live holders at its predecessor, those whose statements
        count only on the other side outnumber those only on its side (a tie voids neither); a bundle built on a void
        one is void, but a join of both lines. MUTATION root_sf_unread: nothing is void; root_t_unread: every
        self-forked bundle is void."""
        self._contest = set()
        if "root_sf_unread" in MUT: return frozenset()
        cs = [self.by[i] for i in self.concluded()]
        own = lambda ks: frozenset(self.owner(k) for k in ks)
        def voices_of(b):
            """b's counted voices, as the holders they speak for: a recovery's is the recovering holder."""
            if b.get("recovers") is not None and "recovery_exempt" not in MUT:
                return own([b["recovers"][0]])
            return own(self.voices(b) & (self.base(b) if b["prev"] else frozenset(b["holders"])))
        def rivals(b):
            """The bundles b is behind; with SIBLING_T, its siblings too (successors of the same bundles, neither in
            the other's past)."""
            out = [c for c in cs if self.behind(b, c)]
            if SIBLING_T[-1]:
                out += [c for c in cs if c["id"] != b["id"] and b["prev"] and frozenset(c["prev"]) == frozenset(b["prev"])
                        and c["id"] not in self.past(b["id"]) and b["id"] not in self.past(c["id"])]
            return out
        def forked(b):
            if not b["prev"]: return False
            if b.get("recovers") is not None and "recovery_exempt" in MUT: return False
            v = voices_of(b)
            rv = rivals(b)
            return bool(v) and all(any(k in own(self.voices(c)) for c in rv) for k in v)
        out = {b["id"] for b in cs if forked(b)}
        tv = set()
        for i in out:
            b = self.by[i]
            if "root_t_unread" in MUT: tv.add(i); continue
            mem = own(self.base(b))
            beh = rivals(b)
            chain = set()
            todo = [c["id"] for c in beh]
            while todo:
                x = todo.pop()
                if x in chain or x in self.line(b["prev"][0]) or x not in self.by: continue
                chain.add(x); todo.extend(self.by[x]["prev"])
            mine = [c for c in cs if (c["id"] == i or i in self.past(c["id"]))
                    and not any(x["id"] in self.past(c["id"]) for x in beh)]
            other = [c for c in cs if c["id"] != i and i not in self.past(c["id"])
                     and (c["id"] in chain or any(x["id"] in self.past(c["id"]) for x in beh))]
            km = set().union(*[voices_of(c) & mem for c in mine]) if mine else set()
            ko = set().union(*[voices_of(c) & mem for c in other]) if other else set()
            if len(ko - km) > len(km - ko): tv.add(i)
        def close():
            """Built on: void. A join naming a void predecessor concludes nothing, though it names the line the void
            one is behind too (MUTATION join_void_prev_spared: such a join stands)."""
            changed = True
            while changed:
                changed = False
                for c in cs:
                    if c["id"] in tv or not any(p in tv for p in c["prev"]): continue
                    if "join_void_prev_spared" in MUT and any(
                            f in self.past(c["id"]) and any(x["id"] in self.past(c["id"]) for x in cs if self.behind(self.by[f], x))
                            for f in tv):
                        continue
                    tv.add(c["id"]); changed = True
        close()
        # two recoveries of one seat, neither in the other's past, are contested: neither replaces the seat until a
        # bundle names both (one holder may not seat two keys for one seat by forking its own recovery); a bundle
        # built on some of a contest and not all is void with them (MUTATION recovery_fork_both: both conclude)
        if "recovery_fork_both" not in MUT:
            recs = [c for c in cs if c.get("recovers") is not None and c["id"] not in tv]
            seat = lambda c: (c["prev"][0], c["recovers"][0])
            groups = {}
            for c in recs:
                rivals = [x["id"] for x in recs if x["id"] != c["id"] and seat(x) == seat(c)
                          and x["id"] not in self.past(c["id"]) and c["id"] not in self.past(x["id"])]
                if rivals: groups.setdefault(seat(c), set()).update(rivals + [c["id"]])
            for (pv, _), g in groups.items():
                if any(g <= self.past(c["id"]) for c in cs if c["id"] not in tv): continue    # a bundle names both
                # T among them: of the live holders at their predecessor, those who built only on one recovery's
                # line; the recoveries short of the most are void, and only a tie at the most is contested
                if "recovery_t_unread" not in MUT:
                    mem = own(self.live(self.by[pv]["holders"]))
                    side = {}
                    for r in g:
                        xs = [x for x in cs if r in self.line(x["id"]) and not (g - {r}) & self.line(x["id"])]
                        side[r] = set().union(*[voices_of(x) & mem for x in xs]) if xs else set()
                    only = {r: len(side[r] - set().union(*[side[q] for q in g if q != r])) for r in g}
                    top = max(only.values())
                    lose = {r for r in g if only[r] < top}
                    for r in lose: tv.add(r)
                    g = g - lose
                    if len(g) < 2: continue
                for c in cs:
                    line = self.line(c["id"])
                    if line & g and not g <= line: tv.add(c["id"])
                    if c["id"] in g: self._contest.add(c["id"])
            close()
        # a forked join: joins of the same tips under different charters are contested, neither stands, and a reader
        # keeps the tips they tried to join; a bundle naming every one of them settles them (counted over those tips'
        # common holders, prev_base); one built on some and not all is void with them
        jgroups = {}
        for c in cs:
            if self.contested_join(c["id"]): jgroups.setdefault(frozenset(c["prev"]), set()).add(c["id"])
        changed = True
        while changed:
            changed = False
            for g in jgroups.values():
                if any(g <= self.past(c["id"]) for c in cs if c["id"] not in tv): continue    # settled
                for c in cs:
                    line = self.line(c["id"])
                    if c["id"] not in tv and line & g and (c["id"] in g or not g <= line):
                        tv.add(c["id"]); changed = True
                        if c["id"] in g: self._contest.add(c["id"])
        close()
        return frozenset(tv)

    # ---- for one reader ----------------------------------------------------------------------------------
    def valid(self):
        v = self.void()
        return [i for i in self.concluded() if i not in v]

    def first(self, rd):
        """The reader's first bundle, or None (`genesis_bundle_not_anchored`)."""
        firsts = [i for i in self.valid() if not self.by[i]["prev"]]
        if "anchor_unread" in MUT: return firsts[0] if firsts else None
        for i in sorted(firsts):
            if rd["anchor"] == i or (rd["thumbs"] is not None and frozenset(self.by[i]["holders"]) == rd["thumbs"]):
                return i
        return None

    def _rv(self, acked, valid):
        on = set().union(*[self.line(a) for a in acked]) if acked else set()
        out = {i for i in valid if i not in on and any(self.behind(self.by[i], self.by[a]) for a in acked)}
        changed = True
        while changed:
            changed = False
            for i in valid:
                if i not in out and i not in on and any(p in out for p in self.by[i]["prev"]):
                    out.add(i); changed = True
        return out

    def reader_line(self, rd):
        """The reader's own line: its acknowledgements in order, each taken unless it is void for the reader by
        those before it (acknowledging never un-voids); and the bundles void for the reader by that line: one
        behind a bundle it acknowledged and not on its line, and every bundle built on one, a join included (a
        join naming a predecessor void for a reader concludes nothing for it; MUTATION reader_line_unread)."""
        valid = self.valid()
        if "reader_line_unread" in MUT:
            return [a for a in rd["acks"] if a in valid], frozenset()
        acc = []
        for a in rd["acks"]:
            if a in valid and a not in self._rv(acc, valid): acc.append(a)
        return acc, frozenset(self._rv(acc, valid))

    def reader_void(self, rd):
        return self.reader_line(rd)[1]

    def held(self, rd):
        """The bundles valid for the reader: of its anchored lineage, and not void by its line."""
        f = self.first(rd)
        if f is None: return []
        rv = self.reader_void(rd)
        return [i for i in self.valid() if (i == f or f in self.past(i)) and i not in rv]

    def heads(self, rd):
        """The bundles in force for the reader: the newest it acknowledged, read by its line (MUTATION
        inforce_global: every tip of the lineage, whatever the reader acknowledged)."""
        h = self.held(rd)
        if not h: return None
        if "inforce_global" in MUT: acked = set(h)
        else: acked = {i for i in self.reader_line(rd)[0] if i in h}
        # a contested bundle the reader acknowledged leaves it at the bundles it extends (the tips a forked join
        # tried to join; the seat a contested recovery tried to replace), and so on down
        self.void()
        todo = [i for i in rd["acks"] if i in self._contest]
        held = set(h)
        while todo and "inforce_global" not in MUT:
            x = todo.pop()
            for p in self.by[x]["prev"]:
                if p in held: acked.add(p)
                elif p in self._contest: todo.append(p)
        if not acked: return (self.first(rd),)
        return tuple(sorted(i for i in acked if not any(i in self.past(j) for j in acked)))

    def in_force(self, rd):
        """(holders, seats) in force for the reader, or None (`genesis_bundle_not_anchored`)."""
        hs = self.heads(rd)
        if hs is None: return None
        return self.fold(hs)

    # ---- the fold ----------------------------------------------------------------------------------------
    def regime(self, i):
        c = self.by[i]["charter"]
        if "charter_part" in MUT and isinstance(c, dict): return repr(sorted(c.get("duties", ())))
        if "regime_reads_commitments" in MUT: return repr((c, sorted(self.by[i]["recovery"].items())))
        return repr(c) if isinstance(c, dict) else c

    def fold(self, tips):
        """The holders and seats at the tips: one tip, its own; several, the guarded fold; tips whose charters
        differ, those common to them (MUTATION fold_common: always the common; fold_union: no guard)."""
        bs = [self.by[t] for t in tips]
        if len(bs) == 1: return (frozenset(bs[0]["holders"]), frozenset(bs[0]["seats"]))
        ch = frozenset.intersection(*[frozenset(b["holders"]) for b in bs])
        cs = frozenset.intersection(*[frozenset(b["seats"]) for b in bs])
        if "fold_common" in MUT or (len({self.regime(t) for t in tips}) > 1 and "charter_folds" not in MUT):
            return (ch, cs)
        if "fold_union" in MUT:
            return (frozenset().union(*[frozenset(b["holders"]) for b in bs]),
                    frozenset().union(*[frozenset(b["seats"]) for b in bs]))
        H = self._fold_field(tips, "holders", ch, None)
        S = self._fold_field(tips, "seats", cs, H)
        return (H, S)

    def _adding(self, t, k, field):
        """The bundles on t's line that add k to `field` (k there, and in none of its predecessors')."""
        return [i for i in self.line(t) if k in self.by[i][field]
                and (not self.by[i]["prev"] or all(k not in self.by[p][field] for p in self.by[i]["prev"]))]

    def _removals(self, t, k, field):
        return [i for i in self.line(t) if self.by[i]["prev"] and k not in self.by[i][field]
                and any(k in self.by[p][field] for p in self.by[i]["prev"])]

    def _fold_field(self, tips, field, common, holders):
        union = frozenset().union(*[frozenset(self.by[t][field]) for t in tips])
        def survives(k):
            at = [t for t in tips if k in self.by[t][field]]
            for t in at:
                adds = self._adding(t, k, field)
                a = max(adds, key=lambda i: (self.by[i]["version"], i)) if adds else None
                ok = True
                for t2 in tips:
                    if t2 in at: continue
                    for r in self._removals(t2, k, field):
                        if a is None or r not in self.past(a): ok = False; break     # removed beside it
                    if not ok: break
                    # a recovery is a rotation of an existing seat, not an addition (CC 2.6.1.11: it "changes only
                    # its own seat"): the key it seats is in only where the holder's seat itself is in, so a tip
                    # that removes the holder (by a bundle that is no rotation of it) takes the rotation out
                    # (MUTATION rotation_outlives_seat)
                    rot = self.by[a].get("recovers") if a is not None and field == "holders" else None
                    if rot is not None and rot[1] == k and "rotation_outlives_seat" not in MUT:
                        for r in self._removals(t2, rot[0], field):
                            rr = self.by[r].get("recovers")
                            if (rr is None or rr[0] != rot[0]) and r not in self.past(a): ok = False; break
                    if not ok: break
                if ok: return True
            return False
        cand = [k for k in sorted(union - common) if survives(k)]
        F = set(common) if holders is None else set(common)
        H = set(common) if holders is None else set(holders)
        changed = True
        while changed:
            changed = False
            for k in cand:
                if k in F: continue
                ok = True
                for t in tips:
                    if k not in self.by[t][field]: continue
                    for a in self._adding(t, k, field):
                        b = self.by[a]
                        if not b["prev"]: continue
                        if b.get("recovers") is not None and b["recovers"][1] == k: continue   # its own recovery
                        if not self.meets(b, self.voices(b), within=H): ok = False
                if ok:
                    F.add(k); changed = True
                    if holders is None: H.add(k)
        return frozenset(F)

    # ---- grants ------------------------------------------------------------------------------------------
    def grant_row(self, gid):
        """A grant EXISTS: counted at a strict majority over the live holders of the bundles it names (one: its
        holders; several: their fold, the common holders where the charters differ), those bundles concluded and
        not void, their charters carrying the grant's duty (MUTATION grant_charter_unread); and it names the newest
        bundles in its signers' own past (the head rule: a grant naming only s1 by signers who had seen s2 concludes
        nothing; MUTATION grant_head_unread)."""
        g = self.grants.get(gid)
        if g is None: return False
        named = g["bundles"]
        if any(n not in self.valid() for n in named): return False
        if not self.antichain(named): return False
        if any(g["duty"] not in duties(self.by[n]["charter"]) for n in named) and "grant_charter_unread" not in MUT:
            return False
        seen = self.seen_of(g)
        if "grant_head_unread" not in MUT:
            lines = set().union(*[self.line(n) for n in named])
            if any(x not in lines for x in seen): return False
        base = self.live(self.fold(named)[0])
        return 2 * len(frozenset(g["signers"]) & base) > len(base)

    def antichain(self, named):
        """The bundles a grant names are an antichain: none in another's past (MUTATION grant_antichain_unread)."""
        return "grant_antichain_unread" in MUT or not any(a in self.past(b) for a in named for b in named)

    def row_past(self, i):
        """The rows of the root's lane in row i's causal past, by what they name."""
        out, todo = set(), list(self.rows[i]["names"])
        while todo:
            x = todo.pop()
            if x in out or x not in self.rows: continue
            out.add(x); todo.extend(self.rows[x]["names"])
        return out

    def seen_of(self, g):
        """The bundles a grant's signers had seen, DERIVED from the rows in the grant row's own causal past: a
        bundle is there only by being named, by an acceptance edge's attached_head_digest or by an earlier grant
        naming the bundles it is counted over (a named bundle brings its whole prev chain, so the head rule reads
        the bundle itself)."""
        out = set()
        for x in self.row_past(g["id"]):
            r = self.rows[x]
            if r["kind"] == "ack": out.add(r["head"])
            elif r["kind"] == "grant": out |= set(r["bundles"])
        return frozenset(out)

    def scope_in_force(self, rd):
        """The duties the reader's bundles in force carry: one head's charter; several, what all carry."""
        hs = self.heads(rd)
        if hs is None: return frozenset()
        return frozenset.intersection(*[duties(self.by[h]["charter"]) for h in hs])

    def grant_in_force(self, gid, rd):
        """(True|False, reason): the grant exists and RESOLVES for the reader: (i) its bundles are in the reader's
        lineage, among its heads or in their past, not on a line behind it (MUTATION grant_any_bundle); (ii) the
        scope of the bundle in force at the reader still carries its duty (MUTATION grant_scope_unread). A later
        bundle re-scopes existing grants with no re-issuance."""
        g = self.grants.get(gid)
        if g is None: return (False, "grant_unknown")
        hs = self.heads(rd)
        if hs is None: return (False, "genesis_bundle_not_anchored")
        if any(n not in self.valid() for n in g["bundles"]): return (False, "grant_bundle_void")
        if not self.antichain(g["bundles"]): return (False, "grant_bundles_not_antichain")
        if not self.grant_row(gid): return (False, "grant_count_short")
        if GRANT_COUNT[-1]:
            H = self.live(self.fold(hs)[0])
            if not 2 * len(frozenset(g["signers"]) & H) > len(H): return (False, "grant_voices_not_in_force")
        elif GRANT_LINE[-1] and "grant_line_unread" not in MUT:
            acked = self.reader_line(rd)[0]
            seen = set().union(*[self.row_past(r) for r in rd.get("rows", ()) if r in self.rows]) if rd.get("rows") else set()
            if gid not in seen and any(n in self.past(a) for n in g["bundles"] for a in acked):
                return (False, "grant_behind_reader_line")
        if "grant_any_bundle" not in MUT and not all(any(n in self.line(h) for h in hs) for n in g["bundles"]):
            return (False, "grant_not_in_reader_lineage")
        if g["duty"] not in self.scope_in_force(rd) and "grant_scope_unread" not in MUT:
            return (False, "grant_scope_not_in_force")
        return (True, None)
