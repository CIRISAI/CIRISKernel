//! Answers indexed by head, receipts and one say, settled and missing; and a node's checkpoint and purge
//! (KERNEL.md sections 3 and 3a; CC 2.7.3, 2.7.5, 2.7.7 rule 6, 2.7.10). `purge.py`.
//!
//! A node holds a **store**: for each kept row either the whole row or a **stub**. Both are an [`Entry`]:
//! the row's digest, the digests it names, its kind and the header fields a rule reads, its conclusion
//! (for a stub), and, where an act's count at its own head is final, that answer. Every answer here reads
//! only those fields, which is why a stub answers as the whole row does.
//!
//! * `counts_at`: does the act count at the head it names: no counted cut of it concurrent with it at that
//!   head or at an older one (rule 4: rows concurrent with the cut do not count from the head the cut names;
//!   CONFERRAL_END.md E3; through 0.3.0 only a cut at the act's own head was read). One say: a signer holding a
//!   clean receipt of the act in a row concurrent with the cut has no say on it (`symmetric_say_forced`,
//!   `say4_closed`). Receipts at the act's head settle it against cuts there, not against a cut at an older
//!   head, which a reader that acknowledged the act's head holds void (the line).
//! * `carried`: is it still in force at a later head; a forward cut is blocked by nothing.
//! * `settled`: clean receipts from n − t + 1 of the n members at its head (`ack_blocking_quorum`).
//! * `void`: the counted rows the reader's own acknowledged line holds void (broad reading, CC 2.7.8).
//!
//! The purge keeps whole every row under a duty of CC 2.7.10's list (unless a deletion duty outranks
//! it), every act whose count at its head is not final with its receipts and cuts, every forward cut, and
//! every window open at the checkpoint. A checkpoint binds nobody and no answer reads it; the digest of
//! the folded state it carries is the caller's to compute (the kernel does not hash).

use alloc::collections::{BTreeMap, BTreeSet};
use alloc::vec::Vec;

/// The depth of an entry on the walk's stack in [`View::new`].
const ON: usize = usize::MAX;
/// The depth of an entry on a cycle of names or naming one: no kept store holds it, and the view leaves it out.
const WAIT: usize = usize::MAX - 1;
/// Up to how many members [`View`] scans a roster version's list for a key before it keeps them as a set.
pub(crate) const MEMBERS_SCANNED: usize = 32;
/// Up to how many held entries [`View`] scans them all for an act's receipts and cuts, an answer or a name;
/// above it, [`View::new`] builds the indexes.
pub(crate) const SCANNED: usize = 64;

/// The kind of a stored row, as these answers read it.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum Kind {
    /// A roster version: names the versions it extends, lists its members and its count.
    Seat,
    /// A counted act at the head it names.
    Act,
    /// A receipt of an act by a member at its head.
    Ack,
    /// The reader's own acknowledgement of a head.
    ReaderAck,
    /// A cut of an act, at the head it names, carrying its signatures.
    Cut,
    /// A row that opens a window, with its length and the instant this node first held it.
    Open,
    /// A row that answers a window.
    Answer,
    /// Anything else.
    Other,
}

/// A duty of CC 2.7.10's list that keeps a row's bytes.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum Duty {
    /// The accountability record (CC 2.4.1.1).
    Accountability,
    /// Identity, consent and config records (CC 6.1.5.2 B1).
    Pinned,
    /// A `legal_hold` (CC 4.4.3.12); it also suspends a deletion duty.
    Hold,
    /// A class's retention floor (CC 4.4.3.12).
    Floor,
    /// Bytes counted toward an item's target or reported `here` (CC 6.1.5.1, 3.1.3.3).
    Owed,
    /// A retirement record under an accepted preserve request (CC 7.5.5).
    Preserve,
}

/// Which reading of the reader's line.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Reading {
    /// Every counted row naming a head strictly older than an acknowledged head (the rule, CC 2.7.8).
    Broad,
    /// Only roster versions so placed (kept to show the difference; not the rule).
    Narrow,
}

/// A stored row: the header fields a rule reads, and what a purge records.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Entry<I, K, T> {
    /// The row's digest.
    pub id: I,
    /// The digests it names.
    pub names: Vec<I>,
    /// Its kind.
    pub kind: Kind,
    /// Its signer.
    pub signer: K,
    /// The head it names (an act, a cut, a reader's acknowledgement).
    pub head: Option<I>,
    /// The act it acknowledges or cuts.
    pub of: Option<I>,
    /// A roster version's members.
    pub members: Vec<K>,
    /// A roster version's count.
    pub q: usize,
    /// A cut's signatures.
    pub sigs: Vec<K>,
    /// A window's length.
    pub length: Option<T>,
    /// The instant this node first held a window's opener.
    pub receipt: Option<T>,
    /// The duties that keep its bytes.
    pub duty: Vec<Duty>,
    /// Whether a deletion duty ends its bytes.
    pub delete: bool,
    /// Whether only the stub is held (no bytes).
    pub stub: bool,
    /// A stub's stored conclusion.
    pub concl: bool,
    /// An act's count at its own head against the cuts naming that head, where it is final (a cut at an older
    /// head is read again).
    pub final_counts: Option<bool>,
    /// The act was settled when stored.
    pub settled_stub: bool,
    /// The keys whose receipts of a final act were held when its receipts were dropped.
    pub ackers: Vec<K>,
    /// The digests of the clean receipts held of a final act when its receipts were dropped (one say on a cut
    /// at an older head reads them).
    pub acks: Vec<I>,
    /// A receipt or cut of a final act, dropped: the cut and receipt rules no longer read it.
    pub dropped: bool,
    /// The instant its signer states for it (persist: `asserted_at`), when it states one: what the `_at`
    /// answers read at ([`View::window_at`], [`View::answers_at`]). 0.3.
    pub at: Option<T>,
}

