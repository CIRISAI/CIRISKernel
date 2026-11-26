//! The moderator election (CC 4.5.13; CC 4.5.4 (v) and rule 2), as the rules C1 to C5 ruled it
//! (CIRISConstitution#241). The reference is `models/causal_kernel/seat.py`, its election block; the cases are
//! `check_election.py`'s.
//!
//! The rows. An election is named by its id row: the room's founding row, or the closed seating of the election
//! before. A ballot ([`SeatKind::Ballot`], [`SeatRow::ranking`] best first) and a decline ([`SeatKind::Decline`])
//! are a member's own rows, each naming its election by [`SeatRow::of`]. The seating is a counted offer of
//! `moderate` over the room under the ranked count ([`Policy::Ranked`]): signed by the winner (its acceptance),
//! `to` the winner, `of` its election, naming the rows it is counted over (its set). It names no head. A receipt
//! of a seating is a [`SeatKind::Ack`] whose `of` is that seating.
//!
//! - C1: the electorate (persons) and the candidates are read at the vacancy the id row defines: every end, in the
//!   reading row's past, of a seat the id row gave; the founding row itself where it gives none. A member admitted
//!   after the vacancy neither votes nor stands; a leaver is no voice and no candidate.
//! - C2: a seating concludes only where no person holds a duty over the room in the seats over its whole past, and
//!   no row of a later election is in its past.
//! - C3: an id row's standing is read in the naming row's past.
//! - C4: CONTAINS: a seating stands only where its set contains every other seating's set of its election (equal
//!   sets are one seat, and an election named by either is one election); sets not nested: nobody.
//! - C5: the causal close: a strict majority of the electorate, the winner and the leavers apart, receipting one
//!   seating that stood under C4 in each receipt's own past; one say per person, read causally. Once closed, no
//!   rival seating counts, and the next election is named by the closed seating.
use super::{
    concluded_over, founding, left_in_past, persons_at_with, roster_offer, roster_word, seat_scopes, signed_by, Conf,
    MembersAt, Obj, ObjOf, Policy, SeatKind, SeatLaw, SeatRow, Seats, AGENT,
};
use crate::cut::CutSpec;
use crate::layers::{Concluded, Past};
use crate::ranked::ranked;
use crate::Row;
use alloc::boxed::Box;
use alloc::collections::{BTreeMap, BTreeSet};
use alloc::string::String;
use alloc::vec::Vec;

/// "Each person ranks up to three": a ballot ranking more is void, the whole ballot.
pub const ELECTION_RANKS: usize = 3;

/// An election, as a key: a founding row (or any row that is no seating) by its id; a seating by its room, its
/// own election's key and its set, so that seatings over equal sets of one election name one election.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub(super) enum EKey<I, K> {
    Id(I),
    Seat(Obj<I, K>, Option<Box<EKey<I, K>>>, BTreeSet<I>),
}

/// What a seating reads over its own past: its election's key, the electorate, and its set.
pub(super) type View<R> =
    (Option<EKey<<R as Row>::Id, <R as Row>::Key>>, BTreeSet<<R as Row>::Key>, BTreeSet<<R as Row>::Id>);

type SeatId<R> = (<R as Row>::Id, <R as Row>::Key, String);
/// An election's key with its room, and its seatings.
type Groups<R> = BTreeMap<(ObjOf<R>, EKey<<R as Row>::Id, <R as Row>::Key>), Vec<usize>>;

/// A seating by the election: a counted offer under the ranked count.
pub(super) fn is_election<R: SeatRow>(law: &SeatLaw, o: &R) -> bool {
    o.seat_kind() == SeatKind::Offer
        && o.conf() == Some(Conf::Group)
        && law.policy_of(o.policy().map(|x| x.as_ref())) == Some(Policy::Ranked)
}

/// The election's reading over one concluded set, with the pass's cache.
pub(super) struct Ctx<'c, 'a, R: SeatRow, S: CutSpec<R>> {
    pub c: &'c Concluded<'a, R>,
    pub law: &'c SeatLaw,
    pub spec: &'c S,
    pub memo: &'c MembersAt<R>,
}

