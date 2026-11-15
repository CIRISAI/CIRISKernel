//! The operators every rule cell is written in (KERNEL.md section 4; CC 2.7.4), as in
//! `models/kernel_lib/kernel_lib.py`: select, group and reduce, interval, table cell and bounded repeat.
//! The closure over what rows name is in [`crate::graph`].
//!
//! Nothing here knows a family, a model or a rule. A reduce that meets a tie between two different
//! elements refuses with [`Tie`]; it never breaks the tie by position.

use alloc::collections::{BTreeMap, BTreeSet};
use alloc::vec::Vec;
use core::fmt;

/// Two different elements are both the least (or the greatest). Nothing in the set picks one.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Tie;

impl fmt::Display for Tie {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("two different rows share the extreme; nothing in the set picks one")
    }
}

/// select: the elements that match a predicate. `kernel_lib.sel` with the pattern written as a predicate.
pub fn sel<T, P>(rows: &[T], pat: P) -> Vec<&T>
where
    P: Fn(&T) -> bool,
{
    rows.iter().filter(|r| pat(r)).collect()
}

/// select with a bound: the elements first held strictly before `before` that match (`kernel_lib.sel(S, before=..)`).
pub fn sel_before<'a, T, V, H, P>(rows: &'a [T], before: Option<&V>, held: H, pat: P) -> Vec<&'a T>
where
    V: Ord,
    H: Fn(&T) -> V,
    P: Fn(&T) -> bool,
{
    rows.iter()
        .filter(|r| before.map_or(true, |b| held(r) < *b) && pat(r))
        .collect()
}

/// group: the elements by a key, each group in input order.
pub fn group_by<'a, T, G, B>(rows: impl IntoIterator<Item = &'a T>, by: B) -> BTreeMap<G, Vec<&'a T>>
where
    T: 'a,
    G: Ord,
    B: Fn(&T) -> G,
{
    let mut out: BTreeMap<G, Vec<&'a T>> = BTreeMap::new();
    for r in rows {
        out.entry(by(r)).or_default().push(r);
    }
    out
}

fn extreme<'a, T, V, K>(rows: &[&'a T], key: K, greatest: bool) -> Result<Option<&'a T>, Tie>
where
    T: PartialEq,
    V: Ord,
    K: Fn(&T) -> V,
{
    let mut best: Option<V> = None;
    for r in rows {
        let v = key(r);
        best = match best {
            None => Some(v),
            Some(b) => Some(if (greatest && v > b) || (!greatest && v < b) { v } else { b }),
        };
    }
    let Some(best) = best else { return Ok(None) };
    let tied: Vec<&'a T> = rows.iter().copied().filter(|r| key(r) == best).collect();
    if tied.iter().skip(1).any(|r| *r != tied[0]) {
        return Err(Tie);
    }
    Ok(Some(tied[0]))
}

/// reduce `least`: the element least by `key`; `Ok(None)` when empty; [`Tie`] when two different elements share it.
pub fn least<'a, T: PartialEq, V: Ord>(rows: &[&'a T], key: impl Fn(&T) -> V) -> Result<Option<&'a T>, Tie> {
    extreme(rows, key, false)
}

/// reduce `greatest`: as [`least`], the greatest.
pub fn greatest<'a, T: PartialEq, V: Ord>(rows: &[&'a T], key: impl Fn(&T) -> V) -> Result<Option<&'a T>, Tie> {
    extreme(rows, key, true)
}

/// reduce `min`: the least value itself, a function of the set.
pub fn min_of<V: Ord>(vals: impl IntoIterator<Item = V>) -> Option<V> {
    vals.into_iter().min()
}

/// reduce `max`: the greatest value itself, a function of the set.
pub fn max_of<V: Ord>(vals: impl IntoIterator<Item = V>) -> Option<V> {
    vals.into_iter().max()
}

/// reduce `one`: the single distinct value; `None` when there are none or two.
pub fn one<V: Ord>(vals: impl IntoIterator<Item = V>) -> Option<V> {
    let s: BTreeSet<V> = vals.into_iter().collect();
    if s.len() == 1 {
        s.into_iter().next()
    } else {
        None
    }
}

/// reduce `count`: the number of distinct values.
pub fn count<V: Ord>(vals: impl IntoIterator<Item = V>) -> usize {
    vals.into_iter().collect::<BTreeSet<V>>().len()
}

/// reduce `sum`: the sum of the value over the distinct `per`; a `per` that states two values adds nothing,
/// as a voice that says two things says nothing.
pub fn sum_per<P: Ord, V: Ord + Copy + Into<i128>>(pairs: impl IntoIterator<Item = (P, V)>) -> i128 {
    let mut said: BTreeMap<P, BTreeSet<V>> = BTreeMap::new();
    for (p, v) in pairs {
        said.entry(p).or_default().insert(v);
    }
    said.values()
        .filter(|s| s.len() == 1)
        .map(|s| (*s.iter().next().unwrap()).into())
        .sum()
}

/// interval: `lo <= x < hi`. An absent `lo` is an interval never opened (false); an absent `hi` one not yet
/// closed. An absent `x` lies in nothing.
pub fn in_range<V: Ord>(x: Option<&V>, lo: Option<&V>, hi: Option<&V>) -> bool {
    match (x, lo) {
        (Some(x), Some(lo)) => lo <= x && hi.map_or(true, |h| x < h),
        _ => false,
    }
}

/// table cell: the value a typed table gives for a key.
pub fn rule<'a, K: Ord, V>(table: &'a BTreeMap<K, V>, key: &K) -> Option<&'a V> {
    table.get(key)
}

/// bounded repeat: apply `step` until the state stops changing, at most `bound` times.
pub fn fix<S: PartialEq>(mut state: S, bound: usize, mut step: impl FnMut(&S) -> S) -> S {
    for _ in 0..bound {
        let nxt = step(&state);
        if nxt == state {
            break;
        }
        state = nxt;
    }
    state
}
