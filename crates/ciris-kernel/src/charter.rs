//! Charter coverage for licensing authorities (CC 3.4.7; CC 4.4.3.12, 4.4.3.34): `charter.py`.
//!
//! A licensing authority is an **affiliation**: a community record of kind `affiliation` (its founding row's
//! [`SeatRow::group_kind`], [`kind_of`]). Its charter is that record's own [`SeatRow::licence_classes`]; there is no
//! separate charter row. "The charter enumerates the licence classes the affiliation issues."
//!
//! - **The record in force.** The charter is read at read: over the rows the reader holds (the [`Seats`] built for
//!   that reader), never at a licence's own instant, so a class a later amendment drops stops matching every licence
//!   of it, those issued before the amendment included.
//! - **A version** is a change of the affiliation's record (a counted offer of scope `record` over it, the act
//!   `record_change`, [`crate::seat::act_of`]) that concludes under the affiliation's declared protocol and counts for
//!   the reader (the cut, the reader's line, built on: [`Seats::cut`], [`Seats::stale`]). A change below the protocol
//!   concludes nothing and leaves the charter as it was. The Constitution's acts table has no row for it yet; the
//!   fixtures' law carries the model's pending row (`cosigned_act`, fixed). A record change is no act against a
//!   member, so the outside countersign a one-seat affiliation's acts against a member need (CC 4.4.3.12) is not
//!   asked of it.
//! - **Unstated.** A version that states no classes (a rename, a protocol) leaves the classes as they were at its
//!   head.
//! - **The wait** (the Constitution's derived reading). Two version tips that differ wait: the classes declared are
//!   those every tip lists, until a version names them all. A version naming them all that states none keeps the
//!   classes in force at its head: the common ones.
//! - **The reader's side** is [`crate::trust`]: an acceptance edge admits the classes it lists (every class when it
//!   lists none), the walk intersects them hop by hop, and a licence is honoured where the walk reaches its authority
//!   for its class and the authority's charter declares the class ([`crate::trust::honours`] over [`charters`]).
//! - **A licence** (a `licensure` row) is admitted as a row whatever class it states; a class the charter does not
//!   declare is honoured by no reader ([`Untrusted::LicenceClassNotTrusted`]). That is a reading, never a refusal at
//!   the door.
//!
//! **The root's charter** (the trust root bundle's `charter`: its scope list, `sub_delegation`) is another fold. It
//! meets this one at [`charters`]' `supplied`: a charter supplied for an authority is met with the one read from
//! rows ([`Charters::meet`]: the classes both declare), and stands alone for an authority that is no affiliation held.

use crate::cut::CutSpec;
use crate::graph::Graph;
use crate::layers::Concluded;
use crate::seat::{kind_of, CommunityKind, Conf, Obj, SeatKind, SeatRow, Seats};
use crate::trust::{reaches, Accepts, Charters, HOP_CAP};
use crate::Row;
use alloc::collections::{BTreeMap, BTreeSet};
use alloc::vec::Vec;

type ObjOf<R> = Obj<<R as Row>::Id, <R as Row>::Key>;

/// A change of affiliation `aff`'s record: a counted offer of scope `record` over it (the act `record_change`), no
/// dissolution.
pub fn is_version<R: SeatRow>(r: &R, aff: &R::Id) -> bool {
    r.seat_kind() == SeatKind::Offer
        && r.conf() == Some(Conf::Group)
        && r.obj().is_some_and(|o| o == Obj::Row(aff.clone()))
        && r.scope().is_some_and(|s| s.as_ref() == "record")
        && !r.dissolves()
}

fn classes_of<R: SeatRow>(r: &R) -> BTreeSet<R::Word> {
    r.licence_classes().map(|c| c.iter().cloned().collect()).unwrap_or_default()
}

/// The rows `v` names, and those they name, through the concluded rows alone (a row not concluded carries nothing),
/// as [`crate::seat::protocol_record`] orders a record's changes.
fn concluded_past<R: Row>(c: &Concluded<'_, R>, v: usize) -> BTreeSet<usize> {
    let g: &Graph<'_, R> = &c.g;
    let mut out = BTreeSet::new();
    let mut todo: Vec<usize> = g.named(v).to_vec();
    while let Some(i) = todo.pop() {
        if out.insert(i) && c.concluded(i) {
            todo.extend_from_slice(g.named(i));
        }
    }
    out
}

/// The classes common to the tips of `sub` (the versions of `sub` no other has in its concluded past), each read at
/// its own version (`at`); the founding record's where `sub` is empty.
fn meet_tips<W: Ord + Clone>(
    sub: &[usize],
    anc: &BTreeMap<usize, BTreeSet<usize>>,
    at: &BTreeMap<usize, BTreeSet<W>>,
    founding: &BTreeSet<W>,
) -> BTreeSet<W> {
    let mut out: Option<BTreeSet<W>> = None;
    for &t in sub.iter().filter(|&&t| !sub.iter().any(|x| anc[x].contains(&t))) {
        let here = &at[&t];
        out = Some(match out {
            None => here.clone(),
            Some(o) => o.intersection(here).cloned().collect(),
        });
    }
    out.unwrap_or_else(|| founding.clone())
}