impl<'c, 'a, R: SeatRow, S: CutSpec<R>> Ctx<'c, 'a, R, S> {
    fn row(&self, i: usize) -> &'a R {
        self.c.g.row(i)
    }

    /// The concluded rows of the set in row i's past, ascending.
    fn past(&self, i: usize) -> Vec<usize> {
        self.c.cs().iter().copied().filter(|&q| self.c.g.in_past(q, i)).collect()
    }

    /// The concluded index of a row named by id, where it is concluded.
    fn idx(&self, id: &R::Id) -> Option<usize> {
        self.c.g.idx(id).filter(|&i| self.c.concluded(i))
    }

    /// The live seats over a sub-set of the rows, each taken as concluded.
    fn live(&self, rows: &[usize]) -> BTreeSet<SeatId<R>> {
        let sub = concluded_over(rows.iter().map(|&q| self.c.g.row(q)));
        let seats = Seats::build(&sub, self.law, self.spec, None, None, Some(self.memo));
        seats.recs().iter().map(|r| (r.offer.clone(), r.k.clone(), String::from(r.scope.as_ref()))).collect()
    }

    /// The seats id row `e` gave: for a founding row, each duty seat it gives a signer; for a seating, its
    /// winner's `moderate`.
    fn id_seats(&self, e: &R) -> Vec<SeatId<R>> {
        if !founding(e) {
            return e
                .to()
                .first()
                .map(|k| alloc::vec![(e.id().clone(), k.clone(), String::from("moderate"))])
                .unwrap_or_default();
        }
        let own = e.scope().map(|s| s.as_ref()).unwrap_or("");
        let decl: Vec<&str> = e.duties().iter().map(|d| d.as_ref()).filter(|d| !roster_word(d)).collect();
        let mut out = Vec::new();
        for k in e.to() {
            for sc in seat_scopes(e, k, signed_by(e, k)) {
                let s = sc.s();
                if (s != own || s == "duty") && self.law.is_duty(s, &decl) {
                    out.push((e.id().clone(), k.clone(), String::from(s)));
                }
            }
        }
        out
    }

    /// C1: the rows of `p` that end a seat id row `ei` gave, or `[ei]` where it gives none; `None` while a seat
    /// it gave has no end in `p`.
    fn vacancy(&self, ei: usize, p: &[usize]) -> Option<Vec<usize>> {
        let seats = self.id_seats(self.row(ei));
        if seats.is_empty() {
            return Some(alloc::vec![ei]);
        }
        let g = &self.c.g;
        let (mut ends, mut ended) = (Vec::new(), BTreeSet::new());
        for &w in p {
            if !matches!(self.row(w).seat_kind(), SeatKind::Withdraw | SeatKind::Unseat) || !g.in_past(ei, w) {
                continue;
            }
            let pre: Vec<usize> = p.iter().copied().filter(|&q| g.in_past(q, w)).collect();
            let before = self.live(&pre);
            let mut post = pre.clone();
            post.push(w);
            post.sort_unstable();
            let after = self.live(&post);
            let gone: Vec<&SeatId<R>> = seats.iter().filter(|s| before.contains(*s) && !after.contains(*s)).collect();
            if !gone.is_empty() {
                ends.push(w);
                ended.extend(gone.into_iter().cloned());
            }
        }
        (ended.len() == seats.len()).then_some(ends)
    }

    /// C1: the persons seated at every row of id row `ei`'s vacancy, read for row `si` over its past `p`.
    fn electorate(&self, ei: usize, si: usize, p: &[usize]) -> BTreeSet<R::Key> {
        let Some(v) = self.vacancy(ei, p) else { return BTreeSet::new() };
        let Some(obj) = self.row(si).obj() else { return BTreeSet::new() };
        let heads: Vec<R::Id> = v.iter().map(|&h| self.row(h).id().clone()).collect();
        let past = Past::new(&self.c.g, si, p);
        persons_at_with(&past, self.law, self.spec, &obj, &heads, "member", Some(self.memo))
    }

    /// The key of the election row `ei` names (its own key when it is no seating).
    fn ekey(&self, ei: usize) -> EKey<R::Id, R::Key> {
        let e = self.row(ei);
        match (is_election(self.law, e), e.obj()) {
            (true, Some(obj)) => {
                let v = self.view(ei);
                EKey::Seat(obj, v.0.map(Box::new), v.2)
            }
            _ => EKey::Id(e.id().clone()),
        }
    }

    /// Row `qi` is of the election keyed `ek`'s set, for the electorate `el`.
    fn election_row(&self, qi: usize, ek: &EKey<R::Id, R::Key>, el: &BTreeSet<R::Key>) -> bool {
        let q = self.row(qi);
        if !el.contains(q.signer()) {
            return false;
        }
        let named = |b: &R| b.of().and_then(|e| self.idx(e)).is_some_and(|ei| self.ekey(ei) == *ek);
        match q.seat_kind() {
            SeatKind::Ballot | SeatKind::Decline => named(q),
            SeatKind::Withdraw => q
                .target()
                .and_then(|t| self.idx(t))
                .map(|t| self.row(t))
                .is_some_and(|t| t.seat_kind() == SeatKind::Ballot && named(t) && t.signer() == q.signer()),
            _ => false,
        }
    }

    /// Seating `si`'s view over its own past, kept per seating for the pass.
    pub(super) fn view(&self, si: usize) -> View<R> {
        let s = self.row(si);
        if let Some(v) = self.memo.views.borrow().get(s.id()) {
            return v.clone();
        }
        let p = self.past(si);
        let ei = s.of().and_then(|e| self.idx(e)).filter(|e| p.binary_search(e).is_ok());
        let v: View<R> = match ei {
            None => (None, BTreeSet::new(), BTreeSet::new()),
            Some(ei) => {
                let ek = self.ekey(ei);
                let el = self.electorate(ei, si, &p);
                let set = s
                    .names()
                    .iter()
                    .filter(|n| {
                        self.idx(n).is_some_and(|qi| p.binary_search(&qi).is_ok() && self.election_row(qi, &ek, &el))
                    })
                    .cloned()
                    .collect();
                (Some(ek), el, set)
            }
        };
        self.memo.views.borrow_mut().insert(s.id().clone(), v.clone());
        v
    }

    /// The seatings among `rows` of the election keyed `ek`, over `obj`.
    fn seatings_of(&self, ek: &EKey<R::Id, R::Key>, rows: &[usize], obj: &ObjOf<R>) -> Vec<usize> {
        rows.iter()
            .copied()
            .filter(|&q| {
                let r = self.row(q);
                is_election(self.law, r) && r.obj().as_ref() == Some(obj) && self.view(q).0.as_ref() == Some(ek)
            })
            .collect()
    }

    /// C4 over one election's seatings: those over the one set that contains every other (equal sets one seat);
    /// none where the sets are not so nested.
    fn standing(&self, seatings: &[usize]) -> BTreeSet<usize> {
        let sets: Vec<BTreeSet<R::Id>> = seatings.iter().map(|&q| self.view(q).2).collect();
        let top: Vec<&BTreeSet<R::Id>> = sets.iter().filter(|g| sets.iter().all(|h| h.is_subset(g))).collect();
        let Some(t) = top.first() else { return BTreeSet::new() };
        if top.iter().any(|x| x != t) {
            return BTreeSet::new();
        }
        seatings.iter().zip(&sets).filter(|(_, s)| s == t).map(|(&q, _)| q).collect()
    }

    /// C5 over `rows` (a causally closed set): the set of the seatings that closed the election keyed `ek`.
    fn closure(&self, ek: &EKey<R::Id, R::Key>, rows: &[usize], obj: &ObjOf<R>) -> Option<BTreeSet<R::Id>> {
        let seats = self.seatings_of(ek, rows, obj);
        if seats.is_empty() {
            return None;
        }
        let g = &self.c.g;
        let seat_of = |a: usize| self.row(a).of().and_then(|s| self.idx(s)).filter(|s| seats.contains(s));
        let mut by_p: BTreeMap<&R::Key, Vec<usize>> = BTreeMap::new();
        for &a in rows {
            if self.row(a).seat_kind() == SeatKind::Ack && seat_of(a).is_some() {
                by_p.entry(self.row(a).signer()).or_default().push(a);
            }
        }
        let mut says: BTreeMap<BTreeSet<R::Id>, Vec<usize>> = BTreeMap::new();
        // E2: a person whose earliest receipts are of different sets has no say, and stays in the base
        let mut mute: BTreeSet<&R::Key> = BTreeSet::new();
        for (p, rs) in &by_p {
            // a person's say: its earliest receipts; of different sets, no say
            let first: Vec<usize> =
                rs.iter().copied().filter(|&a| !rs.iter().any(|&b| b != a && g.in_past(b, a))).collect();
            let sets: BTreeSet<BTreeSet<R::Id>> =
                first.iter().filter_map(|&a| seat_of(a)).map(|s| self.view(s).2).collect();
            if sets.len() != 1 {
                mute.insert(*p);
                continue;
            }
            for &a in &first {
                let Some(s) = seat_of(a) else { continue };
                let past = self.past(a);
                let here = self.seatings_of(ek, &past, obj);
                if self.standing(&here).contains(&s) {
                    says.entry(self.view(s).2).or_default().push(a);
                    break;
                }
            }
        }
        for (group, rs) in &says {
            let Some(&s) = seats.iter().find(|&&q| self.view(q).2 == *group) else { continue };
            let el = self.view(s).1;
            let Some(winner) = self.row(s).to().first() else { continue };
            let mut base = el.clone();
            base.remove(winner);
            // E1: a key departed (left, or removed, and not seated again) in a receipt's past is out of the base
            for &a in rs {
                let p = self.past(a);
                for k in self.departed(a, &p, obj) {
                    base.remove(&k);
                }
            }
            let yes = rs.iter().map(|&a| self.row(a).signer()).filter(|k| base.contains(*k)).collect::<BTreeSet<_>>();
            if base.is_empty() || 2 * yes.len() > base.len() {
                return Some(group.clone());
            }
        }
        // a room of one, or one whose every other elector has departed (E1, the limit): a standing seating closes
        // itself
        let st = self.standing(&seats);
        let gone = match rows.last() {
            Some(&anchor) => self.departed(anchor, rows, obj),
            None => BTreeSet::new(),
        };
        for &q in &seats {
            let v = self.view(q);
            let Some(w) = self.row(q).to().first() else { continue };
            if st.contains(&q) && !v.1.is_empty() && v.1.iter().all(|k| k == w || gone.contains(k)) {
                return Some(v.2);
            }
        }
        None
    }

    /// The keys that have left the room (their own leaving) or been removed from its roster (a counted unseat of
    /// their roster seat) among `p`, and not been seated again after it there. `anchor`: a row of the set whose
    /// past `p` is read as (only `p` is read).
    fn departed(&self, anchor: usize, p: &[usize], obj: &ObjOf<R>) -> BTreeSet<R::Key> {
        let g = &self.c.g;
        let mut out = left_in_past(&Past::new(g, anchor, p), obj, "member");
        for &u in p {
            let ur = self.row(u);
            let roster = ur.scope().is_some_and(|s| self.law.roster_seats.iter().any(|x| x == s.as_ref()));
            if ur.seat_kind() != SeatKind::Unseat
                || ur.obj().as_ref() != Some(obj)
                || !roster
                || ur.conf() != Some(Conf::Group)
            {
                continue;
            }
            for k in ur.to() {
                let again = p.iter().any(|&m| {
                    let mr = self.row(m);
                    mr.seat_kind() == SeatKind::Offer
                        && mr.obj().as_ref() == Some(obj)
                        && mr.to().contains(k)
                        && roster_offer(self.law, mr)
                        && g.in_past(u, m)
                });
                if !again {
                    out.insert(k.clone());
                }
            }
        }
        out
    }

    /// E3, C3: the election id row `ei` names is no longer the room's for row `ri` (read over its past `p`) where
    /// a seating of it that stood (C4) there, and whose seat has ended there, names the next election; under
    /// [`SeatLaw::election_wait_close`], where a seating closed it.
    fn superseded(&self, ei: usize, p: &[usize]) -> bool {
        let Some(obj) = self.row(ei).obj() else { return false };
        let ek = self.ekey(ei);
        if self.law.election_wait_close {
            return self.closure(&ek, p, &obj).is_some();
        }
        let here = self.seatings_of(&ek, p, &obj);
        let st = self.standing(&here);
        here.iter().any(|&x| st.contains(&x) && self.vacancy(x, p).is_some())
    }

    /// C3 and C5: id row `ei` names an election for row `ri`, read over `ri`'s past `p`: the founding row, or a
    /// seating of the room that closed its own election there, or (E3) one that stands under C4 there and whose seat
    /// has ended there (not under [`SeatLaw::election_wait_close`]).
    fn valid_id(&self, ei: usize, ri: usize, p: &[usize]) -> bool {
        let e = self.row(ei);
        let Some(obj) = self.row(ri).obj() else { return false };
        if Obj::Row(e.id().clone()) == obj {
            return true;
        }
        if !is_election(self.law, e) || e.obj().as_ref() != Some(&obj) {
            return false;
        }
        let v = self.view(ei);
        let Some(ek) = v.0.as_ref() else { return false };
        if self.closure(ek, p, &obj).as_ref() == Some(&v.2) {
            return true;
        }
        !self.law.election_wait_close && {
            let here = self.seatings_of(ek, p, &obj);
            self.standing(&here).contains(&ei) && self.vacancy(ei, p).is_some()
        }
    }

    /// The seatings among the concluded rows that do not stand: per election, every one but the closed set's where
    /// it closed (C5), else every one but those C4 stands.
    pub(super) fn beaten(&self) -> BTreeSet<usize> {
        let rows: Vec<usize> = self.c.cs().to_vec();
        let mut groups: Groups<R> = BTreeMap::new();
        for &q in &rows {
            let r = self.row(q);
            if let (true, Some(obj)) = (is_election(self.law, r), r.obj()) {
                if let Some(ek) = self.view(q).0 {
                    groups.entry((obj, ek)).or_default().push(q);
                }
            }
        }
        let mut out = BTreeSet::new();
        for ((obj, ek), el) in &groups {
            let keep = match self.closure(ek, &rows, obj) {
                Some(grp) => el.iter().copied().filter(|&q| self.view(q).2 == grp).collect(),
                None => self.standing(el),
            };
            out.extend(el.iter().copied().filter(|q| !keep.contains(q)));
        }
        out
    }

    /// Per seating, the seatings over its set of its election (itself among them): one seat.
    pub(super) fn twins(&self) -> BTreeMap<usize, Vec<usize>> {
        let el: Vec<usize> = self.c.cs().iter().copied().filter(|&q| is_election(self.law, self.row(q))).collect();
        let keys: Vec<EKey<R::Id, R::Key>> = el.iter().map(|&q| self.ekey(q)).collect();
        el.iter()
            .zip(&keys)
            .map(|(&q, k)| (q, el.iter().zip(&keys).filter(|(_, k2)| *k2 == k).map(|(&x, _)| x).collect()))
            .collect()
    }
}