impl<I, K, T> Entry<I, K, T> {
    /// A whole row with nothing recorded.
    pub fn new(id: I, kind: Kind, signer: K, names: Vec<I>) -> Self {
        Entry {
            id,
            names,
            kind,
            signer,
            head: None,
            of: None,
            members: Vec::new(),
            q: 0,
            sigs: Vec::new(),
            length: None,
            receipt: None,
            duty: Vec::new(),
            delete: false,
            stub: false,
            concl: false,
            final_counts: None,
            settled_stub: false,
            ackers: Vec::new(),
            acks: Vec::new(),
            dropped: false,
            at: None,
        }
    }
    /// The same entry, stating the instant `t` (0.3).
    pub fn with_at(mut self, t: T) -> Self {
        self.at = Some(t);
        self
    }
}

/// The members at a head, as [`View`] reads them.
enum Members<'s, K> {
    Set(&'s BTreeSet<K>),
    List(&'s [K]),
}

impl<K: Ord> Members<'_, K> {
    #[inline]
    fn contains(&self, k: &K) -> bool {
        match self {
            Members::Set(m) => m.contains(k),
            Members::List(m) => m.contains(k),
        }
    }
}

/// The entries naming each act as theirs: one sorted buffer of (act, entry) pairs, as [`View::new`] builds it,
/// or by act, as a held view keeps it, so that one insertion is
/// `O(log n)`. Both answer the same entries in the same (id) order.
#[derive(Clone)]
pub(crate) enum ByOf<I> {
    Sorted(Vec<(I, I)>),
    Map(BTreeMap<I, Vec<I>>),
}

impl<I: Ord + Clone> ByOf<I> {
    /// The entries naming act `a` as theirs, ascending.
    pub(crate) fn of<'s>(&'s self, a: &I) -> impl Iterator<Item = &'s I> + 's {
        let (sorted, map): (&'s [(I, I)], &'s [I]) = match self {
            ByOf::Sorted(v) => {
                let lo = v.partition_point(|(o, _)| o < a);
                (&v[lo..v.partition_point(|(o, _)| o <= a)], &[])
            }
            ByOf::Map(m) => (&[], m.get(a).map_or(&[][..], |x| &x[..])),
        };
        sorted.iter().map(|(_, i)| i).chain(map.iter())
    }
    /// As a map, for insertion.
    pub(crate) fn map(&mut self) -> &mut BTreeMap<I, Vec<I>> {
        if let ByOf::Sorted(v) = self {
            let mut m: BTreeMap<I, Vec<I>> = BTreeMap::new();
            for (o, i) in core::mem::take(v) {
                m.entry(o).or_default().push(i);
            }
            *self = ByOf::Map(m);
        }
        match self {
            ByOf::Map(m) => m,
            ByOf::Sorted(_) => unreachable!("made a map above"),
        }
    }
}

/// The ids answers name: one sorted buffer ([`View::new`]) or a set (a held view).
#[derive(Clone)]
pub(crate) enum Answered<I> {
    Sorted(Vec<I>),
    Set(BTreeSet<I>),
}

impl<I: Ord + Clone> Answered<I> {
    fn contains(&self, o: &I) -> bool {
        match self {
            Answered::Sorted(v) => v.binary_search(o).is_ok(),
            Answered::Set(s) => s.contains(o),
        }
    }
    /// As a set, for insertion.
    pub(crate) fn set(&mut self) -> &mut BTreeSet<I> {
        if let Answered::Sorted(v) = self {
            *self = Answered::Set(core::mem::take(v).into_iter().collect());
        }
        match self {
            Answered::Set(s) => s,
            Answered::Sorted(_) => unreachable!("made a set above"),
        }
    }
}

/// A node's store: every kept row, whole or as a stub, by digest.
pub type Store<I, K, T> = BTreeMap<I, Entry<I, K, T>>;

/// The state of a window at `now`.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum WindowState {
    /// No answer, and not yet lapsed.
    Open,
    /// A row answers it.
    Answered,
    /// Its length has run from the instant this node first held its opener.
    Lapsed,
}

/// Every answer, over a store plus newly offered rows, for the node signing under `own`. An immutable
/// snapshot, built whole by [`View::new`]: its fields are read through methods. A store is closed under the
/// door; an entry of one on a cycle of names, or naming one, which no door keeps, is left out of the view.
/// `Clone` (0.3.x), so a held view is.
#[derive(Clone)]
pub struct View<I, K, T> {
    pub(crate) own: K,
    pub(crate) reading: Reading,
    pub(crate) say: bool,
    pub(crate) rec: BTreeMap<I, Entry<I, K, T>>,
    pub(crate) anc: BTreeMap<I, BTreeSet<I>>,
    pub(crate) depth: BTreeMap<I, usize>,
    pub(crate) c: BTreeMap<I, bool>,
    pub(crate) v: BTreeSet<I>,
    /// Up to how many held entries the answers scan them all; above it they read the next two indexes,
    /// built in [`View::new`] ([`SCANNED`], except in this module's tests).
    pub(crate) scanned: usize,
    /// The held entries that name each act as theirs (`of`), by ascending id: its receipts and cuts.
    pub(crate) by_of: ByOf<I>,
    /// The ids an answer names.
    pub(crate) answered: Answered<I>,
    /// The members of each entry listing more than [`MEMBERS_SCANNED`], as a set.
    pub(crate) mem: BTreeMap<I, BTreeSet<K>>,
    /// The heads this node has acknowledged.
    pub(crate) acked: BTreeSet<I>,
}

