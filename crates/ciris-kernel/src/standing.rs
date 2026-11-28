//! One row that needs two standings: a root grant and an owner binding (CC 3.1.2.1; `models/tla/CONFERRAL_END.md`
//! section J, its reading `acc`).
//!
//! A node that is its owner's by an owner binding and holds a duty by a root grant signs an act. The act names
//! the bundle version in force (its head) and the owner's acceptance of the grant it stands on. The acceptance
//! names no binding (N7): it stands while its author owns the grant's subject, so the binding it stands on is
//! derived, its signer's owner binding live in its past ([`owner_of`]). A re-binding names the binding before it
//! and ends it, and the new owner's acts need a new acceptance.
//!
//! [`answers`] follows those names and judges each act twice with [`conferral::answers`]: once under the grant
//! (the bundle versions as heads, the grant's end as the end) and once under the binding its acceptance stands on
//! (the binding as the only head, a re-binding of it as the end). It joins the two bit by bit: the act
//! **counts** for the binding's owner when it counts under both, and is **in force** when it is in force under
//! both. An act that names a binding row itself, or the bundle alone, stands on no acceptance and counts for
//! nobody. Where the node has two live owners (a binding to another owner held, neither re-binding the other,
//! and that one not re-bound in the act's past) it has none, and the act counts for nobody.
//!
//! The past is the caller's ([`Past`]), read as the rows name it. An act that names the first owner's
//! acceptance and reaches a re-binding through another row it names (its signer's previous act) has that end in
//! its past, and does not count under the binding the re-binding ended (E4).
//!
//! The reference is `chain_answers` in `models/causal_kernel/check_conferral_two.py`; `tests/conferral_two.rs`
//! replays its case table (`tests/fixtures/conferral_two.json`) through this module. Cases only: no run of
//! every state compares the crate with the reference, and no proof covers it.
//!
//! A deputy's act ([`StandingRow::via`]) stands on its deputy edge, the node's own act that names the owner's
//! acceptance; it names none itself. It is judged in both records with its edges, by conferral's own deputy
//! walk (E6: depth, sub-delegation, upstream): it counts for the binding's owner where it and its edges count
//! under the grant and under the binding, and is in force likewise, so a re-binding reaches it as it reaches
//! the edge, and under the binding only its owner receipts. Two owners is none for the edge and every act under it.
//!
//! An act standing directly on an acceptance (a root edge, the node's own act) counts only where its signer is
//! the grant's grantee ([`Role::Grantee`]): a deputy that names the acceptance itself stands on nothing
//! ([`Nobody::NotTheGrantee`]). The binding names no node, so the grant's grantee is the node read here.
//!
//! Not read here: a receipt by a co-holder of the binding (only the binding's owner receipts under it). The
//! caller presents the rows of one node under one grant.

use crate::conferral::{self, ConferralRow, Judged, Past, Refused, Role, Who};
use alloc::collections::{BTreeMap, BTreeSet};
use alloc::vec::Vec;
use core::fmt::Debug;

/// What a row is to the grant and the bindings.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Kind {
    /// A version of the bundle the grant is counted under: a head of the grant.
    Bundle,
    /// An owner binding. One that re-binds the node names the binding before it ([`StandingRow::on`]) and ends
    /// it.
    Binding,
    /// An owner's acceptance of the grant, naming the binding it is made under ([`StandingRow::on`]).
    Acceptance,
    /// An act under the grant, naming its bundle version ([`StandingRow::head`]) and the acceptance it stands
    /// on ([`StandingRow::on`]).
    Act,
    /// The end of the grant, naming its bundle version ([`StandingRow::head`]).
    GrantEnd,
    /// A clean acknowledgement of one act ([`StandingRow::on`]): the conferrer's side keeps it under the grant,
    /// the binding's owner keeps it under the binding.
    Receipt,
    /// A removal of a key.
    Removal,
    /// Any other row. It is not read, and it may still carry the past.
    Other,
}

