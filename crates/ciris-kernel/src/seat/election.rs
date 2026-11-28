//! The moderator election (CC 4.5.13; CC 4.5.4 (v) and rule 2), as the rules C1 to C5 ruled it
//! (CIRISConstitution#241). The reference is `models/causal_kernel/seat.py`, its election block; the cases are
//! `check_election.py`'s.
//!
//! The rows. An election is named by its id row: the room's founding row, or the closed seating of the election
//! before. A ballot ([`SeatKind::Ballot`], [`SeatRow::ranking`] best first) and a decline ([`SeatKind::Decline`])
//! are a member's own rows, each naming its election by [`SeatRow::of`]. The seating is a counted offer of
//! `moderate` over the room under the ranked count ([`Policy::Ranked`]): signed by the winner (its acceptance),
//! `to` the winner, `of` its election, naming the rows it is counted over (its set: ballots, the voters' own
//! withdrawals of them, declines, the leavings it reads, and the end or ends of the seat it reads the electorate
//! at); its heads, if any, are placement only. A receipt of a seating is a [`SeatKind::Ack`] whose `of` is it.
//!
//! - C1, F2: the electorate (persons) and the candidates are read at the vacancy the seating names: the ends of the
//!   id row's seat it names; the founding row itself where it gives none. A member admitted after the vacancy
//!   neither votes nor stands.
//! - F1: every input to the count comes from the set, so seatings over equal sets count alike.
//! - C2: a seating concludes only where no person holds a duty over the room in the seats over its whole past, and
//!   no row of a later election is in its past.
//! - C3, E3: an id row's standing is read in the naming row's past; a seating that stood, never closed, and whose
//!   seat has ended names the next election, and supersedes its own.
//! - C4: CONTAINS: a seating stands only where its set contains every other seating's set of its election (equal
//!   sets are one seat, and an election named by either is one election); sets not nested: nobody.
//! - C5, E1, E2: the causal close: a strict majority of the electorate, the winner and the departed apart,
//!   receipting one seating that stood under C4 in each receipt's own past; one say per person, read causally (an
//!   equivocator has no say and stays in the base). Once closed, no rival seating counts.
//! - F3: a next election stands only while its id row stands, for the rows held.
use super::{
    concluded_over, founding, persons_at_with, persons_of, roster_offer, roster_word, seat_scopes, signed_by, stay_end,
    Conf, MembersAt, Obj, ObjOf, Policy, SeatKind, SeatLaw, SeatRow, Seats, AGENT,
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
/// What a seating reads over its own past: its election's key, the electorate, its set, and the vacancy ends in it.
pub(super) type View<R> = (
    Option<EKey<<R as Row>::Id, <R as Row>::Key>>,
    BTreeSet<<R as Row>::Key>,
    BTreeSet<<R as Row>::Id>,
    BTreeSet<<R as Row>::Id>,
);

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
    /// it gave has no end in `p`. `named` (F2): only the rows a seating names are read as ends. Only a holder's own
    /// withdrawal, or an unseat naming a holder, can end one, so no other row is tried.
    fn vacancy(&self, ei: usize, p: &[usize], named: Option<&BTreeSet<R::Id>>) -> Option<Vec<usize>> {
        let seats = self.id_seats(self.row(ei));
        if seats.is_empty() {
            return Some(alloc::vec![ei]);
        }
        let holders: BTreeSet<&R::Key> = seats.iter().map(|(_, k, _)| k).collect();
        let g = &self.c.g;
        let (mut ends, mut ended) = (Vec::new(), BTreeSet::new());
        for &w in p {
            let wr = self.row(w);
            let touches = match wr.seat_kind() {
                SeatKind::Withdraw => holders.contains(wr.signer()),
                SeatKind::Unseat => wr.to().iter().any(|k| holders.contains(k)),
                _ => false,
            };
            if !touches || !g.in_past(ei, w) || named.is_some_and(|n| !n.contains(wr.id())) {
                continue;
            }
            // a lay-down behind the reader's line is no vacancy end for it (H4)
            if self.memo.rends.borrow().contains(wr.id()) {
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
    fn electorate(&self, ei: usize, si: usize, p: &[usize], named: Option<&BTreeSet<R::Id>>) -> BTreeSet<R::Key> {
        let Some(v) = self.vacancy(ei, p, named) else { return BTreeSet::new() };
        let Some(obj) = self.row(si).obj() else { return BTreeSet::new() };
        let heads: Vec<R::Id> = v.iter().map(|&h| self.row(h).id().clone()).collect();
        // the persons at EVERY end, each end read alone: several heads are folded (the head rules), so the persons
        // common to the ends are taken here
        let mut out: Option<BTreeSet<R::Key>> = None;
        for h in heads.chunks(1) {
            // each end read over its own past only (C1, F1, F2: a withdrawal in the seating's past that the seating
            // does not name strikes nobody, though members_at reads every withdrawal of a counting row's past for a
            // roster count)
            let Some(e) = self.c.g.idx(&h[0]) else { continue };
            let pe: Vec<usize> = p.iter().copied().filter(|&q| q == e || self.c.g.in_past(q, e)).collect();
            let past_e = Past::new(&self.c.g, si, &pe);
            let at = persons_at_with(&past_e, self.law, self.spec, &obj, h, "member", Some(self.memo));
            out = Some(match out {
                None => at,
                Some(acc) => acc.intersection(&at).cloned().collect(),
            });
        }
        out.unwrap_or_default()
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

    /// Row `qi` is of the election keyed `ek`'s set, for the electorate `el`, read over the seating's past `p`: a
    /// ballot or decline naming that election, a withdrawal of such a ballot by its own signer, or a leaving (its
    /// own end of its stay, or a counted removal from the roster) of a member of the electorate (F1).
    fn election_row(
        &self,
        qi: usize,
        ek: &EKey<R::Id, R::Key>,
        el: &BTreeSet<R::Key>,
        p: &[usize],
        obj: &ObjOf<R>,
        ends: &[usize],
    ) -> bool {
        let q = self.row(qi);
        let in_p = |id: &R::Id| self.idx(id).filter(|i| p.binary_search(i).is_ok());
        // N2: a leaving in the past of the vacancy end the seating reads is settled there, and is no row of the set
        let window = !ends.iter().any(|&e| self.c.g.in_past(qi, e));
        if q.seat_kind() == SeatKind::Unseat {
            let roster = q.scope().is_some_and(|s| self.law.roster_seats.iter().any(|x| x == s.as_ref()));
            return q.conf() == Some(Conf::Group)
                && q.obj().as_ref() == Some(obj)
                && roster
                && q.to().iter().any(|k| el.contains(k))
                && window;
        }
        if q.seat_kind() == SeatKind::Withdraw && el.contains(q.signer()) {
            let by: BTreeMap<&R::Id, &R> = p.iter().map(|&i| (self.row(i).id(), self.row(i))).collect();
            let held = |a: &R| by.contains_key(a.id()) && self.idx(a.id()).is_some_and(|ai| self.c.g.in_past(ai, qi));
            if stay_end(self.law, &by, q, &held).as_ref() == Some(obj) {
                return window;
            }
        }
        // signed by a member of the electorate, or by a live key of one (counts over persons; ruled on #224)
        if !el.contains(q.signer()) {
            let rows: Vec<&R> = p.iter().map(|&i| self.row(i)).collect();
            if persons_of(&rows, self.law, self.spec, &BTreeSet::from([q.signer().clone()]), el).is_empty() {
                return false;
            }
        }
        let named = |b: &R| b.of().and_then(in_p).is_some_and(|ei| self.ekey(ei) == *ek);
        match q.seat_kind() {
            SeatKind::Ballot | SeatKind::Decline => named(q),
            SeatKind::Withdraw => q
                .target()
                .and_then(in_p)
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
            None => (None, BTreeSet::new(), BTreeSet::new(), BTreeSet::new()),
            Some(ei) => {
                let ek = self.ekey(ei);
                let mut named: BTreeSet<R::Id> = s.names().iter().cloned().collect();
                // (3): an end of the seat is in the set only where a ballot of the set names it, the ballot's signer a
                // member there (it votes on that end); an end no such ballot names is part of no set
                if let Some(obj) = s.obj() {
                    let e_id = self.row(ei).id().clone();
                    let ballots: Vec<&R> = named
                        .iter()
                        .filter_map(|n| self.idx(n).filter(|i| p.binary_search(i).is_ok()))
                        .map(|i| self.row(i))
                        .filter(|b| b.seat_kind() == SeatKind::Ballot && b.of() == Some(&e_id))
                        .collect();
                    let cand: Vec<R::Id> = self
                        .vacancy(ei, &p, Some(&named))
                        .unwrap_or_default()
                        .iter()
                        .map(|&e| self.row(e).id().clone())
                        .filter(|e| *e != e_id)
                        .collect();
                    let past = Past::new(&self.c.g, si, &p);
                    for e in cand {
                        let at = persons_at_with(
                            &past,
                            self.law,
                            self.spec,
                            &obj,
                            core::slice::from_ref(&e),
                            "member",
                            Some(self.memo),
                        );
                        if !ballots.iter().any(|b| b.names().contains(&e) && at.contains(b.signer())) {
                            named.remove(&e);
                        }
                    }
                }
                let el = self.electorate(ei, si, &p, Some(&named));
                let vend: Vec<usize> = self.vacancy(ei, &p, Some(&named)).unwrap_or_default();
                let ends: BTreeSet<R::Id> =
                    vend.iter().map(|&e| self.row(e).id().clone()).filter(|e| named.contains(e)).collect();
                let obj = s.obj();
                let set = s
                    .names()
                    .iter()
                    .filter(|n| {
                        self.idx(n).is_some_and(|qi| {
                            p.binary_search(&qi).is_ok()
                                && obj.as_ref().is_some_and(|o| self.election_row(qi, &ek, &el, &p, o, &vend))
                        })
                    })
                    .cloned()
                    .chain(ends.iter().cloned())
                    .collect();
                (Some(ek), el, set, ends)
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
        // (2): a key that said two things in the election, for this reader, is no voice and is out of the base
        let fork = self.forkers(ek, rows, rows, obj, &BTreeSet::new());
        for (p, rs) in &by_p {
            if fork.contains(*p) {
                continue;
            }
            // a person's say: its earliest receipts; of different sets, no say
            // earliest: none of the person's other receipts in its past; only a lower level can be
            let first: Vec<usize> = rs
                .iter()
                .copied()
                .filter(|&a| !rs.iter().any(|&b| g.level(b) < g.level(a) && g.in_past(b, a)))
                .collect();
            let sets: BTreeSet<BTreeSet<R::Id>> =
                first.iter().filter_map(|&a| seat_of(a)).map(|s| self.view(s).2).collect();
            if sets.len() != 1 {
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
        // E1 (the fifth read, G2): one base per election for a reader: a key departed (left, or removed, not seated
        // again) over the rows held (the reference's `departures(rows)`) is out of it for every group alike, and its
        // receipts count for nothing. H1: unless the key's leaving (or removal) holds its receipt, which then counts, the key staying in the base
        let deps = self.departures(rows, obj);
        let held = |k: &R::Key, d: usize| by_p.get(k).is_some_and(|rs| rs.iter().any(|&a| g.in_past(a, d)));
        let mut gone: BTreeSet<R::Key> = deps
            .iter()
            .filter(|(k, _)| !deps.iter().any(|(k2, d2)| k2 == k && held(k2, *d2)))
            .map(|(k, _)| k.clone())
            .collect();
        // the base is the INTERSECTION of the members at every end any seating of the election names, over the rows
        // held: C1 applied election-wide (each seating still counts its own electorate). A lay-down that does not
        // stand for the reader (H4: behind its line) is no end for it; that comes with the head rules
        let mut els = seats.iter().map(|&q| self.view(q).1);
        let first = els.next().unwrap_or_default();
        let common: BTreeSet<R::Key> = els.fold(first, |acc, e| acc.intersection(&e).cloned().collect());
        let mut met: Vec<&BTreeSet<R::Id>> = Vec::new();
        for (group, rs) in &says {
            let Some(&s) = seats.iter().find(|&&q| self.view(q).2 == *group) else { continue };
            let el = common.clone();
            let Some(winner) = self.row(s).to().first() else { continue };
            let mut base = el.clone();
            base.remove(winner);
            base.retain(|k| !gone.contains(k));
            base.retain(|k| !fork.contains(k));
            let yes = rs.iter().map(|&a| self.row(a).signer()).filter(|k| base.contains(*k)).collect::<BTreeSet<_>>();
            if base.is_empty() || 2 * yes.len() > base.len() {
                met.push(group);
            }
        }
        // (ii), the rule: where more than one group meets its close over the rows held, none is closed; nothing is
        // picked by order
        match met.len() {
            1 => return Some(met[0].clone()),
            0 => {}
            _ => return None,
        }
        // a room of one, or one whose every other elector has departed (E1, the limit): a standing seating closes
        // itself
        let st = self.standing(&seats);
        gone.extend(fork.iter().cloned());
        for &q in &seats {
            let v = self.view(q);
            let Some(w) = self.row(q).to().first() else { continue };
            if st.contains(&q) && !v.1.is_empty() && v.1.iter().all(|k| k == w || gone.contains(k)) {
                return Some(v.2);
            }
        }
        None
    }

    /// (2): the keys that said two things in the election keyed `ek` among `rows`: two rows of the election's own,
    /// signed by the key, neither in the other's past. The election's own rows: a ballot or decline naming it, a
    /// withdrawal of such a ballot, a receipt of one of its seatings, one of its seatings, a lay-down read as its
    /// vacancy (an end in the set of one of its seatings, or among `ends0`). Rows in two rooms, or of two elections,
    /// are never a fork.
    fn forkers(
        &self,
        ek: &EKey<R::Id, R::Key>,
        rows: &[usize],
        resolve: &[usize],
        obj: &ObjOf<R>,
        ends0: &BTreeSet<R::Id>,
    ) -> BTreeSet<R::Key> {
        let g = &self.c.g;
        let seats = self.seatings_of(ek, rows, obj);
        let sids: BTreeSet<&R::Id> = seats.iter().map(|&q| self.row(q).id()).collect();
        let mut ends: BTreeSet<R::Id> = ends0.clone();
        for &q in &seats {
            ends.extend(self.view(q).3);
        }
        // G1: a counted unseat (a room act others cosign) is never its signer's election row: only a holder's own
        // lay-down of the seat is
        ends.retain(|e| self.idx(e).is_some_and(|i| self.row(i).seat_kind() == SeatKind::Withdraw));
        // a row's election is resolved over the rows given for that (the seating's past, or the rows held)
        let at = |id: &R::Id| self.idx(id).filter(|i| resolve.binary_search(i).is_ok());
        let named = |b: &R| b.of().and_then(at).is_some_and(|e| self.ekey(e) == *ek);
        // (4): the fork is per verified signing key (the signer where none is given): a voice's rows signed through two
        // room keys are two keys' rows
        let mut mine: BTreeMap<(&R::Key, &R::Key), Vec<usize>> = BTreeMap::new();
        for &q in rows {
            let r = self.row(q);
            let own = match r.seat_kind() {
                SeatKind::Ballot | SeatKind::Decline => named(r),
                SeatKind::Ack => r.of().is_some_and(|o| sids.contains(o)),
                SeatKind::Withdraw => {
                    ends.contains(r.id())
                        || r.target()
                            .and_then(at)
                            .map(|t| self.row(t))
                            .is_some_and(|t| t.seat_kind() == SeatKind::Ballot && t.signer() == r.signer() && named(t))
                }
                _ => sids.contains(r.id()) || ends.contains(r.id()),
            };
            if own {
                mine.entry((r.signer(), r.signing_key().unwrap_or(r.signer()))).or_default().push(q);
            }
        }
        mine.into_iter()
            .filter(|(_, rs)| {
                // a key whose rows form one chain (each, by level, in the next one's past) said one thing: no pairs
                let mut by_level = rs.clone();
                by_level.sort_by_key(|&q| (g.level(q), q));
                if by_level.windows(2).all(|w| g.in_past(w[0], w[1])) {
                    return false;
                }
                rs.iter().enumerate().any(|(i, &a)| rs[i + 1..].iter().any(|&b| !g.in_past(a, b) && !g.in_past(b, a)))
            })
            .map(|((k, _), _)| k.clone())
            .collect()
    }

    /// Each leaving of the room (the key's own end of its stay) or counted removal from its roster among `p`, with
    /// the row, the key not seated again after it there.
    fn departures(&self, p: &[usize], obj: &ObjOf<R>) -> Vec<(R::Key, usize)> {
        let g = &self.c.g;
        let by: BTreeMap<&R::Id, &R> = p.iter().map(|&i| (self.row(i).id(), self.row(i))).collect();
        let again = |k: &R::Key, d: usize| {
            p.iter().any(|&m| {
                let mr = self.row(m);
                mr.seat_kind() == SeatKind::Offer
                    && mr.obj().as_ref() == Some(obj)
                    && mr.to().contains(k)
                    && roster_offer(self.law, mr)
                    && g.in_past(d, m)
            })
        };
        let mut out = Vec::new();
        for &w in p {
            let wr = self.row(w);
            match wr.seat_kind() {
                SeatKind::Withdraw => {
                    let held = |a: &R| by.contains_key(a.id()) && self.idx(a.id()).is_some_and(|ai| g.in_past(ai, w));
                    if stay_end(self.law, &by, wr, &held).as_ref() == Some(obj) && !again(wr.signer(), w) {
                        out.push((wr.signer().clone(), w));
                    }
                }
                SeatKind::Unseat => {
                    let roster = wr.scope().is_some_and(|s| self.law.roster_seats.iter().any(|x| x == s.as_ref()));
                    if wr.obj().as_ref() == Some(obj) && roster && wr.conf() == Some(Conf::Group) {
                        out.extend(wr.to().iter().filter(|k| !again(k, w)).map(|k| (k.clone(), w)));
                    }
                }
                _ => {}
            }
        }
        out
    }

    /// E3, C3: the election id row `ei` names is no longer the room's for row `ri` (read over its past `p`) where
    /// a seating of it that stood (C4) there, and whose seat has ended there, names the next election.
    fn superseded(&self, ei: usize, p: &[usize]) -> bool {
        let Some(obj) = self.row(ei).obj() else { return false };
        let ek = self.ekey(ei);
        let here = self.seatings_of(&ek, p, &obj);
        let st = self.standing(&here);
        here.iter().any(|&x| st.contains(&x) && self.vacancy(x, p, None).is_some())
    }

    /// C3 and C5: id row `ei` names an election for row `ri`, read over `ri`'s past `p`: the founding row, or a
    /// seating of the room that closed its own election there, or (E3) one that stands under C4 there and whose seat
    /// has ended there.
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
        let here = self.seatings_of(ek, p, &obj);
        self.standing(&here).contains(&ei) && self.vacancy(ei, p, None).is_some()
    }

    /// The seatings among the concluded rows that do not stand: per election, every one but the closed set's where
    /// it closed (C5), else every one but those C4 stands.
    pub(super) fn beaten(&self, void: &BTreeSet<usize>) -> BTreeSet<usize> {
        let rows: Vec<usize> = self.c.cs().to_vec();
        let mut groups: Groups<R> = BTreeMap::new();
        let mut out: BTreeSet<usize> =
            rows.iter().copied().filter(|&q| void.contains(&q) && is_election(self.law, self.row(q))).collect();
        for &q in &rows {
            let r = self.row(q);
            if void.contains(&q) {
                continue;
            }
            if let (true, Some(obj)) = (is_election(self.law, r), r.obj()) {
                if let Some(ek) = self.view(q).0 {
                    groups.entry((obj, ek)).or_default().push(q);
                }
            }
        }
        for ((obj, ek), el) in &groups {
            let keep = match self.closure(ek, &rows, obj) {
                Some(grp) => el.iter().copied().filter(|&q| self.view(q).2 == grp).collect(),
                None => self.standing(el),
            };
            out.extend(el.iter().copied().filter(|q| !keep.contains(q)));
        }
        // F3: a next election stands only while its id row stands, for the rows held
        loop {
            let add: Vec<usize> = rows
                .iter()
                .copied()
                .filter(|&q| is_election(self.law, self.row(q)))
                .filter(|q| {
                    !out.contains(q) && self.row(*q).of().and_then(|e| self.idx(e)).is_some_and(|e| out.contains(&e))
                })
                .collect();
            if add.is_empty() {
                break;
            }
            out.extend(add);
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
    let (ek, el, mine, mine_ends) = cx.view(ri);
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
    // F1: every input to the count comes from the set: the leavings and the withdrawals read are the set's
    let all: Vec<&R> = past.iter().map(|&q| sub.g.row(q)).collect();
    let by: BTreeMap<&R::Id, &R> = all.iter().map(|q| (q.id(), *q)).collect();
    let rows: Vec<&R> = all.iter().copied().filter(|q| mine.contains(q.id())).collect();
    let roster = |s: Option<&R::Word>| s.is_some_and(|s| law.roster_seats.iter().any(|x| x == s.as_ref()));
    let left: BTreeSet<&R::Key> = rows
        .iter()
        .filter(|w| {
            let held = |a: &R| {
                by.contains_key(a.id())
                    && sub.g.idx(a.id()).zip(sub.g.idx(w.id())).is_some_and(|(ai, wi)| sub.g.in_past(ai, wi))
            };
            w.seat_kind() == SeatKind::Withdraw && stay_end(law, &by, **w, &held).as_ref() == Some(&obj)
        })
        .map(|w| w.signer())
        .chain(
            rows.iter()
                .filter(|u| {
                    u.seat_kind() == SeatKind::Unseat
                        && u.conf() == Some(Conf::Group)
                        && u.obj().as_ref() == Some(&obj)
                        && roster(u.scope())
                })
                .flat_map(|u| u.to().iter()),
        )
        .collect();
    let voters: BTreeSet<R::Key> = el.iter().filter(|k| !left.contains(k)).cloned().collect();
    // (2): a key whose two forked rows are both in the set is no ballot (the set alone decides: F1)
    let set_rows: Vec<usize> = past.iter().copied().filter(|&q| mine.contains(sub.g.row(q).id())).collect();
    let fork = cx.forkers(&ek, &set_rows, &past, &obj, &mine_ends);
    let voters: BTreeSet<R::Key> = voters.into_iter().filter(|k| !fork.contains(k)).collect();
    let gone: BTreeSet<&R::Id> = rows
        .iter()
        .filter(|w| w.seat_kind() == SeatKind::Withdraw)
        .filter_map(|w| {
            let t = w.target()?;
            let tr = by.get(t)?;
            (tr.seat_kind() == SeatKind::Ballot && tr.signer() == w.signer()).then_some(t)
        })
        .collect();
    let declined: BTreeSet<&R::Key> = rows
        .iter()
        .filter(|d| d.seat_kind() == SeatKind::Decline && mine.contains(d.id()) && el.contains(d.signer()))
        .map(|d| d.signer())
        .collect();
    // one ballot per person (ruled on CIRISConstitution#224): a ballot counts for the voter its key speaks for
    // ([`persons_of`] over the seating's past); the tally takes one ranking a voter, and a voter whose keys cast two
    // says nothing
    let who = |k: &R::Key| -> Option<R::Key> {
        if voters.contains(k) {
            return Some(k.clone());
        }
        persons_of(&all, law, spec, &BTreeSet::from([k.clone()]), &voters).pop_first()
    };
    let ballots: Vec<(R::Key, Vec<R::Key>)> = rows
        .iter()
        .filter(|b| {
            b.seat_kind() == SeatKind::Ballot
                && mine.contains(b.id())
                && !gone.contains(b.id())
                && b.ranking().iter().all(|k| voters.contains(k))
                && b.ranking().len() <= ELECTION_RANKS
        })
        .filter_map(|b| Some((who(b.signer())?, b.ranking().to_vec())))
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
    let (ek, _, set, _) = cx.view(si);
    let Some(ek) = ek else { return false };
    cx.closure(&ek, c.cs(), &obj).as_ref() == Some(&set)
}
