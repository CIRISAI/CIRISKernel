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
//!
//! **The landing** of every window is one family (CIRISConstitution#221, W1): the receipt is a `window:held`
//! row and the landing a `window:landed` row stating the outcome. The family names are the caller's table
//! entries: the crate reads a row's [`WinKind`], never its family, and checks no family. The
//! moderation fallback's landing is signed by any member at the opener's head; the overturn's by any member
//! there but the act's author (W2): a key no clause counts is no concluder, so where every counted clause of
//! the table is over [`Base::Others`] ([`author_apart`]) the opener's signer signs no receipt and no landing.
//!
//! A table whose concluder is `local` (the accord's halt, ruled 2026-11-28: each node's own fuse, with no landing)
//! has no receipt and no landing that concludes; its at-once counts are read as any table's (the halt's confirmation,
//! a strict majority of the standing holders). The node's own fuse, on its own clock, is the node's and is not read
//! here.

use crate::cut::CutSpec;
use crate::layers::{Concluded, Past};
use crate::ops;
use crate::seat::{
    self, members_in, members_in_scopes, persons, seat_rule, Act, Choice, Obj, Policy, ScopeClass, SeatKind, SeatLaw,
    SeatRow, AGENT,
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
    /// An opener: the act it proposes, and the act's scope class (a lone eviction of a key: `remove`, `key`). Read
    /// only where the law binds acts ([`rule_bound`]): the acts table then names the policy row the window is of.
    fn proposes(&self) -> Option<(Act, ScopeClass)> {
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
    /// The base `active` above the base law's `k` (CIRISConstitution#221): the caller's stated count, the
    /// census's figure (CC 6.1.9), which the kernel takes and does not check. The voices are those of
    /// [`Base::All`]; the size counted over is the stated count where it is larger than the members
    /// [`Base::All`] reads, and never smaller (a caller cannot shrink a base below the members the rows seat).
    Stated(u64),
}

/// One clause of a window's table: if `value` is said by enough of `over`, the outcome is `out`.
#[derive(Clone, Debug, PartialEq, Eq)]
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

/// A window's table (the policy row, the clauses read at once and at the close, and the default). A caller builds
/// one from its policy row with [`spec_from_policy`], or writes it.
#[derive(Clone, Debug, PartialEq, Eq)]
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

/// The window table of a policy row, by family, for an opener over an object: what the acts table binds (the caller
/// builds each with [`spec_from_policy`]; the object, for the base `active` of its room).
/// The third argument is the scope the object's founding row seats (for a row whose count set names several seats,
/// `self+key`: [`spec_from_policy`]'s `seat`); `None` for a key object or one with no founding row held.
pub type Families<'w, R> = dyn Fn(&str, &ObjOf<R>, Option<&str>) -> Option<WindowSpec<<R as WindowRow>::T>> + 'w;

/// The family the acts table binds an opener to: the act it [`WindowRow::proposes`] over its object's kind, through
/// [`seat::policy_for`]. A `fixed` row names one family, and an opener that states another policy is bound to none; a
/// `row` row takes the policy the opener states, if it is one the act may take. A family of `&` (several counts at
/// once) is no window.
pub fn bound_family<'r, R: WindowRow + 'r>(
    law: &'r SeatLaw,
    get: &dyn Fn(&R::Id) -> Option<&'r R>,
    o: &'r R,
) -> Option<&'r str> {
    let obj = o.obj()?;
    let kind = seat::kind_of(law, get, &obj)?;
    let (act, sc) = o.proposes()?;
    let (pols, choice) = seat::policy_for(law, act, sc, kind)?;
    let stated = o.policy().map(|w| w.as_ref());
    let name = match choice {
        Choice::Fixed if pols.len() == 1 && stated.is_none_or(|s| s == pols[0]) => pols[0].as_str(),
        Choice::Row => pols.iter().map(|p| p.as_str()).find(|p| Some(*p) == stated)?,
        _ => return None,
    };
    (!name.contains('&')).then_some(name)
}

