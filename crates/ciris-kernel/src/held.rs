//! The two layers, kept and concluded, held across admissions (KERNEL.md section 3; CC 2.7.3, 2.7.10). Issue
//! #4 and `HELD.md`.
//!
//! [`layers::arrive`](crate::layers::arrive) and [`layers::conclude`](crate::layers::conclude) build the
//! layers whole from the rows given. A [`Held`] is the same two layers as a value the caller owns: rows are
//! admitted one at a time, and an admission computes only the row and the rows it releases (rows that waited
//! on it). No earlier conclusion is read again, because none can change: a conclusion reads the row and its
//! concluded ancestors only, and is final once the row is kept (`Causal.concl_final`; T6 ii). A new row is
//! no earlier row's ancestor. That is the whole of the locality theorem (T6 iii, `conclOf_local`) at this
//! layer: the rows a new row can change are itself and its descendants, and a held row's descendants are not
//! held before it is.
//!
//! What a `Held` answers equals [`layers::conclude`](crate::layers::conclude) over
//! [`layers::kept`](crate::layers::kept) of every row admitted, in every order of admission;
//! [`differential`] checks it after every admission, and the crate's tests run it.
//!
//! Pure and sync: no I/O, no clock, no global state. The cache is the `Held` value itself; dropping it drops
//! everything. A refused admission changes nothing, and a `Held` is `Clone`, so a caller inside a transaction
//! that may roll back can keep the value it had.
//!
//! **Memory.** A held row's past is kept only while the row is among the [`PAST_WINDOW`] kept most recently
//! ([`Held::set_past_window`]). The pasts kept are compact where that is smaller ([`Bits`](crate::graph::Bits)).
//!
//! **Cost of one admission** (`Admitted::visited` counts it): for each row kept, one entry per id it names
//! (a binary search, or a map lookup for a row admitted here), its past as one bit-set walk over what it names
//! (`n / 64` words for `n` held rows), and the conclusion rule over its concluded past. Nothing is
//! proportional to the rows held except the bit set of the new row's past. A row that waits costs one map
//! entry per id it lacks.

use crate::layers::{Concluded, Past};
use crate::Row;
use alloc::collections::{BTreeMap, VecDeque};
use alloc::vec::Vec;

/// The rules of one layered fold, as a value a [`Held`] owns (so a `Held` can live across calls).
pub trait HeldSpec<R: Row> {
    /// Whether a row is well formed alone (signature, shape and the row's own bounds are the caller's).
    fn well_formed(&self, r: &R) -> bool;
    /// The conclusion rule: reads the row and its concluded ancestors.
    fn conclude(&self, p: &Past<'_, '_, R>) -> bool;
    /// Whether the fold has a seed: when `true`, a row with no [`root`](HeldSpec::root) at or above it
    /// concludes nothing (`conclude`'s `root`).
    fn seeded(&self) -> bool {
        false
    }
    /// Whether a row is a root of the seed. Read only when [`seeded`](HeldSpec::seeded).
    fn root(&self, _r: &R) -> bool {
        false
    }
}

/// A [`HeldSpec`] from two closures, with no seed.
#[derive(Clone, Copy)]
pub struct Rules<W, C> {
    /// Well formed alone.
    pub wf: W,
    /// The conclusion rule.
    pub rule: C,
}

impl<R: Row, W: Fn(&R) -> bool, C: Fn(&Past<'_, '_, R>) -> bool> HeldSpec<R> for Rules<W, C> {
    fn well_formed(&self, r: &R) -> bool {
        (self.wf)(r)
    }
    fn conclude(&self, p: &Past<'_, '_, R>) -> bool {
        (self.rule)(p)
    }
}

/// Why an admission was refused. A refused admission changes nothing.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Refused {
    /// The row's id is already held, or already waiting.
    Duplicate,
    /// The row is not well formed alone.
    NotWellFormed,
}

/// What one admission did.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Admitted<I> {
    /// The rows newly kept: the row itself, when all it names is held, and every row it released, in the
    /// order kept (each after everything it names).
    pub kept: Vec<I>,
    /// The row waits on an id not held.
    pub waiting: bool,
    /// The held rows whose answers at this layer changed: those newly kept, ascending, each once. No earlier
    /// row's conclusion can change; a derived answer that reads concurrency has a larger cone (`HELD.md`).
    pub dirty: Vec<I>,
    /// Work done: the rows kept plus the ids they and the row itself name. The bound the benches assert.
    pub visited: usize,
}

