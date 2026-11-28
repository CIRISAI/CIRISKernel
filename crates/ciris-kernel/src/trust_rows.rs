//! The reader's trust walk from rows, and the issuer's standing (CC 4.4.3.34; CC 4.5.4; CC 2.7.5), with the
//! Constitution's rulings of 2026-11-27: `trust_rows.py`. The only public path from rows to whether a reader honours
//! a licence: no caller supplies edges.
//!
//! An acceptance edge is a row: a `delegates_to` row bearing [`BEARS`] (`trust:accepts:v1`), naming the authority it
//! accepts ([`TrustRow::accepts_dst`]), with `trust_classes` (absent: every class the charter declares) and
//! `trust_depth`. Its owner is its signer, or the authority it speaks for ([`TrustRow::on_behalf`]).
//!
//! - **(a) The authority set.** An edge is its owner's where its signatures (signer and cosigners) are the owner's
//!   authority set, read over the edge's own causal past: for a person (a key), the key itself or any live key of its
//!   roster (scope `key` over it); for a community record of any kind, CC 4.5.4's `authority_set(C)`, counted as a
//!   duty conferral is (the acts row `accept / trust_edge / community -> duty_confer`, which the fixtures' law
//!   carries until the Constitution's table has it): a strict majority of all its live duty holders, never fewer than
//!   two where there are two or more, or a lone holder alone. There is no members' fallback: a community with no duty
//!   holder is LOCKED (CC 4.5.4 (v)) and signs no edge.
//! - **Admission.** A `trust_classes` list that is present must be non-empty, sorted and name no class twice
//!   ([`crate::trust::Accepts::refusal`]); `trust_depth` absent reads as 0, 0 to 5 is admitted, any other is
//!   [`DEPTH_OUT_OF_RANGE`]. A refused edge is no edge.
//! - **(d) Ended.** An edge is ended by a concluded withdrawal of it whose signatures are its owner's authority set
//!   over the withdrawal's own past; for the reader's own edge that is the reader's removal, which revokes at once,
//!   for that reader.
//! - **The walk** ([`crate::trust::reaches`]): from the reader's own edges; onward only from an authority's own edges;
//!   the classes intersect hop by hop; a key expanded again only with more budget than before, so a cycle is visited
//!   once; nothing is cached; within the cap of five. It reaches what the model's breadth-first walk reaches.
//! - **(b) The issuer.** A licence is the authority's act where, over the licence's own causal past, its emitter's key
//!   IS the authority (a person is one voice across its keys: any live key of its roster), or holds a `license` seat
//!   over it (a delegation whose chain resolves to the authority: [`Seats::stands`]; over a community its duty holders
//!   confer and withdraw the seat, the acts rows `seat_confer` / `seat_withdraw` of scope `license`, which the
//!   fixtures' law carries until the table has them), or, for a community, the licence is cosigned by its quorum under
//!   its DECLARED `consensus_protocol` ([`crate::seat::declared_count`]; no bootstrap). Any other is testimony, out of
//!   the fold: [`NOT_AUTHORITY`]; a locked community's own licence is [`AUTHORITY_LOCKED`]. A licence naming a link
//!   that is not held is not kept: it waits.
//! - **(d) By ancestry.** The standing is judged at issuance, over the issuance's own past, never at receipt: a
//!   withdrawal of a link in that past stops it; one concurrent with the issuance holds it out of force for a reader
//!   that holds the withdrawal ([`LINK_WITHDRAWN`]); one with the issuance in its own past reaches nothing back.

use crate::charter::{charters, CHARTER_KINDS};
use crate::cut::CutSpec;
use crate::graph::Graph;
use crate::layers::{Concluded, Past};
use crate::seat::{
    affiliation_path_at, body_change, concurrent_growth, countersigned, declared_count, ended_seats, for_reader,
    kind_of, policy_for, recount_on_growth, scope_class, still_met, voices, Act, CommunityKind, Conf, Obj, ScopeClass,
    SeatKind, SeatLaw, SeatRow, Seats, OFFICER,
};
use crate::trust::{reaches, Accepts, Charters, HOP_CAP};
use crate::{Dated, Row};
use alloc::collections::{BTreeMap, BTreeSet};
use alloc::string::String;
use alloc::vec::Vec;

type ObjOf<R> = Obj<<R as Row>::Id, <R as Row>::Key>;

/// What an acceptance edge row bears.
pub const BEARS: &str = "trust:accepts:v1";
/// The admission's refusal of an edge whose `trust_depth` is outside 0 to 5.
pub const DEPTH_OUT_OF_RANGE: &str = "trust_accepts_depth_out_of_range";
/// A licence whose emitter has no standing for its authority over its own past: testimony, out of the fold.
pub const NOT_AUTHORITY: &str = "licensure_delegator_not_authority";
/// A locked community's own licence (CC 4.5.4 (v): no duty holder is left): it concludes nothing, with this reason.
pub const AUTHORITY_LOCKED: &str = "licensure_authority_locked";
/// A licence a withdrawal concurrent with it, held by the reader, holds out of force.
pub const LINK_WITHDRAWN: &str = "licensure_link_withdrawn";

