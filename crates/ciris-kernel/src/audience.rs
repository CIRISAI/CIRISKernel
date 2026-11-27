//! Where a row is placed and who it is for, family by family (CC 3.4.5.1, CC 5.2).
//!
//! The table is the family model's placement cells (the Constitution's `manifests/family_model.json`), derived and
//! pinned by `tools/family_placement.py` into `data/family_placement.json` and [`FAMILIES`]. The reference is
//! `models/causal_kernel/audience.py`, checked by `check_audience.py`; `tests/audience.rs` replays its fixture.
//!
//! **An audience is keys.** The room's roster ([`crate::seat::Seats::roster`]), the signer's own keys, the keys a
//! row names. Which nodes a key's rows go to (its claimed nodes) is the store's.
//!
//! * **Family.** A row's family is matched against the table's patterns: a segment `{name}` matches one segment, a
//!   final `*` one or more; the pattern with the most literal segments that matches decides. No pattern:
//!   [`Refusal::FamilyUnknown`]; two that tie: [`Refusal::FamilyAmbiguous`] ([`family_in`]).
//! * **Placement.** The cohort scope a row states is its placement ([`SCOPES`]): `self` is self_collective,
//!   `family` targeted_family, `community` and `affiliations` targeted_room, `species`, `biosphere` and
//!   `federation` commons, and `addressed` a row for the keys it names. A family on the default takes any of the
//!   first four, chosen for each row; a family the CC table pins takes only the placements its cell names
//!   ([`Refusal::PlacementNotAllowed`]). A family whose cell is not table data is [`Placed::Undecided`], naming
//!   the family: no default is taken for it.
//! * **Audience.** Every audience holds the signer and the keys the row names. Self_collective: the signer's own
//!   keys. Targeted: the room's roster; a row there may name only keys that were members at its own head
//!   ([`Joins::at_head`]; [`Refusal::NamedOutsideAudience`]), so its placement never changes with a later removal
//!   or admission, and names its room ([`Refusal::NoRoom`]). The keys a seat offer or unseat over the room seats or
//!   removes ([`seats_of`], derived from the row, never stated) are always within its audience, ahead of that rule:
//!   a pending admission names its joiner, a removal its removed key. The roster is the roster as it stands (CC 5.2:
//!   a member removed later is owed nothing further), less the members admitted after the row unless its
//!   `history_on_join` is full: the row's own ([`AudienceRow::history_on_join`]), else the room record's
//!   ([`Joins::history`]), else from_join. Commons: everyone. Addressed:
//!   the keys it names.
//! * **Copy** ([`audiences`], [`carried`]: the Constitution's proposal c). Carriage is of rows: a room row is
//!   carried by a concluded room row of its room to that row's audience on the room's current roster; nothing
//!   reaches a key off the roster; a self or addressed row is carried only by a concluded row of its own signer or
//!   that signer's person; the carrier's signer is already in the row's audience; a key grant is never carried.
//!   A refused or undecided row carries nothing and receives nothing.
//! * **Served is not readable.** `history_on_join` changes no audience: a later joiner is served the older room
//!   rows, sealed by keys it lacks (the tier gives the current epoch's key only, CC 4.4.3.16). `full` acts only on
//!   a kept stream, through its producer's own key grants within the catch-up bound: the caller's ([`history_of`]).

use alloc::collections::{BTreeMap, BTreeSet};
use alloc::vec::Vec;

#[rustfmt::skip]
#[path = "audience_table.rs"]
mod table;
pub use table::{FAMILIES, FAMILY_MODEL_SHA256, SCOPES, SEAT_FAMILIES};

/// The key grant family's pattern: a row that resolves to it is never carried.
pub const KEY_GRANT: &str = "key_grant:{axis}";

/// Where a row is placed.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum Placement {
    /// The owner's own keys.
    SelfCollective,
    /// A family's members.
    TargetedFamily,
    /// A room's roster.
    TargetedRoom,
    /// Everyone.
    Commons,
    /// The keys the row names.
    Addressed,
}

