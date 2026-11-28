//! **The consent peer set** (CC 3.3.7, CC 2.7.5, CC 5.2, CC 6.1.5): which `consent:replication` grant is in
//! force, which peers a principal's grants name, and whether a node may send a peer a row of a class, each read
//! at a held row. `models/causal_kernel/consent.py`.
//!
//! A `consent:replication:v1` grant is one signer's **directed** row to one named peer (`subject_key_ids = [P]`),
//! naming the classes it moves (`attestation_prefixes`). It moves those classes and nothing else (CC 5.2). It is
//! seat-shaped, an offer by one key to another that stands until withdrawn, with a class check on top.
//!
//! **Concluded** ([`conclude_rule`]). A grant concludes when it is well formed: one peer, and its classes non-empty
//! entries sorted ascending with no duplicate (CC 3.3.7, "sorted ascending + deduplicated"); placed at federation
//! scope, only where both parties have announced themselves in its past. A withdrawal (a `withdraws` or a
//! `recants`) concludes when the row it names is a concluded grant and its signer is the grant's signer, the peer
//! it names, or the signer's owner read at the withdrawal (the Constitution, reading CC 3.3.7 whole). Any other
//! key's withdrawal concludes nothing. Other rows are the caller's rule.
//!
//! **Read at a row** (`at`; `None` reads every held row).
//! - *The past*: `at` and the rows in its causal past. A grant that is not there is not read.
//! - *Voice*: a grant's signature counts against each of its signer's own revocations (r86, a key end is a cut)
//!   where the grant is in the revocation's past, or states an instant before the revocation's `revoked_after`
//!   and does not have the revocation in its past. Any other grant of a revoked key is no grant.
//! - *The fold* ([`winners`]): causal first, for each (signer, peer) the grants with a voice that no other of them
//!   has in its past, then the latest `asserted_at`, then the lowest id: a grant with an earlier one in its past is
//!   later whatever either states. An earlier grant is replaced (a narrowing is a `supersedes`). A withdrawal or the term of the
//!   latest grant revives no earlier one (CC 3.3.7: on revoke the node "MUST cease replicating the named prefixes
//!   to P").
//! - *Withdrawn*: the end is a cut (CC 2.4.1.1, ruled 2026-11-21). A held withdrawal ends the grant at every row
//!   that is not in the withdrawal's past, so one in `at`'s past and one concurrent with `at` both end it there.
//! - *Term*: `valid_until`, read at the caller's instant `now`, half-open ([`crate::covers_at`]). A grant with a
//!   term and no instant given is not in force.
//!
//! **The node's principals.** The node itself (G is the granting node, CC 3.3.7) and its one owner by the owner
//! binding. The owner is the caller's: [`crate::seat::Seats::one`] of scope `owner` over the node's key, read over
//! `at`'s past (two live owners is none, CC 3.2). A grant by any other key moves none of the node's rows.
//!
//! Edge's replication set is the operator-addressed peers that are in the [`peer_set`] of a principal of the
//! node ([`replication_set`]), and [`may_send`] gates each row.
//!
//! The reference is `models/causal_kernel/consent.py`; `tests/consent.rs` replays the case table of
//! `check_consent.py` (`tests/fixtures/consent.json`). Cases only: no proof covers it.

use crate::layers::{Concluded, Past};
use crate::Row;
use alloc::collections::{BTreeMap, BTreeSet};

/// What a row is to the consent peer set.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Kind {
    /// A `consent:replication` grant: [`ConsentRow::peer`], [`ConsentRow::classes`], its instant and term.
    Grant,
    /// A `withdraws` or `recants` of the grant [`ConsentRow::withdraws`] names.
    Withdrawal,
    /// A key's own revocation ([`ConsentRow::revocation`]).
    Revocation,
    /// A node's announcement of itself (CC 5.4.6), signed by the node.
    Announcement,
    /// Any other row: read only as a place in the causal order.
    Other,
}

/// A row as this module reads it. The caller has verified and decoded it.
pub trait ConsentRow: Row {
    /// An entry of `attestation_prefixes`.
    type Class: AsRef<str>;
    /// An instant (persist: `Micros`).
    type T: Ord + Copy;
    /// What the row is.
    fn kind(&self) -> Kind;
    /// On a grant: the one peer it names (`subject_key_ids = [P]`).
    fn peer(&self) -> Option<&Self::Key> {
        None
    }
    /// On a grant: the classes it moves, as signed.
    fn classes(&self) -> &[Self::Class] {
        &[]
    }
    /// On a grant: its `asserted_at`.
    fn at(&self) -> Option<Self::T> {
        None
    }
    /// On a grant: its `valid_until`, the term.
    fn until(&self) -> Option<Self::T> {
        None
    }
    /// On a grant: it is placed at `cohort_scope: federation` (default). A grant held between the two nodes
    /// returns false.
    fn federation(&self) -> bool {
        true
    }
    /// On a withdrawal: the grant it retracts.
    fn withdraws(&self) -> Option<&Self::Id> {
        None
    }
    /// On a revocation: the key it revokes and its `revoked_after`. Only the key's own is read.
    fn revocation(&self) -> Option<(&Self::Key, Self::T)> {
        None
    }
}