/// An opener's table: where the law binds acts and the caller gives the families, the family the acts table binds it
/// to ([`bound_family`]); otherwise the table its window name names.
fn table_of<'r, R: WindowRow + 'r>(
    o: &'r R,
    get: &dyn Fn(&R::Id) -> Option<&'r R>,
    law: &'r SeatLaw,
    windows: &Tables<'_, R>,
    families: Option<&Families<'_, R>>,
) -> Option<WindowSpec<R::T>> {
    match (families, &law.acts) {
        (Some(f), Some(_)) => {
            let obj = o.obj()?;
            let founding = match &obj {
                Obj::Row(id) => get(id),
                Obj::Key(_) => None,
            };
            f(bound_family(law, get, o)?, &obj, founding.and_then(|g| g.scope()).map(|w| w.as_ref()))
        }
        _ => o.window().and_then(windows),
    }
}

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
            Base::All | Base::Stated(_) => ("all", self.w.counted.as_str()),
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
    // the key view: an answer counts only where its signer's signature on it counts by the end rule
    // (`CutSpec::key_view`; none: every answer counts)
    let kept: Vec<&R>;
    let answers: &[&R] = match x.spec.key_view() {
        Some(kv) => {
            kept = answers.iter().copied().filter(|a| kv.counts(a.id(), a.signer())).collect();
            &kept
        }
        None => answers,
    };
    // one member and one voice per person (ruled on CIRISConstitution#224): every base counted by person, each answer
    // read as its signer's person BEFORE the opener's withdrawal, a duty holder's act and the moot are read; a key
    // that counts as no person answers for nobody. A window over a self roster reads keys ([`seat::Persons`]).
    let pp = seat::Persons::over(x.rows, x.law, x.spec, Some(&x.obj));
    let base = |b: &Base| pp.base(&x.base(b));
    let held = |b: &Base| pp.base(&x.held(b));
    let tv: BTreeSet<R::Key> =
        if w.target_votes { target.map(|t| pp.member(t)).into_iter().collect() } else { BTreeSet::new() };
    let mut voters = base(&Base::All);
    voters.extend(held(&Base::Scope("moderate".into())));
    voters.extend(tv.iter().cloned());
    let opener = pp.voice(&x.opener_signer).unwrap_or_else(|| x.opener_signer.clone());
    let person = |a: &R| -> Option<R::Key> { pp.voice(a.signer()).filter(|p| voters.contains(p)) };
    // the proposer's withdrawal is its own voice on the opener's clause, and never replaces what it said by opening.
    // It is the opener's own: its signer read as the opener is (its person, or, a key of no person, the key itself
    // as no person), whether or not that person is a voter
    let own = |k: &R::Key| -> Result<R::Key, R::Key> { pp.voice(k).ok_or_else(|| k.clone()) };
    let opener_own = own(&x.opener_signer);
    let is_wd = |a: &&R| own(a.signer()) == opener_own && a.says().is_some_and(|w| w.as_ref() == "withdraw");
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
    let acted: BTreeSet<R::Key> = answers
        .iter()
        .copied()
        .filter(|a| !is_wd(a))
        .filter_map(|a| {
            let p = person(a)?;
            duty_word(a).is_some_and(|b| held(b).contains(&p)).then_some(p)
        })
        .collect();
    let moot = |a: &R| person(a).is_some_and(|p| acted.contains(&p)) && duty_word(a).is_none();
    // a voice that says two things says nothing
    let by = ops::group_by(answers.iter().copied().filter(|a| person(a).is_some() && !is_wd(a)), |a| {
        person(a).expect("a voter")
    });
    let mut said: BTreeMap<R::Key, String> = BTreeMap::new();
    for (s, rs) in by {
        let heard = rs.iter().filter(|a| !moot(a));
        if let Some(v) = ops::one(heard.filter_map(|a| a.says().map(|w| String::from(w.as_ref())))) {
            said.insert(s, v);
        }
    }
    if let Some(o) = &w.opener_says {
        said.entry(opener.clone()).or_insert_with(|| o.clone());
    }
    let met = |cl: &Clause, floor: bool| {
        if cl.over == Base::Opener {
            return if cl.value == "withdraw" { withdrawn } else { said.get(&opener) == Some(&cl.value) };
        }
        // a count (a fraction, a floor) leaves the agents out; a clause one holder's act resolves reads them
        let keys = if cl.how == How::One { held(&cl.over) } else { base(&cl.over) };
        let yes = said
            .iter()
            .filter(|(s, v)| {
                **v == cl.value && (keys.contains(*s) || (floor && tv.contains(*s) && cl.value == "approve"))
            })
            .count();
        // CC 4.5.13: two comparisons (strictly more than a fraction, at least a fraction), each read by the
        // seat's count, with a floor in voices and a choice of base
        // every count is read in u128: a `usize` and a stated `u64` widen without loss, so no target (a
        // 32-bit one included) reads another count than a 64-bit one
        let y = yes as u128;
        let n = base_size(keys.len(), &cl.over);
        let more = |num, den, base| seat::met_wide(Some(Policy::Strict(num, den)), y, base, None);
        match &cl.how {
            &How::AtLeast(num, den, least) => {
                seat::met_wide(Some(Policy::AtLeast(num, den)), y, n, None) && y >= least as u128
            }
            &How::More(num, den) => more(num, den, n),
            &How::MoreAtLeast(num, den, least) => more(num, den, n) && y >= least as u128,
            How::MoreOfVoted(num, den, least, against) => {
                let no = said.iter().filter(|(s, v)| *v == against && keys.contains(*s)).count();
                more(*num, *den, y + no as u128) && y >= *least as u128
            }
            How::One => seat::met_wide(Some(Policy::One), y, n, None),
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

/// The size a clause counts over: the members its base reads, or for [`Base::Stated`] the stated count where it
/// is larger, never smaller. In `u128`, so that a stated count past `u32::MAX` is read whole on every target.
fn base_size(members: usize, over: &Base) -> u128 {
    let m = members as u128;
    match over {
        Base::Stated(s) => m.max(*s as u128),
        _ => m,
    }
}

/// Whether no clause of `w` counts the opener's signer: every counted clause (one not over [`Base::Opener`]) is
/// over [`Base::Others`], as the members' check is. The opener's signer is then no concluder of the window
/// (CIRISConstitution#221, W2: the overturn's landing is signed by any member but the act's author).
///
/// The assumption: a table every counted clause of which is over `others` is a judgment of its opener's
/// signer. It holds for the members' check because the act opens its own window, so the opener's signer is the
/// act's author. Nothing ties the opener to an act: a table over `others` whose opener is a proposer, and not
/// the subject, also leaves the opener's signer no concluder (the reference's `proposal@others` cases).
pub fn author_apart<T>(w: &WindowSpec<T>) -> bool {
    let mut over = w.at_once.iter().chain(&w.at_close).map(|c| &c.over).filter(|b| **b != Base::Opener).peekable();
    over.peek().is_some() && over.all(|b| *b == Base::Others)
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

/// Each (row, signer) a withdrawal among `rows` names: a row `r` is withdrawn by its own signer iff
/// `(r.id(), r.signer())` is in the set. Pass concluded rows. The seat rule concludes a withdrawal by any
/// signer of the row it names, a cosigner included (and, for an offer, by a key it seats), so the match on the
/// signer is what makes it the row's own: a cosigner's withdrawal of a ballot withdraws nothing. The one
/// reading of a ballot's withdrawal: the window's ballots here, and any count of ballots of its own (an
/// election's) may read it. A withdrawal is read wherever it concludes, itself withdrawn or not: a withdrawn
/// ballot stays withdrawn, and the way back is a new ballot (CIRISConstitution#221, ruling C2).
pub fn own_withdrawals<'a, R: SeatRow + 'a>(
    rows: impl IntoIterator<Item = &'a R>,
) -> BTreeSet<(&'a R::Id, &'a R::Key)> {
    rows.into_iter()
        .filter(|w| w.seat_kind() == SeatKind::Withdraw)
        .filter_map(|w| w.target().map(|t| (t, w.signer())))
        .collect()
}

/// The rows of `answers` less each one saying a word of `words` that its own signer withdrew by a
/// withdrawal among `rows` (one ballot a person, folded as `ballot:moderator`: a withdrawn ballot is no
/// ballot; CC 2.4.1.1 rule 1). Pass the concluded rows: a withdrawal by another key withdraws nothing, even a
/// cosigner's, which concludes ([`own_withdrawals`] matches the signer). The
/// fold of the ballots left is [`ops::one`] per signer. Any caller folding ballots of its own (an election's)
/// may read its withdrawals here.
pub fn unwithdrawn<'r, R: SeatRow>(
    answers: Vec<&'r R>,
    rows: &[&R],
    words: &BTreeSet<&str>,
    says: impl Fn(&R) -> Option<&str>,
) -> Vec<&'r R> {
    let wd: BTreeSet<(&R::Id, &R::Key)> = own_withdrawals(rows.iter().copied());
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
    rule_why(p, windows, law, spec).map(|v| v.unwrap_or(false))
}

/// [`rule`], telling a window row that waits from one that concludes nothing ([`crate::Wait`]): `None` for a row
/// that is not a window row; `Some(Err(Wait(x)))` where it concludes nothing only for want of row `x`. A window row
/// reads its concluded ancestors, which no arrival changes, so it waits only where an opener that is an offer or
/// an unseat waits by the seat's rule ([`seat::seat_rule_why`]).
pub fn rule_why<R: WindowRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    windows: &Tables<'_, R>,
    law: &SeatLaw,
    spec: &S,
) -> Option<Result<bool, crate::Wait<R::Id>>> {
    rule_with(p, windows, None, law, spec, true)
}