/// The answers compared before and after a purge.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Answers<I, K> {
    /// The kept ids, ascending.
    pub kept: Vec<I>,
    /// Each kept row's conclusion.
    pub concluded: Vec<(I, bool)>,
    /// For each concluded act, whether it counts at its head.
    pub counts_at: Vec<(I, bool)>,
    /// For each concluded act, whether it is still in force at the latest head.
    pub carried: Vec<(I, bool)>,
    /// For each concluded act, whether it is settled.
    pub settled: Vec<(I, bool)>,
    /// For each concluded act, the members at its head whose clean receipt is not held.
    pub missing: Vec<(I, Vec<K>)>,
    /// The ids void for the reader, ascending.
    pub void: Vec<I>,
    /// Each window's state.
    pub window: Vec<(I, WindowState)>,
}

impl<I: Ord + Clone, K: Ord + Clone, T: Ord + Copy + core::ops::Add<Output = T>> View<I, K, T> {
    /// The view over `store` with `extra` offered: a row waits for what it names.
    pub fn new(
        store: &BTreeMap<I, Entry<I, K, T>>,
        extra: &[Entry<I, K, T>],
        own: K,
        reading: Reading,
        say: bool,
    ) -> Self {
        Self::build(store, extra, own, reading, say, SCANNED)
    }

    /// The held entries by id.
    pub fn rec(&self) -> &BTreeMap<I, Entry<I, K, T>> {
        &self.rec
    }
    /// The conclusion of every held entry.
    pub fn c(&self) -> &BTreeMap<I, bool> {
        &self.c
    }
    /// The counted rows the reader's line holds void.
    pub fn v(&self) -> &BTreeSet<I> {
        &self.v
    }

    pub(crate) fn build(
        store: &BTreeMap<I, Entry<I, K, T>>,
        extra: &[Entry<I, K, T>],
        own: K,
        reading: Reading,
        say: bool,
        scanned: usize,
    ) -> Self {
        let mut rec = store.clone();
        let mut pending: Vec<Entry<I, K, T>> = extra.iter().filter(|r| !rec.contains_key(&r.id)).cloned().collect();
        let mut moved = true;
        while moved {
            moved = false;
            let mut k = 0;
            while k < pending.len() {
                if pending[k].names.iter().all(|n| rec.contains_key(n)) {
                    let r = pending.remove(k);
                    rec.insert(r.id.clone(), r);
                    moved = true;
                } else {
                    k += 1;
                }
            }
        }
        let mut me = View {
            own,
            reading,
            say,
            rec,
            anc: BTreeMap::new(),
            depth: BTreeMap::new(),
            c: BTreeMap::new(),
            v: BTreeSet::new(),
            scanned,
            by_of: ByOf::Sorted(Vec::new()),
            answered: Answered::Sorted(Vec::new()),
            mem: BTreeMap::new(),
            acked: BTreeSet::new(),
        };
        // depths first: an entry on a cycle of names, or naming one, waits; no kept store holds it, so the
        // view leaves it out
        let mut ids: Vec<I> = me.rec.keys().cloned().collect();
        for i in &ids {
            me.depth_of(i);
        }
        let gone: Vec<I> = me.depth.iter().filter(|(_, d)| **d == WAIT).map(|(i, _)| i.clone()).collect();
        if !gone.is_empty() {
            for i in &gone {
                me.rec.remove(i);
                me.depth.remove(i);
            }
            ids.retain(|i| me.rec.contains_key(i));
        }
        let index = me.rec.len() > scanned;
        let (mut by_of, mut answered): (Vec<(I, I)>, Vec<I>) = (Vec::new(), Vec::new());
        for (i, r) in &me.rec {
            if r.members.len() > MEMBERS_SCANNED {
                me.mem.insert(i.clone(), r.members.iter().cloned().collect());
            }
            if index {
                if let Some(o) = &r.of {
                    by_of.push((o.clone(), i.clone()));
                }
                if r.kind == Kind::Answer {
                    answered.extend(r.names.iter().cloned());
                }
            }
        }
        // each index one sorted buffer: (act, entry) pairs, and the ids answers name
        by_of.sort();
        me.by_of = ByOf::Sorted(by_of);
        answered.sort();
        answered.dedup();
        me.answered = Answered::Sorted(answered);
        let mut by_depth = ids.clone();
        by_depth.sort_by_key(|i| me.depth[i]);
        for i in &by_depth {
            let mut a = BTreeSet::new();
            for n in &me.rec[i].names {
                a.insert(n.clone());
                a.extend(me.anc[n].iter().cloned());
            }
            me.anc.insert(i.clone(), a);
        }
        for i in &ids {
            let c = me.concl(&me.rec[i]);
            me.c.insert(i.clone(), c);
        }
        me.acked = me.acked_of();
        me.v = me.void_set(&by_depth);
        me
    }

    fn is_member(&self, head: &Option<I>, k: &K) -> bool {
        self.member_of(head).contains(k)
    }

