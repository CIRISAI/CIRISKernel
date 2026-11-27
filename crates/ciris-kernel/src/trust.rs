//! The reader's trust walk (KERNEL.md section 5, **stands**; CC 2.7.5 and CC 4.4.3.34), as
//! `formal/trust_set/TrustSet.lean` states it (parent repository). There is no trust set among the inputs:
//! the walk starts at the reader's own acceptance edges.
//!
//! An onward hop counts only from an authority's own acceptance edges. At each hop the remaining depth is
//! the lesser of what is left and the edge's own; an edge admits a class it lists, or every class when its
//! `trust_classes` is absent, so the classes along a walk intersect; and a cycle is visited once, since arriving
//! again at a key with no more budget than before reaches nothing new (`reaches_mono_budget`). A present list must be
//! non-empty, sorted and name no class twice; any other is refused at admission (`trust_accepts_classes_malformed`,
//! [`Accepts::refusal`]), and the walk reads such an edge as no edge.
//!
//! Whether an authority's charter declares a class is no caller's answer: [`Charters`] holds each authority's
//! declared classes, read from rows by [`crate::charter::charters`] (a community's record in force over the rows
//! the reader holds), with any other charter supplied for an authority (the trust root's scope) met with it. Whether a
//! reader honours a licence is read from rows alone, its edges included: [`crate::trust_rows::read_licence`], the
//! only public path; no caller supplies edges to it.

use alloc::collections::{BTreeMap, BTreeSet};
use alloc::vec::Vec;

/// Per authority, the licence classes its charter declares. An authority with no entry declares none. Built by
/// [`crate::charter::charters`]; a charter from elsewhere (the trust root bundle's scope) enters by [`Charters::meet`].
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Charters<K: Ord, C: Ord> {
    by: BTreeMap<K, BTreeSet<C>>,
}

impl<K: Ord, C: Ord> Default for Charters<K, C> {
    fn default() -> Self {
        Charters { by: BTreeMap::new() }
    }
}

impl<K: Ord, C: Ord> Charters<K, C> {
    /// No authority declares anything.
    pub fn new() -> Self {
        Self::default()
    }
    /// Meet a charter for `auth` with the one held: the classes both declare (the first charter for an authority is
    /// taken as it is).
    pub fn meet(&mut self, auth: K, classes: impl IntoIterator<Item = C>) {
        let new: BTreeSet<C> = classes.into_iter().collect();
        match self.by.get_mut(&auth) {
            Some(have) => have.retain(|c| new.contains(c)),
            None => {
                self.by.insert(auth, new);
            }
        }
    }
    /// Whether `auth`'s charter declares class `cls`.
    pub fn declares(&self, auth: &K, cls: &C) -> bool {
        self.by.get(auth).is_some_and(|s| s.contains(cls))
    }
    /// The classes `auth`'s charter declares, where it has one.
    pub fn classes(&self, auth: &K) -> Option<&BTreeSet<C>> {
        self.by.get(auth)
    }
    /// Every authority with a charter, and the classes it declares, in key order.
    pub fn iter(&self) -> impl Iterator<Item = (&K, &BTreeSet<C>)> {
        self.by.iter()
    }
}

/// An acceptance edge: `src` trusts `dst` as a licensor, for the classes listed (`trust_classes`; every class when
/// absent), with `depth` further hops allowed past `dst`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Accepts<K, C> {
    /// The key whose own row the edge is.
    pub src: K,
    /// The authority it accepts.
    pub dst: K,
    /// The classes it admits (`trust_classes`); `None` (absent) admits every class the charter declares. A list must
    /// be non-empty, sorted and without a class twice ([`Accepts::refusal`]).
    pub classes: Option<Vec<C>>,
    /// How far the walk may continue past `dst` (0: this authority alone).
    pub depth: u32,
}

/// The admission's refusal of an acceptance edge whose `trust_classes` list is malformed (CC 4.4.3.34).
pub const CLASSES_MALFORMED: &str = "trust_accepts_classes_malformed";

