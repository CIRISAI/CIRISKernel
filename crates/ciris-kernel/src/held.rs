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
//! **Memory.** A held row's past is kept only while the row is among the [`PAST_WINDOW`] used most recently
//! (kept, or named by a row kept since)
//! ([`Held::set_past_window`]). The pasts kept are compact where that is smaller ([`Bits`](crate::graph::Bits)).
//!
//! **Cost of one admission** (`Admitted::visited` counts it): for each row kept, one entry per id it names
//! (a binary search, or a map lookup for a row admitted here), its past as one bit-set walk over what it names
//! (`n / 64` words for `n` held rows), and the conclusion rule over its concluded past. Nothing is
//! proportional to the rows held except the bit set of the new row's past. A row that waits costs one map
//! entry per id it lacks.

use crate::layers::{Concluded, Past};
use crate::Row;
use alloc::collections::{BTreeMap, BTreeSet, VecDeque};
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
    /// The keys a row carries, for answers that read by key ("any row matching K"): a row that carries a key
    /// wakes every registered answer whose [`Reads`] names it ([`Held::register`]). None by default (0.3).
    fn keys(&self, _r: &R) -> Vec<R::Key> {
        Vec::new()
    }
    /// Whether any row this spec admits can carry key `k`. A registered read of a key no row can carry is a
    /// read with no possible writer: an answer that can never be woken ([`Held::unwritable`]). Every key by
    /// default (0.3).
    fn can_carry(&self, _k: &R::Key) -> bool {
        true
    }
}

/// What an answer read: row ids, and keys read by key ("any row matching K"). Sorted and each once, so two
/// recorders of the same reads agree byte for byte (0.3).
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct Reads<I, K> {
    ids: Vec<I>,
    keys: Vec<K>,
}

impl<I, K> Default for Reads<I, K> {
    fn default() -> Self {
        Reads { ids: Vec::new(), keys: Vec::new() }
    }
}

impl<I: Ord, K: Ord> Reads<I, K> {
    /// Nothing read.
    pub fn new() -> Self {
        Self::default()
    }
    /// These ids and keys, sorted and each once.
    pub fn of(ids: impl IntoIterator<Item = I>, keys: impl IntoIterator<Item = K>) -> Self {
        let mut ids: Vec<I> = ids.into_iter().collect();
        let mut keys: Vec<K> = keys.into_iter().collect();
        ids.sort_unstable();
        ids.dedup();
        keys.sort_unstable();
        keys.dedup();
        Reads { ids, keys }
    }
    /// The ids read, ascending.
    pub fn ids(&self) -> &[I] {
        &self.ids
    }
    /// The keys read, ascending.
    pub fn keys(&self) -> &[K] {
        &self.keys
    }
    /// Record an id read.
    pub fn add_id(&mut self, id: I) {
        if let Err(k) = self.ids.binary_search(&id) {
            self.ids.insert(k, id);
        }
    }
    /// Record a key read.
    pub fn add_key(&mut self, k: K) {
        if let Err(at) = self.keys.binary_search(&k) {
            self.keys.insert(at, k);
        }
    }
    /// Record everything `o` read.
    pub fn extend(&mut self, o: Reads<I, K>) {
        for i in o.ids {
            self.add_id(i);
        }
        for k in o.keys {
            self.add_key(k);
        }
    }
    /// Whether id `i` was read.
    pub fn reads_id(&self, i: &I) -> bool {
        self.ids.binary_search(i).is_ok()
    }
    /// Whether key `k` was read.
    pub fn reads_key(&self, k: &K) -> bool {
        self.keys.binary_search(k).is_ok()
    }
    /// Nothing was read.
    pub fn is_empty(&self) -> bool {
        self.ids.is_empty() && self.keys.is_empty()
    }
}

/// What a recording [`Past`] logged of one conclusion ([`Held::recorded_reads`]).
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Logged<I, K> {
    /// The rows the rule read through the past's methods.
    pub reads: Reads<I, K>,
    /// Whether that is all it read: `false` when it read the whole closure or the whole concluded past.
    pub complete: bool,
}

/// A registered answer ([`Held::register`]): the handle the caller re-runs when [`Admitted::wake`] names it.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct AnswerId(pub u64);

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
    /// The registered answers to run again (0.3): every answer whose [`Reads`] names a newly kept row's id, an
    /// id it names, or a key it carries ([`HeldSpec::keys`]). Ascending, each once.
    pub wake: Vec<AnswerId>,
    /// The foreign rows the dirty rows' answers read ([`Held::admit_foreign`]): every foreign row in the read
    /// set (the concluded past) of a row in `dirty`. Ascending, each once; empty when no foreign row is held
    /// (0.3.x).
    pub foreign: Vec<I>,
}

