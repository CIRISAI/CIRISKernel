//! The reader's trust walk from rows, and the issuer's standing (CC 4.4.3.34; CC 2.7.5): `trust_rows.py`.
//!
//! An acceptance edge is a row: a `delegates_to` row bearing [`BEARS`] (`trust:accepts:v1`), naming the authority it
//! accepts ([`TrustRow::accepts_dst`]), with `trust_classes` (absent: every class the charter declares) and
//! `trust_depth`. Whose edge it is: its signer's, or, where it speaks for another ([`TrustRow::on_behalf`]), that
//! authority's, if ruling (a) says the signer speaks for it.
//!
//! - **Admission.** An edge whose `trust_classes` list is empty, unsorted or names a class twice is refused
//!   ([`crate::trust::Accepts::refusal`], the one place); one whose depth ruling (c) refuses is refused
//!   ([`DEPTH_MALFORMED`]). A refused edge is no edge.
//! - **Ended.** An edge ruling (d) holds ended is no edge.
//! - **The walk.** From the reader's own edges (signed by the reader); an onward hop only from an authority's own
//!   edges (ruling (a)); the classes intersect hop by hop; a key is expanded again only with more budget than before,
//!   so a cycle is visited once; nothing is cached across reads; within the cap of five ([`crate::trust::reaches`],
//!   which finds what the model's breadth-first walk finds).
//! - **The issuer.** A licence is honoured iff the walk reaches its authority for its class, the authority's record
//!   declares the class ([`crate::charter`]), and the licence row is the authority's act (ruling (b)).
//!
//! The four rulings are with the Constitution and plug in through [`Rulings`]; [`Pending`] is what the crate reads
//! until they land. Where a ruling is pending the answer is [`Unhonoured::Pending`] with its reason, never a silent
//! pass:
//! - (a) [`Rulings::speaks_for`]: a key speaks for itself alone; for a community authority `authority_set_pending`.
//! - (b) [`Rulings::issued_by`]: a key authority's licence is the one it signs; a community authority's
//!   `issuer_standing_pending`.
//! - (c) [`Rulings::depth`]: 0 to 5, else refused.
//! - (d) [`Rulings::ended`]: a concluded withdrawal of the edge by its signer is held.

use crate::charter::{charters, CHARTER_KINDS};
use crate::cut::CutSpec;
use crate::seat::{kind_of, Obj, SeatKind, SeatRow, Seats};
use crate::trust::{reaches, Accepts, Charters, HOP_CAP};
use crate::{Dated, Row};
use alloc::collections::BTreeSet;
use alloc::vec::Vec;

type ObjOf<R> = Obj<<R as Row>::Id, <R as Row>::Key>;

/// What an acceptance edge row bears.
pub const BEARS: &str = "trust:accepts:v1";
/// The admission's refusal of an edge whose `trust_depth` ruling (c) refuses.
pub const DEPTH_MALFORMED: &str = "trust_accepts_depth_malformed";

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
    /// An edge's `trust_depth`, as stated.
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

/// A ruling's answer.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Ruled {
    /// It holds.
    Yes,
    /// It does not.
    No,
    /// The ruling is pending: undecided, with its reason.
    Pending(&'static str),
}

/// `o` is a held, concluded community record: an authority whose authority set is ruling (a)'s.
pub fn is_community<R: SeatRow, S: CutSpec<R>>(seats: &Seats<'_, '_, R, S>, o: &ObjOf<R>) -> bool {
    let Obj::Row(id) = o else { return false };
    let c = seats.c();
    let g = &c.g;
    let get = |i: &R::Id| g.idx(i).map(|x| g.row(x));
    c.concluded_id(id) && kind_of(seats.law(), &get, o).is_some_and(|k| CHARTER_KINDS.contains(&k))
}

/// The rulings (a) to (d). The defaults are [`Pending`]'s: what the crate reads until the Constitution's land.
pub trait Rulings<R: TrustRow, S: CutSpec<R>> {
    /// (a) Whether edge `row` is authority `src`'s own.
    fn speaks_for(&self, seats: &Seats<'_, '_, R, S>, row: &R, src: &ObjOf<R>) -> Ruled {
        if *src == Obj::Key(row.signer().clone()) {
            Ruled::Yes
        } else if is_community(seats, src) {
            Ruled::Pending("authority_set_pending")
        } else {
            Ruled::No
        }
    }
    /// (b) Whether licence `lic` is authority `auth`'s act.
    fn issued_by(&self, seats: &Seats<'_, '_, R, S>, lic: &R, auth: &ObjOf<R>) -> Ruled {
        if *auth == Obj::Key(lic.signer().clone()) {
            Ruled::Yes
        } else if is_community(seats, auth) {
            Ruled::Pending("issuer_standing_pending")
        } else {
            Ruled::No
        }
    }
    /// (c) The depth an edge stating `d` walks with, or `None`: refused.
    fn depth(&self, d: i64) -> Option<u32> {
        (0..=HOP_CAP as i64).contains(&d).then_some(d as u32)
    }
    /// (d) Whether the edge at index `i` of the concluded set is ended for the reader.
    fn ended(&self, seats: &Seats<'_, '_, R, S>, i: usize) -> bool {
        let c = seats.c();
        let r = c.g.row(i);
        c.cs()
            .iter()
            .map(|&j| c.g.row(j))
            .any(|w| w.seat_kind() == SeatKind::Withdraw && w.target() == Some(r.id()) && w.signer() == r.signer())
    }
}

/// The rulings as the crate reads them until the Constitution's land.
#[derive(Clone, Copy, Debug, Default)]
pub struct Pending;

impl<R: TrustRow, S: CutSpec<R>> Rulings<R, S> for Pending {}