/// A row as this module reads it. The caller has verified and decoded it.
pub trait StandingRow {
    /// The row's digest.
    type Id: Ord + Clone + Debug;
    /// A key id.
    type Key: Ord + Clone + Debug;
    /// The row's own digest.
    fn id(&self) -> &Self::Id;
    /// What the row is.
    fn kind(&self) -> Kind;
    /// The key that signed it.
    fn signer(&self) -> &Self::Key;
    /// The bundle version an act or the grant's end names. `None` on any other row.
    fn head(&self) -> Option<&Self::Id>;
    /// The one row this row is made on: for an act, the row it stands on (an acceptance, if it is to count);
    /// for a binding, the binding it re-binds; for a receipt, the act. An acceptance names no binding (N7): the
    /// binding it stands on is derived ([`owner_of`]), and its `on` is not read. Default `None`.
    fn on(&self) -> Option<&Self::Id> {
        None
    }
    /// On a binding: the owner it binds the node to.
    fn owner(&self) -> Option<&Self::Key> {
        None
    }
    /// The key a removal removes.
    fn target(&self) -> Option<&Self::Key> {
        None
    }
    /// On the grant's end by a count: it lifts the receipts of single co-holders and of the receipter.
    fn lifts(&self) -> bool {
        false
    }
    /// On a deputy's act: the deputy edge it stands on, itself an act (the node's own, which names the owner's
    /// acceptance, or a deputy's onward edge). A deputy's act names no acceptance: it stands where the root of
    /// its edges stands. Default `None`: the node's own act.
    fn via(&self) -> Option<&Self::Id> {
        None
    }
    /// On a deputy edge: the deputy may deputize onward ([`conferral::ConferralRow::sub_delegation`]).
    fn sub_delegation(&self) -> bool {
        false
    }
}

/// Why an act stands on no acceptance and counts for nobody.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Nobody {
    /// It names the bundle alone.
    NoAcceptance,
    /// It names a binding row itself.
    NamesBinding,
    /// The row it names is neither an acceptance nor a binding.
    NotAnAcceptance,
    /// The acceptance it names names no binding. No longer given (N7: the binding is derived); kept for the
    /// fixture's names.
    AcceptanceNamesNoBinding,
    /// The acceptance it names is by no owner of the node at it: its signer owns no binding live in its past (a
    /// former owner, whose binding a re-binding ended, or never an owner).
    NotTheOwnersAcceptance,
    /// An act standing directly on an acceptance (a root edge) signed by a key that is not the grant's grantee
    /// ([`Role::Grantee`] under the grant's `role`): a deputy that names the acceptance itself.
    NotTheGrantee,
    /// The deputy edge it names (`via`) is a held row that is no act.
    EdgeNotAnAct,
    /// Its chain of deputy edges is longer than the deputy depth allows, by more than one hop.
    TooDeep,
    /// The node has two live owners, so none (CC 3.2: "two owners is none"; `seat::Seats::one`): a binding
    /// of it to another owner is held, neither re-binds the other (one in the other's past without re-binding it
    /// is still live), and no re-binding of that one is in the act's past.
    TwoOwners,
}

impl Nobody {
    /// The reason's name in `models/causal_kernel/check_conferral_two.py` and the fixture.
    pub fn as_str(self) -> &'static str {
        match self {
            Nobody::NoAcceptance => "no_acceptance",
            Nobody::NamesBinding => "names_binding",
            Nobody::NotAnAcceptance => "not_an_acceptance",
            Nobody::AcceptanceNamesNoBinding => "acceptance_names_no_binding",
            Nobody::NotTheOwnersAcceptance => "not_the_owners_acceptance",
            Nobody::NotTheGrantee => "not_the_grantee",
            Nobody::EdgeNotAnAct => "edge_not_an_act",
            Nobody::TooDeep => "too_deep",
            Nobody::TwoOwners => "two_owners",
        }
    }
}

/// An act that stands on an owner's acceptance: what the two records conclude.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Stands<I, K> {
    /// The binding its acceptance names: the stint it is judged under.
    pub binding: I,
    /// That binding's owner. The bits below are for this owner; for any other owner both are false.
    pub owner: K,
    /// It counts under the grant and under the binding.
    pub counted: bool,
    /// It is in force under the grant and under the binding.
    pub in_force: bool,
    /// What the grant's record concludes, with the rule that decides.
    pub grant: Judged,
    /// What the binding's record concludes, with the rule that decides.
    pub under: Judged,
}

/// The answer for one act.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Answer<I, K> {
    /// It stands on an owner's acceptance, and the rows decide it.
    Stands(Stands<I, K>),
    /// It stands on no acceptance: it counts for nobody and is in force for nobody.
    Nobody(Nobody),
    /// The rows cannot tell until this row is held: a row the act or its acceptance names, or one the
    /// caller's past needs.
    Undecided(I),
}

