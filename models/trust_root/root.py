#!/usr/bin/env python3
"""The trust root's fork fold (persist's item 15): a root's lineage of genesis bundles, its count, its heads, the
fold at two tips, the bundle in force for one reader, and the root grants counted over it.

    the object   a bundle (`ceg-genesis-bundle/2`) is a signed object, not a row. Its payload: `holders`, `seats`
                 (serve_nodes), `charter` (one value), `version`, `family` (family_key_id, the lineage's name),
                 `recovery` (recovery_commitments: holder -> recovery key, keys exactly the holders) and `prev` (the
                 bundles it extends: one; two for a join). `stmts` are its holders' statements, (key, iat), one per
                 key over the one payload; `iat` is the payload's.
    the count    the first bundle is counted over every holder it lists; a later one over a strict majority of its
                 predecessor's live holders; a join over a strict majority of the live holders common to its two
                 predecessors (the text's GAP, modelled abstractly). A statement whose iat disagrees is Invalid on
                 its own, and the bundle is counted on the rest. A holder whose key is revoked with no bound leaves
                 the live holders; a statement its bound voids (on a bundle not at or before the bound) does not
                 count. The exception: a holder's own key recovery, a later bundle under that holder's recovery key
                 changing only its own seat (else `recovery_changes_other_seat`); a spent commitment (one a
                 recovery in the bundle's past used) concludes nothing.
    the heads    `version` is prev's plus one (a join: the greater plus one) and `family` is prev's: a consistency
                 check, never ranked; a mismatch is Invalid. A later bundle is a counted change of the holders'
                 roster: it names the newest bundle in its signers' own past, and S'' and T at the fork point
                 apply to it as to a roster change (MINE, the Constitution's derived reading).
    the fold     two later bundles on one bundle are both tips, and no rule picks one. The holders and seats at
                 several tips are the guarded fold (CC 2.7.8). Tips whose regime differs do not fold: a bundle's
                 regime is its WHOLE charter, compared as one value, and the holders are then those common to the
                 tips (and the seats likewise) until a bundle names both.
    in force     per reader, never global: the reader's anchor (a bundle id, or the holders' thumbprints) names its
                 first bundle (else `genesis_bundle_not_anchored`), and any other first bundle is void for it; the
                 bundle in force is the newest of the lineage the reader has acknowledged (acceptance edges with
                 attached_head_digest), read by its line; several acknowledged tips are folded; none, the anchor.
    grants       a root grant is a row counted over the holders of the bundle it names, at a strict majority
                 (accord_majority). A grant made under either successor stands as a row. Read against a reader,
                 it is in force where the bundle it names is one of the reader's heads, counted over the reader's
                 in-force holders (folded, or common where charters differ).

Receipts, equivocation records and fork-attempt records move no head and are not read here.

MUT holds planted breaks, switched on by check_root.py.
"""

MUT = set()

INVALID, VOID, CONCLUDED, REFUSED = "invalid", "void", "concluded", "refused"


