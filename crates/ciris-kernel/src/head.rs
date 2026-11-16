//! Answers indexed by head, receipts and one say, settled and missing; and a node's checkpoint and purge
//! (KERNEL.md sections 3 and 3a; CC 2.7.3, 2.7.5, 2.7.7 rule 6, 2.7.10). `purge.py`.
//!
//! A node holds a **store**: for each kept row either the whole row or a **stub**. Both are an [`Entry`]:
//! the row's digest, the digests it names, its kind and the header fields a rule reads, its conclusion
//! (for a stub), and, where an act's count at its own head is final, that answer. Every answer here reads
//! only those fields, which is why a stub answers as the whole row does.
//!
//! * `counts_at`: does the act count at the head it names. One say: a signer holding a clean receipt of
//!   the act in a row concurrent with the cut has no say on it (`symmetric_say_forced`, `say4_closed`).
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
use core::cell::OnceCell;

/// Up to how many members [`View`] scans a roster version's list for a key before it keeps them as a set.
const MEMBERS_SCANNED: usize = 32;
/// Up to how many held entries [`View`] scans them all for an act's receipts and cuts, an answer or a name,
/// before it builds an index (built once, when first read).
const SCANNED: usize = 64;

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
    /// An act's count at its own head, where it is final.
    pub final_counts: Option<bool>,
    /// The act was settled when stored.
    pub settled_stub: bool,
    /// The keys whose receipts of a final act were held when its receipts were dropped.
    pub ackers: Vec<K>,
    /// The receipt digests of a settled act.
    pub acks: Vec<I>,
    /// A receipt or cut of a final act, dropped: the cut and receipt rules no longer read it.
    pub dropped: bool,
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