/// The fields of an acceptance edge row and of a licence row. Every accessor has a default for a row that does not
/// carry the field.
pub trait TrustRow: SeatRow {
    /// The row is a `delegates_to` row.
    fn is_delegates_to(&self) -> bool {
        false
    }
    /// What a `delegates_to` row bears ([`BEARS`] for an acceptance edge).
    fn bears(&self) -> Option<&Self::Word> {
        None
    }
    /// The authority an acceptance edge accepts.
    fn accepts_dst(&self) -> Option<ObjOf<Self>> {
        None
    }
    /// The authority an edge speaks for, where it is not its signer's own.
    fn on_behalf(&self) -> Option<ObjOf<Self>> {
        None
    }
    /// An edge's `trust_classes`: `None` where absent.
    fn trust_classes(&self) -> Option<&[Self::Word]> {
        None
    }
    /// An edge's `trust_depth`, as stated; `None` where absent (read as 0).
    fn trust_depth(&self) -> Option<i64> {
        None
    }
    /// A licence: the authority it is issued under.
    fn licence_authority(&self) -> Option<ObjOf<Self>> {
        None
    }
    /// A licence: its class.
    fn licence_class(&self) -> Option<&Self::Word> {
        None
    }
}

/// `o` is a held, concluded community record (a community, an infrastructure community, an affiliation).
fn is_community<R: SeatRow, S: CutSpec<R>>(seats: &Seats<'_, '_, R, S>, o: &ObjOf<R>) -> bool {
    let Obj::Row(id) = o else { return false };
    let c = seats.c();
    let g = &c.g;
    let get = |i: &R::Id| g.idx(i).map(|x| g.row(x));
    c.concluded_id(id) && kind_of(seats.law(), &get, o).is_some_and(|k| CHARTER_KINDS.contains(&k))
}

/// A strict majority of `n`, never fewer than two where `n` is two or more; a lone holder alone (CC 4.5.4 (iv)).
fn counted(yes: usize, n: usize) -> bool {
    match n {
        0 => false,
        1 => yes == 1,
        _ => yes >= 2 && 2 * yes > n,
    }
}

/// CC 4.5.4 (v): community `c` has no live duty holder over the rows `seats` was built on, and is LOCKED: it signs no
/// NEW onward acceptance edge, confers no new license seat (the duty holders' count takes none) and issues no licence of
/// its own, until an election seats a holder. A license seat's holder is no duty holder and keeps no room from
/// locking. A license seat, or an edge, from before the lock stands until its term ends or it is withdrawn, by
/// ancestry ([`ended_for_reader`]). An affiliation is never locked: with no officer (its authority body,
/// [`Seats::authority_body`]) it is dissolved.
fn locked<R: SeatRow, S: CutSpec<R>>(seats: &Seats<'_, '_, R, S>, c: &ObjOf<R>) -> bool {
    // an affiliation's authority is its officers: with none it is dissolved (CC 4.4.3.12), and signs nothing either
    seats.authority_body(c).is_empty()
}

/// The licence's emitter `k` IS authority `a`: a person is one voice across its keys, so any live key of its roster
/// (scope `key` over it, read by `seats` over the licence's own past) is the person.
fn is_the_authority<R: SeatRow, S: CutSpec<R>>(seats: &Seats<'_, '_, R, S>, k: &R::Key, a: &ObjOf<R>) -> bool {
    match a {
        Obj::Key(x) => x == k || seats.holders("key", a, None).contains(k),
        Obj::Row(_) => false,
    }
}

/// Whether the keys `who` are `src`'s authority set over the rows `seats` was built on (a row's own past).
fn speaks_for<R: SeatRow, S: CutSpec<R>>(
    seats: &Seats<'_, '_, R, S>,
    past: &Past<'_, '_, R>,
    who: &BTreeSet<&R::Key>,
    src: &ObjOf<R>,
) -> bool {
    match src {
        Obj::Row(_) => {
            if !is_community(seats, src) {
                return false;
            }
            // an affiliation's edge is its officers' act under its declared protocol (the officers ruling: the acts
            // row `accept / trust_edge / affiliation -> cosigned_act`, which the fixtures' law carries)
            let g = &seats.c().g;
            let get = |i: &R::Id| g.idx(i).map(|x| g.row(x));
            if kind_of(seats.law(), &get, src) == Some(CommunityKind::Affiliation) {
                let bound = policy_for(seats.law(), Act::Accept, ScopeClass::TrustEdge, CommunityKind::Affiliation)
                    .is_some_and(|(p, _)| p.iter().any(|x| x == "cosigned_act"));
                let voices: BTreeSet<R::Key> = who.iter().map(|k| (*k).clone()).collect();
                return bound
                    && declared_count(past, seats.law(), seats.spec(), src, &seats.protocol_body(src), &voices);
            }
            // the acts row binds the count
            let bound = policy_for(seats.law(), Act::Accept, ScopeClass::TrustEdge, CommunityKind::Community)
                .is_some_and(|(p, _)| p.len() == 1 && p[0] == "duty_confer");
            if !bound {
                return false;
            }
            // no members' fallback: a community with no duty holder is locked, and signs no edge
            if locked(seats, src) {
                return false;
            }
            let duty = seats.authority_body(src);
            counted(duty.iter().filter(|k| who.contains(k)).count(), duty.len())
        }
        // a person: the key itself, or a live key of its roster
        Obj::Key(k) => who.contains(k) || seats.holders("key", src, None).iter().any(|x| who.contains(x)),
    }
}

/// The group or key a row acts over: its object, the authority it speaks for, or a licence's authority; an
/// acceptance's, its offer's object.
fn object_of<R: TrustRow>(c: &Concluded<'_, R>, q: &R) -> Option<ObjOf<R>> {
    if q.seat_kind() == SeatKind::Accept {
        if let Some(o) = q.of().and_then(|i| c.g.idx(i)) {
            return c.g.row(o).obj();
        }
    }
    q.obj().or_else(|| q.on_behalf()).or_else(|| q.licence_authority())
}