struct Wait<'a, R> {
    row: &'a R,
    left: usize,
}

/// The kept and concluded layers, held. Rows are borrowed for `'a`; the caller owns the rows and the `Held`.
pub struct Held<'a, R: Row, S> {
    spec: S,
    con: Concluded<'a, R>,
    /// Whether each held row has a root at or above it (all `true` when the spec has no seed).
    rooted: Vec<bool>,
    /// The rows offered whose names are not all held, by id.
    waiting: BTreeMap<R::Id, Wait<'a, R>>,
    /// For each id not held that a waiting row names, the waiting rows that name it.
    waiting_on: BTreeMap<R::Id, Vec<R::Id>>,
    /// The rows kept most recently, whose pasts stay computed; older rows' pasts are dropped.
    recent: VecDeque<usize>,
    /// How many rows' pasts stay computed ([`Held::set_past_window`]).
    window: usize,
}

/// How many of the rows kept most recently keep their pasts computed, unless [`Held::set_past_window`] says.
pub const PAST_WINDOW: usize = 64;

impl<'a, R: Row, S: Clone> Clone for Held<'a, R, S> {
    fn clone(&self) -> Self {
        Held {
            spec: self.spec.clone(),
            con: self.con.clone(),
            rooted: self.rooted.clone(),
            waiting: self.waiting.iter().map(|(k, w)| (k.clone(), Wait { row: w.row, left: w.left })).collect(),
            waiting_on: self.waiting_on.clone(),
            recent: self.recent.clone(),
            window: self.window,
        }
    }
}

impl<'a, R: Row, S: HeldSpec<R>> Held<'a, R, S> {
    /// Nothing held.
    pub fn empty(spec: S) -> Self {
        let mut g = crate::graph::Graph::new(core::iter::empty());
        g.set_compact(true);
        Held {
            spec,
            con: Concluded::with(g, None),
            rooted: Vec::new(),
            waiting: BTreeMap::new(),
            waiting_on: BTreeMap::new(),
            recent: VecDeque::new(),
            window: PAST_WINDOW,
        }
    }

    /// Keep the pasts of the `w` rows kept most recently, and drop the rest as rows are kept (`usize::MAX`
    /// keeps every past, as [`layers::conclude`](crate::layers::conclude) does while it runs).
    ///
    /// A past is read in full once, when its row is concluded. After that it serves only as a shortcut for the
    /// rows kept later that name it: a walk down from a new row takes a known past whole. New rows mostly name
    /// recent ones, so a window of recent pasts keeps that shortcut while the memory stays about
    /// `w × n / 64` words, not `n² / 128`. A dropped past is computed again when a question needs it. No
    /// answer depends on the window, only time and memory do.
    pub fn set_past_window(&mut self, w: usize) {
        self.window = w;
        self.trim();
    }
    /// What computing pasts has cost this view ([`PastCounts`](crate::graph::PastCounts)): `walked` against the
    /// rows admitted, measured on a caller's own rows, says whether the window is wide enough.
    pub fn past_counts(&self) -> crate::graph::PastCounts {
        self.con.g.past_counts()
    }
    /// How many recent rows keep their pasts.
    pub fn past_window(&self) -> usize {
        self.window
    }
    fn trim(&mut self) {
        while self.recent.len() > self.window {
            let j = self.recent.pop_front().expect("longer than the window");
            self.con.g.forget_past(j);
        }
    }

    /// The rows admitted in order, each refusal skipped: the same layers as
    /// [`layers::arrive`](crate::layers::arrive) over them.
    pub fn new(spec: S, rows: impl IntoIterator<Item = &'a R>) -> Self {
        let mut h = Self::empty(spec);
        for r in rows {
            let _ = h.admit(r);
        }
        h
    }

