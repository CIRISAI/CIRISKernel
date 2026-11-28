//! **The consent peer set** (CC 3.3.7, CC 2.7.5, CC 5.2, CC 6.1.5): which `consent:replication` grant is in
//! force, which peers a principal's grants name, and whether a node may send a peer a row of a class, each read
//! at a held row. `models/causal_kernel/consent.py`.
//!
//! A `consent:replication:v1` grant is one signer's **directed** row to one named peer (`subject_key_ids = [P]`),
//! naming the classes it moves (`attestation_prefixes`). It moves those classes and nothing else (CC 5.2). It is
//! seat-shaped, an offer by one key to another that stands until withdrawn, with a class check on top. A grant
//! **permits and never obliges**: a node may always send less, with no row.
//!
//! **Concluded** ([`conclude_rule`]). A grant concludes when it is well formed: one peer, and its classes non-empty
//! entries sorted ascending with no duplicate (CC 3.3.7, "sorted ascending + deduplicated"). A withdrawal (a
//! `withdraws` or a `recants`) concludes when the row it names is a concluded grant; who may withdraw is read below.
//! Other rows are the caller's rule.
//!
//! **What consent reads from the rest of the kernel** ([`Reading`], REQUIRED, one reading each, the caller's):
//! the key view ([`crate::key_end::KeyReading`]), the person map ([`crate::seat::Persons::voice`]) and the one owner
//! reading ([`crate::seat::Seats::owner`]), each over the rows the call names. There is no default that counts every
//! voice.
//!
//! **Read at a row** (`at`; `None` reads every held row).
//! - *The past*: `at` and the rows in its causal past. A grant that is not there is not read. An `at` that is not
//!   held reads nothing (no grant in force, an empty set, `None`).
//! - *Voice*: the grant's signer's signature counts by the key view (the end rule every count reads: a key end is
//!   a cut). A stated instant never helps a grant concurrent with an end.
//! - *Placement*: a grant at federation scope is a grant only where its signer and its peer each have an
//!   announcement in its past whose signature counts by the key view (CC 3.3.7: "A grant that an unannounced node
//!   signs or is named in is never placed at federation"). A grant held between the two (`federation()` false) reads
//!   no announcement: holding it between the two nodes and serving it to no other is the replication layer's
//!   (**Edge's duty**).
//! - *The fold* ([`winners`]): [`crate::derived::fold_default`], the one default fold, per (signer, peer): causal
//!   first, a row beating every row something in its own past beat, then the latest `asserted_at`, then the lowest
//!   id. A withdrawal or the term of the latest grant revives no earlier one (CC 3.3.7: on revoke the node "MUST
//!   cease replicating the named prefixes to P").
//! - *Who withdraws* ([`may_withdraw`]), ONE RULE (the Constitution, A3), over the withdrawal's past: its signer is
//!   the grant's signer as a person (the same key, or a live key of the same person); or a named party (CC 2.4.1.1
//!   rule 2: the peer, or a node the grant is for, one whose owner is the grant's signer's person); or its signer's
//!   person owns the grant's signer. The arms that stand on an ownership, or on a key being the person's, are cut
//!   by that standing's end, by the end rule: a held row that ends it concurrent with the withdrawal voids it (r97
//!   F1, F3; r103 PE1, PR1: an evicted or revoked device, the key's own ends read through the key view).
//! - *Withdrawn*: the end is a cut (CC 2.4.1.1, ruled 2026-11-21). A withdrawal that counts ends the grant at every
//!   row that is not in the withdrawal's past, so one in `at`'s past and one concurrent with `at` both end it there.
//! - *Term*: `valid_until`, read at the caller's instant `now`, half-open ([`crate::covers_at`]). A grant with a
//!   term and no instant given is not in force. **Caller duty**: `now` is the caller's, as charter's edge terms
//!   read it; nodes agree on an answer with a term only where they read it at the same `now`.
//!
//! **The node's principals.** The node itself (G is the granting node, CC 3.3.7) and its one owner,
//! [`Reading::owner`] at `at` (A7, as ruled: the owner is read at the reading row, so a grant an owner made before
//! it owned the node moves the node's rows once the binding is in `at`'s past). A grant by any other key moves none
//! of the node's rows.
//!
//! Edge's replication set is the operator-addressed peers that are in the [`peer_set`] of a principal of the
//! node ([`replication_set`]), and [`may_send`] gates each row.
//!
//! The residuals, stated: the signer's own concurrent regrants that name neither settle nothing, and the next
//! regrant naming both does (r103 FD1: the fold fails closed on the signer's own split); a person with one key,
//! whose key is stolen and then revoked, has no other device to withdraw a grant the thief made that a reader took
//! up; the peer, and a node the grant is for, still may.
//!
//! The reference is `models/causal_kernel/consent.py`; `tests/consent.rs` replays the case table of
//! `check_consent.py` (`tests/fixtures/consent.json`) twice: with the model's readings, and end to end over the
//! crate's own `KeyReading`, `Persons` and `Seats::owner`. Cases only: no proof covers it.

