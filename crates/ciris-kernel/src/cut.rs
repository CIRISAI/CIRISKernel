//! Rule 4, the cut (KERNEL.md section 6; CC 2.7.7): removal by causal past, as one derived rule. `cut.py`.
//!
//! A cut is a concluded row that carries the slots it cuts. Once a cut counts, a row on one of those slots
//! that is concurrent with the cut does not count. Rows in its past stand, and rows that name it are judged
//! at the head they name. "Counts" refers to itself through negation, and two rows can each depend on the
//! other not counting; that is solved the only symmetric way, by the well-founded fixed point. A cut is
//! [`Status::Counts`] when it counts whatever the undecided ones do, [`Status::Void`] when it cannot count,
//! and [`Status::Contested`] otherwise. Two cuts by keys of equal standing that undo each other stay
//! contested (rule 5).

use crate::derived;
use crate::layers::Concluded;
use crate::ops;
use crate::Row;
use alloc::collections::BTreeSet;
use alloc::vec::Vec;
use core::cell::OnceCell;

/// What the cut reads of a row. The slots are the caller's (a key, a seat, a window, a contest).
pub trait CutSpec<R: Row> {
    /// A slot.
    type Slot: Ord + Clone;
    /// What a cut says on its slots; two concurrent cuts that say the same thing do not contest each other.
    type Say: Ord + Clone;
    /// The slot of a key: every row is on its signer's key slot, and a removal cuts it.
    fn key_slot(&self, k: &R::Key) -> Self::Slot;
    /// The slots a row is on, its signer's key slot included.
    fn on_slots(&self, r: &R) -> BTreeSet<Self::Slot>;
    /// The slots a row cuts; empty for a row that is not a cut.
    fn cuts_of(&self, r: &R) -> BTreeSet<Self::Slot>;
    /// What a cut says.
    fn says(&self, r: &R) -> Self::Say;
    /// The distinct signers among its live voices it needs (default one).
    fn need(&self, _r: &R) -> usize {
        1
    }
    /// The ids in its past, on a slot it cuts, that it voids: how a row naming both decides (rule 3).
    fn rejects(&self, _r: &R) -> Vec<R::Id> {
        Vec::new()
    }
    /// Whether `cosign`, a concluded row the cut names, is a voice for it.
    fn is_voice_for(&self, _cosign: &R, _cut: &R) -> bool {
        false
    }
    /// The trust root this node reads, for a stalled recovery ([`crate::seat::recovery_verdict`]); None (the
    /// default): such a recovery is undecided, and concludes nothing.
    #[allow(clippy::type_complexity)]
    fn trust_root(&self) -> Option<&dyn crate::root::RootView<R::Id, R::Key, crate::seat::Obj<R::Id, R::Key>>> {
        None
    }
    /// The key lane a count reads at its voices step ([`crate::seat::voices_with`]): each voice by the end rule
    /// ([`crate::key_end::counts_by`]). A store with key records MUST supply it; `None` (the default) lets every
    /// voice count, which is only for a caller with no key lane.
    fn key_view(&self) -> Option<&dyn crate::key_end::KeyView<R::Id, R::Key>> {
        None
    }
}

/// The status of a row under the cut.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum Status {
    /// The row did not conclude.
    ConcludesNothing,
    /// It counts whatever the undecided cuts do.
    Counts,
    /// It counts under some resolution of the undecided cuts and not under another.
    Contested,
    /// It cannot count.
    Void,
}

/// Who holds a slot under the cut.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Holder<V> {
    /// One value.
    Held(V),
    /// No row on the slot counts.
    Empty,
    /// Two values, or a contested row on the slot that no counting cut answers.
    Conflict,
}

/// The cut over a concluded set.
pub struct Cut<'c, 'a, R: Row, S: CutSpec<R>> {
    /// The concluded set.
    pub c: &'c Concluded<'a, R>,
    spec: &'c S,
    cuts: Vec<usize>,
    lo: BTreeSet<usize>,
    hi: BTreeSet<usize>,
    /// Each row's status, kept once asked: the cut is solved when built, so a status never changes.
    memo: Vec<OnceCell<Status>>,
}

impl<'c, 'a, R: Row, S: CutSpec<R>> Cut<'c, 'a, R, S> {
    /// Solve the cut by the well-founded fixed point.
    pub fn new(c: &'c Concluded<'a, R>, spec: &'c S) -> Self {
        Self::new_without(c, spec, &BTreeSet::new())
    }

    /// [`Cut::new`], with the rows of `without` cutting nothing (a counted act void for a reader: the reader's
    /// line is read before the cut, `seat::Seats`).
    pub fn new_without(c: &'c Concluded<'a, R>, spec: &'c S, without: &BTreeSet<usize>) -> Self {
        let cuts: Vec<usize> =
            c.cs().iter().copied().filter(|&i| !without.contains(&i) && !spec.cuts_of(c.g.row(i)).is_empty()).collect();
        let memo = (0..c.g.len()).map(|_| OnceCell::new()).collect();
        let mut me = Cut { c, spec, cuts, lo: BTreeSet::new(), hi: BTreeSet::new(), memo };
        let bound = me.cuts.len() + 2;
        let lo = ops::fix(BTreeSet::new(), bound, |l| me.t(&me.t(l)));
        me.hi = me.t(&lo);
        me.lo = lo;
        me
    }

