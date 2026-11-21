//! The only order is what rows name (KERNEL.md section 2; CC 2.7.2), and the closure over it
//! (KERNEL.md section 4, last operator): a row's past, whether two rows are concurrent, and the frontier
//! of a set. `kernel_lib.ancestors`, `closure`, `concurrent`, `frontier` and `past`.
//!
//! A [`Graph`] is built over a set of rows in which every row names only rows of the set (a kept set always
//! is one). A named digest with no row in the set is followed no further and is not an index here; the
//! Python model keeps such a digest in the ancestor set, and since no row carries it no answer differs.

use crate::Row;
use alloc::collections::BTreeMap;
use core::cell::{Cell, OnceCell};

/// How many rows a point question of the past searches before it computes and keeps the whole past.
const SEARCH_BUDGET: usize = 256;
/// A level not yet known, while the walk in [`Graph::new`] runs.
const UNSET: u32 = u32::MAX;
/// A row on the walk's stack in [`Graph::new`]: expanded, its level not yet known.
const ON: u32 = u32::MAX - 1;
/// The level of a row that waits on a cycle of names (and never concludes); below [`ON`] and [`UNSET`], and
/// above every level a row of a kept set can have.
const WAITING: u32 = u32::MAX - 2;
/// Up to how many rows [`Graph::frontier`] compares pairwise before it walks down from all of them at once.
const FRONTIER_PAIRWISE: usize = 16;
use alloc::vec;
use alloc::vec::Vec;

/// A set of row indices.
///
/// Two forms, one set: **dense**, a bit per index, for the sets a walk builds and reads at once; and
/// **compact**, the sorted segments of a dense set (runs of whole 64-index words all present, and single words
/// holding some), for a set that is kept. A [`Held`](crate::held::Held) view keeps its rows' pasts compact: rows are
/// indexed in the order the door admitted them, so a past is mostly a run of whole words below the row and a few
/// words near it, and held compact it costs about its number of distinct words rather than `n / 64` words.
/// Equality and hashing read the set, not its form.
#[derive(Clone, Debug)]
pub struct Bits {
    r: Repr,
}

#[derive(Clone, Debug)]
enum Repr {
    /// One bit per index; word `k` holds indices `64 k .. 64 k + 64`.
    Dense(Vec<u64>),
    /// Ascending, disjoint, non-adjacent runs and words; no word is zero or all ones.
    Compact(Vec<Seg>),
}

/// A segment of a compact set, by word index.
#[derive(Clone, Copy, Debug)]
enum Seg {
    /// Words `at .. at + len`, every bit set.
    Ones { at: u32, len: u32 },
    /// Word `at`, these bits.
    Word { at: u32, w: u64 },
}

impl Seg {
    #[inline]
    fn at(self) -> usize {
        match self {
            Seg::Ones { at, .. } | Seg::Word { at, .. } => at as usize,
        }
    }
    #[inline]
    fn end(self) -> usize {
        match self {
            Seg::Ones { at, len } => (at + len) as usize,
            Seg::Word { at, .. } => at as usize + 1,
        }
    }
}

/// The non-zero words of a set, ascending, with their indices.
enum Words<'b> {
    Dense(core::iter::Enumerate<core::slice::Iter<'b, u64>>),
    Compact { segs: core::slice::Iter<'b, Seg>, run: core::ops::Range<usize> },
}

impl Iterator for Words<'_> {
    type Item = (usize, u64);
    fn next(&mut self) -> Option<(usize, u64)> {
        match self {
            Words::Dense(it) => it.find(|(_, w)| **w != 0).map(|(k, w)| (k, *w)),
            Words::Compact { segs, run } => {
                if let Some(k) = run.next() {
                    return Some((k, !0));
                }
                match segs.next()? {
                    Seg::Word { at, w } => Some((*at as usize, *w)),
                    Seg::Ones { at, len } => {
                        *run = (*at as usize + 1)..(*at + *len) as usize;
                        Some((*at as usize, !0))
                    }
                }
            }
        }
    }
}

impl PartialEq for Bits {
    fn eq(&self, o: &Bits) -> bool {
        self.words().eq(o.words())
    }
}
impl Eq for Bits {}
impl core::hash::Hash for Bits {
    fn hash<H: core::hash::Hasher>(&self, h: &mut H) {
        for (k, w) in self.words() {
            k.hash(h);
            w.hash(h);
        }
    }
}

