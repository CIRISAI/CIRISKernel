//! The reader's trust walk (KERNEL.md section 5, **stands**; CC 2.7.5 and CC 4.4.3.34), as
//! `formal/trust_set/TrustSet.lean` states it (parent repository). There is no trust set among the inputs:
//! the walk starts at the reader's own acceptance edges.
//!
//! An onward hop counts only from an authority's own acceptance edges. At each hop the remaining depth is
//! the lesser of what is left and the edge's own; an edge admits a class it lists, or every class when it
//! lists none, so the classes along a walk intersect; and a cycle is visited once, since arriving again at a
//! key with no more budget than before reaches nothing new (`reaches_mono_budget`).

use alloc::collections::BTreeMap;
use alloc::vec::Vec;

/// An acceptance edge: `src` trusts `dst` as a licensor, for the classes listed (all when empty), with
/// `depth` further hops allowed past `dst`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Accepts<K, C> {
    /// The key whose own row the edge is.
    pub src: K,
    /// The authority it accepts.
    pub dst: K,
    /// The classes it admits; empty admits every class.
    pub classes: Vec<C>,
    /// How far the walk may continue past `dst` (0: this authority alone).
    pub depth: u32,
}

impl<K, C: PartialEq> Accepts<K, C> {
    /// An edge admits a class when it lists it, or lists nothing.
    pub fn admits(&self, c: &C) -> bool {
        self.classes.is_empty() || self.classes.contains(c)
    }
}

/// The traversal cap of CC 4.1.1.
pub const HOP_CAP: u32 = 5;

/// Whether the walk from `from`, with `budget` hops, reaches authority `a` for class `c`
/// (`TrustSet.reaches`). Each key is expanded only with the greatest budget it has been reached with.
pub fn reaches<K: Ord + Clone, C: PartialEq>(edges: &[Accepts<K, C>], from: &K, c: &C, budget: u32, a: &K) -> bool {
    let mut best: BTreeMap<K, u32> = BTreeMap::new();
    best.insert(from.clone(), budget);
    let mut todo: Vec<K> = alloc::vec![from.clone()];
    while let Some(k) = todo.pop() {
        let b = best[&k];
        if b == 0 {
            continue;
        }
        for e in edges.iter().filter(|e| e.src == k && e.admits(c)) {
            if e.dst == *a {
                return true;
            }
            let nb = core::cmp::min(b - 1, e.depth);
            if best.get(&e.dst).map_or(true, |&o| nb > o) {
                best.insert(e.dst.clone(), nb);
                todo.push(e.dst.clone());
            }
        }
    }
    false
}

/// Whether the reader honours a licence of class `cls` issued by `auth`: its own walk, within the cap,
/// reaches the authority for that class, and the authority's charter declares the class (`TrustSet.honours`).
pub fn honours<K: Ord + Clone, C: PartialEq>(
    edges: &[Accepts<K, C>],
    reader: &K,
    charter_declares: impl Fn(&K, &C) -> bool,
    auth: &K,
    cls: &C,
) -> bool {
    charter_declares(auth, cls) && reaches(edges, reader, cls, HOP_CAP, auth)
}
