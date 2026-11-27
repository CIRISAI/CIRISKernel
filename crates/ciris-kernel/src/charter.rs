//! Charter coverage for licensing authorities (CC 3.4.7; CC 4.4.3.12, 4.4.3.34): `charter.py`.
//!
//! "Anyone may be an authority under their own key, a community included." A community's charter is its record's own
//! [`SeatRow::licence_classes`]: each a class and its `legal_weight`. There is no separate charter row. An
//! **affiliation** is a community record whose [`SeatRow::declared_cohort`] is `affiliations`
//! ([`CommunityKind::Affiliation`]); charter coverage reads the classes from any community record (a community, an
//! infrastructure community, an affiliation), and a community declaring a class with legal weight takes on the
//! affiliation's duties for it, whatever its declared cohort. A family's record, an accord's and a self roster's are
//! no charter.
//!
//! - **The record in force.** The charter is read at read: over the rows the reader holds (the [`Seats`] built for
//!   that reader), never at a licence's own instant, so a class a later amendment drops stops matching every licence
//!   of it, those issued before the amendment included.
//! - **A version** is a change of the record (a counted offer of scope `record` over it, the act `record_change`,
//!   [`crate::seat::act_of`]) that concludes under the record's protocol and counts for the reader (the cut, the
//!   reader's line, built on: [`Seats::cut`], [`Seats::stale`]). A change below the protocol concludes nothing and
//!   leaves the charter as it was. A record change is no act against a member, so the outside countersign a one-seat
//!   affiliation's acts against a member need (CC 4.4.3.12) is not asked of it.
//! - **Whole.** A version is the whole record: one that states no classes declares none.
//! - **The wait** (the Constitution's derived reading). Two version tips that differ wait: the classes declared are
//!   those every tip lists, until a version names them all. A class is listed with its legal weight, and the pair is
//!   what the tips must share.
//! - **Dissolved.** A dissolved group declares nothing ([`Seats::dissolved`]: a concluded dissolution, or the lapse of
//!   the last deciding seat, the no-signer dissolution). A record version's own stated end (`dissolves_at`, read as
//!   [`Dated::valid_until`]) is read against the caller's instant `now`, where it gives one: a version whose end is at
//!   or before `now` declares nothing.
//! - **The reader's side** is [`crate::trust`]: an acceptance edge admits the classes it lists (every class when its
//!   `trust_classes` is absent; a malformed list is refused at admission, [`crate::trust::Accepts::refusal`]), the
//!   walk intersects them hop by hop, and a licence is honoured where the walk reaches its authority for its class
//!   and the authority's charter declares the class ([`crate::trust::honours`] over [`charters`]).
//! - **A licence** (a `licensure` row) is admitted as a row whatever class it states; a class the charter does not
//!   declare is honoured by no reader ([`Untrusted::LicenceClassNotTrusted`]). That is a reading, never a refusal at
//!   the door.
//!
//! **The root's charter** (the trust root bundle's `charter`: its scope list, `sub_delegation`) is another fold. It
//! meets this one at [`charters`]' `supplied`: a charter supplied for an authority is met with the one read from
//! rows ([`Charters::meet`]: the classes both declare), and stands alone for an authority that is no community held.

use crate::cut::CutSpec;
use crate::graph::Graph;
use crate::layers::Concluded;
use crate::seat::{kind_of, CommunityKind, Conf, Obj, SeatKind, SeatRow, Seats};
use crate::trust::{reaches, Accepts, Charters, HOP_CAP};
use crate::{Dated, Row};
use alloc::collections::{BTreeMap, BTreeSet};
use alloc::vec::Vec;

type ObjOf<R> = Obj<<R as Row>::Id, <R as Row>::Key>;

/// The kinds of record that are a charter: the community records.
pub const CHARTER_KINDS: [CommunityKind; 3] =
    [CommunityKind::Community, CommunityKind::Infrastructure, CommunityKind::Affiliation];

/// A change of community `aff`'s record: a counted offer of scope `record` over it (the act `record_change`), no
/// dissolution.
pub fn is_version<R: SeatRow>(r: &R, aff: &R::Id) -> bool {
    r.seat_kind() == SeatKind::Offer
        && r.conf() == Some(Conf::Group)
        && r.obj().is_some_and(|o| o == Obj::Row(aff.clone()))
        && r.scope().is_some_and(|s| s.as_ref() == "record")
        && !r.dissolves()
}

