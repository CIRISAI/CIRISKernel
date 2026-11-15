//! **window**: a window as rows (KERNEL.md section 5; CC 2.7.5). `window.py`, the recount rule.
//!
//! A row opens a window; an answer names it; a receipt is the concluder's own holding of the opener, at its
//! own instant; a landing names that receipt, states its own instant and the outcome. "Inside the window"
//! is a relation between rows: in the past of the landing and not in the past of the receipt. The length is
//! the concluder's own two instants; no instant of one signer is compared with another's.
//!
//! A landing concludes iff its signer held the concluder's seat at the head the opener names, it names its
//! own receipt, and the outcome it states is the one the table gives over its own past. An answer
//! concurrent with the landing is **recounted**: it is counted with the landing's past, and the landing
//! stands only if the table still gives the outcome it stated (`Recount.dishonest_never_stands`,
//! `stands_is_table_over_all_not_late`). A row of a key whose seat over the object was ended counts only if
//! the ending row has it in its past, and a landing that does not stand says nothing against one that does.
//!
//! The two rejected rules (the landing voids concurrent answers; any concurrent answer contests it) are not
//! implemented; KERNEL.md runs them only as the reason.

use crate::cut::CutSpec;
use crate::layers::{Concluded, Past};
use crate::ops;
use crate::seat::{members_in, Obj, SeatKind, SeatLaw, SeatRow};
use crate::Row;
use alloc::collections::{BTreeMap, BTreeSet};
use alloc::string::String;
use alloc::vec::Vec;

/// What a window row is.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum WinKind {
    /// It opens a window.
    Open,
    /// It answers one.
    Answer,
    /// The concluder's receipt of the opener.
    Receipt,
    /// The concluder's landing.
    Landing,
}

/// The fields a window reads.
pub trait WindowRow: SeatRow {
    /// An instant (the signer's own).
    type T: Ord + Copy + core::ops::Sub<Output = Self::T>;
    /// What the row is, if a window row.
    fn win_kind(&self) -> Option<WinKind>;
    /// An opener: the window's name in the table.
    fn window(&self) -> Option<&Self::Word> {
        None
    }
    /// An opener: the key it targets (an eviction's target).
    fn target_key(&self) -> Option<&Self::Key> {
        None
    }
    /// An answer or a landing: what it says.
    fn says(&self) -> Option<&Self::Word> {
        None
    }
    /// A landing: the receipt it names.
    fn receipt(&self) -> Option<&Self::Id> {
        None
    }
    /// A receipt or a landing: the signer's own instant.
    fn at(&self) -> Option<Self::T> {
        None
    }
}

/// How a clause counts.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum How {
    /// A strict majority of the keys counted.
    Strict,
    /// One voice.
    One,
    /// At least `max(least, ceil(num * n / den))`.
    AtLeast(u64, u64, u64),
    /// More than `num / den` of n.
    More(u64, u64),
}

/// Which keys a clause counts over.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Base {
    /// The window's counted scope at the opener's head.
    All,
    /// The same, less the opener's signer.
    Others,
    /// Another scope at the opener's head.
    Scope(String),
}

/// One clause of a window's table: if `value` is said by enough of `over`, the outcome is `out`.
#[derive(Clone, Debug)]
pub struct Clause {
    /// What a voice says.
    pub value: String,
    /// How many.
    pub how: How,
    /// Of whom.
    pub over: Base,
    /// The outcome.
    pub out: String,
}

/// A window's table (the policy row, the clauses read at once and at the close, and the default).
#[derive(Clone, Debug)]
pub struct WindowSpec<T> {
    /// The scope counted.
    pub counted: String,
    /// The scope of the concluder.
    pub concluder: String,
    /// What the opener's signer says by opening.
    pub opener_says: Option<String>,
    /// Clauses that close the window at once.
    pub at_once: Vec<Clause>,
    /// The outcome when the target signed anything inside the window.
    pub silent: Option<String>,
    /// Clauses read at the close.
    pub at_close: Vec<Clause>,
    /// The outcome at the close otherwise.
    pub default: String,
    /// The joiner's own yes is a voice of the floor.
    pub target_votes: bool,
    /// The length, from the policy table.
    pub secs: T,
}

