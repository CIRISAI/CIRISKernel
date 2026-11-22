//! The head layer held: a [`head::View`](crate::head::View) kept across admissions, and its checkpoint
//! (issue #4, `HELD.md` slice 4; KERNEL.md section 3a; CC 2.7.10).
//!
//! [`View::new`] builds every index of a store whole. A [`HeldView`] is the same view as a value the caller owns:
//! entries are admitted one at a time, and an admission updates only what the new entry can change. It
//! returns [`Admitted::dirty`]: the held entries whose answers may have changed, so a caller re-runs its door for
//! those alone. After every admission, [`HeldView::view`] answers exactly as [`View::new`] over the store and
//! every entry offered so far ([`differential`] checks it; the crate's tests run it).
//!
//! **What an admission recomputes.** A view's answers read an act, the rows naming it as theirs (its receipts
//! and cuts: the act's conflict set, found by its conflict key, [`conflict_key`], through an index), the
//! members at the heads they name, and the reader's acknowledged heads. A new entry `x` whose names are held:
//! - is concluded, and its past is one union over what it names (the past term, `|past(x)|`, reported apart);
//! - makes dirty itself, the act it names as its own (a receipt or cut changes that act's answers), and the
//!   windows it answers;
//! - is void, or not, by its own heads, read once. No earlier entry's conclusion or void changes, because no
//!   held entry has `x` in its past (`Causal.concl_final`, `conclOf_local`);
//!
//! except in two cases, where answers outside the cone of `x` change and the void set is read again whole
//! (`O(n)`, counted in [`Admitted::visited`]): `x` is a head that held entries name as theirs without naming
//! it (they read its members by id), or `x` makes a head acknowledged by this node that was not (every entry at
//! an older head may become void or closed). Neither occurs when every entry names the head it is at.
//!
//! **Cost of one admission** in the local case: `O((|kept| + |names|) · log n)`, plus the past term. The bench
//! (`examples/persist_paths.rs`, `held_view::`) asserts it by count at 1,024 and 64,000 entries.
//!
//! **Checkpoint** ([`HeldView::checkpoint`], [`HeldView::resume`]). The bytes carry kernel-side state only: the
//! view's reader, the held ids in fold order with each one's stub fields (what [`head::purge`](crate::head::purge)
//! recorded) and conclusion, the acknowledged heads, and the ids that wait. Row content comes back by id from
//! the caller's own store, so a checkpoint cannot disagree with the stored bytes of a row. Ids and keys are
//! written through [`Encode`]; fixed-width `[u8; N]`, the unsigned integers, `i64` and `String` are provided.
//! The kernel has no dependency, so the encoding is written here by hand:
//!
//! ```text
//! u16 version (CHECKPOINT_VERSION), big-endian
//! u8 reading (0 broad, 1 narrow) · u8 say (0, 1) · own: K
//! u64 held · per held entry, by (depth, id) ascending:
//!     id: I · u8 flags (bit 0 stub, 1 stored conclusion, 2 final count stated, 3 its value,
//!                       4 settled stub, 5 dropped, 6 the view's conclusion; bit 7 clear)
//!     u64 ackers · K each · u64 acks · I each
//! u64 acknowledged heads · I each, ascending
//! u64 waiting · I each, ascending
//! ```
//!
//! Pure and sync: no I/O, no clock, no global state. A refused admission changes nothing, and a `HeldView` is
//! `Clone`, so a caller inside a transaction that may roll back can keep the value it had. A `HeldView` owns its
//! entries, so unlike a borrowing [`Held`](crate::held::Held) it can live across transactions without a
//! checkpoint; the checkpoint is for a restart.

use crate::head::{Answered, ByOf, Entry, Kind, Reading, Store, View, WindowState, MEMBERS_SCANNED, SCANNED};
use crate::held::{Admitted, Mismatch, Refused};
use alloc::collections::{BTreeMap, BTreeSet};
use alloc::string::String;
use alloc::vec::Vec;
use core::ops::Add;

/// The version [`HeldView::checkpoint`] writes and [`HeldView::resume`] reads.
pub const CHECKPOINT_VERSION: u16 = 1;

/// Why bytes did not decode as a value.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DecodeError {
    /// The bytes end before the value does.
    Truncated,
    /// The bytes are no encoding of a value (for a `String`, not UTF-8).
    Invalid,
}

