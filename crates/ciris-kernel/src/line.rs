//! Which counted acts of a group's ledger count for a reader (KERNEL.md sections 7 and 8a; CC 2.7.7, 2.7.8).
//! `checkpoint.py` with the refused group checkpoint left out.
//!
//! * **Built on.** A counted act counts only if every counted act among the heads it names counts. A row
//!   built on a counted act that does not count is void, down the whole line.
//! * **The reader's line.** A reader's own acknowledgement of a head makes the acknowledged act, and every
//!   counted act in its past, that reader's line. For that reader the line counts, and a counted act not in
//!   the past of an act of the line, every head of which is strictly in the past of that act's OWN heads,
//!   does not count (CC 2.7.8 as amended by the ruling of 2026-11-27: the line is sibling-safe). A sibling of
//!   the acknowledged act (a row at its own head) is behind no line: two versions of one head wait as tips for
//!   every reader. A row built on a void act is void. This binds nobody else, and it ranks no line.
//!
//! The group checkpoint (every counting act a checkpoint for everyone) is not part of the kernel: it ranks
//! lines by depth, and KERNEL.md section 8a runs it only as the reason. It is not implemented here.

use crate::layers::Concluded;
use crate::Row;
use alloc::collections::BTreeSet;
use alloc::vec::Vec;

/// What the reader's line reads of a row.
pub trait LineSpec<R: Row> {
    /// What a counted act is on (a group's founding row, or a key).
    type Obj: Ord + Clone;
    /// The object a counted act is on, with the heads it is counted over: a row counted by a group that
    /// names at least one head. `None` for every other row.
    fn counted_act<'r>(&self, r: &'r R) -> Option<(Self::Obj, &'r [R::Id])>;
    /// The object and heads a reader's acknowledgement names, when `r` is an acknowledgement signed by `own`.
    fn ack_by<'r>(&self, r: &'r R, own: &R::Key) -> Option<(Self::Obj, &'r [R::Id])>;
    /// The object a row `own` signed or cosigned is over, where the row is one of its acknowledgements: a
    /// reader's own signed rows acknowledge the counted acts in their past (the heads ruling of 2026-11-26,
    /// H6). `get` reads a row of the set by id. By default none: only [`LineSpec::ack_by`] is read.
    fn acknowledges<'r>(&self, r: &'r R, own: &R::Key, get: &dyn Fn(&R::Id) -> Option<&'r R>) -> Option<Self::Obj> {
        let _ = (r, own, get);
        None
    }
    /// A counted act judged on the line by its own heads alone: a head the reader holds void does not keep it from
    /// counting (a roster merge). By default none.
    fn own_heads_only(&self, r: &R) -> bool {
        let _ = r;
        false
    }
}

fn older<R: Row>(c: &Concluded<'_, R>, heads: &[R::Id], than: &[R::Id]) -> bool {
    !heads.is_empty() && heads.iter().all(|h| than.iter().any(|t| c.g.idx(t).is_some_and(|t| c.g.id_in_past(h, t))))
}

/// The counted acts on `obj`, concluded, in index order.
pub fn counted_acts<R: Row, L: LineSpec<R>>(c: &Concluded<'_, R>, spec: &L, obj: &L::Obj) -> Vec<usize> {
    c.cs().iter().copied().filter(|&i| spec.counted_act(c.g.row(i)).is_some_and(|(o, _)| o == *obj)).collect()
}

/// The counted acts on `obj` this reader has acknowledged, with the counted acts in their past: the heads its
/// explicit acknowledgements name ([`LineSpec::ack_by`]), and every row it signed or cosigned over `obj`
/// ([`LineSpec::acknowledges`], H6) with the counted acts in that row's past.
pub fn own_line<R: Row, L: LineSpec<R>>(
    c: &Concluded<'_, R>,
    spec: &L,
    own: Option<&R::Key>,
    obj: &L::Obj,
) -> Vec<usize> {
    own_line_with(c, spec, own, obj, &|_| BTreeSet::new())
}