/// The answer for every act, by the act's id.
pub type Answers<I, K> = BTreeMap<I, Answer<I, K>>;

/// What [`answers`] returns: the answers, or why none is given.
pub type Outcome<I, K> = Result<Answers<I, K>, Refused<I>>;

// A row as one record reads it.
struct As<'a, R: StandingRow> {
    row: &'a R,
    kind: conferral::Kind,
    head: Option<&'a R::Id>,
}

impl<R: StandingRow> ConferralRow for As<'_, R> {
    type Id = R::Id;
    type Key = R::Key;
    fn id(&self) -> &R::Id {
        self.row.id()
    }
    fn kind(&self) -> conferral::Kind {
        self.kind
    }
    fn signer(&self) -> &R::Key {
        self.row.signer()
    }
    fn head(&self) -> Option<&R::Id> {
        self.head
    }
    fn of(&self) -> Option<&R::Id> {
        (self.kind == conferral::Kind::Receipt).then(|| self.row.on()).flatten()
    }
    fn target(&self) -> Option<&R::Key> {
        self.row.target()
    }
    fn lifts(&self) -> bool {
        self.row.kind() == Kind::GrantEnd && self.row.lifts()
    }
    // a deputy's act and its edges, read by conferral's own deputy walk (E6) in both records
    fn via(&self) -> Option<&R::Id> {
        (self.kind == conferral::Kind::Act).then(|| self.row.via()).flatten()
    }
    fn sub_delegation(&self) -> bool {
        self.kind == conferral::Kind::Act && self.row.sub_delegation()
    }
}

/// The owner binding acceptance `a` stands on, derived (N7: an owner's acceptance of the grant names no binding; it
/// stands while its author owns the grant's subject): a binding owned by `a`'s signer in `a`'s past, with no
/// re-binding of it in `a`'s past; of several, the newest (none of the others has it in its past), the least id
/// on a tie. `None`: its signer owns nothing there (a former owner, its binding ended; or never an owner). `Err`:
/// the row `past` needs to tell. The reference is `owner_of` in `models/causal_kernel/check_conferral_two.py`.
pub fn owner_of<'a, R: StandingRow, P: Past<R::Id>>(a: &R, rows: &[&'a R], past: &P) -> Result<Option<&'a R>, R::Id> {
    let mut live: Vec<&'a R> = Vec::new();
    for &b in rows.iter().filter(|b| b.kind() == Kind::Binding && b.owner() == Some(a.signer())) {
        if !past.in_past(b.id(), a.id())? {
            continue;
        }
        let mut ended = false;
        for e in rows.iter().filter(|e| e.kind() == Kind::Binding && e.on() == Some(b.id())) {
            if past.in_past(e.id(), a.id())? {
                ended = true;
                break;
            }
        }
        if !ended {
            live.push(b);
        }
    }
    let mut top: Vec<&'a R> = Vec::new();
    for &b in &live {
        let mut older = false;
        for &c in live.iter().filter(|c| c.id() != b.id()) {
            if past.in_past(b.id(), c.id())? {
                older = true;
                break;
            }
        }
        if !older {
            top.push(b);
        }
    }
    Ok(top.into_iter().min_by(|x, y| x.id().cmp(y.id())))
}

// where an act stands: its root edge (itself, for the node's own act) and the binding that edge's acceptance
// stands on (derived, [`owner_of`]), why it stands on none, or the row to fetch. `index`: the rows by id; `cap`:
// the deputy depth
fn stands_on<'a, R: StandingRow, P: Past<R::Id>>(
    x: &'a R,
    index: &BTreeMap<&R::Id, &'a R>,
    rows: &[&'a R],
    past: &P,
    cap: usize,
    grant: &conferral::Standing<'_, R::Id, R::Key>,
) -> Result<Result<(&'a R, &'a R), Nobody>, R::Id> {
    let held = |i: &R::Id| index.get(i).copied().ok_or_else(|| i.clone());
    let x = match root_edge(x, index, cap)? {
        Ok(x) => x,
        Err(why) => return Ok(Err(why)),
    };
    let Some(on) = x.on() else { return Ok(Err(Nobody::NoAcceptance)) };
    let a = held(on)?;
    match a.kind() {
        Kind::Acceptance => {}
        Kind::Binding => return Ok(Err(Nobody::NamesBinding)),
        _ => return Ok(Err(Nobody::NotAnAcceptance)),
    }
    // N7: the binding it stands on is its signer's owner binding live at it, not a row it names
    let Some(b) = owner_of(a, rows, past)? else { return Ok(Err(Nobody::NotTheOwnersAcceptance)) };
    // a root edge (an act standing directly on an acceptance) is the grantee's own act: any other key's
    // root-shaped act stands on nothing
    if (grant.role)(x.signer()) != Role::Grantee {
        return Ok(Err(Nobody::NotTheGrantee));
    }
    Ok(Ok((x, b)))
}

