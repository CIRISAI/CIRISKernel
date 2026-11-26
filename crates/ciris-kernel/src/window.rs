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
//!
//! **A ballot** (CIRISConstitution#221) is an answer a [`How::MoreOfVoted`] clause reads: its value or its
//! `against` (the moderation fallback's `ballot:moderation_action`, `for` or `against`; the family is the
//! caller's). One ballot a person, folded as `ballot:moderator` is: agreeing ballots are one and disagreeing
//! ones say nothing ([`ops::one`], the fold every answer has here). A ballot its own signer withdrew (a
//! withdrawal row naming it, concluded by the seat rule) is no ballot ([`unwithdrawn`]); a withdrawal
//! concurrent with a landing is recounted with it, as an answer is. An answer that is no ballot is read as
//! before, withdrawn or not.

use crate::cut::CutSpec;
use crate::layers::{Concluded, Past};
use crate::ops;
use crate::seat::{
    self, members_in, members_in_scopes, persons, seat_rule, Obj, Policy, SeatKind, SeatLaw, SeatRow, AGENT,
};
use crate::Row;
use alloc::collections::{BTreeMap, BTreeSet};
use alloc::string::String;
use alloc::vec::Vec;

/// What a window row is.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum WinKind {
    /// It opens a window. A row may be an act of the seat as well (an offer or an unseat that opens its own
    /// window: a moderator's lone removal of an agent's key): it then concludes only where the seat's rule
    /// concludes it too.
    Open,
    /// It answers one.
    Answer,
    /// The concluder's receipt of the opener. One that has a row of the target in its past, beyond what the
    /// opener has in its own, is no receipt, and a landing naming it concludes nothing.
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
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum How {
    /// A strict majority of the keys counted.
    Strict,
    /// One voice.
    One,
    /// At least `max(least, ceil(num * n / den))`.
    AtLeast(u64, u64, u64),
    /// More than `num / den` of n.
    More(u64, u64),
    /// More than `num / den` of n, and never fewer than `least` voices (a strict majority with a floor).
    MoreAtLeast(u64, u64, u64),
    /// `MoreOfVoted(num, den, least, against)`: more than `num / den` of the keys of the base that voted, and
    /// never fewer than `least` voices. A key voted if it said the clause's value or `against`; a silent key
    /// is not counted over (the moderation fallback: "a strict majority of the members who voted, never fewer
    /// than two voices").
    MoreOfVoted(u64, u64, u64, String),
}