/// [`own_line`], where a signed row `s` does not acknowledge the counted acts `except(s)` gives (by index): the
/// changes void for one of the reader's own counted rows (a fork head it had to name; `seat::Seats` passes them).
///
/// Acknowledging never un-voids (the ruling of 2026-11-27; CC 2.7.9: an acknowledgement closes older heads, and
/// nothing reopens them): a row the reader signed acknowledges the counted acts in its past that are not already
/// void for the line its earlier rows (those in its own past) drew. A change behind the reader's line stays behind
/// it after the reader signs a row naming it as a head.
pub fn own_line_with<R: Row, L: LineSpec<R>>(
    c: &Concluded<'_, R>,
    spec: &L,
    own: Option<&R::Key>,
    obj: &L::Obj,
    except: &dyn Fn(usize) -> BTreeSet<usize>,
) -> Vec<usize> {
    let Some(own) = own else { return Vec::new() };
    let get = |i: &R::Id| c.g.idx(i).map(|i| c.g.row(i));
    let acts = counted_acts(c, spec, obj);
    let heads = |i: usize| spec.counted_act(c.g.row(i)).map(|(_, h)| h).unwrap_or(&[]);
    // the reader's own rows over `obj`, each with the heads an explicit acknowledgement names, oldest first
    let mut rows: Vec<(usize, Vec<usize>)> = Vec::new();
    for &a in c.cs() {
        let r = c.g.row(a);
        let named: Vec<usize> = match spec.ack_by(r, own) {
            Some((o, hs)) if o == *obj => hs.iter().filter_map(|h| c.g.idx(h)).collect(),
            _ => Vec::new(),
        };
        if !named.is_empty() || spec.acknowledges(r, own, &get).is_some_and(|o| o == *obj) {
            rows.push((a, named));
        }
    }
    rows.sort_by_key(|&(a, _)| c.g.level(a));
    // the counted acts behind a line (sibling-safe), and those built on them, the line's own acts apart
    let void_for = |line: &BTreeSet<usize>| -> BTreeSet<usize> {
        let mut out: BTreeSet<usize> = acts
            .iter()
            .copied()
            .filter(|&r| {
                !line.contains(&r) && line.iter().any(|&m| m != r && !c.g.in_past(r, m) && older(c, heads(r), heads(m)))
            })
            .collect();
        loop {
            let more: Vec<usize> = acts
                .iter()
                .copied()
                .filter(|&r| {
                    !out.contains(&r)
                        && !line.contains(&r)
                        && heads(r).iter().any(|h| c.g.idx(h).is_some_and(|hi| out.contains(&hi)))
                })
                .collect();
            if more.is_empty() {
                return out;
            }
            out.extend(more);
        }
    };
    let mut got: Vec<(usize, BTreeSet<usize>)> = Vec::new();
    for (a, named) in &rows {
        let ex = except(*a);
        let prior: BTreeSet<usize> =
            got.iter().filter(|(b, _)| c.g.in_past(*b, *a)).flat_map(|(_, s)| s.iter().copied()).collect();
        let held = void_for(&prior);
        let cov: BTreeSet<usize> = acts
            .iter()
            .copied()
            .filter(|&r| {
                r == *a || c.g.in_past(r, *a) || named.contains(&r) || named.iter().any(|&h| c.g.in_past(r, h))
            })
            .filter(|&r| r == *a || (!ex.contains(&r) && !held.contains(&r)))
            .collect();
        got.push((*a, cov));
    }
    let mine: BTreeSet<usize> = got.into_iter().flat_map(|(_, s)| s).collect();
    acts.into_iter().filter(|i| mine.contains(i)).collect()
}

/// The counted acts on `obj` that count for reader `own`, given which of them the cut lets count.
pub fn settle<R: Row, L: LineSpec<R>>(
    c: &Concluded<'_, R>,
    spec: &L,
    obj: &L::Obj,
    own: Option<&R::Key>,
    cut_counts: impl Fn(usize) -> bool,
) -> BTreeSet<usize> {
    settle_with(c, spec, obj, own, cut_counts, |_| false)
}

/// [`settle`], with `never_behind(i)` naming the acts the line never leaves behind (an election's seating, read
/// at its election's vacancy; `seat::Seats` passes it).
pub fn settle_with<R: Row, L: LineSpec<R>>(
    c: &Concluded<'_, R>,
    spec: &L,
    obj: &L::Obj,
    own: Option<&R::Key>,
    cut_counts: impl Fn(usize) -> bool,
    never_behind: impl Fn(usize) -> bool,
) -> BTreeSet<usize> {
    settle_except(c, spec, obj, own, cut_counts, never_behind, &|_| BTreeSet::new())
}