impl<I> Admitted<I> {
    /// Nothing kept, nothing dirty.
    pub fn none(waiting: bool, visited: usize) -> Self {
        Admitted { kept: Vec::new(), waiting, dirty: Vec::new(), visited, wake: Vec::new(), foreign: Vec::new() }
    }
}

struct Wait<'a, R> {
    row: &'a R,
    left: usize,
    foreign: bool,
}

/// The kept and concluded layers, held. Rows are borrowed for `'a`; the caller owns the rows and the `Held`.
pub struct Held<'a, R: Row, S> {
    spec: S,
    con: Concluded<'a, R>,
    /// Whether each held row has a root at or above it (all `true` when the spec has no seed).
    rooted: Vec<bool>,
    /// Whether each held row is foreign: held for reads, not a member of the scope ([`Held::admit_foreign`]).
    foreign: Vec<bool>,
    /// How many held rows are foreign.
    foreigners: usize,
    /// The rows offered whose names are not all held, by id.
    waiting: BTreeMap<R::Id, Wait<'a, R>>,
    /// For each id not held that a waiting row names, the waiting rows that name it.
    waiting_on: BTreeMap<R::Id, Vec<R::Id>>,
    /// The rows whose pasts stay computed, least recently used first, as (use, row). A row is used when it
    /// is kept and whenever a row kept later names it. An entry whose use is older than the row's last use is
    /// stale and skipped.
    recent: VecDeque<(u64, usize)>,
    /// Each row's last use; 0 for a row not in the window.
    last_use: Vec<u64>,
    /// The uses so far, and how many rows are in the window.
    uses: u64,
    live: usize,
    /// How many rows' pasts stay computed ([`Held::set_past_window`]).
    window: usize,
    /// For each held id, the held rows that name it (0.3).
    named_by: BTreeMap<R::Id, Vec<usize>>,
    /// The registered answers, with what each read, and the indexes over them (0.3).
    answers: BTreeMap<AnswerId, Reads<R::Id, R::Key>>,
    by_id: BTreeMap<R::Id, BTreeSet<AnswerId>>,
    by_key: BTreeMap<R::Key, BTreeSet<AnswerId>>,
    next_answer: u64,
}

/// How many rows keep their pasts computed (the most recently used), unless [`Held::set_past_window`] says.
pub const PAST_WINDOW: usize = 64;

impl<'a, R: Row, S: Clone> Clone for Held<'a, R, S> {
    fn clone(&self) -> Self {
        Held {
            spec: self.spec.clone(),
            con: self.con.clone(),
            rooted: self.rooted.clone(),
            foreign: self.foreign.clone(),
            foreigners: self.foreigners,
            waiting: self
                .waiting
                .iter()
                .map(|(k, w)| (k.clone(), Wait { row: w.row, left: w.left, foreign: w.foreign }))
                .collect(),
            waiting_on: self.waiting_on.clone(),
            recent: self.recent.clone(),
            last_use: self.last_use.clone(),
            uses: self.uses,
            live: self.live,
            window: self.window,
            named_by: self.named_by.clone(),
            answers: self.answers.clone(),
            by_id: self.by_id.clone(),
            by_key: self.by_key.clone(),
            next_answer: self.next_answer,
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
            foreign: Vec::new(),
            foreigners: 0,
            waiting: BTreeMap::new(),
            waiting_on: BTreeMap::new(),
            recent: VecDeque::new(),
            last_use: Vec::new(),
            uses: 0,
            live: 0,
            window: PAST_WINDOW,
            named_by: BTreeMap::new(),
            answers: BTreeMap::new(),
            by_id: BTreeMap::new(),
            by_key: BTreeMap::new(),
            next_answer: 0,
        }
    }