/// A value written into a checkpoint: an id or a key. The encoding must be canonical (one value, one
/// encoding) and self-delimiting.
pub trait Encode: Sized {
    /// Append the value's bytes.
    fn encode(&self, out: &mut Vec<u8>);
    /// The value at the start of `b`, and how many bytes it took.
    fn decode(b: &[u8]) -> Result<(Self, usize), DecodeError>;
}

/// Fixed width: the `N` bytes themselves (a 32-byte digest needs no code).
impl<const N: usize> Encode for [u8; N] {
    fn encode(&self, out: &mut Vec<u8>) {
        out.extend_from_slice(self);
    }
    fn decode(b: &[u8]) -> Result<(Self, usize), DecodeError> {
        let x: [u8; N] = b.get(..N).ok_or(DecodeError::Truncated)?.try_into().map_err(|_| DecodeError::Truncated)?;
        Ok((x, N))
    }
}

macro_rules! fixed {
    ($($t:ty),*) => {$(
        /// Fixed width, big-endian.
        impl Encode for $t {
            fn encode(&self, out: &mut Vec<u8>) {
                out.extend_from_slice(&self.to_be_bytes());
            }
            fn decode(b: &[u8]) -> Result<(Self, usize), DecodeError> {
                let (x, n) = <[u8; core::mem::size_of::<$t>()]>::decode(b)?;
                Ok((<$t>::from_be_bytes(x), n))
            }
        }
    )*};
}
fixed!(u8, u16, u32, u64, i64);

/// Length-prefixed: a `u32` byte count, big-endian, then the UTF-8 bytes.
impl Encode for String {
    fn encode(&self, out: &mut Vec<u8>) {
        (self.len() as u32).encode(out);
        out.extend_from_slice(self.as_bytes());
    }
    fn decode(b: &[u8]) -> Result<(Self, usize), DecodeError> {
        let (n, k) = u32::decode(b)?;
        let s = b.get(k..k + n as usize).ok_or(DecodeError::Truncated)?;
        let s = core::str::from_utf8(s).map_err(|_| DecodeError::Invalid)?;
        Ok((String::from(s), k + n as usize))
    }
}

/// Why [`HeldView::resume`] gave no view. It never gives a partial one.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum CheckpointError<I> {
    /// The bytes are of a version this kernel does not read.
    Version(u16),
    /// The bytes are not the ones the resumed view writes: trailing bytes, an unknown flag, ids out of
    /// order, a waiting row that would be kept, an id not encoded canonically.
    NotCanonical,
    /// The bytes end early.
    Truncated,
    /// An id the checkpoint names, or a resumed row names, that the caller's rows do not supply.
    Missing(I),
    /// A row the caller supplies concludes otherwise than the checkpoint states, or the heads it acknowledges
    /// differ: the store and the checkpoint disagree about this id.
    Differs(I),
}

impl<I> From<DecodeError> for CheckpointError<I> {
    fn from(e: DecodeError) -> Self {
        match e {
            DecodeError::Truncated => CheckpointError::Truncated,
            DecodeError::Invalid => CheckpointError::NotCanonical,
        }
    }
}

/// An entry's conflict key: the act it names as its own (a receipt's or a cut's `of`). Two entries conflict
/// when they share one; an act's answers read the entries of its key, through the view's index by key, never a
/// scan of pairs.
pub fn conflict_key<I, K, T>(e: &Entry<I, K, T>) -> Option<&I> {
    e.of.as_ref()
}

/// [`head::View`](crate::head::View), held across admissions. Equal, after every admission, to [`View::new`]
/// over the store it began from and every entry offered since.
#[derive(Clone)]
pub struct HeldView<I, K, T> {
    view: View<I, K, T>,
    /// For each id, the held entries whose head it is (whether or not they name it).
    by_head: BTreeMap<I, Vec<I>>,
    /// The entries offered whose names are not all held, by id, with how many names they lack.
    waiting: BTreeMap<I, (Entry<I, K, T>, usize)>,
    /// For each id not held that a waiting entry names, the waiting entries that name it.
    waiting_on: BTreeMap<I, Vec<I>>,
}