impl Bits {
    /// The empty set over `n` indices (dense).
    pub fn new(n: usize) -> Self {
        Bits { r: Repr::Dense(vec![0; n.div_ceil(64)]) }
    }
    /// Whether `i` is in the set.
    #[inline]
    pub fn has(&self, i: usize) -> bool {
        let k = i / 64;
        let w = match &self.r {
            Repr::Dense(w) => w.get(k).copied().unwrap_or(0),
            Repr::Compact(s) => {
                let at = s.partition_point(|x| x.at() <= k);
                match at.checked_sub(1).map(|j| s[j]) {
                    Some(Seg::Ones { at, len }) if k < (at + len) as usize => !0,
                    Some(Seg::Word { at, w }) if k == at as usize => w,
                    _ => 0,
                }
            }
        };
        (w >> (i % 64)) & 1 == 1
    }
    /// Add `i`. A dense set panics on an index at or past the `n` it was made for, as it always has; a compact
    /// set becomes dense first.
    #[inline]
    pub fn set(&mut self, i: usize) {
        if let Repr::Compact(_) = self.r {
            self.densify(i / 64 + 1);
        }
        let Repr::Dense(w) = &mut self.r else { unreachable!("made dense above") };
        w[i / 64] |= 1 << (i % 64);
    }
    /// Add every index of `o` below this set's size (a dense set's `n`; a compact one grows to hold `o`).
    pub fn union(&mut self, o: &Bits) {
        if let Repr::Compact(_) = self.r {
            let need = self.words_len().max(o.words_len());
            self.densify(need);
        }
        let Repr::Dense(w) = &mut self.r else { unreachable!("made dense above") };
        match &o.r {
            Repr::Dense(ow) => {
                for (a, b) in w.iter_mut().zip(ow.iter()) {
                    *a |= *b;
                }
            }
            Repr::Compact(segs) => {
                let n = w.len();
                for s in segs {
                    match *s {
                        Seg::Word { at, w: x } => {
                            if let Some(a) = w.get_mut(at as usize) {
                                *a |= x;
                            }
                        }
                        Seg::Ones { at, len } => {
                            let (a, e) = ((at as usize).min(n), ((at + len) as usize).min(n));
                            w[a..e].iter_mut().for_each(|x| *x = !0);
                        }
                    }
                }
            }
        }
    }
    /// The number of indices in the set.
    pub fn len(&self) -> usize {
        match &self.r {
            Repr::Dense(w) => w.iter().map(|x| x.count_ones() as usize).sum(),
            Repr::Compact(s) => s
                .iter()
                .map(|x| match *x {
                    Seg::Ones { len, .. } => 64 * len as usize,
                    Seg::Word { w, .. } => w.count_ones() as usize,
                })
                .sum(),
        }
    }
    /// Whether the set is empty.
    pub fn is_empty(&self) -> bool {
        match &self.r {
            Repr::Dense(w) => w.iter().all(|x| *x == 0),
            Repr::Compact(s) => s.is_empty(),
        }
    }
    /// The indices, ascending.
    pub fn iter(&self) -> impl Iterator<Item = usize> + '_ {
        // one step per index held (lowest set bit first), not one per bit of the word
        self.words().flat_map(|(k, x)| {
            let mut x = x;
            core::iter::from_fn(move || {
                if x == 0 {
                    return None;
                }
                let b = x.trailing_zeros() as usize;
                x &= x - 1;
                Some(k * 64 + b)
            })
        })
    }
    /// The same set, held compact when that is smaller than dense.
    pub fn compact(self) -> Bits {
        let Repr::Dense(w) = &self.r else { return self };
        let mut segs: Vec<Seg> = Vec::new();
        for (k, &x) in w.iter().enumerate() {
            if x == 0 {
                continue;
            }
            if x == !0 {
                if let Some(Seg::Ones { at, len }) = segs.last_mut() {
                    if (*at + *len) as usize == k {
                        *len += 1;
                        continue;
                    }
                }
                segs.push(Seg::Ones { at: k as u32, len: 1 });
            } else {
                segs.push(Seg::Word { at: k as u32, w: x });
            }
        }
        // a segment is two words' worth of bytes: compact only when that is fewer
        if segs.len() * core::mem::size_of::<Seg>() < w.len() * 8 {
            segs.shrink_to_fit();
            Bits { r: Repr::Compact(segs) }
        } else {
            self
        }
    }
    /// The bytes this set holds on the heap.
    pub fn heap_bytes(&self) -> usize {
        match &self.r {
            Repr::Dense(w) => w.capacity() * 8,
            Repr::Compact(s) => s.capacity() * core::mem::size_of::<Seg>(),
        }
    }
    fn words(&self) -> Words<'_> {
        match &self.r {
            Repr::Dense(w) => Words::Dense(w.iter().enumerate()),
            Repr::Compact(s) => Words::Compact { segs: s.iter(), run: 0..0 },
        }
    }
    /// The number of words a dense form of this set needs.
    fn words_len(&self) -> usize {
        match &self.r {
            Repr::Dense(w) => w.len(),
            Repr::Compact(s) => s.last().map_or(0, |x| x.end()),
        }
    }
    fn densify(&mut self, at_least: usize) {
        let mut w = vec![0u64; self.words_len().max(at_least)];
        for (k, x) in self.words() {
            w[k] = x;
        }
        self.r = Repr::Dense(w);
    }
}

