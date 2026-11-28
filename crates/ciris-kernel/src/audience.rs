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
//!   a member removed later is owed nothing further; one admitted later is owed the older rows too, sealed by keys
//!   it lacks: see below). Commons: everyone. Addressed: the keys it names.
//! * **Copy** ([`audiences`], [`carried`]: the Constitution's proposal c). Carriage is of rows: a room row is
//!   carried by a concluded room row of its room to that row's audience on the room's current roster; nothing
//!   reaches a key off the roster; a self or addressed row is carried only by a concluded row of its own signer or
//!   that signer's person; the carrier's signer is already in the row's audience; a key grant is never carried,
//!   and is served per its placement (the content's scope), opened only by the key it names.
//!   A refused or undecided row carries nothing and receives nothing.
//! * **Served is not readable.** `history_on_join` changes no audience: a later joiner is served the older room
//!   rows, sealed by keys it lacks (the tier gives the current epoch's key only, CC 4.4.3.16). `full` acts only on
//!   a kept stream, through its producer's own key grants within the catch-up bound: the caller's ([`history_of`]).

use alloc::collections::{BTreeMap, BTreeSet};
use alloc::vec::Vec;

#[rustfmt::skip]
#[path = "audience_table.rs"]
mod table;
pub use table::{
    DUTY_SEAT_FAMILIES, FAMILIES, FAMILY_MODEL_SHA256, FOLLOWS, PERMISSION_FAMILIES, SCOPES, SEAT_FAMILIES,
};

/// How a row of a `follows` family is placed against the row it follows ([`FOLLOWS`], [`follow`]).
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Follows {
    /// At the followed row's own scope: its placement and audience (the content a custody row holds, the stream a
    /// head heads).
    Same,
    /// At that scope or narrower: an audience within the followed row's (a duty on the permission it attaches to).
    Narrower,
}

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

/// A person reading, through the seat model's ONE persons function (key-person): `voice`, the person a key counts as
/// ([`crate::seat::Persons::voice`]; `None` for a key of two persons, an agent's key, a key that revoked itself, an
/// evicted genesis key), and `keys`, a person's live keys ([`crate::seat::person_keys`]). No separate notion of a
/// person is kept here.
pub struct PersonsOf<'a, K> {
    /// The person a key counts as.
    pub voice: &'a dyn Fn(&K) -> Option<K>,
    /// A person's live keys.
    pub keys: &'a dyn Fn(&K) -> BTreeSet<K>,
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
    /// A row of a `follows` family names no row it follows.
    FollowsNotNamed,
    /// The row it follows is not held.
    FollowsNotHeld,
    /// The row it follows is refused or undecided.
    FollowsUnplaced,
    /// It cites several rows, so names no one row it follows.
    FollowsAmbiguous,
    /// It is not at the scope of the row it follows.
    FollowsMismatch,
    /// Its audience is wider than the row it follows.
    FollowsWider,
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
            Refusal::FollowsNotNamed => "follows_not_named",
            Refusal::FollowsNotHeld => "follows_not_held",
            Refusal::FollowsUnplaced => "follows_unplaced",
            Refusal::FollowsAmbiguous => "follows_ambiguous",
            Refusal::FollowsMismatch => "follows_mismatch",
            Refusal::FollowsWider => "follows_wider",
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
    /// On a custody report: the content row its `evidence_refs` names (the blob's address, resolved by the caller).
    fn evidence(&self) -> Option<&Self::Id> {
        None
    }
    /// On a stream head: the stream it heads (its `sub`, resolved by the caller to the stream's row).
    fn stream(&self) -> Option<&Self::Id> {
        None
    }
    /// On a delegation: its `delegation_purpose`.
    fn purpose(&self) -> Option<&str> {
        None
    }
    /// The rows it cites in `refs.also.cites`.
    fn cites(&self) -> &[Self::Id] {
        &[]
    }
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
    person: &PersonsOf<'_, R::Key>,
    joins: &Joins<'_, R::Id, R::Key>,
) -> Placed<R::Key> {
    place_in(FAMILIES, r, roster, person, joins)
}