impl<I: PartialEq, K: PartialEq, T: PartialEq> PartialEq for HeldView<I, K, T> {
    /// The same reader, entries, pasts, depths, conclusions, void set, acknowledged heads and waiting entries.
    fn eq(&self, o: &Self) -> bool {
        let (a, b) = (&self.view, &o.view);
        a.own == b.own
            && a.reading == b.reading
            && a.say == b.say
            && a.rec == b.rec
            && a.anc == b.anc
            && a.depth == b.depth
            && a.c == b.c
            && a.v == b.v
            && a.acked == b.acked
            && self.waiting.len() == o.waiting.len()
            && self.waiting.iter().zip(o.waiting.iter()).all(|((i, (e, n)), (j, (f, m)))| i == j && e == f && n == m)
    }
}

/// One held entry as a checkpoint writes it: its id, the entry, and its conclusion.
type Held1<'v, I, K, T> = (&'v I, &'v Entry<I, K, T>, bool);

/// What one checkpoint entry states.
struct Stated<I, K> {
    id: I,
    flags: u8,
    ackers: Vec<K>,
    acks: Vec<I>,
}

const STUB: u8 = 1;
const CONCL: u8 = 1 << 1;
const FINAL: u8 = 1 << 2;
const FINAL_YES: u8 = 1 << 3;
const SETTLED: u8 = 1 << 4;
const DROPPED: u8 = 1 << 5;
const CONCLUDED: u8 = 1 << 6;

struct Cur<'b> {
    b: &'b [u8],
    at: usize,
}

impl Cur<'_> {
    fn take<X: Encode>(&mut self) -> Result<X, DecodeError> {
        let (x, n) = X::decode(&self.b[self.at..])?;
        self.at += n;
        Ok(x)
    }
    fn list<X: Encode>(&mut self) -> Result<Vec<X>, DecodeError> {
        let n: u64 = self.take()?;
        let mut v = Vec::new();
        for _ in 0..n {
            v.push(self.take()?);
        }
        Ok(v)
    }
}

fn put_list<X: Encode>(out: &mut Vec<u8>, v: &[X]) {
    (v.len() as u64).encode(out);
    for x in v {
        x.encode(out);
    }
}

impl<I: Ord + Clone, K: Ord + Clone, T: Ord + Copy + Add<Output = T>> HeldView<I, K, T> {
    /// The view over `store`: equal to [`View::new`]`(store, &[], own, reading, say)`. The store is closed under
    /// the door (every id an entry names is in it), as [`View::new`] requires.
    pub fn new(store: &Store<I, K, T>, own: K, reading: Reading, say: bool) -> Self {
        Self::from_view(View::new(store, &[], own, reading, say))
    }

    /// Nothing held.
    pub fn empty(own: K, reading: Reading, say: bool) -> Self {
        Self::new(&BTreeMap::new(), own, reading, say)
    }

    /// Hold a built view: its indexes whole, whatever its size ([`View::new`] builds them above
    /// [`SCANNED`] entries only, and scans below; both answer the same).
    fn from_view(mut view: View<I, K, T>) -> Self {
        let mut by_of: BTreeMap<I, Vec<I>> = BTreeMap::new();
        let mut answered: BTreeSet<I> = BTreeSet::new();
        let mut by_head: BTreeMap<I, Vec<I>> = BTreeMap::new();
        for (i, r) in &view.rec {
            if let Some(o) = &r.of {
                by_of.entry(o.clone()).or_default().push(i.clone()); // ascending, as `rec` is
            }
            if r.kind == Kind::Answer {
                answered.extend(r.names.iter().cloned());
            }
            if let Some(h) = &r.head {
                by_head.entry(h.clone()).or_default().push(i.clone());
            }
        }
        view.by_of = ByOf::Map(by_of);
        view.answered = Answered::Set(answered);
        HeldView { view, by_head, waiting: BTreeMap::new(), waiting_on: BTreeMap::new() }
    }

