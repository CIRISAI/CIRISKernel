//! Which counted acts of a group's ledger count for a reader (KERNEL.md sections 7 and 8a; CC 2.7.7, 2.7.8).
//! `checkpoint.py` with the refused group checkpoint left out.
//!
//! * **Built on.** A counted act counts only if every counted act among the heads it names counts. A row
//!   built on a counted act that does not count is void, down the whole line.
//! * **The reader's line.** A reader's own acknowledgement of a head makes the acknowledged act, and every
//!   counted act in its past, that reader's line. For that reader the line counts, and a counted act not in
//!   the past of an act of the line that names only heads strictly in that act's past does not count
//!   (CC 2.7.8: "holds void every counted act that names an older head and is not in that head's past";
//!   `Reader.line_voids_old_fork`). So a sibling of the acknowledged act is void for this reader, and so is
//!   a row built on it. For a reader with no acknowledgement on that line, two versions of one head wait as
//!   tips (CC 2.7.8; `Reader.sibling_by_acknowledgement`). This binds nobody else, and it ranks no line.
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
}

fn older<R: Row>(c: &Concluded<'_, R>, heads: &[R::Id], than: &[R::Id]) -> bool {
    !heads.is_empty() && heads.iter().all(|h| than.iter().any(|t| c.g.idx(t).is_some_and(|t| c.g.id_in_past(h, t))))
}

/// The counted acts on `obj`, concluded, in index order.
pub fn counted_acts<R: Row, L: LineSpec<R>>(c: &Concluded<'_, R>, spec: &L, obj: &L::Obj) -> Vec<usize> {
    c.cs().iter().copied().filter(|&i| spec.counted_act(c.g.row(i)).is_some_and(|(o, _)| o == *obj)).collect()
}

/// The counted acts on `obj` this reader has acknowledged, with the counted acts in their past.
pub fn own_line<R: Row, L: LineSpec<R>>(
    c: &Concluded<'_, R>,
    spec: &L,
    own: Option<&R::Key>,
    obj: &L::Obj,
) -> Vec<usize> {
    let Some(own) = own else { return Vec::new() };
    let mut acked: BTreeSet<&R::Id> = BTreeSet::new();
    for &a in c.cs() {
        if let Some((o, hs)) = spec.ack_by(c.g.row(a), own) {
            if o == *obj {
                acked.extend(hs.iter());
            }
        }
    }
    counted_acts(c, spec, obj)
        .into_iter()
        .filter(|&r| {
            let id = c.g.row(r).id();
            acked.contains(id) || acked.iter().any(|h| c.g.idx(h).is_some_and(|h| c.g.in_past(r, h)))
        })
        .collect()
}

/// The counted acts on `obj` that count for reader `own`, given which of them the cut lets count.
pub fn settle<R: Row, L: LineSpec<R>>(
    c: &Concluded<'_, R>,
    spec: &L,
    obj: &L::Obj,
    own: Option<&R::Key>,
    cut_counts: impl Fn(usize) -> bool,
) -> BTreeSet<usize> {
    let acts = counted_acts(c, spec, obj);
    let line: BTreeSet<&R::Id> = acts.iter().map(|&i| c.g.row(i).id()).collect();
    let mut live: Vec<usize> = acts.iter().copied().filter(|&i| cut_counts(i)).collect();
    // ancestors first
    live.sort_by_key(|&i| c.g.level(i));
    // own_line returns counted acts on obj only, so one of them is live exactly when the cut lets it count
    let mine: BTreeSet<usize> = own_line(c, spec, own, obj).into_iter().filter(|&i| cut_counts(i)).collect();
    let heads = |i: usize| spec.counted_act(c.g.row(i)).map(|(_, h)| h).unwrap_or(&[]);
    // CC 2.7.8: "holds void every counted act that names an older head and is not in that head's past, however
    // many rows it has": no test of concurrency, so an act with `m` in its own past that names a head older
    // than `m` is void too. This is the rule `head::View` reads (an act not in an acknowledged head's past that
    // names only heads strictly in it).
    let behind =
        |r: usize, m: usize| m != r && !c.g.in_past(r, m) && older(c, heads(r), core::slice::from_ref(c.g.row(m).id()));
    let mut out: BTreeSet<usize> = BTreeSet::new();
    let mut out_ids: BTreeSet<&R::Id> = BTreeSet::new();
    for &r in &live {
        let built_ok = heads(r).iter().filter(|h| line.contains(h)).all(|h| out_ids.contains(h));
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
    let objs: BTreeSet<L::Obj> = c.cs().iter().filter_map(|&i| spec.counted_act(c.g.row(i)).map(|(o, _)| o)).collect();
    let mut out = BTreeSet::new();
    for obj in &objs {
        let ok = settle(c, spec, obj, own, &cut_counts);
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
    let conc = |i: usize, j: usize| i != j && !past(j).contains(&i) && !past(i).contains(&j);
    // i extends only versions strictly in the past of j, an act of the reader's line (CC 2.7.8)
    let stale = |i: usize, j: usize| {
        let bi = builds_on(i);
        conc(i, j) && !bi.is_empty() && bi.iter().all(|e| past(j).contains(e))
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