/// The outcome of a window.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Outcome {
    /// The opener is not held or did not conclude.
    None,
    /// No landing concluded yet.
    Open,
    /// Two landings that stand state different outcomes, or none stands.
    Contested,
    /// The outcome the standing landings state.
    Landed(String),
}

type ObjOf<R> = Obj<<R as Row>::Id, <R as Row>::Key>;

/// The window tables, looked up by an opener's window name.
pub type Tables<'w, R> = dyn Fn(&<R as SeatRow>::Word) -> Option<WindowSpec<<R as WindowRow>::T>> + 'w;

struct Ctx<'x, R: WindowRow, S: CutSpec<R>> {
    rows: &'x [&'x R],
    past: &'x dyn Fn(&R::Id, &R::Id) -> bool,
    law: &'x SeatLaw,
    spec: &'x S,
    obj: ObjOf<R>,
    head: &'x [R::Id],
    opener_signer: R::Key,
    w: &'x WindowSpec<R::T>,
    cache: core::cell::RefCell<BTreeMap<String, BTreeSet<R::Key>>>,
}

impl<'x, R: WindowRow, S: CutSpec<R>> Ctx<'x, R, S> {
    fn base(&self, b: &Base) -> BTreeSet<R::Key> {
        let (name, scope) = match b {
            Base::All => ("all", self.w.counted.as_str()),
            Base::Others => ("others", self.w.counted.as_str()),
            Base::Scope(s) => (s.as_str(), s.as_str()),
        };
        if let Some(m) = self.cache.borrow().get(name) {
            return m.clone();
        }
        let mut m = members_in(self.rows, self.past, self.law, self.spec, &self.obj, self.head, scope);
        if matches!(b, Base::Others) {
            m.remove(&self.opener_signer);
        }
        self.cache.borrow_mut().insert(name.into(), m.clone());
        m
    }
}

fn table_outcome<R: WindowRow, S: CutSpec<R>>(
    x: &Ctx<'_, R, S>,
    target: Option<&R::Key>,
    answers: &[&R],
    inside: &[&R],
    elapsed: bool,
) -> String {
    let w = x.w;
    let tv: BTreeSet<R::Key> = if w.target_votes { target.cloned().into_iter().collect() } else { BTreeSet::new() };
    let mut voters = x.base(&Base::All);
    voters.extend(x.base(&Base::Scope("moderate".into())));
    voters.extend(tv.iter().cloned());
    // a voice that says two things says nothing
    let by = ops::group_by(answers.iter().copied().filter(|a| voters.contains(a.signer())), |a| a.signer().clone());
    let mut said: BTreeMap<R::Key, String> = BTreeMap::new();
    for (s, rs) in by {
        if let Some(v) = ops::one(rs.iter().filter_map(|a| a.says().map(|w| String::from(w.as_ref())))) {
            said.insert(s, v);
        }
    }
    if let Some(o) = &w.opener_says {
        said.entry(x.opener_signer.clone()).or_insert_with(|| o.clone());
    }
    let met = |cl: &Clause, floor: bool| {
        let keys = x.base(&cl.over);
        let yes = said
            .iter()
            .filter(|(s, v)| **v == cl.value && (keys.contains(*s) || (floor && tv.contains(*s) && cl.value == "approve")))
            .count() as u64;
        let n = keys.len() as u64;
        match cl.how {
            How::AtLeast(num, den, least) => yes >= core::cmp::max(least, (num * n).div_ceil(den)),
            How::More(num, den) => yes * den > num * n,
            How::One => yes >= 1,
            How::Strict => 2 * yes > n,
        }
    };
    for cl in &w.at_once {
        if met(cl, false) {
            return cl.out.clone();
        }
    }
    if !elapsed {
        return "open".into();
    }
    if let (Some(s), Some(t)) = (&w.silent, target) {
        if inside.iter().any(|q| q.signer() == t) {
            return s.clone();
        }
    }
    for cl in &w.at_close {
        if met(cl, true) {
            return cl.out.clone();
        }
    }
    w.default.clone()
}

