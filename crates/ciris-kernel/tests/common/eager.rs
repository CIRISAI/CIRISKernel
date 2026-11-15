//! The closure as the first version of the crate computed it: every row's past as a bitset, built at once.
//! Kept as the oracle the lazy closure of `graph::Graph` is compared with.
#![allow(dead_code)]
use ciris_kernel::graph::Bits;
use ciris_kernel::Row;
use std::collections::BTreeMap;

/// A set of rows with the closure over what they name. Indices follow the order the rows were given in.
pub struct EagerGraph<'a, R: Row> {
    rows: Vec<&'a R>,
    index: BTreeMap<R::Id, usize>,
    anc: Vec<Bits>,
}

impl<'a, R: Row> EagerGraph<'a, R> {
    /// Build the closure. A later row with an id already present is ignored.
    pub fn new(rows: impl IntoIterator<Item = &'a R>) -> Self {
        let mut v: Vec<&'a R> = Vec::new();
        let mut index = BTreeMap::new();
        for r in rows {
            if !index.contains_key(r.id()) {
                index.insert(r.id().clone(), v.len());
                v.push(r);
            }
        }
        let n = v.len();
        let names: Vec<Vec<usize>> =
            v.iter().map(|r| r.names().iter().filter_map(|x| index.get(x).copied()).collect()).collect();
        // iterative depth-first: a row's past is the union of what it names and their pasts
        let mut anc: Vec<Option<Bits>> = vec![None; n];
        let mut stack: Vec<(usize, bool)> = Vec::new();
        for s in 0..n {
            if anc[s].is_some() {
                continue;
            }
            stack.push((s, false));
            while let Some((i, expanded)) = stack.pop() {
                if anc[i].is_some() {
                    continue;
                }
                if !expanded {
                    stack.push((i, true));
                    for &p in &names[i] {
                        if anc[p].is_none() && p != i {
                            stack.push((p, false));
                        }
                    }
                } else {
                    let mut b = Bits::new(n);
                    for &p in &names[i] {
                        if p == i {
                            continue;
                        }
                        b.set(p);
                        if let Some(pa) = &anc[p] {
                            b.union(pa);
                        }
                    }
                    anc[i] = Some(b);
                }
            }
        }
        EagerGraph { rows: v, index, anc: anc.into_iter().map(|b| b.unwrap_or_else(|| Bits::new(n))).collect() }
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
        self.index.get(id).copied()
    }
    /// The past of row `i`: every row it names, and theirs.
    pub fn ancestors(&self, i: usize) -> &Bits {
        &self.anc[i]
    }
    /// Whether row `a` is in the past of row `b` (`a in anc[b]`).
    #[inline]
    pub fn in_past(&self, a: usize, b: usize) -> bool {
        self.anc[b].has(a)
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
    pub fn frontier(&self, of: &[usize]) -> Vec<usize> {
        of.iter().copied().filter(|&r| !of.iter().any(|&q| self.in_past(r, q))).collect()
    }
    /// The rows in the past of `i` (and `i` itself when `inclusive`), in index order.
    pub fn past(&self, i: usize, inclusive: bool) -> Vec<usize> {
        (0..self.len()).filter(|&q| self.in_past(q, i) || (inclusive && q == i)).collect()
    }
    /// The number of rows in the past of `i`: a row reads only rows with strictly fewer.
    pub fn depth(&self, i: usize) -> usize {
        self.anc[i].len()
    }
}