/// An end the reader reads over its own rows: a withdrawal (a lay-down, a resignation, a conferrer's withdrawal, an
/// edge's withdrawal), an unseat (a counted removal or withdrawal of a seat, a key's eviction from a roster), or a
/// change of a group's record (an amendment of its protocol or of what it declares).
fn is_end<R: SeatRow>(q: &R) -> bool {
    match q.seat_kind() {
        SeatKind::Withdraw | SeatKind::Unseat => true,
        SeatKind::Offer => q.conf() == Some(Conf::Group) && q.scope().is_some_and(|s| s.as_ref() == "record"),
        _ => false,
    }
}

fn founding_row<R: SeatRow>(t: &R) -> bool {
    t.seat_kind() == SeatKind::Offer && t.obj().is_some_and(|o| o == Obj::Row(t.id().clone()))
}

/// One seat an end ends: its key, its object, its scope.
type Ended<R> = (<R as Row>::Key, ObjOf<R>, Option<String>);

/// The (key, object, scope) seats end `e` ends, read as the seat model reads ends ([`crate::seat::ended_seats`], the
/// one read: an unseat's keys in its scope, a withdrawal's seat), and only where the end is in force for the reader: a
/// removal the reader's seats hold out of force or contested ([`Seats::dropped`]: a lone removal lifted, rule 5) ends
/// nothing. A change of the record ends no seat.
fn ends_keys<R: TrustRow, S: CutSpec<R>>(seats: &Seats<'_, '_, R, S>, e: &R) -> Vec<Ended<R>> {
    if e.seat_kind() == SeatKind::Unseat && seats.dropped().contains(e.id()) {
        return Vec::new();
    }
    let c = seats.c();
    let by: BTreeMap<&R::Id, &R> = c.g.rows().iter().map(|q| (q.id(), *q)).collect();
    ended_seats(&by, e).into_iter().filter_map(|(k, sc, o)| o.map(|o| (k, o, sc))).collect()
}

/// The standings act `q` over `o` rests on (the classes [`scope_class`] gives): a counted row's body (`counted`); a
/// row conferred under a seat, that seat's; a single key's own offer over a group, its authority body's; an edge
/// speaking for a group, its authority body's, and for a person, the roster's `key`; a licence, its seat's or its
/// quorum's.
fn rests_on<R: TrustRow>(c: &Concluded<'_, R>, law: &SeatLaw, q: &R, o: &ObjOf<R>) -> Vec<String> {
    let get = |i: &R::Id| c.g.idx(i).map(|x| c.g.row(x));
    let body = if kind_of(law, &get, o) == Some(CommunityKind::Affiliation) { OFFICER } else { "duty" };
    let group = matches!(o, Obj::Row(i) if c.g.idx(i).is_some_and(|x| founding_row(c.g.row(x))));
    match q.seat_kind() {
        SeatKind::Offer | SeatKind::Unseat => match q.conf() {
            Some(Conf::Group) => {
                scope_class(c, law, o, Some(q.counted().map_or("member", |w| w.as_ref()))).into_iter().collect()
            }
            Some(Conf::Seat) => {
                let up = q.under().and_then(|u| c.g.idx(u)).map(|x| c.g.row(x));
                up.and_then(|u| scope_class(c, law, o, u.scope().map(|w| w.as_ref()))).into_iter().collect()
            }
            Some(Conf::Own) if !founding_row(q) && group => alloc::vec![String::from(body)],
            _ => Vec::new(),
        },
        _ if q.is_delegates_to() => alloc::vec![String::from(if group { body } else { "key" })],
        _ if q.licence_authority().is_some() => {
            alloc::vec![String::from("license"), String::from("member"), String::from(OFFICER)]
        }
        _ => Vec::new(),
    }
}

/// Key `k` holds standing `cls` over `o` over the rows `idx` (their conclusions as `seats`' set has them).
fn holds_over<R: TrustRow, S: CutSpec<R>>(
    seats: &Seats<'_, '_, R, S>,
    idx: &[usize],
    k: &R::Key,
    o: &ObjOf<R>,
    cls: &str,
) -> bool {
    let sub = sub_of(seats.c(), idx);
    let (rc, _) = for_reader(&sub, seats.law(), seats.spec(), None);
    Seats::new(&rc, seats.law(), seats.spec(), None).holders(cls, o, None).contains(k)
}

/// Key `k` LOSES standing `cls` over `o` by its ends: it holds it over the JUDGED rows (the judged row's past, the
/// ends the reader holds and their pasts) with EVERY end of `k`'s seats over `o` taken out, and every row that has one
/// of those ends in its past (so a second end of the same seat cannot cancel the first's cut, and a later re-seat does
/// not mask it), and no more with the ends read in (and still without the rows after them). A partial end (one duty
/// laid down, another held, a seat gained beside it) loses nothing; a full end (a resignation, the withdrawal of an
/// appointment) loses every standing the seat it ends gave, whatever scope the end's target names.
fn loses<R: TrustRow, S: CutSpec<R>>(
    seats: &Seats<'_, '_, R, S>,
    judged: &[usize],
    k: &R::Key,
    o: &ObjOf<R>,
    cls: &str,
) -> bool {
    let c = seats.c();
    let mine: Vec<usize> = judged
        .iter()
        .copied()
        .filter(|&x| {
            c.concluded(x)
                && is_end(c.g.row(x))
                && ends_keys(seats, c.g.row(x)).iter().any(|(kk, ob, _)| kk == k && ob == o)
        })
        .collect();
    let after = |x: usize| mine.iter().any(|&m| c.g.ancestors(x).has(m));
    let without: Vec<usize> = judged.iter().copied().filter(|&x| !mine.contains(&x) && !after(x)).collect();
    let with: Vec<usize> = judged.iter().copied().filter(|&x| !after(x)).collect();
    holds_over(seats, &without, k, o, cls) && !holds_over(seats, &with, k, o, cls)
}

