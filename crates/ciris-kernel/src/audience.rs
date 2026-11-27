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
//!   [`Refusal::FamilyUnknown`].
//! * **Placement.** The cohort scope a row states is its placement ([`SCOPES`]): `self` is self_collective,
//!   `family` targeted_family, `community` and `affiliations` targeted_room, `species`, `biosphere` and
//!   `federation` commons, and `addressed` a row for the keys it names. A family on the default takes any of the
//!   first four, chosen for each row; a family the CC table pins takes only the placements its cell names
//!   ([`Refusal::PlacementNotAllowed`]). A family whose cell is not table data is [`Placed::Undecided`], naming
//!   the family: no default is taken for it.
//! * **Audience.** Every audience holds the signer and the keys the row names. Self_collective: the signer's own
//!   keys. Targeted: the room's roster; a row there may name only keys on the roster
//!   ([`Refusal::NamedOutsideAudience`]) and names its room ([`Refusal::NoRoom`]). The keys a seat offer or unseat
//!   over the room seats or removes ([`AudienceRow::seats`]) are always within its audience, ahead of that rule: a
//!   pending admission names its joiner, a removal its removed key. The roster is the roster as it stands (CC 5.2:
//!   a member removed later is owed nothing further), less the members admitted after the row unless its
//!   `history_on_join` is full: the row's own ([`AudienceRow::history_on_join`]), else the room record's
//!   ([`Joins::history`]), else from_join. Commons: everyone. Addressed:
//!   the keys it names.
//! * **Copy** ([`audiences`]). A row's audience includes that of every concluded row naming it from the same room
//!   or signed by the same key, whose signer is already in its audience: the least fixed point. A refused or
//!   undecided row carries nothing and receives nothing.

use alloc::collections::{BTreeMap, BTreeSet};
use alloc::vec::Vec;

#[rustfmt::skip]
#[path = "audience_table.rs"]
mod table;
pub use table::{FAMILIES, FAMILY_MODEL_SHA256, SCOPES};

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
    /// The row that admitted the key to the room; `None` for a founding member.
    pub joined: &'a dyn Fn(&I, &K) -> Option<I>,
    /// The `history_on_join` the room's record states, where it states one.
    pub history: &'a dyn Fn(&I) -> Option<History>,
    /// Row `a` is in row `b`'s past.
    pub past: &'a dyn Fn(&I, &I) -> bool,
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
    /// On a seat offer or unseat over the room: the keys it seats or removes (its `to`), among [`Self::named`].
    fn seats(&self) -> &[Self::Key] {
        &[]
    }
    /// The row concludes.
    fn concluded(&self) -> bool;
    /// The row's own `history_on_join` (set per stream by its producer, CC 2.1), where it states one.
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

/// The family pattern that decides a family name, with its cell: the most literal segments among those that
/// match.
pub fn family_of(name: &str) -> Option<&'static (&'static str, FamilyPlacement)> {
    let mut best: Option<(usize, &'static (&'static str, FamilyPlacement))> = None;
    for f in FAMILIES {
        if let Some(k) = matches(f.0, name) {
            if best.is_none_or(|(b, _)| k > b) {
                best = Some((k, f));
            }
        }
    }
    best.map(|(_, f)| f)
}

/// The placement and audience of one row, before the copy rule. `roster` is the room's roster as
/// [`crate::seat::Seats::roster`] reads it over the rows held; `person` the keys of the signer's person.
pub fn place<R: AudienceRow>(
    r: &R,
    roster: &dyn Fn(&R::Id) -> BTreeSet<R::Key>,
    person: &dyn Fn(&R::Key) -> BTreeSet<R::Key>,
    joins: &Joins<'_, R::Id, R::Key>,
) -> Placed<R::Key> {
    let Some(&(fam, cell)) = family_of(r.family()) else { return Placed::Refused(Refusal::FamilyUnknown) };
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
            // the current roster, not the members at the row's own head (CC 5.2 as ruled: a row is owed to the
            // roster as it stands when the node replicates; a member removed since is owed nothing further)
            let members = roster(room);
            // the keys a seat offer or unseat seats or removes are within its audience, ahead of named_within
            if !r.named().iter().all(|k| members.contains(k) || r.seats().contains(k)) {
                return Placed::Refused(Refusal::NamedOutsideAudience);
            }
            // a member admitted after the row receives it only where the history is full: the row's own, else the
            // room record's, else from_join
            let history = r.history_on_join().or_else(|| (joins.history)(room)).unwrap_or(History::FromJoin);
            keys.extend(members.into_iter().filter(|k| {
                history == History::Full || (joins.joined)(room, k).is_none_or(|adm| !(joins.past)(r.id(), &adm))
            }));
        }
    }
    Placed::Placed(placement, Audience::Keys(keys))
}

/// Every row's answer, the copy rule applied: a placed row's audience grows by that of every concluded placed row
/// naming it from the same room, or signed by the same key, whose signer is already in its audience (CC 5.2).
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
        for d in rows.iter().filter(|d| d.concluded()) {
            let Some(Placed::Placed(_, ad)) = out.get(d.id()).cloned() else { continue };
            for n in d.names() {
                let Some(r) = by.get(n) else { continue };
                let same_room = d.room().is_some() && d.room() == r.room();
                if !same_room && d.signer() != r.signer() {
                    continue; // a row leaves its room only by its own signer's act
                }
                if let Some(Placed::Placed(_, a)) = out.get_mut(n) {
                    if a.holds(d.signer()) && a.join(&ad) {
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