// the node's own act a deputy's act stands on: its edges (`via`) followed to one that has none, at most
// `cap + 1` hops (further down conferral's E6.depth counts nothing anyway); why it stands on none (an edge that
// is a held row and no act, a cycle of edges, a chain past the cap); or the edge to fetch
fn root_edge<'a, R: StandingRow>(
    x: &'a R,
    index: &BTreeMap<&R::Id, &'a R>,
    cap: usize,
) -> Result<Result<&'a R, Nobody>, R::Id> {
    let mut at = x;
    let mut seen: BTreeSet<&R::Id> = core::iter::once(x.id()).collect();
    let mut hops = 0usize;
    while let Some(v) = at.via() {
        let Some(e) = index.get(v).copied() else { return Err(v.clone()) };
        if e.kind() != Kind::Act {
            return Ok(Err(Nobody::EdgeNotAnAct));
        }
        if seen.contains(v) {
            return Ok(Err(Nobody::NoAcceptance));
        }
        hops += 1;
        if hops > cap + 1 {
            return Ok(Err(Nobody::TooDeep));
        }
        seen.insert(v);
        at = e;
    }
    Ok(Ok(at))
}

// `c` is `b`, or re-binds `b` through a chain of re-bindings (`on`), among the rows held
fn rebinds<R: StandingRow>(c: &R, b: &R, rows: &[&R]) -> bool {
    let mut at = Some(c);
    for _ in 0..=rows.len() {
        let Some(r) = at else { return false };
        if r.id() == b.id() {
            return true;
        }
        at = r.on().and_then(|o| rows.iter().copied().find(|q| q.id() == o && q.kind() == Kind::Binding));
    }
    false
}

// two owners is none: a binding of the node to another owner than `b`'s is held, neither re-binding the other
// (one in the other's past without re-binding it is still live), and no re-binding of it is in act `x`'s past.
// Several live bindings to the same owner are one owner.
fn two_owners<R: StandingRow, P: Past<R::Id>>(x: &R, b: &R, rows: &[&R], past: &P) -> Result<bool, R::Id> {
    for c in rows.iter().filter(|c| c.kind() == Kind::Binding && c.id() != b.id() && c.owner() != b.owner()) {
        if rebinds(*c, b, rows) || rebinds(b, *c, rows) {
            continue; // one ends the other: a stint, not a rival
        }
        let mut ended = false;
        for e in rows.iter().filter(|e| e.kind() == Kind::Binding && e.on() == Some(c.id())) {
            if past.in_past(e.id(), x.id())? {
                ended = true;
                break;
            }
        }
        if !ended {
            return Ok(true);
        }
    }
    Ok(false)
}