    /// The members at a head, read once for several keys: a set for a long list, else the list.
    fn member_of(&self, head: &Option<I>) -> Members<'_, K> {
        match head.as_ref().and_then(|h| self.mem.get(h)) {
            Some(m) => Members::Set(m),
            None => Members::List(self.members(head)),
        }
    }

    /// The held entries that name act `a` as theirs, ascending, read through the index (a store of more than
    /// `scanned` entries; a smaller one is scanned by the caller).
    fn of_entries<'s>(&'s self, a: &I) -> impl Iterator<Item = &'s Entry<I, K, T>> + 's {
        self.by_of.of(a).map(move |i| &self.rec[i])
    }

    /// The depth of entry `i`, by a walk down what entries name. An entry is ON the walk's stack while it
    /// waits for the depths of what it names; one still ON when an entry naming it is finished closes a cycle,
    /// and that entry, and every entry naming one that waits, gets [`WAIT`].
    fn depth_of(&mut self, i: &I) {
        if self.depth.contains_key(i) {
            return;
        }
        // iterative: the rows a row names are held (the door)
        let mut stack = alloc::vec![i.clone()];
        while let Some(x) = stack.last().cloned() {
            match self.depth.get(&x).copied() {
                None => {
                    // never pushed onto itself: a name of its own is read as a cycle when it is finished
                    let pending: Vec<I> = self.rec[&x]
                        .names
                        .iter()
                        .filter(|n| **n != x && !self.depth.contains_key(*n))
                        .cloned()
                        .collect();
                    if !pending.is_empty() {
                        self.depth.insert(x, ON);
                        stack.extend(pending);
                        continue;
                    }
                }
                Some(ON) => {}
                Some(_) => {
                    stack.pop(); // done already (pushed twice)
                    continue;
                }
            }
            let (mut top, mut waits) = (0, false);
            for n in &self.rec[&x].names {
                if *n == x {
                    waits = true; // a name of its own: a cycle of one
                    continue;
                }
                let d = self.depth[n];
                if d >= WAIT {
                    waits = true; // a named entry on the stack (a cycle), or waiting
                } else if d > top {
                    top = d;
                }
            }
            self.depth.insert(x, if waits { WAIT } else { 1 + top });
            stack.pop();
        }
    }

    fn conc(&self, a: &I, b: &I) -> bool {
        a != b && !self.anc[b].contains(a) && !self.anc[a].contains(b)
    }

    fn members(&self, head: &Option<I>) -> &[K] {
        head.as_ref().and_then(|h| self.rec.get(h)).map_or(&[], |r| &r.members[..])
    }

    fn q(&self, head: &Option<I>) -> usize {
        head.as_ref().and_then(|h| self.rec.get(h)).map_or(0, |r| r.q)
    }

    pub(crate) fn concl(&self, r: &Entry<I, K, T>) -> bool {
        if r.stub {
            return r.concl; // Settled.checkpoint_conclusions: the stored conclusion
        }
        match r.kind {
            Kind::Act => self.is_member(&r.head, &r.signer),
            Kind::Ack => match r.of.as_ref().and_then(|o| self.rec.get(o)) {
                Some(act) => self.anc[&r.id].contains(r.of.as_ref().unwrap()) && self.is_member(&act.head, &r.signer),
                None => false,
            },
            Kind::ReaderAck => r.signer == self.own,
            _ => true,
        }
    }

    /// The heads this node has acknowledged.
    pub fn acked(&self) -> BTreeSet<I> {
        self.acked.clone()
    }

    pub(crate) fn acked_of(&self) -> BTreeSet<I> {
        self.rec
            .values()
            .filter(|r| r.kind == Kind::ReaderAck && self.c[&r.id])
            .filter_map(|r| r.head.clone())
            .collect()
    }

    pub(crate) fn heads_of(&self, r: &Entry<I, K, T>) -> Vec<I> {
        if r.kind == Kind::Seat {
            return r.names.iter().filter(|n| self.rec[*n].kind == Kind::Seat).cloned().collect();
        }
        r.head.iter().cloned().collect()
    }

    /// The line (CC 2.7.8 as amended by the ruling of 2026-11-27, sibling-safe): `r` names heads all strictly in
    /// the past of an acknowledged head's OWN heads, and is not in that head's past. A row at the acknowledged
    /// head's own head is not behind it.
    pub(crate) fn behind(&self, r: &Entry<I, K, T>, acked: &BTreeSet<I>) -> bool {
        let hs = self.heads_of(r);
        acked.iter().any(|h| {
            // an acknowledged head not held (a reader's acknowledgement not naming its head) has no past here
            let (Some(ah), Some(hr)) = (self.anc.get(h), self.rec.get(h)) else { return false };
            let own = self.heads_of(hr);
            let older = |x: &I| own.iter().any(|t| self.anc.get(t).is_some_and(|s| s.contains(x)));
            !hs.is_empty() && hs.iter().all(older) && !ah.contains(&r.id) && r.id != *h
        })
    }

    pub(crate) fn void_set(&self, by_depth: &[I]) -> BTreeSet<I> {
        let acked = &self.acked;
        let mut out = BTreeSet::new();
        for i in by_depth {
            let r = &self.rec[i];
            if !matches!(r.kind, Kind::Act | Kind::Cut | Kind::Seat) || !self.c[i] {
                continue;
            }
            if self.reading == Reading::Narrow && r.kind != Kind::Seat {
                continue;
            }
            if self.behind(r, acked) || self.heads_of(r).iter().any(|h| out.contains(h)) {
                out.insert(i.clone());
            }
        }
        out
    }

    fn cuts(&self, a: &I) -> Vec<&Entry<I, K, T>> {
        let is = |c: &&Entry<I, K, T>| {
            c.kind == Kind::Cut && c.of.as_ref() == Some(a) && !c.dropped && self.c[&c.id] && !self.v.contains(&c.id)
        };
        if self.rec.len() <= self.scanned {
            return self.rec.values().filter(is).collect();
        }
        self.of_entries(a).filter(is).collect()
    }

    /// The keys holding a clean receipt of act `a`, each with its receipt rows: a receipt with no cut of
    /// the act by that key in its own past.
    pub fn receipts(&self, a: &I) -> BTreeMap<K, Vec<I>> {
        let cuts = self.cuts(a);
        let mut out: BTreeMap<K, Vec<I>> = BTreeMap::new();
        let mut visit = |x: &Entry<I, K, T>| {
            if x.kind != Kind::Ack || x.of.as_ref() != Some(a) || x.dropped || !self.c[&x.id] {
                return;
            }
            let k = &x.signer;
            if !cuts.iter().any(|c| self.anc[&x.id].contains(&c.id) && c.sigs.contains(k)) {
                out.entry(k.clone()).or_default().push(x.id.clone());
            }
        };
        if self.rec.len() <= self.scanned {
            self.rec.values().for_each(&mut visit);
        } else {
            self.of_entries(a).for_each(visit);
        }
        out
    }

    /// The clean receipts one say reads: those held ([`View::receipts`]), and those a purge dropped and recorded
    /// on a final act ([`Entry::acks`]).
    fn say_receipts(&self, a: &I) -> BTreeMap<K, Vec<I>> {
        let mut out = self.receipts(a);
        for x in &self.rec[a].acks {
            if let Some(e) = self.rec.get(x) {
                let l = out.entry(e.signer.clone()).or_default();
                if !l.contains(x) {
                    l.push(x.clone());
                }
            }
        }
        out
    }

    /// Whether cut `c`'s say-holding signatures by members at `head` reach that head's count. One say: a
    /// signer holding a clean receipt of the act in a row concurrent with the cut has no say on it.
    fn met(&self, c: &Entry<I, K, T>, head: &Option<I>, rcpts: &BTreeMap<K, Vec<I>>) -> bool {
        let m = self.member_of(head);
        let voice: BTreeSet<&K> = c
            .sigs
            .iter()
            .filter(|k| m.contains(k))
            .filter(|k| !(self.say && rcpts.get(*k).is_some_and(|xs| xs.iter().any(|x| self.conc(x, &c.id)))))
            .collect();
        voice.len() >= self.q(head)
    }

    /// Whether head `h` has head `he` strictly in its past.
    fn later(&self, h: &Option<I>, he: &Option<I>) -> bool {
        match (h, he) {
            (Some(h), Some(he)) => h != he && self.anc.get(h).is_some_and(|s| s.contains(he)),
            _ => false,
        }
    }

    /// A cut at the act's own head, concurrent with it.
    fn voids_at(&self, c: &Entry<I, K, T>, a: &I, rcpts: &BTreeMap<K, Vec<I>>) -> bool {
        let act = &self.rec[a];
        c.head == act.head && self.conc(&c.id, a) && self.met(c, &act.head, rcpts)
    }

    /// A cut at a head older than the act's (a head in the past of the act's head), concurrent with it: rule 4,
    /// rows on the slot concurrent with the cut do not count from the head the cut names (CONFERRAL_END.md E3).
    /// Counted over the members at the cut's head, with one say as at the act's own head.
    fn voids_from(&self, c: &Entry<I, K, T>, a: &I) -> bool {
        let act = &self.rec[a];
        if !self.later(&act.head, &c.head) || !self.conc(&c.id, a) {
            return false;
        }
        let rc = if self.say { self.say_receipts(a) } else { BTreeMap::new() };
        self.met(c, &c.head, &rc)
    }

    /// Whether act `a` counts at its head against the cuts naming that head: the answer a purge stores as
    /// final ([`Entry::final_counts`]).
    pub(crate) fn counts_own(&self, a: &I) -> bool {
        let r = &self.rec[a];
        if let Some(f) = r.final_counts {
            return f;
        }
        if self.v.contains(a) {
            return false;
        }
        let rc = if self.say { self.receipts(a) } else { BTreeMap::new() };
        !self.cuts(a).iter().any(|c| self.voids_at(c, a, &rc))
    }

    /// Whether act `a` counts at the head it names: no counted cut of it concurrent with it at that head or at
    /// an older one (KERNEL.md section 6, rule 4). A cut naming a later head acts forward ([`View::carried`]).
    pub fn counts_at(&self, a: &I) -> bool {
        self.counts_own(a) && !self.cuts(a).iter().any(|c| self.voids_from(c, a))
    }

    /// Whether act `a` is still in force at the latest head: it counts at its own, and no cut of it naming
    /// a later head carries that head's count.
    pub fn carried(&self, a: &I) -> bool {
        if !self.counts_at(a) {
            return false;
        }
        let r = &self.rec[a];
        for c in self.cuts(a) {
            let later = c.head != r.head
                && match (&r.head, &c.head) {
                    (Some(h), Some(ch)) => self.anc.get(ch).is_some_and(|s| s.contains(h)),
                    _ => false,
                };
            if later {
                let m = self.member_of(&c.head);
                let n: BTreeSet<&K> = c.sigs.iter().filter(|k| m.contains(k)).collect();
                if n.len() >= self.q(&c.head) {
                    return false;
                }
            }
        }
        true
    }

    fn have(&self, a: &I) -> BTreeSet<K> {
        let mut h: BTreeSet<K> = self.receipts(a).into_keys().collect();
        h.extend(self.rec[a].ackers.iter().cloned());
        h
    }

    /// Whether act `a` is settled: clean receipts from n − t + 1 of the n members at its head.
    pub fn settled(&self, a: &I) -> bool {
        let r = &self.rec[a];
        if r.settled_stub {
            return true;
        }
        let m = self.members(&r.head);
        let have = self.have(a);
        let n = m.iter().collect::<BTreeSet<_>>().iter().filter(|k| have.contains(**k)).count();
        n + self.q(&r.head) > m.len()
    }

    /// Whether act `a`'s count at its head is final for this node: its head is strictly in the past of the own
    /// heads of one it has acknowledged (broad reading only; sibling-safe, as the line): every cut at that
    /// head or an older one is behind its line.
    pub fn closed_for_me(&self, a: &I) -> bool {
        if self.reading != Reading::Broad {
            return false;
        }
        match &self.rec[a].head {
            Some(h) => self.acked.iter().any(|x| {
                self.rec
                    .get(x)
                    .is_some_and(|xr| self.heads_of(xr).iter().any(|t| self.anc.get(t).is_some_and(|s| s.contains(h))))
            }),
            None => false,
        }
    }

    /// For an act not settled, the members at its head whose clean receipt is not held, ascending.
    pub fn missing(&self, a: &I) -> Vec<K> {
        if self.settled(a) {
            return Vec::new();
        }
        let have = self.have(a);
        let m: BTreeSet<K> = self.members(&self.rec[a].head).iter().cloned().collect();
        m.into_iter().filter(|k| !have.contains(k)).collect()
    }

    /// A window's state at the instant row `at` states ([`Entry::at`]), never a clock; `None` when `at` is
    /// not held or states no instant (0.3). The window still runs from the instant this node first held the
    /// opener, which CC rules node-local; only the reader's clock is replaced.
    pub fn window_at(&self, o: &I, at: &I) -> Option<WindowState> {
        let t = self.rec.get(at)?.at?;
        Some(self.window(o, t))
    }

    /// Every answer at the instant row `at` states; `None` when `at` is not held or states no instant (0.3).
    pub fn answers_at(&self, at: &I) -> Option<Answers<I, K>> {
        let t = self.rec.get(at)?.at?;
        Some(self.answers(t))
    }

    /// A window's state at `now`, read from the instant this node first held the opener. A per-node reading
    /// (CC 2.7.9) that decides nothing that counts (CIRISConstitution#221, W5): for serving and display. A
    /// window whose close binds others lands by a signed row ([`crate::window`]); a verdict reads
    /// [`View::window_at`].
    pub fn window(&self, o: &I, now: T) -> WindowState {
        let answered = if self.rec.len() <= self.scanned {
            self.rec.values().any(|x| x.kind == Kind::Answer && x.names.contains(o))
        } else {
            self.answered.contains(o)
        };
        if answered {
            return WindowState::Answered;
        }
        let r = &self.rec[o];
        match (r.receipt, r.length) {
            (Some(rc), Some(l)) if now >= rc + l => WindowState::Lapsed,
            _ => WindowState::Open,
        }
    }

    /// Every answer at `now`.
    pub fn answers(&self, now: T) -> Answers<I, K> {
        let ids: Vec<I> = self.rec.keys().cloned().collect();
        let acts: Vec<I> = ids.iter().filter(|i| self.rec[*i].kind == Kind::Act && self.c[*i]).cloned().collect();
        Answers {
            kept: ids.clone(),
            concluded: ids.iter().map(|i| (i.clone(), self.c[i])).collect(),
            counts_at: acts.iter().map(|a| (a.clone(), self.counts_at(a))).collect(),
            carried: acts.iter().map(|a| (a.clone(), self.carried(a))).collect(),
            settled: acts.iter().map(|a| (a.clone(), self.settled(a))).collect(),
            missing: acts.iter().map(|a| (a.clone(), self.missing(a))).collect(),
            void: self.v.iter().cloned().collect(),
            window: ids
                .iter()
                .filter(|o| self.rec[*o].kind == Kind::Open)
                .map(|o| (o.clone(), self.window(o, now)))
                .collect(),
        }
    }

    /// The held ids no held row names: what a checkpoint names.
    pub fn tips(&self) -> Vec<I> {
        if self.rec.len() <= self.scanned {
            return self.rec.keys().filter(|i| !self.rec.values().any(|r| r.names.contains(i))).cloned().collect();
        }
        // the ids named, read once for this call (a checkpoint asks once)
        let named: BTreeSet<&I> = self.rec.values().flat_map(|r| r.names.iter()).collect();
        self.rec.keys().filter(|i| !named.contains(i)).cloned().collect()
    }
}