/// [`rule`], with each opener's table taken through the act binding where the law carries one (`law.acts`): the
/// policy row the acts table binds the act the opener proposes to, from `families` ([`bound_family`]); an opener
/// bound to no family concludes nothing. Where the law binds no act, the opener's window name, as [`rule`].
pub fn rule_bound<R: WindowRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    families: &Families<'_, R>,
    windows: &Tables<'_, R>,
    law: &SeatLaw,
    spec: &S,
) -> Option<bool> {
    rule_with(p, windows, Some(families), law, spec, true).map(|v| v.unwrap_or(false))
}

/// [`rule`], with every scope the table reads walked at once (`prefill`) or each read when first asked (the
/// two must agree; this module's tests compare them).
fn rule_with<R: WindowRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    windows: &Tables<'_, R>,
    families: Option<&Families<'_, R>>,
    law: &SeatLaw,
    spec: &S,
    prefill: bool,
) -> Option<Result<bool, crate::Wait<R::Id>>> {
    let r = p.row();
    let k = r.win_kind()?;
    let rows: Vec<&R> = p.rows().collect();
    let past = |a: &R::Id, b: &R::Id| p.past(a, b);
    if k == WinKind::Open {
        let get = |i: &R::Id| p.get(i);
        let (Some(w), Some(obj)) = (table_of(r, &get, law, windows, families), r.obj()) else { return Some(Ok(false)) };
        // an act that opens its own window is validly made by the seat's rule too
        if matches!(r.seat_kind(), SeatKind::Offer | SeatKind::Unseat) {
            match seat::seat_rule_why(p, law, spec, &|_| true) {
                Ok(true) => {}
                Ok(false) => return Some(Ok(false)),
                Err(w) => return Some(Err(w)),
            }
        }
        // an opening names the newest counted changes over its object in its own past, and is counted there (H1)
        if !matches!(r.seat_kind(), SeatKind::Offer | SeatKind::Unseat)
            && seat::newer_head_in_past(p, law, &obj, r.head(), &seat::signers(r))
        {
            return Some(Ok(false));
        }
        let scope = w.opener.as_ref().unwrap_or(&w.counted);
        return Some(Ok(members_in(&rows, &past, law, spec, &obj, r.head(), scope).contains(r.signer())));
    }
    let Some(o) = r.of().and_then(|o| p.get(o)) else { return Some(Ok(false)) };
    if o.win_kind() != Some(WinKind::Open) {
        return Some(Ok(false));
    }
    if k == WinKind::Answer {
        return Some(Ok(true)); // whether its voice counts is read against the roster at the opener's head
    }
    let get = |i: &R::Id| p.get(i);
    let (Some(w), Some(obj)) = (table_of(o, &get, law, windows, families), o.obj()) else { return Some(Ok(false)) };
    // a `local` concluder (the accord's halt, ruled 2026-11-28): each node reads its own close and signs nothing, so
    // no receipt and no landing of it concludes
    if w.concluder == "local" {
        return Some(Ok(false));
    }
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
        return Some(Ok(false));
    }
    if r.signer() == o.signer() && author_apart(&w) {
        return Some(Ok(false)); // out of every count of the window, so no concluder of it
    }
    if k == WinKind::Receipt {
        // a receipt puts no row of the target before the window: none in its past that the opener's past does
        // not hold
        let Some(t) = o.target_key() else { return Some(Ok(true)) };
        return Some(Ok(!rows.iter().any(|q| q.signer() == t && q.id() != o.id() && !p.past(q.id(), o.id()))));
    }
    let Some(rec) = r.receipt().and_then(|x| p.get(x)) else { return Some(Ok(false)) };
    if rec.win_kind() != Some(WinKind::Receipt) || rec.signer() != r.signer() || rec.of() != Some(o.id()) {
        return Some(Ok(false));
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
    Some(Ok(r.says().is_some_and(|s| s.as_ref() == got)))
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
    outcome_with(c, pid, windows, None, law, spec, cut_counts, true)
}

/// [`outcome`], with the opener's table taken through the act binding as [`rule_bound`] takes it.
pub fn outcome_bound<R: WindowRow, S: CutSpec<R>>(
    c: &Concluded<'_, R>,
    pid: usize,
    families: &Families<'_, R>,
    windows: &Tables<'_, R>,
    law: &SeatLaw,
    spec: &S,
    cut_counts: &dyn Fn(usize) -> bool,
) -> Outcome {
    outcome_with(c, pid, windows, Some(families), law, spec, cut_counts, true)
}