impl Placement {
    /// The placement's word in the family model.
    pub fn word(self) -> &'static str {
        match self {
            Placement::SelfCollective => "self_collective",
            Placement::TargetedFamily => "targeted_family",
            Placement::TargetedRoom => "targeted_room",
            Placement::Commons => "commons",
            Placement::Addressed => "addressed",
        }
    }

    /// The placement a cohort scope word is ([`SCOPES`]).
    pub fn of_scope(scope: &str) -> Option<Placement> {
        SCOPES.iter().find(|(s, _)| *s == scope).map(|(_, p)| *p)
    }
}

/// A family's placement cell.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum FamilyPlacement {
    /// The placements a row of the family may take.
    Allowed(&'static [Placement]),
    /// The cell is not table data (a code, prose or gap source): the Constitution has not stated it.
    Undecided,
}

/// Who a row is for.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Audience<K> {
    /// Every key.
    Everyone,
    /// These keys.
    Keys(BTreeSet<K>),
}

impl<K: Ord + Clone> Audience<K> {
    /// The key is in the audience.
    pub fn holds(&self, k: &K) -> bool {
        match self {
            Audience::Everyone => true,
            Audience::Keys(ks) => ks.contains(k),
        }
    }

    fn meet(&self, other: &Audience<K>) -> Audience<K> {
        match (self, other) {
            (Audience::Everyone, b) => b.clone(),
            (a, Audience::Everyone) => a.clone(),
            (Audience::Keys(a), Audience::Keys(b)) => Audience::Keys(a.intersection(b).cloned().collect()),
        }
    }

    fn join(&mut self, other: &Audience<K>) -> bool {
        match other {
            Audience::Everyone => {
                let was = matches!(self, Audience::Everyone);
                *self = Audience::Everyone;
                !was
            }
            Audience::Keys(b) => match self {
                Audience::Everyone => false,
                Audience::Keys(a) => {
                    let n = a.len();
                    a.extend(b.iter().cloned());
                    a.len() != n
                }
            },
        }
    }
}

/// Why a row is refused a placement.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Refusal {
    /// No family pattern matches the row's family.
    FamilyUnknown,
    /// The row states no cohort scope the table knows.
    ScopeUnknown,
    /// The family's cell does not take this placement.
    PlacementNotAllowed,
    /// A targeted row names a key off the room's roster (CC 5.2).
    NamedOutsideAudience,
    /// A targeted row names no room.
    NoRoom,
    /// Two family patterns tie on the row's family.
    FamilyAmbiguous,
}

impl Refusal {
    /// The refusal's name in the reference and the fixture.
    pub fn as_str(self) -> &'static str {
        match self {
            Refusal::FamilyUnknown => "family_unknown",
            Refusal::ScopeUnknown => "scope_unknown",
            Refusal::PlacementNotAllowed => "placement_not_allowed",
            Refusal::NamedOutsideAudience => "named_outside_audience",
            Refusal::NoRoom => "no_room",
            Refusal::FamilyAmbiguous => "family_ambiguous",
        }
    }
}

/// The answer for one row.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Placed<K> {
    /// Placed, with its audience.
    Placed(Placement, Audience<K>),
    /// Refused.
    Refused(Refusal),
    /// The family's placement cell is not table data: the family pattern.
    Undecided(&'static str),
}

/// What a later member receives of the rows before its join (CC 2.1, CC 4.4.3.16).
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum History {
    /// The rows before the join too.
    Full,
    /// Only the rows from the join (the default).
    FromJoin,
}

impl History {
    /// The value's word on the wire.
    pub fn from_word(w: &str) -> Option<History> {
        match w {
            "full" => Some(History::Full),
            "from_join" => Some(History::FromJoin),
            _ => None,
        }
    }
}

