import sys
p = sys.argv[1] + '/crates/ciris-kernel/src/seat.rs'
s = open(p).read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a, s.count(a))
    s = s.replace(a, b)


# ---- module doc
rep('''//! Whether an offer or an unseat was validly made is concluded ([`seat_rule`]); whether a seat is live now
//! is derived ([`Seats`]). No instant, digest or list position is read.
''', '''//! Whether an offer or an unseat was validly made is concluded ([`seat_rule`]); whether a seat is live now
//! is derived ([`Seats`]). No instant, digest or list position is read.
//!
//! **A duty seat stands only on a member** (CC 4.5.4, "a non-member holds no duty"). Over a community whose
//! founding row is of scope `duty`, a seat that makes its holder a duty holder stands only where that holder
//! holds the roster's seat over the same community at the same reading: a member seat, or the founding seat
//! where it holds `member`. A conferral on a key that is not a member seats nobody and is no voice in a duty
//! count; when the key's widening lands the seat stands with no further row. An end of the holder's stay ends
//! the duty seats whose offers are in that end's past: a counted removal from the roster, or the holder's own
//! withdrawal of a seat that holds `member`. Nothing revives: a later admission does not seat an offer so
//! ended, and a conferral that is not in the end's past waits for the next admission. At tips the duty seat
//! follows the folded roster. A seat the duty holders place that is no duty (a node's detector seat) is not
//! asked for membership.
''')

# ---- helpers after duty_seat
rep('''fn founding_many<R: SeatRow>(by: &BTreeMap<&R::Id, &R>, obj: &ObjOf<R>) -> bool {''', '''/// A community whose founding row seats duty holders: the only place the duty rules engage.
fn duty_room<R: SeatRow>(by: &BTreeMap<&R::Id, &R>, obj: &ObjOf<R>) -> bool {
    row_of(by, obj).is_some_and(|g| {
        g.seat_kind() == SeatKind::Offer
            && g.obj() == Some(Obj::Row(g.id().clone()))
            && g.scope().map(|s| s.as_ref()) == Some("duty")
    })
}

/// A duty seat proper: a seat the duty holders place over their community ([`duty_seat`]) whose scope makes
/// its holder a duty holder. The seat the membership rule reaches.
fn duty_held<R: SeatRow>(law: &SeatLaw, by: &BTreeMap<&R::Id, &R>, o: &R) -> bool {
    let (Some(obj), Some(s)) = (o.obj(), o.scope()) else { return false };
    duty_seat(law, by, o) && law.is_duty(s.as_ref(), &declared(by, &obj))
}

/// An offer of the roster's own seat over a community: a scope its duty holders do not place, or the founding
/// row itself, where the seat it offers holds `member`. Every other offer over the community is a duty seat.
fn roster_seat<R: SeatRow>(law: &SeatLaw, o: &R) -> bool {
    let Some(s) = o.scope().map(|s| s.as_ref()) else { return false };
    let own = o.obj() == Some(Obj::Row(o.id().clone())) || law.roster_seats.iter().any(|x| x == s);
    own && (covers(s, "member") || law.holds.get(s).is_some_and(|h| h.iter().any(|x| x == "member")))
}

/// Whether withdrawal `w` is its signer's own end of a stay as a member, and of which community: a withdrawal
/// by a key of an offer of the roster's seat that names it, or of its own acceptance of one (the offer the
/// acceptance names, or a standing acceptance's own scope and object). Read from the rows alone.
fn stay_end<R: SeatRow>(law: &SeatLaw, by: &BTreeMap<&R::Id, &R>, w: &R) -> Option<ObjOf<R>> {
    let k = w.signer();
    let mut t = *by.get(w.target()?)?;
    if t.seat_kind() == SeatKind::Accept && t.signer() == k {
        match t.of() {
            Some(of) => t = *by.get(of)?,
            None => {
                let (obj, s) = (t.obj()?, t.scope()?);
                let roster = law.roster_seats.iter().any(|x| x == s.as_ref());
                return (roster && duty_room(by, &obj)).then_some(obj);
            }
        }
    }
    if t.seat_kind() != SeatKind::Offer || !t.to().contains(k) {
        return None;
    }
    let obj = t.obj()?;
    (duty_room(by, &obj) && roster_seat(law, t)).then_some(obj)
}

fn founding_many<R: SeatRow>(by: &BTreeMap<&R::Id, &R>, obj: &ObjOf<R>) -> bool {''')