/// Which keys a clause counts over.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Base {
    /// The window's counted scope at the opener's head, less the agents there (every count of a room is by
    /// person: an AI agent's key, seated in [`AGENT`], is no voice and is not counted over).
    All,
    /// The same, less the opener's signer: out of the voices and out of the size counted over (the members'
    /// check: a strict majority of the members seated at the head the act names, the act's author apart).
    /// Where the opener is a moderator's lone removal of an agent's key, the key it removes is an agent's and
    /// so in no count, on every path: the count with no landing, a landing's, and the recount.
    Others,
    /// Another scope at the opener's head, less the agents there (in no count, for every scope), except in a
    /// clause one holder's act resolves ([`How::One`]), which reads an agent holder's act.
    Scope(String),
    /// The opener's signer alone: the proposer's own voice (its withdrawal of an open proposal).
    Opener,
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
    /// The scope the opener's signer holds, where it is not the counted one (a duty holder's act that the
    /// members may lift opens its own window). `None`: the counted scope.
    pub opener: Option<String>,
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
    /// No landing has concluded and the answers held meet no at-once count.
    Open,
    /// Two landings that stand state different outcomes, or none stands.
    Contested,
    /// The outcome the standing landings state, or, where no landing has concluded, the outcome of an at-once
    /// count the answers held meet (a count that is met needs no clock and no concluder).
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
    /// Whether any row read holds a seat of [`AGENT`] scope: without one, no key is an agent's here.
    fn has_agents(&self) -> bool {
        self.rows.iter().any(|q| q.scope().is_some_and(|s| s.as_ref() == AGENT))
    }

    fn base(&self, b: &Base) -> BTreeSet<R::Key> {
        let (name, scope) = match b {
            Base::Opener => return core::iter::once(self.opener_signer.clone()).collect(),
            Base::All => ("all", self.w.counted.as_str()),
            Base::Others => ("others", self.w.counted.as_str()),
            Base::Scope(s) => (s.as_str(), s.as_str()),
        };
        if let Some(m) = self.cache.borrow().get(name) {
            return m.clone();
        }
        let mut m = members_in(self.rows, self.past, self.law, self.spec, &self.obj, self.head, scope);
        if scope != AGENT && self.has_agents() {
            // in no count: the agents at the head are out of the base and the voices for every scope a clause
            // reads, a named one (`moderate`) included
            let agents = members_in(self.rows, self.past, self.law, self.spec, &self.obj, self.head, AGENT);
            m = persons(m, &agents);
        }
        if matches!(b, Base::Others) {
            m.remove(&self.opener_signer);
        }
        self.cache.borrow_mut().insert(name.into(), m.clone());
        m
    }

    /// The keys a clause one holder's act resolves ([`How::One`]) reads over `b`: for a named scope its
    /// holders, agents included (an agent acts under its seat by the acts one signature resolves); for any
    /// other base, [`Ctx::base`].
    fn held(&self, b: &Base) -> BTreeSet<R::Key> {
        let Base::Scope(s) = b else { return self.base(b) };
        let key = alloc::format!("held|{s}");
        if let Some(m) = self.cache.borrow().get(&key) {
            return m.clone();
        }
        let m = members_in(self.rows, self.past, self.law, self.spec, &self.obj, self.head, s);
        self.cache.borrow_mut().insert(key, m.clone());
        m
    }

    /// Read every scope the table reads (and `extra`, returned) in one walk of the seats at the head, and keep
    /// them as [`Ctx::base`] would. A clause over a scope named `all` or `others` shares a name with
    /// [`Base::All`] or [`Base::Others`] in the cache, so then each is left to be read when first asked.
    fn prefill(&self, extra: Option<&str>) -> Option<BTreeSet<R::Key>> {
        let w = self.w;
        let named: Vec<&str> = w
            .at_once
            .iter()
            .chain(&w.at_close)
            .filter_map(|c| match &c.over {
                Base::Scope(s) => Some(s.as_str()),
                _ => None,
            })
            .collect();
        let read = |scope: &str| members_in(self.rows, self.past, self.law, self.spec, &self.obj, self.head, scope);
        if named.iter().any(|s| *s == "all" || *s == "others") {
            return extra.map(read);
        }
        let mut scopes: Vec<&str> = alloc::vec![w.counted.as_str(), "moderate", AGENT];
        scopes.extend(named.iter().copied());
        scopes.extend(extra);
        let mut sets = members_in_scopes(self.rows, self.past, self.law, self.spec, &self.obj, self.head, &scopes);
        let got = extra.and_then(|_| sets.pop());
        let mut cache = self.cache.borrow_mut();
        // a count of the room is by person: the agents at the head are no voice and not counted over
        let at_head = sets[2].clone();
        let agents = if w.counted == AGENT { BTreeSet::new() } else { at_head.clone() };
        let mut others = persons(sets[0].clone(), &agents);
        others.remove(&self.opener_signer);
        cache.insert("others".into(), others);
        cache.insert("all".into(), persons(sets[0].clone(), &agents));
        for (scope, set) in scopes.iter().zip(sets).skip(1) {
            // a named scope's base leaves its agents out too; its holders, agents included, are what a clause
            // one holder's act resolves reads
            cache.insert(alloc::format!("held|{scope}"), set.clone());
            let set = if *scope == AGENT { set } else { persons(set, &at_head) };
            cache.insert((*scope).into(), set);
        }
        got
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
    voters.extend(x.held(&Base::Scope("moderate".into())));
    voters.extend(tv.iter().cloned());
    // the proposer's withdrawal is its own voice on the opener's clause, and never replaces what it said by opening
    let is_wd = |a: &&R| *a.signer() == x.opener_signer && a.says().is_some_and(|w| w.as_ref() == "withdraw");
    let withdrawn = answers.iter().any(is_wd);
    // a duty holder's single-signature answer (a value an at-once clause reads as one voice over a named scope,
    // said by a holder of that scope) is what that key said: a vote the same key also cast is moot
    let mut duty: BTreeMap<&str, &Base> = BTreeMap::new();
    for cl in &w.at_once {
        if cl.how == How::One && matches!(cl.over, Base::Scope(_)) {
            duty.insert(cl.value.as_str(), &cl.over);
        }
    }
    let duty_word = |a: &R| a.says().and_then(|s| duty.get(s.as_ref()).copied());
    let acted: BTreeSet<&R::Key> = answers
        .iter()
        .copied()
        .filter(|a| voters.contains(a.signer()) && !is_wd(a))
        .filter(|a| duty_word(a).is_some_and(|b| x.held(b).contains(a.signer())))
        .map(|a| a.signer())
        .collect();
    let moot = |a: &R| acted.contains(a.signer()) && duty_word(a).is_none();
    // a voice that says two things says nothing
    let by = ops::group_by(answers.iter().copied().filter(|a| voters.contains(a.signer()) && !is_wd(a)), |a| {
        a.signer().clone()
    });
    let mut said: BTreeMap<R::Key, String> = BTreeMap::new();
    for (s, rs) in by {
        let heard = rs.iter().filter(|a| !moot(a));
        if let Some(v) = ops::one(heard.filter_map(|a| a.says().map(|w| String::from(w.as_ref())))) {
            said.insert(s, v);
        }
    }
    if let Some(o) = &w.opener_says {
        said.entry(x.opener_signer.clone()).or_insert_with(|| o.clone());
    }
    let met = |cl: &Clause, floor: bool| {
        if cl.over == Base::Opener {
            return if cl.value == "withdraw" { withdrawn } else { said.get(&x.opener_signer) == Some(&cl.value) };
        }
        // a count (a fraction, a floor) leaves the agents out; a clause one holder's act resolves reads them
        let keys = if cl.how == How::One { x.held(&cl.over) } else { x.base(&cl.over) };
        let yes = said
            .iter()
            .filter(|(s, v)| {
                **v == cl.value && (keys.contains(*s) || (floor && tv.contains(*s) && cl.value == "approve"))
            })
            .count();
        // CC 4.5.13: two comparisons (strictly more than a fraction, at least a fraction), each read by the
        // seat's count, with a floor in voices and a choice of base
        let n = keys.len();
        let more = |num, den, base| seat::met(Some(Policy::Strict(num, den)), yes, base, None);
        match &cl.how {
            &How::AtLeast(num, den, least) => {
                seat::met(Some(Policy::AtLeast(num, den)), yes, n, None) && yes as u64 >= least
            }
            &How::More(num, den) => more(num, den, n),
            &How::MoreAtLeast(num, den, least) => more(num, den, n) && yes as u64 >= least,
            How::MoreOfVoted(num, den, least, against) => {
                let no = said.iter().filter(|(s, v)| *v == against && keys.contains(*s)).count();
                more(*num, *den, yes + no) && yes as u64 >= *least
            }
            How::One => seat::met(Some(Policy::One), yes, n, None),
            How::Strict => more(1, 2, n),
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

/// The words a ballot says: the value and the `against` of each [`How::MoreOfVoted`] clause of `w`.
pub fn ballot_words<T>(w: &WindowSpec<T>) -> BTreeSet<&str> {
    let mut out = BTreeSet::new();
    for cl in w.at_once.iter().chain(&w.at_close) {
        if let How::MoreOfVoted(_, _, _, against) = &cl.how {
            out.insert(cl.value.as_str());
            out.insert(against.as_str());
        }
    }
    out
}

/// The rows of `answers` less each one saying a word of `words` that its own signer withdrew by a
/// withdrawal among `rows` (one ballot a person, folded as `ballot:moderator`: a withdrawn ballot is no
/// ballot; CC 2.4.1.1 rule 1). Pass the concluded rows: a withdrawal by another key does not conclude. The
/// fold of the ballots left is [`ops::one`] per signer. Any caller folding ballots of its own (an election's)
/// may read its withdrawals here.
pub fn unwithdrawn<'r, R: SeatRow>(
    answers: Vec<&'r R>,
    rows: &[&R],
    words: &BTreeSet<&str>,
    says: impl Fn(&R) -> Option<&str>,
) -> Vec<&'r R> {
    let wd: BTreeSet<(&R::Id, &R::Key)> = rows
        .iter()
        .filter(|w| w.seat_kind() == SeatKind::Withdraw)
        .filter_map(|w| w.target().map(|t| (t, w.signer())))
        .collect();
    answers
        .into_iter()
        .filter(|a| !says(*a).is_some_and(|v| words.contains(v)) || !wd.contains(&(a.id(), a.signer())))
        .collect()
}

fn says_of<R: WindowRow>(a: &R) -> Option<&str> {
    a.says().map(|s| s.as_ref())
}

/// The answers that are voices: an approval that has the proposer's withdrawal in its past approves nothing.
fn voices_of<'r, R: WindowRow>(
    answers: Vec<&'r R>,
    opener: &R::Key,
    past: &dyn Fn(&R::Id, &R::Id) -> bool,
) -> Vec<&'r R> {
    let says = |a: &R, w: &str| a.says().is_some_and(|s| s.as_ref() == w);
    let wd: Vec<&R::Id> =
        answers.iter().filter(|a| a.signer() == opener && says(a, "withdraw")).map(|a| a.id()).collect();
    answers.iter().copied().filter(|a| !(says(a, "approve") && wd.iter().any(|w| past(w, a.id())))).collect()
}