/// The classes affiliation `aff`'s record in force declares, over the rows `seats` was built on, for its reader (build
/// it with [`crate::seat::for_reader`] and [`Seats::for_reader`], or [`Seats::new`] for a reader with no row). `None`
/// where no concluded founding row of an affiliation `aff` is held: no charter, so no class is declared.
pub fn declared<R: SeatRow, S: CutSpec<R>>(seats: &Seats<'_, '_, R, S>, aff: &R::Id) -> Option<BTreeSet<R::Word>> {
    let c = seats.c();
    let g = &c.g;
    let gi = g.idx(aff)?;
    if !c.concluded(gi) {
        return None;
    }
    let get = |i: &R::Id| g.idx(i).map(|x| g.row(x));
    if kind_of(seats.law(), &get, &Obj::Row(aff.clone())) != Some(CommunityKind::Affiliation) {
        return None;
    }
    let founding = classes_of(g.row(gi));
    let vs: Vec<usize> = c
        .cs()
        .iter()
        .copied()
        .filter(|&i| is_version(g.row(i), aff) && seats.cut().counts(i) && !seats.stale().contains(&i))
        .collect();
    if vs.is_empty() {
        return Some(founding);
    }
    let anc: BTreeMap<usize, BTreeSet<usize>> = vs.iter().map(|&v| (v, concluded_past(c, v))).collect();
    // each version's classes in force, lower levels first: its own where it states them, else those at its head
    let mut order = vs.clone();
    order.sort_by_key(|&v| g.level(v));
    let mut at: BTreeMap<usize, BTreeSet<R::Word>> = BTreeMap::new();
    for &v in &order {
        let got = match g.row(v).licence_classes() {
            Some(cs) => cs.iter().cloned().collect(),
            None => {
                let sub: Vec<usize> = vs.iter().copied().filter(|x| anc[&v].contains(x)).collect();
                meet_tips(&sub, &anc, &at, &founding)
            }
        };
        at.insert(v, got);
    }
    Some(meet_tips(&vs, &anc, &at, &founding))
}

/// Every affiliation whose concluded founding row `seats` holds, as `Obj::Row(id)`, with the classes its record in
/// force declares for the reader ([`declared`]), each met with the charter `supplied` gives for it; a supplied charter
/// for an authority that is no affiliation held stands alone. The value [`crate::trust::honours`] reads.
pub fn charters<R: SeatRow, S: CutSpec<R>>(
    seats: &Seats<'_, '_, R, S>,
    supplied: &Charters<ObjOf<R>, R::Word>,
) -> Charters<ObjOf<R>, R::Word> {
    let c = seats.c();
    let mut out = Charters::new();
    for &i in c.cs() {
        let r = c.g.row(i);
        if r.seat_kind() == SeatKind::Offer && r.obj().is_some_and(|o| o == Obj::Row(r.id().clone())) {
            if let Some(d) = declared(seats, r.id()) {
                out.meet(Obj::Row(r.id().clone()), d);
            }
        }
    }
    for (a, cs) in supplied.iter() {
        out.meet(a.clone(), cs.iter().cloned());
    }
    out
}

/// Why a reader does not honour a licence.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Untrusted {
    /// The authority's charter does not declare the licence's class (`licence_class_not_trusted`).
    LicenceClassNotTrusted,
    /// The reader's walk does not reach the authority for the class.
    AuthorityNotReached,
}

impl Untrusted {
    /// The reason's word (`charter.py`'s).
    pub fn word(self) -> &'static str {
        match self {
            Untrusted::LicenceClassNotTrusted => "licence_class_not_trusted",
            Untrusted::AuthorityNotReached => "authority_not_reached",
        }
    }
}

/// Whether `reader` honours a licence of class `cls` issued under `authority` (the licence row's own fields), read
/// over the rows `seats` was built on, with the reader's acceptance edges and the charters `supplied` from elsewhere:
/// `Ok` where the authority's charter declares the class and the reader's walk, within the cap, reaches it for that
/// class. The licence row itself is admitted whatever this answers.
pub fn read_licence<R: SeatRow, S: CutSpec<R>>(
    seats: &Seats<'_, '_, R, S>,
    edges: &[Accepts<ObjOf<R>, R::Word>],
    reader: &ObjOf<R>,
    authority: &ObjOf<R>,
    cls: &R::Word,
    supplied: &Charters<ObjOf<R>, R::Word>,
) -> Result<(), Untrusted> {
    if !charters(seats, supplied).declares(authority, cls) {
        return Err(Untrusted::LicenceClassNotTrusted);
    }
    if !reaches(edges, reader, cls, HOP_CAP, authority) {
        return Err(Untrusted::AuthorityNotReached);
    }
    Ok(())
}