/// [`place`] over another table of family patterns: the pinned [`FAMILIES`] in use, a synthetic table in a test
/// (the pinned table has no undecided family since d5d42bf, so the Undecided path is tested this way).
pub fn place_in<R: AudienceRow>(
    table: &'static [(&'static str, FamilyPlacement)],
    r: &R,
    roster: &dyn Fn(&R::Id) -> BTreeSet<R::Key>,
    person: &PersonsOf<'_, R::Key>,
    joins: &Joins<'_, R::Id, R::Key>,
) -> Placed<R::Key> {
    let &(fam, cell) = match family_in(table, r.family()) {
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
        Placement::SelfCollective => {
            if let Some(p) = (person.voice)(r.signer()) {
                keys.extend((person.keys)(&p));
            }
        }
        Placement::Addressed => {}
        Placement::TargetedFamily | Placement::TargetedRoom => {
            let Some(room) = r.room() else { return Placed::Refused(Refusal::NoRoom) };
            // WHO IS OWED: the current roster (CC 5.2 as ruled: a row is owed to the roster as it stands when the
            // node replicates; a member removed since is owed nothing further)
            let members = roster(room);
            // WHAT IT MAY NAME: the members at the row's own head, so placement never changes with a later removal
            // or admission; the keys a seat offer or unseat seats or removes are within its audience, ahead of it
            let within = (joins.at_head)(room, r.id());
            // a seat of a DUTY over the room (the moderator's acceptance) seats a member at the row's own head, never
            // an outsider: only such keys pass
            let duty = DUTY_SEAT_FAMILIES.contains(&fam);
            let seats: Vec<&R::Key> = seats_of(r).iter().filter(|k| !duty || within.contains(*k)).collect();
            if !r.named().iter().all(|k| within.contains(k) || seats.contains(&k)) {
                return Placed::Refused(Refusal::NamedOutsideAudience);
            }
            keys.extend(seats.into_iter().cloned());
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
fn same_person<K: Ord + Clone>(person: &PersonsOf<'_, K>, k: &K, of: &K) -> bool {
    k == of || (person.voice)(of).is_some_and(|p| (person.voice)(k) == Some(p))
}

/// The keys a concluded placed row `d` naming `r` carries `r` to, or `None`: the copy rule of CC 5.2 as the
/// Constitution read it (proposal c), the one place it is stated. Carriage is of ROWS; served is not readable.
/// * c.1: a room row is carried by a concluded room row of the same room, to that row's audience;
/// * c.2: only to keys on the room's current roster (an offered key that never accepted gets the offer alone, a
///   removed key its removal alone);
/// * c.3: a self or an addressed row is carried only by a concluded row of its own signer or that signer's person,
///   into that row's audience (bounded by c.2 where it is a room row). `person` is [`PersonsOf`] over the seat
///   model's one persons function ([`crate::seat::Persons::voice`], [`crate::seat::person_keys`]), so an evicted
///   or revoked key, a key of two persons or an agent's key is no key of the person and carries nothing.
///
/// The carrier's signer is already in `r`'s audience (CC 5.2's gate). A key grant is never carried (CC 3.3.2): it is
/// served per its placement, the content's scope (so it is purged, taken down and replicated with the content), and
/// only the key it names can open it; in a room the members see that a grant exists and to which key, never the
/// key.
pub fn carried<R: AudienceRow>(
    r: &R,
    a: &Placed<R::Key>,
    d: &R,
    ad: &Placed<R::Key>,
    roster: &dyn Fn(&R::Id) -> BTreeSet<R::Key>,
    person: &PersonsOf<'_, R::Key>,
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

// audience a is within audience b
// every PERSON audience a holds is one audience b holds (the ruling: "narrower" is over persons): a key of a is within
// b where b holds it or another key of its person
fn within<K: Ord>(a: &Audience<K>, b: &Audience<K>, person: &PersonsOf<'_, K>) -> bool {
    match (a, b) {
        (_, Audience::Everyone) => true,
        (Audience::Everyone, Audience::Keys(_)) => false,
        (Audience::Keys(a), Audience::Keys(b)) => {
            let held: BTreeSet<K> = b.iter().filter_map(|x| (person.voice)(x)).collect();
            a.iter().all(|k| b.contains(k) || (person.voice)(k).is_some_and(|p| held.contains(&p)))
        }
    }
}

/// A row of a `follows` family placed at the scope of the row it follows: its own answer where `rule` holds against
/// the followed row's answer, else the refusal. `named` is whether the row names the row it follows, or why not
/// ([`followed_of`]). `Narrower` is over persons (the Constitution's ruling): every person
/// of its audience is a person of the followed row's, by `person`, the person contract. `named` is whether the row names a row it follows; `followed` that
/// row's answer, `None` where it is not held.
pub fn follow<K: Ord + Clone>(
    named: Result<(), Refusal>,
    own: Placed<K>,
    followed: Option<&Placed<K>>,
    rule: Follows,
    person: &PersonsOf<'_, K>,
) -> Placed<K> {
    let Placed::Placed(p, a) = &own else { return own };
    if let Err(why) = named {
        return Placed::Refused(why);
    }
    let Some(f) = followed else { return Placed::Refused(Refusal::FollowsNotHeld) };
    let Placed::Placed(fp, fa) = f else { return Placed::Refused(Refusal::FollowsUnplaced) };
    match rule {
        Follows::Same if p == fp && a == fa => own,
        Follows::Same => Placed::Refused(Refusal::FollowsMismatch),
        Follows::Narrower if within(a, fa, person) => own,
        Follows::Narrower => Placed::Refused(Refusal::FollowsWider),
    }
}

/// The reference by which a row of a `follows` family names the row it follows (the ruling G34).
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum FollowsRef {
    /// A custody report's `evidence_refs`: the content it holds ([`AudienceRow::evidence`]).
    Evidence,
    /// A stream head's `sub`: the stream it heads ([`AudienceRow::stream`]).
    Stream,
    /// `refs.also.cites` ([`AudienceRow::cites`]): exactly one cited row of the given families (a duty's permission,
    /// [`PERMISSION_FAMILIES`]); cited rows of other families are not read.
    Cites(&'static [&'static str]),
    /// `refs.also.cites`: exactly one cited owner binding ([`is_owner_binding`], by row type and purpose): an
    /// ownership row, the binding's mirror.
    OwnerBinding,
}

/// Each `follows` family's reference: the role the family already uses for the row it follows, where one exists,
/// else `refs.also.cites` (the ruling G34).
pub const FOLLOWS_REF: &[(&str, FollowsRef)] = &[
    ("custody:{kind}", FollowsRef::Evidence),
    ("stream:head", FollowsRef::Stream),
    ("ownership:{relation}:{target_kind}:{version}", FollowsRef::OwnerBinding),
    ("duty:{kind}", FollowsRef::Cites(PERMISSION_FAMILIES)),
];

/// An owner binding (CC 3.2), by [`crate::seat::owner_binding`], the one recogniser beside `Seats` (row type and
/// purpose, not family). It is placed by its own scope and follows nothing.
pub fn is_owner_binding<R: AudienceRow>(x: &R) -> bool {
    family_of(x.family()).is_some_and(|f| crate::seat::owner_binding(f.0, x.purpose()))
}

/// The row a row of a `follows` family follows, read by its family's reference ([`FOLLOWS_REF`]); the refusal where
/// it names none. Under `cites`, the held cited rows (`by`) of the right family: exactly one; none gives
/// [`Refusal::FollowsNotNamed`], several of that family [`Refusal::FollowsAmbiguous`].
pub fn followed_of<'r, R: AudienceRow>(r: &'r R, by: &BTreeMap<&R::Id, &R>) -> Result<&'r R::Id, Refusal> {
    let role = family_of(r.family()).and_then(|f| FOLLOWS_REF.iter().find(|(p, _)| *p == f.0)).map(|(_, x)| *x);
    match role {
        Some(FollowsRef::Evidence) => r.evidence().ok_or(Refusal::FollowsNotNamed),
        Some(FollowsRef::Stream) => r.stream().ok_or(Refusal::FollowsNotNamed),
        Some(rf @ (FollowsRef::Cites(_) | FollowsRef::OwnerBinding)) => {
            let right = |c: &&R::Id| {
                by.get(*c).is_some_and(|x| match rf {
                    FollowsRef::Cites(of) => family_of(x.family()).is_some_and(|f| of.contains(&f.0)),
                    _ => is_owner_binding(*x),
                })
            };
            let mut hits = r.cites().iter().filter(right);
            match (hits.next(), hits.next()) {
                (Some(one), None) => Ok(one),
                (None, _) => Err(Refusal::FollowsNotNamed),
                (Some(_), Some(_)) => Err(Refusal::FollowsAmbiguous),
            }
        }
        None => Err(Refusal::FollowsNotNamed),
    }
}

// the follows rule of the row's family, where it has one
fn follows_rule(family: &str) -> Option<Follows> {
    let f = family_of(family)?;
    FOLLOWS.iter().find(|(p, _)| *p == f.0).map(|(_, r)| *r)
}

/// Every row's answer, the follows rule ([`follow`]) and then the copy rule applied ([`carried`]): a placed row's audience grows by the keys every
/// concluded placed row naming it carries it to; the least fixed point, which only grows. The consequence: a
/// joiner may hold the room's whole named reply chain, as ciphertext it cannot read.
pub fn audiences<R: AudienceRow>(
    rows: &[&R],
    roster: &dyn Fn(&R::Id) -> BTreeSet<R::Key>,
    person: &PersonsOf<'_, R::Key>,
    joins: &Joins<'_, R::Id, R::Key>,
) -> BTreeMap<R::Id, Placed<R::Key>> {
    let mut out: BTreeMap<R::Id, Placed<R::Key>> =
        rows.iter().map(|r| (r.id().clone(), place(*r, roster, person, joins))).collect();
    let by: BTreeMap<&R::Id, &R> = rows.iter().map(|r| (r.id(), *r)).collect();
    // follows, along chains of followers: each against its followed row's answer once that one is settled; a cycle
    // of followers places none
    let mut waiting: Vec<(&R, Follows)> = rows
        .iter()
        .filter(|r| matches!(out.get(r.id()), Some(Placed::Placed(..))))
        .filter_map(|r| follows_rule(r.family()).map(|f| (*r, f)))
        .collect();
    while !waiting.is_empty() {
        let pending: BTreeSet<&R::Id> = waiting.iter().map(|(r, _)| r.id()).collect();
        let (ready, rest): (Vec<_>, Vec<_>) =
            waiting.into_iter().partition(|(r, _)| followed_of(*r, &by).map_or(true, |f| !pending.contains(f)));
        if ready.is_empty() {
            for (r, _) in &rest {
                out.insert(r.id().clone(), Placed::Refused(Refusal::FollowsUnplaced));
            }
            break;
        }
        for (r, rule) in ready {
            let own = out.get(r.id()).cloned().expect("placed");
            let target = followed_of(r, &by);
            let followed = target.ok().and_then(|f| out.get(f)).cloned();
            out.insert(r.id().clone(), follow(target.map(|_| ()), own, followed.as_ref(), rule, person));
        }
        waiting = rest;
    }
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