/// What computing pasts has cost a graph so far: the price of a held view's window, measured on the caller's own
/// rows ([`Held::set_past_window`](crate::held::Held::set_past_window)).
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct PastCounts {
    /// Pasts computed.
    pub computed: u64,
    /// Of those, pasts computed again after the window dropped them.
    pub recomputed: u64,
    /// Rows a walk expanded one at a time because their own past was not kept. With every past kept, a walk takes
    /// each named row's past whole and this stays near zero; a window too narrow for the rows admitted shows here
    /// first, because a new row naming an old one walks the old row's past.
    pub walked: u64,
}

/// A set of rows with the closure over what they name. Indices follow the order the rows were given in.
///
/// Building it is linear in the rows and the names: it records each row's held names and its level (one
/// more than the greatest level among the rows it names). A row's past is computed when an answer first
/// asks for it and kept. A row can be in the past of another only if
/// its level is lower, so most questions of concurrency are answered without a past at all.
pub struct Graph<'a, R: Row> {
    rows: Vec<&'a R>,
    /// Each id with its row's index, sorted by id: the index of an id is a binary search in one buffer.
    index: Vec<(R::Id, usize)>,
    /// What each row names, as one buffer: row i names `names[off[i]..off[i + 1]]`, ascending.
    off: Vec<usize>,
    names: Vec<usize>,
    /// Each row's level; [`WAITING`] for a row on a cycle of names or naming one (no kept set holds it).
    level: Vec<u32>,
    anc: Vec<OnceCell<Bits>>,
    /// Rows added by [`Graph::push`] after building, by id. Empty for a graph built whole by [`Graph::new`].
    pushed: BTreeMap<R::Id, usize>,
    /// Keep each computed past compact ([`Bits::compact`]). Off for a graph built by [`Graph::new`], so every
    /// existing caller keeps dense pasts as before; a [`Held`](crate::held::Held) view turns it on.
    compact: bool,
    /// Rows whose past was dropped by [`forget_past`](Graph::forget_past) and not computed since.
    forgotten: Vec<bool>,
    /// Pasts computed, and of those, pasts computed again after being dropped.
    computed: Cell<u64>,
    recomputed: Cell<u64>,
    /// Rows a past's walk expanded one by one because their own past was not kept.
    walked: Cell<u64>,
}

impl<R: crate::Dated> Graph<'_, R> {
    /// The instant row `id` states ([`Dated::asserted_at`](crate::Dated::asserted_at)), when it is held and
    /// states one: the instant every `_at` answer reads at.
    pub fn instant_of(&self, id: &R::Id) -> Option<R::Instant> {
        self.idx(id).and_then(|i| self.row(i).asserted_at())
    }
}

impl<R: Row> Clone for Graph<'_, R> {
    fn clone(&self) -> Self {
        Graph {
            rows: self.rows.clone(),
            index: self.index.clone(),
            off: self.off.clone(),
            names: self.names.clone(),
            level: self.level.clone(),
            anc: self.anc.clone(),
            pushed: self.pushed.clone(),
            compact: self.compact,
            forgotten: self.forgotten.clone(),
            computed: self.computed.clone(),
            recomputed: self.recomputed.clone(),
            walked: self.walked.clone(),
        }
    }
}