/// The conclusion rule for a window row; `None` for a row that is not one (conclude it by the seat).
pub fn rule<R: WindowRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    windows: &Tables<'_, R>,
    law: &SeatLaw,
    spec: &S,
) -> Option<bool> {
    let r = p.row();
    let k = r.win_kind()?;
    let rows: Vec<&R> = p.rows().collect();
    let past = |a: &R::Id, b: &R::Id| p.past(a, b);
    if k == WinKind::Open {
        let (Some(w), Some(obj)) = (r.window().and_then(windows), r.obj()) else { return Some(false) };
        return Some(members_in(&rows, &past, law, spec, &obj, r.head(), &w.counted).contains(r.signer()));
    }
    let Some(o) = r.of().and_then(|o| p.get(o)) else { return Some(false) };
    if o.win_kind() != Some(WinKind::Open) {
        return Some(false);
    }
    if k == WinKind::Answer {
        return Some(true); // whether its voice counts is read against the roster at the opener's head
    }
    let (Some(w), Some(obj)) = (o.window().and_then(windows), o.obj()) else { return Some(false) };
    let x = Ctx {
        rows: &rows,
        past: &past,
        law,
        spec,
        obj: obj.clone(),
        head: o.head(),
        opener_signer: o.signer().clone(),
        w: &w,
        cache: Default::default(),
    };
    if !members_in(&rows, &past, law, spec, &obj, o.head(), &w.concluder).contains(r.signer()) {
        return Some(false);
    }
    if k == WinKind::Receipt {
        return Some(true);
    }
    let Some(rec) = r.receipt().and_then(|x| p.get(x)) else { return Some(false) };
    if rec.win_kind() != Some(WinKind::Receipt) || rec.signer() != r.signer() || rec.of() != Some(o.id()) {
        return Some(false);
    }
    let answers: Vec<&R> = rows.iter().copied().filter(|q| q.win_kind() == Some(WinKind::Answer) && q.of() == Some(o.id())).collect();
    let inside: Vec<&R> = rows.iter().copied().filter(|q| q.id() != rec.id() && !p.past(q.id(), rec.id())).collect();
    let elapsed = match (r.at(), rec.at()) {
        (Some(a), Some(b)) => a >= b && a - b >= w.secs,
        _ => false,
    };
    let got = table_outcome(&x, o.target_key(), &answers, &inside, elapsed);
    Some(r.says().is_some_and(|s| s.as_ref() == got))
}