#[allow(clippy::too_many_arguments)]
fn outcome_with<R: WindowRow, S: CutSpec<R>>(
    c: &Concluded<'_, R>,
    pid: usize,
    windows: &Tables<'_, R>,
    families: Option<&Families<'_, R>>,
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
    let get = |i: &R::Id| g.idx(i).map(|x| g.row(x));
    let (Some(w), Some(obj)) = (table_of(p, &get, law, windows, families), p.obj()) else { return Outcome::None };
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
    let mut by: Option<BTreeMap<&R::Id, &R>> = None;
    for &wi in c.cs() {
        let wr = g.row(wi);
        if wr.seat_kind() != SeatKind::Withdraw {
            continue;
        }
        // a withdrawal that names a scope ends the signer's seat on the roster only where it ends its stay as a
        // member over the object (seat::stay_end): one naming a duty lays that seat down, and the key's voice
        // stands; the older presentation's founding seat of scope `duty` holds `member`, so laying it down ends
        // the stay; one naming `member` of an offer that seats no member ends nothing
        if wr.scope().is_some() {
            let by = by.get_or_insert_with(|| g.rows().iter().map(|r| (r.id(), *r)).collect());
            if seat::stay_end(law, by, wr, &|a| c.concluded_id(a.id()) && g.id_in_past(a.id(), wi)).as_ref()
                != Some(&obj)
            {
                continue;
            }
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

// ---- a window's table from its policy row -------------------------------------------------------------------

/// A typed rule cell of a policy row (`enact_rule`, `cancel_rule`, `floor_rule`): `{kind, num, den, count, roles,
/// choices}` as the table writes it, a field it leaves out `None` (or empty).
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct RuleCell {
    /// `fraction`, `strict_majority`, `strict_majority_of_others`, `one_of_n`, `voices`, `voices_or_roster`,
    /// `voted_majority`, `role_at`, `ranked_irv`, `protocol` or `none`.
    pub kind: String,
    /// A fraction's numerator.
    pub num: Option<u64>,
    /// A fraction's denominator.
    pub den: Option<u64>,
    /// A count of voices.
    pub count: Option<u64>,
    /// The roles of `role_at`.
    pub roles: Vec<String>,
    /// The choices of `ranked_irv`.
    pub choices: Option<u64>,
}

/// A cell of a policy row's `counted` object: its value and the section that states it.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct Cell {
    /// The value (`unstated` where the text does not state it).
    pub value: String,
    /// The section, where the table cites one.
    pub cc_ref: Option<String>,
}

/// The `counted` object of a policy row (the table's `counted_columns`).
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct CountedCells {
    /// The role tokens counted, joined by `+`, less `-target`, `-proposer` or `-node`.
    pub count_set: Cell,
    /// `person` or `key`.
    pub voice: Cell,
    /// `signed`, `named`, `act` or `founding`.
    pub counted_at: Cell,
    /// `scrubs`, `objection` or `ballot`.
    pub voices: Cell,
    /// `yes`: a row of the target inside the window refuses it.
    pub target_silent: Cell,
    /// `adds`, `removes` or `no`.
    pub changes_set: Cell,
    /// `yes`: the target's own yes is a voice.
    pub target_voice: Cell,
}

/// A prose cell of a policy row (`enact`, `cancel`, `floor`): JSON `null`, a string, or a `{num, den}` fraction.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Stated {
    /// `null`.
    Null,
    /// A string.
    Text(String),
    /// `{num, den}`.
    Fraction(u64, u64),
}

/// A cell of words: a list (`["landed", "refused"]`), or one word (`—`, `unstated`).
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Words {
    /// A list.
    Listed(Vec<String>),
    /// One word.
    Word(String),
}

impl Words {
    fn list(&self) -> &[String] {
        match self {
            Words::Listed(v) => v,
            Words::Word(_) => &[],
        }
    }
}

/// The `comparison` cell: how the enact, the cancel and the floor are met (`more_than` or `at_least` the fraction).
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct Comparison {
    /// The enact's.
    pub enact: String,
    /// The cancel's.
    pub cancel: String,
    /// The floor's.
    pub floor: String,
}

/// One row of the governance policy table (the Constitution's `manifests/governance_policy.json`, `families`),
/// every field as the table carries it. The crate reads no JSON: the caller decodes the row into this, unchanged.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PolicyRow {
    /// The family.
    pub family: String,
    /// The sections.
    pub cc_ref: String,
    /// `two_path`, `mirror`, `cosigned`, `ranked` or `tally`.
    pub kind: String,
    /// The standing set, in words.
    pub standing_set: String,
    /// `standing` or `active`.
    pub base: String,
    /// The enact, in words or a fraction.
    pub enact: Stated,
    /// The cancel, in words or a fraction.
    pub cancel: Stated,
    /// The floor, in words or a fraction.
    pub floor: Stated,
    /// The enact, typed.
    pub enact_rule: RuleCell,
    /// The cancel, typed.
    pub cancel_rule: RuleCell,
    /// The floor, typed.
    pub floor_rule: RuleCell,
    /// The counted columns.
    pub counted: CountedCells,
    /// `base`, `others` or `—`.
    pub cancel_over: String,
    /// The text's description of the close with no count met (`default_at_close` is the leaf): carried, unread.
    pub at_window: String,
    /// Who signs the landing: a scope word of the count set (`-proposer`: any but the opener's signer), `local`
    /// (each node reads its own close and signs nothing), `none` (the row lands when its count is met).
    pub concluder: String,
    /// The scope whose act opens the window; `none`: nothing signed opens it.
    pub opener: String,
    /// What the opening act counts as: `approve`, `nothing` or `fires`.
    pub opener_says: String,
    /// The leaves a landing may state (`landed`, `refused`); `—` where the row has no window rows.
    pub outcome_words: Words,
    /// What an answer says: `assent` and `raised`, `for` and `against`, `cosign`, `ballot`.
    pub answer_words: Words,
    /// The leaf at the close with no count met.
    pub default_at_close: String,
    /// What `landed` means for the row (carried, read for no spec cell).
    pub landed_means: String,
    /// What `refused` means for the row (carried, read for no spec cell).
    pub refused_means: String,
    /// How the enact, the cancel and the floor are met.
    pub comparison: Comparison,
    /// The base, where the text states it as a number.
    pub stated_census: Option<u64>,
    /// The window's length.
    pub window_secs: u64,
    /// The window's class (a key of the table's `window_classes`).
    pub window_class: String,
    /// No instant landing.
    pub irreversible: bool,
    /// A floored, unopposed proposal lands at the close.
    pub reverse_path: bool,
    /// The corridor (a key of the table's `min_count`, for a row that has one).
    pub corridor: String,
    /// The models.
    pub model: Vec<String>,
    /// `default` or `normative`.
    pub status: String,
    /// The note.
    pub note: String,
}