impl<'a, R: Row> Graph<'a, R> {
    /// Build the index. A later row with an id already present is ignored.
    ///
    /// Precondition: the rows are closed under [`kept`](crate::layers::kept): every row names only rows of
    /// the set (a named id with no row is followed no further), and no chain of names returns to a row. Rows
    /// with digests for ids cannot form such a cycle. If some do, building still ends: a row on a cycle, and
    /// every row naming one, is [`waiting`](Graph::waiting), as `kept` would never have kept it, and
    /// [`conclude`](crate::layers::conclude) concludes nothing for it.
    pub fn new(rows: impl IntoIterator<Item = &'a R>) -> Self {
        let mut v: Vec<&'a R> = rows.into_iter().collect();
        // the ids sorted, each with the first position it was given at
        let mut index: Vec<(R::Id, usize)> = v.iter().enumerate().map(|(p, r)| (r.id().clone(), p)).collect();
        index.sort_unstable();
        index.dedup_by(|b, a| a.0 == b.0);
        if index.len() < v.len() {
            // a later row with an id already present is ignored: keep each first, in the order given
            let mut first = vec![false; v.len()];
            for (_, p) in &index {
                first[*p] = true;
            }
            let mut at = vec![0usize; v.len()];
            let mut k = 0;
            for p in 0..v.len() {
                at[p] = k;
                if first[p] {
                    v[k] = v[p];
                    k += 1;
                }
            }
            v.truncate(k);
            for e in index.iter_mut() {
                e.1 = at[e.1];
            }
        }
        let n = v.len();
        // a level is below WAITING; so is the number of rows
        assert!(n < WAITING as usize, "more rows than a level can count");
        let find = |id: &R::Id| index.binary_search_by(|e| e.0.cmp(id)).ok().map(|k| index[k].1);
        let mut off: Vec<usize> = Vec::with_capacity(n + 1);
        let mut names: Vec<usize> = Vec::with_capacity(v.iter().map(|r| r.names().len()).sum());
        // a row naming its own id is a cycle of one: it waits, as `kept` would never keep it
        let mut level = vec![UNSET; n];
        off.push(0);
        for (i, r) in v.iter().enumerate() {
            let s = names.len();
            names.extend(r.names().iter().filter_map(find).filter(|&p| {
                if p == i {
                    level[i] = WAITING;
                }
                p != i
            }));
            names[s..].sort_unstable();
            let mut w = s;
            for k in s..names.len() {
                if w == s || names[k] != names[w - 1] {
                    names[w] = names[k];
                    w += 1;
                }
            }
            names.truncate(w);
            off.push(names.len());
        }
        // levels, by a walk down what rows name: a row's level is known once those of the rows it names are.
        // A row is ON the walk's stack from when it is first expanded until its level is known. When its turn
        // comes again, every row it named and pushed is done, so a named row still ON is below it on the stack:
        // a cycle of names. Such a row, and every row naming a row that waits, WAITS.
        let mut stack: Vec<usize> = Vec::new();
        for s in 0..n {
            if level[s] != UNSET {
                continue;
            }
            stack.push(s);
            while let Some(&i) = stack.last() {
                let named = &names[off[i]..off[i + 1]];
                if level[i] == UNSET {
                    let before = stack.len();
                    for &p in named {
                        if level[p] == UNSET {
                            stack.push(p);
                        }
                    }
                    if stack.len() > before {
                        level[i] = ON; // its turn comes again once what it pushed is done
                        continue;
                    }
                } else if level[i] != ON {
                    stack.pop(); // done already (pushed twice)
                    continue;
                }
                // every row i names is done, or ON below it on the stack: a cycle of names
                let (mut top, mut waits) = (0, false);
                for &p in named {
                    let l = level[p];
                    if l >= WAITING {
                        waits = true; // a named row on the stack (a back edge), or waiting
                    } else if l > top {
                        top = l;
                    }
                }
                level[i] = if waits { WAITING } else { 1 + top };
                stack.pop();
            }
        }
        let anc = (0..n).map(|_| OnceCell::new()).collect();
        Graph {
            rows: v,
            index,
            off,
            names,
            level,
            anc,
            pushed: BTreeMap::new(),
            compact: false,
            forgotten: Vec::new(),
            computed: Cell::new(0),
            recomputed: Cell::new(0),
            walked: Cell::new(0),
        }
    }

    /// Room for `rows` more rows naming `names` ids in all, so the next [`push`](Graph::push)es do not grow
    /// a buffer.
    pub fn reserve(&mut self, rows: usize, names: usize) {
        self.rows.reserve(rows);
        self.off.reserve(rows);
        self.level.reserve(rows);
        self.anc.reserve(rows);
        self.names.reserve(names);
    }