    /// Admit one row. Refused, changing nothing, when its id is held or waiting or it is not well formed.
    /// Otherwise it is kept when every id it names is held, and then so is every waiting row this releases;
    /// else it waits.
    pub fn admit(&mut self, r: &'a R) -> Result<Admitted<R::Id>, Refused> {
        let id = r.id();
        if self.con.g.idx(id).is_some() || self.waiting.contains_key(id) {
            return Err(Refused::Duplicate);
        }
        if !self.spec.well_formed(r) {
            return Err(Refused::NotWellFormed);
        }
        let mut visited = r.names().len();
        let mut lacks: Vec<&R::Id> = r.names().iter().filter(|n| self.con.g.idx(n).is_none()).collect();
        lacks.sort_unstable();
        lacks.dedup();
        if !lacks.is_empty() {
            for n in &lacks {
                self.waiting_on.entry((*n).clone()).or_default().push(id.clone());
            }
            self.waiting.insert(id.clone(), Wait { row: r, left: lacks.len() });
            return Ok(Admitted { kept: Vec::new(), waiting: true, dirty: Vec::new(), visited });
        }
        // every id it names is held: keep it, then whatever it releases
        let mut kept: Vec<R::Id> = Vec::new();
        let mut ready: Vec<&'a R> = alloc::vec![r];
        while let Some(x) = ready.pop() {
            self.keep(x);
            visited += 1;
            kept.push(x.id().clone());
            if let Some(ws) = self.waiting_on.remove(x.id()) {
                for w in ws {
                    let done = match self.waiting.get_mut(&w) {
                        Some(e) => {
                            e.left -= 1;
                            e.left == 0
                        }
                        None => false,
                    };
                    if done {
                        let e = self.waiting.remove(&w).expect("present above");
                        visited += e.row.names().len();
                        ready.push(e.row);
                    }
                }
            }
        }
        let mut dirty = kept.clone();
        dirty.sort_unstable();
        Ok(Admitted { kept, waiting: false, dirty, visited })
    }

    /// Admit rows in order; refusals are skipped. Returns every row kept, in order, and the dirty set.
    pub fn admit_all(&mut self, rows: impl IntoIterator<Item = &'a R>) -> Admitted<R::Id> {
        let mut all = Admitted { kept: Vec::new(), waiting: false, dirty: Vec::new(), visited: 0 };
        for r in rows {
            if let Ok(a) = self.admit(r) {
                all.kept.extend(a.kept);
                all.visited += a.visited;
            }
        }
        all.dirty = all.kept.clone();
        all.dirty.sort_unstable();
        all
    }

    /// Keep a row whose every named id is held, and conclude it.
    fn keep(&mut self, r: &'a R) {
        let i = self.con.g.push(r).expect("not held, and every name held");
        let g = &self.con.g;
        let rooted = !self.spec.seeded() || self.spec.root(r) || g.named(i).iter().any(|&p| self.rooted[p]);
        self.rooted.push(rooted);
        let c = !g.waiting(i) && rooted && {
            let all = self.con.all();
            let p: Vec<usize> = g.ancestors(i).iter().filter(|&q| all[q]).collect();
            self.spec.conclude(&Past { g, i, p: &p })
        };
        self.con.conclude_pushed(c);
        self.recent.push_back(i);
        self.trim();
    }

    /// Room for `rows` more rows naming `names` ids in all, so the next admissions do not grow a buffer. A
    /// clone has no spare room: reserve after cloning when the next admission's time matters.
    pub fn reserve(&mut self, rows: usize, names: usize) {
        self.con.reserve(rows, names);
        self.rooted.reserve(rows);
    }

    /// The held rows, their closure and every conclusion.
    pub fn concluded(&self) -> &Concluded<'a, R> {
        &self.con
    }
    /// The number of rows held.
    pub fn len(&self) -> usize {
        self.con.g.len()
    }
    /// Whether no row is held.
    pub fn is_empty(&self) -> bool {
        self.con.g.is_empty()
    }
    /// Whether a row with this id is held (kept).
    pub fn holds(&self, id: &R::Id) -> bool {
        self.con.g.idx(id).is_some()
    }
    /// Whether a row with this id was offered and waits.
    pub fn waits(&self, id: &R::Id) -> bool {
        self.waiting.contains_key(id)
    }
    /// The ids of the rows that wait, ascending.
    pub fn waiting(&self) -> impl Iterator<Item = &R::Id> + '_ {
        self.waiting.keys()
    }
    /// Whether the row with this id is held and concluded.
    pub fn concluded_id(&self, id: &R::Id) -> bool {
        self.con.concluded_id(id)
    }
    /// The rules.
    pub fn spec(&self) -> &S {
        &self.spec
    }
}