    /// Every [`View`] answer, unchanged.
    pub fn view(&self) -> &View<I, K, T> {
        &self.view
    }
    /// The number of entries held.
    pub fn len(&self) -> usize {
        self.view.rec.len()
    }
    /// Whether no entry is held.
    pub fn is_empty(&self) -> bool {
        self.view.rec.is_empty()
    }
    /// Whether an entry with this id is held.
    pub fn holds(&self, id: &I) -> bool {
        self.view.rec.contains_key(id)
    }
    /// Whether an entry with this id was offered and waits for an id it names.
    pub fn waits(&self, id: &I) -> bool {
        self.waiting.contains_key(id)
    }
    /// The ids of the entries that wait, ascending.
    pub fn waiting(&self) -> impl Iterator<Item = &I> + '_ {
        self.waiting.keys()
    }
    /// How many ids entry `id`'s past holds: the past term of its admission, which [`Admitted::visited`] does
    /// not count. `None` when `id` is not held.
    pub fn past_len(&self, id: &I) -> Option<usize> {
        self.view.anc.get(id).map(BTreeSet::len)
    }

    /// Admit one entry. Refused, changing nothing, when its id is held or waiting
    /// ([`Refused::Duplicate`]). Otherwise it is kept when every id it names is held, and then so is every
    /// waiting entry this releases; else it waits (an entry naming itself waits for good, as in
    /// [`Held`](crate::held::Held)).
    ///
    /// `dirty` is every held entry whose answers may have changed: each entry kept, each act whose conflict
    /// set (receipts and cuts) or void or closed state changed, each window answered, ascending and each once.
    /// `wake` and `foreign` are empty: a view registers no answers and holds no foreign rows.
    pub fn admit(&mut self, e: Entry<I, K, T>) -> Result<Admitted<I>, Refused> {
        if self.view.rec.contains_key(&e.id) || self.waiting.contains_key(&e.id) {
            return Err(Refused::Duplicate);
        }
        let mut visited = e.names.len();
        let mut lacks: Vec<I> = e.names.iter().filter(|n| !self.view.rec.contains_key(*n)).cloned().collect();
        lacks.sort();
        lacks.dedup();
        if !lacks.is_empty() {
            for n in &lacks {
                self.waiting_on.entry(n.clone()).or_default().push(e.id.clone());
            }
            self.waiting.insert(e.id.clone(), (e, lacks.len()));
            return Ok(Admitted {
                kept: Vec::new(),
                waiting: true,
                dirty: Vec::new(),
                visited,
                wake: Vec::new(),
                foreign: Vec::new(),
            });
        }
        let mut kept: Vec<I> = Vec::new();
        let mut dirty: BTreeSet<I> = BTreeSet::new();
        let mut ready: Vec<Entry<I, K, T>> = alloc::vec![e];
        while let Some(x) = ready.pop() {
            let id = x.id.clone();
            visited += self.keep(x, &mut dirty);
            kept.push(id.clone());
            if let Some(ws) = self.waiting_on.remove(&id) {
                for w in ws {
                    let done = match self.waiting.get_mut(&w) {
                        Some(e) => {
                            e.1 -= 1;
                            e.1 == 0
                        }
                        None => false,
                    };
                    if done {
                        let (e, _) = self.waiting.remove(&w).expect("present above");
                        visited += e.names.len();
                        ready.push(e);
                    }
                }
            }
        }
        Ok(Admitted {
            kept,
            waiting: false,
            dirty: dirty.into_iter().collect(),
            visited,
            wake: Vec::new(),
            foreign: Vec::new(),
        })
    }

    /// Admit entries in order; refusals are skipped. Every entry kept, in order, and the dirty set of all.
    pub fn admit_all(&mut self, es: impl IntoIterator<Item = Entry<I, K, T>>) -> Admitted<I> {
        let mut all = Admitted {
            kept: Vec::new(),
            waiting: false,
            dirty: Vec::new(),
            visited: 0,
            wake: Vec::new(),
            foreign: Vec::new(),
        };
        let mut dirty: BTreeSet<I> = BTreeSet::new();
        for e in es {
            if let Ok(a) = self.admit(e) {
                all.kept.extend(a.kept);
                all.visited += a.visited;
                dirty.extend(a.dirty);
            }
        }
        all.dirty = dirty.into_iter().collect();
        all
    }

    /// Mark entry `i` dirty, and the act it names as its own, when held.
    fn touch(view: &View<I, K, T>, dirty: &mut BTreeSet<I>, i: &I) {
        if let Some(a) = view.rec.get(i).and_then(conflict_key) {
            if view.rec.contains_key(a) {
                dirty.insert(a.clone());
            }
        }
        dirty.insert(i.clone());
    }

    /// Keep an entry whose every named id is held; returns the work done (the past term apart).
    fn keep(&mut self, x: Entry<I, K, T>, dirty: &mut BTreeSet<I>) -> usize {
        let mut visited = 1;
        let id = x.id.clone();
        let v = &mut self.view;
        // its past: one union over what it names
        let mut a: BTreeSet<I> = BTreeSet::new();
        let mut top = 0;
        for n in &x.names {
            a.insert(n.clone());
            a.extend(v.anc[n].iter().cloned());
            top = top.max(v.depth[n]);
        }
        v.anc.insert(id.clone(), a);
        v.depth.insert(id.clone(), 1 + top);
        if x.members.len() > MEMBERS_SCANNED {
            v.mem.insert(id.clone(), x.members.iter().cloned().collect());
        }
        if let Some(o) = conflict_key(&x) {
            let l = v.by_of.map().entry(o.clone()).or_default();
            let at = l.partition_point(|q| *q < id);
            l.insert(at, id.clone());
        }
        if x.kind == Kind::Answer {
            v.answered.set().extend(x.names.iter().cloned());
        }
        if let Some(h) = &x.head {
            self.by_head.entry(h.clone()).or_default().push(id.clone());
        }
        let (kind, head) = (x.kind, x.head.clone());
        if kind == Kind::Answer {
            for n in &x.names {
                if v.rec[n].kind == Kind::Open {
                    dirty.insert(n.clone());
                }
            }
        }
        v.rec.insert(id.clone(), x);
        let c = v.concl(&v.rec[&id]);
        v.c.insert(id.clone(), c);
        Self::touch(v, dirty, &id);
        // entries held before it that read it by id as their head without naming it: their conclusions, and
        // their receipts' (which read the act's head), are read again, and so is the void set
        let readers: Vec<I> =
            self.by_head.get(&id).map(|r| r.iter().filter(|q| **q != id).cloned().collect()).unwrap_or_default();
        let mut whole = !readers.is_empty();
        for r in &readers {
            let mut again: Vec<I> = alloc::vec![r.clone()];
            if v.rec[r].kind == Kind::Act {
                again.extend(v.by_of.of(r).filter(|k| v.rec[*k].kind == Kind::Ack).cloned());
            }
            for q in &again {
                visited += 1;
                let c = v.concl(&v.rec[q]);
                v.c.insert(q.clone(), c);
                Self::touch(v, dirty, q);
            }
        }
        // a head this node acknowledges, newly so or newly held: acts at heads in its past are closed, and
        // entries at older heads may be void
        let mut closing: Vec<I> = Vec::new();
        if kind == Kind::ReaderAck && c {
            if let Some(h) = &head {
                if v.acked.insert(h.clone()) && v.anc.contains_key(h) {
                    closing.push(h.clone());
                }
            }
        }
        if v.acked.contains(&id) && !closing.contains(&id) {
            closing.push(id.clone());
        }
        for h in &closing {
            whole = true;
            for y in &v.anc[h] {
                visited += 1;
                for a in self.by_head.get(y).into_iter().flatten() {
                    visited += 1;
                    if v.rec[a].kind == Kind::Act {
                        dirty.insert(a.clone());
                    }
                }
            }
        }
        if whole {
            let mut order: Vec<I> = v.rec.keys().cloned().collect();
            order.sort_by_key(|i| v.depth[i]);
            let nv = v.void_set(&order);
            visited += order.len();
            let changed: Vec<I> = nv.symmetric_difference(&v.v).cloned().collect();
            v.v = nv;
            for i in &changed {
                Self::touch(v, dirty, i);
            }
        } else if Self::void_now(v, &id) {
            v.v.insert(id); // dirty already holds it and its act
        }
        visited
    }

    /// Whether newly kept entry `x` is void, read as [`View::new`]'s pass reads it: in (depth, id) order, by
    /// the heads before it in that order. Only `x` is new, and it is no held entry's head.
    fn void_now(v: &View<I, K, T>, x: &I) -> bool {
        let r = &v.rec[x];
        if !matches!(r.kind, Kind::Act | Kind::Cut | Kind::Seat) || !v.c[x] {
            return false;
        }
        if v.reading == Reading::Narrow && r.kind != Kind::Seat {
            return false;
        }
        let me = (v.depth[x], x);
        v.behind(r, &v.acked) || v.heads_of(r).iter().any(|h| v.v.contains(h) && (v.depth[h], h) < me)
    }

    /// The held ids in fold order: by depth, then id (the order [`View::new`] concludes and voids them in).
    /// Each with its entry and conclusion, read in one pass over the maps (they share their keys, ascending).
    fn order(&self) -> Vec<Held1<'_, I, K, T>> {
        let v = &self.view;
        debug_assert!(v.rec.len() == v.depth.len() && v.rec.len() == v.c.len());
        let mut o: Vec<(usize, Held1<'_, I, K, T>)> =
            v.rec.iter().zip(v.depth.values()).zip(v.c.values()).map(|(((i, e), d), c)| (*d, (i, e, *c))).collect();
        o.sort_by_key(|x| x.0); // stable: ids stay ascending within a depth
        o.into_iter().map(|x| x.1).collect()
    }
}