/// Whether a grant is well formed: one peer, and its classes non-empty, sorted ascending, with no duplicate.
pub fn well_formed<R: ConsentRow>(r: &R) -> bool {
    let cs = r.classes();
    r.peer().is_some()
        && !cs.is_empty()
        && cs.iter().all(|c| !c.as_ref().is_empty())
        && cs.windows(2).all(|w| w[0].as_ref() < w[1].as_ref())
}

/// The conclusion rule for the consent rows. A grant concludes when [`well_formed`], and, placed at federation
/// scope, only where its signer and its peer both have an announcement in its past (CC 3.3.7: "A grant that an
/// unannounced node signs or is named in is never placed at federation"). A withdrawal concludes when it names a
/// concluded grant and its signer is one of three keys: the grant's signer; the peer it names (CC 2.4.1.1 rule 2,
/// "stop sending to me"); or the signer's one owner read over the withdrawal's own past, which `owner_of(signer,
/// past)` gives (the caller's `Seats::one("owner", signer)` over that past; `None` with none or two). Every other
/// row concludes here; the caller's own rule decides it.
pub fn conclude_rule<R: ConsentRow>(
    p: &Past<'_, '_, R>,
    owner_of: impl Fn(&R::Key, &Past<'_, '_, R>) -> Option<R::Key>,
) -> bool {
    let r = p.row();
    match r.kind() {
        Kind::Grant => {
            well_formed(r)
                && (!r.federation()
                    || r.peer().is_some_and(|peer| {
                        let announced = |k: &R::Key| p.rows().any(|q| q.kind() == Kind::Announcement && q.signer() == k);
                        announced(r.signer()) && announced(peer)
                    }))
        }
        Kind::Withdrawal => r.withdraws().and_then(|g| p.get(g)).is_some_and(|g| {
            g.kind() == Kind::Grant
                && (g.signer() == r.signer()
                    || g.peer() == Some(r.signer())
                    || owner_of(g.signer(), p).as_ref() == Some(r.signer()))
        }),
        Kind::Revocation | Kind::Announcement | Kind::Other => true,
    }
}

/// Whether the classes cover `class`: an entry ending in `:` is a namespace prefix and covers every class it
/// begins (the trailing colon is significant); any other entry is a corpus class name and covers itself only.
pub fn covers<C: AsRef<str>>(classes: &[C], class: &str) -> bool {
    classes.iter().any(|e| {
        let e = e.as_ref();
        if e.ends_with(":") {
            class.starts_with(e)
        } else {
            class == e
        }
    })
}

// `a` is `b` or in its past
fn upto<R: Row>(c: &Concluded<'_, R>, a: usize, b: usize) -> bool {
    a == b || c.g.in_past(a, b)
}

// the rows read at `at`: `at` and its past; every row with none. `None` where `at` is not held
fn reading<R: Row>(c: &Concluded<'_, R>, at: Option<&R::Id>) -> Option<Option<usize>> {
    match at {
        None => Some(None),
        Some(id) => c.g.idx(id).map(Some),
    }
}

/// The grant's signature counts against each of its signer's own revocations.
pub fn voice<R: ConsentRow>(c: &Concluded<'_, R>, g: usize) -> bool {
    let gr = c.g.row(g);
    c.cs().iter().all(|&v| {
        let vr = c.g.row(v);
        let Some((k, ra)) = vr.revocation() else { return true };
        if k != gr.signer() || vr.signer() != gr.signer() || upto(c, g, v) {
            return true;
        }
        !c.g.in_past(v, g) && gr.at().is_some_and(|t| t < ra)
    })
}

/// Whether a held withdrawal ends grant `g` at `at` (`None`: at every held row): one that `at` is not in the
/// past of.
pub fn withdrawn<R: ConsentRow>(c: &Concluded<'_, R>, g: usize, at: Option<usize>) -> bool {
    let id = c.g.row(g).id();
    c.cs().iter().any(|&w| {
        let wr = c.g.row(w);
        wr.kind() == Kind::Withdrawal
            && wr.withdraws() == Some(id)
            && match at {
                None => true,
                Some(a) => !(a != w && c.g.in_past(a, w)),
            }
    })
}

/// Whether grant `g` is inside its term at the caller's instant `now`.
pub fn in_term<R: ConsentRow>(c: &Concluded<'_, R>, g: usize, now: Option<R::T>) -> bool {
    match (c.g.row(g).until(), now) {
        (None, _) => true,
        (Some(_), None) => false,
        (Some(u), Some(t)) => crate::covers_at(None, Some(u), &t),
    }
}