/// Sign a checkpoint over the store and drop what CC 2.7.10 lets a node drop. Returns the new store and
/// the digests the checkpoint names (the rows no held row names). The checkpoint row itself, and the digest
/// of the folded state it carries, are the caller's to sign.
pub fn purge<I: Ord + Clone, K: Ord + Clone, T: Ord + Copy + core::ops::Add<Output = T>>(
    store: &BTreeMap<I, Entry<I, K, T>>,
    own: K,
    now: T,
    reading: Reading,
) -> (Store<I, K, T>, Vec<I>) {
    let v = View::new(store, &[], own, reading, true);
    let tips = v.tips();
    let acts: Vec<I> = v.rec.keys().filter(|a| v.rec[*a].kind == Kind::Act && v.c[*a]).cloned().collect();
    let fin: BTreeSet<I> = acts.iter().filter(|a| v.settled(a) || v.closed_for_me(a)).cloned().collect();
    let open: BTreeSet<I> = acts.iter().filter(|a| !fin.contains(*a)).cloned().collect();
    let mut out = BTreeMap::new();
    for (i, r) in &v.rec {
        if r.stub {
            // a stub stays a stub; a final act's receipt signers and receipt digests are kept
            let mut r = r.clone();
            if r.kind == Kind::Act && r.final_counts.is_some() {
                let held = v.receipts(i);
                let mut d: BTreeSet<I> = r.acks.iter().cloned().collect();
                d.extend(held.values().flatten().cloned());
                r.acks = d.into_iter().collect();
                if !r.settled_stub {
                    let mut a: BTreeSet<K> = r.ackers.iter().cloned().collect();
                    a.extend(held.into_keys());
                    r.ackers = a.into_iter().collect();
                    r.settled_stub = v.settled(i);
                }
            }
            out.insert(i.clone(), r);
            continue;
        }
        let deleted = r.delete && !r.duty.contains(&Duty::Hold); // a hold suspends deletion; nothing else does
        let mut whole = !r.duty.is_empty() && !deleted;
        let of_open = r.of.as_ref().is_some_and(|o| open.contains(o));
        if r.kind == Kind::Act && open.contains(i) {
            whole = true;
        }
        if matches!(r.kind, Kind::Ack | Kind::Cut) && of_open {
            whole = true;
        }
        if r.kind == Kind::Cut {
            if let Some(act) = r.of.as_ref().and_then(|o| v.rec.get(o)) {
                if act.head != r.head {
                    whole = true; // a cut at another head: carried, or counts_at for an older head, reads it again
                }
            }
        }
        if r.kind == Kind::Open && v.window(i, now) == WindowState::Open {
            whole = true;
        }
        if deleted {
            whole = false;
        }
        // a stub keeps the header only: the signatures a cut carries and what an earlier purge recorded go
        let mut e = r.clone();
        if !whole {
            e.sigs = Vec::new();
            e.final_counts = None;
            e.settled_stub = false;
            e.ackers = Vec::new();
            e.acks = Vec::new();
            e.dropped = false;
            e.stub = true;
            e.concl = v.c[i];
        }
        if r.kind == Kind::Act && v.c[i] {
            if fin.contains(i) {
                e.final_counts = Some(v.counts_own(i));
            }
            let mut acks: Vec<I> = v.receipts(i).into_values().flatten().collect();
            acks.sort();
            if v.settled(i) {
                e.settled_stub = true;
                e.acks = acks;
            } else if fin.contains(i) {
                e.ackers = v.receipts(i).into_keys().collect();
                e.acks = acks;
            }
        }
        if !whole && matches!(r.kind, Kind::Ack | Kind::Cut) && r.of.as_ref().is_some_and(|o| fin.contains(o)) {
            e.dropped = true;
        }
        out.insert(i.clone(), e);
    }
    (out, tips)
}