/// How the room's members joined, the caller's: read for a targeted row's audience.
pub struct Joins<'a, I, K> {
    /// The `history_on_join` the room's record states, where it states one (an unknown word: none). It changes no
    /// audience; [`history_of`] reads it for a kept stream.
    pub history: &'a dyn Fn(&I) -> Option<History>,
    /// The members of the room at the row's own head ([`crate::seat::members_at`]), which `named_within` reads.
    /// No fallback to the current roster: that would make a row's placement change with a later removal.
    pub at_head: &'a dyn Fn(&I, &I) -> BTreeSet<K>,
}

/// What a seat row is to the room it names.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum SeatAct {
    /// A seat offer: its `to` are seated.
    Offer,
    /// An unseat: its `to` are removed.
    Unseat,
}

/// A row as this module reads it. The caller has verified and decoded it.
pub trait AudienceRow {
    /// The row's digest; also a room's id.
    type Id: Ord + Clone;
    /// A key id.
    type Key: Ord + Clone;
    /// The row's own digest.
    fn id(&self) -> &Self::Id;
    /// The row's family name.
    fn family(&self) -> &str;
    /// The cohort scope the row states, or `addressed`.
    fn scope(&self) -> &str;
    /// The room or family a targeted row is in.
    fn room(&self) -> Option<&Self::Id>;
    /// The key that signed it.
    fn signer(&self) -> &Self::Key;
    /// The keys the row names: attested, subjects, `for_key_id`.
    fn named(&self) -> &[Self::Key];
    /// The rows it names.
    fn names(&self) -> &[Self::Id];
    /// On a seat row: whether it is an offer or an unseat. `None` on every other row.
    fn seat_act(&self) -> Option<SeatAct> {
        None
    }
    /// On a seat row: the object it is over.
    fn obj(&self) -> Option<&Self::Id> {
        None
    }
    /// On a seat row: the keys it seats or removes.
    fn to(&self) -> &[Self::Key] {
        &[]
    }
    /// The row concludes.
    fn concluded(&self) -> bool;
    /// The row's own `history_on_join` (set per stream by its producer, CC 2.1), where it states one. A word the
    /// caller does not know ([`History::from_word`] gives none) is absent: the door refuses it.
    fn history_on_join(&self) -> Option<History> {
        None
    }
}

// the number of literal segments by which `pattern` matches `name`
fn matches(pattern: &str, name: &str) -> Option<usize> {
    let p: Vec<&str> = pattern.split(':').collect();
    let n: Vec<&str> = name.split(':').collect();
    let (p, n) = if p.last() == Some(&"*") {
        if n.len() < p.len() {
            return None;
        }
        (&p[..p.len() - 1], &n[..p.len() - 1])
    } else if p.len() != n.len() {
        return None;
    } else {
        (&p[..], &n[..])
    };
    let mut lit = 0;
    for (a, b) in p.iter().zip(n) {
        if a.starts_with('{') && a.ends_with('}') {
            continue;
        }
        if a != b {
            return None;
        }
        lit += 1;
    }
    Some(lit)
}

/// How a family name resolves against a table of patterns.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum FamilyMatch<'t> {
    /// No pattern matches.
    None,
    /// The one pattern with the most literal segments, with its cell.
    One(&'t (&'t str, FamilyPlacement)),
    /// Two patterns tie on the name: refused ([`Refusal::FamilyAmbiguous`]).
    Tie,
}

/// How `name` resolves against `table`: the most literal segments among the patterns that match; two that tie
/// decide nothing.
pub fn family_in<'t>(table: &'t [(&'t str, FamilyPlacement)], name: &str) -> FamilyMatch<'t> {
    let mut best: Option<(usize, &'t (&'t str, FamilyPlacement))> = None;
    let mut tie = false;
    for f in table {
        if let Some(k) = matches(f.0, name) {
            match best {
                Some((b, _)) if k < b => {}
                Some((b, _)) if k == b => tie = true,
                _ => {
                    best = Some((k, f));
                    tie = false;
                }
            }
        }
    }
    match best {
        None => FamilyMatch::None,
        Some(_) if tie => FamilyMatch::Tie,
        Some((_, f)) => FamilyMatch::One(f),
    }
}

/// The family pattern that decides a family name in [`FAMILIES`], with its cell; `None` where none matches or two
/// tie.
pub fn family_of(name: &str) -> Option<&'static (&'static str, FamilyPlacement)> {
    match family_in(FAMILIES, name) {
        FamilyMatch::One(f) => Some(f),
        _ => None,
    }
}