/// The outcome of window `pid` under recount, given which rows count under the cut.
pub fn outcome<R: WindowRow, S: CutSpec<R>>(
    c: &Concluded<'_, R>,
    pid: usize,
    windows: &Tables<'_, R>,
    law: &SeatLaw,
    spec: &S,
    cut_counts: &dyn Fn(usize) -> bool,
) -> Outcome {
    let g = &c.g;
    if !c.concluded(pid) {
        return Outcome::None;
    }
    let p = g.row(pid);
    let (Some(w), Some(obj)) = (p.window().and_then(windows), p.obj()) else { return Outcome::None };
    let ls: Vec<usize> = c
        .cs()
        .iter()
        .copied()
        .filter(|&i| g.row(i).win_kind() == Some(WinKind::Landing) && g.row(i).of() == Some(p.id()))
        .collect();
    if ls.is_empty() {
        return Outcome::Open;
    }
    let rows: Vec<&R> = c.cs().iter().map(|&i| g.row(i)).collect();
    let past = |a: &R::Id, b: &R::Id| match (g.idx(a), g.idx(b)) {
        (Some(a), Some(b)) => g.in_past(a, b),
        _ => false,
    };
    let x = Ctx {
        rows: &rows,
        past: &past,
        law,
        spec,
        obj: obj.clone(),
        head: p.head(),
        opener_signer: p.signer().clone(),
        w: &w,
        cache: Default::default(),
    };
    // the rows that ended a seat over the object, with the keys each ended
    let mut gone: Vec<(BTreeSet<R::Key>, usize)> = Vec::new();
    for &u in c.cs() {
        let ur = g.row(u);
        if ur.seat_kind() == SeatKind::Unseat && ur.obj().as_ref() == Some(&obj) && cut_counts(u) {
            gone.push((ur.to().iter().cloned().collect(), u));
        }
    }
    for &wi in c.cs() {
        let wr = g.row(wi);
        if wr.seat_kind() != SeatKind::Withdraw {
            continue;
        }
        if let Some(o) = wr.target().and_then(|t| g.idx(t)).map(|t| g.row(t)) {
            if o.seat_kind() == SeatKind::Offer && o.obj().as_ref() == Some(&obj) {
                let ks = if o.to().contains(wr.signer()) {
                    core::iter::once(wr.signer().clone()).collect()
                } else {
                    o.to().iter().cloned().collect()
                };
                gone.push((ks, wi));
            }
        }
    }
    let late = |r: usize| gone.iter().any(|(ks, x)| ks.contains(g.row(r).signer()) && !g.in_past(r, *x));
    let mut voters = x.base(&Base::All);
    voters.extend(x.base(&Base::Scope("moderate".into())));
    if w.target_votes {
        voters.extend(p.target_key().cloned());
    }
    let mut said: Vec<Option<String>> = Vec::new();
    for l in g.frontier(&ls) {
        let lr = g.row(l);
        let conc: Vec<usize> = c.cs().iter().copied().filter(|&r| g.concurrent(r, l) && !late(r)).collect();
        let ans: Vec<&R> = conc
            .iter()
            .map(|&r| g.row(r))
            .filter(|r| r.win_kind() == Some(WinKind::Answer) && r.of() == Some(p.id()) && voters.contains(r.signer()))
            .collect();
        let tgt: Vec<&R> = match (&w.silent, p.target_key()) {
            (Some(_), Some(t)) => conc.iter().map(|&r| g.row(r)).filter(|r| r.signer() == t).collect(),
            _ => Vec::new(),
        };
        let Some(rec) = lr.receipt().and_then(|x| g.idx(x)) else {
            said.push(None);
            continue;
        };
        let mine: Vec<usize> = c.cs().iter().copied().filter(|&q| g.in_past(q, l)).collect();
        let mut inside: Vec<&R> = mine.iter().copied().filter(|&q| q != rec && !g.in_past(q, rec)).map(|q| g.row(q)).collect();
        inside.extend(tgt.iter().copied());
        let mut answers: Vec<&R> = mine
            .iter()
            .map(|&q| g.row(q))
            .filter(|q| q.win_kind() == Some(WinKind::Answer) && q.of() == Some(p.id()))
            .collect();
        answers.extend(ans);
        let elapsed = match (lr.at(), g.row(rec).at()) {
            (Some(a), Some(b)) => a >= b && a - b >= w.secs,
            _ => false,
        };
        let again = table_outcome(&x, p.target_key(), &answers, &inside, elapsed);
        let says = lr.says().map(|s| String::from(s.as_ref()));
        said.push(if says.as_deref() == Some(again.as_str()) { says } else { None });
    }
    // a landing that does not stand is no voice against one that does
    let standing: Vec<String> = said.iter().flatten().cloned().collect();
    match ops::one(standing) {
        Some(v) => Outcome::Landed(v),
        None => Outcome::Contested,
    }
}