use crate::layers::{Concluded, Past};
use crate::Row;
use alloc::collections::{BTreeMap, BTreeSet};
use alloc::vec::Vec;

/// What a row is to the consent peer set.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Kind {
    /// A `consent:replication` grant: [`ConsentRow::peer`], [`ConsentRow::classes`], its instant and term.
    Grant,
    /// A `withdraws` or `recants` of the grant [`ConsentRow::withdraws`] names.
    Withdrawal,
    /// A node's announcement of itself (CC 5.4.6), signed by the node.
    Announcement,
    /// Any other row: read only as a place in the causal order (and by the caller's readings).
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
}

/// What consent reads from the rest of the kernel: one reading each, the caller's, over the rows it concluded in
/// one causal order with the key lane and the seat rows.
pub trait Reading<I, K> {
    /// The key view ([`crate::key_end::KeyView`], [`crate::key_end::KeyReading`] for the reading node): `key`'s
    /// signature on `row` counts by the end rule. A row the reading does not hold counts nothing.
    fn counts(&self, row: &I, key: &K) -> bool;
    /// The person `key` speaks for over the concluded rows in `row`'s past, with `row` itself where `inclusive`
    /// ([`crate::seat::Persons::voice`] over them): `None` for none (a key of two persons, a revoked key).
    fn person(&self, key: &K, row: &I, inclusive: bool) -> Option<K>;
    /// `node`'s one owner ([`crate::seat::Seats::owner`]) over the concluded rows in `row`'s past, with `row` itself
    /// where `inclusive`; over every held row where `row` is `None`. `None` with none or two.
    fn owner(&self, node: &K, row: Option<&I>, inclusive: bool) -> Option<K>;
}

/// The reading a call takes.
pub type Rd<'r, R> = &'r dyn Reading<<R as Row>::Id, <R as Row>::Key>;

/// Whether a grant is well formed: one peer, and its classes non-empty, sorted ascending, with no duplicate.
pub fn well_formed<R: ConsentRow>(r: &R) -> bool {
    let cs = r.classes();
    r.peer().is_some()
        && !cs.is_empty()
        && cs.iter().all(|c| !c.as_ref().is_empty())
        && cs.windows(2).all(|w| w[0].as_ref() < w[1].as_ref())
}

