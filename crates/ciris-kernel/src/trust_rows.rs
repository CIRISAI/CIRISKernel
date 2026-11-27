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
    declared_count, for_reader, kind_of, policy_for, Act, CommunityKind, Conf, Obj, ScopeClass, SeatKind, SeatRow,
    Seats,
};
use crate::trust::{reaches, Accepts, Charters, HOP_CAP};
use crate::{Dated, Row};
use alloc::collections::BTreeSet;
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

/// A row's signatures: its signer and its cosigners.
fn signers<R: SeatRow>(r: &R) -> BTreeSet<&R::Key> {
    core::iter::once(r.signer()).chain(r.cosigners()).collect()
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
/// NEW onward acceptance edge, confers no license seat (the duty holders' count takes none) and issues no licence of
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
                    .is_some_and(|(p, _)| p.len() == 1 && p[0] == "cosigned_act");
                let voices: BTreeSet<R::Key> = who.iter().map(|k| (*k).clone()).collect();
                return bound && declared_count(past, src, &seats.protocol_body(src), &voices);
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

/// The (key, object) seats end `e` ends: an unseat's keys over its object; a withdrawal by a seated key of its own
/// seat, or by the conferrer of an offer's seats (a counted offer's conferrer is its count, and its signer ends
/// nothing alone); a change of the record ends no seat.
fn ends_keys<R: TrustRow>(c: &Concluded<'_, R>, e: &R) -> Vec<(R::Key, ObjOf<R>)> {
    match e.seat_kind() {
        SeatKind::Unseat => {
            let Some(o) = e.obj() else { return Vec::new() };
            e.to().iter().map(|k| (k.clone(), o.clone())).collect()
        }
        SeatKind::Withdraw => {
            let Some(t) = e.target().and_then(|i| c.g.idx(i)).map(|i| c.g.row(i)) else { return Vec::new() };
            match t.seat_kind() {
                SeatKind::Accept => object_of(c, t).map(|o| alloc::vec![(e.signer().clone(), o)]).unwrap_or_default(),
                SeatKind::Offer => {
                    let Some(o) = t.obj() else { return Vec::new() };
                    if t.to().contains(e.signer()) {
                        alloc::vec![(e.signer().clone(), o)]
                    } else if signers(t).contains(e.signer()) && t.conf() != Some(Conf::Group) {
                        t.to().iter().map(|k| (k.clone(), o.clone())).collect()
                    } else {
                        Vec::new()
                    }
                }
                _ => Vec::new(),
            }
        }
        _ => Vec::new(),
    }
}

/// The concluded set of the rows `idx` of `c` (index order kept), their conclusions copied.
fn sub_of<'a, R: Row>(c: &Concluded<'a, R>, idx: &[usize]) -> Concluded<'a, R> {
    let g = Graph::new(idx.iter().map(|&j| c.g.row(j)));
    Concluded::with(g, Some(idx.iter().map(|&j| c.concluded(j)).collect()))
}

/// THE END RULE (the r73 attack), the one read of ends for every path (the emitter, the quorum, the seat, the edge):
/// an END cuts every row of what it ends that is not in the end's past. The rows (indices of `c`) row `i`'s authority
/// is judged over: its own past, with every end in it cutting the rows concurrent with it (`read` false: its
/// existence at issuance); with `read`, every end the READER holds concurrent with `i` too (a key's eviction, an
/// unseat, a lay-down and so the lock, an edge's withdrawal, an amendment of the record), each cutting what it ends
/// there. Dissolution is read the same way ([`read_licence`]).
fn ended_for_reader<R: TrustRow>(c: &Concluded<'_, R>, i: usize, read: bool) -> Vec<usize> {
    let anc = c.g.ancestors(i);
    let mut rows: Vec<usize> = (0..c.g.len()).filter(|&j| anc.has(j)).collect();
    if read {
        rows.extend(
            c.cs().iter().copied().filter(|&j| j != i && !anc.has(j) && is_end(c.g.row(j)) && !c.g.ancestors(j).has(i)),
        );
        rows.sort_unstable();
    }
    let mut cut: BTreeSet<usize> = BTreeSet::new();
    for &e in rows.iter().filter(|&&e| c.concluded(e) && is_end(c.g.row(e))) {
        let ks = ends_keys(c, c.g.row(e));
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
            let who = signers(qr);
            if ks.iter().any(|(k, ob)| *ob == o && who.contains(k)) {
                cut.insert(q);
            }
        }
    }
    rows.retain(|j| !cut.contains(j));
    rows
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
    who: &BTreeSet<&R::Key>,
    src: &ObjOf<R>,
) -> bool {
    let c = seats.c();
    let (sub, with) = judged(c, i, idx);
    let (rc, _) = for_reader(&sub, seats.law(), seats.spec(), None);
    let last = with.g.len() - 1;
    let p: Vec<usize> = with.cs().iter().copied().filter(|&j| j != last).collect();
    speaks_for(&Seats::new(&rc, seats.law(), seats.spec(), None), &Past::new(&with.g, last, &p), who, src)
}