/// The keys a seat offer or unseat over the row's own room seats or removes (its `to`): derived from the row, never
/// stated by the caller. Only a row of a seat family ([`SEAT_FAMILIES`]: one whose seats a body confers) seats
/// anyone, so a content row cannot use `to` to pass `named_within`. Empty on every other row.
pub fn seats_of<R: AudienceRow>(r: &R) -> &[R::Key] {
    let seat_family = family_of(r.family()).is_some_and(|f| SEAT_FAMILIES.contains(&f.0));
    if seat_family && r.seat_act().is_some() && r.obj().is_some() && r.obj() == r.room() {
        r.to()
    } else {
        &[]
    }
}

/// The placement and audience of one row, before the copy rule. `roster` is the room's roster as
/// [`crate::seat::Seats::roster`] reads it over the rows held; `person` the keys of the signer's person.
pub fn place<R: AudienceRow>(
    r: &R,
    roster: &dyn Fn(&R::Id) -> BTreeSet<R::Key>,
    person: &dyn Fn(&R::Key) -> BTreeSet<R::Key>,
    joins: &Joins<'_, R::Id, R::Key>,
) -> Placed<R::Key> {
    let &(fam, cell) = match family_in(FAMILIES, r.family()) {
        FamilyMatch::One(f) => f,
        FamilyMatch::None => return Placed::Refused(Refusal::FamilyUnknown),
        FamilyMatch::Tie => return Placed::Refused(Refusal::FamilyAmbiguous),
    };
    let Some(placement) = Placement::of_scope(r.scope()) else { return Placed::Refused(Refusal::ScopeUnknown) };
    let allowed = match cell {
        FamilyPlacement::Undecided => return Placed::Undecided(fam),
        FamilyPlacement::Allowed(a) => a,
    };
    if !allowed.contains(&placement) {
        return Placed::Refused(Refusal::PlacementNotAllowed);
    }
    let mut keys: BTreeSet<R::Key> = r.named().iter().cloned().collect();
    keys.insert(r.signer().clone());
    match placement {
        Placement::Commons => return Placed::Placed(placement, Audience::Everyone),
        Placement::SelfCollective => keys.extend(person(r.signer())),
        Placement::Addressed => {}
        Placement::TargetedFamily | Placement::TargetedRoom => {
            let Some(room) = r.room() else { return Placed::Refused(Refusal::NoRoom) };
            // WHO IS OWED: the current roster (CC 5.2 as ruled: a row is owed to the roster as it stands when the
            // node replicates; a member removed since is owed nothing further)
            let members = roster(room);
            // WHAT IT MAY NAME: the members at the row's own head, so placement never changes with a later removal
            // or admission; the keys a seat offer or unseat seats or removes are within its audience, ahead of it
            let within = (joins.at_head)(room, r.id());
            let seats = seats_of(r);
            if !r.named().iter().all(|k| within.contains(k) || seats.contains(k)) {
                return Placed::Refused(Refusal::NamedOutsideAudience);
            }
            keys.extend(seats.iter().cloned());
            // history_on_join changes no audience: a later joiner is served the older room rows, sealed by keys it
            // lacks (served is not readable; the tier gives the current epoch's key only, CC 4.4.3.16)
            keys.extend(members);
        }
    }
    Placed::Placed(placement, Audience::Keys(keys))
}

/// The `history_on_join` a caller reads for a KEPT STREAM, where `full` lets the producer's own key grants reach
/// a late joiner within the catch-up bound (CC 5.1; the caller's): the row's own, else the room record's, else
/// from_join. It changes no audience here.
pub fn history_of<R: AudienceRow>(r: &R, joins: &Joins<'_, R::Id, R::Key>) -> History {
    r.history_on_join().or_else(|| r.room().and_then(|room| (joins.history)(room))).unwrap_or(History::FromJoin)
}

