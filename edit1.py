import sys
p = sys.argv[1]
s = open(p).read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a, s.count(a))
    s = s.replace(a, b)


rep('''               ended by a removal from the roster. A seat so conferred is rooted in the group: its conferrer's
               withdrawal or departure does not end it.
''', '''               ended by a removal from the roster. A seat so conferred is rooted in the group: its conferrer's
               withdrawal or departure does not end it.
    member     a duty seat stands only where its holder holds the roster's seat over the same community at the
               same reading (a member seat, or the founding seat, which holds `member`). A conferral on a key that
               is not a member seats nobody, is no voice in a duty count, and stands with no further row once the
               key's widening lands. An end of the holder's stay ends the duty seats whose offers are in that
               end's past: a counted removal from the roster, or the holder's own withdrawal of a seat that holds
               `member` over the community. Nothing revives: a later admission does not seat an offer so ended. A
               conferral that is not in the end's past (made after it, or beside it) waits for the next admission
               like any conferral on a non-member. At tips the duty seat follows the folded roster.
               Only where the community's founding row is of scope `duty`.
''')

rep('''def _lone(r, P, by):''', '''def duty_room(by, obj):
    """obj is a community whose founding row seats duty holders (the only place the duty rules engage)."""
    g = by.get(obj)
    return g is not None and g["kind"] == "offer" and g["obj"] == g["id"] and g["scope"] == "duty"


def roster_seat(o, holds=None):
    """An offer of the roster's own seat over a community: a scope its duty holders do not place (ROSTER_SEATS), or the
    founding row itself, where the seat it offers holds `member`. Every other offer over the community is a duty seat."""
    if not (o["id"] == o["obj"] or o["scope"] in ROSTER_SEATS): return False
    return covers(o["scope"], "member") or "member" in K.rule(HOLDS if holds is None else holds, o["scope"], ())


def stay_ends(rows, by, holds=None):
    """The holders' own ends of a stay as a member, among `rows`: (withdrawal, key, community) for each withdrawal by a
    key of an offer of the roster's seat that names it, or of its own acceptance of one (the offer the acceptance
    names, or a standing acceptance's own scope and object). Read from the rows alone."""
    out = []
    for w in rows:
        if w["kind"] != "withdraw": continue
        t, k = by.get(w["target"]), w["signer"]
        if t is None: continue
        if t["kind"] == "accept" and t["signer"] == k:
            if t["of"] is not None: t = by.get(t["of"])
            elif t.get("obj") is not None and t.get("scope") in ROSTER_SEATS and duty_room(by, t["obj"]):
                out.append((w, k, t["obj"])); continue
            else: continue
        if t is None or t["kind"] != "offer" or k not in t["to"]: continue
        if duty_room(by, t["obj"]) and roster_seat(t, holds): out.append((w, k, t["obj"]))
    return out


def _lone(r, P, by):''')

rep('''        def unseated(o, k):
            for u in unseats:''', '''        left = stay_ends(wd, S.by, holds)                       # the holders' own ends of a stay as a member
        gone = {(k, g) for _, k, g in left}

        def resigned(o, k):
            """A duty seat whose offer is in the past of its holder's own end of its stay as a member is ended by it."""
            if "duty_revives" in MUT or "resign_keeps_duty" in MUT or not duty_seat(S.by, o): return False
            return any(k2 == k and g == o["obj"] and ((pos[o["id"]] < pos[w["id"]]) if by_arrival else (o["id"] in S.anc[w["id"]]))
                       for w, k2, g in left)

        def unseated(o, k):
            for u in unseats:''')
rep('''                if not held: continue
                # MUTATION by_arrival''', '''                if not held: continue
                # MUTATION duty_revives: a removal from the roster ends no duty seat by its past, so the next admission seats the old offer
                if "duty_revives" in MUT and ("seat", k, o["scope"], o["obj"]) not in u["cuts"] and duty_seat(S.by, o): continue
                # MUTATION by_arrival''')
rep('''for k in o["to"] if not off_ended(o, k) and accepted(o, k) and not unseated(o, k)]

        def step(live):''', '''for k in o["to"] if not off_ended(o, k) and accepted(o, k) and not unseated(o, k) and not resigned(o, k)]

        def step(live):''')
rep('''        self.live = K.fix(step, frozenset(), depth + 1)       # one link per pass: at most `depth` links below a root
''', '''        self.live = K.fix(step, frozenset(), depth + 1)       # one link per pass: at most `depth` links below a root
        # a duty seat stands only where its holder holds the roster's seat over the same community at this reading. The
        # walk is run again without the duty seats of keys that are not members, until none is left (a seat under one falls too)
        while "duty_no_member" not in MUT:
            mem = {(S.by[oid]["obj"], k) for oid, k, _, _ in self.live if roster_seat(S.by[oid], holds)}
            # MUTATION resign_keeps_duty: a key that ended its own stay still reads as a member for its duty seats
            keep = [(o, k) for o, k in base if not duty_seat(S.by, o) or (o["obj"], k) in mem
                    or ("resign_keeps_duty" in MUT and (k, o["obj"]) in gone)]
            if len(keep) == len(base): break
            base[:] = keep
            self.live = K.fix(step, frozenset(), depth + 1)
''')

rep('''    def stands(self, k, s, o, root=None):
        if not any(self._has(r, s) and (root is None or r["root"] == root) for r in K.sel(self.recs, k=k, obj=o)): return False
        fold = self.tips_fold(s, o)                             # with several tips, the fold of their changes
        return fold is None or k in fold

    def holders(self, s, o, root=None):
        got = frozenset(r["k"] for r in K.sel(self.recs, obj=o) if self._has(r, s) and (root is None or r["root"] == root))
        fold = self.tips_fold(s, o)
        return got if fold is None else got & fold
''', '''    def _member(self, rec):
        """A duty seat follows the folded roster: with several tips, its holder is among the members the fold seats."""
        if "duty_no_member" in MUT or "duty_fold_unread" in MUT or not duty_seat(self.S.by, self.S.by[rec["offer"]]): return True
        fold = self.tips_fold("member", rec["obj"])
        return fold is None or rec["k"] in fold

    def stands(self, k, s, o, root=None):
        if not any(self._has(r, s) and (root is None or r["root"] == root) and self._member(r) for r in K.sel(self.recs, k=k, obj=o)): return False
        fold = self.tips_fold(s, o)                             # with several tips, the fold of their changes
        return fold is None or k in fold

    def holders(self, s, o, root=None):
        got = frozenset(r["k"] for r in K.sel(self.recs, obj=o) if self._has(r, s) and (root is None or r["root"] == root) and self._member(r))
        fold = self.tips_fold(s, o)
        return got if fold is None else got & fold
''')
open(p, 'w').write(s)