/// The seating's count (C1, C2, C5 and the carried-over ballot rules), over its concluded past: the seat rule's
/// ranked arm.
pub(super) fn count<R: SeatRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
    cache: Option<&MembersAt<R>>,
) -> bool {
    let r = p.row();
    let (Some(obj), Some(e), Some(winner)) = (r.obj(), r.of(), r.to().first()) else { return false };
    if r.seat_kind() != SeatKind::Offer {
        return false;
    }
    // the row and its concluded past, as a set of their own
    let sub = concluded_over(p.rows().chain(core::iter::once(r)));
    let local = MembersAt::<R>::default();
    let cx = Ctx { c: &sub, law, spec, memo: cache.unwrap_or(&local) };
    let Some(ri) = sub.g.idx(r.id()) else { return false };
    let past = cx.past(ri);
    let Some(ei) = cx.idx(e).filter(|ei| past.binary_search(ei).is_ok()) else { return false };
    if !cx.valid_id(ei, ri, &past) || cx.superseded(ei, &past) {
        return false;
    }
    // C2: no person holds a duty over the room in the seats over the whole past
    let over = concluded_over(past.iter().map(|&q| sub.g.row(q)));
    let seats = Seats::build(&over, law, spec, None, None, Some(cx.memo));
    let agents = seats.holders(AGENT, &obj, None);
    if seats.holders("duty", &obj, None).iter().any(|k| !agents.contains(k)) {
        return false;
    }
    let (ek, el, mine) = cx.view(ri);
    let Some(ek) = ek else { return false };
    // C2: no row of a later election (one named by a seating of this election) in the past
    let later: BTreeSet<EKey<R::Id, R::Key>> = cx.seatings_of(&ek, &past, &obj).iter().map(|&q| cx.ekey(q)).collect();
    let of_later = |q: &R| q.of().and_then(|x| cx.idx(x)).is_some_and(|x| later.contains(&cx.ekey(x)));
    if past
        .iter()
        .map(|&q| sub.g.row(q))
        .any(|q| (matches!(q.seat_kind(), SeatKind::Ballot | SeatKind::Decline) || is_election(law, q)) && of_later(q))
    {
        return false;
    }
    // C5: an election closed in the past takes no further seating but its own
    if cx.closure(&ek, &past, &obj).is_some_and(|grp| grp != mine) {
        return false;
    }
    if el.is_empty() {
        return false;
    }
    let pp = Past::new(&sub.g, ri, &past);
    let left = left_in_past(&pp, &obj, "member");
    let voters: BTreeSet<R::Key> = el.iter().filter(|k| !left.contains(*k)).cloned().collect();
    let rows: Vec<&R> = past.iter().map(|&q| sub.g.row(q)).collect();
    let gone: BTreeSet<&R::Id> = rows
        .iter()
        .filter(|w| w.seat_kind() == SeatKind::Withdraw)
        .filter_map(|w| {
            let t = w.target()?;
            let tr = rows.iter().find(|q| q.id() == t)?;
            (tr.seat_kind() == SeatKind::Ballot && tr.signer() == w.signer()).then_some(t)
        })
        .collect();
    let declined: BTreeSet<&R::Key> = rows
        .iter()
        .filter(|d| d.seat_kind() == SeatKind::Decline && mine.contains(d.id()) && el.contains(d.signer()))
        .map(|d| d.signer())
        .collect();
    let ballots: Vec<(R::Key, Vec<R::Key>)> = rows
        .iter()
        .filter(|b| {
            b.seat_kind() == SeatKind::Ballot
                && mine.contains(b.id())
                && voters.contains(b.signer())
                && !gone.contains(b.id())
                && b.ranking().iter().all(|k| voters.contains(k))
                && b.ranking().len() <= ELECTION_RANKS
        })
        .map(|b| (b.signer().clone(), b.ranking().to_vec()))
        .collect();
    if ballots.is_empty() {
        return false;
    }
    let cands: Vec<R::Key> = voters.iter().filter(|k| !declined.contains(k)).cloned().collect();
    let won = ranked(&ballots, &cands, 2, false).0;
    won.as_ref() == Some(winner) && r.signer() == winner
}

/// Whether the election seating `seating` names (by id, a concluded row of `c`) is closed over `c` by the seatings
/// over `seating`'s own set (C5): the causal close, read over every concluded row.
pub fn election_closed<R: SeatRow, S: CutSpec<R>>(
    c: &Concluded<'_, R>,
    law: &SeatLaw,
    spec: &S,
    seating: &R::Id,
) -> bool {
    let memo = MembersAt::<R>::default();
    let cx = Ctx { c, law, spec, memo: &memo };
    let Some(si) = cx.idx(seating) else { return false };
    let r = cx.row(si);
    let (true, Some(obj)) = (is_election(law, r), r.obj()) else { return false };
    let (ek, _, set) = cx.view(si);
    let Some(ek) = ek else { return false };
    cx.closure(&ek, c.cs(), &obj).as_ref() == Some(&set)
}