def bundle(id, family, version, holders, prev=(), charter="c0", seats=(), stmts=None, iat=0, recovery=None,
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


def grant(id, bundle_id, to, scope, signers, identity=("user",)):
    """A root grant: a row counted over the holders of `bundle_id`, naming key `to` for room `scope`."""
    return {"id": id, "kind": "grant", "bundle": bundle_id, "to": to, "scope": scope, "signers": tuple(signers),
            "identity": tuple(identity)}


def reader(anchor=None, thumbs=None, acks=()):
    """A reader: its anchor (a first bundle's id, or the holders' thumbprints), and the bundles it acknowledged."""
    return {"anchor": anchor, "thumbs": frozenset(thumbs) if thumbs is not None else None, "acks": frozenset(acks)}


class Root:
    def __init__(self, bundles, revokes=(), grants=()):
        self.by = {b["id"]: b for b in bundles}
        self.revokes = list(revokes)
        self.grants = {g["id"]: g for g in grants}
        self._past, self._concl = {}, {}

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
        return True

    def base(self, b):
        """The live holders a later bundle is counted over: its predecessor's, or those common to a join's two."""
        ps = [self.by[p] for p in b["prev"]]
        if "count_over_own" in MUT: return self.live(b["holders"])
        if "join_union" in MUT: hs = frozenset().union(*[frozenset(p["holders"]) for p in ps])
        else: hs = frozenset.intersection(*[frozenset(p["holders"]) for p in ps])
        return self.live(hs)

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
        base = self.base(b)
        return (2 * len(v & base) > len(base), None)

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
        if "root_sf_unread" in MUT: return frozenset()
        cs = [self.by[i] for i in self.concluded()]
        def voices_of(b):
            return self.voices(b) & (self.base(b) if b["prev"] else frozenset(b["holders"]))
        def forked(b):
            if not b["prev"] or b.get("recovers") is not None: return False
            v = voices_of(b)
            return bool(v) and all(any(k in self.voices(c) and self.behind(b, c) for c in cs) for k in v)
        out = {b["id"] for b in cs if forked(b)}
        tv = set()
        for i in out:
            b = self.by[i]
            if "root_t_unread" in MUT: tv.add(i); continue
            mem = self.base(b)
            beh = [c for c in cs if self.behind(b, c)]
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
        # built on: void, unless a join of both lines
        changed = True
        while changed:
            changed = False
            for c in cs:
                if c["id"] in tv or not any(p in tv for p in c["prev"]): continue
                if any(f in self.past(c["id"]) and any(x["id"] in self.past(c["id"]) for x in cs if self.behind(self.by[f], x))
                       for f in tv):
                    continue
                tv.add(c["id"]); changed = True
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

    def held(self, rd):
        """The bundles valid for the reader: of its anchored lineage."""
        f = self.first(rd)
        if f is None: return []
        return [i for i in self.valid() if i == f or f in self.past(i)]

    def heads(self, rd):
        """The bundles in force for the reader: the newest it acknowledged, read by its line (MUTATION
        inforce_global: every tip of the lineage, whatever the reader acknowledged)."""
        h = self.held(rd)
        if not h: return None
        if "inforce_global" in MUT: acked = set(h)
        else: acked = {i for i in h if i in rd["acks"]}
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
        if "charter_part" in MUT and isinstance(c, dict): return c.get("protocol")
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
                        base = self.base(b) & H
                        if not 2 * len(self.voices(b) & base) > len(base): ok = False
                if ok:
                    F.add(k); changed = True
                    if holders is None: H.add(k)
        return frozenset(F)

    # ---- grants ------------------------------------------------------------------------------------------
    def grant_row(self, gid):
        """A grant as a row: counted over the live holders of the bundle it names, at a strict majority, that
        bundle concluded and not void."""
        g = self.grants.get(gid)
        if g is None or g["bundle"] not in self.valid(): return False
        base = self.live(self.by[g["bundle"]]["holders"])
        return 2 * len(frozenset(g["signers"]) & base) > len(base)

    def grant_in_force(self, gid, rd):
        """(True|False, reason): the grant names one of the reader's bundles in force and is counted at a strict
        majority over the reader's in-force holders (folded, or common where charters differ)."""
        g = self.grants.get(gid)
        if g is None: return (False, "grant_unknown")
        hs = self.heads(rd)
        if hs is None: return (False, "genesis_bundle_not_anchored")
        if g["bundle"] not in hs and "grant_any_bundle" not in MUT: return (False, "grant_not_on_bundle_in_force")
        if g["bundle"] not in self.valid(): return (False, "grant_bundle_void")
        H = self.live(self.fold(hs)[0])
        if not 2 * len(frozenset(g["signers"]) & H) > len(H): return (False, "grant_count_short")
        return (True, None)