# ---- struct field
rep('''    recs: Vec<Live<R::Id, R::Key, R::Word>>,
    /// [`Seats::tips`]''', '''    recs: Vec<Live<R::Id, R::Key, R::Word>>,
    /// Per live seat, whether it is a duty seat proper ([`duty_held`]): such a seat follows the folded roster.
    duty: Vec<bool>,
    /// [`Seats::tips`]''')

# ---- withdrawals by index, the stay ends
rep('''        for &i in cs {
            let r = g.row(i);
            match r.seat_kind() {
                SeatKind::Withdraw => {
                    if let Some(t) = r.target() {
                        wd.entry(t).or_default().push(r);
                    }
                }''', '''        // the holders' own ends of a stay as a member: (withdrawal, key, community)
        let mut left: Vec<(usize, &R::Key, ObjOf<R>)> = Vec::new();
        for &i in cs {
            let r = g.row(i);
            match r.seat_kind() {
                SeatKind::Withdraw => {
                    if let Some(t) = r.target() {
                        wd.entry(t).or_default().push(r);
                    }
                    if let Some(room) = stay_end(law, &by, r) {
                        left.push((i, r.signer(), room));
                    }
                }''')
rep('''        // `signed`: whether k signed the offer, read by the caller once per offer's signer set''', '''        // a duty seat whose offer is in the past of its holder's own end of its stay as a member is ended by it
        let resigned = |oi: usize, k: &R::Key| {
            if left.is_empty() {
                return false;
            }
            let o = g.row(oi);
            let oo = o.obj();
            duty_held(law, &by, o)
                && left.iter().any(|(w, k2, room)| *k2 == k && oo.as_ref() == Some(room) && g.in_past(oi, *w))
        };
        // `signed`: whether k signed the offer, read by the caller once per offer's signer set''')
rep('''                if !off_ended(o, k) && accepted(o, k, signed) && !unseated(oi, k) {''',
    '''                if !off_ended(o, k) && accepted(o, k, signed) && !unseated(oi, k) && !resigned(oi, k) {''')

# ---- the walk as a closure, run again without the duty seats of non-members
old_walk = s[s.index("        // one link per pass: at most `depth` links below a root\n"):s.index("        let recs = at\n")]
new_walk = '''        // one link per pass: at most `depth` links below a root
        type At<'r, I, K> = BTreeMap<(&'r I, &'r K), (usize, Root<I, K>)>;
        let walk = |base: &[(usize, &'a R::Key)]| {
            let mut at: At<'a, R::Id, R::Key> = BTreeMap::new();
            for _ in 0..(law.depth + 1) {
                let mut add: Vec<Step<'a, R>> = Vec::new();
                for &(oi, k) in base {
                    let o = g.row(oi);
                    let key = (o.id(), k);
                    if at.contains_key(&key) {
                        continue;
                    }
                    let obj = o.obj();
                    match o.conf() {
                        Some(Conf::Own) => {
                            let founding = obj == Some(Obj::Row(o.id().clone()));
                            let ok = founding
                                || !obj.as_ref().is_some_and(|x| founding_many(&by, x))
                                || matches!(&obj, Some(Obj::Row(f)) if at.contains_key(&(f, o.signer())));
                            if ok {
                                add.push((key, (0, Root::Key(o.signer().clone()))));
                            }
                        }
                        Some(Conf::Group) => {
                            if let Some(x) = obj {
                                add.push((key, (0, Root::Group(x))));
                            }
                        }
                        _ if eq(o) => {
                            if let Some(x) = obj {
                                add.push((key, (0, Root::Group(x))));
                            }
                        }
                        Some(Conf::Seat) => {
                            if let Some(u) = o.under() {
                                if let (Some(up), Some(hit)) = (by.get(u), at.get(&(u, o.signer()))) {
                                    if may_confer(law, *up, o) {
                                        add.push((key, (hit.0 + 1, hit.1.clone())));
                                    }
                                }
                            }
                        }
                        None => {}
                    }
                }
                if add.is_empty() {
                    break;
                }
                for (k, v) in add {
                    at.entry(k).or_insert(v);
                }
            }
            at
        };
        let mut at = walk(&base);
        // a duty seat stands only where its holder holds the roster's seat over the same community at this
        // reading. The walk is run again without the duty seats of keys that are not members, until none is
        // left (a seat under one falls too). Where no offer is a duty seat proper, nothing is run again.
        let held: Vec<bool> = base.iter().map(|&(oi, _)| duty_held(law, &by, g.row(oi))).collect();
        if held.contains(&true) {
            let mut on: Vec<bool> = base.iter().map(|_| true).collect();
            loop {
                let mem: BTreeSet<(ObjOf<R>, &R::Key)> = at
                    .keys()
                    .filter_map(|&(oid, k)| {
                        let o = by[oid];
                        if roster_seat(law, o) {
                            o.obj().map(|x| (x, k))
                        } else {
                            None
                        }
                    })
                    .collect();
                let mut dropped = false;
                for (j, &(oi, k)) in base.iter().enumerate() {
                    if on[j] && held[j] && !g.row(oi).obj().is_some_and(|x| mem.contains(&(x, k))) {
                        on[j] = false;
                        dropped = true;
                    }
                }
                if !dropped {
                    break;
                }
                let kept: Vec<(usize, &'a R::Key)> =
                    base.iter().zip(&on).filter(|(_, keep)| **keep).map(|(b, _)| *b).collect();
                at = walk(&kept);
            }
        }
'''
s = s.replace(old_walk, new_walk)