// ---- the reader's line over a group's body (the r77 attack: body growth is a counted change, not an end) ----------

/// The object a row is over, as the reader's line reads it (`checkpoint.object_of`): its `obj`, its `room`, or the
/// object of the row its `of` or `target` names.
fn line_object<R: SeatRow>(c: &Concluded<'_, R>, r: &R, n: usize) -> Option<ObjOf<R>> {
    if n > 8 {
        return None;
    }
    if let Some(o) = r.obj() {
        return Some(o);
    }
    if let Some(o) = r.room() {
        return Some(o);
    }
    let t = r.of().or(r.target()).and_then(|i| c.g.idx(i)).map(|i| c.g.row(i))?;
    line_object(c, t, n + 1)
}

/// The changes of `o`'s body reader `own` has taken up: each concluded change in the past of (or equal to) a row `own`
/// signed or cosigned over `o` (CC 2.7.8), or named as a head by its acknowledgement (an `Ack`).
fn line_of<R: SeatRow>(c: &Concluded<'_, R>, own: Option<&R::Key>, o: &ObjOf<R>) -> Vec<usize> {
    let Some(own) = own else { return Vec::new() };
    let acks: Vec<usize> = c
        .cs()
        .iter()
        .copied()
        .filter(|&a| {
            let r = c.g.row(a);
            (r.signer() == own || r.cosigners().contains(own)) && line_object(c, r, 0).as_ref() == Some(o)
        })
        .collect();
    c.cs()
        .iter()
        .copied()
        .filter(|&x| {
            body_change(c.g.row(x), o)
                && acks.iter().any(|&a| {
                    let ar = c.g.row(a);
                    let named: &[R::Id] = if ar.seat_kind() == SeatKind::Ack { ar.head() } else { &[] };
                    x == a
                        || c.g.ancestors(a).has(x)
                        || named.iter().filter_map(|h| c.g.idx(h)).any(|h| h == x || c.g.ancestors(h).has(x))
                })
        })
        .collect()
}

/// Authority act `q` (index) over `o` is BEHIND reader `own`'s line: the heads it names (its named changes of `o`'s
/// body and `o` itself, or every row it names where it names none) are all strictly in the past of a change the
/// reader has taken up, which `q` does not have in its own past. It concludes nothing for that reader (the
/// checkpoint's monotone line, as rosters read it). A reader with no row of its own is the newcomer residual.
fn behind_line<R: SeatRow>(c: &Concluded<'_, R>, own: Option<&R::Key>, q: usize, o: &ObjOf<R>) -> bool {
    let line = line_of(c, own, o);
    if line.is_empty() {
        return false;
    }
    let r = c.g.row(q);
    let named: Vec<usize> = r.names().iter().filter_map(|n| c.g.idx(n)).collect();
    let mut heads: Vec<usize> = named
        .iter()
        .copied()
        .filter(|&n| Obj::Row(c.g.row(n).id().clone()) == *o || body_change(c.g.row(n), o))
        .collect();
    if heads.is_empty() {
        heads = named;
    }
    !heads.is_empty()
        && line.iter().any(|&x| {
            x != q
                && !c.g.ancestors(x).has(q)
                && !c.g.ancestors(q).has(x)
                && heads.iter().all(|&h| c.g.ancestors(x).has(h))
        })
}

/// The group an authority act `q` acts for, or `None`: a change of a group's body ([`body_change`]), an edge speaking
/// for a group, or a licence of a group.
fn authority_act_over<R: TrustRow>(c: &Concluded<'_, R>, q: &R) -> Option<ObjOf<R>> {
    let held = |o: &ObjOf<R>| matches!(o, Obj::Row(i) if c.g.idx(i).is_some());
    if let Some(o) = q.obj().filter(|o| held(o) && body_change(q, o)) {
        return Some(o);
    }
    if q.is_delegates_to() {
        return q.on_behalf().filter(held);
    }
    q.licence_authority().filter(held)
}

/// The concluded set of the rows `idx` of `c` (index order kept), their conclusions copied.
fn sub_of<'a, R: Row>(c: &Concluded<'a, R>, idx: &[usize]) -> Concluded<'a, R> {
    let g = Graph::new(idx.iter().map(|&j| c.g.row(j)));
    Concluded::with(g, Some(idx.iter().map(|&j| c.concluded(j)).collect()))
}

// ---- body growth over the rows the reader HOLDS: the seat model's one reading ([`crate::seat::recount_on_growth`],
// the DRY item "re-count on growth"), read here as the seat walk reads it ---------------------------------------------

/// Authority act `q` over `o`, CONCURRENT with growth of the body the reader holds, still holds counted over the grown
/// body: [`crate::seat::recount_on_growth`], the one re-count (a lone conferral by the one gate, a counted conferral
/// by its count at the newest counted changes), with an edge read by its owner's authority set over the grown rows.
fn recounted<R: TrustRow, S: CutSpec<R>>(seats: &Seats<'_, '_, R, S>, q: usize, o: &ObjOf<R>) -> bool {
    let c = seats.c();
    let r = c.g.row(q);
    let edge = |idx: &[usize]| !r.is_delegates_to() || speaks_over(seats, q, idx, &owner(r));
    recount_on_growth(c, seats.law(), seats.spec(), q, o, &BTreeSet::new(), Some(&edge))
}

/// A counted row: an offer or unseat a group's count concludes (`Conf::Group`), naming its heads.
fn is_counted_row<R: SeatRow>(q: &R) -> bool {
    matches!(q.seat_kind(), SeatKind::Offer | SeatKind::Unseat) && q.conf() == Some(Conf::Group) && !q.head().is_empty()
}