/// The cells of the policy table every row is read with: `min_count` and `window_classes`.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct PolicyTable {
    /// The least voices, by corridor.
    pub min_count: BTreeMap<String, u64>,
    /// The length of each window class.
    pub window_classes: BTreeMap<String, u64>,
}

/// The base `active`, which the table states as a law and not a count (CC 4.5.13, `base_law`): the caller says which.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Active {
    /// The room has at most `base_law.k` members: the base is the members (`base(N) = N`).
    WithinK,
    /// The census's figure (CC 6.1.9), which the kernel takes and does not check ([`Base::Stated`]).
    Census(u64),
}

/// Why a cell stops a row giving a window's table.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum Why {
    /// The cell reads `unstated`.
    Unstated,
    /// A value [`spec_from_policy`] does not read as a window.
    Unknown,
    /// The cell disagrees with another cell of the row (named).
    Disagrees(&'static str),
    /// The row carries no window (`window_secs` 0).
    NoWindow,
    /// The row's kind is a counted row, a ranked count or a tally, which no window table closes.
    NotAWindow,
    /// The row's close is each node's own and signs nothing (`concluder` `local`): no landing to judge.
    Local,
    /// The table has no column for what the table needs (named).
    NoCell(&'static str),
    /// The cell needs what the caller states and did not (named).
    Caller(&'static str),
}

/// A cell that stops a row giving a window's table, and why.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub struct PolicyRefusal {
    /// The cell, as the table names it (`counted.voices`, `cancel_over`, ...).
    pub cell: &'static str,
    /// Why.
    pub why: Why,
}

const NONE: &str = "\u{2014}";

/// The window table one row of the policy table gives, every cell read, nothing defaulted but where the
/// Constitution's text states it; or every cell that stops it, sorted and once each (the table names its cells; it
/// does not order them). `window.py`'s `spec_from_policy` is the same reading; ADOPTING.md lists each cell.
///
/// `active` is the base `active` where the row states no census; `seat`, where the count set names several seats
/// (`self+key`), the one the object seats. A `two_path` or `mirror` row gives a table:
/// - `counted.count_set`: the scope counted (the seat); `-proposer` counts the others ([`Base::Others`]).
/// - `concluder`: a scope word of the count set, the counted scope (`-proposer`: the opener's signer apart, by
///   [`author_apart`]); `local` is refused ([`Why::Local`]). `opener`: the counted scope ([`None`]) or another.
/// - `opener_says`: `approve`, the yes of `answer_words` (CC 3.1.9.2); `nothing`, no voice.
/// - `answer_words`: objection's `assent` and `raised`, or a ballot's `for` and `against`: the clauses' values.
/// - `outcome_words` (`landed`, `refused`): the clauses' leaves; `default_at_close`, the default.
/// - `comparison`: the enact, cancel and floor, `more_than` ([`How::MoreAtLeast`]; [`How::Strict`] for 1/2 with at
///   most one voice) or `at_least` ([`How::AtLeast`]).
/// - two_path: `enact_rule` at once (at the close where `irreversible`), at least `min_count` voices; `cancel_rule`
///   over `cancel_over`, at once on the self corridor (CC 3.3.6.4), at the close otherwise; `floor_rule` with
///   `reverse_path` at the close, left out where `default_at_close` is `landed` too; the self corridor's proposer's
///   withdrawal, `refused` at once (CC 3.3.6.4).
/// - mirror: a strict majority enact of the one answer word with the floor's voices, at once; a `role_at` enact is
///   refused ([`Why::NoCell`]: no cell says the word a holder's act says).
/// - `counted.target_silent` `yes`: `silent` `refused`; `counted.target_voice` `yes`: `target_votes`.
/// - `base`, `stated_census`: the members; [`Base::Stated`] of the census; `active` as the caller says.
/// - `window_secs`, which `window_class` must give too.
///
/// Carried and read for no cell: `at_window`, `landed_means`, `refused_means`, `cc_ref`, `model`, `status`, `note`.
/// Ruled 2026-11-28: `accord_halt`'s concluder `local` (each node's own fuse, no landing: refused, [`Why::Local`]) and
/// opener_says `fires` (no confirming voice); a counted row at the window stays open (`at_window` `dropped` is a
/// storage note, read for nothing; a `cosigned` row is refused).
pub fn spec_from_policy<T: TryFrom<u64>>(
    row: &PolicyRow,
    table: &PolicyTable,
    active: Option<Active>,
    seat: Option<&str>,
) -> Result<WindowSpec<T>, Vec<PolicyRefusal>> {
    let mut why: Vec<PolicyRefusal> = Vec::new();
    let mut no = |cell: &'static str, w: Why| why.push(PolicyRefusal { cell, why: w });
    let c = &row.counted;
    for (name, cell) in [
        ("counted.count_set", &c.count_set),
        ("counted.voice", &c.voice),
        ("counted.counted_at", &c.counted_at),
        ("counted.voices", &c.voices),
        ("counted.target_silent", &c.target_silent),
        ("counted.changes_set", &c.changes_set),
        ("counted.target_voice", &c.target_voice),
    ] {
        if cell.value == "unstated" {
            no(name, Why::Unstated);
        }
    }
    let aw_unstated = row.answer_words == Words::Word("unstated".into());
    for (name, unstated) in [
        ("concluder", row.concluder == "unstated"),
        ("opener", row.opener == "unstated"),
        ("opener_says", row.opener_says == "unstated"),
        ("answer_words", aw_unstated),
    ] {
        if unstated {
            no(name, Why::Unstated);
        }
    }
    match table.window_classes.get(&row.window_class) {
        None => no("window_class", Why::Unknown),
        Some(&s) if s != row.window_secs => no("window_secs", Why::Disagrees("window_class")),
        _ => {}
    }
    if row.window_secs == 0 {
        no("window_secs", Why::NoWindow);
    }
    for (cell, prose, rule, other) in [
        ("enact", &row.enact, &row.enact_rule, "enact_rule"),
        ("cancel", &row.cancel, &row.cancel_rule, "cancel_rule"),
        ("floor", &row.floor, &row.floor_rule, "floor_rule"),
    ] {
        let fits = match prose {
            Stated::Null => rule.kind == "none",
            Stated::Text(_) => rule.kind != "none",
            Stated::Fraction(n, d) => rule.kind == "fraction" && rule.num == Some(*n) && rule.den == Some(*d),
        };
        if !fits {
            no(cell, Why::Disagrees(other));
        }
    }
    let cmp = &row.comparison;
    for (cell, v) in
        [("comparison.enact", &cmp.enact), ("comparison.cancel", &cmp.cancel), ("comparison.floor", &cmp.floor)]
    {
        if v != "more_than" && v != "at_least" {
            no(cell, Why::Unknown);
        }
    }
    let mut toks = c.count_set.value.split('-');
    let incl: Vec<&str> = toks.next().unwrap_or("").split('+').collect();
    let excl: Vec<&str> = toks.collect();
    let less = row.standing_set.replace(',', " ").split_whitespace().any(|w| w == "less");
    if less != !excl.is_empty() {
        no("counted.count_set", Why::Disagrees("standing_set"));
    }
    let kind = row.kind.as_str();
    match kind {
        "two_path" | "mirror" => {}
        "cosigned" | "ranked" | "tally" => no("kind", Why::NotAWindow),
        _ => no("kind", Why::Unknown),
    }
    if row.concluder == "local" {
        no("concluder", Why::Local);
    }
    if !matches!(kind, "two_path" | "mirror") || row.concluder == "local" {
        return Err(sorted(why));
    }
    // ---- a window: two_path or mirror
    let words: &[String] = row.outcome_words.list();
    if words.is_empty() || words.iter().any(|w| !matches!(w.as_str(), "held" | "landed" | "refused")) {
        no("outcome_words", Why::Unknown);
    }
    let has = |w: &str| words.iter().any(|x| x == w);
    let (landed_ok, refused_ok) = (has("landed"), has("refused"));
    let default = row.default_at_close.clone();
    if !has(&default) {
        no("default_at_close", Why::Disagrees("outcome_words"));
    }
    if incl.len() > 1 {
        match seat {
            None => no("counted.count_set", Why::Caller("the seat the object counts, of the count set")),
            Some(s) if !incl.contains(&s) => no("counted.count_set", Why::Disagrees("seat")),
            _ => {}
        }
    } else if seat.is_some_and(|s| s != incl[0]) {
        no("counted.count_set", Why::Disagrees("seat"));
    }
    let scope = String::from(seat.filter(|s| incl.contains(s)).unwrap_or(incl[0]));
    if excl.iter().any(|e| *e != "proposer") {
        no("counted.count_set", Why::Unknown);
    }
    let others = excl.contains(&"proposer");
    let named = |w: &str| incl.contains(&w.split('-').next().unwrap_or(""));
    if !named(&row.concluder) {
        no("concluder", Why::Unknown);
    }
    if row.concluder.ends_with("-proposer") != others {
        no("concluder", Why::Disagrees("counted.count_set"));
    }
    let opener = if named(&row.opener) { None } else { Some(row.opener.clone()) };
    if row.opener == "none" || row.opener == NONE {
        no("opener", Why::Unknown);
    }
    match c.voice.value.as_str() {
        "key" if row.corridor != "self" => no("counted.voice", Why::Disagrees("corridor")),
        "person" | "key" | "unstated" => {}
        _ => no("counted.voice", Why::Unknown),
    }
    if !matches!(c.counted_at.value.as_str(), "named" | "act" | "unstated") {
        no("counted.counted_at", Why::Unknown);
    }
    let aw: &[String] = row.answer_words.list();
    let all_in = |set: &[&str]| aw.iter().all(|w| set.contains(&w.as_str()));
    let (yes_w, no_w) = match c.voices.value.as_str() {
        "objection" if !aw.is_empty() && all_in(&["assent", "raised"]) => ("assent", "raised"),
        "ballot" if aw.len() == 2 && all_in(&["for", "against"]) && aw[0] != aw[1] => ("for", "against"),
        v => {
            if v != "unstated" {
                no("counted.voices", Why::Disagrees("answer_words"));
            }
            ("", "")
        }
    };
    let says = match row.opener_says.as_str() {
        "approve" => Some(String::from(yes_w)),
        "nothing" => None,
        _ => {
            no("opener_says", Why::Unknown);
            None
        }
    };
    let mut over = match (row.stated_census, row.base.as_str(), active) {
        (Some(n), _, a) => {
            if a.is_some() {
                no("base", Why::Disagrees("active"));
            }
            Base::Stated(n)
        }
        (None, "standing", a) => {
            if a.is_some() {
                no("base", Why::Disagrees("active"));
            }
            Base::All
        }
        (None, "active", None) => {
            no("base", Why::Caller("the census figure (CC 6.1.9), or within_k"));
            Base::All
        }
        (None, "active", Some(Active::WithinK)) => Base::All,
        (None, "active", Some(Active::Census(n))) => Base::Stated(n),
        _ => {
            no("base", Why::Unknown);
            Base::All
        }
    };
    if others {
        if over != Base::All {
            no("counted.count_set", Why::Disagrees("base"));
        }
        over = Base::Others;
    }
    let mc_ = table.min_count.get(&row.corridor).copied();
    let mut mc = || {
        if mc_.is_none() {
            no("corridor", Why::Unknown);
        }
        mc_.unwrap_or(0)
    };
    let mut leaf_no = Vec::new();
    let mut leaf = |w: &'static str| {
        if !has(w) {
            leaf_no.push(w);
        }
        String::from(w)
    };
    let clause = |value: &str, how: How, over: Base, out: String| Clause { value: value.into(), how, over, out };
    let frac = |n: u64, d: u64, comparison: &str, least: u64| match comparison {
        "more_than" if (n, d) == (1, 2) && least <= 1 => How::Strict,
        "more_than" if least > 0 => How::MoreAtLeast(n, d, least),
        "more_than" => How::More(n, d),
        _ => How::AtLeast(n, d, least),
    };
    let (er, cr, fr) = (&row.enact_rule, &row.cancel_rule, &row.floor_rule);
    let lone = row.corridor == "self";
    let (mut at_once, mut at_close) = (Vec::new(), Vec::new());
    let mut unknown: Vec<&'static str> = Vec::new();
    let mut disagree: Vec<(&'static str, &'static str)> = Vec::new();
    let mut nocell: Vec<(&'static str, &'static str)> = Vec::new();
    if kind == "two_path" {
        if er.kind != "fraction" {
            unknown.push("enact_rule");
        }
        let m = mc();
        let enact =
            clause(yes_w, frac(er.num.unwrap_or(0), er.den.unwrap_or(0), &cmp.enact, m), over.clone(), leaf("landed"));
        if !row.irreversible {
            at_once.push(enact.clone());
        }
        if lone {
            at_once.push(clause("withdraw", How::One, Base::Opener, leaf("refused")));
        }
        let co = row.cancel_over.as_str();
        let cancel = match cr.kind.as_str() {
            "fraction" => {
                if co != "base" {
                    disagree.push(("cancel_over", "cancel_rule"));
                }
                let (n, d) = (cr.num.unwrap_or(0), cr.den.unwrap_or(0));
                Some(clause(no_w, frac(n, d, &cmp.cancel, m), over.clone(), leaf("refused")))
            }
            "strict_majority_of_others" => {
                if co != "others" {
                    disagree.push(("cancel_over", "cancel_rule"));
                } else if over != Base::All {
                    disagree.push(("cancel_over", "base"));
                }
                Some(clause(no_w, How::Strict, Base::Others, leaf("refused")))
            }
            "none" if co == NONE => None,
            _ => {
                unknown.push("cancel_rule");
                None
            }
        };
        if let Some(cl) = cancel {
            if lone {
                at_once.push(cl)
            } else {
                at_close.push(cl)
            }
        }
        if row.irreversible {
            at_close.push(enact);
        }
        if row.reverse_path {
            let floor = match fr.kind.as_str() {
                "fraction" => Some(clause(
                    yes_w,
                    frac(fr.num.unwrap_or(0), fr.den.unwrap_or(0), &cmp.floor, m),
                    over.clone(),
                    leaf("landed"),
                )),
                "one_of_n" => Some(clause(yes_w, How::One, over.clone(), leaf("landed"))),
                "none" => None,
                _ => {
                    unknown.push("floor_rule");
                    None
                }
            };
            // a floor that gives the default is no clause
            if let (Some(f), false) = (floor, default == "landed") {
                at_close.push(f);
            }
        }
    } else {
        // a mirror: the act is in force and its window counts against it; the floor is the enact's least voices
        if cr.kind != "none" {
            unknown.push("cancel_rule");
        }
        match (er.kind.as_str(), fr.kind.as_str(), fr.count) {
            ("strict_majority", "voices", Some(k)) => {
                if aw.len() != 1 {
                    disagree.push(("answer_words", "enact_rule"));
                } else {
                    let how = if cmp.enact == "more_than" { How::MoreAtLeast(1, 2, k) } else { How::AtLeast(1, 2, k) };
                    at_once.push(clause(&aw[0], how, over.clone(), leaf("landed")));
                }
            }
            ("role_at", f, k) => {
                nocell.push(("enact_rule", "the word a role holder's act says, and the leaf it gives"));
                match (f, k, c.voices.value.as_str()) {
                    ("voted_majority", Some(k), "ballot") => at_close.push(clause(
                        yes_w,
                        How::MoreOfVoted(1, 2, k, no_w.into()),
                        over.clone(),
                        leaf("landed"),
                    )),
                    _ => unknown.push("floor_rule"),
                }
            }
            _ => unknown.push("enact_rule"),
        }
    }
    let mut silent = None;
    if c.target_silent.value == "yes" {
        if c.changes_set.value != "removes" {
            disagree.push(("counted.target_silent", "counted.changes_set"));
        }
        silent = Some(leaf("refused"));
    }
    let tv = c.target_voice.value == "yes";
    if tv && c.changes_set.value != "adds" {
        disagree.push(("counted.target_voice", "counted.changes_set"));
    }
    for w in leaf_no {
        no(
            "outcome_words",
            Why::Disagrees(if w == "landed" { "a clause's leaf landed" } else { "a clause's leaf refused" }),
        );
    }
    let _ = (landed_ok, refused_ok);
    for cell in unknown {
        no(cell, Why::Unknown);
    }
    for (cell, other) in disagree {
        no(cell, Why::Disagrees(other));
    }
    for (cell, what) in nocell {
        no(cell, Why::NoCell(what));
    }
    let secs = T::try_from(row.window_secs).ok();
    if secs.is_none() {
        no("window_secs", Why::Unknown);
    }
    let Some(secs) = secs.filter(|_| why.is_empty()) else { return Err(sorted(why)) };
    Ok(WindowSpec {
        counted: scope.clone(),
        concluder: scope,
        opener,
        opener_says: says,
        at_once,
        silent,
        at_close,
        default,
        target_votes: tv,
        secs,
    })
}