/// An acceptance edge row at its own reading: not an edge, refused at admission (with the reason), or an edge.
fn edge_of<R: TrustRow, S: CutSpec<R>>(
    seats: &Seats<'_, '_, R, S>,
    rulings: &impl Rulings<R, S>,
    r: &R,
) -> Option<Result<Accepts<ObjOf<R>, R::Word>, &'static str>> {
    if !r.is_delegates_to() || r.bears().is_none_or(|b| b.as_ref() != BEARS) {
        return None;
    }
    let dst = r.accepts_dst()?;
    let src = r.on_behalf().unwrap_or_else(|| Obj::Key(r.signer().clone()));
    let mut e = Accepts { src, dst, classes: r.trust_classes().map(|c| c.to_vec()), depth: 0 };
    if let Some(why) = e.refusal() {
        return Some(Err(why));
    }
    match r.trust_depth().and_then(|d| rulings.depth(d)) {
        Some(d) => e.depth = d,
        None => return Some(Err(DEPTH_MALFORMED)),
    }
    Some(Ok(e))
}

/// The admission's refusal of acceptance edge row `r`, or `None` (an edge, or no `delegates_to` bearing [`BEARS`]).
pub fn refusal<R: TrustRow, S: CutSpec<R>>(
    seats: &Seats<'_, '_, R, S>,
    rulings: &impl Rulings<R, S>,
    r: &R,
) -> Option<&'static str> {
    edge_of(seats, rulings, r).and_then(|e| e.err())
}

/// The acceptance edges the concluded rows give: each admitted, live edge whose owner ruling (a) decides, with `None`,
/// and each whose owner it leaves pending, with the reason. An edge's `src` is its owner.
pub fn edges_of<R: TrustRow, S: CutSpec<R>>(
    seats: &Seats<'_, '_, R, S>,
    rulings: &impl Rulings<R, S>,
) -> Vec<(Accepts<ObjOf<R>, R::Word>, Option<&'static str>)> {
    let c = seats.c();
    let mut out = Vec::new();
    for &i in c.cs() {
        let r = c.g.row(i);
        let Some(Ok(e)) = edge_of(seats, rulings, r) else { continue };
        if rulings.ended(seats, i) {
            continue;
        }
        match rulings.speaks_for(seats, r, &e.src) {
            Ruled::Yes => out.push((e, None)),
            Ruled::Pending(why) => out.push((e, Some(why))),
            Ruled::No => {}
        }
    }
    out
}

/// Why a reader does not honour a licence.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Unhonoured {
    /// The licence row is not held.
    NotHeld,
    /// The authority's record does not declare the class (`licence_class_not_trusted`).
    ClassNotTrusted,
    /// The licence is not the authority's act (`licence_not_the_authoritys_act`).
    NotTheAuthoritysAct,
    /// The reader's walk does not reach the authority for the class (`authority_not_reached`).
    NotReached,
    /// A pending ruling leaves it undecided (its reason).
    Pending(&'static str),
}

impl Unhonoured {
    /// The reason's word (`trust_rows.py`'s).
    pub fn word(self) -> &'static str {
        match self {
            Unhonoured::NotHeld => "not_held",
            Unhonoured::ClassNotTrusted => "licence_class_not_trusted",
            Unhonoured::NotTheAuthoritysAct => "licence_not_the_authoritys_act",
            Unhonoured::NotReached => "authority_not_reached",
            Unhonoured::Pending(w) => w,
        }
    }
}

/// Whether `reader` honours licence row `licence`, read over the rows `seats` was built on at the caller's instant
/// `now`, with the acceptance edges those rows give, the charters `supplied` from elsewhere and the `rulings`: `Ok`
/// where the authority's record declares the licence's class, the licence is the authority's act, and the reader's
/// walk reaches the authority for the class. Where only an edge whose owner is pending would reach it, the pending
/// reason. The licence row itself is admitted whatever this answers.
pub fn read_licence<R: TrustRow + Dated, S: CutSpec<R>>(
    seats: &Seats<'_, '_, R, S>,
    rulings: &impl Rulings<R, S>,
    reader: &ObjOf<R>,
    licence: &R::Id,
    supplied: &Charters<ObjOf<R>, R::Word>,
    now: Option<&R::Instant>,
) -> Result<(), Unhonoured> {
    let c = seats.c();
    let r = c.g.idx(licence).map(|i| c.g.row(i)).ok_or(Unhonoured::NotHeld)?;
    let (Some(auth), Some(cls)) = (r.licence_authority(), r.licence_class()) else {
        return Err(Unhonoured::ClassNotTrusted);
    };
    if !charters(seats, supplied, now).declares(&auth, cls) {
        return Err(Unhonoured::ClassNotTrusted);
    }
    match rulings.issued_by(seats, r, &auth) {
        Ruled::Yes => {}
        Ruled::No => return Err(Unhonoured::NotTheAuthoritysAct),
        Ruled::Pending(why) => return Err(Unhonoured::Pending(why)),
    }
    let es = edges_of(seats, rulings);
    let decided: Vec<Accepts<ObjOf<R>, R::Word>> =
        es.iter().filter(|(_, why)| why.is_none()).map(|(e, _)| e.clone()).collect();
    if reaches(&decided, reader, cls, HOP_CAP, &auth) {
        return Ok(());
    }
    let pending: BTreeSet<&'static str> = es.iter().filter_map(|(_, why)| *why).collect();
    let all: Vec<Accepts<ObjOf<R>, R::Word>> = es.into_iter().map(|(e, _)| e).collect();
    match pending.iter().next() {
        Some(&why) if reaches(&all, reader, cls, HOP_CAP, &auth) => Err(Unhonoured::Pending(why)),
        _ => Err(Unhonoured::NotReached),
    }
}