/// [`settle_with`], the reader's line read with [`own_line_with`] (`except`).
pub fn settle_except<R: Row, L: LineSpec<R>>(
    c: &Concluded<'_, R>,
    spec: &L,
    obj: &L::Obj,
    own: Option<&R::Key>,
    cut_counts: impl Fn(usize) -> bool,
    never_behind: impl Fn(usize) -> bool,
    except: &dyn Fn(usize) -> BTreeSet<usize>,
) -> BTreeSet<usize> {
    let acts = counted_acts(c, spec, obj);
    let line: BTreeSet<&R::Id> = acts.iter().map(|&i| c.g.row(i).id()).collect();
    let mut live: Vec<usize> = acts.iter().copied().filter(|&i| cut_counts(i)).collect();
    // ancestors first
    live.sort_by_key(|&i| c.g.level(i));
    // own_line returns counted acts on obj only, so one of them is live exactly when the cut lets it count
    let mine: BTreeSet<usize> =
        own_line_with(c, spec, own, obj, except).into_iter().filter(|&i| cut_counts(i)).collect();
    let heads = |i: usize| spec.counted_act(c.g.row(i)).map(|(_, h)| h).unwrap_or(&[]);
    // CC 2.7.8 as amended (the ruling of 2026-11-27): an act not in the past of `m` every head of which is strictly
    // in the past of `m`'s own heads is behind `m`, with no test of concurrency. A sibling of `m` is not.
    let behind = |r: usize, m: usize| {
        let beside = !c.g.in_past(r, m);
        m != r && beside && !never_behind(r) && older(c, heads(r), heads(m))
    };
    let mut out: BTreeSet<usize> = BTreeSet::new();
    let mut out_ids: BTreeSet<&R::Id> = BTreeSet::new();
    for &r in &live {
        let built_ok = spec.own_heads_only(c.g.row(r))
            || heads(r).iter().filter(|h| line.contains(h)).all(|h| out_ids.contains(h));
        if mine.contains(&r) || (built_ok && !mine.iter().any(|&m| behind(r, m))) {
            out.insert(r);
            out_ids.insert(c.g.row(r).id());
        }
    }
    out
}

/// The counted acts the cut lets count that do not count for reader `own`: left behind by its acknowledged
/// line, or built on a counted act that does not count.
pub fn void<R: Row, L: LineSpec<R>>(
    c: &Concluded<'_, R>,
    spec: &L,
    own: Option<&R::Key>,
    cut_counts: impl Fn(usize) -> bool,
) -> BTreeSet<usize> {
    void_with(c, spec, own, cut_counts, |_| false)
}

/// [`void`], with `never_behind` as in [`settle_with`].
pub fn void_with<R: Row, L: LineSpec<R>>(
    c: &Concluded<'_, R>,
    spec: &L,
    own: Option<&R::Key>,
    cut_counts: impl Fn(usize) -> bool,
    never_behind: impl Fn(usize) -> bool,
) -> BTreeSet<usize> {
    void_except(c, spec, own, cut_counts, never_behind, &|_| BTreeSet::new())
}

/// [`void_with`], the reader's line read with [`own_line_with`] (`except`).
pub fn void_except<R: Row, L: LineSpec<R>>(
    c: &Concluded<'_, R>,
    spec: &L,
    own: Option<&R::Key>,
    cut_counts: impl Fn(usize) -> bool,
    never_behind: impl Fn(usize) -> bool,
    except: &dyn Fn(usize) -> BTreeSet<usize>,
) -> BTreeSet<usize> {
    let objs: BTreeSet<L::Obj> = c.cs().iter().filter_map(|&i| spec.counted_act(c.g.row(i)).map(|(o, _)| o)).collect();
    let mut out = BTreeSet::new();
    for obj in &objs {
        let ok = settle_except(c, spec, obj, own, &cut_counts, &never_behind, except);
        for i in counted_acts(c, spec, obj) {
            if cut_counts(i) && !ok.contains(&i) {
                out.insert(i);
            }
        }
    }
    out
}