// a key of `k`'s person, `k` included
fn same_person<K: Ord + Clone>(person: &dyn Fn(&K) -> BTreeSet<K>, k: &K, of: &K) -> bool {
    k == of || person(of).contains(k)
}

/// The keys a concluded placed row `d` naming `r` carries `r` to, or `None`: the copy rule of CC 5.2 as the
/// Constitution read it (proposal c), the one place it is stated. Carriage is of ROWS; served is not readable.
/// * c.1: a room row is carried by a concluded room row of the same room, to that row's audience;
/// * c.2: only to keys on the room's current roster (an offered key that never accepted gets the offer alone, a
///   removed key its removal alone);
/// * c.3: a self or an addressed row is carried only by a concluded row of its own signer or that signer's person,
///   into that row's audience (bounded by c.2 where it is a room row). The contract: `person` is the person's
///   CURRENT, concluded key roster (`seat::Persons` on the key-person lane, once merged; no separate notion), so an
///   evicted or revoked key leaves the person and carries nothing.
///
/// The carrier's signer is already in `r`'s audience (CC 5.2's gate). A key grant is never carried: it reaches only
/// the key it names.
pub fn carried<R: AudienceRow>(
    r: &R,
    a: &Placed<R::Key>,
    d: &R,
    ad: &Placed<R::Key>,
    roster: &dyn Fn(&R::Id) -> BTreeSet<R::Key>,
    person: &dyn Fn(&R::Key) -> BTreeSet<R::Key>,
) -> Option<Audience<R::Key>> {
    let (Placed::Placed(pr, ar), Placed::Placed(pd, aud)) = (a, ad) else { return None };
    let key_grant = family_of(r.family()).is_some_and(|f| f.0 == KEY_GRANT);
    if !d.concluded() || key_grant || !ar.holds(d.signer()) {
        return None;
    }
    let targeted = |p: &Placement| matches!(p, Placement::TargetedFamily | Placement::TargetedRoom);
    let on_roster = |room: &R::Id| aud.meet(&Audience::Keys(roster(room)));
    if targeted(pr) {
        if !targeted(pd) || d.room() != r.room() {
            return None;
        }
        return r.room().map(on_roster);
    }
    if !same_person(person, d.signer(), r.signer()) {
        return None;
    }
    if targeted(pd) {
        d.room().map(on_roster)
    } else {
        Some(aud.clone())
    }
}

/// Every row's answer, the copy rule applied ([`carried`]): a placed row's audience grows by the keys every
/// concluded placed row naming it carries it to; the least fixed point, which only grows. The consequence: a
/// joiner may hold the room's whole named reply chain, as ciphertext it cannot read.
pub fn audiences<R: AudienceRow>(
    rows: &[&R],
    roster: &dyn Fn(&R::Id) -> BTreeSet<R::Key>,
    person: &dyn Fn(&R::Key) -> BTreeSet<R::Key>,
    joins: &Joins<'_, R::Id, R::Key>,
) -> BTreeMap<R::Id, Placed<R::Key>> {
    let mut out: BTreeMap<R::Id, Placed<R::Key>> =
        rows.iter().map(|r| (r.id().clone(), place(*r, roster, person, joins))).collect();
    let by: BTreeMap<&R::Id, &R> = rows.iter().map(|r| (r.id(), *r)).collect();
    loop {
        let mut changed = false;
        for d in rows.iter() {
            let Some(ad) = out.get(d.id()).cloned() else { continue };
            for n in d.names() {
                let Some(r) = by.get(n) else { continue };
                let Some(a) = out.get(n) else { continue };
                let Some(add) = carried(*r, a, *d, &ad, roster, person) else { continue };
                if let Some(Placed::Placed(_, a)) = out.get_mut(n) {
                    if a.join(&add) {
                        changed = true;
                    }
                }
            }
        }
        if !changed {
            return out;
        }
    }
}