#[cfg(test)]
mod tests {
    use super::*;
    use alloc::vec;

    struct Lcg(u64);
    impl Lcg {
        fn next(&mut self, n: u64) -> u64 {
            self.0 = self.0.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
            (self.0 >> 33) % n.max(1)
        }
    }

    /// A closed store of every kind, each entry naming only earlier ones: roster versions (some with more
    /// than 32 members), acts at them, receipts and cuts of the acts, the reader's acknowledgements, windows
    /// and answers, and entries of other kinds that name windows and acts too.
    fn store(g: &mut Lcg, n: u32) -> Store<u32, u32, i64> {
        let mut s: Store<u32, u32, i64> = BTreeMap::new();
        let (mut seats, mut acts, mut opens): (Vec<u32>, Vec<u32>, Vec<u32>) = (vec![], vec![], vec![]);
        for i in 0..n {
            let pick = |g: &mut Lcg, v: &Vec<u32>| v[g.next(v.len() as u64) as usize];
            let mut names: Vec<u32> = (0..g.next(3)).filter(|_| i > 0).map(|_| g.next(i as u64) as u32).collect();
            let kind = match g.next(10) {
                _ if seats.is_empty() => Kind::Seat,
                0 | 1 => Kind::Seat,
                2 | 3 => Kind::Act,
                4 if !acts.is_empty() => Kind::Ack,
                5 if !acts.is_empty() => Kind::Cut,
                6 => Kind::ReaderAck,
                7 => Kind::Open,
                8 if !opens.is_empty() => Kind::Answer,
                _ => Kind::Other,
            };
            let mut e = Entry::new(i, kind, g.next(40) as u32, vec![]);
            match kind {
                Kind::Seat => {
                    let m = if g.next(3) == 0 { 33 + g.next(8) } else { g.next(8) };
                    e.members = (0..m as u32).collect();
                    e.q = 1 + g.next(1 + m / 2) as usize;
                    seats.push(i);
                }
                Kind::Act | Kind::ReaderAck => {
                    let h = pick(g, &seats);
                    e.head = Some(h);
                    names.push(h);
                    if kind == Kind::Act {
                        acts.push(i);
                    }
                }
                Kind::Ack | Kind::Cut => {
                    let a = pick(g, &acts);
                    e.of = Some(a);
                    if g.next(4) != 0 {
                        names.push(a);
                    }
                    if kind == Kind::Cut {
                        let h = pick(g, &seats);
                        e.head = Some(if g.next(2) == 0 { s[&a].head.unwrap() } else { h });
                        names.push(e.head.unwrap());
                        e.sigs = (0..g.next(6)).map(|_| g.next(40) as u32).collect();
                    }
                }
                Kind::Open => {
                    e.length = Some(10 + g.next(40) as i64);
                    e.receipt = Some(g.next(30) as i64);
                    opens.push(i);
                }
                Kind::Answer => names.push(pick(g, &opens)),
                _ => {
                    if !opens.is_empty() && g.next(2) == 0 {
                        names.push(pick(g, &opens)); // a row that names a window and is no answer
                    }
                    if !acts.is_empty() && g.next(2) == 0 {
                        e.of = Some(pick(g, &acts)); // a row that names an act as its own and is no receipt
                    }
                }
            }
            names.sort_unstable();
            names.dedup();
            e.names = names;
            s.insert(i, e);
        }
        s
    }