/// The default fold read at `at`, causal first ([`crate::derived::fold_default`]'s order): for each (signer,
/// peer), of the concluded grants in the past with a voice, those no other of them has in its past; of those, the
/// latest `asserted_at`, then the lowest id. `None` where `at` is not held.
pub fn winners<R: ConsentRow>(c: &Concluded<'_, R>, at: Option<&R::Id>) -> Option<BTreeMap<(R::Key, R::Key), usize>> {
    let at = reading(c, at)?;
    let mut groups: BTreeMap<(R::Key, R::Key), alloc::vec::Vec<usize>> = BTreeMap::new();
    for &i in c.cs() {
        let r = c.g.row(i);
        let Some(peer) = r.peer().filter(|_| r.kind() == Kind::Grant) else { continue };
        if at.is_some_and(|a| !upto(c, i, a)) || !voice(c, i) {
            continue;
        }
        groups.entry((r.signer().clone(), peer.clone())).or_default().push(i);
    }
    let pick = |g: &[usize]| {
        g.iter()
            .copied()
            .filter(|&i| !g.iter().any(|&j| j != i && c.g.in_past(i, j)))
            .max_by(|&a, &b| {
                let (x, y) = (c.g.row(a), c.g.row(b));
                (x.at(), core::cmp::Reverse(x.id())).cmp(&(y.at(), core::cmp::Reverse(y.id())))
            })
    };
    Some(groups.into_iter().filter_map(|(k, g)| pick(&g).map(|i| (k, i))).collect())
}

/// Whether grant `g` (an id) is in force at `at` (`None`: over every held row), at the caller's instant `now`.
pub fn in_force<R: ConsentRow>(c: &Concluded<'_, R>, g: &R::Id, at: Option<&R::Id>, now: Option<R::T>) -> bool {
    let (Some(gi), Some(ai), Some(w)) = (c.g.idx(g), reading(c, at), winners(c, at)) else { return false };
    let r = c.g.row(gi);
    let (Some(peer), true) = (r.peer(), c.concluded(gi) && r.kind() == Kind::Grant) else { return false };
    w.get(&(r.signer().clone(), peer.clone())) == Some(&gi) && !withdrawn(c, gi, ai) && in_term(c, gi, now)
}

/// The principal's grants in force at `at`, by peer.
pub fn grants_in_force<R: ConsentRow>(
    c: &Concluded<'_, R>,
    principal: &R::Key,
    at: Option<&R::Id>,
    now: Option<R::T>,
) -> BTreeMap<R::Key, usize> {
    let (Some(ai), Some(w)) = (reading(c, at), winners(c, at)) else { return BTreeMap::new() };
    w.into_iter()
        .filter(|((s, _), g)| s == principal && !withdrawn(c, *g, ai) && in_term(c, *g, now))
        .map(|((_, p), g)| (p, g))
        .collect()
}

/// The consent peer set of `principal` at `at`: the peers its grants in force there name.
pub fn peer_set<R: ConsentRow>(
    c: &Concluded<'_, R>,
    principal: &R::Key,
    at: Option<&R::Id>,
    now: Option<R::T>,
) -> BTreeSet<R::Key> {
    grants_in_force(c, principal, at, now).into_keys().collect()
}

/// A bilateral peering at `at`: `a`'s grant to `b` and `b`'s grant to `a`, both in force (CC 3.3.7: each
/// direction is its own grant).
pub fn bilateral<R: ConsentRow>(c: &Concluded<'_, R>, a: &R::Key, b: &R::Key, at: Option<&R::Id>, now: Option<R::T>) -> bool {
    peer_set(c, a, at, now).contains(b) && peer_set(c, b, at, now).contains(a)
}

/// The node's principals: the node itself and `owner`, its one owner at `at` by the owner binding (the caller's
/// `Seats::one("owner", node)` over `at`'s past; `None` with none or two).
pub fn principals<K: Ord + Clone>(node: &K, owner: Option<&K>) -> BTreeSet<K> {
    core::iter::once(node).chain(owner).cloned().collect()
}

/// The grant under which `node` may send `peer` a row of `class` at `at`: one in force from a principal of the
/// node (itself, or `owner`) to that peer whose classes [`covers`] the class. `None`: the row does not move.
pub fn may_send<'a, R: ConsentRow>(
    c: &Concluded<'a, R>,
    node: &R::Key,
    owner: Option<&R::Key>,
    peer: &R::Key,
    class: &str,
    at: Option<&R::Id>,
    now: Option<R::T>,
) -> Option<&'a R::Id> {
    principals(node, owner).iter().find_map(|p| {
        grants_in_force(c, p, at, now)
            .get(peer)
            .map(|&g| c.g.row(g))
            .filter(|g| covers(g.classes(), class))
            .map(|g| g.id())
    })
}

/// Edge's fan-out: the operator-addressed peers that are in the consent peer set of a principal of the node.
pub fn replication_set<R: ConsentRow>(
    c: &Concluded<'_, R>,
    node: &R::Key,
    owner: Option<&R::Key>,
    addressed: &BTreeSet<R::Key>,
    at: Option<&R::Id>,
    now: Option<R::T>,
) -> BTreeSet<R::Key> {
    let ps: BTreeSet<R::Key> = principals(node, owner).iter().flat_map(|p| peer_set(c, p, at, now)).collect();
    addressed.intersection(&ps).cloned().collect()
}