/// The conclusion rule for the consent rows: a grant concludes when [`well_formed`]; a withdrawal when it names a
/// concluded grant (who may withdraw is [`may_withdraw`]). Every other row concludes here; the caller's own rule
/// decides it.
pub fn conclude_rule<R: ConsentRow>(p: &Past<'_, '_, R>) -> bool {
    let r = p.row();
    match r.kind() {
        Kind::Grant => well_formed(r),
        Kind::Withdrawal => r.withdraws().and_then(|g| p.get(g)).is_some_and(|g| g.kind() == Kind::Grant),
        Kind::Announcement | Kind::Other => true,
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

/// Whether grant `g`'s signer's signature counts by the key view.
pub fn voice<R: ConsentRow>(c: &Concluded<'_, R>, g: usize, rd: Rd<'_, R>) -> bool {
    let r = c.g.row(g);
    rd.counts(r.id(), r.signer())
}

/// Whether grant `g` is placed: held between the two, or at federation scope with both parties announced in its
/// past, each announcement counting by the key view.
pub fn placed<R: ConsentRow>(c: &Concluded<'_, R>, g: usize, rd: Rd<'_, R>) -> bool {
    let r = c.g.row(g);
    if !r.federation() {
        return true;
    }
    let announced = |k: &R::Key| {
        c.cs().iter().any(|&a| {
            let q = c.g.row(a);
            q.kind() == Kind::Announcement && q.signer() == k && c.g.in_past(a, g) && rd.counts(q.id(), k)
        })
    };
    r.peer().is_some_and(|peer| announced(r.signer()) && announced(peer))
}

/// The held rows that end `owner`'s ownership of `node`: one where `owner` is the node's owner over its past and not
/// over its past with it (a withdrawal of the binding, a re-binding, a second binding that makes two owners).
pub fn ownership_ends<R: ConsentRow>(c: &Concluded<'_, R>, node: &R::Key, owner: &R::Key, rd: Rd<'_, R>) -> Vec<usize> {
    c.cs()
        .iter()
        .copied()
        .filter(|&e| {
            let id = c.g.row(e).id();
            c.g.row(e).kind() == Kind::Other
                && rd.owner(node, Some(id), false).as_ref() == Some(owner)
                && rd.owner(node, Some(id), true).as_ref() != Some(owner)
        })
        .collect()
}

/// The held rows that end `key` as `person`'s: one where `key` is that person's over its past and not over its past
/// with it (an eviction from the person's self roster that landed, a `registered` revocation of the key).
pub fn person_ends<R: ConsentRow>(c: &Concluded<'_, R>, key: &R::Key, person: &R::Key, rd: Rd<'_, R>) -> Vec<usize> {
    c.cs()
        .iter()
        .copied()
        .filter(|&e| {
            let id = c.g.row(e).id();
            !matches!(c.g.row(e).kind(), Kind::Grant | Kind::Withdrawal)
                && rd.person(key, id, false).as_ref() == Some(person)
                && rd.person(key, id, true).as_ref() != Some(person)
        })
        .collect()
}

// the end rule on a standing: withdrawal `w`, standing on it, is cut by any of its ends concurrent with it
fn uncut_by<R: ConsentRow>(c: &Concluded<'_, R>, w: usize, ends: Vec<usize>) -> bool {
    ends.into_iter().all(|e| c.g.in_past(e, w) || c.g.in_past(w, e))
}

// the end rule on an ownership: withdrawal `w`, standing on `owner` owning `node`, cut by its ends
fn uncut<R: ConsentRow>(c: &Concluded<'_, R>, w: usize, node: &R::Key, owner: &R::Key, rd: Rd<'_, R>) -> bool {
    uncut_by(c, w, ownership_ends(c, node, owner, rd))
}

// the end rule on a key as a person's (r103 PE1, PR1): withdrawal `w` by key `k`, standing on `k` being `person`'s, cut
// by an end of `k` as that person's concurrent with it, and read through the key view for the key's own ends
fn person_stands<R: ConsentRow>(c: &Concluded<'_, R>, w: usize, k: &R::Key, person: &R::Key, rd: Rd<'_, R>) -> bool {
    rd.counts(c.g.row(w).id(), k) && uncut_by(c, w, person_ends(c, k, person, rd))
}

/// Who may withdraw grant `g` by withdrawal `w`, ONE RULE (the Constitution, A3), over `w`'s past: the grant's
/// signer as a person; a named party (the peer, or a node the grant is for); or the owner of the grant's signer.
/// The two ownership arms are cut by the ownership's end, by the end rule.
pub fn may_withdraw<R: ConsentRow>(c: &Concluded<'_, R>, w: usize, g: usize, rd: Rd<'_, R>) -> bool {
    let (wr, gr) = (c.g.row(w), c.g.row(g));
    let k = wr.signer();
    if k == gr.signer() {
        return true;
    }
    let (pw, pg) = (rd.person(k, wr.id(), false), rd.person(gr.signer(), wr.id(), false));
    if let Some(p) = pw.as_ref().filter(|p| Some(*p) == pg.as_ref()) {
        if person_stands(c, w, k, p, rd) {
            return true;
        }
    }
    if gr.peer() == Some(k) {
        return true;
    }
    // a node the grant is for: `w`'s signer, owned by the grant's signer's person
    if let Some(o) = rd.owner(k, Some(wr.id()), false) {
        if pg.is_some() && rd.person(&o, wr.id(), false) == pg && uncut(c, w, k, &o, rd) {
            return true;
        }
    }
    // the owner over the grant's signer
    if let Some(o) = rd.owner(gr.signer(), Some(wr.id()), false) {
        if pw.is_some() && rd.person(&o, wr.id(), false) == pw && uncut(c, w, gr.signer(), &o, rd) {
            return true;
        }
    }
    false
}

/// Whether a held withdrawal that counts ends grant `g` at `at` (`None`: at every held row): one that `at` is not
/// in the past of.
pub fn withdrawn<R: ConsentRow>(c: &Concluded<'_, R>, g: usize, at: Option<usize>, rd: Rd<'_, R>) -> bool {
    let id = c.g.row(g).id();
    c.cs().iter().any(|&w| {
        let wr = c.g.row(w);
        wr.kind() == Kind::Withdrawal
            && wr.withdraws() == Some(id)
            && match at {
                None => true,
                Some(a) => !(a != w && c.g.in_past(a, w)),
            }
            && may_withdraw(c, w, g, rd)
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

/// The default fold read at `at` ([`crate::derived::fold_default`], the one fold), per (signer, peer), over the
/// concluded grants in the past with a voice that are placed. `None` where `at` is not held.
pub fn winners<R: ConsentRow>(
    c: &Concluded<'_, R>,
    at: Option<&R::Id>,
    rd: Rd<'_, R>,
) -> Option<BTreeMap<(R::Key, R::Key), usize>> {
    let at = reading(c, at)?;
    let rows: Vec<usize> = c
        .cs()
        .iter()
        .copied()
        .filter(|&i| {
            let r = c.g.row(i);
            r.kind() == Kind::Grant
                && r.peer().is_some()
                && at.is_none_or(|a| upto(c, i, a))
                && voice(c, i, rd)
                && placed(c, i, rd)
        })
        .collect();
    Some(crate::derived::fold_default(c, &rows, |r: &R| r.peer().cloned(), |_| 0, |r: &R| r.at()))
}

/// Whether grant `g` (an id) is in force at `at` (`None`: over every held row), at the caller's instant `now`.
pub fn in_force<R: ConsentRow>(
    c: &Concluded<'_, R>,
    g: &R::Id,
    at: Option<&R::Id>,
    now: Option<R::T>,
    rd: Rd<'_, R>,
) -> bool {
    let (Some(gi), Some(ai), Some(w)) = (c.g.idx(g), reading(c, at), winners(c, at, rd)) else { return false };
    let r = c.g.row(gi);
    let (Some(peer), true) = (r.peer(), c.concluded(gi) && r.kind() == Kind::Grant) else { return false };
    w.get(&(r.signer().clone(), peer.clone())) == Some(&gi) && !withdrawn(c, gi, ai, rd) && in_term(c, gi, now)
}

/// The principal's grants in force at `at`, by peer.
pub fn grants_in_force<R: ConsentRow>(
    c: &Concluded<'_, R>,
    principal: &R::Key,
    at: Option<&R::Id>,
    now: Option<R::T>,
    rd: Rd<'_, R>,
) -> BTreeMap<R::Key, usize> {
    let (Some(ai), Some(w)) = (reading(c, at), winners(c, at, rd)) else { return BTreeMap::new() };
    w.into_iter()
        .filter(|((s, _), g)| s == principal && !withdrawn(c, *g, ai, rd) && in_term(c, *g, now))
        .map(|((_, p), g)| (p, g))
        .collect()
}

/// The consent peer set of `principal` at `at`: the peers its grants in force there name.
pub fn peer_set<R: ConsentRow>(
    c: &Concluded<'_, R>,
    principal: &R::Key,
    at: Option<&R::Id>,
    now: Option<R::T>,
    rd: Rd<'_, R>,
) -> BTreeSet<R::Key> {
    grants_in_force(c, principal, at, now, rd).into_keys().collect()
}

/// A bilateral peering at `at`: `a`'s grant to `b` and `b`'s grant to `a`, both in force (CC 3.3.7: each
/// direction is its own grant).
pub fn bilateral<R: ConsentRow>(
    c: &Concluded<'_, R>,
    a: &R::Key,
    b: &R::Key,
    at: Option<&R::Id>,
    now: Option<R::T>,
    rd: Rd<'_, R>,
) -> bool {
    peer_set(c, a, at, now, rd).contains(b) && peer_set(c, b, at, now, rd).contains(a)
}

/// The node's principals at `at`: the node itself and its one owner there ([`Reading::owner`]).
pub fn principals<R: ConsentRow>(node: &R::Key, at: Option<&R::Id>, rd: Rd<'_, R>) -> BTreeSet<R::Key> {
    core::iter::once(node.clone()).chain(rd.owner(node, at, true)).collect()
}

/// The grant under which `node` may send `peer` a row of `class` at `at`: one in force from a principal of the
/// node to that peer whose classes [`covers`] the class. `None`: the row does not move.
pub fn may_send<'a, R: ConsentRow>(
    c: &Concluded<'a, R>,
    node: &R::Key,
    peer: &R::Key,
    class: &str,
    at: Option<&R::Id>,
    now: Option<R::T>,
    rd: Rd<'_, R>,
) -> Option<&'a R::Id> {
    reading(c, at)?;
    principals::<R>(node, at, rd).iter().find_map(|p| {
        grants_in_force(c, p, at, now, rd)
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
    addressed: &BTreeSet<R::Key>,
    at: Option<&R::Id>,
    now: Option<R::T>,
    rd: Rd<'_, R>,
) -> BTreeSet<R::Key> {
    let ps: BTreeSet<R::Key> = principals::<R>(node, at, rd).iter().flat_map(|p| peer_set(c, p, at, now, rd)).collect();
    addressed.intersection(&ps).cloned().collect()
}