    /// The view read through its indexes answers as the view that scans, on every store, reader and now.
    #[test]
    fn indexed_view_answers_as_the_scanning_one() {
        let mut g = Lcg(7);
        let (mut cases, mut bad) = (0usize, 0usize);
        for _ in 0..400 {
            let n = 70 + g.next(80) as u32;
            let s = store(&mut g, n);
            for (reading, say, own) in
                [(Reading::Broad, true, 0u32), (Reading::Narrow, false, 3), (Reading::Broad, false, 5)]
            {
                let scan = View::build(&s, &[], own, reading, say, usize::MAX);
                let index = View::build(&s, &[], own, reading, say, 0);
                for now in [0i64, 25, 80] {
                    cases += 1;
                    bad += (scan.answers(now) != index.answers(now)) as usize;
                }
                cases += 2;
                bad += (scan.tips() != index.tips()) as usize;
                bad += (scan.acked() != index.acked()) as usize;
                for a in s.keys() {
                    cases += 1;
                    bad += (scan.receipts(a) != index.receipts(a)) as usize;
                }
            }
        }
        assert!(cases > 100_000);
        assert_eq!(bad, 0, "{bad} of {cases} answers differ");
    }

    /// Rule 4 read from the head the cut names (CONFERRAL_END.md E2, E3): a cut at an older head reaches an act
    /// at a later head concurrent with it, one say excepted; a cut at a later head acts forward; a cut at a head
    /// concurrent with the act's, or one the act has in its past, changes nothing at the act's head; a reader
    /// that acknowledged a head built on the act's head holds the older cut void.
    #[test]
    fn a_cut_reaches_forward_from_the_head_it_names() {
        type E = Entry<&'static str, char, i64>;
        let seat = |id, names: Vec<&'static str>, m: &str, q| {
            let mut e = E::new(id, Kind::Seat, 'r', names);
            e.members = m.chars().collect();
            e.q = q;
            e
        };
        let act = |id, by, head| {
            let mut e = E::new(id, Kind::Act, by, vec![head]);
            e.head = Some(head);
            e
        };
        let ack = |id, by, of| {
            let mut e = E::new(id, Kind::Ack, by, vec![of]);
            e.of = Some(of);
            e
        };
        let cut = |id, of, sigs: &str, head: &'static str| {
            let mut e = E::new(id, Kind::Cut, sigs.chars().next().unwrap(), vec![head]);
            e.of = Some(of);
            e.head = Some(head);
            e.sigs = sigs.chars().collect();
            e
        };
        let mut rk = E::new("rk", Kind::ReaderAck, 'N', vec!["v2"]);
        rk.head = Some("v2");
        let base = [
            seat("v0", vec![], "ABC", 2),
            seat("v1", vec!["v0"], "ABC", 2),
            seat("w1", vec!["v0"], "ABC", 2),
            seat("v2", vec!["v1"], "ABC", 2),
            act("E", 'A', "v1"),
            ack("aA", 'A', "E"),
        ];
        let answer = |extra: Vec<E>, a: &'static str| {
            let s: Store<&'static str, char, i64> = base.iter().cloned().chain(extra).map(|e| (e.id, e)).collect();
            let v = View::new(&s, &[], 'N', Reading::Broad, true);
            (v.counts_at(&a), v.carried(&a))
        };
        let at = |extra: Vec<E>| answer(extra, "E");
        assert_eq!(at(vec![]), (true, true));
        // E3: a cut naming v0, older than E's v1, concurrent with E: E does not count at v1 (through 0.3.0: it did)
        assert_eq!(at(vec![cut("x", "E", "BC", "v0")]), (false, false));
        // one say: B holds a clean receipt of E concurrent with the cut, so B has no say and the cut falls short
        assert_eq!(at(vec![cut("x", "E", "BC", "v0"), ack("aB", 'B', "E")]), (true, true));
        // the line (sibling-safe, the ruling of 2026-11-27): a reader that acknowledged v2 holds the cut at v0 void,
        // v0 being strictly in the past of v2's own head v1
        assert_eq!(at(vec![cut("x", "E", "BC", "v0"), rk]), (true, true));
        // a cut the act has in its past: rows in its past stand
        let mut e2 = act("E2", 'A', "v1");
        e2.names.push("x2");
        assert_eq!(answer(vec![cut("x2", "E2", "BC", "v0"), e2], "E2"), (true, true));
        // E2: a cut at E's own head voids it there, as before
        assert_eq!(at(vec![cut("y", "E", "BC", "v1")]), (false, false));
        // forward: a cut at the later v2 never changes what counted at v1; E is out of force
        assert_eq!(at(vec![cut("z", "E", "BC", "v2")]), (true, false));
        // a cut at w1, concurrent with E's head v1, is neither older nor later: E counts at v1 (E2). `carried`
        // reads only cuts at later heads, so it is not read there either (open: KERNEL.md section 6)
        assert_eq!(at(vec![cut("w", "E", "BC", "w1")]), (true, true));
    }

    #[test]
    fn a_view_is_send_and_sync() {
        fn both<X: Send + Sync>() {}
        both::<View<u32, u32, i64>>();
    }
}