impl<K, C: Ord> Accepts<K, C> {
    /// The admission's refusal of this edge, or `None`: a `trust_classes` list that is present must be non-empty,
    /// sorted and name no class twice; any other is [`CLASSES_MALFORMED`], and the edge is no edge. THE ONE PLACE the
    /// empty list is read.
    pub fn refusal(&self) -> Option<&'static str> {
        match &self.classes {
            None => None,
            Some(cs) if cs.is_empty() || cs.windows(2).any(|w| w[0] >= w[1]) => Some(CLASSES_MALFORMED),
            Some(_) => None,
        }
    }
    /// An admitted edge admits a class when it lists it, or when its list is absent (an empty list is read only if
    /// [`Accepts::refusal`] admits it, and then as every class).
    pub fn admits(&self, c: &C) -> bool {
        self.classes.as_ref().is_none_or(|cs| cs.is_empty() || cs.binary_search(c).is_ok())
    }
}

/// The traversal cap of CC 4.1.1.
pub const HOP_CAP: u32 = 5;

/// Whether the walk from `from`, with `budget` hops, reaches authority `a` for class `c`
/// (`TrustSet.reaches`). Each key is expanded only with the greatest budget it has been reached with.
pub fn reaches<K: Ord + Clone, C: Ord>(edges: &[Accepts<K, C>], from: &K, c: &C, budget: u32, a: &K) -> bool {
    walk_from(from, c, budget, a, |k, see| edges.iter().filter(|e| e.src == *k).any(see))
}

// The walk, over whatever gives the edges out of a key: `out(k, see)` shows `see` each edge whose source is
// `k`, in the edges' order, until one answers true.
fn walk_from<'e, K: Ord + Clone + 'e, C: Ord + 'e>(
    from: &K,
    c: &C,
    budget: u32,
    a: &K,
    out: impl Fn(&K, &mut dyn FnMut(&'e Accepts<K, C>) -> bool) -> bool,
) -> bool {
    let mut best: BTreeMap<K, u32> = BTreeMap::new();
    best.insert(from.clone(), budget);
    let mut todo: Vec<K> = alloc::vec![from.clone()];
    while let Some(k) = todo.pop() {
        let b = best[&k];
        if b == 0 {
            continue;
        }
        let found = out(&k, &mut |e| {
            if e.refusal().is_some() || !e.admits(c) {
                return false;
            }
            if e.dst == *a {
                return true;
            }
            let nb = core::cmp::min(b - 1, e.depth);
            if best.get(&e.dst).is_none_or(|&o| nb > o) {
                best.insert(e.dst.clone(), nb);
                todo.push(e.dst.clone());
            }
            false
        });
        if found {
            return true;
        }
    }
    false
}

/// The edges sorted by source, built once for a caller that walks the same edges again and again (each walk of
/// [`reaches`] reads every edge at every key it expands; one over an index reads only that key's run).
pub struct EdgeIndex<'e, K, C> {
    edges: &'e [Accepts<K, C>],
    by_src: Vec<usize>,
}

impl<'e, K: Ord + Clone, C: Ord> EdgeIndex<'e, K, C> {
    /// Index the edges by source (stable: one key's edges keep their order).
    pub fn new(edges: &'e [Accepts<K, C>]) -> Self {
        let mut by_src: Vec<usize> = (0..edges.len()).collect();
        by_src.sort_by(|&x, &y| edges[x].src.cmp(&edges[y].src));
        EdgeIndex { edges, by_src }
    }
    /// [`reaches`] over the indexed edges: the same answer.
    pub fn reaches(&self, from: &K, c: &C, budget: u32, a: &K) -> bool {
        walk(self.edges, &self.by_src, from, c, budget, a)
    }
}

/// [`reaches`] with the edges from a key read as their run in `by_src` (the edges' positions sorted by source),
/// not by a scan: the same walk, in the same order.
fn walk<K: Ord + Clone, C: Ord>(
    edges: &[Accepts<K, C>],
    by_src: &[usize],
    from: &K,
    c: &C,
    budget: u32,
    a: &K,
) -> bool {
    walk_from(from, c, budget, a, |k, see| {
        let lo = by_src.partition_point(|&x| edges[x].src < *k);
        by_src[lo..].iter().map(|&x| &edges[x]).take_while(|e| e.src == *k).any(see)
    })
}