impl<I: Ord + Clone + Encode, K: Ord + Clone + Encode, T: Ord + Copy + Add<Output = T>> HeldView<I, K, T> {
    /// The checkpoint: kernel-side state only, ids and keys through [`Encode`] (the layout is in the module
    /// documentation). Canonical: two equal views give the same bytes, whatever order their entries came in.
    pub fn checkpoint(&self) -> Vec<u8> {
        let v = &self.view;
        let mut out = Vec::new();
        CHECKPOINT_VERSION.encode(&mut out);
        out.push(match v.reading {
            Reading::Broad => 0,
            Reading::Narrow => 1,
        });
        out.push(v.say as u8);
        v.own.encode(&mut out);
        let order = self.order();
        (order.len() as u64).encode(&mut out);
        for (i, e, c) in order {
            i.encode(&mut out);
            let mut f = 0u8;
            for (on, bit) in [
                (e.stub, STUB),
                (e.concl, CONCL),
                (e.final_counts.is_some(), FINAL),
                (e.final_counts == Some(true), FINAL_YES),
                (e.settled_stub, SETTLED),
                (e.dropped, DROPPED),
                (c, CONCLUDED),
            ] {
                if on {
                    f |= bit;
                }
            }
            out.push(f);
            put_list(&mut out, &e.ackers);
            put_list(&mut out, &e.acks);
        }
        let acked: Vec<I> = v.acked.iter().cloned().collect();
        put_list(&mut out, &acked);
        let waiting: Vec<I> = self.waiting.keys().cloned().collect();
        put_list(&mut out, &waiting);
        out
    }

