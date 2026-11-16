//! Three layers (KERNEL.md section 3; CC 2.7.3): **kept**, **concluded**, and the derived answers built on
//! them. `causal_kernel.kept`, `concluded` and `arrive`.
//!
//! * kept: the least set closed under the door. A row is kept iff it is well formed alone and every row it
//!   names is kept. Nothing is refused because of another row.
//! * concluded: recursion on ancestry. The rule reads the row and its concluded ancestors only, so the
//!   answer is one, in every arrival order, and final once the row is kept (`Causal.concl_final`).

use crate::graph::Graph;
use crate::Row;
use alloc::collections::{BTreeMap, BTreeSet};
use alloc::vec;
use alloc::vec::Vec;

/// The least set closed under the door, in the order offered, each id once.
/// `wf` reads the row alone (signature, shape and the row's own bounds are the caller's).
pub fn kept<R: Row>(offered: &[R], wf: impl Fn(&R) -> bool) -> Vec<&R> {
    let mut acc: BTreeSet<&R::Id> = BTreeSet::new();
    // a row waits on the distinct ids it names that are not yet kept
    let mut waiting_on: BTreeMap<&R::Id, Vec<usize>> = BTreeMap::new();
    let mut left: Vec<usize> = vec![0; offered.len()];
    let mut ready: Vec<usize> = Vec::new();
    for (i, r) in offered.iter().enumerate() {
        if !wf(r) {
            left[i] = usize::MAX;
            continue;
        }
        let names: BTreeSet<&R::Id> = r.names().iter().collect();
        left[i] = names.len();
        for n in names {
            waiting_on.entry(n).or_default().push(i);
        }
        if left[i] == 0 {
            ready.push(i);
        }
    }
    while let Some(i) = ready.pop() {
        let id = offered[i].id();
        if !acc.insert(id) {
            continue;
        }
        if let Some(ws) = waiting_on.remove(id) {
            for w in ws {
                left[w] -= 1;
                if left[w] == 0 {
                    ready.push(w);
                }
            }
        }
    }
    let mut seen: BTreeSet<&R::Id> = BTreeSet::new();
    offered.iter().filter(|r| acc.contains(r.id()) && seen.insert(r.id())).collect()
}

/// A kept set with its closure and the conclusion of every row.
pub struct Concluded<'a, R: Row> {
    /// The kept rows and the closure over what they name.
    pub g: Graph<'a, R>,
    c: Vec<bool>,
    cs: Vec<usize>,
}

impl<'a, R: Row> Concluded<'a, R> {
    /// A graph with the conclusions given (every row concluded when `c` is `None`).
    pub fn with(g: Graph<'a, R>, c: Option<Vec<bool>>) -> Self {
        let c = c.unwrap_or_else(|| vec![true; g.len()]);
        let cs = (0..g.len()).filter(|&i| c[i]).collect();
        Concluded { g, c, cs }
    }
    /// Whether row `i` concluded.
    #[inline]
    pub fn concluded(&self, i: usize) -> bool {
        self.c[i]
    }
    /// Whether the row with this id is held and concluded.
    pub fn concluded_id(&self, id: &R::Id) -> bool {
        self.g.idx(id).is_some_and(|i| self.c[i])
    }
    /// The concluded rows, in index order.
    pub fn cs(&self) -> &[usize] {
        &self.cs
    }
    /// The conclusion of every row, in index order.
    pub fn all(&self) -> &[bool] {
        &self.c
    }
}

/// What a conclusion rule is given: the row, its concluded ancestors (in index order) and the closure.
pub struct Past<'g, 'a, R: Row> {
    /// The closure over the kept set.
    pub g: &'g Graph<'a, R>,
    /// The row being concluded.
    pub i: usize,
    /// Its concluded ancestors, in index order.
    pub p: &'g [usize],
}

impl<'g, 'a, R: Row> Past<'g, 'a, R> {
    /// The row being concluded.
    pub fn row(&self) -> &'a R {
        self.g.row(self.i)
    }
    /// Its concluded ancestors, as rows.
    pub fn rows(&self) -> impl Iterator<Item = &'a R> + '_ {
        self.p.iter().map(move |&q| self.g.row(q))
    }
    /// The concluded ancestor with this id.
    pub fn get(&self, id: &R::Id) -> Option<&'a R> {
        let q = self.g.idx(id)?;
        // `p` is in index order (ascending), as `conclude` builds it
        if self.p.binary_search(&q).is_ok() {
            Some(self.g.row(q))
        } else {
            None
        }
    }
    /// Whether row `a` is in the past of row `b` (both by id; an id not held is in no past).
    pub fn past(&self, a: &R::Id, b: &R::Id) -> bool {
        match (self.g.idx(a), self.g.idx(b)) {
            (Some(a), Some(b)) => self.g.in_past(a, b),
            _ => false,
        }
    }
}

/// Conclude every kept row. `rule` reads the row and its concluded ancestors; `root`, when given, is the
/// test for a row with a root at or above it: a row with none concludes nothing.
pub fn conclude<'a, R: Row>(
    kept_rows: impl IntoIterator<Item = &'a R>,
    mut rule: impl FnMut(&Past<'_, 'a, R>) -> bool,
    root: Option<&dyn Fn(&R) -> bool>,
) -> Concluded<'a, R> {
    let g = Graph::new(kept_rows);
    let n = g.len();
    let mut order: Vec<usize> = (0..n).collect();
    order.sort_by_key(|&i| g.level(i)); // a row reads only rows of lower level
    let mut c = vec![false; n];
    for &i in &order {
        if g.waiting(i) {
            continue; // on a cycle of names, or naming one: no kept set holds it
        }
        let live = match root {
            None => true,
            Some(f) => f(g.row(i)) || g.ancestors(i).iter().any(|a| f(g.row(a))),
        };
        if !live {
            continue;
        }
        let p: Vec<usize> = g.ancestors(i).iter().filter(|&q| c[q]).collect();
        c[i] = rule(&Past { g: &g, i, p: &p });
    }
    Concluded::with(g, Some(c))
}

/// The same two layers as a node runs them: rows arrive one at a time in `order`; a row whose named rows are
/// not all held waits; a row is concluded once, when it is kept. Returns the held rows in the order the door
/// admitted them, concluded. That this equals [`conclude`] over [`kept`] in every order is what
/// `door_any_order` and `concl_final` state.
pub fn arrive<'a, R: Row>(
    order: &'a [R],
    rule: impl FnMut(&Past<'_, 'a, R>) -> bool,
    root: Option<&dyn Fn(&R) -> bool>,
    wf: impl Fn(&R) -> bool,
) -> Concluded<'a, R> {
    let mut held: Vec<&'a R> = Vec::new();
    let mut ids: BTreeSet<&R::Id> = BTreeSet::new();
    let mut waiting: Vec<&'a R> = Vec::new();
    for r in order {
        if ids.contains(r.id()) || waiting.iter().any(|w| w.id() == r.id()) {
            continue;
        }
        waiting.push(r);
        let mut moved = true;
        while moved {
            moved = false;
            let mut k = 0;
            while k < waiting.len() {
                let w = waiting[k];
                if wf(w) && w.names().iter().all(|n| ids.contains(n)) {
                    waiting.remove(k);
                    ids.insert(w.id());
                    held.push(w);
                    moved = true;
                } else {
                    k += 1;
                }
            }
        }
    }
    // every ancestor of a held row was held before it, so the conclusion at admission is the conclusion
    // over the held set: the same recursion on ancestry
    conclude(held, rule, root)
}