/// Where a [`Held`] and the whole fold disagreed.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Mismatch<I> {
    /// How many rows of the order had been offered.
    pub prefix: usize,
    /// The row the answers differ on, when there is one.
    pub id: Option<I>,
    /// Which answer differed.
    pub what: &'static str,
}

/// Admit `order` one row at a time and, after every admission, compare the held layers with
/// [`layers::conclude`](crate::layers::conclude) over [`layers::kept`](crate::layers::kept) of the rows
/// offered so far: the same kept set, each row's conclusion, level, what it names and the size of its past,
/// and, up to 64 rows, every question of the past. A refused admission must change nothing, and the dirty
/// set must be exactly the rows newly kept. Quadratic or worse; for tests, including the caller's own over
/// its own rows. Precondition: rows with the same id are the same row (ids are digests).
pub fn differential<R: Row, S: HeldSpec<R>>(spec: S, order: &[R]) -> Result<(), Mismatch<R::Id>> {
    let mut h = Held::empty(spec);
    let fail = |prefix: usize, id: Option<&R::Id>, what: &'static str| Mismatch { prefix, id: id.cloned(), what };
    for k in 0..order.len() {
        let before: Vec<R::Id> = h.con.g.rows().iter().map(|r| r.id().clone()).collect();
        let waiting_before = h.waiting.len();
        match h.admit(&order[k]) {
            Err(_) => {
                let after: Vec<R::Id> = h.con.g.rows().iter().map(|r| r.id().clone()).collect();
                if after != before || h.waiting.len() != waiting_before {
                    return Err(fail(k + 1, Some(order[k].id()), "refused but changed"));
                }
            }
            Ok(a) => {
                let mut fresh: Vec<R::Id> = h.con.g.rows()[before.len()..].iter().map(|r| r.id().clone()).collect();
                fresh.sort_unstable();
                if a.dirty != fresh {
                    return Err(fail(k + 1, Some(order[k].id()), "dirty is not the rows newly kept"));
                }
            }
        }
        let prefix = &order[..=k];
        let spec = &h.spec;
        let kept = crate::layers::kept(prefix, |r| spec.well_formed(r));
        let root = |r: &R| spec.root(r);
        let full = crate::layers::conclude(
            kept.iter().copied(),
            |p| spec.conclude(p),
            if spec.seeded() { Some(&root as &dyn Fn(&R) -> bool) } else { None },
        );
        let (hg, fg) = (&h.con.g, &full.g);
        if hg.len() != fg.len() {
            return Err(fail(k + 1, None, "kept sets differ in size"));
        }
        for fi in 0..fg.len() {
            let id = fg.row(fi).id();
            let Some(hi) = hg.idx(id) else {
                return Err(fail(k + 1, Some(id), "kept by the fold, not held"));
            };
            if h.con.concluded(hi) != full.concluded(fi) {
                return Err(fail(k + 1, Some(id), "conclusion"));
            }
            if hg.level(hi) != fg.level(fi) {
                return Err(fail(k + 1, Some(id), "level"));
            }
            let mut hn: Vec<&R::Id> = hg.named(hi).iter().map(|&q| hg.row(q).id()).collect();
            let mut fnm: Vec<&R::Id> = fg.named(fi).iter().map(|&q| fg.row(q).id()).collect();
            hn.sort_unstable();
            fnm.sort_unstable();
            if hn != fnm {
                return Err(fail(k + 1, Some(id), "names"));
            }
            if hg.depth(hi) != fg.depth(fi) {
                return Err(fail(k + 1, Some(id), "past"));
            }
        }
        if fg.len() <= 64 {
            for fa in 0..fg.len() {
                for fb in 0..fg.len() {
                    let (ha, hb) = (hg.idx(fg.row(fa).id()).unwrap(), hg.idx(fg.row(fb).id()).unwrap());
                    if hg.in_past(ha, hb) != fg.in_past(fa, fb) || hg.concurrent(ha, hb) != fg.concurrent(fa, fb) {
                        return Err(fail(k + 1, Some(fg.row(fa).id()), "in past / concurrent"));
                    }
                }
            }
        }
    }
    Ok(())
}