rep('''        let recs = at
            .into_iter()
            .filter_map(|((oid, k), (depth, root))| {
                let o = by[oid];
                Some(Live { offer: oid.clone(), k: k.clone(), scope: o.scope()?.clone(), obj: o.obj()?, depth, root })
            })
            .collect();
        Seats {
            c,
            cut,
            law,
            spec,
            by,
            stale,
            recs,''', '''        let recs: Vec<Live<R::Id, R::Key, R::Word>> = at
            .into_iter()
            .filter_map(|((oid, k), (depth, root))| {
                let o = by[oid];
                Some(Live { offer: oid.clone(), k: k.clone(), scope: o.scope()?.clone(), obj: o.obj()?, depth, root })
            })
            .collect();
        let duty = recs.iter().map(|r| by.get(&r.offer).is_some_and(|o| duty_held(law, &by, *o))).collect();
        Seats {
            c,
            cut,
            law,
            spec,
            by,
            stale,
            recs,
            duty,''')

# ---- stands / holders: the folded roster
rep('''    /// Whether key `k` stands in scope `s` over `o` (rooted at `root`, when given). With several tips, a key
    /// stands only if the fold of their changes seats it ([`Seats::tips_fold`]).
    pub fn stands(&self, k: &R::Key, s: &str, o: &ObjOf<R>, root: Option<&Root<R::Id, R::Key>>) -> bool {
        let any =
            self.recs.iter().any(|r| r.k == *k && r.obj == *o && self.has(r, s) && root.is_none_or(|x| r.root == *x));
        any && self.tips_fold(s, o).is_none_or(|c| c.contains(k))
    }
''', '''    /// A duty seat follows the folded roster: with several tips, its holder is among the members the fold
    /// seats. Any other seat is not asked.
    fn member(&self, i: usize) -> bool {
        let r = &self.recs[i];
        !self.duty[i] || self.tips_fold("member", &r.obj).is_none_or(|c| c.contains(&r.k))
    }

    /// The live seats that give scope `s` over `o` (rooted at `root`, when given), by index.
    fn giving<'s>(
        &'s self,
        s: &'s str,
        o: &'s ObjOf<R>,
        root: Option<&'s Root<R::Id, R::Key>>,
    ) -> impl Iterator<Item = &'s Live<R::Id, R::Key, R::Word>> + 's {
        self.recs
            .iter()
            .enumerate()
            .filter(move |(i, r)| r.obj == *o && self.has(r, s) && root.is_none_or(|x| r.root == *x) && self.member(*i))
            .map(|(_, r)| r)
    }

    /// Whether key `k` stands in scope `s` over `o` (rooted at `root`, when given). With several tips, a key
    /// stands only if the fold of their changes seats it ([`Seats::tips_fold`]).
    pub fn stands(&self, k: &R::Key, s: &str, o: &ObjOf<R>, root: Option<&Root<R::Id, R::Key>>) -> bool {
        let any = self.giving(s, o, root).any(|r| r.k == *k);
        any && self.tips_fold(s, o).is_none_or(|c| c.contains(k))
    }
''')
rep('''        let got: BTreeSet<R::Key> = self
            .recs
            .iter()
            .filter(|r| r.obj == *o && self.has(r, s) && root.is_none_or(|x| r.root == *x))
            .map(|r| r.k.clone())
            .collect();
        match self.tips_fold(s, o) {
            None => got,
            Some(c) => got.intersection(&c).cloned().collect(),
        }
    }
''', '''        let got: BTreeSet<R::Key> = self.giving(s, o, root).map(|r| r.k.clone()).collect();
        match self.tips_fold(s, o) {
            None => got,
            Some(c) => got.intersection(&c).cloned().collect(),
        }
    }
''')
rep('''        let got: BTreeSet<R::Key> = self
            .recs
            .iter()
            .filter(|r| {
                r.obj == *o && self.has(r, s) && root.is_none_or(|x| r.root == *x) && self.offer_covers(&r.offer, &t)
            })
            .map(|r| r.k.clone())
            .collect();''', '''        let got: BTreeSet<R::Key> =
            self.giving(s, o, root).filter(|r| self.offer_covers(&r.offer, &t)).map(|r| r.k.clone()).collect();''')