/// Counted row `q` still meets its count over its own past with the voices of `gone` taken out:
/// [`crate::seat::still_met`], the seat model's one re-count (its voices path, the persons counted), as its contest
/// reads a discounted voice.
fn recount_without<R: TrustRow, S: CutSpec<R>>(seats: &Seats<'_, '_, R, S>, q: usize, gone: &BTreeSet<R::Key>) -> bool {
    let c = seats.c();
    let anc = c.g.ancestors(q);
    let p: Vec<usize> = c.cs().iter().copied().filter(|&j| anc.has(j)).collect();
    still_met(&Past::new(&c.g, q, &p), seats.law(), seats.spec(), gone)
}

/// THE END RULE (the r73 attack), the one read of ends for every path (the emitter, the quorum, the seat, the edge):
/// an END cuts every row of what it ends that is not in the end's past. The rows (indices of `seats`' set) row `i`'s
/// authority is judged over: its own past, with every end in it cutting the rows concurrent with it (`read` false: its
/// existence at issuance); with `read`, every end the READER holds concurrent with `i` too (a key's eviction, an
/// unseat, a lay-down and so the lock, an edge's withdrawal, an amendment of the record), each cutting what it ends
/// there: a row signed by a key whose seat over the row's object, of a scope whose standing the row rests on, the end
/// ends (and the key holds that standing no more), concurrent with it. Authority acts behind reader `own`'s line are cut
/// too ([`behind_line`]). Dissolution is read the same way ([`read_licence`]).
fn ended_for_reader<R: TrustRow, S: CutSpec<R>>(
    seats: &Seats<'_, '_, R, S>,
    i: usize,
    read: bool,
    own: Option<&R::Key>,
) -> Vec<usize> {
    ended_for_reader_with(seats, i, read, true, own)
}

/// A change of a group's record: it cuts nothing, and changes the rule a row is judged under.
fn is_amendment<R: SeatRow>(q: &R) -> bool {
    q.seat_kind() == SeatKind::Offer
        && q.conf() == Some(Conf::Group)
        && q.scope().is_some_and(|s| s.as_ref() == "record")
}

/// [`ended_for_reader`], with the reader's concurrent amendments of the record read in (`amend`) or left out.
fn ended_for_reader_with<R: TrustRow, S: CutSpec<R>>(
    seats: &Seats<'_, '_, R, S>,
    i: usize,
    read: bool,
    amend: bool,
    own: Option<&R::Key>,
) -> Vec<usize> {
    let c = seats.c();
    let anc = c.g.ancestors(i);
    let mut rows: Vec<usize> = (0..c.g.len()).filter(|&j| anc.has(j)).collect();
    if read {
        rows.extend(c.cs().iter().copied().filter(|&j| {
            j != i
                && !anc.has(j)
                && is_end(c.g.row(j))
                && !c.g.ancestors(j).has(i)
                && (amend || !is_amendment(c.g.row(j)))
        }));
    }
    // the growth of the authority's body the reader holds, concurrent with i: i is counted over the grown body
    // (`amend` false leaves it out, as an amendment: it changes the rule, it cuts nothing)
    if read && amend {
        if let Some(o) = authority_act_over(c, c.g.row(i)) {
            for x in concurrent_growth(c, seats.law(), i, &o, &BTreeSet::new()) {
                rows.extend((0..c.g.len()).filter(|&j| j != i && (j == x || c.g.ancestors(x).has(j))));
            }
        }
    }
    rows.sort_unstable();
    rows.dedup();
    let mut cut: BTreeSet<usize> = BTreeSet::new();
    let mut lost: BTreeMap<usize, BTreeSet<R::Key>> = BTreeMap::new();
    let ends: Vec<usize> = rows.iter().copied().filter(|&e| c.concluded(e) && is_end(c.g.row(e))).collect();
    let judged: Vec<usize> = (0..c.g.len())
        .filter(|&j| rows.binary_search(&j).is_ok() || ends.iter().any(|&e| c.g.ancestors(e).has(j)))
        .collect();
    for &e in &ends {
        let ks = ends_keys(seats, c.g.row(e));
        if ks.is_empty() {
            continue;
        }
        let ea = c.g.ancestors(e);
        for &q in &rows {
            if q == e || ea.has(q) || c.g.ancestors(q).has(e) {
                continue;
            }
            let qr = c.g.row(q);
            let Some(o) = object_of(c, qr) else { continue };
            let qa = c.g.ancestors(q);
            let qp: Vec<usize> = c.cs().iter().copied().filter(|&j| qa.has(j)).collect();
            let who = voices(qr, &Past::new(&c.g, q, &qp));
            let need = rests_on(c, seats.law(), qr, &o);
            // an end is keyed by every standing its key LOSES by it, whatever scope its target names
            for (k, ob, _) in &ks {
                if *ob == o && who.contains(k) && need.iter().any(|cls| loses(seats, &judged, k, ob, cls)) {
                    lost.entry(q).or_default().insert(k.clone());
                }
            }
        }
    }
    // a COUNTED row loses only the ended keys' voices: it is re-counted over the voices left, and cut only where the
    // count then fails (as contested_out drops voices); a single key's own row is cut
    for (q, gone) in &lost {
        if !is_counted_row(c.g.row(*q)) || !recount_without(seats, *q, gone) {
            cut.insert(*q);
        }
    }
    for &q in &rows {
        let qr = c.g.row(q);
        if let Some(o) = authority_act_over(c, qr) {
            if behind_line(c, own, q, &o) || (qr.licence_authority().is_none() && !recounted(seats, q, &o)) {
                cut.insert(q);
            }
        }
    }
    // what rests on a void row is the seat model's to void (a counted act counts only if every counted act among its
    // heads counts; a lone conferral regrown against the body seats nothing, and every row built on it with it). The
    // seat model over the rows judged is THE answer, so the cut keeps no row it voids: a row the lane cuts leaves what
    // rests on it to be read over rows without it, where the seat model could no longer see it rests on a void row
    // (E6: an election's growth voids A's lone conferral of B, A's concurrent lay-down cuts it, and B and C's
    // conferral built on it was then counted as C's alone)
    let void = voided_over(seats, &rows);
    rows.retain(|j| !cut.contains(j) && !void.contains(j));
    rows
}