/// The same two rules over roster versions (`checkpoint.versions`, the shape of `roster_fork`): `builds_on[i]`
/// the versions version `i` extends, `past[i]` every version in its past, `valid(i)` counted over the heads
/// it extends, `ack` the version this reader acknowledged. Returns the versions that count for the reader.
pub fn versions(
    ids: &[usize],
    builds_on: &dyn Fn(usize) -> Vec<usize>,
    past: &dyn Fn(usize) -> BTreeSet<usize>,
    valid: &dyn Fn(usize) -> bool,
    ack: Option<usize>,
) -> BTreeSet<usize> {
    // i is not in the past of j, an act of the reader's line, and extends only versions strictly in the past of a
    // version j extends (CC 2.7.8 as amended, sibling-safe; no test of concurrency, as `settle`)
    let stale = |i: usize, j: usize| {
        let bi = builds_on(i);
        let bj = builds_on(j);
        let beside = i != j && !past(j).contains(&i);
        beside && !bi.is_empty() && bi.iter().all(|e| bj.iter().any(|&h| past(h).contains(e)))
    };
    let mine: BTreeSet<usize> = match ack {
        None => BTreeSet::new(),
        Some(a) => {
            let mut m = past(a);
            m.insert(a);
            m
        }
    };
    let mut p: Vec<usize> = ids
        .iter()
        .copied()
        .filter(|&i| valid(i))
        .filter(|&i| mine.contains(&i) || !mine.iter().any(|&a| stale(i, a)))
        .collect();
    p.sort_by_key(|&i| past(i).len());
    let mut out = BTreeSet::new();
    for i in p {
        if builds_on(i).iter().all(|e| out.contains(e)) {
            out.insert(i);
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::layers::conclude;
    use alloc::vec;

    struct Rw {
        id: u32,
        names: Vec<u32>,
        signer: u32,
        head: Vec<u32>,
        ack: bool,
    }
    impl Row for Rw {
        type Id = u32;
        type Key = u32;
        fn id(&self) -> &u32 {
            &self.id
        }
        fn names(&self) -> &[u32] {
            &self.names
        }
        fn signer(&self) -> &u32 {
            &self.signer
        }
    }
    struct Spec;
    impl LineSpec<Rw> for Spec {
        type Obj = u32;
        fn counted_act<'r>(&self, r: &'r Rw) -> Option<(u32, &'r [u32])> {
            (!r.ack && !r.head.is_empty()).then_some((0, r.head.as_slice()))
        }
        fn ack_by<'r>(&self, r: &'r Rw, own: &u32) -> Option<(u32, &'r [u32])> {
            (r.ack && r.signer == *own).then_some((0, r.head.as_slice()))
        }
    }

    /// CC 2.7.8 as amended (the ruling of 2026-11-27): an act every head of which is strictly in the past of the
    /// acknowledged act's own heads, and not in its past, is void for that reader, with no test of concurrency;
    /// a sibling of the acknowledged act (at its own head) is not.
    #[test]
    fn the_line_voids_a_descendant_that_names_an_older_head() {
        let row = |id, names: Vec<u32>, signer, head: Vec<u32>, ack| Rw { id, names, signer, head, ack };
        let rows = vec![
            row(0, vec![], 1, vec![], false),
            row(1, vec![0], 1, vec![0], false),    // a1, at the founding row
            row(2, vec![1], 1, vec![1], false),    // a1b, at a1
            row(3, vec![0, 2], 1, vec![0], false), // a2, at the founding row, with a1b in its past
            row(4, vec![0], 1, vec![0], false),    // s, a sibling of a1 at the founding row
            row(5, vec![2], 9, vec![2], true),     // the reader 9 acknowledges a1b
            row(6, vec![1], 8, vec![1], true),     // the reader 8 acknowledges a1
        ];
        let c = conclude(rows.iter(), |_| true, None);
        let ids = |v: BTreeSet<usize>| v.into_iter().map(|i| c.g.row(i).id).collect::<Vec<_>>();
        assert_eq!(ids(super::void(&c, &Spec, Some(&9), |_| true)), vec![3, 4]);
        // for the reader of a1, a2 and s name the founding row, a1's own head: siblings, behind nothing
        assert!(super::void(&c, &Spec, Some(&8), |_| true).is_empty());
        assert!(super::void(&c, &Spec, None, |_| true).is_empty());
    }
}