rep('''        let any = self.recs.iter().any(|r| {
            r.k == *k
                && r.obj == *o
                && self.has(r, s)
                && root.is_none_or(|x| r.root == *x)
                && self.offer_covers(&r.offer, &t)
        });''', '''        let any = self.giving(s, o, root).any(|r| r.k == *k && self.offer_covers(&r.offer, &t));''')

# ---- the count
rep('''/// offer that seats it in `scope` over `obj`. A version with a key's leaving in its own past does not count
/// that key (`RosterHead.leaving_binds_by_past`).
pub fn left_in_past''', '''/// offer that seats it in `scope` over `obj`. A version with a key's leaving in its own past does not count
/// that key (`RosterHead.leaving_binds_by_past`). A count over the duty holders also leaves out
/// [`stay_ended_in_past`], which [`count_members`] subtracts.
pub fn left_in_past''')
rep('''/// The keys that signed a counted row: its signer, its cosigners, and the signers of the cosignatures it''',
    '''/// The keys whose own end of a stay as a member of `obj` is among `p` (a counted row's past) with no
/// admission of the key after it there: a count over the duty holders with such an end in its past does not
/// count that key, since the end ended its duty seats. Empty where `obj` is not a community whose founding row
/// seats duty holders. A counted removal needs no such reading: it is a head, read by [`members_at`].
pub fn stay_ended_in_past<R: SeatRow>(p: &Past<'_, '_, R>, law: &SeatLaw, obj: &ObjOf<R>) -> BTreeSet<R::Key> {
    let by: BTreeMap<&R::Id, &R> = p.rows().map(|q| (q.id(), q)).collect();
    let mut out = BTreeSet::new();
    if !duty_room(&by, obj) {
        return out;
    }
    for w in p.rows().filter(|w| w.seat_kind() == SeatKind::Withdraw) {
        if stay_end(law, &by, w).as_ref() != Some(obj) {
            continue;
        }
        let k = w.signer();
        let back = p.rows().any(|m| {
            m.seat_kind() == SeatKind::Offer
                && m.obj().as_ref() == Some(obj)
                && m.to().contains(k)
                && roster_seat(law, m)
                && p.past(w.id(), m.id())
        });
        if !back {
            out.insert(k.clone());
        }
    }
    out
}

/// The keys that signed a counted row: its signer, its cosigners, and the signers of the cosignatures it''')
rep('''    for k in left_in_past(p, &over, counted) {
        mem.remove(&k);
    }
    mem
}''', '''    for k in left_in_past(p, &over, counted) {
        mem.remove(&k);
    }
    // a count over the duty holders: a holder whose own end of its stay as a member is in the row's past
    let duties: Vec<&str> = match &over {
        Obj::Row(i) => p.get(i).map_or(Vec::new(), |g| g.duties().iter().map(|d| d.as_ref()).collect()),
        Obj::Key(_) => Vec::new(),
    };
    if !mem.is_empty() && law.is_duty(counted, &duties) {
        for k in stay_ended_in_past(p, law, &over) {
            mem.remove(&k);
        }
    }
    mem
}''')
rep('''/// names ([`members_at`]: read from the concluded rows in each head's past, intersected over the heads), less
/// the keys whose own leaving is in the row's past ([`left_in_past`]). With [`voices`], what''',
    '''/// names ([`members_at`]: read from the concluded rows in each head's past, intersected over the heads), less
/// the keys whose own leaving is in the row's past ([`left_in_past`]; for a count over the duty holders, the
/// end of a holder's stay as a member too, [`stay_ended_in_past`]). With [`voices`], what''')
rep('''///   a function of the head *and the row*: cache [`members_at`] per head if you will, and subtract
///   `left_in_past` on every count.''', '''///   a function of the head *and the row*: cache [`members_at`] per head if you will, and subtract
///   `left_in_past` on every count (and, for a count over the duty holders, [`stay_ended_in_past`]).''')
open(p, 'w').write(s)
