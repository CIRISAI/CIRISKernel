//! Derived answers over concluded rows (KERNEL.md sections 5 and 6; CC 2.7.5, 2.7.7):
//! the order on kinds (`wins`), the slot (`slot`), removal by causal past (`counts`), the trust walk over
//! live edges (`reach`, `means`) and the count of distinct voices (`tally`). `causal_kernel.py`.
//!
//! The fields each answer reads are parameters, as in `kernel_lib`: the caller says which row carries a
//! target, a pick, a removal or an edge. No instant, no rank and no id is compared.

use crate::layers::Concluded;
use crate::ops;
use crate::Row;
use alloc::collections::{BTreeMap, BTreeSet};
use alloc::vec::Vec;

/// Rule 1, different kinds on one target: of `rows`, those with no row on the same target of a higher kind.
/// Rows of the top kind all win; the order on kinds decides between kinds and nothing else (`wins_unique`).
pub fn wins<R: Row, T: Ord, L: Ord>(
    c: &Concluded<'_, R>,
    rows: &[usize],
    target: impl Fn(&R) -> Option<T>,
    label: impl Fn(&R) -> L,
) -> Vec<usize> {
    let mut top: BTreeMap<T, L> = BTreeMap::new();
    for &i in rows {
        let r = c.g.row(i);
        if let Some(t) = target(r) {
            let l = label(r);
            match top.get(&t) {
                Some(b) if *b >= l => {}
                _ => {
                    top.insert(t, l);
                }
            }
        }
    }
    rows.iter()
        .copied()
        .filter(|&i| {
            let r = c.g.row(i);
            target(r).is_some_and(|t| top.get(&t).is_some_and(|l| *l == label(r)))
        })
        .collect()
}

/// Rules 2 and 3: who holds a slot. `cands` are the concluded claims and deciding rows on it. A deciding row
/// carries a pick (a claim in its past) and speaks for that claim. Only the frontier speaks. Returns the one
/// value the frontier speaks (none when it speaks two) and the number of distinct values spoken.
/// So two concurrent claims are both or neither, and a row naming both decides (`Slot.descendant_decides`).
pub fn slot<R: Row, V: Ord + Clone>(
    c: &Concluded<'_, R>,
    cands: &[usize],
    picks: impl Fn(&R) -> Option<R::Id>,
    value: impl Fn(&R) -> V,
) -> (Option<V>, usize) {
    let ok: Vec<usize> = cands
        .iter()
        .copied()
        .filter(|&i| match picks(c.g.row(i)) {
            None => true,
            Some(p) => c.g.id_in_past(&p, i) && c.concluded_id(&p),
        })
        .collect();
    let spoken: Vec<V> = c
        .g
        .frontier(&ok)
        .into_iter()
        .map(|i| {
            let r = c.g.row(i);
            match picks(r).and_then(|p| c.g.idx(&p)) {
                Some(p) => value(c.g.row(p)),
                None => value(r),
            }
        })
        .collect();
    (ops::one(spoken.iter().cloned()), ops::count(spoken))
}

/// Removal by causal past (`Causal.counts`): row `i` counts iff it concluded and it is in the past of every
/// concluded row that removes `key(i)`. A row of a removed key counts when the removal has it among its
/// ancestors (`only_removals_stop_counting`, `sign_after_removal_never_counts`).
pub fn counts<R: Row, K: Ord>(
    c: &Concluded<'_, R>,
    i: usize,
    key: impl Fn(&R) -> Option<K>,
    removes: impl Fn(&R) -> Option<K>,
) -> bool {
    if !c.concluded(i) {
        return false;
    }
    let Some(k) = key(c.g.row(i)) else { return true };
    c.cs().iter().all(|&x| removes(c.g.row(x)).map_or(true, |rk| rk != k) || c.g.in_past(i, x))
}

/// The live edges: concluded rows that carry an edge (signer to key), with no concluded withdrawal that
/// names the edge and is signed by the edge's own signer (`only_withdrawals_remove`).
pub fn live_edges<R: Row>(
    c: &Concluded<'_, R>,
    edge_to: impl Fn(&R) -> Option<R::Key>,
    is_withdraw: impl Fn(&R) -> bool,
) -> Vec<(R::Key, R::Key)> {
    let wd: Vec<usize> = c.cs().iter().copied().filter(|&w| is_withdraw(c.g.row(w))).collect();
    let mut out = Vec::new();
    for &e in c.cs() {
        let r = c.g.row(e);
        let Some(to) = edge_to(r) else { continue };
        let ended = wd.iter().any(|&w| {
            let wr = c.g.row(w);
            wr.names().contains(r.id()) && wr.signer() == r.signer()
        });
        if !ended {
            out.push((r.signer().clone(), to));
        }
    }
    out
}

/// The keys a walk of at most `depth` live edges from the reader's own key arrives at. There is no trust
/// set among the inputs: it is a fold over the rows the reader's key signed (`no_own_edge_no_reach`).
pub fn reach<K: Ord + Clone>(own: &K, depth: usize, edges: &[(K, K)]) -> BTreeSet<K> {
    let start: BTreeSet<K> = core::iter::once(own.clone()).collect();
    ops::fix(start, depth, |ks| {
        let mut n = ks.clone();
        for (s, t) in edges {
            if ks.contains(s) {
                n.insert(t.clone());
            }
        }
        n
    })
}

/// Whether row `i` means something to the reader: it concluded and its signer is in the reader's reach.
pub fn means<R: Row>(c: &Concluded<'_, R>, i: usize, reach: &BTreeSet<R::Key>) -> bool {
    c.concluded(i) && reach.contains(c.g.row(i).signer())
}

/// Distinct counting voices on a proposal: concluded votes that name it, signed by a key of the roster it is
/// counted over, that count. A voice that says two things says nothing.
pub fn tally<R: Row, C: Ord>(
    c: &Concluded<'_, R>,
    proposal: usize,
    is_vote: impl Fn(&R) -> bool,
    member: impl Fn(&R::Key) -> bool,
    choice: impl Fn(&R) -> C,
    want: &C,
    counting: impl Fn(usize) -> bool,
) -> usize {
    let pid = c.g.row(proposal).id();
    let votes: Vec<usize> = c
        .cs()
        .iter()
        .copied()
        .filter(|&v| {
            let r = c.g.row(v);
            is_vote(r) && r.names().contains(pid) && member(r.signer()) && counting(v)
        })
        .collect();
    let by = ops::group_by(votes.iter().map(|&v| c.g.row(v)), |r| r.signer().clone());
    by.values().filter(|rs| ops::one(rs.iter().map(|r| choice(r))).as_ref() == Some(want)).count()
}