/// The rows among `idx` (indices of `seats`' set) that the seat model over those rows alone voids ([`Seats::stale`]):
/// counted acts built on one that does not count, and regrown lone conferrals with every row built on them.
fn voided_over<R: TrustRow, S: CutSpec<R>>(seats: &Seats<'_, '_, R, S>, idx: &[usize]) -> BTreeSet<usize> {
    let sub = sub_of(seats.c(), idx);
    let (rc, _) = for_reader(&sub, seats.law(), seats.spec(), None);
    let q = Seats::new(&rc, seats.law(), seats.spec(), None);
    q.stale().iter().filter_map(|&j| idx.get(j).copied()).collect()
}

/// The rows `idx` of `c`, as their concluded set and with row `i` (not among them) beside them: the Seats are built
/// over the first, and a [`Past`] of `i` over the second reads the same rows (the record in force there).
fn judged<'a, R: TrustRow>(c: &Concluded<'a, R>, i: usize, idx: &[usize]) -> (Concluded<'a, R>, Concluded<'a, R>) {
    let mut with: Vec<usize> = idx.to_vec();
    with.push(i);
    (sub_of(c, idx), sub_of(c, &with))
}

/// Whether the keys `who` are `src`'s authority set over the rows `idx` of `seats`' set, for row `i` (a row's own
/// past, or with the ends the reader holds: [`ended_for_reader`]).
fn speaks_over<R: TrustRow, S: CutSpec<R>>(
    seats: &Seats<'_, '_, R, S>,
    i: usize,
    idx: &[usize],
    src: &ObjOf<R>,
) -> bool {
    let c = seats.c();
    let (sub, with) = judged(c, i, idx);
    let (rc, _) = for_reader(&sub, seats.law(), seats.spec(), None);
    let last = with.g.len() - 1;
    let p: Vec<usize> = with.cs().iter().copied().filter(|&j| j != last).collect();
    let past = Past::new(&with.g, last, &p);
    // the row's voices, read as the seat model reads them ([`voices`]: its signatures and the cosign rows it names)
    let v = voices(c.g.row(i), &past);
    let who: BTreeSet<&R::Key> = v.iter().collect();
    speaks_for(&Seats::new(&rc, seats.law(), seats.spec(), None), &past, &who, src)
}

/// Whether the keys `who` are `src`'s authority set for row `i`: over its own past, and with every end the reader
/// holds ([`ended_for_reader`]).
fn speaks_at<R: TrustRow, S: CutSpec<R>>(
    seats: &Seats<'_, '_, R, S>,
    i: usize,
    src: &ObjOf<R>,
    own: Option<&R::Key>,
) -> bool {
    [false, true].iter().all(|&read| speaks_over(seats, i, &ended_for_reader(seats, i, read, own), src))
}

fn owner<R: TrustRow>(r: &R) -> ObjOf<R> {
    r.on_behalf().unwrap_or_else(|| Obj::Key(r.signer().clone()))
}

/// An acceptance edge row as admitted: not an edge (`None`), refused at admission (with the reason), or the edge.
fn edge_of<R: TrustRow>(r: &R) -> Option<Result<Accepts<ObjOf<R>, R::Word>, &'static str>> {
    if !r.is_delegates_to() || r.bears().is_none_or(|b| b.as_ref() != BEARS) {
        return None;
    }
    let dst = r.accepts_dst()?;
    let e = Accepts { src: owner(r), dst, classes: r.trust_classes().map(|c| c.to_vec()), depth: 0 };
    if let Some(why) = e.refusal() {
        return Some(Err(why));
    }
    match r.trust_depth().unwrap_or(0) {
        d @ 0..=5 => Some(Ok(Accepts { depth: d as u32, ..e })),
        _ => Some(Err(DEPTH_OUT_OF_RANGE)),
    }
}

/// The admission's refusal of acceptance edge row `r`, or `None` (an edge, or no `delegates_to` bearing [`BEARS`]).
pub fn refusal<R: TrustRow>(r: &R) -> Option<&'static str> {
    edge_of(r).and_then(|e| e.err())
}

/// An edge's own term (`asserted_at <= now < valid_until`) covers the CALLER's instant `now`: every edge carries a
/// term (CC 4.4.3.12), so an edge stating none is not walked, and with no `now` no term is read and no edge is walked
/// (never at the licence's own stated instant: that would let the issuer's word reach the reader's own edge). The
/// caller passes `now`.
fn edge_term<R: Dated>(r: &R, now: Option<&R::Instant>) -> bool {
    match (r.valid_until(), now) {
        (None, _) | (Some(_), None) => false,
        (Some(_), Some(t)) => crate::covers_at(r.asserted_at(), r.valid_until(), t),
    }
}