/// Whether the keys `who` are `src`'s authority set for row `i`: over its own past, and with every end the reader
/// holds ([`ended_for_reader`]).
fn speaks_at<R: TrustRow, S: CutSpec<R>>(
    seats: &Seats<'_, '_, R, S>,
    i: usize,
    who: &BTreeSet<&R::Key>,
    src: &ObjOf<R>,
) -> bool {
    let c = seats.c();
    [false, true].iter().all(|&read| speaks_over(seats, i, &ended_for_reader(c, i, read), who, src))
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

/// An edge's own term (`asserted_at <= t < valid_until`, as a license seat's) covers instant `t`: the caller's
/// instant, or the licence's own; with no instant, only an edge that states no term.
fn edge_term<R: Dated>(r: &R, t: Option<&R::Instant>) -> bool {
    match t {
        None => r.valid_until().is_none(),
        Some(t) => crate::covers_at(r.asserted_at(), r.valid_until(), t),
    }
}

/// The acceptance edges the concluded rows give at instant `t`: each admitted edge its owner's authority set signed
/// (over its own past and with every end the reader holds), within its term, no withdrawal by that set ended; its
/// `src` is its owner.
pub fn edges_of<R: TrustRow + Dated, S: CutSpec<R>>(
    seats: &Seats<'_, '_, R, S>,
    t: Option<&R::Instant>,
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
        if !edge_term(r, t) {
            continue;
        }
        if !speaks_at(seats, i, &signers(r), &e.src) {
            continue;
        }
        let ended = c.cs().iter().any(|&j| {
            let w = c.g.row(j);
            w.seat_kind() == SeatKind::Withdraw
                && w.target() == Some(r.id())
                && speaks_at(seats, j, &signers(w), &e.src)
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
    if let Some(t) = t {
        if idx.iter().any(|&j| c.g.row(j).asserted_at().is_some_and(|u| u > t)) {
            return Some(INSTANT_BEFORE_PAST);
        }
    }
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
        let voices: BTreeSet<R::Key> = signers(r).into_iter().cloned().collect();
        if declared_count(&past, &a, &at.protocol_body(&a), &voices) {
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

/// Whether licence row `i` is its authority's act in force for the reader holding the rows `seats` was built on:
/// `None`, or the reason it CONCLUDES NOTHING in the authority's fold (never a refusal: the licence row is admitted,
/// and the reason reads other rows, CC 2.7.3). Its existence is judged over its own past ([`ended_for_reader`],
/// `read` false): [`NOT_AUTHORITY`] (testimony), [`AUTHORITY_LOCKED`] (a locked community's quorum) or
/// [`INSTANT_BEFORE_PAST`]. Then every end the reader holds is read over the reader's rows: a licence that stood and is
/// cut so is [`LINK_WITHDRAWN`], or [`AUTHORITY_LOCKED`] where the end locks its community.
pub fn standing<R: TrustRow + Dated, S: CutSpec<R>>(seats: &Seats<'_, '_, R, S>, i: usize) -> Option<&'static str> {
    let c = seats.c();
    if let Some(why) = issuance(seats, i, &ended_for_reader(c, i, false)) {
        return Some(why);
    }
    match issuance(seats, i, &ended_for_reader(c, i, true)) {
        None => None,
        Some(AUTHORITY_LOCKED) => Some(AUTHORITY_LOCKED),
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
    // a dissolved authority (CC 4.4.3.12, "What stands after dissolution"): an issued licence stands, its authority
    // judged at issuance, and reads `lapsed` for every later use; one with no standing over its own past is testimony
    // (the issuance judgement first, over the licence's own past: its standing, then its class; only a licence that
    // stood then reads `lapsed`)
    if is_community(seats, &auth) && seats.dissolved(&auth) {
        if let Some(why) = standing(seats, i) {
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
    if let Some(why) = standing(seats, i) {
        return Err(Unhonoured::Standing(why));
    }
    let t = now.copied().or(r.asserted_at());
    if !reaches(&edges_of(seats, t.as_ref()), reader, cls, HOP_CAP, &auth) {
        return Err(Unhonoured::NotReached);
    }
    Ok(())
}