    fn voided(&self, r: usize, slots: &BTreeSet<S::Slot>, a: &BTreeSet<usize>, as_cut: bool) -> bool {
        let g = &self.c.g;
        let rr = g.row(r);
        for &x in &self.cuts {
            if !a.contains(&x) || x == r {
                continue;
            }
            let xr = g.row(x);
            let xs = self.spec.cuts_of(xr);
            if self.spec.rejects(xr).iter().any(|i| i == rr.id()) && g.in_past(r, x) {
                let mine: BTreeSet<S::Slot> = self.spec.on_slots(rr).union(&self.spec.cuts_of(rr)).cloned().collect();
                if xs.intersection(&mine).next().is_some() {
                    return true;
                }
            }
            if !g.concurrent(x, r) {
                continue;
            }
            let mut hit: BTreeSet<S::Slot> = xs.intersection(slots).cloned().collect();
            if as_cut && self.spec.says(xr) == self.spec.says(rr) {
                for s in self.spec.cuts_of(rr) {
                    hit.remove(&s);
                }
            }
            if !hit.is_empty() {
                return true;
            }
        }
        false
    }

    fn voices(&self, cut: usize) -> Vec<usize> {
        let g = &self.c.g;
        let cr = g.row(cut);
        let mut v = alloc::vec![cut];
        for n in cr.names() {
            if let Some(q) = g.idx(n) {
                if self.c.concluded(q) && self.spec.is_voice_for(g.row(q), cr) {
                    v.push(q);
                }
            }
        }
        v
    }

    /// The cuts that count if exactly the cuts in `a` do the voiding.
    fn t(&self, a: &BTreeSet<usize>) -> BTreeSet<usize> {
        let g = &self.c.g;
        let mut out = BTreeSet::new();
        for &c in &self.cuts {
            let cr = g.row(c);
            let live: Vec<usize> = self
                .voices(c)
                .into_iter()
                .filter(|&v| {
                    let ks: BTreeSet<S::Slot> = core::iter::once(self.spec.key_slot(g.row(v).signer())).collect();
                    !self.voided(v, &ks, a, false)
                })
                .collect();
            if ops::count(live.iter().map(|&v| g.row(v).signer())) < self.spec.need(cr) {
                continue;
            }
            let mut slots = self.spec.on_slots(cr);
            slots.remove(&self.spec.key_slot(cr.signer()));
            slots.extend(self.spec.cuts_of(cr));
            if self.voided(c, &slots, a, true) {
                continue;
            }
            out.insert(c);
        }
        out
    }

    /// The status of row `i`.
    pub fn status(&self, i: usize) -> Status {
        *self.memo[i].get_or_init(|| self.solve(i))
    }

    fn solve(&self, i: usize) -> Status {
        if !self.c.concluded(i) {
            return Status::ConcludesNothing;
        }
        if self.cuts.is_empty() {
            // a concluded row that cuts a slot is among the cuts, so with none every concluded row counts
            return Status::Counts;
        }
        let r = self.c.g.row(i);
        if !self.spec.cuts_of(r).is_empty() {
            return if self.lo.contains(&i) {
                Status::Counts
            } else if self.hi.contains(&i) {
                Status::Contested
            } else {
                Status::Void
            };
        }
        let sl = self.spec.on_slots(r);
        if self.voided(i, &sl, &self.lo, false) {
            return Status::Void;
        }
        if self.voided(i, &sl, &self.hi, false) {
            Status::Contested
        } else {
            Status::Counts
        }
    }

    /// Whether row `i` counts.
    pub fn counts(&self, i: usize) -> bool {
        self.status(i) == Status::Counts
    }

    /// Who holds `slot`: the slot rule over the rows on it that count. A contested row on the slot that no
    /// counting cut has in its past leaves it in conflict. `on` says which rows are on the slot (the key slot
    /// of a signer is not meant here).
    pub fn holder<V: Ord + Clone>(
        &self,
        on: impl Fn(&R) -> bool,
        picks: impl Fn(&R) -> Option<R::Id>,
        value: impl Fn(&R) -> V,
    ) -> Holder<V> {
        let g = &self.c.g;
        let rows: Vec<usize> = self.c.cs().iter().copied().filter(|&i| on(g.row(i))).collect();
        let settled: Vec<usize> =
            rows.iter().copied().filter(|&x| !self.spec.cuts_of(g.row(x)).is_empty() && self.counts(x)).collect();
        if rows.iter().any(|&r| self.status(r) == Status::Contested && !settled.iter().any(|&x| g.in_past(r, x))) {
            return Holder::Conflict;
        }
        let counting: Vec<usize> = rows.iter().copied().filter(|&r| self.counts(r)).collect();
        match derived::slot(self.c, &counting, picks, value) {
            (Some(h), 1) => Holder::Held(h),
            (_, 0) => Holder::Empty,
            _ => Holder::Conflict,
        }
    }
}
