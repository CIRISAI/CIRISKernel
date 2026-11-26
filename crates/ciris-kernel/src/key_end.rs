//! A key's own end (KERNEL.md section 5, "Two notions of time"; CC 2.7.5): `key_end.py`.
//!
//! A key record states its own end (`valid_until`), read from the record alone. A key is live while one of
//! its own records covers now and it has not revoked itself; no row of another key enters that reading
//! (`KeyEnd.lean`). A renewal is a further record of the same key that names its earlier record, and counts
//! whenever it was signed. A rotation names the old key's record and carries the old key's signature. A row
//! of an ended key that no live row has in its past lapses and counts in no answer. A revocation never lapses.
//!
//! The only instants compared are one key's own. Nothing is ranked by an instant or a digest.

use crate::graph::Bits;
use crate::layers::{Concluded, Past};
use crate::Row;
use alloc::collections::{BTreeMap, BTreeSet};
use alloc::vec::Vec;

/// Whether a record must, must not, or may state an end. The caller reads it from the record alone: CC
/// 2.4.1.1 requires one for a `node` or `agent` key outside a private room, and forbids one for a person's
/// own key and an accord holder's.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum EndRule {
    /// The record must state an end.
    Required,
    /// The record must not state one.
    Forbidden,
    /// It may.
    Optional,
}

/// The fields of a key's records and statements.
pub trait KeyEndRow: Row {
    /// An instant (persist: `Micros`).
    type T: Ord + Copy + core::ops::Sub<Output = Self::T>;
    /// For a key record: the key, its from, its until, the old key (rotation), the old key's instant, the
    /// signatures carried and whether an end is required.
    fn record(&self) -> Option<Record<'_, Self::Key, Self::T>> {
        None
    }
    /// For a statement (an attestation or an edge): its instant and the record it names as its cover.
    fn statement(&self) -> Option<(Self::T, &Self::Id)> {
        None
    }
    /// For a revocation: the key and its `revoked_after`.
    fn revocation(&self) -> Option<(&Self::Key, Self::T)> {
        None
    }
}

/// A key record, as [`KeyEndRow::record`] gives it.
#[derive(Clone, Copy, Debug)]
pub struct Record<'r, K, T> {
    /// The key.
    pub key: &'r K,
    /// Its own signed instant.
    pub from: T,
    /// Its stated end, if any.
    pub until: Option<T>,
    /// For a rotation, the old key.
    pub succ_of: Option<&'r K>,
    /// For a rotation, the old key's own instant on it.
    pub at_old: Option<T>,
    /// The keys whose signatures it carries.
    pub sigs: &'r [K],
    /// Whether it must, may or must not state an end.
    pub end: EndRule,
}

/// The door for a key record, read from the row alone: the end it must or must not state, `from < until` (an
/// equal end covers nothing, CC 2.6.2),
/// `until - from <= ceil`, and a rotation carrying the old key's signature beside the new key's.
pub fn well_formed<R: KeyEndRow>(r: &R, ceil: R::T) -> bool {
    let Some(x) = r.record() else { return true };
    match x.until {
        None => x.end != EndRule::Required,
        Some(u) => {
            if x.end == EndRule::Forbidden || x.from >= u || u - x.from > ceil {
                return false;
            }
            if let Some(old) = x.succ_of {
                if !x.sigs.contains(old) {
                    return false;
                }
            }
            x.sigs.contains(x.key)
        }
    }
}

/// The conclusion rule: a first record concludes; a renewal concludes when it names its own key's record;
/// a rotation when the old key's instant on it lies inside the old record it names; a statement when its
/// signer's instant lies inside the record it names. It never reads now.
pub fn conclude_rule<R: KeyEndRow>(p: &Past<'_, '_, R>) -> bool {
    let r = p.row();
    let prev: Vec<&R> = r.names().iter().filter_map(|n| p.get(n)).filter(|q| q.record().is_some()).collect();
    if let Some(x) = r.record() {
        match x.succ_of {
            None => {
                if r.names().is_empty() {
                    return true;
                }
                prev.first().is_some_and(|q| q.record().unwrap().key == x.key)
            }
            Some(old) => prev.first().is_some_and(|q| {
                let o = q.record().unwrap();
                o.key == old && x.at_old.is_some_and(|a| crate::covers_at(Some(o.from), o.until, &a))
            }),
        }
    } else if let Some((at, cover)) = r.statement() {
        match p.get(cover).and_then(|c| c.record()) {
            Some(c) => c.key == r.signer() && crate::covers_at(Some(c.from), c.until, &at),
            None => false,
        }
    } else {
        true
    }
}

fn records<'c, R: KeyEndRow>(c: &'c Concluded<'_, R>, k: &R::Key) -> impl Iterator<Item = Record<'c, R::Key, R::T>> + 'c
where
    R::Key: 'c,
{
    let k = k.clone();
    c.cs().iter().filter_map(move |&i| c.g.row(i).record()).filter(move |x| *x.key == k)
}