/// The (class, legal_weight) pairs a record version lists: none where it states none, and none once its own stated
/// end is at or before `now`.
fn classes_of<R: SeatRow + Dated>(r: &R, now: Option<&R::Instant>) -> BTreeSet<(R::Word, bool)> {
    if now.is_some_and(|t| r.valid_until().is_some_and(|u| *t >= u)) {
        return BTreeSet::new();
    }
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

/// The (class, legal_weight) pairs community `aff`'s record in force declares, over the rows `seats` was built on, for
/// its reader (build it with [`crate::seat::for_reader`] and [`Seats::for_reader`], or [`Seats::new`] for a reader
/// with no row), at the caller's instant `now` (`None`: no clock is read). `None` where no concluded founding row of a
/// community record `aff` is held: no charter, so no class is declared. Empty where the group is dissolved.
pub fn declared<R: SeatRow + Dated, S: CutSpec<R>>(
    seats: &Seats<'_, '_, R, S>,
    aff: &R::Id,
    now: Option<&R::Instant>,
) -> Option<BTreeSet<(R::Word, bool)>> {
    let c = seats.c();
    let g = &c.g;
    let gi = g.idx(aff)?;
    if !c.concluded(gi) {
        return None;
    }
    let get = |i: &R::Id| g.idx(i).map(|x| g.row(x));
    let obj = Obj::Row(aff.clone());
    if !kind_of(seats.law(), &get, &obj).is_some_and(|k| CHARTER_KINDS.contains(&k)) {
        return None;
    }
    if seats.dissolved(&obj) {
        return Some(BTreeSet::new());
    }
    let vs: Vec<usize> = c
        .cs()
        .iter()
        .copied()
        .filter(|&i| is_version(g.row(i), aff) && seats.cut().counts(i) && !seats.stale().contains(&i))
        .collect();
    if vs.is_empty() {
        return Some(classes_of(g.row(gi), now));
    }
    // the tips among the versions, read over the concluded rows alone (as seat::protocol_record); each declares its
    // own pairs, and the pairs declared are those every tip lists
    let anc: BTreeMap<usize, BTreeSet<usize>> = vs.iter().map(|&v| (v, concluded_past(c, v))).collect();
    let mut out: Option<BTreeSet<(R::Word, bool)>> = None;
    for &t in vs.iter().filter(|&&t| !vs.iter().any(|x| anc[x].contains(&t))) {
        let here = classes_of(g.row(t), now);
        out = Some(match out {
            None => here,
            Some(o) => o.intersection(&here).cloned().collect(),
        });
    }
    out
}

/// Every community whose concluded founding row `seats` holds, as `Obj::Row(id)`, with the classes its record in
/// force declares for the reader at `now` ([`declared`]), each met with the charter `supplied` gives for it; a
/// supplied charter for an authority that is no community held stands alone. The value [`crate::trust::honours`]
/// reads.
pub fn charters<R: SeatRow + Dated, S: CutSpec<R>>(
    seats: &Seats<'_, '_, R, S>,
    supplied: &Charters<ObjOf<R>, R::Word>,
    now: Option<&R::Instant>,
) -> Charters<ObjOf<R>, R::Word> {
    let c = seats.c();
    let mut out = Charters::new();
    for &i in c.cs() {
        let r = c.g.row(i);
        if r.seat_kind() == SeatKind::Offer && r.obj().is_some_and(|o| o == Obj::Row(r.id().clone())) {
            if let Some(d) = declared(seats, r.id(), now) {
                out.meet(Obj::Row(r.id().clone()), d.into_iter().map(|(cls, _)| cls));
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
/// over the rows `seats` was built on at the caller's instant `now`, with the reader's acceptance edges and the
/// charters `supplied` from elsewhere: `Ok` where the authority's charter declares the class and the reader's walk,
/// within the cap, reaches it for that class. The licence row itself is admitted whatever this answers.
pub fn read_licence<R: SeatRow + Dated, S: CutSpec<R>>(
    seats: &Seats<'_, '_, R, S>,
    edges: &[Accepts<ObjOf<R>, R::Word>],
    reader: &ObjOf<R>,
    authority: &ObjOf<R>,
    cls: &R::Word,
    supplied: &Charters<ObjOf<R>, R::Word>,
    now: Option<&R::Instant>,
) -> Result<(), Untrusted> {
    if !charters(seats, supplied, now).declares(authority, cls) {
        return Err(Untrusted::LicenceClassNotTrusted);
    }
    if !reaches(edges, reader, cls, HOP_CAP, authority) {
        return Err(Untrusted::AuthorityNotReached);
    }
    Ok(())
}