/// The acceptance edges the concluded rows give at the caller's instant `now`, for reader `own`: each admitted edge
/// its owner's authority set signed (over its own past and with every end the reader holds), not behind the reader's
/// line over its owner's body, within its term, no withdrawal by that set ended; its `src` is its owner.
pub fn edges_of<R: TrustRow + Dated, S: CutSpec<R>>(
    seats: &Seats<'_, '_, R, S>,
    now: Option<&R::Instant>,
    own: Option<&R::Key>,
) -> Vec<Accepts<ObjOf<R>, R::Word>> {
    let c = seats.c();
    let mut out = Vec::new();
    for &i in c.cs() {
        let r = c.g.row(i);
        let Some(Ok(e)) = edge_of(r) else { continue };
        // a dissolved authority's own edges end with its record (CC 4.4.3.12): no walk hops through it
        if matches!(e.src, Obj::Row(_)) && seats.dissolved(&e.src) {
            continue;
        }
        if !edge_term(r, now) {
            continue;
        }
        // an edge speaking for a group, behind the reader's line over its body, concludes nothing for that reader
        if matches!(e.src, Obj::Row(_)) && behind_line(c, own, i, &e.src) {
            continue;
        }
        if !speaks_at(seats, i, &e.src, own) {
            continue;
        }
        // a one-officer affiliation's edge is a proposal: it stands only where countersigned (the item-8 ruling)
        if !countersigned(seats, i) {
            continue;
        }
        // the path an edge states, where it states one (seat::affiliation_path_at: by person, over its own past)
        if !affiliation_path_at(seats, i) {
            continue;
        }
        let ended = c.cs().iter().any(|&j| {
            let w = c.g.row(j);
            w.seat_kind() == SeatKind::Withdraw && w.target() == Some(r.id()) && speaks_at(seats, j, &e.src, own)
        });
        if !ended {
            out.push(e);
        }
    }
    out
}

/// A licence stating an instant earlier than a row it cites: a row cannot claim to predate what it names.
pub const INSTANT_BEFORE_PAST: &str = "licensure_instant_before_its_past";

/// Licence row `i`'s standing over the rows `idx` of `seats`' set: `None`, [`NOT_AUTHORITY`] (no standing:
/// testimony), [`AUTHORITY_LOCKED`] (a locked community's quorum) or [`INSTANT_BEFORE_PAST`].
fn issuance<R: TrustRow + Dated, S: CutSpec<R>>(
    seats: &Seats<'_, '_, R, S>,
    i: usize,
    idx: &[usize],
) -> Option<&'static str> {
    let c = seats.c();
    let r = c.g.row(i);
    let Some(a) = r.licence_authority() else { return Some(NOT_AUTHORITY) };
    let t = r.asserted_at();
    let (law, spec) = (seats.law(), seats.spec());
    let (sub, with) = judged(c, i, idx);
    let (rc, _) = for_reader(&sub, law, spec, None);
    let at = Seats::new(&rc, law, spec, None);
    if is_the_authority(&at, r.signer(), &a) {
        return None;
    }
    if is_community(&at, &a) {
        // (1) the community's own licence: its quorum under its DECLARED protocol, in force over these rows; (2) a
        // locked community issues none of its own (a license seat conferred before the lock is read below)
        let last = with.g.len() - 1;
        let p: Vec<usize> = with.cs().iter().copied().filter(|&j| j != last).collect();
        let past = Past::new(&with.g, last, &p);
        let v = voices(r, &past);
        if declared_count(&past, at.law(), at.spec(), &a, &at.protocol_body(&a), &v) {
            if !locked(&at, &a) {
                return None;
            }
            if !at.stands(r.signer(), "license", &a, None) {
                return Some(AUTHORITY_LOCKED);
            }
        }
    }
    // a license seat, within its term at the licence's instant: no instant meets no term ([`Seats::stands_within`])
    if !at.stands(r.signer(), "license", &a, None) || !at.stands_within(r.signer(), "license", &a, None, t.as_ref()) {
        return Some(NOT_AUTHORITY);
    }
    None
}

/// Licence row `i` is its authority's OWN licence over the rows `idx`: a community's, met by its quorum under its
/// declared protocol, its emitter not the authority's own key.
fn own_licence<R: TrustRow + Dated, S: CutSpec<R>>(seats: &Seats<'_, '_, R, S>, i: usize, idx: &[usize]) -> bool {
    let c = seats.c();
    let r = c.g.row(i);
    let Some(a) = r.licence_authority() else { return false };
    let (sub, with) = judged(c, i, idx);
    let (rc, _) = for_reader(&sub, seats.law(), seats.spec(), None);
    let at = Seats::new(&rc, seats.law(), seats.spec(), None);
    if !is_community(&at, &a) || is_the_authority(&at, r.signer(), &a) {
        return false;
    }
    let last = with.g.len() - 1;
    let p: Vec<usize> = with.cs().iter().copied().filter(|&j| j != last).collect();
    let past = Past::new(&with.g, last, &p);
    let v = voices(r, &past);
    declared_count(&past, at.law(), at.spec(), &a, &at.protocol_body(&a), &v)
}