fn revoked_from<R: KeyEndRow>(c: &Concluded<'_, R>, k: &R::Key) -> Option<R::T> {
    c.cs()
        .iter()
        .filter_map(|&i| {
            let r = c.g.row(i);
            r.revocation().filter(|(rk, _)| *rk == k && r.signer() == k).map(|(_, a)| a)
        })
        .min()
}

/// Whether key `k` is live at `now`: one of its own concluded records covers now, and it has not revoked
/// itself by now.
pub fn live<R: KeyEndRow>(c: &Concluded<'_, R>, k: &R::Key, now: R::T) -> bool {
    if revoked_from(c, k).is_some_and(|a| now >= a) {
        return false;
    }
    records(c, k).any(|x| crate::covers_at(Some(x.from), x.until, &now))
}

/// Whether key `k` has ended at `now`: no record of it states an end after now, or it revoked itself by now.
/// A record not yet begun is not ended.
pub fn ended<R: KeyEndRow>(c: &Concluded<'_, R>, k: &R::Key, now: R::T) -> bool {
    if revoked_from(c, k).is_some_and(|a| now >= a) {
        return true;
    }
    records(c, k).all(|x| x.until.is_some_and(|u| u <= now))
}

/// The rows that have not lapsed at `now`: every concluded row of a key that has not ended, every
/// revocation, and everything in their past.
pub fn retained<R: KeyEndRow>(c: &Concluded<'_, R>, now: R::T) -> BTreeSet<usize> {
    // `ended` for every key at once: its earliest self-revocation, and whether every record of it ends by now
    let mut rev: BTreeMap<&R::Key, R::T> = BTreeMap::new();
    let mut open: BTreeSet<&R::Key> = BTreeSet::new();
    for &i in c.cs() {
        let r = c.g.row(i);
        if let Some((rk, a)) = r.revocation() {
            if rk == r.signer() {
                rev.entry(rk).and_modify(|x| *x = core::cmp::min(*x, a)).or_insert(a);
            }
        }
        if let Some(x) = r.record() {
            if x.until.is_none_or(|u| u > now) {
                open.insert(x.key);
            }
        }
    }
    let ended = |k: &R::Key| rev.get(k).is_some_and(|a| now >= *a) || !open.contains(k);
    // the seeds and everything in their past, by one walk down what rows name
    let mut b = Bits::new(c.g.len());
    let mut todo: Vec<usize> = Vec::new();
    for &i in c.cs() {
        let r = c.g.row(i);
        let seed = r.revocation().is_some() || !ended(r.record().map(|x| x.key).unwrap_or(r.signer()));
        if seed && !b.has(i) {
            b.set(i);
            todo.push(i);
            while let Some(x) = todo.pop() {
                for &p in c.g.named(x) {
                    if !b.has(p) {
                        b.set(p);
                        todo.push(p);
                    }
                }
            }
        }
    }
    b.iter().collect()
}

/// [`live`] **at a held row** (0.3): at the instant row `at` states ([`crate::Dated`]), never a clock. `None`
/// when `at` is not held or states no instant. The `now` form is a node-local reading (CC 2.7.9): for serving
/// and display, not for a verdict.
pub fn live_at<R: KeyEndRow + crate::Dated<Instant = <R as KeyEndRow>::T>>(
    c: &Concluded<'_, R>,
    k: &R::Key,
    at: &R::Id,
) -> Option<bool> {
    Some(live(c, k, c.g.instant_of(at)?))
}

/// [`ended`] at the instant row `at` states; `None` when `at` is not held or states no instant.
pub fn ended_at<R: KeyEndRow + crate::Dated<Instant = <R as KeyEndRow>::T>>(
    c: &Concluded<'_, R>,
    k: &R::Key,
    at: &R::Id,
) -> Option<bool> {
    Some(ended(c, k, c.g.instant_of(at)?))
}

/// [`retained`] at the instant row `at` states; `None` when `at` is not held or states no instant.
pub fn retained_at<R: KeyEndRow + crate::Dated<Instant = <R as KeyEndRow>::T>>(
    c: &Concluded<'_, R>,
    at: &R::Id,
) -> Option<BTreeSet<usize>> {
    Some(retained(c, c.g.instant_of(at)?))
}

/// The successor of key `k`: the one key the frontier of its concluded rotations (among `ret`, when given)
/// names. Two keys spoken leave it empty.
pub fn successor<R: KeyEndRow>(c: &Concluded<'_, R>, k: &R::Key, ret: Option<&BTreeSet<usize>>) -> Option<R::Key> {
    let rots: Vec<usize> = c
        .cs()
        .iter()
        .copied()
        .filter(|&i| c.g.row(i).record().is_some_and(|x| x.succ_of == Some(k)))
        .filter(|i| ret.is_none_or(|s| s.contains(i)))
        .collect();
    let keys: BTreeSet<R::Key> =
        c.g.frontier(&rots).into_iter().map(|i| c.g.row(i).record().unwrap().key.clone()).collect();
    if keys.len() == 1 {
        keys.into_iter().next()
    } else {
        None
    }
}