fn sorted(mut why: Vec<PolicyRefusal>) -> Vec<PolicyRefusal> {
    why.sort();
    why.dedup();
    why
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

    /// The size a stated base counts over is read whole past `u32::MAX` (no truncation on a 32-bit target) and
    /// never below the members the rows seat.
    #[test]
    fn a_stated_base_is_read_whole_and_never_below_the_members() {
        let big = u32::MAX as u64 + 1;
        assert_eq!(base_size(13, &Base::Stated(big)), big as u128);
        assert_eq!(base_size(13, &Base::Stated(big + 13)), big as u128 + 13);
        assert_eq!(base_size(13, &Base::Stated(5)), 13);
        assert_eq!(base_size(13, &Base::All), 13);
        // nine approvals of thirteen members over a stated 2^32 meet no 2/3 count, nor over 2^32 + 13
        for s in [big, big + 13] {
            assert!(!seat::met_wide(Some(Policy::AtLeast(2, 3)), 9, base_size(13, &Base::Stated(s)), None));
        }
        assert!(seat::met_wide(Some(Policy::AtLeast(2, 3)), 9, base_size(13, &Base::Stated(5)), None));
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
        policy: Option<String>,
        of: Option<u32>,
        win: Option<WinKind>,
        window: Option<String>,
        says: Option<String>,
        receipt: Option<u32>,
        at: Option<i64>,
        target: Option<u32>,
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
                policy: None,
                of: None,
                win: None,
                window: None,
                says: None,
                receipt: None,
                at: None,
                target: None,
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
        fn word(s: &'static str) -> String {
            s.into()
        }
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
        fn policy(&self) -> Option<&String> {
            self.policy.as_ref()
        }
        fn of(&self) -> Option<&u32> {
            self.of.as_ref()
        }
        fn target(&self) -> Option<&u32> {
            self.target.as_ref()
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

    /// Clauses drawn from `g`, and from `h` (a second stream, so that `g` draws what it drew before) a clause
    /// counted over those who voted and a stated base, now and then one past 32 bits.
    fn clauses(g: &mut Lcg, h: &mut Lcg) -> Vec<Clause> {
        let mut out: Vec<Clause> = (0..g.next(3))
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
            .collect();
        for cl in &mut out {
            if h.next(5) == 0 {
                cl.how =
                    How::MoreOfVoted(1, 2, h.next(3), if cl.value == "no" { "approve".into() } else { "no".into() });
            }
            if h.next(6) == 0 {
                cl.over = Base::Stated(if h.next(8) == 0 { (1u64 << 32) + h.next(9) } else { h.next(15) });
            }
        }
        out
    }

    /// A group with seats in five scopes (two named `all` and `others`), an opener at its version, answers
    /// (some withdrawn, by their signer or another key), the concluder's receipt and landings, under a generated
    /// table (some clauses counted over those who voted, some over a stated base): every conclusion and the outcome are
    /// the same whether the scopes the table reads are walked at once or each when first asked.
    #[test]
    fn prefilled_scopes_answer_as_scopes_read_when_asked() {
        // a roster seat over a group is placed by the founding record or a counted row: the members are seated by
        // the founding record, and the agent's key by the room's counted admission
        let mut law = SeatLaw::default();
        law.policy.insert("community_invite".into(), Policy::AtLeast(2, 3));
        let mut g = Lcg(3);
        let mut h = Lcg(17);
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
                    if sc == "member" {
                        // the founding record lists and is signed by the member (the draw order is as before)
                        rows[0].to.push(k);
                        rows[0].cosigners.push(k);
                        id += 1;
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
            // the newest counted change over the room: the opener names it as its head (H1, H8: a head is a counted
            // change or the founding row, never a note)
            let mut newest = 0;
            // now and then the last key holds an agent's seat as well: every base leaves it out, read either way
            if (id + n).is_multiple_of(4) {
                let mut o = W::new(id, vec![0], 1);
                o.kind = SeatKind::Offer;
                o.to = vec![n];
                // the room's counted admission: every member signs it (key 1 is the signer), and the agent's own
                // signature is its consent
                o.cosigners = rows[0].to.iter().copied().filter(|&k| k != 1).chain([n]).collect();
                o.scope = Some(AGENT.into());
                o.obj = Some(Obj::Row(0));
                o.conf = Some(Conf::Group);
                o.head = vec![0];
                o.policy = Some("community_invite".into());
                newest = o.id;
                rows.push(o);
            }
            let v = W::new(100, rows.iter().map(|r| r.id).collect(), 1);
            rows.push(v);
            let mut op = W::new(200, vec![100], 1 + g.next(n as u64) as u32);
            op.win = Some(WinKind::Open);
            op.window = Some("w".into());
            op.obj = Some(Obj::Row(0));
            op.head = vec![newest];
            rows.push(op);
            let mut answers = vec![];
            for j in 0..g.next(2 * n as u64) as u32 {
                let mut a = W::new(300 + j, vec![200], 1 + g.next(n as u64 + 1) as u32);
                a.win = Some(WinKind::Answer);
                a.of = Some(200);
                a.says = Some(if g.next(3) == 0 { "no".into() } else { "approve".into() });
                answers.push(a.id);
                // now and then its signer, or another key, withdraws it (drawn from `h`)
                let wd = (h.next(4) == 0).then(|| {
                    let by = if h.next(3) == 0 { 1 + h.next(n as u64) as u32 } else { a.signer };
                    let mut w = W::new(600 + j, vec![a.id], by);
                    w.kind = SeatKind::Withdraw;
                    w.target = Some(a.id);
                    w
                });
                rows.push(a);
                rows.extend(wd);
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
                at_once: clauses(&mut g, &mut h),
                silent: None,
                at_close: clauses(&mut g, &mut h),
                default: "cancel".into(),
                target_votes: false,
                secs: 50,
            };
            let tables = |w: &String| if w == "w" { Some(spec.clone()) } else { None };
            let concl = |prefill: bool| {
                conclude(
                    rows.iter(),
                    |p| match rule_with(p, &tables, None, &law, &NoCut, prefill) {
                        Some(v) => v.unwrap_or(false),
                        None => seat_rule(p, &law, &NoCut, &|_| true),
                    },
                    None,
                )
            };
            let (a, b) = (concl(true), concl(false));
            cases += 1;
            bad += (a.all() != b.all()) as usize;
            let op = a.g.idx(&200).unwrap();
            let oa = outcome_with(&a, op, &tables, None, &law, &NoCut, &|_| true, true);
            let ob = outcome_with(&a, op, &tables, None, &law, &NoCut, &|_| true, false);
            landed += matches!(oa, Outcome::Landed(_)) as usize;
            cases += 1;
            bad += (oa != ob) as usize;
        }
        assert!(landed > 300, "only {landed} windows landed");
        assert_eq!(bad, 0, "{bad} of {cases} differ");
    }
}
