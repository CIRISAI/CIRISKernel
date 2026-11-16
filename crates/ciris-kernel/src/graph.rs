//! The only order is what rows name (KERNEL.md section 2; CC 2.7.2), and the closure over it
//! (KERNEL.md section 4, last operator): a row's past, whether two rows are concurrent, and the frontier
//! of a set. `kernel_lib.ancestors`, `closure`, `concurrent`, `frontier` and `past`.
//!
//! A [`Graph`] is built over a set of rows in which every row names only rows of the set (a kept set always
//! is one). A named digest with no row in the set is followed no further and is not an index here; the
//! Python model keeps such a digest in the ancestor set, and since no row carries it no answer differs.

use crate::Row;
use alloc::collections::BTreeMap;
use core::cell::OnceCell;

/// How many rows a point question of the past searches before it computes and keeps the whole past.
const SEARCH_BUDGET: usize = 256;
/// Up to how many rows [`Graph::frontier`] compares pairwise before it walks down from all of them at once.
const FRONTIER_PAIRWISE: usize = 16;
use alloc::vec;
use alloc::vec::Vec;

/// A fixed-size set of row indices.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct Bits {
    w: Vec<u64>,
}

impl Bits {
    /// The empty set over `n` indices.
    pub fn new(n: usize) -> Self {
        Bits { w: vec![0; n.div_ceil(64)] }
    }
    /// Whether `i` is in the set.
    #[inline]
    pub fn has(&self, i: usize) -> bool {
        self.w.get(i / 64).is_some_and(|x| (x >> (i % 64)) & 1 == 1)
    }
    /// Add `i`.
    #[inline]
    pub fn set(&mut self, i: usize) {
        self.w[i / 64] |= 1 << (i % 64);
    }
    /// Add every index of `o`.
    pub fn union(&mut self, o: &Bits) {
        for (a, b) in self.w.iter_mut().zip(o.w.iter()) {
            *a |= *b;
        }
    }
    /// The number of indices in the set.
    pub fn len(&self) -> usize {
        self.w.iter().map(|x| x.count_ones() as usize).sum()
    }
    /// Whether the set is empty.
    pub fn is_empty(&self) -> bool {
        self.w.iter().all(|x| *x == 0)
    }
    /// The indices, ascending.
    pub fn iter(&self) -> impl Iterator<Item = usize> + '_ {
        // one step per index held (lowest set bit first), not one per bit of the word
        self.w.iter().enumerate().flat_map(|(k, x)| {
            let mut x = *x;
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
    level: Vec<u32>,
    anc: Vec<OnceCell<Bits>>,
}

impl<'a, R: Row> Graph<'a, R> {
    /// Build the index. A later row with an id already present is ignored.
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
        let find = |id: &R::Id| index.binary_search_by(|e| e.0.cmp(id)).ok().map(|k| index[k].1);
        let mut off: Vec<usize> = Vec::with_capacity(n + 1);
        let mut names: Vec<usize> = Vec::with_capacity(v.iter().map(|r| r.names().len()).sum());
        off.push(0);
        for (i, r) in v.iter().enumerate() {
            let s = names.len();
            names.extend(r.names().iter().filter_map(find).filter(|&p| p != i));
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
        // levels, iteratively: a row's level is known once those of the rows it names are
        const UNSET: u32 = u32::MAX;
        let mut level = vec![UNSET; n];
        let mut stack: Vec<usize> = Vec::new();
        for s in 0..n {
            if level[s] != UNSET {
                continue;
            }
            stack.push(s);
            while let Some(&i) = stack.last() {
                if level[i] != UNSET {
                    stack.pop();
                    continue;
                }
                let before = stack.len();
                for &p in &names[off[i]..off[i + 1]] {
                    if level[p] == UNSET {
                        stack.push(p);
                    }
                }
                if stack.len() == before {
                    level[i] = 1 + names[off[i]..off[i + 1]].iter().map(|&p| level[p]).max().unwrap_or(0);
                    stack.pop();
                }
            }
        }
        let anc = (0..n).map(|_| OnceCell::new()).collect();
        Graph { rows: v, index, off, names, level, anc }
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
        self.index.binary_search_by(|e| e.0.cmp(id)).ok().map(|k| self.index[k].1)
    }
    /// The held rows row `i` names directly.
    #[inline]
    pub fn named(&self, i: usize) -> &[usize] {
        &self.names[self.off[i]..self.off[i + 1]]
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
                None => todo.extend(self.named(p).iter().copied().filter(|&q| !b.has(q))),
            }
        }
        let _ = self.anc[i].set(b);
        self.anc[i].get().expect("computed above")
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