/// For every act among `rows`: the binding it stands under and that binding's owner, whether it counts and is
/// in force for that owner, and the rule that decides under each record; or why it counts for nobody; or the
/// row that must be held to tell.
///
/// `rows` are the rows the caller holds that bear on one node's duty under one root grant: the bundle
/// versions, the node's bindings and re-bindings, the owners' acceptances of the grant, the node's acts, the
/// grant's end if one is held, receipts and key removals. `grant` is the grant's standing as
/// [`conferral::answers`] takes it: who each key is to the grant, and the bundle versions the reader has
/// acknowledged. Under a binding the binding's owner is the conferrer and nobody else receipts.
///
/// `past` is asked only about ids of these rows. Two ends of the grant, or two re-bindings of one binding, are
/// refused as [`conferral::answers`] refuses two ends.
pub fn answers<R: StandingRow, P: Past<R::Id>>(
    rows: &[&R],
    grant: &conferral::Standing<'_, R::Id, R::Key>,
    past: &P,
) -> Outcome<R::Id, R::Key> {
    let acts: Vec<&R> = rows.iter().copied().filter(|r| r.kind() == Kind::Act).collect();
    let mut out = BTreeMap::new();
    // the binding each act stands under
    let mut at: Vec<(&R, &R)> = Vec::new();
    // the rows by id, so that each act's walk to its root edge is at most `deputy_depth + 1` lookups
    let mut index: BTreeMap<&R::Id, &R> = BTreeMap::new();
    for &r in rows {
        index.entry(r.id()).or_insert(r);
    }
    for &x in &acts {
        match stands_on(x, &index, rows, past, grant.deputy_depth, grant) {
            // two owners is none for the edge, and so for every act under it
            Ok(Ok((e, b))) => match two_owners(e, b, rows, past) {
                Ok(false) => at.push((x, b)),
                Ok(true) => drop(out.insert(x.id().clone(), Answer::Nobody(Nobody::TwoOwners))),
                Err(i) => drop(out.insert(x.id().clone(), Answer::Undecided(i))),
            },
            Ok(Err(why)) => drop(out.insert(x.id().clone(), Answer::Nobody(why))),
            Err(i) => drop(out.insert(x.id().clone(), Answer::Undecided(i))),
        }
    }
    // the grant's record: the bundle versions are its heads
    let as_grant: Vec<As<'_, R>> = rows
        .iter()
        .map(|&row| {
            let (kind, head) = match row.kind() {
                Kind::Bundle => (conferral::Kind::Head, None),
                Kind::Act => (conferral::Kind::Act, row.head()),
                Kind::GrantEnd => (conferral::Kind::End, row.head()),
                Kind::Receipt => (conferral::Kind::Receipt, None),
                Kind::Removal => (conferral::Kind::Removal, None),
                Kind::Binding | Kind::Acceptance | Kind::Other => (conferral::Kind::Other, None),
            };
            As { row, kind, head }
        })
        .collect();
    let under_grant = conferral::answers(&as_grant.iter().collect::<Vec<_>>(), grant, past)?;
    // each binding's record: the binding is its only head, a re-binding of it its end, its owner the conferrer
    let bindings: BTreeSet<&R::Id> = at.iter().map(|(_, b)| b.id()).collect();
    for bid in bindings {
        let mine: BTreeSet<&R::Id> = at.iter().filter(|(_, b)| b.id() == bid).map(|(x, _)| x.id()).collect();
        let owner = at.iter().find(|(_, b)| b.id() == bid).and_then(|(_, b)| b.owner());
        let as_stint: Vec<As<'_, R>> = rows
            .iter()
            .map(|&row| {
                let (kind, head) = match row.kind() {
                    Kind::Binding if row.id() == bid => (conferral::Kind::Head, None),
                    Kind::Binding if row.on() == Some(bid) => (conferral::Kind::End, Some(bid)),
                    Kind::Act if mine.contains(row.id()) => (conferral::Kind::Act, Some(bid)),
                    Kind::Receipt => (conferral::Kind::Receipt, None),
                    Kind::Removal => (conferral::Kind::Removal, None),
                    _ => (conferral::Kind::Other, None),
                };
                As { row, kind, head }
            })
            .collect();
        let role = |k: &R::Key| if Some(k) == owner { Role::Conferrer } else { Role::Other };
        let stint = conferral::Standing {
            role: &role,
            other_standing: false,
            who: Who::ConferrerOnly,
            reader_acks: &[],
            deputy_depth: grant.deputy_depth,
        };
        let under_binding = conferral::answers(&as_stint.iter().collect::<Vec<_>>(), &stint, past)?;
        for (x, b) in at.iter().filter(|(_, b)| b.id() == bid) {
            let a = match (under_grant.get(x.id()), under_binding.get(x.id()), owner) {
                (Some(conferral::Answer::Judged(g)), Some(conferral::Answer::Judged(u)), Some(o)) => {
                    Answer::Stands(Stands {
                        binding: b.id().clone(),
                        owner: o.clone(),
                        counted: g.counted && u.counted,
                        in_force: g.in_force && u.in_force,
                        grant: *g,
                        under: *u,
                    })
                }
                (Some(conferral::Answer::Undecided(i)), _, _) | (_, Some(conferral::Answer::Undecided(i)), _) => {
                    Answer::Undecided(i.clone())
                }
                // every act is in both records, and a binding an act stands under has an owner
                _ => continue,
            };
            out.insert(x.id().clone(), a);
        }
    }
    Ok(out)
}