    /// Keep the pasts of the `w` rows used most recently, and drop the rest as rows are kept (`usize::MAX`
    /// keeps every past, as [`layers::conclude`](crate::layers::conclude) does while it runs). A row is used
    /// when it is kept and whenever a row kept later names it, so a row many later rows name stays in the
    /// window however old it is.
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
    /// Mark row `i` used now: it moves to the newest end of the window.
    fn touch(&mut self, i: usize) {
        if self.last_use.len() <= i {
            self.last_use.resize(i + 1, 0);
        }
        self.uses += 1;
        if self.last_use[i] == 0 {
            self.live += 1;
        }
        self.last_use[i] = self.uses;
        self.recent.push_back((self.uses, i));
    }
    /// Drop the pasts of the least recently used rows until at most `window` remain, and the stale entries.
    fn trim(&mut self) {
        while self.live > self.window {
            let (u, j) = self.recent.pop_front().expect("live rows have entries");
            if self.last_use[j] != u {
                continue; // stale: used again since
            }
            self.last_use[j] = 0;
            self.live -= 1;
            self.con.g.forget_past(j);
        }
        // a hot row leaves one stale entry per use: keep the deque within a constant of the rows in the window
        if self.recent.len() > 4 * self.live + 64 {
            let last = &self.last_use;
            self.recent.retain(|&(u, j)| last[j] == u);
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
        self.admit_as(r, false)
    }

    /// Admit a foreign row (0.3.x): a row outside the view's scope that a rule or gate reads (an owner seat
    /// read from a group's gate, a trust root read from anywhere). It is held, concluded and named exactly as a
    /// member is, so the answers over it equal the whole fold, but it is never in [`Admitted::dirty`]: the
    /// caller runs no door of the scope for it. A member whose read set holds it lists it in
    /// [`Admitted::foreign`]. The view never assumes the world closed: an id neither held nor supplied leaves
    /// the rows naming it waiting, as any admission does. Refused, changing nothing, as [`Held::admit`].
    pub fn admit_foreign(&mut self, r: &'a R) -> Result<Admitted<R::Id>, Refused> {
        self.admit_as(r, true)
    }

    /// Whether the held or waiting row with this id is foreign ([`Held::admit_foreign`]).
    pub fn is_foreign(&self, id: &R::Id) -> bool {
        match self.con.g.idx(id) {
            Some(i) => self.foreign[i],
            None => self.waiting.get(id).is_some_and(|w| w.foreign),
        }
    }

    fn admit_as(&mut self, r: &'a R, foreign: bool) -> Result<Admitted<R::Id>, Refused> {
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
            self.waiting.insert(id.clone(), Wait { row: r, left: lacks.len(), foreign });
            return Ok(Admitted::none(true, visited));
        }
        // every id it names is held: keep it, then whatever it releases
        let mut kept: Vec<R::Id> = Vec::new();
        let mut dirty: Vec<R::Id> = Vec::new();
        let mut ready: Vec<(&'a R, bool)> = alloc::vec![(r, foreign)];
        while let Some((x, fx)) = ready.pop() {
            self.keep(x, fx);
            visited += 1;
            kept.push(x.id().clone());
            if !fx {
                dirty.push(x.id().clone());
            }
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
                        ready.push((e.row, e.foreign));
                    }
                }
            }
        }
        dirty.sort_unstable();
        let mut wake: BTreeSet<AnswerId> = BTreeSet::new();
        for id in &kept {
            if let Some(i) = self.con.g.idx(id) {
                wake.extend(self.wakes_for(self.con.g.row(i)));
            }
        }
        let foreign = self.foreign_read(&dirty);
        Ok(Admitted { kept, waiting: false, dirty, visited, wake: wake.into_iter().collect(), foreign })
    }

    /// The foreign rows in the read sets of rows `ids`: their concluded foreign ancestors, ascending, each once.
    fn foreign_read(&self, ids: &[R::Id]) -> Vec<R::Id> {
        if self.foreigners == 0 {
            return Vec::new();
        }
        let g = &self.con.g;
        let all = self.con.all();
        let mut out: BTreeSet<&R::Id> = BTreeSet::new();
        for id in ids {
            let Some(i) = g.idx(id) else { continue };
            out.extend(g.ancestors(i).iter().filter(|&q| self.foreign[q] && all[q]).map(|q| g.row(q).id()));
        }
        out.into_iter().cloned().collect()
    }

    /// Admit rows in order; refusals are skipped. Returns every row kept, in order, and the dirty set.
    pub fn admit_all(&mut self, rows: impl IntoIterator<Item = &'a R>) -> Admitted<R::Id> {
        let mut all = Admitted::none(false, 0);
        let mut wake: BTreeSet<AnswerId> = BTreeSet::new();
        for r in rows {
            if let Ok(a) = self.admit(r) {
                all.kept.extend(a.kept);
                all.dirty.extend(a.dirty);
                all.visited += a.visited;
                wake.extend(a.wake);
            }
        }
        all.dirty.sort_unstable();
        all.wake = wake.into_iter().collect();
        all.foreign = self.foreign_read(&all.dirty);
        all
    }

    /// Keep a row whose every named id is held, and conclude it.
    fn keep(&mut self, r: &'a R, foreign: bool) {
        let i = self.con.g.push(r).expect("not held, and every name held");
        self.foreign.push(foreign);
        self.foreigners += foreign as usize;
        let g = &self.con.g;
        let rooted = !self.spec.seeded() || self.spec.root(r) || g.named(i).iter().any(|&p| self.rooted[p]);
        self.rooted.push(rooted);
        let c = !g.waiting(i) && rooted && {
            let all = self.con.all();
            let p: Vec<usize> = g.ancestors(i).iter().filter(|&q| all[q]).collect();
            self.spec.conclude(&Past::new(g, i, &p))
        };
        self.con.conclude_pushed(c);
        for &p in self.con.g.named(i) {
            self.named_by.entry(self.con.g.row(p).id().clone()).or_default().push(i);
        }
        // the rows it names were just used as shortcuts: they stay in the window, then so does it
        let named: Vec<usize> = self.con.g.named(i).to_vec();
        for p in named {
            if self.con.g.has_past(p) {
                self.touch(p);
            }
        }
        self.touch(i);
        self.trim();
    }

    /// The held rows that name `id`, ascending by id (0.3): the by-name index, so the rows a new row of a given
    /// id answers are a lookup.
    pub fn named_by(&self, id: &R::Id) -> Vec<&'a R::Id> {
        let g = &self.con.g;
        let mut v: Vec<&'a R::Id> = self.named_by.get(id).into_iter().flatten().map(|&q| g.row(q).id()).collect();
        v.sort_unstable();
        v
    }

    /// The sound read set of row `id`'s conclusion (0.3): the row and its concluded ancestors, by id. A
    /// conclusion reads nothing else (`Causal.concl_final`, `conclOf_local`), so this is complete for any rule.
    /// `None` when `id` is not held.
    pub fn reads_of(&self, id: &R::Id) -> Option<Reads<R::Id, R::Key>> {
        let g = &self.con.g;
        let i = g.idx(id)?;
        let all = self.con.all();
        let p: Vec<usize> = g.ancestors(i).iter().filter(|&q| all[q]).collect();
        let past = Past::new(g, i, &p);
        Some(Reads::of(past.reads().into_iter().map(|q| g.row(q).id().clone()), core::iter::empty()))
    }

    /// The rows row `id`'s conclusion rule actually read, by running it again through a recording [`Past`]
    /// (0.3), and whether that log is complete: `false` when the rule read the whole closure or the whole
    /// concluded past ([`Past::graph`], [`Past::ancestors`]), in which case [`Held::reads_of`] is the read set.
    /// `None` when `id` is not held, waits on a cycle, or has no root.
    pub fn recorded_reads(&self, id: &R::Id) -> Option<Logged<R::Id, R::Key>> {
        let g = &self.con.g;
        let i = g.idx(id)?;
        if g.waiting(i) || !self.rooted[i] {
            return None;
        }
        let all = self.con.all();
        let p: Vec<usize> = g.ancestors(i).iter().filter(|&q| all[q]).collect();
        let log = core::cell::RefCell::new(crate::layers::Recorded::default());
        let _ = self.spec.conclude(&Past::recording(g, i, &p, &log));
        let log = log.into_inner();
        Some(Logged {
            reads: Reads::of(log.read.into_iter().map(|q| g.row(q).id().clone()), core::iter::empty()),
            complete: !log.escaped,
        })
    }

    /// Register an answer's reads; the returned handle is named in [`Admitted::wake`] whenever a newly kept row
    /// carries an id or key it read (0.3).
    pub fn register(&mut self, reads: Reads<R::Id, R::Key>) -> AnswerId {
        let h = AnswerId(self.next_answer);
        self.next_answer += 1;
        self.index(h, &reads);
        self.answers.insert(h, reads);
        h
    }
    /// Replace what answer `h` read (after it ran again). `false`, changing nothing, when `h` is not registered.
    pub fn update(&mut self, h: AnswerId, reads: Reads<R::Id, R::Key>) -> bool {
        if !self.answers.contains_key(&h) {
            return false;
        }
        self.unregister(h);
        self.index(h, &reads);
        self.answers.insert(h, reads);
        true
    }
    /// Forget answer `h`; returns what it read.
    pub fn unregister(&mut self, h: AnswerId) -> Option<Reads<R::Id, R::Key>> {
        let r = self.answers.remove(&h)?;
        for i in r.ids() {
            if let Some(s) = self.by_id.get_mut(i) {
                s.remove(&h);
                if s.is_empty() {
                    self.by_id.remove(i);
                }
            }
        }
        for k in r.keys() {
            if let Some(s) = self.by_key.get_mut(k) {
                s.remove(&h);
                if s.is_empty() {
                    self.by_key.remove(k);
                }
            }
        }
        Some(r)
    }
    /// What answer `h` read.
    pub fn registered(&self, h: AnswerId) -> Option<&Reads<R::Id, R::Key>> {
        self.answers.get(&h)
    }
    fn index(&mut self, h: AnswerId, r: &Reads<R::Id, R::Key>) {
        for i in r.ids() {
            self.by_id.entry(i.clone()).or_default().insert(h);
        }
        for k in r.keys() {
            self.by_key.entry(k.clone()).or_default().insert(h);
        }
    }
    /// The registered answers row `r` would wake if kept: those whose reads name its id, an id it names, or a
    /// key it carries ([`HeldSpec::keys`]). Ascending (0.3).
    pub fn wakes_for(&self, r: &R) -> Vec<AnswerId> {
        let mut w: BTreeSet<AnswerId> = BTreeSet::new();
        for id in core::iter::once(r.id()).chain(r.names().iter()) {
            if let Some(s) = self.by_id.get(id) {
                w.extend(s.iter().copied());
            }
        }
        for k in self.spec.keys(r) {
            if let Some(s) = self.by_key.get(&k) {
                w.extend(s.iter().copied());
            }
        }
        w.into_iter().collect()
    }
    /// Every registered key no row this spec admits can carry ([`HeldSpec::can_carry`]): a read with no possible
    /// writer, so an answer that can never be woken by key. Ascending (0.3).
    pub fn unwritable(&self) -> Vec<(AnswerId, R::Key)> {
        let mut v: Vec<(AnswerId, R::Key)> = self
            .by_key
            .iter()
            .filter(|(k, _)| !self.spec.can_carry(k))
            .flat_map(|(k, hs)| hs.iter().map(move |h| (*h, k.clone())))
            .collect();
        v.sort_unstable();
        v
    }

    /// Room for `rows` more rows naming `names` ids in all, so the next admissions do not grow a buffer. A
    /// clone has no spare room: reserve after cloning when the next admission's time matters.
    pub fn reserve(&mut self, rows: usize, names: usize) {
        self.con.reserve(rows, names);
        self.rooted.reserve(rows);
        self.foreign.reserve(rows);
        self.last_use.reserve(rows);
        self.recent.reserve(rows + names);
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
    differential_foreign(spec, order, |_| false)
}