    /// The view a checkpoint was written from, its rows re-attached by id from the caller's store: `rows(id)`
    /// gives the entry with that id (its row content; any stub fields it carries are replaced by the
    /// checkpoint's, and a stub's signatures are dropped, as [`head::purge`](crate::head::purge) drops them).
    ///
    /// Refused, never partial: an unknown version, bytes that end early, bytes other than those the resumed view
    /// writes (re-encoded and compared), an id the checkpoint or a resumed row names that `rows` does not supply
    /// ([`CheckpointError::Missing`]), or a row that concludes otherwise than the checkpoint states
    /// ([`CheckpointError::Differs`]).
    pub fn resume(bytes: &[u8], rows: impl Fn(&I) -> Option<Entry<I, K, T>>) -> Result<Self, CheckpointError<I>> {
        let ver = u16::from_be_bytes(bytes.get(..2).ok_or(CheckpointError::Truncated)?.try_into().expect("two bytes"));
        if ver != CHECKPOINT_VERSION {
            return Err(CheckpointError::Version(ver));
        }
        let mut cur = Cur { b: bytes, at: 2 };
        let reading = match cur.take::<u8>()? {
            0 => Reading::Broad,
            1 => Reading::Narrow,
            _ => return Err(CheckpointError::NotCanonical),
        };
        let say = match cur.take::<u8>()? {
            0 => false,
            1 => true,
            _ => return Err(CheckpointError::NotCanonical),
        };
        let own: K = cur.take()?;
        let n: u64 = cur.take()?;
        let mut stated: Vec<Stated<I, K>> = Vec::new();
        for _ in 0..n {
            let id: I = cur.take()?;
            let flags: u8 = cur.take()?;
            let ackers: Vec<K> = cur.list()?;
            let acks: Vec<I> = cur.list()?;
            stated.push(Stated { id, flags, ackers, acks });
        }
        let acked: Vec<I> = cur.list()?;
        let waiting: Vec<I> = cur.list()?;
        if cur.at != bytes.len() {
            return Err(CheckpointError::NotCanonical);
        }
        // the held ids, each once, and where each comes in the fold order
        let mut pos: BTreeMap<&I, usize> = BTreeMap::new();
        for (k, s) in stated.iter().enumerate() {
            if pos.insert(&s.id, k).is_some() || s.flags & 0x80 != 0 {
                return Err(CheckpointError::NotCanonical);
            }
        }
        let mut view = View {
            own,
            reading,
            say,
            rec: BTreeMap::new(),
            anc: BTreeMap::new(),
            depth: BTreeMap::new(),
            c: BTreeMap::new(),
            v: BTreeSet::new(),
            scanned: SCANNED,
            by_of: ByOf::Sorted(Vec::new()),
            answered: Answered::Sorted(Vec::new()),
            mem: BTreeMap::new(),
            acked: BTreeSet::new(),
        };
        // the entries, in fold order: each names only entries before it
        for (k, s) in stated.iter().enumerate() {
            let mut e = rows(&s.id).filter(|e| e.id == s.id).ok_or_else(|| CheckpointError::Missing(s.id.clone()))?;
            e.stub = s.flags & STUB != 0;
            e.concl = s.flags & CONCL != 0;
            e.final_counts = (s.flags & FINAL != 0).then_some(s.flags & FINAL_YES != 0);
            e.settled_stub = s.flags & SETTLED != 0;
            e.dropped = s.flags & DROPPED != 0;
            e.ackers = s.ackers.clone();
            e.acks = s.acks.clone();
            if e.stub {
                e.sigs = Vec::new();
            }
            let mut a: BTreeSet<I> = BTreeSet::new();
            let mut top = 0;
            for nm in &e.names {
                match pos.get(nm) {
                    None => return Err(CheckpointError::Missing(nm.clone())),
                    Some(&p) if p >= k => return Err(CheckpointError::NotCanonical),
                    Some(_) => {}
                }
                a.insert(nm.clone());
                a.extend(view.anc[nm].iter().cloned());
                top = top.max(view.depth[nm]);
            }
            if e.members.len() > MEMBERS_SCANNED {
                view.mem.insert(s.id.clone(), e.members.iter().cloned().collect());
            }
            view.anc.insert(s.id.clone(), a);
            view.depth.insert(s.id.clone(), 1 + top);
            view.rec.insert(s.id.clone(), e);
        }
        // conclusions, read once every entry is held (an act reads the members at its head by id)
        for s in &stated {
            let c = view.concl(&view.rec[&s.id]);
            if c != (s.flags & CONCLUDED != 0) {
                return Err(CheckpointError::Differs(s.id.clone()));
            }
            view.c.insert(s.id.clone(), c);
        }
        view.acked = view.acked_of();
        let stated_acked: BTreeSet<I> = acked.into_iter().collect();
        if let Some(h) = view.acked.symmetric_difference(&stated_acked).next() {
            return Err(CheckpointError::Differs(h.clone()));
        }
        let order: Vec<I> = stated.iter().map(|s| s.id.clone()).collect();
        view.v = view.void_set(&order);
        let mut hv = Self::from_view(view);
        for w in &waiting {
            let e = rows(w).filter(|e| e.id == *w).ok_or_else(|| CheckpointError::Missing(w.clone()))?;
            match hv.admit(e) {
                Ok(a) if a.waiting => {}
                _ => return Err(CheckpointError::NotCanonical),
            }
        }
        // decode re-encodes and compares: one view, one encoding
        if hv.checkpoint() != bytes {
            return Err(CheckpointError::NotCanonical);
        }
        Ok(hv)
    }
}