/// Every answer, over a store plus newly offered rows, for the node signing under `own`.
pub struct View<I, K, T> {
    own: K,
    reading: Reading,
    say: bool,
    /// The held entries by id.
    pub rec: BTreeMap<I, Entry<I, K, T>>,
    anc: BTreeMap<I, BTreeSet<I>>,
    depth: BTreeMap<I, usize>,
    /// The conclusion of every held entry.
    pub c: BTreeMap<I, bool>,
    /// The counted rows the reader's line holds void.
    pub v: BTreeSet<I>,
    /// The held entries that name each act as theirs (`of`), by ascending id: its receipts and cuts. Built
    /// when an answer first reads it, as are the next two.
    by_of: OnceCell<BTreeMap<I, Vec<I>>>,
    /// The ids an answer names.
    answered: OnceCell<BTreeSet<I>>,
    /// The ids any held entry names.
    named: OnceCell<BTreeSet<I>>,
    /// The members of each entry listing more than [`MEMBERS_SCANNED`], as a set.
    mem: BTreeMap<I, BTreeSet<K>>,
    /// The heads this node has acknowledged.
    acked: BTreeSet<I>,
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
            by_of: OnceCell::new(),
            answered: OnceCell::new(),
            named: OnceCell::new(),
            mem: BTreeMap::new(),
            acked: BTreeSet::new(),
        };
        for (i, r) in &me.rec {
            if r.members.len() > MEMBERS_SCANNED {
                me.mem.insert(i.clone(), r.members.iter().cloned().collect());
            }
        }
        let ids: Vec<I> = me.rec.keys().cloned().collect();
        for i in &ids {
            me.depth_of(i);
        }
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
        match head.as_ref().and_then(|h| self.mem.get(h)) {
            Some(m) => m.contains(k),
            None => self.members(head).contains(k),
        }
    }

    /// The held entries that may name act `a` as theirs, ascending.
    /// A small store gives every entry (each caller reads `of`); a larger one gives the act's own, by index.
    fn of_entries<'s>(&'s self, a: &I) -> impl Iterator<Item = &'s Entry<I, K, T>> + 's {
        let small = self.rec.len() <= SCANNED;
        let scan = small.then(|| self.rec.values());
        let by_of = (!small).then(|| self.by_of.get_or_init(|| {
            let mut m: BTreeMap<I, Vec<I>> = BTreeMap::new();
            for (i, r) in &self.rec {
                if let Some(o) = &r.of {
                    m.entry(o.clone()).or_default().push(i.clone());
                }
            }
            m
        }));
        let indexed = by_of.and_then(|m| m.get(a)).into_iter().flatten().map(move |i| &self.rec[i]);
        scan.into_iter().flatten().chain(indexed)
    }

    fn depth_of(&mut self, i: &I) -> usize {
        if let Some(d) = self.depth.get(i) {
            return *d;
        }
        // iterative: the rows a row names are held (the door)
        let mut stack = alloc::vec![i.clone()];
        while let Some(x) = stack.last().cloned() {
            let pending: Vec<I> = self.rec[&x].names.iter().filter(|n| !self.depth.contains_key(*n)).cloned().collect();
            if pending.is_empty() {
                let d = 1 + self.rec[&x].names.iter().map(|n| self.depth[n]).max().unwrap_or(0);
                self.depth.insert(x, d);
                stack.pop();
            } else {
                stack.extend(pending);
            }
        }
        self.depth[i]
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

    fn concl(&self, r: &Entry<I, K, T>) -> bool {
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

    fn acked_of(&self) -> BTreeSet<I> {
        self.rec
            .values()
            .filter(|r| r.kind == Kind::ReaderAck && self.c[&r.id])
            .filter_map(|r| r.head.clone())
            .collect()
    }

    fn heads_of(&self, r: &Entry<I, K, T>) -> Vec<I> {
        if r.kind == Kind::Seat {
            return r.names.iter().filter(|n| self.rec[*n].kind == Kind::Seat).cloned().collect();
        }
        r.head.iter().cloned().collect()
    }

    fn behind(&self, r: &Entry<I, K, T>, acked: &BTreeSet<I>) -> bool {
        let hs = self.heads_of(r);
        acked.iter().any(|h| {
            !hs.is_empty() && hs.iter().all(|x| self.anc[h].contains(x)) && !self.anc[h].contains(&r.id) && r.id != *h
        })
    }

    fn void_set(&self, by_depth: &[I]) -> BTreeSet<I> {
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
        self.of_entries(a)
            .filter(|c| {
                c.kind == Kind::Cut
                    && c.of.as_ref() == Some(a)
                    && !c.dropped
                    && self.c[&c.id]
                    && !self.v.contains(&c.id)
            })
            .collect()
    }

    /// The keys holding a clean receipt of act `a`, each with its receipt rows: a receipt with no cut of
    /// the act by that key in its own past.
    pub fn receipts(&self, a: &I) -> BTreeMap<K, Vec<I>> {
        let cuts = self.cuts(a);
        let mut out: BTreeMap<K, Vec<I>> = BTreeMap::new();
        for x in self.of_entries(a) {
            if x.kind != Kind::Ack || x.of.as_ref() != Some(a) || x.dropped || !self.c[&x.id] {
                continue;
            }
            let k = &x.signer;
            if !cuts.iter().any(|c| self.anc[&x.id].contains(&c.id) && c.sigs.contains(k)) {
                out.entry(k.clone()).or_default().push(x.id.clone());
            }
        }
        out
    }

    fn voids_at(&self, c: &Entry<I, K, T>, a: &I, rcpts: &BTreeMap<K, Vec<I>>) -> bool {
        let act = &self.rec[a];
        if c.head != act.head || !self.conc(&c.id, a) {
            return false;
        }
        let voice: BTreeSet<&K> = c
            .sigs
            .iter()
            .filter(|k| self.is_member(&act.head, k))
            .filter(|k| !(self.say && rcpts.get(*k).is_some_and(|xs| xs.iter().any(|x| self.conc(x, &c.id)))))
            .collect();
        voice.len() >= self.q(&act.head)
    }

    /// Whether act `a` counts at the head it names.
    pub fn counts_at(&self, a: &I) -> bool {
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
                let n: BTreeSet<&K> = c.sigs.iter().filter(|k| self.is_member(&c.head, k)).collect();
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

    /// Whether act `a`'s count at its head is final for this node: its head is older than one it has
    /// acknowledged (broad reading only).
    pub fn closed_for_me(&self, a: &I) -> bool {
        if self.reading != Reading::Broad {
            return false;
        }
        match &self.rec[a].head {
            Some(h) => self.acked.iter().any(|x| self.anc[x].contains(h)),
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

    /// A window's state at `now`, read from the instant this node first held the opener.
    pub fn window(&self, o: &I, now: T) -> WindowState {
        let answered = if self.rec.len() <= SCANNED {
            self.rec.values().any(|x| x.kind == Kind::Answer && x.names.contains(o))
        } else {
            self.answered
                .get_or_init(|| {
                    self.rec.values().filter(|x| x.kind == Kind::Answer).flat_map(|x| x.names.iter().cloned()).collect()
                })
                .contains(o)
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
        if self.rec.len() <= SCANNED {
            return self.rec.keys().filter(|i| !self.rec.values().any(|r| r.names.contains(i))).cloned().collect();
        }
        let named = self.named.get_or_init(|| self.rec.values().flat_map(|r| r.names.iter().cloned()).collect());
        self.rec.keys().filter(|i| !named.contains(*i)).cloned().collect()
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
            // a stub stays a stub; a final act's receipt signers are kept
            let mut r = r.clone();
            if r.kind == Kind::Act && r.final_counts.is_some() && !r.settled_stub {
                let mut a: BTreeSet<K> = r.ackers.iter().cloned().collect();
                a.extend(v.receipts(i).into_keys());
                r.ackers = a.into_iter().collect();
                r.settled_stub = v.settled(i);
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
                    whole = true; // a forward cut: carried reads it again
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
                e.final_counts = Some(v.counts_at(i));
            }
            if v.settled(i) {
                e.settled_stub = true;
                let mut acks: Vec<I> = v.receipts(i).into_values().flatten().collect();
                acks.sort();
                e.acks = acks;
            } else if fin.contains(i) {
                e.ackers = v.receipts(i).into_keys().collect();
            }
        }
        if !whole && matches!(r.kind, Kind::Ack | Kind::Cut) && r.of.as_ref().is_some_and(|o| fin.contains(o)) {
            e.dropped = true;
        }
        out.insert(i.clone(), e);
    }
    (out, tips)
}