/// [`differential`], with the rows `foreign` picks admitted as foreign rows ([`Held::admit_foreign`]) and the
/// rest as members (0.3.x). The answers must still equal the whole fold over every row offered; `dirty` must be
/// the members newly kept, and [`Admitted::foreign`] exactly the concluded foreign ancestors of those, by the
/// fold's own closure.
pub fn differential_foreign<R: Row, S: HeldSpec<R>>(
    spec: S,
    order: &[R],
    foreign: impl Fn(&R) -> bool,
) -> Result<(), Mismatch<R::Id>> {
    let mut h = Held::empty(spec);
    let fail = |prefix: usize, id: Option<&R::Id>, what: &'static str| Mismatch { prefix, id: id.cloned(), what };
    for k in 0..order.len() {
        let before: Vec<R::Id> = h.con.g.rows().iter().map(|r| r.id().clone()).collect();
        let waiting_before = h.waiting.len();
        let foreign_before = h.foreigners;
        let mut admitted: Option<Admitted<R::Id>> = None;
        match h.admit_as(&order[k], foreign(&order[k])) {
            Err(_) => {
                let after: Vec<R::Id> = h.con.g.rows().iter().map(|r| r.id().clone()).collect();
                if after != before || h.waiting.len() != waiting_before || h.foreigners != foreign_before {
                    return Err(fail(k + 1, Some(order[k].id()), "refused but changed"));
                }
            }
            Ok(a) => {
                let mut fresh: Vec<R::Id> = h.con.g.rows()[before.len()..]
                    .iter()
                    .filter(|r| !h.is_foreign(r.id()))
                    .map(|r| r.id().clone())
                    .collect();
                fresh.sort_unstable();
                if a.dirty != fresh {
                    return Err(fail(k + 1, Some(order[k].id()), "dirty is not the members newly kept"));
                }
                admitted = Some(a);
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
        if let Some(a) = &admitted {
            let mut want: Vec<R::Id> = Vec::new();
            for d in &a.dirty {
                let Some(fi) = fg.idx(d) else { continue };
                want.extend(
                    fg.ancestors(fi)
                        .iter()
                        .filter(|&q| full.concluded(q) && foreign(fg.row(q)))
                        .map(|q| fg.row(q).id().clone()),
                );
            }
            want.sort_unstable();
            want.dedup();
            if a.foreign != want {
                return Err(fail(k + 1, Some(order[k].id()), "foreign is not the foreign rows the dirty rows read"));
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