/// What a view says about one held entry, for [`differential`]: its conclusion and void, and, for an act, every
/// answer about it; for a window, its state at each instant.
type Says<I, K> = (bool, bool, Option<(bool, bool, bool, Vec<K>, bool, BTreeMap<K, Vec<I>>)>, Vec<WindowState>);

fn says<I: Ord + Clone, K: Ord + Clone, T: Ord + Copy + Add<Output = T>>(
    v: &View<I, K, T>,
    i: &I,
    nows: &[T],
) -> Says<I, K> {
    let r = &v.rec[i];
    let act = (r.kind == Kind::Act)
        .then(|| (v.counts_at(i), v.carried(i), v.settled(i), v.missing(i), v.closed_for_me(i), v.receipts(i)));
    let win = if r.kind == Kind::Open { nows.iter().map(|t| v.window(i, *t)).collect() } else { Vec::new() };
    (v.c[i], v.v.contains(i), act, win)
}

/// Admit `order` one entry at a time into a [`HeldView`] over `store` and, after every admission, compare it
/// with [`View::new`]`(store, offered so far, own, reading, say)`: every answer at each of `nows`, the
/// conclusions, void set, acknowledged heads, tips, and every act's receipts, counts, carriage, settlement,
/// missing members and closure. A refused admission must change nothing, and every held entry whose answers
/// changed must be in [`Admitted::dirty`]. Quadratic or worse; for tests, the caller's included. Precondition:
/// entries with the same id are the same entry (ids are digests), and `store` is closed under the door.
pub fn differential<I: Ord + Clone, K: Ord + Clone, T: Ord + Copy + Add<Output = T>>(
    store: &Store<I, K, T>,
    own: K,
    reading: Reading,
    say: bool,
    order: &[Entry<I, K, T>],
    nows: &[T],
) -> Result<(), Mismatch<I>> {
    let fail = |prefix: usize, id: Option<&I>, what: &'static str| Mismatch { prefix, id: id.cloned(), what };
    let mut h = HeldView::new(store, own.clone(), reading, say);
    let mut before: BTreeMap<I, Says<I, K>> = h.view.rec.keys().map(|i| (i.clone(), says(&h.view, i, nows))).collect();
    for k in 0..order.len() {
        let prior = h.clone();
        let dirty = match h.admit(order[k].clone()) {
            Err(_) => {
                if !(prior == h) {
                    return Err(fail(k + 1, Some(&order[k].id), "refused but changed"));
                }
                Vec::new()
            }
            Ok(a) => {
                let mut fresh: Vec<&I> = h.view.rec.keys().filter(|i| !prior.view.rec.contains_key(*i)).collect();
                let mut kept: Vec<&I> = a.kept.iter().collect();
                fresh.sort();
                kept.sort();
                if fresh != kept {
                    return Err(fail(k + 1, Some(&order[k].id), "kept is not the entries newly held"));
                }
                if a.dirty.windows(2).any(|w| w[0] >= w[1]) {
                    return Err(fail(k + 1, Some(&order[k].id), "dirty not ascending, each once"));
                }
                a.dirty
            }
        };
        let full = View::new(store, &order[..=k], own.clone(), reading, say);
        let v = &h.view;
        if v.rec != full.rec {
            return Err(fail(k + 1, None, "held entries"));
        }
        if v.c != full.c {
            return Err(fail(k + 1, None, "conclusions"));
        }
        if v.v != full.v {
            return Err(fail(k + 1, None, "void"));
        }
        if v.acked != full.acked {
            return Err(fail(k + 1, None, "acknowledged heads"));
        }
        if v.tips() != full.tips() {
            return Err(fail(k + 1, None, "tips"));
        }
        for t in nows {
            if v.answers(*t) != full.answers(*t) {
                return Err(fail(k + 1, None, "answers"));
            }
        }
        let mut after: BTreeMap<I, Says<I, K>> = BTreeMap::new();
        for i in v.rec.keys() {
            let s = says(v, i, nows);
            if s != says(&full, i, nows) {
                return Err(fail(k + 1, Some(i), "an answer about a held entry"));
            }
            if before.get(i) != Some(&s) && dirty.binary_search(i).is_err() {
                return Err(fail(k + 1, Some(i), "an answer changed and the entry is not dirty"));
            }
            after.insert(i.clone(), s);
        }
        before = after;
    }
    Ok(())
}