    /// Add one row whose every named id is already a row here (the door's order: a row is held only once
    /// what it names is held). Returns its index, or `None`, changing nothing, when the id is already present
    /// or a named id is not. No past, level or answer about an earlier row changes: an earlier row cannot name
    /// it. Linear in what the row names, plus the log of the rows for each.
    pub fn push(&mut self, r: &'a R) -> Option<usize> {
        if self.idx(r.id()).is_some() {
            return None;
        }
        let mut named: Vec<usize> = Vec::with_capacity(r.names().len());
        for n in r.names() {
            named.push(self.idx(n)?);
        }
        named.sort_unstable();
        named.dedup();
        let i = self.rows.len();
        assert!(i + 1 < WAITING as usize, "more rows than a level can count");
        let mut top = 0;
        let mut waits = false;
        for &p in &named {
            let l = self.level[p];
            if l >= WAITING {
                waits = true;
            } else if l > top {
                top = l;
            }
        }
        self.names.extend_from_slice(&named);
        self.off.push(self.names.len());
        self.level.push(if waits { WAITING } else { 1 + top });
        self.anc.push(OnceCell::new());
        self.rows.push(r);
        self.pushed.insert(r.id().clone(), i);
        Some(i)
    }

    /// The number of rows.
    pub fn len(&self) -> usize {
        self.rows.len()
    }
    /// Whether there are no rows.
    pub fn is_empty(&self) -> bool {
        self.rows.is_empty()
    }
    /// The row at an index.
    pub fn row(&self, i: usize) -> &'a R {
        self.rows[i]
    }
    /// Every row, in index order.
    pub fn rows(&self) -> &[&'a R] {
        &self.rows
    }
    /// The index of a row id, when the row is in the set.
    pub fn idx(&self, id: &R::Id) -> Option<usize> {
        match self.index.binary_search_by(|e| e.0.cmp(id)) {
            Ok(k) => Some(self.index[k].1),
            Err(_) if self.pushed.is_empty() => None,
            Err(_) => self.pushed.get(id).copied(),
        }
    }
    /// The held rows row `i` names directly.
    #[inline]
    pub fn named(&self, i: usize) -> &[usize] {
        &self.names[self.off[i]..self.off[i + 1]]
    }
    /// Whether row `i` is on a cycle of names, or names a row that is: a row no kept set holds, which
    /// concludes nothing. Its level and the questions of its past answer nothing meaningful.
    pub fn waiting(&self, i: usize) -> bool {
        self.level[i] == WAITING
    }
    /// One more than the greatest level among the rows `i` names: a row's past holds only lower levels.
    pub fn level(&self, i: usize) -> u32 {
        self.level[i]
    }
    /// The past of row `i`: every row it names, and theirs. Computed when first asked, by a walk that takes
    /// whole any past already known, and kept; the pasts it passes through are not kept.
    pub fn ancestors(&self, i: usize) -> &Bits {
        if let Some(b) = self.anc[i].get() {
            return b;
        }
        // a walk down what rows name, taking whole any past already known; only i's past is kept
        let mut b = Bits::new(self.len());
        let mut todo: Vec<usize> = self.named(i).to_vec();
        while let Some(p) = todo.pop() {
            if b.has(p) {
                continue;
            }
            b.set(p);
            match self.anc[p].get() {
                Some(pa) => b.union(pa),
                None => {
                    self.walked.set(self.walked.get() + 1);
                    todo.extend(self.named(p).iter().copied().filter(|&q| !b.has(q)))
                }
            }
        }
        self.computed.set(self.computed.get() + 1);
        if self.forgotten.get(i).copied().unwrap_or(false) {
            // counted once per drop: the flag clears when the window drops it again (forget_past sets it)
            self.recomputed.set(self.recomputed.get() + 1);
        }
        let _ = self.anc[i].set(if self.compact { b.compact() } else { b });
        self.anc[i].get().expect("computed above")
    }
    /// Keep the pasts computed from now on compact where that is smaller (a [`Held`](crate::held::Held) view's
    /// graph). Answers do not change.
    pub(crate) fn set_compact(&mut self, on: bool) {
        self.compact = on;
    }
    /// Whether row `i`'s past is computed and kept.
    pub(crate) fn has_past(&self, i: usize) -> bool {
        self.anc[i].get().is_some()
    }
    /// Drop the kept past of row `i`; the next question that needs it computes it again. No answer changes.
    pub(crate) fn forget_past(&mut self, i: usize) {
        if self.anc[i].take().is_some() {
            if self.forgotten.len() <= i {
                self.forgotten.resize(i + 1, false);
            }
            self.forgotten[i] = true;
        }
    }
    /// What computing pasts has cost so far ([`PastCounts`]).
    pub fn past_counts(&self) -> PastCounts {
        PastCounts { computed: self.computed.get(), recomputed: self.recomputed.get(), walked: self.walked.get() }
    }
    /// The bytes the pasts computed so far hold on the heap (each past is kept compact; see [`Bits`]).
    pub fn past_bytes(&self) -> usize {
        self.anc.iter().filter_map(|c| c.get()).map(Bits::heap_bytes).sum()
    }
    /// Whether row `a` is in the past of row `b`.
    #[inline]
    pub fn in_past(&self, a: usize, b: usize) -> bool {
        if self.level[a] >= self.level[b] {
            return false;
        }
        if self.named(b).binary_search(&a).is_ok() {
            return true;
        }
        if let Some(pb) = self.anc[b].get() {
            return pb.has(a);
        }
        // a short search down from b through rows above a's level only, taking a known past whole; past
        // SEARCH_BUDGET rows it stops and b's past is computed and kept instead
        let la = self.level[a];
        let mut budget = SEARCH_BUDGET;
        let mut seen = Bits::new(self.len());
        let mut todo: Vec<usize> = alloc::vec![b];
        while let Some(x) = todo.pop() {
            for &p in self.named(x) {
                if p == a {
                    return true;
                }
                if self.level[p] <= la || seen.has(p) {
                    continue;
                }
                seen.set(p);
                budget -= 1;
                if budget == 0 {
                    return self.ancestors(b).has(a);
                }
                match self.anc[p].get() {
                    Some(pp) if pp.has(a) => return true,
                    Some(_) => {}
                    None => todo.push(p),
                }
            }
        }
        false
    }
    /// Whether id `a` is in the past of row `b`. An id with no row here is in no past.
    pub fn id_in_past(&self, a: &R::Id, b: usize) -> bool {
        self.idx(a).is_some_and(|a| self.in_past(a, b))
    }
    /// Neither names the other, through any chain.
    #[inline]
    pub fn concurrent(&self, a: usize, b: usize) -> bool {
        a != b && !self.in_past(a, b) && !self.in_past(b, a)
    }
    /// The rows of `of` that no other row of `of` has in its past, in the order given.
    ///
    /// A few rows are compared pairwise. For more, one walk goes down from all of them at once, through rows
    /// no lower than the lowest of them (a row's past holds only lower levels), and a row of `of` the walk
    /// reaches is in the past of another: linear in the rows walked, not quadratic in `of`.
    pub fn frontier(&self, of: &[usize]) -> Vec<usize> {
        if of.len() <= FRONTIER_PAIRWISE {
            return of.iter().copied().filter(|&r| !of.iter().any(|&q| self.in_past(r, q))).collect();
        }
        let low = of.iter().map(|&i| self.level[i]).min().unwrap_or(0);
        let mut below = Bits::new(self.len());
        let mut todo: Vec<usize> = Vec::new();
        for &q in of {
            todo.push(q);
            while let Some(x) = todo.pop() {
                for &p in self.named(x) {
                    if self.level[p] < low || below.has(p) {
                        continue;
                    }
                    below.set(p);
                    match self.anc[p].get() {
                        Some(pa) => below.union(pa), // the whole past of p, already known
                        None => todo.push(p),
                    }
                }
            }
        }
        of.iter().copied().filter(|&r| !below.has(r)).collect()
    }
    /// The rows in the past of `i` (and `i` itself when `inclusive`), in index order.
    pub fn past(&self, i: usize, inclusive: bool) -> Vec<usize> {
        let b = self.ancestors(i);
        (0..self.len()).filter(|&q| b.has(q) || (inclusive && q == i)).collect()
    }
    /// The number of rows in the past of `i`.
    pub fn depth(&self, i: usize) -> usize {
        self.ancestors(i).len()
    }
}

/// `kernel_lib.ancestors` over ids alone: the ids `rid` names, and the ids those name, through `by`. An id
/// named and not held is in the answer and is followed no further.
pub fn ancestor_ids<R: Row>(by: &BTreeMap<R::Id, &R>, rid: &R::Id) -> alloc::collections::BTreeSet<R::Id> {
    let mut out = alloc::collections::BTreeSet::new();
    let mut todo: Vec<R::Id> = Vec::new();
    if let Some(r) = by.get(rid) {
        todo.extend(r.names().iter().cloned());
    }
    while let Some(x) = todo.pop() {
        if out.insert(x.clone()) {
            if let Some(r) = by.get(&x) {
                todo.extend(r.names().iter().cloned());
            }
        }
    }
    out
}
