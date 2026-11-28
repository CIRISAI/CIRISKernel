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
    /// The row's own signed instant, where it states one: a statement's, or a seat row's (read by [`counts`] and
    /// [`counts_by`] against a self-revocation's `revoked_after`). A row stating no instant is judged by its past
    /// alone: the `revoked_after` reaches only rows that state one. **Default: a statement's instant only**, so a
    /// caller presenting seat rows to a [`KeyReading`] overrides this to give each row its signed instant (the
    /// model, `key_end.instant`, reads every row's `at`, as the crate's test adapter does); left at the default, a
    /// seat row is cut by a revocation only where it is not in the revocation's past.
    fn instant(&self) -> Option<Self::T> {
        self.statement().map(|s| s.0)
    }
    /// For a counted removal of one key (the act a person's self roster evicts a key by, or voids a rotation by):
    /// the key it removes. Only an id of [`KeyReading::roster`] (the roster's own concluded acts,
    /// [`crate::seat::self_roster_ends`]) is read. Default: none.
    fn roster_end(&self) -> Option<&Self::Key> {
        None
    }
    /// The keys whose signatures a row carries beside its signer's (a seat row's cosigners): with the signer, the
    /// keys whose own line the row is on (a reader's own rows, [`counts_for`]). Default: none.
    fn cosigned_by(&self) -> &[Self::Key] {
        &[]
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

/// Whether concluded row `i` counts, by THE END RULE every count reads: a statement of key `k` counts only where it
/// is in the causal past of each of `k`'s own ends (its self-revocations, where also its own instant is before the
/// `revoked_after` `k` stated; and each rotation naming `k`'s record: a rotated holder speaks under its new key).
/// With no such end, a concluded statement counts: its instant inside the record it names is the holder's word,
/// bounded below by its own past (the licence term's residual and caller duty). Whether a live row cites it is
/// never read: a count reads no anchor (only content may be anchored by others' rows). A row that is no statement
/// counts where it concluded.
pub fn counts<R: KeyEndRow>(c: &Concluded<'_, R>, i: usize) -> bool {
    if !c.all().get(i).copied().unwrap_or(false) {
        return false;
    }
    let r = c.g.row(i);
    if r.statement().is_none() {
        return true;
    }
    counts_for(c, i, r.signer(), None, &BTreeSet::new(), &BTreeSet::new())
}

/// THE END RULE for key `k`'s signature on concluded row `i` (a statement, or a seat row `k` signed or cosigned, held
/// in one causal order with `k`'s key lane), read with no reader's line: [`counts_for`] with none.
pub fn counts_by<R: KeyEndRow>(c: &Concluded<'_, R>, i: usize, k: &R::Key) -> bool {
    counts_for(c, i, k, None, &BTreeSet::new(), &BTreeSet::new())
}

/// Whether rotation `rot` (a concluded record rotating a key) is VOIDED by the person's self roster (T3): an id of
/// `roster` (the roster's own concluded acts) that removes the rotated-to key and cites the rotation (names it,
/// refs.also.cites). Voided, the rotation is no end of the old key and its successor does not stand; the old key is
/// restored exactly as it was (voiding is not removal). In a fork the roster's act names the one it voids. A one-key
/// roster cannot void (the residual).
pub fn voided<R: KeyEndRow>(c: &Concluded<'_, R>, rot: usize, roster: &BTreeSet<R::Id>) -> bool {
    let r = c.g.row(rot);
    let Some(x) = r.record() else { return false };
    roster.iter().filter_map(|e| c.g.idx(e)).any(|e| {
        let q = c.g.row(e);
        q.roster_end() == Some(x.key) && q.names().contains(r.id())
    })
}

/// Key `k`'s ends, as rows of `c`, each with the instant it ends rows from (if it states one): its LIVENESS (G33:
/// only the key's own acts end it):
/// - its self-revocations, but NONE where a concluded rotation of `k` is held at all: a retired key's revocation is
///   no end, whoever signed it and whatever its past holds;
/// - every concluded rotation naming `k`'s record not [`voided`] by the person's self roster. Two rotations of one
///   key are a FORK of the key: both are ends of the old key, and neither successor stands until the self roster's
///   count settles which (voids one);
/// - for a rotated-to key, the roster's act voiding the rotation to it: its rows fall by the cut rule like any
///   ended key's.
///
/// An eviction from the person's self roster is NOT an end here: it ends the key AS A KEY OF THAT PERSON (G33), read
/// by the person map at each count's voices ([`crate::seat::Persons`], [`crate::seat::person_at`]), and a row the
/// key signs as itself is read as any unowned key's. The caller presents the person's self-roster rows.
///
/// The residual, stated: a person with ONE key (a self roster of one), whose key is stolen, cannot be told from the
/// thief: the thief can rotate or revoke it as the owner could, and no roster can void a rotation.
pub fn ends<R: KeyEndRow>(c: &Concluded<'_, R>, k: &R::Key, roster: &BTreeSet<R::Id>) -> Vec<(usize, Option<R::T>)> {
    let rots: Vec<usize> = c
        .cs()
        .iter()
        .copied()
        .filter(|&e| c.g.row(e).record().is_some_and(|x| x.succ_of == Some(k)) && !voided(c, e, roster))
        .collect();
    let mut out: Vec<(usize, Option<R::T>)> = rots.iter().map(|&e| (e, None)).collect();
    for &e in c.cs() {
        let q = c.g.row(e);
        if let Some((rk, ra)) = q.revocation() {
            if rk == k && q.signer() == k && rots.is_empty() {
                out.push((e, Some(ra)));
            }
        }
    }
    // the roster's void of a rotation to k ends k
    for e in roster.iter().filter_map(|e| c.g.idx(e)) {
        let q = c.g.row(e);
        if q.roster_end() == Some(k)
            && q.names()
                .iter()
                .filter_map(|n| c.g.idx(n))
                .any(|n| c.g.row(n).record().is_some_and(|x| x.succ_of.is_some() && x.key == k))
        {
            out.push((e, None));
        }
    }
    out
}

/// THE END RULE read for a reader (A KEY END IS A CUT, the Constitution's ruling): key `k`'s signature on concluded
/// row `i` counts where, against each of `k`'s ends `e`, (a) `i` is in `e`'s past (and, where `e` states an instant
/// and `i` states one, `i`'s is before it); or (b) `i` is on `reader`'s own line from before the reader held `e`: a
/// row the reader signed or cosigned is `i` or has `i` in its past, without `e` there (taken up); or (c) `i` is part
/// of a count FINAL BY ACKNOWLEDGEMENT (`final_`, the ids of the counts with n - t + 1 clean receipts,
/// [`crate::seat::final_by_ack`]): that count, or a row it names, and only a voice valid when cast: never one whose
/// end `e` is in the final count's own past. A final act is not reopened by a later cut. `roster`: the self roster's
/// concluded acts ([`ends`]). No cite is read.
///
/// The cost, stated: nobody can tell the thief from the owner, so a thief's vote a reader took up before holding the
/// end stands for that reader, and one in a final count stands for everyone; the remedy is the members' later count
/// reversing the act. Readers can differ on a count not yet final until receipts or a later count settle it. A
/// newcomer (a reader with no row) reads the plain cut and the final counts. Caller duty: an honest rotation or
/// revocation names the key's last rows.
pub fn counts_for<R: KeyEndRow>(
    c: &Concluded<'_, R>,
    i: usize,
    k: &R::Key,
    reader: Option<&R::Key>,
    final_: &BTreeSet<R::Id>,
    roster: &BTreeSet<R::Id>,
) -> bool {
    if !c.all().get(i).copied().unwrap_or(false) {
        return false;
    }
    let r = c.g.row(i);
    let at = r.instant();
    let own: Vec<usize> = match reader {
        Some(o) => c
            .cs()
            .iter()
            .copied()
            .filter(|&a| c.g.row(a).signer() == o || c.g.row(a).cosigned_by().contains(o))
            .collect(),
        None => Vec::new(),
    };
    // the final counts this row is part of: the count itself, or a row it names
    let finals: Vec<usize> = final_
        .iter()
        .filter_map(|f| c.g.idx(f))
        .filter(|&fi| fi == i || c.g.row(fi).names().contains(r.id()))
        .collect();
    ends(c, k, roster).into_iter().all(|(e, ra)| {
        (c.g.in_past(i, e) && !matches!((at, ra), (Some(t), Some(a)) if t >= a))
            || own.iter().any(|&a| (a == i || c.g.in_past(i, a)) && !c.g.in_past(e, a))
            || finals.iter().any(|&fi| !c.g.in_past(e, fi))
    })
}

/// What a count asks of the key lane at its voices step ([`crate::cut::CutSpec::key_view`]): whether key `key`'s
/// signature on row `row` counts by the end rule. A store with key records MUST supply one; with none (the
/// default), every voice counts, which is only for a caller with no key lane.
pub trait KeyView<I, K> {
    /// Whether `key`'s signature on `row` counts ([`counts_by`]). A row the view does not hold counts nothing.
    fn counts(&self, row: &I, key: &K) -> bool;
}

/// The kernel's [`KeyView`]: [`counts_by`] over one [`Concluded`] of the seat and key lanes in one causal order,
/// concluded by [`conclude_rule`], which the caller builds from its store.
pub struct KeyReading<'c, 'a, R: KeyEndRow> {
    /// The key lane and the seat rows, in one causal order.
    pub c: &'c Concluded<'a, R>,
    /// The reader whose line it reads ([`counts_for`] (b)); `None`: no reader's line. A store builds one per reader
    /// and passes it in the spec it gives [`crate::seat::for_reader`] and [`crate::seat::Seats::for_reader`].
    pub reader: Option<R::Key>,
    /// The counts final by acknowledgement ([`crate::seat::final_by_ack`], read over the rows as they concluded with
    /// no key view: a final act is not reopened by a later cut).
    pub final_: BTreeSet<R::Id>,
    /// The self roster's acts concluded under that roster's own count rule (the seat's reading, with no key view):
    /// the roster ends [`ends`] reads.
    pub roster: BTreeSet<R::Id>,
}

impl<R: KeyEndRow> KeyView<R::Id, R::Key> for KeyReading<'_, '_, R> {
    fn counts(&self, row: &R::Id, key: &R::Key) -> bool {
        self.c.g.idx(row).is_some_and(|i| counts_for(self.c, i, key, self.reader.as_ref(), &self.final_, &self.roster))
    }
}

/// The rows whose STUB is kept for good at `now` (digest, names, the fields a count reads, the conclusion): every
/// row a count reads ([`counts`]), every row whose bytes are kept ([`bytes_retained`]), and everything in their
/// past. Storage only: a count reads [`counts`], never this.
pub fn retained<R: KeyEndRow>(c: &Concluded<'_, R>, now: R::T) -> BTreeSet<usize> {
    keep(c, now, true)
}

/// The rows whose BYTES are kept at `now`: every concluded row of a key that has not ended, every revocation and
/// rotation, and everything in their past (what a live row names). A row a count reads that is not among them (an
/// expired key's in-time vote, its count settled) keeps only its stub ([`retained`]), as the purge keeps a settled
/// act's stub.
pub fn bytes_retained<R: KeyEndRow>(c: &Concluded<'_, R>, now: R::T) -> BTreeSet<usize> {
    keep(c, now, false)
}

fn keep<R: KeyEndRow>(c: &Concluded<'_, R>, now: R::T, stubs: bool) -> BTreeSet<usize> {
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
        let seed = r.revocation().is_some()
            || r.record().is_some_and(|x| x.succ_of.is_some())
            || (stubs && r.statement().is_some() && counts(c, i))
            || !ended(r.record().map(|x| x.key).unwrap_or(r.signer()));
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