/// The conclusion rule for a window row; `None` for a row that is not one (conclude it by the seat). An
/// opener that is also an offer or an unseat is concluded here by both rules.
pub fn rule<R: WindowRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    windows: &Tables<'_, R>,
    law: &SeatLaw,
    spec: &S,
) -> Option<bool> {
    rule_with(p, windows, law, spec, true)
}

/// [`rule`], with every scope the table reads walked at once (`prefill`) or each read when first asked (the
/// two must agree; this module's tests compare them).
fn rule_with<R: WindowRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    windows: &Tables<'_, R>,
    law: &SeatLaw,
    spec: &S,
    prefill: bool,
) -> Option<bool> {
    let r = p.row();
    let k = r.win_kind()?;
    let rows: Vec<&R> = p.rows().collect();
    let past = |a: &R::Id, b: &R::Id| p.past(a, b);
    if k == WinKind::Open {
        let (Some(w), Some(obj)) = (r.window().and_then(windows), r.obj()) else { return Some(false) };
        // an act that opens its own window is validly made by the seat's rule too
        if matches!(r.seat_kind(), SeatKind::Offer | SeatKind::Unseat) && !seat_rule(p, law, spec, &|_| true) {
            return Some(false);
        }
        let scope = w.opener.as_ref().unwrap_or(&w.counted);
        return Some(members_in(&rows, &past, law, spec, &obj, r.head(), scope).contains(r.signer()));
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
    let concluders = if prefill {
        x.prefill(Some(&w.concluder)).unwrap_or_default()
    } else {
        members_in(&rows, &past, law, spec, &obj, o.head(), &w.concluder)
    };
    if !concluders.contains(r.signer()) {
        return Some(false);
    }
    if k == WinKind::Receipt {
        // a receipt puts no row of the target before the window: none in its past that the opener's past does
        // not hold
        let Some(t) = o.target_key() else { return Some(true) };
        return Some(!rows.iter().any(|q| q.signer() == t && q.id() != o.id() && !p.past(q.id(), o.id())));
    }
    let Some(rec) = r.receipt().and_then(|x| p.get(x)) else { return Some(false) };
    if rec.win_kind() != Some(WinKind::Receipt) || rec.signer() != r.signer() || rec.of() != Some(o.id()) {
        return Some(false);
    }
    let answers: Vec<&R> = voices_of(
        unwithdrawn(
            rows.iter().copied().filter(|q| q.win_kind() == Some(WinKind::Answer) && q.of() == Some(o.id())).collect(),
            &rows,
            &ballot_words(&w),
            says_of,
        ),
        o.signer(),
        &past,
    );
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
    outcome_with(c, pid, windows, law, spec, cut_counts, true)
}

fn outcome_with<R: WindowRow, S: CutSpec<R>>(
    c: &Concluded<'_, R>,
    pid: usize,
    windows: &Tables<'_, R>,
    law: &SeatLaw,
    spec: &S,
    cut_counts: &dyn Fn(usize) -> bool,
    prefill: bool,
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
    if prefill {
        x.prefill(None);
    }
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
    voters.extend(x.held(&Base::Scope("moderate".into())));
    if w.target_votes {
        voters.extend(p.target_key().cloned());
    }
    if ls.is_empty() {
        // no landing has concluded: a count that is met needs no clock and no concluder, so the table's at-once
        // outcome over the answers held is the outcome; short of it the window is open
        let held: Vec<&R> = c
            .cs()
            .iter()
            .copied()
            .filter(|&r| g.row(r).win_kind() == Some(WinKind::Answer) && g.row(r).of() == Some(p.id()) && !late(r))
            .map(|r| g.row(r))
            .collect();
        let counted: Vec<&R> = c.cs().iter().copied().filter(|&r| !late(r)).map(|r| g.row(r)).collect();
        let held = unwithdrawn(held, &counted, &ballot_words(&w), says_of);
        let got = table_outcome(&x, p.target_key(), &voices_of(held, p.signer(), &past), &[], false);
        return if got == "open" { Outcome::Open } else { Outcome::Landed(got) };
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
        let mut inside: Vec<&R> =
            mine.iter().copied().filter(|&q| q != rec && !g.in_past(q, rec)).map(|q| g.row(q)).collect();
        inside.extend(tgt.iter().copied());
        let mut answers: Vec<&R> = mine
            .iter()
            .map(|&q| g.row(q))
            .filter(|q| q.win_kind() == Some(WinKind::Answer) && q.of() == Some(p.id()))
            .collect();
        answers.extend(ans);
        // a withdrawal of a ballot concurrent with the landing is recounted with it, as an answer is
        let wrows: Vec<&R> = mine.iter().chain(&conc).map(|&q| g.row(q)).collect();
        let answers = voices_of(unwithdrawn(answers, &wrows, &ballot_words(&w), says_of), p.signer(), &past);
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::layers::conclude;
    use crate::seat::{seat_rule, Conf};
    use alloc::vec;

    struct Lcg(u64);
    impl Lcg {
        fn next(&mut self, n: u64) -> u64 {
            self.0 = self.0.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
            (self.0 >> 33) % n.max(1)
        }
    }

    #[derive(Clone, Debug)]
    struct W {
        id: u32,
        names: Vec<u32>,
        signer: u32,
        kind: SeatKind,
        to: Vec<u32>,
        cosigners: Vec<u32>,
        scope: Option<String>,
        obj: Option<Obj<u32, u32>>,
        conf: Option<Conf>,
        head: Vec<u32>,
        of: Option<u32>,
        win: Option<WinKind>,
        window: Option<String>,
        says: Option<String>,
        receipt: Option<u32>,
        at: Option<i64>,
    }

    impl W {
        fn new(id: u32, names: Vec<u32>, signer: u32) -> W {
            W {
                id,
                names,
                signer,
                kind: SeatKind::Other,
                to: vec![],
                cosigners: vec![],
                scope: None,
                obj: None,
                conf: None,
                head: vec![],
                of: None,
                win: None,
                window: None,
                says: None,
                receipt: None,
                at: None,
            }
        }
    }

    impl Row for W {
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

    impl SeatRow for W {
        type Word = String;
        fn seat_kind(&self) -> SeatKind {
            self.kind
        }
        fn to(&self) -> &[u32] {
            &self.to
        }
        fn cosigners(&self) -> &[u32] {
            &self.cosigners
        }
        fn scope(&self) -> Option<&String> {
            self.scope.as_ref()
        }
        fn obj(&self) -> Option<Obj<u32, u32>> {
            self.obj.clone()
        }
        fn conf(&self) -> Option<Conf> {
            self.conf
        }
        fn head(&self) -> &[u32] {
            &self.head
        }
        fn of(&self) -> Option<&u32> {
            self.of.as_ref()
        }
    }

    impl WindowRow for W {
        type T = i64;
        fn win_kind(&self) -> Option<WinKind> {
            self.win
        }
        fn window(&self) -> Option<&String> {
            self.window.as_ref()
        }
        fn says(&self) -> Option<&String> {
            self.says.as_ref()
        }
        fn receipt(&self) -> Option<&u32> {
            self.receipt.as_ref()
        }
        fn at(&self) -> Option<i64> {
            self.at
        }
    }

    struct NoCut;
    impl CutSpec<W> for NoCut {
        type Slot = u32;
        type Say = ();
        fn key_slot(&self, k: &u32) -> u32 {
            *k
        }
        fn on_slots(&self, r: &W) -> BTreeSet<u32> {
            core::iter::once(r.signer).collect()
        }
        fn cuts_of(&self, _r: &W) -> BTreeSet<u32> {
            BTreeSet::new()
        }
        fn says(&self, _r: &W) {}
    }

    const SCOPES: [&str; 5] = ["member", "moderate", "all", "others", "concl"];
    const OUTS: [&str; 3] = ["enact", "cancel", "open"];

    fn clauses(g: &mut Lcg) -> Vec<Clause> {
        (0..g.next(3))
            .map(|_| Clause {
                value: if g.next(3) == 0 { "no".into() } else { "approve".into() },
                how: match g.next(4) {
                    0 => How::Strict,
                    1 => How::One,
                    2 => How::AtLeast(2, 3, 1),
                    _ => How::More(1, 2),
                },
                over: match g.next(6) {
                    0 => Base::All,
                    1 => Base::Others,
                    2 => Base::Scope("moderate".into()),
                    3 if g.next(3) == 0 => Base::Scope("all".into()),
                    4 if g.next(3) == 0 => Base::Scope("others".into()),
                    _ => Base::Scope("concl".into()),
                },
                out: OUTS[g.next(2) as usize].into(),
            })
            .collect()
    }

    /// A group with seats in five scopes (two named `all` and `others`), an opener at its version, answers,
    /// the concluder's receipt and landings, under a generated table: every conclusion and the outcome are
    /// the same whether the scopes the table reads are walked at once or each when first asked.
    #[test]
    fn prefilled_scopes_answer_as_scopes_read_when_asked() {
        let law = SeatLaw::default();
        let mut g = Lcg(3);
        let (mut cases, mut bad, mut landed) = (0usize, 0usize, 0usize);
        for _ in 0..3_000 {
            let n = 2 + g.next(6) as u32;
            let mut f = W::new(0, vec![], 1);
            f.kind = SeatKind::Offer;
            f.to = vec![1];
            f.scope = Some("member".into());
            f.obj = Some(Obj::Row(0));
            f.conf = Some(Conf::Own);
            let mut rows = vec![f];
            let mut id = 10;
            for k in 1..=n {
                for sc in SCOPES {
                    if (sc == "member" && k == 1) || g.next(3) == 0 {
                        continue;
                    }
                    let mut o = W::new(id, vec![0], 1);
                    o.kind = SeatKind::Offer;
                    o.to = vec![k];
                    if k != 1 {
                        o.cosigners = vec![k];
                    }
                    o.scope = Some(sc.into());
                    o.obj = Some(Obj::Row(0));
                    o.conf = Some(Conf::Own);
                    rows.push(o);
                    id += 1;
                }
            }
            // now and then the last key holds an agent's seat as well: every base leaves it out, read either way
            if (id + n).is_multiple_of(4) {
                let mut o = W::new(id, vec![0], 1);
                o.kind = SeatKind::Offer;
                o.to = vec![n];
                o.cosigners = vec![n];
                o.scope = Some(AGENT.into());
                o.obj = Some(Obj::Row(0));
                o.conf = Some(Conf::Own);
                rows.push(o);
            }
            let v = W::new(100, rows.iter().map(|r| r.id).collect(), 1);
            rows.push(v);
            let mut op = W::new(200, vec![100], 1 + g.next(n as u64) as u32);
            op.win = Some(WinKind::Open);
            op.window = Some("w".into());
            op.obj = Some(Obj::Row(0));
            op.head = vec![100];
            rows.push(op);
            let mut answers = vec![];
            for j in 0..g.next(2 * n as u64) as u32 {
                let mut a = W::new(300 + j, vec![200], 1 + g.next(n as u64 + 1) as u32);
                a.win = Some(WinKind::Answer);
                a.of = Some(200);
                a.says = Some(if g.next(3) == 0 { "no".into() } else { "approve".into() });
                answers.push(a.id);
                rows.push(a);
            }
            let c_key = 1 + g.next(n as u64) as u32;
            let mut rc = W::new(400, vec![200], c_key);
            rc.win = Some(WinKind::Receipt);
            rc.of = Some(200);
            rc.at = Some(0);
            rows.push(rc);
            for l in 0..1 + g.next(2) as u32 {
                let named: Vec<u32> = answers.iter().copied().filter(|_| g.next(2) == 0).collect();
                let mut ld = W::new(500 + l, [vec![400], named].concat(), c_key);
                ld.win = Some(WinKind::Landing);
                ld.of = Some(200);
                ld.receipt = Some(400);
                ld.at = Some(g.next(100) as i64);
                ld.says = Some(OUTS[g.next(3) as usize].into());
                rows.push(ld);
            }
            let spec = WindowSpec {
                counted: "member".into(),
                concluder: if g.next(2) == 0 { "concl".into() } else { "member".into() },
                opener: None,
                opener_says: if g.next(2) == 0 { Some("approve".into()) } else { None },
                at_once: clauses(&mut g),
                silent: None,
                at_close: clauses(&mut g),
                default: "cancel".into(),
                target_votes: false,
                secs: 50,
            };
            let tables = |w: &String| if w == "w" { Some(spec.clone()) } else { None };
            let concl = |prefill: bool| {
                conclude(
                    rows.iter(),
                    |p| match rule_with(p, &tables, &law, &NoCut, prefill) {
                        Some(v) => v,
                        None => seat_rule(p, &law, &NoCut, &|_| true),
                    },
                    None,
                )
            };
            let (a, b) = (concl(true), concl(false));
            cases += 1;
            bad += (a.all() != b.all()) as usize;
            let op = a.g.idx(&200).unwrap();
            let oa = outcome_with(&a, op, &tables, &law, &NoCut, &|_| true, true);
            let ob = outcome_with(&a, op, &tables, &law, &NoCut, &|_| true, false);
            landed += matches!(oa, Outcome::Landed(_)) as usize;
            cases += 1;
            bad += (oa != ob) as usize;
        }
        assert!(landed > 300, "only {landed} windows landed");
        assert_eq!(bad, 0, "{bad} of {cases} differ");
    }
}