/// Whether licence row `i` is its authority's act in force for the reader holding the rows `seats` was built on:
/// `None`, or the reason it CONCLUDES NOTHING in the authority's fold (never a refusal: the licence row is admitted,
/// and the reason reads other rows, CC 2.7.3). Its existence is judged over its own past (`ended_for_reader`,
/// `read` false): [`NOT_AUTHORITY`] (testimony), [`AUTHORITY_LOCKED`] (a locked community's quorum) or
/// [`INSTANT_BEFORE_PAST`]. Then every end the reader holds is read over the reader's rows: a licence that stood and is
/// cut so is [`LINK_WITHDRAWN`], or [`AUTHORITY_LOCKED`] where the end locks its community; one that fails only under
/// an amendment of the record the reader holds is judged under it: [`NOT_AUTHORITY`].
pub fn standing<R: TrustRow + Dated, S: CutSpec<R>>(
    seats: &Seats<'_, '_, R, S>,
    i: usize,
    own: Option<&R::Key>,
) -> Option<&'static str> {
    let c = seats.c();
    let r = c.g.row(i);
    // the instant's lower bound is the licence's OWN past alone: the reader's ends cut, they never set it
    if let Some(t) = r.asserted_at() {
        let anc = c.g.ancestors(i);
        if (0..c.g.len()).any(|j| anc.has(j) && c.g.row(j).asserted_at().is_some_and(|u| u > t)) {
            return Some(INSTANT_BEFORE_PAST);
        }
    }
    // an authority act behind the reader's line over the authority's body concludes nothing for that reader
    if let Some(a) = r.licence_authority().filter(|a| matches!(a, Obj::Row(_))) {
        if behind_line(c, own, i, &a) {
            return Some(NOT_AUTHORITY);
        }
    }
    if let Some(why) = issuance(seats, i, &ended_for_reader(seats, i, false, own)) {
        return Some(why);
    }
    match issuance(seats, i, &ended_for_reader(seats, i, true, own)) {
        // the body's OWN licence (its quorum's, not a seat holder's or the authority's key's) is a counted act of the
        // body: while it has one officer it needs the countersign, read by seat::countersigned over the reader's rows
        None if own_licence(seats, i, &ended_for_reader(seats, i, false, own)) && !countersigned(seats, i) => {
            Some(NOT_AUTHORITY)
        }
        None => None,
        Some(AUTHORITY_LOCKED) => Some(AUTHORITY_LOCKED),
        // an amendment cuts nothing: it changes the rule the licence is judged under, so a licence that fails under
        // the amended record (and stands with every other end the reader holds) is judged so: testimony
        Some(_) if issuance(seats, i, &ended_for_reader_with(seats, i, true, false, own)).is_none() => {
            Some(NOT_AUTHORITY)
        }
        Some(_) => Some(LINK_WITHDRAWN),
    }
}

/// Why a reader does not honour a licence.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Unhonoured {
    /// The licence row is not held.
    NotHeld,
    /// The authority's record does not declare the class (`licence_class_not_trusted`).
    ClassNotTrusted,
    /// The licence is not its authority's act in force ([`NOT_AUTHORITY`], [`LINK_WITHDRAWN`]).
    Standing(&'static str),
    /// The reader's walk does not reach the authority for the class (`authority_not_reached`).
    NotReached,
    /// Its authority is dissolved: a licence that stood at issuance (its standing and its class over its own past)
    /// stands and reads `lapsed` for every later use.
    Lapsed,
}

impl Unhonoured {
    /// The reason's word (`trust_rows.py`'s).
    pub fn word(self) -> &'static str {
        match self {
            Unhonoured::NotHeld => "not_held",
            Unhonoured::ClassNotTrusted => "licence_class_not_trusted",
            Unhonoured::Standing(w) => w,
            Unhonoured::NotReached => "authority_not_reached",
            Unhonoured::Lapsed => "lapsed",
        }
    }
}

/// Whether `reader` honours licence row `licence`, read over the rows `seats` was built on (the reader's holding) at
/// the caller's instant `now`, with the acceptance edges those rows give and the charters `supplied` from elsewhere
/// (the trust root's scope): `Ok` where the authority's record declares the licence's class ([`charters`]), the
/// licence is the authority's act in force ([`standing`]), and the reader's walk reaches the authority for the
/// class. The licence row itself is admitted whatever this answers.
pub fn read_licence<R: TrustRow + Dated, S: CutSpec<R>>(
    seats: &Seats<'_, '_, R, S>,
    reader: &ObjOf<R>,
    licence: &R::Id,
    supplied: &Charters<ObjOf<R>, R::Word>,
    now: Option<&R::Instant>,
) -> Result<(), Unhonoured> {
    let c = seats.c();
    let i = c.g.idx(licence).ok_or(Unhonoured::NotHeld)?;
    let r = c.g.row(i);
    let (Some(auth), Some(cls)) = (r.licence_authority(), r.licence_class()) else {
        return Err(Unhonoured::ClassNotTrusted);
    };
    // the reader's line is the reader's own (the r77 attack)
    let own = match reader {
        Obj::Key(k) => Some(k),
        Obj::Row(_) => None,
    };
    // a dissolved authority (CC 4.4.3.12, "What stands after dissolution"): an issued licence stands, its authority
    // judged at issuance, and reads `lapsed` for every later use; one with no standing over its own past is testimony
    // (the issuance judgement first, over the licence's own past: its standing, then its class; only a licence that
    // stood then reads `lapsed`)
    if is_community(seats, &auth) && seats.dissolved(&auth) {
        if let Some(why) = standing(seats, i, own) {
            return Err(Unhonoured::Standing(why));
        }
        let anc = c.g.ancestors(i);
        let idx: Vec<usize> = (0..c.g.len()).filter(|&j| anc.has(j)).collect();
        let sub = sub_of(c, &idx);
        let (rc, _) = for_reader(&sub, seats.law(), seats.spec(), None);
        let at = Seats::new(&rc, seats.law(), seats.spec(), None);
        if !charters(&at, supplied, now).declares(&auth, cls) {
            return Err(Unhonoured::ClassNotTrusted);
        }
        return Err(Unhonoured::Lapsed);
    }
    if !charters(seats, supplied, now).declares(&auth, cls) {
        return Err(Unhonoured::ClassNotTrusted);
    }
    if let Some(why) = standing(seats, i, own) {
        return Err(Unhonoured::Standing(why));
    }
    if !reaches(&edges_of(seats, now, own), reader, cls, HOP_CAP, &auth) {
        return Err(Unhonoured::NotReached);
    }
    Ok(())
}
